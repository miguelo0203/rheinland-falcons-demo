# Rheinland Falcons Basketball — Deployment Guide

> **100% Synthetic Demo** — This container uses only fictitious data.  
> No real player, team, or match information is included.

---

## Prerequisites

| Tool           | Minimum Version |
|----------------|-----------------|
| Docker Engine  | 24.0+           |
| Docker Compose | 2.20+ (V2)      |

---

## Quick Start

### Option A — Docker CLI

```bash
# Build the image
docker build -t rheinland-falcons-demo .

# Run the container
docker run --rm -p 8501:8501 rheinland-falcons-demo
```

Open **http://localhost:8501** — Password: `demotool`

### Option B — Docker Compose

```bash
# Build and start
docker compose up --build

# Detached mode
docker compose up --build -d

# Stop
docker compose down
```

---

## Configuration

### Environment Variables

| Variable               | Default      | Description                    |
|------------------------|--------------|--------------------------------|
| `DEMO_AUTH_PASSWORD`   | `demotool`   | Coach login password           |
| `PORT`                 | `8501`       | Streamlit server port          |

Override at runtime:

```bash
# Docker CLI
docker run --rm -p 8501:8501 -e DEMO_AUTH_PASSWORD=mypassword rheinland-falcons-demo

# Compose (via .env file)
echo "DEMO_AUTH_PASSWORD=mypassword" > .env
docker compose up --build -d
```

### Custom Port

```bash
docker run --rm -p 9000:8501 -e PORT=8501 rheinland-falcons-demo
```

Or in `compose.yaml`, change the host port: `"9000:8501"`.

---

## Architecture

```
Container /app/
├── .streamlit/          # Streamlit theme & config
├── app/                 # Streamlit UI (main.py entry point)
│   ├── auth.py          # Authentication gate
│   ├── services/        # DataService (DuckDB + Parquet)
│   └── components/      # Radar, trajectory, court plots
├── python/              # Analytics & database modules
├── config/              # settings.yaml
├── schemas/             # DDL definitions
├── data/
│   ├── basketball_demo.duckdb   # Synthetic DuckDB (9.8 MB)
│   ├── derived/                 # 27 analytical Parquet files
│   ├── normalized/              # 20 normalized Parquet files
│   └── video/                   # Synthetic tactical match video
└── pyproject.toml
```

**Entry point:** `streamlit run app/main.py`

---

## Health Check

The container includes a built-in healthcheck at `/_stcore/health`:

```bash
curl http://localhost:8501/_stcore/health
```

---

## Cloud Deployment Options

> ⚠️ **Do NOT deploy without changing the default password.**

### Render

1. Push the demo directory to a Git repository
2. Create a **Web Service** on [render.com](https://render.com)
3. Set the root directory to the demo folder
4. Add environment variable: `DEMO_AUTH_PASSWORD=<secure-password>`
5. Render auto-detects the Dockerfile and deploys

### Railway

```bash
railway login
railway init
railway up
```

Set `DEMO_AUTH_PASSWORD` in the Railway dashboard.

### Google Cloud Run

```bash
# Build & push
gcloud builds submit --tag gcr.io/PROJECT_ID/rheinland-falcons-demo

# Deploy
gcloud run deploy rheinland-falcons-demo \
  --image gcr.io/PROJECT_ID/rheinland-falcons-demo \
  --port 8501 \
  --allow-unauthenticated \
  --set-env-vars DEMO_AUTH_PASSWORD=<secure-password>
```

### Fly.io

```bash
fly launch
fly secrets set DEMO_AUTH_PASSWORD=<secure-password>
fly deploy
```

---

## Security Checklist

- [ ] Change `DEMO_AUTH_PASSWORD` from default before public deployment
- [ ] Enable HTTPS (most cloud providers do this automatically)
- [ ] Verify no real data exists in the container: `docker run --rm rheinland-falcons-demo find /app/data -type f | head -30`
- [ ] Review container logs after first deploy

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Port already in use | `docker run --rm -p 9000:8501 rheinland-falcons-demo` |
| Permission denied | Ensure Docker daemon is running |
| Healthcheck failing | Wait 15s for startup, then check `curl localhost:8501/_stcore/health` |
| Import errors | Rebuild image: `docker build --no-cache -t rheinland-falcons-demo .` |
