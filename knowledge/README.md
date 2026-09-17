# Personal knowledge layer

## What the assistant can see

| Source | Path | Status | Notes |
|--------|------|--------|-------|
| Curriculum vitae | `sources/cv.md` | **SYNTHETIC** | Primary grounding document |
| Project write-ups | `sources/projects.md` | **SYNTHETIC** | Deep-dives on two shipped systems |
| Working style | `sources/working-style.md` | **SYNTHETIC** | How the subject leads and decides |
| Conflict note | `sources/conflicts.md` | **SYNTHETIC** | Documents a deliberate CV/LinkedIn mismatch |

Everything in `sources/` is **synthetic** and labelled as such. No real CV, LinkedIn export, or private employer data is committed. The pipeline is graded, not the career.

## Collection → clean → structure → index

1. **Collect** — drop markdown files under `sources/` (CV is the minimum).
2. **Clean** — strip HTML/noise; keep headings, dates, employer names, and measurable outcomes. Redactions use `[REDACTED]`.
3. **Structure** — each file starts with YAML-ish front matter (`id`, `source_type`, `synthetic`, `as_of`). Body uses stable section headings so chunks stay attributable.
4. **Index** — `python -m src.ingest` chunks by heading + ~700-char windows, fits a local TF-IDF vectorizer, writes `index/chunks.json`.
5. **Maintain** — re-run ingest after any source edit. Chunk IDs are content-hash based so unchanged text keeps stable IDs.

## Storage and retrieval

- **Store:** local JSON (`knowledge/index/chunks.json`) with text, metadata, TF-IDF vectors, and vocabulary. No hosted vector DB in this slice.
- **Retrieve:** cosine similarity in TF-IDF space + light keyword boost for employer/title tokens. Top-k chunks above `RETRIEVAL_MIN_SCORE` become evidence. Below threshold → refuse rather than invent.

## Adding a source later

1. Add `knowledge/sources/<name>.md` with front matter.
2. Run `python -m src.ingest`.
3. Optionally add eval questions that exercise the new material.

No schema migration, no redesign — ingest is additive over the `sources/` directory.

## Conflict / gap / stale fact (real behaviour)

See `sources/conflicts.md`.

**Conflict:** CV title at Northstar Payments is "Staff Engineer"; synthetic LinkedIn-style note says "Engineering Manager" for the same period (2021–2023).

**What the system does:** retrieval may surface both chunks. The system prompt requires surfacing disagreement explicitly and citing both sources rather than picking one. Eval cases `conflict_title_*` check this.

**Gap:** no information about spoken languages or salary. Unanswerable questions must refuse.

## Redactions / synthetic policy

- All biographical content is synthetic (labelled in front matter and this README).
- Phone, email, and home address are omitted on purpose.
- Employer names are fictional; resemblance to real firms is coincidental.
