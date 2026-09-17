"""Web UI: resume upload + clean chat assistant."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.resume_store import hydrate_resume, resume_status, save_and_index

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"

app = FastAPI(title="Resume AI Assistant", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_assistant = None


def get_assistant():
    global _assistant
    if _assistant is None:
        from src.assistant import Assistant

        _assistant = Assistant()
    return _assistant


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    # Client session fallback for serverless (Vercel) where disk/memory may reset
    resume_text: str | None = Field(default=None, max_length=200_000)
    resume_filename: str | None = Field(default=None, max_length=260)


class AskResponse(BaseModel):
    answer: str
    can_answer: bool
    kind: str
    sources: list[dict] = []


@app.get("/")
def index() -> FileResponse:
    html = STATIC_DIR / "index.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(html)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "serverless": bool(os.getenv("VERCEL")),
        "has_gemini": bool(os.getenv("GEMINI_API_KEY", "").strip()),
    }


@app.get("/api/resume")
def get_resume_status() -> dict:
    return resume_status()


def _error_detail(exc: BaseException) -> str:
    msg = str(exc).strip() or exc.__class__.__name__
    return msg[:500]


@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        result = save_and_index(file.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"Could not process resume: {_error_detail(exc)}"
        ) from exc

    try:
        assistant = get_assistant()
        assistant.reload_retriever()
    except Exception:
        # Retriever optional — answers still work from resume text
        pass

    return {
        "ok": True,
        "filename": result.filename,
        "chars": result.chars,
        "text": result.text,
        "message": "Resume studied and ready. Ask questions or generate interview questions.",
    }


@app.post("/api/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    # Rehydrate from browser session so ask works across serverless instances
    if body.resume_text and len(body.resume_text.strip()) > 40:
        try:
            hydrate_resume(
                body.resume_text, body.resume_filename or "session_resume.txt"
            )
            try:
                get_assistant().reload_retriever()
            except Exception:
                pass
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            pass

    try:
        resp = get_assistant().ask(question)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Could not answer: {_error_detail(exc)}",
        ) from exc
    return AskResponse(
        answer=resp.answer,
        can_answer=resp.can_answer,
        kind=resp.kind,
        sources=[],
    )


def main() -> None:
    import uvicorn

    uvicorn.run("src.webapp:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
