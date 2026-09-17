"""TF-IDF retrieval over the local index."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import Settings, get_settings


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+.#/-]{1,}", re.I)


@dataclass
class RetrievedChunk:
    chunk_id: str
    source_id: str
    source_path: str
    source_type: str
    section: str
    text: str
    score: float
    synthetic: bool


class Retriever:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        if not self.settings.index_path.exists():
            raise FileNotFoundError(
                f"Index missing at {self.settings.index_path}. Run: python -m src.ingest"
            )
        data = json.loads(self.settings.index_path.read_text(encoding="utf-8"))
        self.chunks = data["chunks"]
        # Rebuild vectorizer from stored vocabulary/idf for identical query space
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
            vocabulary=data["vocabulary"],
        )
        # fit on chunk texts to attach idf; then overwrite idf from store
        self.vectorizer.fit([c["text"] for c in self.chunks])
        self.vectorizer.idf_ = np.array(data["idf"], dtype=np.float64)
        # sklearn stores idf in _tfidf.idf_
        self.vectorizer._tfidf.idf_ = self.vectorizer.idf_
        self.matrix = np.array([c["embedding"] for c in self.chunks], dtype=np.float64)

    def _keyword_boost(self, query: str, text: str) -> float:
        q_tokens = {t.lower() for t in TOKEN_RE.findall(query)}
        if not q_tokens:
            return 0.0
        t_tokens = {t.lower() for t in TOKEN_RE.findall(text)}
        overlap = len(q_tokens & t_tokens) / max(1, len(q_tokens))
        return 0.12 * overlap

    def all_chunks_for_source(self, source_id: str, limit: int = 8) -> list[RetrievedChunk]:
        out: list[RetrievedChunk] = []
        for chunk in self.chunks:
            if chunk.get("source_id") != source_id:
                continue
            out.append(
                RetrievedChunk(
                    chunk_id=chunk["chunk_id"],
                    source_id=chunk["source_id"],
                    source_path=chunk["source_path"],
                    source_type=chunk["source_type"],
                    section=chunk["section"],
                    text=chunk["text"],
                    score=1.0,
                    synthetic=bool(chunk.get("synthetic", False)),
                )
            )
            if len(out) >= limit:
                break
        return out

    def retrieve(self, query: str, top_k: int | None = None, *, prefer_source: str | None = None) -> list[RetrievedChunk]:
        top_k = top_k or self.settings.retrieval_top_k
        q = self.vectorizer.transform([query]).toarray()
        from sklearn.metrics.pairwise import cosine_similarity

        sims = cosine_similarity(q, self.matrix)[0]
        scored: list[RetrievedChunk] = []
        for i, chunk in enumerate(self.chunks):
            score = float(sims[i]) + self._keyword_boost(query, chunk["text"])
            if prefer_source and chunk.get("source_id") == prefer_source:
                score += 0.35
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk["chunk_id"],
                    source_id=chunk["source_id"],
                    source_path=chunk["source_path"],
                    source_type=chunk["source_type"],
                    section=chunk["section"],
                    text=chunk["text"],
                    score=score,
                    synthetic=bool(chunk.get("synthetic", False)),
                )
            )
        scored.sort(key=lambda c: c.score, reverse=True)

        if prefer_source:
            preferred = [c for c in scored if c.source_id == prefer_source]
            if preferred:
                filtered = [c for c in preferred if c.score >= self.settings.retrieval_min_score]
                if not filtered:
                    filtered = preferred[:top_k]
                return filtered[:top_k]

        filtered = [c for c in scored if c.score >= self.settings.retrieval_min_score]
        return filtered[:top_k]

