# Deployment & Remote Access Strategy: Rheinland Falcons Player Intelligence MVP

---

## 1. Objective & Architectural Context

The **Player Intelligence MVP** is developed with **100% relative project paths** and zero machine-specific hardcoded dependencies. While operating locally in `F:\Rheinland Falcons Prueba` during development, the application is engineered to be deployed remotely so that Coach Ferran and the Rheinland Falcons coaching staff can access it from any browser, tablet, or phone.

---

## 2. Recommended Deployment Options

| Option | Setup Complexity | Hosting Cost | Security / Access Control | Performance | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Option A: Streamlit Community Cloud (GitHub Integration)** | **Lowest** (1-Click git push) | **Free** ($0 / month) | Password / SSO protection via Streamlit | **High** (Standard container) | **🏆 BEST FOR QUICK COACH ACCESS** |
| **Option B: Lightweight Virtual Private Server (Hetzner / DigitalOcean)** | **Low** (Docker / Systemd) | **Very Low** (~€4–6 / month) | Full control, NGINX SSL, Basic Auth, VPN | **Very High** (Dedicated CPU/RAM) | **🏆 BEST FOR CLUB PRODUCTION** |
| **Option C: Club Internal Docker Container** | **Moderate** (Docker Compose) | **Included** in club IT infra | Local club intranet / WireGuard | **Maximum** | **BEST FOR PRIVATE VIDEO INGESTION** |

---

## 3. Step-by-Step Implementation for Recommended Options

### Option A: Streamlit Community Cloud (Fastest for Ferran)
1. Ensure the repository contains:
   - `pyproject.toml` or `requirements.txt` (including `streamlit`, `duckdb`, `plotly`, `pandas`, `pyarrow`, `scipy`).
   - `.streamlit/config.toml` configuring theme and headless mode.
2. Push repository branch to GitHub private repository.
3. Connect GitHub repository to [share.streamlit.io](https://share.streamlit.io).
4. Set entrypoint: `app/main.py`.
5. Enable private access or Streamlit password authentication.

### Option B: Dedicated Club VPS with Docker & NGINX
1. **Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install --no-cache-dir -e .
   EXPOSE 8501
   CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```
2. **Docker Compose with SSL Reverse Proxy**:
   ```yaml
   version: '3.8'
   services:
     falcons-analytics:
       build: .
       ports:
         - "8501:8501"
       restart: always
       volumes:
         - ./data:/app/data
         - ./database:/app/database
   ```
3. NGINX reverse proxy with Let's Encrypt SSL certificate (`analytics.falcons-falcons.com`).

---

## 4. Portability Guarantee
- All database connections in `app/services/data_service.py` use `Path("database/jbbl_sandbox.duckdb")` relative to the repository root.
- All derived datasets resolve via `Path("data/derived")`.
- No absolute host paths exist in the application code.
