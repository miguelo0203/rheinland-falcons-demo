# Canonical Data Dictionary

## 1. Tables Overview

| Table | Stage | Grain | Description |
|:---|:---|:---|:---|
| `competition` | Normalized | One row per tournament / competition | Competition metadata |
| `season` | Normalized | One row per competition season | Season timeline |
| `team` | Normalized | One row per canonical basketball team | Canonical team records |
| `player` | Normalized | One row per human athlete | Athlete biometric & listed info |
| `player_team` | Normalized | One row per player-season-team | Club affiliation & jersey |
| `game` | Normalized | One row per basketball match | Master fixture / match entity |
| `game_sources` | Validated | One row per match | Source availability & quality |
| `source_provenance` | Normalized | One row per ingested source file | SHA-256 hash & parser metadata |
| `game_roster` | Normalized | One row per active player per game | Matchday lineup roster |
| `boxscore_team` | Normalized | One row per team per game | Team-level aggregated boxscore |
| `boxscore_player` | Normalized | One row per player per game | Individual traditional boxscore |
| `pbp_event` | Normalized | One row per chronological event | Play-by-play actions |
| `shot` | Normalized | One row per field goal attempt | Spatial coordinates & shot type |
| `lineup_stint` | Derived | One row per 5-man substitution stint | On-court lineup metrics |
| `video` | Normalized | One row per video recording file | Video asset metadata & codec |
| `video_event_sync` | Normalized | One row per sync anchor | PBP event to video timestamp |
| `entity_alias` | Normalized | One row per external provider entity | Fuzzy resolution & confidence |
| `source_conflict_log` | Validated | One row per multi-source discrepancy | Source differences & precedence |
| `validation_log` | Validated | One row per rule evaluation | Quality & integrity audit log |
