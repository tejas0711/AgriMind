# AgriMind Database Setup & Migration Guide

## Overview

AgriMind uses **PostgreSQL** for persistent application storage (user accounts, saved soil reports, and analysis histories) while keeping **ChromaDB** strictly dedicated to vector embeddings and RAG retrieval.

- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Driver**: `psycopg2-binary` (PostgreSQL) / `sqlite3` (zero-config local dev & tests)
- **Authentication**: `bcrypt` (12 rounds) + HMAC-SHA256 JWT tokens

---

## Environment Configuration

Configure the database connection and JWT secret in your `backend/.env` file:

```bash
# Production PostgreSQL connection
DATABASE_URL=postgresql://agrimind_user:agrimind_password@localhost:5432/agrimind_db

# Local SQLite fallback (default if DATABASE_URL is omitted)
# DATABASE_URL=sqlite:///./agrimind.db

# JWT Security
JWT_SECRET_KEY=generate-a-strong-random-hex-string-for-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## Schema Architecture

### 1. `users` Table
Stores registered farmer accounts.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `INTEGER` | PRIMARY KEY | Unique user ID |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, INDEX | Login email |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | Salted bcrypt hash |
| `full_name` | `VARCHAR(255)` | NULLABLE | Farmer or farm title |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Account active flag |
| `created_at` | `TIMESTAMP` | NOT NULL, UTC | Registration time |
| `updated_at` | `TIMESTAMP` | NOT NULL, UTC | Last profile update |

### 2. `saved_reports` Table
Stores parsed measurements, deterministic evaluations, and weather advisories. **Raw PDF binaries are never stored by default.**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `INTEGER` | PRIMARY KEY | Unique report ID |
| `user_id` | `INTEGER` | FOREIGN KEY (`users.id` ON DELETE CASCADE), INDEX | Owner user ID |
| `title` | `VARCHAR(255)` | NOT NULL | Report title / plot name |
| `farm_name` | `VARCHAR(255)` | NULLABLE | Farm or village name |
| `location_name` | `VARCHAR(255)` | NULLABLE | Geocoded location |
| `latitude` | `FLOAT` | NULLABLE | Coordinates latitude |
| `longitude` | `FLOAT` | NULLABLE | Coordinates longitude |
| `selected_crop` | `VARCHAR(100)` | NULLABLE | Evaluated target crop |
| `soil_data` | `JSON` | NOT NULL | Parsed soil test values (N, P, K, pH, etc.) |
| `deficiencies` | `JSON` | NOT NULL | Deterministic nutrient classifications & units |
| `crop_scores` | `JSON` | NOT NULL | Suitability scores & penalties |
| `fertilizer_options` | `JSON` | NOT NULL | Recommended organic & chemical options |
| `application_window` | `JSON` | NULLABLE | Weather GO/WAIT advisory |
| `evidence` | `JSON` | NOT NULL | Cited agronomic references & standards |
| `explanation` | `TEXT` | NULLABLE | Plain-language AI / deterministic explanation |
| `notes` | `TEXT` | NULLABLE | Farmer field notes |
| `created_at` | `TIMESTAMP` | NOT NULL, UTC | Save timestamp |
| `updated_at` | `TIMESTAMP` | NOT NULL, UTC | Last modification timestamp |

---

## Running Migrations with Alembic

All database migrations are located in `backend/alembic/versions/`.

### Apply Migrations to Target Database
```bash
cd backend
# With virtualenv active:
alembic upgrade head
```

### Check Current Migration Status
```bash
alembic current
```

### Generate a New Migration (Schema Changes)
```bash
alembic revision --autogenerate -m "describe_change"
```

### Roll Back One Revision
```bash
alembic downgrade -1
```

---

## Local PostgreSQL Quickstart (Docker)

To run a dedicated PostgreSQL 16 container for AgriMind:

```bash
docker run -d \
  --name agrimind-postgres \
  -e POSTGRES_USER=agrimind_user \
  -e POSTGRES_PASSWORD=agrimind_password \
  -e POSTGRES_DB=agrimind_db \
  -p 5432:5432 \
  postgres:16-alpine
```

Set in `backend/.env`:
```bash
DATABASE_URL=postgresql://agrimind_user:agrimind_password@localhost:5432/agrimind_db
```

Then run:
```bash
cd backend
alembic upgrade head
```

---

## Strict Authorization & Security Rules

1. **User Isolation**:
   - `GET /api/reports`: Returns only records matching `user_id == current_user.id`.
   - `GET /api/reports/{id}` & `DELETE /api/reports/{id}`: Returns HTTP 403 Forbidden if accessed by any other user.
2. **Credential Protection**:
   - Passwords hashed using `bcrypt` (12 work factor rounds).
   - No plain passwords or password hashes are ever returned in API responses.
3. **Guest / Anonymous Support**:
   - AgriMind allows full anonymous soil analysis, crop scoring, weather application windows, and RAG/voice assistant without an account.
   - Authentication is strictly required only to persist and review historical records across sessions.
