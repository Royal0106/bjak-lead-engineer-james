# Architecture

Production path is simple and intentional:

```
Upload resume (PDF/DOCX/TXT/MD)
        ↓
Extract text → save knowledge/uploads/active_resume.md
        ↓
Chunk + TF-IDF index (local, reviewable)
        ↓
User question
   ├─ greeting → welcome
   ├─ off-topic → "I can help you based on resume"
   ├─ interview questions → Gemini (resume-grounded list)
   └─ resume QA → retrieve chunks → Gemini JSON answer
```

When an uploaded resume is present, retrieval prefers `uploaded_resume` so seed demo sources do not leak into answers.

## Why this shape

| Choice | Rejected | Why |
|--------|----------|-----|
| Upload + re-index | Only hard-coded CV | Matches production use: any resume |
| TF-IDF retrieve + Gemini generate | Fine-tune | Provenance, no invented employers |
| Clean product answers | Debug banners / score dumps | Recruiter UX; engineering detail stays in docs/eval |
| Exact off-topic copy | Long refuse essays | Clear scope boundary |

## Failure paths

- Gemini unavailable → local extractive answer from retrieved resume text (still no invention)
- No relevant resume content / off-topic → `I can help you based on resume` or “I don't have that in the resume.”
- Upload parse failure → clear HTTP 400, no stack trace in UI

## Security

- `GEMINI_API_KEY` in `.env` only
- Uploaded resumes gitignored under `knowledge/uploads/`
- Resume text is sent to Gemini as prompt context when generation runs
