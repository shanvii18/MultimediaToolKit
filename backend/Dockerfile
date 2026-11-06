FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_CACHE_DIR=/app/models \
    WORK_DIR=/tmp/mtk-work \
    MALLOC_ARENA_MAX=2

WORKDIR /app

# System dependencies: FFmpeg (media), Tesseract + English data (OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Optionally bake the CPU models (~330 MB) into the image so cold starts never download them:
#   docker build --build-arg PRELOAD_MODELS=1 ...
ARG PRELOAD_MODELS=0
RUN if [ "$PRELOAD_MODELS" = "1" ]; then python -m app.cli download-models; fi

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
