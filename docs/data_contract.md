# Data Contract — Ingestion & Storage Layers

## 1. Scope
This document specifies the strict schema constraints, missingness semantics, and referential integrity expectations for all data entering the sandbox.

## 2. Missingness Standard
| Enum Value | Semantic Meaning | Database Representation |
|:---|:---|:---|
| `OBSERVED` | Confirmed observed metric from source. | Explicit numeric / text value |
| `NOT_AVAILABLE` | Tracked by sport but missing in source file. | `NULL` |
| `NOT_APPLICABLE` | Meaningless in current context. | `NULL` |
| `NOT_OBSERVED` | Source was not captured or enabled. | `NULL` |
| `ESTIMATED` | Reconstructed via statistical model. | Explicit value + Flag |

## 3. Surrogate Key Design
- Competition: `CMP_[A-Z0-9_]+`
- Season: `SEA_[A-Z0-9_]+`
- Team: `TEM_[A-Z0-9]{12}`
- Player: `PLY_[A-Z0-9]{12}`
- Game: `GAM_[A-Z0-9_]+`
- Provenance: `PRV_[A-Z0-9]{12}`
- Boxscore Team: `BXT_[A-Z0-9]{12}`
- Boxscore Player: `BXP_[A-Z0-9]{12}`
- Event: `EVT_[A-Z0-9]{12}`
- Shot: `SHT_[A-Z0-9]{12}`
- Stint: `STI_[A-Z0-9]{12}`
- Video: `VID_[A-Z0-9_]+`
- Sync: `SYN_[A-Z0-9]{12}`
- Alias: `ALS_[A-Z0-9]{12}`
- Conflict: `CNF_[A-Z0-9]{12}`
- Validation: `VAL_[A-Z0-9]{12}`
