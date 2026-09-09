# Provenance & Auditability Architecture

## 1. Provenance Model
Every ingested record links to `source_provenance` via `provenance_id`.

```text
Source File (RAW)
       │
       ▼
compute_file_sha256()
       │
       ▼
SourceProvenance (PRV_...)
       ├── source_type: BOXSCORE / PBP / VIDEO
       ├── source_provider: DBB / FIBA / NBN23
       ├── source_file_path: data/raw/...
       ├── source_file_hash: SHA-256
       ├── parser_version: 1.0.0
       └── ingestion_timestamp: UTC
```
