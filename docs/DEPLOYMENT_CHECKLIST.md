# AgriMind Production Deployment Checklist & Runbook

This document details the exact pre-flight checks, cloud deployment steps, verification procedures, and operational guidelines for deploying AgriMind to production.

---

## 1. Pre-Flight Verification Checklist

Before pushing code or provisioning infrastructure, ensure all local automated verifications pass:

- [ ] **Backend Tests**: Run `pytest` inside the backend environment. All 127 tests must pass without errors.
  ```bash
  cd backend
  .\.venv\Scripts\pytest -v
  ```
- [ ] **Frontend Production Build**: Execute Vite compilation to ensure zero syntax or bundle errors:
  ```bash
  cd frontend
  npm run build
  ```
- [ ] **Git Secret Audit**: Confirm that no `.env`, SQLite databases (`agrimind.db`), vector stores (`vector_db/`), or upload caches are tracked:
  ```bash
  git status --ignored
  ```
- [ ] **CORS Origins**: Note the planned public frontend URL (e.g., `https://agrimind.vercel.app`) to inject into backend `CORS_ORIGINS`.

---

## 2. Infrastructure Architecture & Service Topology

| Component | Recommended Production Provider | Alternative | Build / Start Command | Required Env Vars |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | **Vercel** (Static SPA) | Netlify / Render Static / Cloudflare Pages | `npm run build` (output: `dist`) | `VITE_API_BASE_URL` (Build-time) |
| **Backend** | **Render** (Python Web Service) | Railway / Fly.io / GCP Cloud Run | `pip install -r requirements.txt && alembic upgrade head && python -m app.rag.index_knowledge`<br>`uvicorn app.main:app --host 0.0.0.0 --port $PORT` | `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `FRONTEND_ORIGIN` |
| **Database** | **Render Managed PostgreSQL** | Supabase / Neon / AWS RDS | Automatic managed PostgreSQL 16 | `DATABASE_URL` (Automatic linking) |
| **Vector DB** | **Embedded ChromaDB** | Persistent Disk / Ephemeral self-healing | Pre-built during image build or self-healed on startup via `ensure_indexed()` | `CHROMA_PERSIST_DIR` |
| **Weather** | **Open-Meteo API** | Open-Meteo Public | Free tier REST requests | None required |

---

## 3. Step-by-Step Cloud Deployment

### A. Deploy Managed PostgreSQL (e.g. Render / Supabase)
1. In your cloud console, create a new PostgreSQL instance named `agrimind-db`.
2. Copy the **Internal Connection String** (if backend is in the same cloud region) or **External Connection String**.
3. Format: `postgresql://user:password@host:5432/database`.

### B. Deploy Backend Web Service (Render / Railway / Cloud Run)
1. Create a new Web Service pointing to your AgriMind repository root or `backend` subdirectory.
2. Select **Python 3.12** runtime.
3. Set **Build Command**:
   ```bash
   pip install -r requirements.txt && alembic upgrade head && python -m app.rag.index_knowledge
   ```
4. Set **Start Command**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Set **Health Check Path**: `/health` (or `/api/health`).
6. Configure the following **Environment Variables**:
   - `DATABASE_URL`: Your PostgreSQL connection string.
   - `JWT_SECRET_KEY`: A 32+ character random hex string (`openssl rand -hex 32`).
   - `JWT_ALGORITHM`: `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440` (24 hours).
   - `CORS_ORIGINS`: Comma-separated list including your planned frontend domain (e.g., `https://agrimind.vercel.app,http://localhost:5173`).
   - `FRONTEND_ORIGIN`: `https://agrimind.vercel.app`.
   - `CHROMA_PERSIST_DIR`: `/tmp/vector_db` (or mount a persistent disk at `/app/vector_db`).
   - `UPLOAD_DIR`: `/tmp/uploads`.
   - `OPENAI_API_KEY`: *(Optional)* Your server-side OpenAI key if enabling AI explanations.
   - `GEMINI_API_KEY`: *(Optional)* Your server-side Google Gemini key for failover.
7. Trigger deployment and observe the build logs:
   - Verify `alembic upgrade head` applies all database migrations.
   - Verify ChromaDB indexes 26+ agricultural knowledge chunks.
   - Verify Uvicorn starts and `/health` returns `HTTP 200 {"status": "healthy"}`.
8. Note your public backend URL: `https://your-agrimind-backend.onrender.com`.

### C. Deploy Frontend (Vercel / Netlify)
1. In Vercel, click **Add New Project** and import the AgriMind repository.
2. Set **Root Directory** to `frontend`.
3. Set **Framework Preset** to `Vite`.
4. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: The public URL of your deployed backend (e.g., `https://your-agrimind-backend.onrender.com`).
5. Ensure `frontend/vercel.json` is present in the repository to guarantee client-side route rewrites.
6. Click **Deploy**.
7. Once deployed, note your public frontend URL: `https://agrimind.vercel.app`.

### D. Update Backend CORS
1. Return to your backend settings (e.g. on Render) and ensure `CORS_ORIGINS` includes the exact URL assigned by Vercel (`https://agrimind.vercel.app`).
2. Redeploy or restart the backend to apply origin changes.

---

## 4. Post-Deployment Smoke Test (Live Verification Protocol)

Perform these steps on the live production frontend:

1. **Health Verification**:
   - Visit `https://[backend-domain]/health` -> Should return HTTP 200 with status `healthy`.
   - Visit `https://[backend-domain]/docs` -> FastAPI OpenAPI Swagger interactive documentation.
2. **Soil Report Ingestion**:
   - Navigate to the live frontend homepage.
   - Upload `sample_data/soil_report_sample_1.pdf` (or your valid soil test report).
   - Confirm parsing completes and presents extracted Nitrogen, Phosphorus, Potassium, pH, OC, and EC with review badges.
3. **Recommendation & Runoff Analysis**:
   - Select a target crop (e.g., `wheat`) and enter location (e.g., `Pune, Maharashtra`).
   - Click **Generate Complete Advisory**.
   - Verify crop suitability scores, specific fertilizer doses, and weather runoff spray window ("Spray / Wait / Caution").
4. **Multilingual Interaction**:
   - Toggle language to Hindi (हिंदी) and Marathi (मराठी).
   - Verify interface labels, advisory highlights, and text assistant respond accurately.
5. **Persistence & User Isolation**:
   - Click **Sign In** -> **Create Account** and register a new test user.
   - Click **Save Report to Account**.
   - Navigate to **Saved Reports**; confirm the report is listed.
   - Log out, create a second user, and confirm the second user cannot see the first user's saved data (cross-user isolation).

---

## 5. Security & Operational Rules

1. **No Frontend Secrets**:
   Never inject database credentials, JWT secrets, or LLM API keys into `VITE_*` environment variables. Vite injects variables directly into browser JavaScript where anyone can read them.
2. **Safe Fallbacks**:
   If LLM keys expire, run out of quota, or fail, AgriMind automatically activates the deterministic template explainer. Agricultural calculations are never halted or hallucinated.
3. **ChromaDB on Ephemeral Storage**:
   On stateless cloud tiers where local disk is wiped on restart, AgriMind automatically checks the ChromaDB vector count on boot (`ensure_indexed()`). If the store is empty, it indexes the bundled knowledge markdown files in ~2 seconds with zero human intervention.
4. **Agricultural Disclaimer & KVK Escalation**:
   Every AgriMind advisory includes a mandatory disclaimer:
   > *"AgriMind provides decision-support guidance grounded in university and ICAR research. It does not replace field inspection by certified agronomists or your local Krishi Vigyan Kendra (KVK). Always test soil regularly and follow local regulations."*
