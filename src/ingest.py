"""Ingest knowledge sources (+ optional upload dirs) into a local TF-IDF index."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import get_settings


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def _parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    match = FRONT_MATTER_RE.match(raw)
    meta: dict[str, str] = {}
    if not match:
        return meta, raw
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    body = raw[match.end() :]
    return meta, body


def _split_sections(body: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(body))
    if not matches:
        return [("body", body.strip())]
    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        preamble = body[: matches[0].start()].strip()
        if preamble:
            sections.append(("preamble", preamble))
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()
        if text:
            sections.append((title, text))
    return sections


def _window(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    if len(text) <= size:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        parts.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - overlap)
    return [p for p in parts if p]


def _chunks_from_document(
    *,
    source_id: str,
    source_type: str,
    synthetic: bool,
    source_path: str,
    raw: str,
) -> list[dict]:
    meta, body = _parse_front_matter(raw)
    source_id = meta.get("id", source_id)
    source_type = meta.get("source_type", source_type)
    synthetic = meta.get("synthetic", str(synthetic)).lower() == "true"
    pending: list[dict] = []
    for section, section_text in _split_sections(body):
        for window in _window(section_text):
            payload = f"{section}\n{window}"
            digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
            chunk_id = f"{source_id}:{digest}"
            pending.append(
                {
                    "chunk_id": chunk_id,
                    "source_id": source_id,
                    "source_path": source_path,
                    "source_type": source_type,
                    "synthetic": synthetic,
                    "section": section,
                    "text": payload,
                }
            )
    return pending


def build_chunks_from_dirs(dirs: list[Path]) -> list[dict]:
    pending: list[dict] = []
    seen_paths: set[str] = set()
    for sources_dir in dirs:
        if not sources_dir.exists():
            continue
        for path in sorted(sources_dir.glob("*.md")):
            key = str(path.resolve())
            if key in seen_paths:
                continue
            seen_paths.add(key)
            raw = path.read_text(encoding="utf-8")
            pending.extend(
                _chunks_from_document(
                    source_id=path.stem,
                    source_type="unknown",
                    synthetic=False,
                    source_path=str(path.as_posix()),
                    raw=raw,
                )
            )
    return pending


def build_index_payload(
    *,
    sources_dir: Path | None = None,
    extra_dirs: list[Path] | None = None,
    extra_documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    settings = get_settings(require_api_key=False)
    dirs = [sources_dir or settings.sources_dir]
    if extra_dirs:
        dirs.extend(extra_dirs)
    uploads = settings.upload_dir
    if uploads.exists() and uploads not in dirs:
        dirs.append(uploads)

    pending = build_chunks_from_dirs(dirs)
    seen_ids = {c["source_id"] for c in pending}

    for doc in extra_documents or []:
        sid = str(doc.get("id") or "uploaded_resume")
        # Prefer the live memory/upload document over a stale file copy
        pending = [c for c in pending if c.get("source_id") != sid]
        seen_ids.discard(sid)
        pending.extend(
            _chunks_from_document(
                source_id=sid,
                source_type=str(doc.get("source_type") or "cv"),
                synthetic=bool(doc.get("synthetic", False)),
                source_path=str(doc.get("path") or "memory://uploaded_resume"),
                raw=str(doc.get("text") or ""),
            )
        )

    if not pending:
        raise RuntimeError("No knowledge sources found to index.")

    texts = [c["text"] for c in pending]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        stop_words="english",
    )
    matrix = vectorizer.fit_transform(texts)
    dense = matrix.toarray().tolist()
    for i, chunk in enumerate(pending):
        chunk["embedding"] = dense[i]

    return {
        "retrieval": "tfidf",
        "vocabulary": vectorizer.vocabulary_,
        "idf": vectorizer.idf_.tolist(),
        "chunk_count": len(pending),
        "chunks": pending,
    }


def write_index_payload(payload: dict[str, Any], index_path: Path) -> Path:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return index_path


def ingest(
    *,
    sources_dir: Path | None = None,
    extra_dirs: list[Path] | None = None,
) -> Path:
    settings = get_settings(require_api_key=False)
    payload = build_index_payload(sources_dir=sources_dir, extra_dirs=extra_dirs)
    path = write_index_payload(payload, settings.index_path)
    print(f"Indexed {payload['chunk_count']} chunks -> {path}")
    return path


def main() -> None:
    ingest()


if __name__ == "__main__":
    main()
