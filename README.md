# Resume AI Assistant

A simple chat app that **studies an uploaded resume** and answers as that candidate.

Ask about skills, experience, projects, or education.  
It can also generate interview practice questions.

Answers stay honest: facts come from the resume. If something is not listed, it says so instead of inventing.

---

## What you need

- **Python 3.11+**
- A browser
- Optional but recommended: a **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey)

Without a Gemini key, the app still runs using local resume matching (less fluent answers).

---

## Quick start (Windows)

1. Double-click **`start.bat`**  
   (or in PowerShell run: `.\start.ps1`)
2. Wait until the browser opens **http://127.0.0.1:8000**
3. Click **Upload resume** (PDF, DOCX, TXT, or MD)
4. Ask a question, for example:
   - `Introduce yourself`
   - `What technologies do you use?`
   - `Generate interview questions`

That is all you need for local use.

### What `start.bat` does for you

1. Creates a virtual environment (`.venv`) if needed  
2. Installs dependencies  
3. Creates `.env` from `.env.example` if missing  
4. Builds the knowledge index if needed  
5. Starts the web app and opens it in your browser  

---

## Add Gemini (better answers)

1. Get an API key: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Open the `.env` file in the project root
3. Set:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
FORCE_LOCAL_SYNTH=0
```

4. Restart the app (`start.bat` again)

**Tips**

- Prefer **Flash** models (`gemini-2.0-flash` or `gemini-2.5-flash`) for free-tier quota.
- If you see weak or “list-like” answers, the key may be out of quota (HTTP 429). Create a new key or wait and retry.

---

## How to use the app

| Step | Action |
|------|--------|
| 1 | Upload a resume |
| 2 | Ask about **that person** (skills, projects, education, metrics) |
| 3 | Or ask for **interview questions** |

Example questions:

- `Introduce yourself.`
- `What cloud platforms have you worked with?`
- `Describe your React experience.`
- `What measurable improvements have you achieved?`
- `What university did you graduate from?`
- `Generate interview questions I might get asked.`

The assistant answers in **first person** as the candidate on the resume.

---

## macOS / Linux

```bash
chmod +x start.sh
./start.sh
```

Then open **http://127.0.0.1:8000**

---

## Deploy on Vercel

1. Push this project to GitHub
2. Import the repo in [Vercel](https://vercel.com)
3. Add environment variables:

| Name | Value |
|------|--------|
| `GEMINI_API_KEY` | your Gemini key |
| `GEMINI_MODEL` | `gemini-2.0-flash` (recommended) |

4. Deploy

**Notes for Vercel**

- Uploaded resumes are kept in browser session storage and sent with each question (serverless hosts do not keep files permanently).
- Max upload size is about **4MB** on Vercel.
- Set the Gemini key in Vercel → Project → Settings → Environment Variables, then redeploy.

---

## Project layout (simple view)

```text
main.py                 CLI entry + exports the web app for Vercel
start.bat / start.ps1   One-click run on Windows
start.sh                One-click run on macOS/Linux
src/
  webapp.py             Web UI + API
  assistant.py          Chat logic (Gemini + resume fallback)
  resume_store.py       Upload / extract resume text
  retrieve.py           Search resume chunks
  gemini_client.py      Gemini API calls
web/static/             Frontend (HTML, CSS, JS)
knowledge/              Local index + uploads
.env                    Your secrets (do not commit)
```

---

## Other useful commands

Activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
# CLI chat
python main.py

# Rebuild the local search index
python -m src.ingest

# Run evaluation suite
python -m eval.run_eval
```

---

## How answers work

```text
Upload resume
    → extract text
    → (optional) build search index

Ask a question
    → Gemini studies the resume and answers as the candidate
    → If Gemini is unavailable, local resume matching is used
    → If the fact is not on the resume → honest “not listed” reply
```

The app will **not** invent certifications, schools, or metrics that are not on the resume.

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Page will not open | Run `start.bat` again; check http://127.0.0.1:8000 |
| Upload fails | Use PDF/DOCX/TXT/MD under 8MB (4MB on Vercel) |
| Answers look like raw resume dumps | Redeploy/restart after latest code; set a working Gemini key |
| “Server error” or empty answers | Check `GEMINI_API_KEY`; free-tier quota may be exhausted |
| Vercel upload works but ask forgets resume | Keep the same browser tab (session storage holds the resume text) |

---

## Config reference (`.env`)

| Variable | Meaning |
|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Model name (use a Flash model) |
| `FORCE_LOCAL_SYNTH` | `1` = offline only, no Gemini |
| `RETRIEVAL_TOP_K` | How many resume chunks to retrieve |
| `DATA_DIR` | Optional writable folder (used on serverless) |

Copy from `.env.example` if `.env` is missing.

---

## Docs

- Architecture notes: `docs/architecture.md`
- Design decisions: `docs/decisions.md`
