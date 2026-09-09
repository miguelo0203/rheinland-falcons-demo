# Coach Interface v2 Methodology & Decision-Support Design

## 1. Single-Club Multi-Season Architecture
The interface (`app/main.py`) serves Rheinland Falcons Basketball across multiple seasons with:
* Dynamic season discovery from DuckDB (`get_available_seasons()`).
* Explicit population switching (`OFFICIAL_ONLY` vs `ALL_GAMES`).
* Dedicated deep-dive labs: Player Lab, Game Lab, Shot Lab, Evidence Explorer, Hypothesis Lab.