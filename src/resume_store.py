"""Resume upload, text extraction, and indexing hooks.

Works locally and on serverless (Vercel): writes go to a writable data dir (/tmp),
with an in-memory fallback when the filesystem is read-only or ephemeral.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.ingest import build_index_payload, write_index_payload

ALLOWED_SUFFIXES = {".pdf", ".txt", ".md", ".docx"}

# Process memory — required on Vercel because /tmp is per-instance and ephemeral
_MEMORY_RESUME: str = ""
_MEMORY_FILENAME: str = ""
_MEMORY_INDEX: dict[str, Any] | None = None


@dataclass
class UploadResult:
    filename: str
    chars: int
    path: str
    text: str


def upload_dir() -> Path:
    return get_settings(require_api_key=False).upload_dir


def active_resume_path() -> Path:
    return upload_dir() / "active_resume.md"


def ensure_dirs() -> None:
    try:
        upload_dir().mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def get_memory_index() -> dict[str, Any] | None:
    return _MEMORY_INDEX


def set_memory_index(payload: dict[str, Any] | None) -> None:
    global _MEMORY_INDEX
    _MEMORY_INDEX = payload


def has_active_resume() -> bool:
    if len(_MEMORY_RESUME.strip()) > 40:
        return True
    path = active_resume_path()
    try:
        return path.exists() and path.stat().st_size > 40
    except OSError:
        return False


def active_resume_text() -> str:
    if _MEMORY_RESUME.strip():
        return _MEMORY_RESUME
    path = active_resume_path()
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except OSError:
        pass
    return ""


def _set_memory_resume(body: str, filename: str) -> None:
    global _MEMORY_RESUME, _MEMORY_FILENAME
    _MEMORY_RESUME = body
    _MEMORY_FILENAME = filename


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Supported formats: PDF, DOCX, TXT, MD")

    if suffix in {".txt", ".md"}:
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                return _clean_text(data.decode(enc))
            except UnicodeDecodeError:
                continue
        return _clean_text(data.decode("utf-8", errors="ignore"))

    if suffix == ".pdf":
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        text = _clean_text("\n\n".join(pages))
        if len(text) < 40:
            raise ValueError("Could not extract text from this PDF. Try TXT or DOCX.")
        return text

    if suffix == ".docx":
        from io import BytesIO

        from docx import Document

        doc = Document(BytesIO(data))
        text = _clean_text("\n".join(p.text for p in doc.paragraphs if p.text.strip()))
        if len(text) < 40:
            raise ValueError("Could not extract text from this DOCX.")
        return text

    raise ValueError("Unsupported file type")


def _format_resume_md(filename: str, text: str) -> str:
    safe_name = Path(filename).name.replace("`", "'")
    return (
        "---\n"
        "id: uploaded_resume\n"
        "source_type: cv\n"
        "synthetic: false\n"
        f"original_filename: {safe_name}\n"
        "---\n\n"
        f"{text.strip()}\n"
    )


def _plain_body(raw: str) -> str:
    return re.sub(r"^---.*?---\s*", "", raw, count=1, flags=re.S).strip()


def hydrate_resume(
    text: str, filename: str = "session_resume.txt", *, reindex: bool = False
) -> None:
    """Restore resume from client session (needed across serverless instances)."""
    cleaned = _clean_text(text or "")
    if len(cleaned) < 40:
        raise ValueError("Resume text is empty or too short")
    body = _format_resume_md(filename, cleaned)
    _set_memory_resume(body, Path(filename).name)
    try:
        ensure_dirs()
        active_resume_path().write_text(body, encoding="utf-8")
    except OSError:
        pass
    # Skip heavy TF-IDF rebuild on every ask — that caused timeouts/500s on Vercel
    if reindex:
        _reindex_best_effort()


def _reindex_best_effort() -> None:
    settings = get_settings(require_api_key=False)
    try:
        payload = build_index_payload(
            sources_dir=settings.sources_dir,
            extra_dirs=[settings.upload_dir],
            extra_documents=[
                {
                    "id": "uploaded_resume",
                    "source_type": "cv",
                    "synthetic": False,
                    "path": "memory://uploaded_resume",
                    "text": active_resume_text(),
                }
            ],
        )
        set_memory_index(payload)
        try:
            write_index_payload(payload, settings.index_path)
        except OSError:
            pass
    except Exception:
        # Answering still works from resume body without TF-IDF index
        set_memory_index(None)


def save_and_index(filename: str, data: bytes) -> UploadResult:
    max_bytes = 4 * 1024 * 1024 if __import__("os").getenv("VERCEL") else 8 * 1024 * 1024
    if len(data) > max_bytes:
        raise ValueError(f"File too large (max {max_bytes // (1024 * 1024)}MB)")

    text = extract_text(filename, data)
    safe_name = Path(filename).name.replace("`", "'")
    body = _format_resume_md(safe_name, text)
    _set_memory_resume(body, safe_name)

    path_str = "memory://uploaded_resume"
    try:
        ensure_dirs()
        path = active_resume_path()
        path.write_text(body, encoding="utf-8")
        path_str = str(path.as_posix())
    except OSError:
        # Read-only filesystem (e.g. Vercel) — memory is enough
        pass

    _reindex_best_effort()

    return UploadResult(
        filename=safe_name,
        chars=len(text),
        path=path_str,
        text=text,
    )


def resume_status() -> dict:
    if not has_active_resume():
        return {"uploaded": False, "filename": None, "chars": 0}
    raw = active_resume_text()
    match = re.search(r"original_filename:\s*(.+)", raw)
    name = (
        match.group(1).strip()
        if match
        else (_MEMORY_FILENAME or "active_resume.md")
    )
    body = _plain_body(raw)
    return {"uploaded": True, "filename": name, "chars": len(body.strip())}
