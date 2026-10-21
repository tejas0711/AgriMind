# AgriMind — Implementation Plan & Phase Roadmap

This document outlines the systematic, step-by-step roadmap for developing, refining, and testing AgriMind. Each phase builds upon the previous one with clear dependencies and acceptance criteria.

---

## Roadmap Overview

```
Phase 0: Repository Audit & Foundation (DONE)
   │
   ▼
Phase 1: Frontend & Visual Design (DONE)
   │
   ▼
Phase 2: FastAPI Backend Foundation & Frontend Integration (DONE)
   │
   ▼
Phase 3: Soil Report PDF Processing (DONE)
   │
   ▼
Phase 4: Deterministic Agricultural Recommendation Engine (DONE)
   │
   ▼
Phase 5: Weather Agent & Multi-Agent Orchestration (DONE)
   │
   ▼
Phase 6: Agricultural RAG & Grounded LLM Explanations (DONE)
   │
   ▼
Phase 7: Hindi & Marathi Voice Assistant (DONE)
   │
   ▼
Phase 8: Optional PostgreSQL Persistence and User Accounts (DONE)
   │
   ▼
Phase 9: Production Readiness and Deployment (DONE)
```

---

## Phase 0: Repository Audit & Foundation (COMPLETED)

- [x] Inspect all backend modules, models, engines, agents, RAG pipelines, and tests.
- [x] Inspect all frontend components, styles, state contexts, and translations.
- [x] Sanitize `backend/.env.example` to remove exposed secrets and replace with safe placeholders.
- [x] Create project-root `.env.example`.
- [x] Generate `PROJECT_STATUS.md` recording verified vs. unverified status.
- [x] Generate `ARCHITECTURE.md` detailing tech choices, folder structure, and data flows.
- [x] Generate `IMPLEMENTATION_PLAN.md` with structured criteria.
- [x] Generate `AGENT_HANDOFF.md` with resumption instructions.
- [x] Review and update `README.md` with beginner-friendly instructions.

---

## Phase 1: Frontend & Visual Design (COMPLETED)

**Objective:** Build a polished, responsive, farmer-friendly AgriMind website with a natural agricultural visual identity and clear editorial layout.

- [x] Establish agricultural visual identity (warm off-white canvas `#faf8f4`, deep forest-green `#18392b`, leaf-green `#456b28`, earth tones, soft restrained shadows).
- [x] Integrate `lucide-react` for consistent iconography (zero emojis as UI controls).
- [x] Build Navigation header (`Navbar.jsx`) with brand identity, mobile drawer, demo toggle, and language switcher.
- [x] Build Landing page (`LandingPage.jsx`) with hero value proposition, 3-step workflow, and architectural guardrails.
- [x] Build Soil analysis workspace (`SoilWorkspace.jsx`) with drag-and-drop PDF upload, location input with quick hubs, crop selector, and organic preference.
- [x] Build Results dashboard (`ResultsDashboard.jsx`) with executive summary metrics, stratified soil core (`SoilCore.jsx`), crop suitability (`RecommendationPanel.jsx`), weather runoff timing (`WeatherPanel.jsx`), and grounded citations (`WhyPanel.jsx`).
- [x] Build Farmer assistant panel (`AssistantPage.jsx`) with suggested question chips, microphone speech-to-text integration, and speech-synthesis read-aloud button.
- [x] Build Methodology & About section (`MethodologyPage.jsx`) with Soil Health Card standards table, runoff safety rules, and CGIAR citations.
- [x] Create clearly labeled demonstration mode (`demoData.js`) matching certified `Soil_Test_Report_Demo_Farm.pdf` benchmark with unambiguous Demo Mode banner.
- [x] Configure API client (`api.js`) to support `VITE_API_BASE_URL` with fallback to `VITE_API_BASE` and `http://localhost:8000`.
- [x] Expand multilingual dictionaries in `translations.js` for complete English, Hindi, and Marathi coverage.
- [x] Verify production build (`npm run build`) succeeds cleanly with zero errors.

---

## Phase 2: FastAPI Backend Foundation & Frontend Integration (COMPLETED)

**Objective:** Create a reliable FastAPI backend foundation with centralized configuration, structured logging, safe error masking, health/capabilities endpoints, dynamic CORS, and connect the React frontend with a real-time status indicator and robust failure handling.

