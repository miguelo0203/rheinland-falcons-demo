# Render Production Deployment Guide
## Rheinland Falcons Basketball — Coach-Facing Basketball Intelligence Platform

---

## 1. Architecture Overview

Deploying the **Rheinland Falcons Basketball Player Intelligence MVP** to **Render** provides an enterprise-grade, isolated container environment with automatic HTTPS, zero server management, and 100% independence from your local computer.

```text
┌────────────────────────────────────────────────────────┐
│  GitHub Repository (PRIVATE)                           │
│  miguelo0203/falcons-falcons-intelligence (branch: main) │
└───────────────────────────┬────────────────────────────┘
                            │ Continuous Deployment Trigger
                            ▼
┌────────────────────────────────────────────────────────┐
│  Render Cloud Platform                                 │
│  • Free Tier Web Service (Docker Runtime)              │
│  • Automated Docker Build                              │
│  • Dynamic $PORT binding (0.0.0.0:$PORT)               │
│  • Environment Secrets (DEMO_AUTH_PASSWORD)           │
└───────────────────────────┬────────────────────────────┘
                            │ Global Anycast HTTPS (:443)
                            ▼
┌────────────────────────────────────────────────────────┐
│  Coach Ferran & Technical Staff                        │
│  https://falcons-falcons-intelligence.onrender.com       │
└────────────────────────────────────────────────────────┘
```

---

## 2. 60-Second Deployment Instructions

### Step 1: Log in to Render
1. Open **[dashboard.render.com](https://dashboard.render.com)**.
2. Sign in with your GitHub account (`miguelo0203`).

---

### Step 2: Create a New Web Service
1. Click **"New +"** (top right) -> **"Web Service"**.
2. Under **"Build and deploy from a Git repository"**, connect your private repository:
   - **`miguelo0203/falcons-falcons-intelligence`**
3. Configure the service:
   - **Name**: `falcons-falcons-intelligence`
   - **Region**: `Frankfurt (EU Central)` *(closest to Rheinland)*
   - **Branch**: `main`
   - **Runtime**: **`Docker`**
   - **Instance Type**: **`Free`**

---

### Step 3: Add the Coach Password Environment Variable
In the **Environment Variables** section on the same page, click **"Add Environment Variable"**:
- **Key**: `DEMO_AUTH_PASSWORD`
- **Value**: `FalconsTool` *(or your chosen coach password)*

---

### Step 4: Deploy
Click **"Create Web Service"**.

Render will automatically:
1. Pull the repository and Git LFS database/parquet layers.
2. Build the Docker container using `Dockerfile`.
3. Start Streamlit bound dynamically to `0.0.0.0:$PORT`.
4. Provision a dedicated SSL certificate and assign your public URL:
   ```text
   https://falcons-falcons-intelligence.onrender.com
   ```

---

## 3. Security & Access Verification

1. **Zero Hardcoded Secrets**: The password `FalconsTool` is never stored in Git; it exists strictly inside Render's encrypted environment variable store.
2. **Read-Only Database**: DuckDB is queried strictly in `read_only=True` mode, preventing multi-user write conflicts.
3. **Session Isolation**: Each coach session is isolated in memory with `st.session_state`.
4. **Independent Availability**: Once deployed, Miguel's PC can be turned off completely.

---

## 4. Automatic Continuous Deployment

Whenever you push new commits to GitHub (`origin main`):
```powershell
git add .
git commit -m "feat: updated match dossiers"
git push origin main
```
Render will automatically rebuild and redeploy the live container with zero downtime.
