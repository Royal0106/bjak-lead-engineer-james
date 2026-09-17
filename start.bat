@echo off
setlocal
cd /d "%~dp0"

echo.
echo  Resume AI Assistant - starting...
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11+ and try again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create .venv
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"

echo Installing dependencies...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install requirements.
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example
  echo Edit .env and set GEMINI_API_KEY, then run start.bat again for Gemini answers.
)

if not exist "knowledge\index\chunks.json" (
  echo Building knowledge index...
  python -m src.ingest
)

echo.
echo  Opening http://127.0.0.1:8000
echo  Keep this window open while using the app.
echo  Press Ctrl+C to stop.
echo.

start "" "http://127.0.0.1:8000"
python -m src.webapp

pause
