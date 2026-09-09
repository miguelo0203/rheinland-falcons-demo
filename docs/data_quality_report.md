# Data Quality & Multi-Source Reconciliation Audit

## 1. Quantitative Completeness & Reliability Matrix

* **Total Audited Matches Ingested**: **56 matches**
* **Boxscore Completeness**: **56 / 56** (100.0%)
* **Play-by-Play Completeness**: **56 / 56** (100.0%)
* **Shot Events Completeness**: **56 / 56** (100.0%)
* **Spatial Coordinate Completeness**: **56 / 56** (100.0%)
* **Lineup Stint Completeness**: **56 / 56** (100.0%)
* **Exact Boxscore Scoring Reconciliation**: **56 / 56** (100.0%)
* **High Quality Tier (Quality Score $\ge 0.80$)**: **0 / 56** (0.0%)

---

## 2. Epistemic Status Hierarchy

Every modality is evaluated under strict epistemology:
- `OBSERVED`: Raw data present and verified directly from source replay packets.
- `NOT_AVAILABLE`: Source was queried and does not deliver this modality for this fixture.
- `NOT_APPLICABLE`: Modality not applicable for this fixture structure.