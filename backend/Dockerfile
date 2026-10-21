FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build the RAG index at image build time so the container is pre-warmed
RUN python -m app.rag.index_knowledge || true

EXPOSE 8000

# Apply database migrations on launch, then start uvicorn
CMD ["sh", "-c", "alembic upgrade head 2>/dev/null || true; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
