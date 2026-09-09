# ==============================================================================
# RHEINLAND FALCONS BASKETBALL — DEMO PLATFORM DOCKERFILE
# ==============================================================================
# Self-contained Streamlit Intelligence Demo — 100% synthetic data.
# ==============================================================================

FROM python:3.11-slim

# ── Environment ──────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ── System dependencies ─────────────────────────────────────────────────────
# curl          → healthcheck
# libgl1 + glib → OpenCV (video hub)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    socat \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies (cached layer) ──────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Application code ────────────────────────────────────────────────────────
COPY .streamlit/         .streamlit/
COPY config/             config/
COPY schemas/            schemas/
COPY python/             python/
COPY app/                app/
COPY pyproject.toml      .

# ── Synthetic data (DuckDB + Parquet + Video) ────────────────────────────────
COPY data/basketball_demo.duckdb         data/basketball_demo.duckdb
COPY data/derived/                       data/derived/
COPY data/normalized/                    data/normalized/
COPY data/video/demo_tactical_match.mp4  data/video/demo_tactical_match.mp4

# ── Streamlit secrets for container (100% fictitious demo config only) ─────────
# All local secrets (.env, secrets.toml) are strictly excluded via .dockerignore.
# The container receives ONLY fictitious demo settings with zero real credentials.
# At runtime in production, DEMO_AUTH_PASSWORD env var takes precedence.
RUN echo 'auth_password = "demotool"' > .streamlit/secrets.toml && \
    echo 'environment = "demo"'      >> .streamlit/secrets.toml

# ── Security: non-root user ─────────────────────────────────────────────────
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# ── Network ──────────────────────────────────────────────────────────────────
EXPOSE 8501 10000

# ── Healthcheck ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://127.0.0.1:8501/_stcore/health || exit 1

# ── Entrypoint ───────────────────────────────────────────────────────────────
CMD ["sh", "-c", "STREAMLIT_PORT=${STREAMLIT_SERVER_PORT:-8501}; if [ -n \"$PORT\" ] && [ \"$PORT\" != \"$STREAMLIT_PORT\" ]; then socat TCP-LISTEN:$PORT,fork,reuseaddr TCP:127.0.0.1:$STREAMLIT_PORT & fi; if [ \"$PORT\" != \"10000\" ] && [ \"$STREAMLIT_PORT\" != \"10000\" ]; then socat TCP-LISTEN:10000,fork,reuseaddr TCP:127.0.0.1:$STREAMLIT_PORT & fi; exec python -m streamlit run app/main.py --server.port=$STREAMLIT_PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --browser.gatherUsageStats=false"]
