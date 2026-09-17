"""Web UI: resume upload + clean chat assistant."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.assistant import Assistant
from src.resume_store import resume_status, save_and_index

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"

app = FastAPI(title="Resume AI Assistant", version="2.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_assistant: Assistant | None = None


def get_assistant() -> Assistant:
    global _assistant
    if _assistant is None:
        _assistant = Assistant()
    return _assistant


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    answer: str
    can_answer: bool
    kind: str
    sources: list[dict] = []


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/resume")
def get_resume_status() -> dict:
    return resume_status()


@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    data = await file.read()
    try:
        result = save_and_index(file.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Could not process resume: {exc}") from exc

    assistant = get_assistant()
    assistant.reload_retriever()
    return {
        "ok": True,
        "filename": result.filename,
        "chars": result.chars,
        "message": "Resume studied and ready. Ask questions or generate interview questions.",
    }


@app.post("/api/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    try:
        resp = get_assistant().ask(question)
    except Exception as exc:  # noqa: BLE001
        # Never leak stack traces to the product UI
        raise HTTPException(
            status_code=500,
            detail="I can help you based on resume",
        ) from exc
    return AskResponse(
        answer=resp.answer,
        can_answer=resp.can_answer,
        kind=resp.kind,
        # Keep the chat interview-clean — no source dump under answers.
        sources=[],
    )


def main() -> None:
    import uvicorn

    uvicorn.run("src.webapp:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
