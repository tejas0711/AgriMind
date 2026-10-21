# AgriMind — Windows from-scratch setup script
#
# Run this from PowerShell, from inside the extracted `agrimind` folder:
#   powershell -ExecutionPolicy Bypass -File setup_windows.ps1
#
# This script checks for (but does not silently auto-install) the heavy
# prerequisites — Python 3.12, Node.js, and the C++ Build Tools needed by
# chroma-hnswlib — and tells you exactly what to install if they're
# missing, before doing the actual project setup.

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

Write-Step "Checking prerequisites"

# --- Python 3.12 ---
$pythonOk = $false
try {
    $pyVersion = & py -3.12 --version 2>$null
    if ($pyVersion) { $pythonOk = $true; Write-Host "Found: $pyVersion" }
} catch {}

if (-not $pythonOk) {
    Write-Host "Python 3.12 was not found via the 'py' launcher." -ForegroundColor Yellow
    Write-Host "Install it from https://www.python.org/downloads/release/python-3129/"
    Write-Host "(pick the Windows installer, and tick 'Add python.exe to PATH')."
    Write-Host "Re-run this script after installing."
    exit 1
}

# --- Node.js ---
if (-not (Test-Command "node")) {
    Write-Host "Node.js was not found." -ForegroundColor Yellow
    Write-Host "Install the LTS version from https://nodejs.org/ then re-run this script."
    exit 1
} else {
    Write-Host "Found Node: $(node --version)"
}

# --- C++ Build Tools (needed by chroma-hnswlib) ---
# There's no reliable one-line check for this from PowerShell, so we just
# warn up front since it's the single most common install failure on
# Windows for this project (per your own earlier notes).
Write-Host ""
Write-Host "NOTE: chromadb depends on 'chroma-hnswlib', which needs Microsoft" -ForegroundColor Yellow
Write-Host "C++ Build Tools to compile on Windows. If 'pip install -r requirements.txt'" -ForegroundColor Yellow
Write-Host "fails below with an error mentioning 'Microsoft Visual C++ 14.0 or greater'," -ForegroundColor Yellow
Write-Host "install Visual Studio Build Tools with the 'Desktop development with C++'" -ForegroundColor Yellow
Write-Host "workload from https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Yellow
Write-Host "then re-run this script." -ForegroundColor Yellow

Write-Step "Setting up backend virtual environment"
Set-Location backend

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
    Write-Host "Created .venv"
} else {
    Write-Host ".venv already exists, reusing it"
}

& .\.venv\Scripts\Activate.ps1

Write-Step "Upgrading pip and installing backend requirements (this can take a few minutes)"
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Step "Setting up environment variables"
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend\.env from .env.example."
    Write-Host "IMPORTANT: open backend\.env now and set OPENAI_API_KEY to a real key" -ForegroundColor Yellow
    Write-Host "if you want real LLM explanations instead of the templated fallback." -ForegroundColor Yellow
} else {
    Write-Host "backend\.env already exists, leaving it as-is"
}

Write-Step "Building the RAG knowledge index"
python -m app.rag.index_knowledge

Write-Step "Running backend test suite"
pytest -v

Write-Step "Running the parser self-check against the sample soil report"
python ..\verify_setup.py

Set-Location ..

Write-Step "Setting up frontend"
Set-Location frontend
npm install
Set-Location ..

Write-Step "Setup complete"
Write-Host ""
Write-Host "To run the app now, open TWO PowerShell windows:" -ForegroundColor Green
Write-Host ""
Write-Host "  Window 1 (backend):"
Write-Host "    cd backend"
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host "    uvicorn app.main:app --reload --port 8000"
Write-Host ""
Write-Host "  Window 2 (frontend):"
Write-Host "    cd frontend"
Write-Host "    npm run dev"
Write-Host ""
Write-Host "Then open http://localhost:5173 and upload sample_data\Soil_Test_Report_Demo_Farm.pdf"
Write-Host "to confirm Organic Carbon shows LOW (0.45%), not UNKNOWN."
