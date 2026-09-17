# Decision record

## D1 — RAG with hard refuse vs chat-over-full-CV

- **Decision:** Retrieve top-k chunks; refuse below threshold.
- **Rejected:** Stuff the entire CV into the prompt every time.
- **Constraint:** Full-prompt works at this corpus size but does not demonstrate retrieval, scoring, or "what happens when evidence is missing." Threshold refusal is the behaviour we need to prove.

## D2 — Synthetic labelled corpus vs waiting on a real CV

- **Decision:** Ship a clearly labelled synthetic profile (Jordan Hale).
- **Rejected:** Block the exercise on personal data export.
- **Evidence:** Brief explicitly allows synthetic material; pipeline quality is the graded object.

## D3 — Deterministic label eval primary; LLM-as-judge optional

- **Decision:** Score with `must_include` / `must_never_claim` / refusal checks in code.
- **Rejected:** LLM-as-judge as the only metric.
- **Constraint:** Judges drift and need a safeguard. Prompt committed in `eval/judge_prompt.md` for optional use; primary numbers are recomputable.

## D4 — CLI with visible sources vs polished chat UI

- **Decision:** Rich CLI that always prints sources and fallback reason.
- **Rejected:** Streamlit/chat skin first.
- **Constraint:** Brief prefers sources over polish; 15 minutes UX budget.

## D5 — Gemini Flash + local TF-IDF

- **Decision:** `gemini-2.0-flash` (with fallbacks) for generation; local TF-IDF for retrieval.
- **Rejected:** Gemini embeddings for this corpus; local-only GGUF for the submission path.
- **Evidence:** Reviewer runs with one API key for synthesis; retrieval stays offline/reproducible. Switch to dense embeddings if paraphrased questions miss too often after lexical boost.