- [x] Centralize backend settings using `pydantic-settings` (`backend/app/core/config.py`) loading `.env`, typed configurations, and dynamic CORS origins.
- [x] Implement structured logging (`backend/app/core/logging.py`) with ISO-8601 timestamps, log level routing, and third-party log noise suppression.
- [x] Create Pydantic system schemas (`backend/app/models/system.py`) for health, system capabilities, and standardized error responses.
- [x] Implement `GET /api/health` and `GET /api/info` endpoints (`backend/app/api/health.py`) and alias root `/health`.
- [x] Add global exception handlers in `backend/app/main.py` for `HTTPException`, `RequestValidationError`, and generic 500 errors preventing internal stack trace or secret leaks.
- [x] Implement Swagger documentation at `/docs` and `/redoc`.
- [x] Write comprehensive unit tests in `backend/tests/test_api_health.py` verifying health check, capabilities, validation errors, and custom parameters.
- [x] Verify full backend pytest suite passes (40/40 tests pass in 4.52s).
- [x] Run `verify_setup.py` against sample PDF benchmark (100% field completeness and rating accuracy).
- [x] Configure unified API client (`frontend/src/api.js`) supporting `VITE_API_BASE_URL`, 15-second timeouts, AbortController, and typed `ApiError`.
- [x] Connect real-time backend status badge in `frontend/src/components/Navbar.jsx` with loading, online, offline, latency, and click-to-retry capabilities.
- [x] Implement farmer-friendly, transparent backend-unavailable feedback in `SoilWorkspace.jsx` and `App.jsx` without fake concealment.
- [x] Keep demonstration mode strictly separated from live backend mode with explicit benchmark indicators.
- [x] Update developer documentation in `README.md`, `backend/.env.example`, and create `frontend/.env.example`.
- [x] Verify frontend production build succeeds (`npm run build`) in 4.06s.

---

## Phase 3: Soil Report PDF Processing (COMPLETED)

**Objective:** Allow a farmer to upload a soil report PDF, extract 12 supported soil measurements (N, P, K, pH, OC, EC, Zn, Fe, Mn, Cu, S, B) into validated structured data with PyMuPDF, detect scanned image PDFs without invented numbers, and provide an interactive review table on the frontend.

- [x] Implement in-memory PDF stream extraction in `backend/app/services/pdf_service.py` (`extract_pdf_from_bytes()`) avoiding lingering disk storage.
- [x] Detect image-only or scanned PDFs lacking digital text and provide helpful OCR advice.
- [x] Create Pydantic schemas in `backend/app/models/soil.py` (`SoilMeasurement`, `SoilReport`, `SoilParseResponse`).
- [x] Implement tolerant deterministic regex parsing in `backend/app/services/soil_parser.py` capturing value, unit, verbatim source text, and Soil Health Card ratings.
- [x] Add range plausibility checks (pH 3-11, OC 0.02-15%, etc.) and flag out-of-bounds metrics with `needs_review`.
- [x] Implement `POST /api/soil/parse` and backward-compatible `POST /api/soil/upload` with upload size limits (10MB) and non-PDF rejection.
- [x] Add automated unit and integration tests in `backend/tests/test_api_soil.py` and `backend/tests/test_soil_parser.py` (50/50 tests pass).
- [x] Verify `verify_setup.py` passes at 100% field completeness and rating accuracy.
- [x] Connect frontend `SoilWorkspace.jsx` to `POST /api/soil/parse` with animated PyMuPDF extraction feedback.
- [x] Build interactive Review & Edit Table in `SoilWorkspace.jsx` enabling in-place value and unit adjustments.
- [x] Maintain clear visual audit distinction between extracted data (green) and user-edited data (blue).
- [x] Provide report removal and re-upload capabilities.
- [x] Verify frontend production build succeeds (`npm run build`) in 3.27s.

---

## Phase 4: Deterministic Agricultural Recommendation Engine (COMPLETED)

**Objective:** Build and validate the core deterministic recommendation engine in pure Python, evaluating crop suitability and fertilizer/soil amendment options strictly from validated soil measurements and documented agricultural rules without relying on an LLM for calculations.

