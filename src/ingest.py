"""Ingest knowledge sources (+ optional upload dirs) into a local TF-IDF index."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

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
            meta, body = _parse_front_matter(raw)
            source_id = meta.get("id", path.stem)
            source_type = meta.get("source_type", "unknown")
            synthetic = meta.get("synthetic", "false").lower() == "true"
            for section, section_text in _split_sections(body):
                for window in _window(section_text):
                    payload = f"{section}\n{window}"
                    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
                    chunk_id = f"{source_id}:{digest}"
                    pending.append(
                        {
                            "chunk_id": chunk_id,
                            "source_id": source_id,
                            "source_path": str(path.as_posix()),
                            "source_type": source_type,
                            "synthetic": synthetic,
                            "section": section,
                            "text": payload,
                        }
                    )
    return pending


def ingest(
    *,
    sources_dir: Path | None = None,
    extra_dirs: list[Path] | None = None,
) -> Path:
    settings = get_settings(require_api_key=False)
    dirs = [sources_dir or settings.sources_dir]
    if extra_dirs:
        dirs.extend(extra_dirs)
    # Always include uploads when present
    uploads = settings.sources_dir.parent / "uploads"
    if uploads.exists() and uploads not in dirs:
        dirs.append(uploads)

    pending = build_chunks_from_dirs(dirs)
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

    settings.index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "retrieval": "tfidf",
        "vocabulary": vectorizer.vocabulary_,
        "idf": vectorizer.idf_.tolist(),
        "chunk_count": len(pending),
        "chunks": pending,
    }
    settings.index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Indexed {len(pending)} chunks -> {settings.index_path}")
    return settings.index_path


def main() -> None:
    ingest()


if __name__ == "__main__":
    main()
