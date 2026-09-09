---
title: Rheinland Falcons Basketball Intelligence
emoji: 🏀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8501
pinned: false
---

# Rheinland Falcons Basketball Intelligence Platform

> **Synthetic Demo & Portfolio Edition**  
> *A 100% synthetic, privacy-guaranteed, forensic-grade basketball analytics, video intelligence, and scouting platform.*

---

## 1. Overview

The **Rheinland Falcons Basketball Intelligence Platform** is an enterprise-grade sports performance and analytics architecture developed for elite youth and academy basketball (JBBL U16 and NBBL U19). 

This standalone demo platform preserves **100% of the production software architecture, analytical pipelines, database schemas, and user interfaces**, while replacing **all real-world data with completely synthetic, mathematically consistent entities, statistics, and tactical video assets**.

### 🔒 Absolute Data Privacy & Security Guarantee
- **Zero Real Entities**: No real players, coaches, clubs, or external opponents exist anywhere in this platform.
- **Zero Real Identifiers**: All player IDs (`PLY_DEMO_*`), team IDs (`TEM_DEMO_*`), and match IDs (`GAM_JBBL_2025_*`) are generated programmatically.
- **Zero Real Media / Assets**: No real video recordings, raw files, or external databases are included. Tactical match video is programmatically rendered using OpenCV simulations.
- **Fail-Closed Verification**: Validated by a strict automated forensic audit (`python -m python.demo.audit_synthetic_data`) guaranteeing 0 violations across 8 audit dimensions.

---

## 2. Quick Start & Execution

### Access Credentials
- **Password**: `demotool`

### Docker Quickstart
```bash
docker compose up --build
```
Open **http://localhost:8501**

### Local Quickstart (without Docker)
```bash
pip install -r requirements.txt
streamlit run app/main.py --server.port=8501
```