- [x] Implement deterministic soil nutrient & property classifier in `backend/app/engine/soil_classifier.py` following official Indian Soil Health Card (2015) and ICAR standards for 12 parameters (N, P, K, OC, pH, EC, Zn, Fe, S, B, Cu, Mn).
- [x] Support unit normalization and conversion (`kg/ha`, `ppm`, `lbs/acre`, `%`, `g/kg`, `dS/m`, `mS/cm`).
- [x] Provide granular agronomic implications for both DEFICIENT / LOW and EXCESSIVE / HIGH nutrient values.
- [x] Build deterministic crop suitability scoring in `backend/app/engine/crop_scorer.py` (0-100 scale, suitability categories, positive factors, limiting constraints, missing factor tracking, and legume nitrogen-fixation awareness).
- [x] Curate fertilizer & organic amendment knowledge base in `backend/data/knowledge/fertilizer/fertilizer_options.json` with purposes, application notes, cautions, rule sources, and provisional flags.
- [x] Enforce multi-layer contradiction detection in `backend/app/engine/fertilizer_optimizer.py` (high nutrient blocking, user query conflict detection, lime on alkaline soil blocking, and legume nodulation safeguards).
- [x] Strict safety boundary: Guarantee ZERO chemical pesticide recommendations.
- [x] Create standalone deterministic pipeline entry point in `backend/app/engine/recommendation_engine.py` (`evaluate_recommendations()`) callable without LLM or network dependencies.
- [x] Expose primary endpoint `POST /api/recommendations` and alias `POST /api/recommendation` returning structured `RecommendationResponse`.
- [x] Connect frontend `RecommendationPanel.jsx`, `WhyPanel.jsx`, and `ResultsDashboard.jsx` to display categories, positive/limiting factors, missing property warnings, rule sources, and provisional advisory disclaimers.
- [x] Write 19 comprehensive unit tests in `backend/tests/test_recommendation_engine.py` (thresholds, units, missing data, crop scoring, contradictions, determinism, and endpoints).
- [x] Demonstrate determinism: identical inputs and rules produce 100% identical outputs across runs.
- [x] Verify full test suite passes (69/69 backend tests pass; `verify_setup.py` benchmark passes 100%; frontend compiles cleanly).

---

## Phase 5: Weather Agent & Multi-Agent Orchestration (COMPLETED)

**Objective:** Integrate live weather data from Open-Meteo for geocoding and forecasting, implement agronomic application-window rules, create simple domain agents with transparent multi-agent orchestration, and report partial failures without fabricating weather numbers.

- [x] Implement `weather_service.py` with typed error hierarchy (`WeatherTimeoutError`, `WeatherConnectionError`, `WeatherResponseValidationError`, `WeatherLocationNotFoundError`).
- [x] Implement location geocoding resolving city/district names to lat/lon and place metadata with Open-Meteo Geocoding API.
- [x] Implement daily forecast retrieval (temperature, precipitation, precipitation probability, wind speed, humidity, WMO weather codes) with Open-Meteo CC BY 4.0 attribution.
- [x] Guarantee zero fabricated weather data: when Open-Meteo fails or location is invalid, raise typed errors and report unavailable status.
- [x] Implement conservative agronomic application-window rules in `application_window.py` (runoff hazard, spray drift, heat volatilization, clear windows, next window scan).
- [x] Enforce safety guidelines: never guarantee weather safety from forecast alone; include clear limitations notice.
- [x] Implement `WeatherAgent` (`weather_agent.py`) obtaining and interpreting forecast data for farm locations.
- [x] Implement `Orchestrator` (`orchestrator.py`) coordinating Soil/Crop Agent, Weather Agent, and the deterministic Recommendation Engine, recording partial failures without crashing.
- [x] Create/extend API endpoints: `GET /api/weather/forecast`, `POST /api/analysis`, `POST /api/recommendations/analyze`, and `POST /api/recommendations`.
- [x] Enhance frontend `WeatherPanel.jsx` with 5-day agro timeline cards, freshness timestamps, GO/WAIT badges, limitations notice, and provider attribution.
- [x] Enhance `ResultsDashboard.jsx` with partial analysis notices and a live weather refresh action.
- [x] Write 25 unit and integration tests in `backend/tests/test_weather_and_orchestrator.py` covering geocoding, forecasts, failure handling, application window rules, orchestrator partial failures, and API routes.
- [x] Verify all 94 backend tests pass with 0 failures; frontend builds cleanly in 5.10s.

---

## Phase 6: Agricultural RAG & Grounded LLM Explanations (COMPLETED)

**Objective:** Retrieve relevant agricultural evidence from authoritative Indian and international agronomic institutions (ICAR, CGIAR, Ministry of Agriculture, FAI) using Sentence Transformers and persistent ChromaDB, and use a configurable multi-provider LLM abstraction (OpenAI, Gemini, OpenRouter) to explain already-computed deterministic recommendations in plain language with prompt-injection defense and a keyless offline template fallback.

