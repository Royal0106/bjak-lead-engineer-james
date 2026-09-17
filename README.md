# Resume AI Assistant

Upload a resume, ask questions, generate interview questions. Answers stay grounded in the file.

## Run (easiest)

**Windows:** double-click `start.bat`  
(or in PowerShell: `.\start.ps1`)

That’s it. The script will:
1. create `.venv` if needed  
2. install dependencies  
3. create `.env` if missing  
4. build the knowledge index if needed  
5. open **http://127.0.0.1:8000**

Optional: edit `.env` and set `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/apikey) for stronger Gemini answers.

## Use the app

1. Click **Upload resume** (PDF / DOCX / TXT / MD)
2. Ask about experience, skills, projects
3. Or ask: `Generate interview questions based on this resume.`

Off-topic questions get: `I can help you based on resume`

## Other commands

```powershell
.\.venv\Scripts\Activate.ps1
python main.py                          # CLI chat
python -m eval.run_eval                 # evaluation suite
python -m src.ingest                    # rebuild index after editing seed sources
```

macOS / Linux: `chmod +x start.sh && ./start.sh`

## Architecture

```
Upload resume → extract text → chunk + TF-IDF index
Ask → retrieve resume chunks → Gemini answer (local fallback if needed)
Interview-question ask → Gemini generates questions from the resume only
```

- Secrets in `.env` (not committed)
- Uploaded files in `knowledge/uploads/` (gitignored)
- Design notes: `docs/architecture.md`, `docs/decisions.md`
