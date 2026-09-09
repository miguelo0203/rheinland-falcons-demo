# Deployment Manifest — Rheinland Falcons Analytics Platform
## Canonical Inventory of Deployed vs Local-Only Artifacts

---

## 1. Summary Statistics

- **Total Deployed Package Size**: ~48.1 MB (Well under GitHub's 100 MB single-file limit and Streamlit Cloud RAM capacity).
- **Excluded Local Artifacts**: ~8.9 MB (Raw scraper dumps, intermediate JSON logs, test caches).
- **Canonical Analytical Database**: `database/jbbl_sandbox.duckdb` (44.0 MB, accessed in `read_only=True` mode).

---

## 2. Detailed File Inventory

### A. Included in Cloud Deployment (`REQUIRED FOR MVP`)

| Directory / File | Size | Rationale / Purpose |
| :--- | :---: | :--- |
| `app/` | 0.19 MB | Streamlit presentation layer, Hero View, Game Lab, UI theme components, and authentication gate (`app/auth.py`). |
| `python/analytics/` | 0.29 MB | Evidence Engine v2, player evolution, league benchmarks, shot intelligence, and population filters. |
| `python/database/` | 0.04 MB | DuckDB connection manager (`read_only=True` support) and views. |
| `python/models/` | 0.04 MB | Canonical dataclasses, enums, and metric schemas. |
| `python/validation/` | 0.09 MB | Business rule validation engine. |
| `python/config.py` | 2.4 KB | Portable path resolution using `Path(__file__).resolve().parent.parent`. |
| `database/jbbl_sandbox.duckdb` | 44.0 MB | Canonical historical database (65 games, 60 boxscores, 36 PBP, 5,024 shots, 767 players). |
| `data/derived/` | 1.14 MB | Parquet datasets for coach findings, player evolution, and league distributions. |
| `config/settings.yaml` | 1.1 KB | Non-secret system settings, metric tolerances, and entity resolution parameters. |
| `schemas/` | 0.01 MB | Canonical SQL DDL and schema definitions. |
| `.streamlit/config.toml` | 0.3 KB | Streamlit theme (FALCONS navy/blue), CORS and XSRF protection. |
| `.streamlit/secrets.toml.example` | 0.5 KB | Example template for Cloud Secrets configuration. |
| `requirements.txt` | 0.2 KB | Pinned runtime dependencies (`streamlit`, `duckdb`, `pandas`, `plotly`, etc.). |
| `docs/` | 1.59 MB | Technical documentation, architecture specs, and evidence methodologies. |
| `tests/` | 0.71 MB | Full test suite ensuring platform stability. |

---

### B. Excluded from Deployment (`LOCAL ONLY / DO NOT DEPLOY`)

| Directory / Pattern | Size | Exclusion Rationale |
| :--- | :---: | :--- |
| `.streamlit/secrets.toml` | — | **CRITICAL SECURITY**: Contains actual production passwords. Excluded via `.gitignore`. |
| `data/raw/` | 2.60 MB | Raw websocket stream dumps and scraper artifacts. Not needed by the analytical runtime. |
| `data/staging/` | 0.00 MB | Transient ETL staging directory. |
| `data/normalized/` | 0.30 MB | Intermediate extraction files. |
| `data/validated/` | 0.00 MB | Intermediate validation directory. |
| `reports/source_audit/` | 5.98 MB | Development scraping logs and exploration dumps. |
| `logs/` | 0.00 MB | Local process execution logs. |
| `__pycache__/`, `*.pyc` | — | Python bytecode caches. |
| `.pytest_cache/` | 0.01 MB | Pytest test execution cache. |
| `scratch/` | — | Temporary agent development scripts. |
| `F:\Rheinland Falcons` | — | **PRODUCTION SAFETY**: Production directory is completely external to the repository. |

---

## 3. Security & Integrity Verification

1. **Zero Hardcoded Secrets**: All passwords and access credentials are provided exclusively at runtime via `st.secrets`.
2. **Read-Only Concurrency**: `database/jbbl_sandbox.duckdb` is opened in `read_only=True` mode, preventing any concurrent write conflicts or database file locks.
3. **Platform Independence**: All file references use `pathlib.Path` relative to project root, eliminating dependencies on Windows drive letters (`F:\`).
