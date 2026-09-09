# Docker Production Deployment Guide
## Rheinland Falcons Basketball — Coach-Facing Basketball Intelligence Platform

---

## 1. Overview & Architecture

This guide details how to build, run, and deploy the **Rheinland Falcons Basketball Basketball Intelligence MVP** as a standalone, production-ready **Docker container**.

The containerized application is completely self-contained:
- Encapsulates Python 3.11 runtime, dependencies, and Streamlit presentation layer.
- Packages the read-only DuckDB analytical database (`database/jbbl_sandbox.duckdb`) and derived Parquet datasets (`data/derived/`).
- Operates independently of any local Windows PC filesystem.
- Enforces application-level authentication via runtime environment variables (`DEMO_AUTH_PASSWORD`).

```text
┌────────────────────────────────────────────────────────┐
│  INTERNET (Coach Ferran & Technical Staff)             │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS (:443)
                            ▼
┌────────────────────────────────────────────────────────┐
│  REVERSE PROXY (NGINX / Caddy / Traefik with SSL)      │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP (:8501)
                            ▼
┌────────────────────────────────────────────────────────┐
│  DOCKER CONTAINER: falcons_falcons_app                   │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Streamlit Application (app/main.py)              │  │
│  │ • Security Gate (app/auth.py)                    │  │
│  │ • Player Intelligence Engine                     │  │
│  │ • Hero View, 6-Axis Radar, 2D Shot Map           │  │
│  └──────────────────────────┬───────────────────────┘  │
│                             │ Read-Only Queries        │
│                             ▼                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Embedded Data Layer                              │  │
│  │ • DuckDB (database/jbbl_sandbox.duckdb) [RO]     │  │
│  │ • Parquet Datasets (data/derived/*.parquet)      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

- **Docker Engine** (v24.0+ recommended)
- **Docker Compose** (v2.20+ recommended)

---

## 3. Quickstart: Local Docker Deployment

### Step 1: Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Edit `.env` and configure your secure coach authentication password:
```env
DEMO_AUTH_PASSWORD=YOUR_SECURE_COACH_PASSWORD
```

### Step 2: Build the Docker Image
```bash
docker compose build
```
*(Alternatively: `docker build -t falcons-falcons-intelligence .`)*

### Step 3: Run the Container
```bash
docker compose up -d
```

### Step 4: Verify Container Status & Logs
Check container health:
```bash
docker compose ps
docker compose logs -f
```

### Step 5: Access the Dashboard
Open your web browser at:
```text
http://localhost:8501
```
Enter the `DEMO_AUTH_PASSWORD` configured in your `.env` file to access the Player Intelligence dashboard.

### Step 6: Stop the Container
```bash
docker compose down
```

---

## 4. Deploying to a Linux VPS (DigitalOcean, Hetzner, AWS, Linode)

### A. Server Setup
On your remote Linux VPS (Ubuntu 22.04/24.04 LTS):
```bash
# 1. Update and install Docker + Compose
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2

# 2. Clone the private repository
git clone https://github.com/miguelo0203/falcons-falcons-intelligence.git
cd falcons-falcons-intelligence

# 3. Create .env with the production password
cp .env.example .env
nano .env
# Set DEMO_AUTH_PASSWORD=your_production_password

# 4. Launch the container
sudo docker compose up -d --build
```

---

### B. Production HTTPS Reverse Proxy (Caddy or NGINX)

#### Option 1: Automatic SSL with Caddy (Recommended)
Install Caddy:
```bash
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update && sudo apt-get install caddy
```

Create `/etc/caddy/Caddyfile`:
```caddy
analytics.yourdomain.com {
    reverse_proxy localhost:8501
}
```
Reload Caddy:
```bash
sudo systemctl reload caddy
```
Caddy will automatically provision and renew a Let's Encrypt SSL certificate.

---

#### Option 2: NGINX with Let's Encrypt (Certbot)
Create `/etc/nginx/sites-available/falcons-analytics`:
```nginx
server {
    listen 80;
    server_name analytics.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```
Enable and secure with Certbot:
```bash
sudo ln -s /etc/nginx/sites-available/falcons-analytics /etc/nginx/sites-enabled/
sudo certbot --nginx -d analytics.yourdomain.com
```

---

## 5. Secret Management & Security Policies

1. **Never Bake Passwords into Images**: The `Dockerfile` does not include default passwords. Passwords are supplied dynamically at runtime via `DEMO_AUTH_PASSWORD` environment variable or `.env` file.
2. **Non-Root Execution**: The container runs as an unprivileged user (`appuser`, UID 10001) to protect the host environment.
3. **Read-Only Database**: The database connection in `DataService` operates in `read_only=True` mode, preventing any concurrent write locks or database corruption.
4. **Git Exclusion**: `.env` and `.streamlit/secrets.toml` are strictly ignored by `.gitignore` and `.dockerignore`.

---

## 6. Updating the Live Application

When new code or match data is committed:
```bash
cd /path/to/falcons-falcons-intelligence
git pull origin main
sudo docker compose build --no-cache
sudo docker compose up -d
```

---

## 7. Backup and Recovery

To back up the canonical analytical state:
```bash
# Backup DuckDB and Parquet layers
tar -czvf falcons_data_backup_$(date +%Y%m%d).tar.gz database/jbbl_sandbox.duckdb data/derived/
```

To restore from a backup:
```bash
tar -xzvf falcons_data_backup_YYYYMMDD.tar.gz
sudo docker compose restart
```
