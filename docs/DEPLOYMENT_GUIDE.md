# Streamlit Community Cloud Deployment Guide
## Rheinland Falcons Basketball — Coach-Facing Basketball Intelligence Platform

---

## 1. Overview & Architecture

This guide explains how to deploy the **Rheinland Falcons Basketball Player Intelligence MVP** to **Streamlit Community Cloud** so that Coach Ferran and technical staff can access the dashboard securely from any device over HTTPS **without requiring Miguel's local PC to be running or acting as a server**.

```text
┌────────────────────────┐
│  Miguel's Local PC     │
│  F:\Rheinland Falcons      │  (100% UNTOUCHED PRODUCTION)
│  F:\Rheinland Falcons Prueba│  (Git Repository Source)
└───────────┬────────────┘
            │ git push
            ▼
┌────────────────────────┐
│  GitHub Repository     │  (PRIVATE Repository)
│  (Code + DuckDB + Data)│
└───────────┬────────────┘
            │ Continuous Deployment
            ▼
┌────────────────────────┐
│  Streamlit Cloud       │  (Cloud Hosting + Secrets Management)
│  app/main.py           │  (Dual-Layer Access Control)
└───────────┬────────────┘
            │ Secure HTTPS URL
            ▼
┌────────────────────────┐
│  Coach Ferran          │  (Remote Web Access)
└────────────────────────┘
```

---

## 2. Step-by-Step Deployment Instructions

### Step 1: Initialize Git and Create Local Commit
Open PowerShell inside `F:\Rheinland Falcons Prueba`:

```powershell
cd "F:\Rheinland Falcons Prueba"
git init
git add .
git commit -m "feat: initial commit for Rheinland Falcons Coach Intelligence MVP"
```

> [!IMPORTANT]
> The included `.gitignore` automatically prevents `.streamlit/secrets.toml`, `data/raw/`, `logs/`, and temporary caches from being added. Confirm that `git status` shows only clean project files.

---

### Step 2: Create a Private GitHub Repository
1. Go to [GitHub.com](https://github.com) and create a **New Repository**.
2. Set the repository name (e.g. `falcons-falcons-intelligence`).
3. Set visibility strictly to **🔒 Private**.
4. Do **not** initialize with a README (the local project already has all files).

Push the local repository to GitHub:
```powershell
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/falcons-falcons-intelligence.git
git branch -M main
git push -u origin main
```

---

### Step 3: Connect to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your private repository: `<YOUR_GITHUB_USERNAME>/falcons-falcons-intelligence`.
4. Branch: `main`.
5. Main file path: `app/main.py`.
6. Click **"Advanced settings..."** before deploying.

---

### Step 4: Configure Cloud Secrets (Authentication Password)
In the Streamlit Cloud **Advanced Settings** -> **Secrets** text box, enter:

```toml
auth_password = "YOUR_SECURE_COACH_PASSWORD"
environment = "production"
```

*(Choose a strong password and share it privately with Coach Ferran).*

Click **"Save"** and then **"Deploy!"**.

---

### Step 5: Verify Deployment & Grant Viewer Access
1. Streamlit Cloud will spin up the Linux container, install `requirements.txt`, and launch `app/main.py`.
2. The initial view will present the **🔒 Youth Intelligence Access** login card.
3. Enter the secret password you configured in Step 4.
4. Verify that the Player Intelligence Dossier, Executive KPIs, 6-Axis Radar, 2D Interactive Shot Map, and Game Lab render smoothly.
5. In the app settings (top right menu -> **Settings** -> **Sharing**), you can restrict viewer access exclusively to invited Google/GitHub emails for additional security.

---

## 3. Workflow for Future Updates

When new games or features are ready to be published:

```powershell
# 1. Work and test locally
cd "F:\Rheinland Falcons Prueba"
python -m pytest tests/ -v

# 2. Commit and push
git add .
git commit -m "feat: updated game payloads and player intelligence"
git push origin main
```

Streamlit Community Cloud will automatically detect the push and redeploy the live application within seconds.

---

## 4. Rollback Procedure

If a deployed update contains an unexpected issue, roll back instantly:

```powershell
# View recent commits
git log --oneline -n 5

# Revert to the last known good commit
git revert HEAD
git push origin main
```