- [x] Enrich knowledge base with YAML frontmatter metadata (title, issuing organization, document date, license, URL/file reference, applicable crops/regions, category) across 6 authoritative agronomic documents.
- [x] Curate authoritative ICAR Soil Fertility Guidelines (IISS Bhopal 2015) and FAI 4R Nutrient Stewardship guidelines with Markdown tables intact.
- [x] Provide a comprehensive setup guide in `backend/data/knowledge/README.md` detailing document acquisition, metadata specs, and indexing commands.
- [x] Implement layout-aware chunking in `backend/app/rag/chunker.py` preserving Markdown tables (`| ... |`) and structured Q/A pairs intact up to 1800 characters.
- [x] Implement repeatable, idempotent indexing command `python -m app.rag.index_knowledge` using SHA-256 chunk hashes and ChromaDB (`agrimind_knowledge` in `./vector_db`).
- [x] Implement targeted semantic retrieval (`retrieve_for_recommendation()`) generating queries based on diagnosed soil deficiencies, pH extremes, organic carbon levels, and selected crops.
- [x] Build multi-provider LLM abstraction (`backend/app/services/llm_service.py`) supporting OpenAI, Google Gemini, and OpenRouter with configurable `DEFAULT_LLM_PROVIDER` and deliberate failover order.
- [x] Enforce prompt injection defense by fencing retrieved snippets inside `<retrieved_evidence>` XML tags and instructing the model to treat them as background reference text, not executable commands.
- [x] Implement deterministic offline fallback (`template_fallback`) generating rule-based plain-language explanations when no LLM API keys are configured or when providers experience timeouts.
- [x] Guarantee citation and provenance integrity: report `llm_provider`, `llm_model`, and `is_llm_fallback` on API responses, never implying an LLM was used when the template generated the text.
- [x] Update frontend `WhyPanel.jsx` to render rich evidence cards (source title, issuing body, date, file path, cosine relevance scores, quotation chips).
- [x] Update frontend `ResultsDashboard.jsx` to display explanation provenance badges (AI-Generated vs. Template Fallback).
- [x] Write 13 comprehensive unit and integration tests in `backend/tests/test_rag_and_llm.py` covering frontmatter parsing, table/QA preservation, idempotent indexing, semantic retrieval, targeted queries, template fallback, provider ordering, prompt injection defense, and numerical immutability.
- [x] Verify all 107 backend tests pass with 0 failures; `verify_setup.py` benchmark passes 100%; frontend compiles in 6.57s.

---

## Phase 7: Hindi & Marathi Voice Assistant (COMPLETED)

**Objective:** Allow farmers to ask agricultural questions in Hindi or Marathi using speech and hear AgriMind's response aloud, while retaining normal text interaction, editable transcript correction, prompt-level safety boundaries, zero audio retention, and graceful runtime fallback for unsupported environments.

- [x] Implement Web Speech API speech recognition with dynamic locales (`hi-IN`, `mr-IN`, `en-IN`) in `frontend/src/components/AssistantPage.jsx`.
- [x] Provide obvious microphone controls with explicit states: `idle`, `listening` (animated pulsing indicator), `processing` (transcription spinner), and `error` (informative localized troubleshooting).
- [x] Add "Cancel listening" controls and ensure recognition lifecycle guarantees the mic indicator never stays active after recognition finishes.
- [x] Populate captured transcript directly into an editable text field, enabling farmers to review and correct misheard crop or nutrient names before submission.
- [x] Implement Web Speech API speech synthesis (`speechSynthesis`) with 0.92x rate for clear Indic pronunciation.
- [x] Add per-message "Read aloud" and "Stop audio" controls with animated audio wave indicators, plus a global stop control.
- [x] Implement platform voice fallback: detect absence of native Marathi TTS voice and fall back cleanly to an available Indian voice with user notification.
- [x] Update multilingual dictionaries in `frontend/src/i18n/translations.js` across English, Hindi, and Marathi for voice recognition, TTS, privacy, and error states.
- [x] Add in-app Speech Recognition & Privacy Notice clarifying browser-vendor cloud processing and zero audio storage by AgriMind.
- [x] Update backend `POST /api/chat` in `backend/app/api/chat.py` returning `answer`, `evidence`, `contradiction_flag`, `llm_provider`, `is_llm_fallback`, and `language`.
- [x] Enforce Devanagari translation guidelines in `backend/app/services/i18n.py` preserving fertilizer trade names (Urea, DAP, NPK, pH) in Latin script and maintaining deterministic recommendation immutability.
- [x] Conduct and document technical assessment of AI4Bharat IndicConformer vs. Web Speech API in `docs/SPEECH_RECOGNITION_ASSESSMENT.md`.
- [x] Write 17 automated tests in `backend/tests/test_voice_and_multilingual.py` and `backend/tests/test_i18n.py` covering normalization, Devanagari responses, technical names, contradictions, and endpoints.
- [x] Verify all 117 backend tests pass with 0 failures; `verify_setup.py` benchmark passes 100%; frontend compiles in 2.92s.

