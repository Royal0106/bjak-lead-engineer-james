# Engineering leadership, cuts, AI use, self-review

## What was cut (inside the time box)

- Web UI, streaming tokens, conversation memory
- Hosted vector DB, reranker model, agent/tool loop
- Continuous CI eval and dashboards
- Multi-lingual sources

**Why cut:** none of these prove grounding better than retrieval threshold + citation filter + a real eval table. Next three things: (1) add a tiny web UI that reuses `Assistant.ask`, (2) wire eval into CI on source changes, (3) replace synthetic CV with a redacted real one and re-baseline metrics.

## Where AI was used

- Scaffolding ideas for dataset categories and README structure (reviewed and rewritten).
- First draft of synthetic CV bullet metrics — **manually edited** so numbers stay consistent across `cv.md` / `projects.md`.
- **Not left to a model:** pass-bar thresholds, conflict policy (CV wins as formal title but both must be shown), refusal copy, and which eval cases count as adversarial.

## Self-review (if this were someone else's PR)

1. Add a golden-file test that does not call the API: given frozen retrieved chunks, assert the prompt builder + refusal paths.
2. Re-baseline eval with a working Gemini key in a supported region — the committed 100% scores are on the local synthesizer; model phrasing will move conflict/ambiguous rows.

## Note on Gemini availability in this environment

The provided API key could not complete `generateContent` here (`NOT_FOUND` on tried Flash models / `FAILED_PRECONDITION` on `models.list` for user location). The system is designed so that failure does not invent facts: retrieval still runs, and `src/local_synth.py` answers only from retrieved chunks or refuses. Rotate the key if it was pasted into chat.
