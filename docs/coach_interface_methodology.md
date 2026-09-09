# Coach Interface Architecture & Interactive Design

## 1. Dynamic Zero-Hardcoding Architecture
* The interface (`app/main.py`) reads 100% of numerical and contextual metrics dynamically from `DataService`.
* Zero hardcoded analytical values guarantees that newly ingested games update all dashboards automatically.