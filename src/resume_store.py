"""Resume upload, text extraction, and indexing hooks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.config import ROOT, get_settings
from src.ingest import ingest

UPLOAD_DIR = ROOT / "knowledge" / "uploads"
ACTIVE_RESUME = UPLOAD_DIR / "active_resume.md"
ALLOWED_SUFFIXES = {".pdf", ".txt", ".md", ".docx"}


@dataclass
class UploadResult:
    filename: str
    chars: int
    path: str


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def has_active_resume() -> bool:
    return ACTIVE_RESUME.exists() and ACTIVE_RESUME.stat().st_size > 40


def active_resume_text() -> str:
    if not has_active_resume():
        return ""
    return ACTIVE_RESUME.read_text(encoding="utf-8")


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
        from pypdf import PdfReader
        from io import BytesIO

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


def save_and_index(filename: str, data: bytes) -> UploadResult:
    ensure_dirs()
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("File too large (max 8MB)")

    text = extract_text(filename, data)
    safe_name = Path(filename).name.replace("`", "'")
    body = (
        "---\n"
        "id: uploaded_resume\n"
        "source_type: cv\n"
        "synthetic: false\n"
        f"original_filename: {safe_name}\n"
        "---\n\n"
        f"{text.strip()}\n"
    )
    ACTIVE_RESUME.write_text(body, encoding="utf-8")

    # Prefer uploaded resume: index uploads + keep seed sources for gaps/demo
    settings = get_settings(require_api_key=False)
    ingest(extra_dirs=[UPLOAD_DIR], sources_dir=settings.sources_dir)

    return UploadResult(
        filename=safe_name,
        chars=len(text),
        path=str(ACTIVE_RESUME.as_posix()),
    )


def resume_status() -> dict:
    if not has_active_resume():
        return {"uploaded": False, "filename": None, "chars": 0}
    raw = active_resume_text()
    match = re.search(r"original_filename:\s*(.+)", raw)
    name = match.group(1).strip() if match else "active_resume.md"
    # Approximate body size without front matter
    body = re.sub(r"^---.*?---\s*", "", raw, count=1, flags=re.S)
    return {"uploaded": True, "filename": name, "chars": len(body.strip())}