---

## Phase 8: Optional PostgreSQL Persistence and User Accounts (COMPLETED)

**Objective:** Allow users to save their soil reports, review past analyses, and optionally sign in to access their own saved history with strict user isolation, while keeping ChromaDB responsible for vector retrieval.

- [x] Configure PostgreSQL support with SQLAlchemy 2.0 ORM and Alembic versioned migrations (`alembic upgrade head`).
- [x] Define documented database models for `User` and `SavedReport` with cascading deletion and indexes.
- [x] Avoid storing uploaded PDF files by default: store validated structured measurements, classifications, and weather advisories as structured JSON.
- [x] Implement secure credential management loading `DATABASE_URL`, `JWT_SECRET_KEY`, and `JWT_ALGORITHM` from environment variables.
- [x] Implement cryptographic password hashing using `bcrypt` (12 work factor rounds) with unique salts; ensure plain-text passwords or hashes are never returned.
- [x] Implement standard HMAC-SHA256 JWT bearer authentication with `get_current_user` FastAPI dependency.
- [x] Enforce strict authorization checks on private report endpoints (`GET /api/reports`, `GET /api/reports/{id}`, `DELETE /api/reports/{id}`); return HTTP 403 Forbidden on cross-user access attempts.
- [x] Create dedicated frontend `SavedReportsPage.jsx` with card grid, empty states, loading skeletons, and interactive report inspection modal.
- [x] Create `AuthModal.jsx` supporting seamless farmer sign-in and registration tabs with informative error handling.
- [x] Add "Save Report" action to `ResultsDashboard.jsx` allowing farmers to save analysis results with plot titles and optional field notes.
- [x] Separate anonymous/demo use from signed-in features: guest farmers can run analyses and use the AI assistant without creating an account.
- [x] Update multilingual dictionaries in `frontend/src/i18n/translations.js` across English, Hindi, and Marathi.
- [x] Write comprehensive automated tests in `backend/tests/test_persistence_and_auth.py` covering hashing, registration, login, JWT validation, report persistence, and cross-user 403 access denial.
- [x] Document database architecture and setup in `docs/DATABASE_MIGRATION_GUIDE.md`.
- [x] Verify all 127 backend tests pass with 0 failures; frontend compiles cleanly in 4.07s.

---

## Phase 9: Production Readiness and Deployment (COMPLETED)

**Objective:** Deploy AgriMind so frontend and backend work together over the internet with zero invented URLs, clear operations documentation, hardened security, and verified automated checks.

- [x] Verify full integration audit: PDF upload -> extraction & validation -> deterministic suitability & fertilizer engine -> live Open-Meteo forecast & runoff window -> RAG evidence retrieval -> multilingual explanation -> frontend dashboard & voice assistant -> PostgreSQL persistence.
- [x] Harden security: keep all API keys and database credentials strictly server-side; enforce 10MB upload limits; sanitize logs; add defensive timeouts for external services.
- [x] Configure dynamic production CORS supporting public frontend origins with development fallbacks.
- [x] Provide prominent agricultural limitation notices directing farmers to local Krishi Vigyan Kendras (KVK).
- [x] Update multi-container `docker-compose.yml` with PostgreSQL 16 Alpine service, health checks, environment linking, and persistent volumes.
- [x] Create Infrastructure-as-Code deployment blueprint (`render.yaml`) for managed PostgreSQL, FastAPI backend, and static frontend.
- [x] Create Vercel client-side routing rewrites (`frontend/vercel.json`).
- [x] Implement self-healing boot-time ChromaDB vector indexing (`ensure_indexed()`) in `backend/app/rag/index_knowledge.py` to support stateless/ephemeral cloud containers without manual intervention.
- [x] Distinguish build-time client variables (`VITE_API_BASE_URL`) from secret runtime server variables across root `.env.example`, `backend/.env.example`, and `frontend/.env.example`.
- [x] Update root `.gitignore` to prevent leaking `.venv`, `vector_db`, `agrimind.db`, `.env`, `dist`, and logs.
- [x] Author comprehensive production runbook in `docs/DEPLOYMENT_CHECKLIST.md` with pre-flight checks, cloud deployment steps, and live verification smoke test protocol.
- [x] Update `README.md` with full production instructions, architecture diagrams, Docker Compose commands, and troubleshooting guides.
- [x] Verify automated test suite: 127/127 backend tests passing in `pytest` (87s); frontend production build succeeds in 4.44s with zero errors.


