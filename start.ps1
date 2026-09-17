# Resume AI Assistant — one-command start (Windows PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host " Resume AI Assistant - starting..." -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found. Install Python 3.11+ and try again." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

& ".venv\Scripts\Activate.ps1"

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip | Out-Null
python -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
    Write-Host "Add GEMINI_API_KEY to .env for Gemini answers (optional for local demo)." -ForegroundColor Yellow
}

if (-not (Test-Path "knowledge\index\chunks.json")) {
    Write-Host "Building knowledge index..."
    python -m src.ingest
}

Write-Host ""
Write-Host " Opening http://127.0.0.1:8000" -ForegroundColor Green
Write-Host " Keep this window open. Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

Start-Process "http://127.0.0.1:8000"
python -m src.webapp
