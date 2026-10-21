# AgriMind 🌾

**Multi-Agent AI Soil, Crop & Fertilizer Optimization System for Farmers**

AgriMind helps farmers make evidence-grounded decisions by analyzing soil health test reports (PDFs), ranking suitable crops, recommending organic and chemical fertilizer amendments, and assessing live weather forecasts to recommend the safest application windows.

---

## 📌 Architectural Rule: Trustworthy AI

> **"The deterministic engine calculates; the AI explains."**

Agricultural calculations must never hallucinate. In AgriMind:
- Nutrient status (LOW / MEDIUM / HIGH), deficiency identification, and crop suitability scores are calculated using **pure Python deterministic rules** matching official Soil Health Card thresholds.
- The AI (LLM) is used **only** to synthesize explanations in plain, supportive language (English, Hindi, Marathi).
- If no LLM API key is provided, AgriMind automatically falls back to built-in translated phrase templates — the app remains **100% functional without an AI key**.
- **Pesticide Safety Guardrail:** The system intentionally does **not** invent chemical pesticide dosages or products.
- **Agricultural Disclaimer:** AgriMind provides decision-support tools based on published agronomic research. It does not replace on-field advisory by certified agronomists or your local Krishi Vigyan Kendra (KVK).

```
Soil Report (PDF) ──► PyMuPDF Extractor ──► Deterministic Soil Parser
                                                     │
                                                     ▼
                                            Agent Orchestrator
                                            ├── Agent 1: Soil & Crop Specialist (Rules + RAG)
                                            └── Agent 2: Weather & Timing Specialist (Open-Meteo)
                                                     │
                                                     ▼
                                            Deterministic Engine
                                            (Deficiencies, Crop Scores, Application Window)
                                                     │
                                                     ▼
                                            Explanation Layer
                                            (OpenAI ➔ Gemini ➔ OpenRouter ➔ Template Fallback)
                                                     │
                                                     ▼
                                            Interactive React Frontend
                                            (Soil Core Horizon, Weather, Evidence, Voice Chat)
                                                     │
                                                     ▼
                                            PostgreSQL Persistence
                                            (Saved Reports, User Accounts, JWT Security)
```

---

## 🚀 Quick Start & Prerequisites

