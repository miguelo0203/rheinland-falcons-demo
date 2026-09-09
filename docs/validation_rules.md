# Validation Engine & Reconciliation Rules

## 1. Rule Catalog

| Rule ID | Category | Severity | Description |
|:---|:---|:---|:---|
| `RULE_GAM_001` | GAME_LEVEL | CRITICAL | Home and away teams must be distinct entities. |
| `RULE_GAM_004` | GAME_LEVEL | CRITICAL | Game scores cannot be negative numbers. |
| `RULE_PLY_001` | PLAYER_LEVEL | CRITICAL | Player boxscore statistics must be non-negative. |
| `RULE_PLY_002` | PLAYER_LEVEL | ERROR | FGM <= FGA and FTM <= FTA. |
| `RULE_PLY_003` | PLAYER_LEVEL | ERROR | Playing time cannot exceed total match duration. |
| `RULE_BXC_PTS_SUM` | BOXSCORE_RECONCILIATION | ERROR | Sum of individual player points equals team points. |
| `RULE_BXC_REB_SUM` | BOXSCORE_RECONCILIATION | WARNING | Player rebounds + team rebounds equal total rebounds. |
| `RULE_PBP_FINAL_SCORE` | PBP_RECONCILIATION | ERROR | PBP cumulative score matches final match score. |
| `RULE_PBP_CLOCK_MONO` | PBP_RECONCILIATION | WARNING | Event timestamps strictly descend monotonically. |
| `RULE_PBP_PTS_RECON` | PBP_RECONCILIATION | ERROR / WARNING | Player points in PBP match or bound boxscore. |
