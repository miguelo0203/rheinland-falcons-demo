# Evidence Traceability Matrix

Every coach finding and analytical metric links deterministically to underlying canonical database entities:

```text
Finding ID
  ├── Metric Formula & Statistical Test
  ├── Population Definition (Pop A / Pop C / Pop E)
  ├── Filtered Games (Game IDs in DuckDB)
  ├── Canonical Relational Rows (boxscore_team, boxscore_player, shot, pbp_event)
  └── Raw Source Payload & Cryptographic SHA-256 Hash
```