### Prerequisites
Before running AgriMind locally, ensure you have:
1. **Python 3.12** (64-bit recommended). Download from [python.org](https://www.python.org/downloads/release/python-3129/).
   - *Important for Windows:* During installation, check the box **"Add python.exe to PATH"**.
2. **Node.js (v18 or v20 LTS)**. Download from [nodejs.org](https://nodejs.org/).
3. **Microsoft C++ Build Tools (Windows only):** Required by `chromadb` / `chroma-hnswlib`. If you encounter build errors during `pip install`, download the Build Tools from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and select the **"Desktop development with C++"** workload.
4. *(Optional)* **Docker & Docker Desktop** if running the full stack with PostgreSQL via containers.

---

## 💻 Running Locally

### Option A: Automated Setup Script (Windows PowerShell)

From PowerShell inside the `agrimind` directory:
```powershell
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```
This script will:
- Check for Python 3.12 and Node.js.
- Create `backend\.venv` and install all backend requirements.
- Copy `.env.example` to `backend\.env`.
- Apply Alembic database migrations.
- Index the agronomic knowledge base into ChromaDB.
- Run the full backend test suite (`pytest`).
- Run `verify_setup.py` against `sample_data/Soil_Test_Report_Demo_Farm.pdf`.
- Install frontend dependencies (`npm install`).

### Option B: Manual Setup (Step-by-Step)

#### 1. Backend Setup
Open a terminal in the project root:
```powershell
# Navigate to backend directory
cd backend

# Create Python 3.12 virtual environment
py -3.12 -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create your local environment configuration
Copy-Item .env.example .env

# Run database migrations (creates SQLite or connects to Postgres)
alembic upgrade head

# Build the vector database knowledge index (idempotent)
python -m app.rag.index_knowledge

# Run the test suite (127 tests)
pytest -v

# Run the backend server
uvicorn app.main:app --reload --port 8000
```
- Backend API Docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- System Information & Capabilities: [http://localhost:8000/api/info](http://localhost:8000/api/info)

#### 2. Frontend Setup
Open a **second** terminal window:
```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev

# Or test production build
npm run build
```
- Frontend Web App: [http://localhost:5173](http://localhost:5173)
- Configured via `VITE_API_BASE_URL` in `frontend/.env.local` (defaults to `http://localhost:8000`)
- Features live real-time backend connection status badge with retry and graceful offline handling

---

## 🐳 Running with Docker Compose (Full-Stack + PostgreSQL)

AgriMind includes a complete Docker Compose setup with managed PostgreSQL 16, FastAPI backend, and Vite React frontend:

```bash
# 1. Copy root environment template
cp .env.example .env

# 2. Build and start containers
docker compose up --build
```
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- PostgreSQL: `localhost:5432` (`agrimind_db`)

---

## 🌐 Production Deployment Guide

For complete, step-by-step instructions and live smoke-testing protocols, see **[DEPLOYMENT_CHECKLIST.md](file:///c:/agrimind/docs/DEPLOYMENT_CHECKLIST.md)**.

### Separate Deployment Architecture

```
Frontend (Vercel / Static Hosting)
   │
   ▼ HTTPS REST / JSON
Backend (Render / Railway / Cloud Run)
   ├── SQLite / Managed PostgreSQL (Alembic)
   ├── ChromaDB Vector Index (Pre-built + Auto-healing on boot)
   └── Open-Meteo Weather API
```

### 1. Frontend (Vercel)
- **Root Directory:** `frontend`
- **Framework Preset:** `Vite`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **SPA Rewrites:** Pre-configured in `frontend/vercel.json`
- **Build-Time Environment Variable:**
  - `VITE_API_BASE_URL`: `https://your-backend.onrender.com`

### 2. Backend (Render / Railway / Docker)
- **Runtime:** Python 3.12 (or Docker using `backend/Dockerfile`)
- **Build Command:**
  ```bash
  pip install -r requirements.txt && alembic upgrade head && python -m app.rag.index_knowledge
  ```
- **Start Command:**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- **Health Check Path:** `/health`
- **Infrastructure as Code:** Pre-configured in `render.yaml`

---

## 🔑 Environment Variables & Security Model

AgriMind strictly separates **Build-Time Client Variables** from **Runtime Server Secrets**:

### Frontend Build-Time Configuration (`frontend/.env.example`)
*Note: These values are compiled into client-side JavaScript. NEVER store secrets here.*
- `VITE_API_BASE_URL`: Full URL of the backend API (e.g., `https://agrimind-api.onrender.com`).

### Backend Runtime Secrets (`backend/.env.example`)
*Note: These values stay strictly confidential on the server.*
- `DATABASE_URL`: PostgreSQL connection string (or `sqlite:///./agrimind.db` for local dev).
- `JWT_SECRET_KEY`: Cryptographic signing secret (generate with `openssl rand -hex 32`).
- `CORS_ORIGINS`: Comma-separated allowed frontend domains (e.g., `https://agrimind.vercel.app`).
- `FRONTEND_ORIGIN`: Primary frontend URL.
- `CHROMA_PERSIST_DIR`: Directory path for ChromaDB vector embeddings.
- `UPLOAD_DIR`: Directory path for temporary PDF processing.
- `OPENAI_API_KEY`: *(Optional)* Primary LLM provider key.
- `GEMINI_API_KEY`: *(Optional)* Secondary LLM provider key.
- `OPENROUTER_API_KEY`: *(Optional)* Tertiary failover provider key.

---

## 🧪 Automated Testing & Verification

AgriMind maintains strict automated test coverage across all features:

```powershell
# Run backend test suite (127 tests)
cd backend
.\.venv\Scripts\pytest -v

# Run laboratory benchmark verification against official demo PDF
python verify_setup.py

# Test frontend production build
cd frontend
npm run build
```

---

## ⚠️ Known Limitations & Disclaimers

1. **Browser Speech Recognition:** Browser-native speech recognition (`webkitSpeechRecognition`) is supported primarily in Google Chrome, Chromium browsers, and Microsoft Edge. In Firefox and Safari, farmers can use text input with full Hindi, Marathi, and English support.
2. **Ephemeral Cloud Storage:** On free/stateless cloud containers, local storage resets on restart. AgriMind solves this through an automatic boot hook (`ensure_indexed()`) that indexes knowledge documents into ChromaDB in ~2 seconds whenever the database is empty.
3. **Field Expert Consultation:** AgriMind recommendations are calculated strictly according to ICAR and university agronomic guidelines. Soil conditions may vary due to micro-climates, salinity, or drainage; always consult your local **Krishi Vigyan Kendra (KVK)** before large-scale fertilizer application.

---

## 📚 Project Documentation

- [DEPLOYMENT_CHECKLIST.md](file:///c:/agrimind/docs/DEPLOYMENT_CHECKLIST.md) — Production deployment checklist, smoke test runbook, and verification steps.
- [DATABASE_MIGRATION_GUIDE.md](file:///c:/agrimind/docs/DATABASE_MIGRATION_GUIDE.md) — Alembic schema migration reference.
- [SPEECH_RECOGNITION_ASSESSMENT.md](file:///c:/agrimind/docs/SPEECH_RECOGNITION_ASSESSMENT.md) — Browser speech runtime capabilities and evaluation.
- [ARCHITECTURE.md](file:///c:/agrimind/ARCHITECTURE.md) — System architecture, data flow, and components.
- [PROJECT_STATUS.md](file:///c:/agrimind/PROJECT_STATUS.md) — Current implementation roadmap and completed phases.
- [AGENT_HANDOFF.md](file:///c:/agrimind/AGENT_HANDOFF.md) — Engineering handoff notes.
