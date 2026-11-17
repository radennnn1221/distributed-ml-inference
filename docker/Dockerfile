# syntax=docker/dockerfile:1.7
# ============================================================
# STAGE 1 - builder: install dependency ke virtualenv terpisah
# ============================================================
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Layer dependensi dipisah dari layer kode agar cache build optimal.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# ============================================================
# STAGE 2 - runtime: image final ramping, tanpa toolchain build
# ============================================================
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="distributed-ml-inference-backend" \
      org.opencontainers.image.description="FastAPI + PostgreSQL replication + Keycloak SSO + Random Forest" \
      org.opencontainers.image.version="2.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app \
    && useradd --system --gid app --create-home app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Kode aplikasi (perubahan kode tidak memicu reinstall dependensi)
COPY ml ./ml
COPY backend ./backend

RUN chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
