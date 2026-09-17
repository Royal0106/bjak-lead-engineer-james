"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    retrieval_min_score: float
    retrieval_top_k: int
    max_output_tokens: int
    force_local_synth: bool
    sources_dir: Path
    index_path: Path


def get_settings(*, require_api_key: bool = True) -> Settings:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    force_local = os.getenv("FORCE_LOCAL_SYNTH", "0").strip() in {"1", "true", "True"}
    # No key → automatic offline mode so start.bat always works
    if not key:
        force_local = True
    if require_api_key and not key and not force_local:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
            "(or set FORCE_LOCAL_SYNTH=1 for offline mode)."
        )
    return Settings(
        gemini_api_key=key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
        retrieval_min_score=float(os.getenv("RETRIEVAL_MIN_SCORE", "0.08")),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
        max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "1024")),
        force_local_synth=force_local,
        sources_dir=ROOT / "knowledge" / "sources",
        index_path=ROOT / "knowledge" / "index" / "chunks.json",
    )
