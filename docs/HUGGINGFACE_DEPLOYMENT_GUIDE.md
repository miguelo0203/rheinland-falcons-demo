# Hugging Face Spaces Deployment Guide
## Rheinland Falcons Basketball — Instant Online Coach Demo

---

## 1. Overview

This guide explains how to get the **Rheinland Falcons Basketball Player Intelligence MVP** online on **Hugging Face Spaces** in less than 2 minutes.

```text
┌──────────────────────────────────────────────┐
│  GitHub Repository (PRIVATE)                 │
│  miguelo0203/falcons-falcons-intelligence      │
└──────────────────────┬───────────────────────┘
                       │ Import / Push
                       ▼
┌──────────────────────────────────────────────┐
│  Hugging Face Space (Streamlit SDK)          │
│  https://huggingface.co/spaces/<user>/<repo> │
└──────────────────────┬───────────────────────┘
                       │ HTTPS
                       ▼
┌──────────────────────────────────────────────┐
│  Coach Ferran (Remote Mobile / Desktop)      │
└──────────────────────────────────────────────┘
```

---

## 2. 60-Second Deployment Instructions

### Option A: Direct Import from GitHub (Fastest)

1. Log in to [Hugging Face](https://huggingface.co).
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
3. Fill in:
   - **Space name**: `falcons-falcons-intelligence`
   - **License**: `mit` (or leave default)
   - **SDK**: Select **Streamlit**
   - **Space hardware**: `CPU basic · 2 vCPU · 16GB` (Free tier)
   - **Visibility**: **Public** (Protected by in-app password gate) or **Private**
4. Under **"Duplicate / Import"** or Git clone:
   - If using HF Git: Follow the on-screen instructions to push directly from your local terminal:
     ```bash
     git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/falcons-falcons-intelligence
     git push space main
     ```

---

### Option B: Push Directly to Hugging Face Git

```powershell
# 1. Add your Hugging Face Space as a remote
git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/falcons-falcons-intelligence

# 2. Push to Hugging Face
git push space main
```

---

## 3. Configuring the Coach Access Password

1. Inside your Hugging Face Space, click on **⚙️ Settings** (top right).
2. Scroll down to **Variables and secrets**.
3. Click **New secret**:
   - **Name**: `DEMO_AUTH_PASSWORD`
   - **Value**: `YOUR_SECRET_PASSWORD`
4. Click **Save**.

The Space will restart and enforce the password gate automatically.

---

## 4. Live URL & Sharing with Ferran

Your Space will be immediately live at:
```text
https://huggingface.co/spaces/<YOUR_HF_USERNAME>/falcons-falcons-intelligence
```

Direct full-screen embed URL (clean coach UI without HF banner):
```text
https://<YOUR_HF_USERNAME>-falcons-falcons-intelligence.hf.space
```

Share this URL and your chosen password with Coach Ferran!
