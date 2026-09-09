# Empirical Audit: League Benchmark Temporal Context & Isolation

---

## 1. Executive Summary & Verdict

This audit examines the exact SQL, Python, and database mechanisms used to construct the JBBL qualified player benchmark population and compute player percentile ranks in the Rheinland Falcons Basketball intelligence platform.

### FINAL CONCLUSION:
> `REQUIRES FIX`

### Summary of Audit Findings:
1. **Season Isolation**: ❌ **NOT GUARANTEED** in current implementation. `get_qualified_league_benchmark()` queries `boxscore_player` globally without filtering by `season_id`. As a result, the current benchmark pool of **47 players** mixes **34 players from 2025/26 (`SEA_2025`)**, **11 players from 2023/24 (`SEA_2023`)**, and **2 synthetic placeholder entries (`PLY_None`)** aggregated across multiple seasons.
2. **Competition Isolation**: ❌ **NOT GUARANTEED** in current implementation. There is no filter on `competition_id = 'CMP_JBBL'` or `game_type = 'OFFICIAL'`, creating a risk of mixing future practice/scrimmage boxscores or NBBL games into the JBBL normative baseline.
3. **Qualification Threshold**: ✅ **Enforced at $\ge 100.0$ minutes** (`HAVING SUM(bp.seconds_played)/60.0 >= 100.0`).
4. **Temporal Look-Ahead**: The current benchmark uses **Full-Season Cumulative Data** (retrospective season benchmark). While methodologically sound for historical season analysis, a live in-season system requires a through-date or weekly-snapshot paradigm to prevent look-ahead bias during an active campaign.

---

## 2. Exact Current Benchmark Definition & SQL Query Path

### 2.1. Current Python Service Implementation
Located in [`app/services/data_service.py`](file:///f:/Falcons%20Falcons%20Prueba/app/services/data_service.py#L121-L171):

```python
def get_qualified_league_benchmark(self, min_minutes: float = 100.0) -> pd.DataFrame:
    """Computes / retrieves distribution metrics for all qualified JBBL players."""
    if self._league_benchmarks_cache is not None:
        return self._league_benchmarks_cache

    q = f"""
    WITH p_totals AS (
        SELECT 
            bp.player_id,
            bp.team_id,
            p.canonical_name,
            COUNT(DISTINCT bp.game_id) as gp,
            SUM(bp.seconds_played)/60.0 as total_min,
            SUM(bp.points) as total_pts,
            AVG(bp.points) as ppg,
            SUM(bp.fga) as total_fga,
            SUM(bp.fgm) as total_fgm,
            SUM(bp.fg3a) as total_fg3a,
            SUM(bp.fg3m) as total_fg3m,
            SUM(bp.fta) as total_fta,
            SUM(bp.ftm) as total_ftm,
            SUM(bp.trb) as total_trb,
            SUM(bp.ast) as total_ast,
            SUM(bp.stl) as total_stl,
            SUM(bp.blk) as total_blk,
            SUM(bp.tov) as total_tov
        FROM boxscore_player bp
        JOIN player p ON bp.player_id = p.player_id
        GROUP BY bp.player_id, bp.team_id, p.canonical_name
        HAVING SUM(bp.seconds_played)/60.0 >= {min_minutes}
    )
    SELECT 
        *,
        ROUND(total_pts * 40.0 / total_min, 1) as pts_per_40,
        ROUND(total_trb * 40.0 / total_min, 1) as reb_per_40,
        ROUND(total_ast * 40.0 / total_min, 1) as ast_per_40,
        ROUND(total_stl * 40.0 / total_min, 1) as stl_per_40,
        ROUND(total_blk * 40.0 / total_min, 1) as blk_per_40,
        ROUND((total_stl + total_blk) * 40.0 / total_min, 1) as def_disruption,
        ROUND(total_tov * 40.0 / total_min, 1) as tov_per_40,
        CASE WHEN total_tov > 0 THEN ROUND(total_ast * 1.0 / total_tov, 2) ELSE total_ast END as ast_to_tov,
        CASE WHEN total_fga > 0 THEN ROUND(total_fgm * 100.0 / total_fga, 1) ELSE NULL END as fg_pct,
        CASE WHEN total_fg3a > 0 THEN ROUND(total_fg3m * 100.0 / total_fg3a, 1) ELSE NULL END as fg3_pct,
        CASE WHEN (2 * (total_fga + 0.44 * total_fta)) > 0 THEN ROUND(total_pts * 100.0 / (2 * (total_fga + 0.44 * total_fta)), 1) ELSE NULL END as ts_pct,
        CASE WHEN total_fga > 0 THEN ROUND(total_fg3a * 100.0 / total_fga, 1) ELSE NULL END as f3a_rate,
        CASE WHEN total_fga > 0 THEN ROUND(total_fta * 100.0 / total_fga, 1) ELSE NULL END as ft_rate
    FROM p_totals;
    """
    df_bench = self.conn.execute(q).df()
    self._league_benchmarks_cache = df_bench
    return df_bench
```

### 2.2. Root Cause of Cross-Season Mixing
1. **Missing `JOIN game g ON bp.game_id = g.game_id`**: The table `boxscore_player` does not store `season_id` directly (it stores `game_id`). Without joining `game`, the query aggregates all matches in the database.
2. **Missing `WHERE g.season_id = ...` Filter**: No season scoping is applied.
3. **Missing Cache Invalidation Key**: `self._league_benchmarks_cache` caches a single global DataFrame regardless of the selected season in the Streamlit UI.

---

## 3. Database Census: Qualified Population Composition

The database `database/jbbl_sandbox.duckdb` currently holds 65 total games across two historical seasons:
- **`SEA_2023` (2023/24 Season)**: 17 games, 449 player-game rows, 127 unique players.
- **`SEA_2025` (2025/26 Season)**: 48 games (43 with boxscores), 1,006 player-game rows, 385 unique players.

### Breakdown of the Current 47-Player Benchmark:
| Contributing Season | Qualified Player Count ($\ge 100$ min) | Notes |
| :--- | :--- | :--- |
| **`SEA_2025` Only** | **34 players** | True 2025/26 JBBL comparison universe |
| **`SEA_2023` Only** | **11 players** | Historical 2023/24 players (e.g. Constantin Clemens, Ilkay Sertel, Leon Blank) |
| **Cross-Season Mixed** | **2 entries** | Unmapped placeholder ID `PLY_None` across different teams |
| **CURRENT TOTAL** | **47 players** | **Unintentionally pooled across 2 separate seasons** |

When isolated strictly to **`SEA_2025` Official JBBL Games**, the true qualified population size is **$N=34$ players**.

---

## 4. Empirical Case Studies: Impact of Season Mixing on Percentiles

### 4.1. Case Study 1: Lukas Weber (`PLY_DEMO_101`, Season `SEA_2025`)
- **Season Volume**: 19 GP, 474.9 MIN, 297 PTS (15.6 PPG), 23/47 3PT (48.9%), 57 AST / 56 TOV.

| Metric | Player Value | Current Mixed Benchmark ($N=47$) | Isolated `SEA_2025` Benchmark ($N=34$) | Percentile Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Scoring Rate (`pts_per_40`)** | **25.0** | **89.4th %ile** (Median: 15.0) | **85.3th %ile** (Median: 16.9) | **-4.1%** |
| **True Shooting (`ts_pct`)** | **64.0%** | **95.7th %ile** (Median: 47.6%) | **94.1th %ile** (Median: 49.1%) | **-1.6%** |
| **3-Point Shooting (`fg3_pct`)** | **48.9%** | **100.0th %ile** (Median: 24.7%) | **100.0th %ile** (Median: 25.0%) | **0.0% (Rank #1)** |
| **Rebounding (`reb_per_40`)** | **8.3** | **53.2th %ile** (Median: 6.8) | **50.0th %ile** (Median: 8.4) | **-3.2%** |
| **Playmaking (`ast_per_40`)** | **4.8** | **83.0th %ile** (Median: 2.7) | **79.4th %ile** (Median: 3.5) | **-3.6%** |
| **Ball Security (`ast_to_tov`)** | **1.02** | **74.5th %ile** (Median: 0.7) | **70.6th %ile** (Median: 0.8) | **-3.9%** |

*Insight*: The 2023/24 cohort in the database had lower per-minute medians in scoring and playmaking. Including them artificially inflated Lukas Weber's percentile ranks by 3–4 percentile points.

---

### 4.2. Case Study 2: Maximilian Becker (`PLY_DEMO_104`, Season `SEA_2025`)
- **Season Volume**: 21 GP, 426.1 MIN, 254 PTS (12.1 PPG), 221 REB (10.5 RPG), 112/183 2PT (61.2%).

| Metric | Player Value | Current Mixed Benchmark ($N=47$) | Isolated `SEA_2025` Benchmark ($N=34$) | Percentile Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Scoring Rate (`pts_per_40`)** | **23.8** | **87.2th %ile** (Median: 15.0) | **82.4th %ile** (Median: 16.9) | **-4.8%** |
| **True Shooting (`ts_pct`)** | **60.0%** | **89.4th %ile** (Median: 47.6%) | **85.3th %ile** (Median: 49.1%) | **-4.1%** |
| **Rebounding (`reb_per_40`)** | **20.7** | **100.0th %ile** (Median: 6.8) | **100.0th %ile** (Median: 8.4) | **0.0% (Rank #1)** |
| **Playmaking (`ast_per_40`)** | **1.4** | **17.0th %ile** (Median: 2.7) | **14.7th %ile** (Median: 3.5) | **-2.3%** |
| **Ball Security (`ast_to_tov`)** | **0.31** | **23.4th %ile** (Median: 0.7) | **14.7th %ile** (Median: 0.8) | **-8.7%** |

*Insight*: Maximilian Becker remains the undisputed #1 rebounder in both benchmarks (100th percentile), but his scoring and TS% ranks were previously calculated against players who played in a different season two years earlier.

---

### 4.3. Case Study 3: Henry Keller (`PLY_DEMO_102`, Season `SEA_2025`)
- **Season Volume**: 22 GP, 523.1 MIN, 273 PTS (12.4 PPG), 68 AST, 52 TOV (AST/TOV: 1.31).

| Metric | Player Value | Current Mixed Benchmark ($N=47$) | Isolated `SEA_2025` Benchmark ($N=34$) | Percentile Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Scoring Rate (`pts_per_40`)** | **18.0** | **63.8th %ile** (Median: 15.0) | **58.8th %ile** (Median: 16.9) | **-5.0%** |
| **True Shooting (`ts_pct`)** | **49.2%** | **57.4th %ile** (Median: 47.6%) | **52.9th %ile** (Median: 49.1%) | **-4.5%** |
| **Playmaking (`ast_per_40`)** | **4.5** | **76.6th %ile** (Median: 2.7) | **70.6th %ile** (Median: 3.5) | **-6.0%** |
| **Ball Security (`ast_to_tov`)** | **1.31** | **89.4th %ile** (Median: 0.7) | **88.2th %ile** (Median: 0.8) | **-1.2%** |

---

## 5. Detailed Evaluation of the 5 Methodological Criteria

### A. Current Behavior
- **Rows Ingested**: All rows in `boxscore_player` where `SUM(seconds_played)/60.0 >= 100.0`, grouped by `(player_id, team_id, canonical_name)`.
- **Filtering**: No `season_id`, `competition_id`, or `game_type` clauses are present in the query.

### B. Season Isolation: ❌ FAILED
- A player from `SEA_2023` is currently pooled into the same benchmark distribution as a player from `SEA_2025`.
- Furthermore, if a player with the same ID had minutes in both seasons, their minutes and counting stats would be erroneously summed across seasons.

### C. Competition Isolation: ❌ FAILED
- There is no filter for `competition_id = 'CMP_JBBL'` or `game_type = 'OFFICIAL'`. If NBBL or practice games are registered in `boxscore_player`, they will pollute the JBBL benchmark.

### D. Qualification Threshold: ✅ VERIFIED
- Enforced at `HAVING SUM(bp.seconds_played)/60.0 >= 100.0`.
- Mathematical denominator is strictly minutes played (seconds played / 60.0).

### E. Temporal Look-Ahead: Full-Season Cumulative
- **Current Mode**: Retrospective Full-Season Benchmark.
- For historical seasons (e.g. completed 2025/26), this compares cumulative season performance against qualified peer cumulative season performance.
- For live in-season tracking (e.g. 2026/27 season as games arrive week-by-week), the benchmark must support a `through_date` or `as_of_game_date` parameter to avoid comparing game 4 performance against game 20 league outcomes.

---

## 6. Recommended Exact Specification & Fix

To achieve rigorous methodological integrity, the following changes are specified:

### 6.1. Updated Query Architecture for `get_qualified_league_benchmark()`
```sql
WITH p_totals AS (
    SELECT 
        bp.player_id,
        bp.team_id,
        p.canonical_name,
        COUNT(DISTINCT bp.game_id) as gp,
        SUM(bp.seconds_played)/60.0 as total_min,
        SUM(bp.points) as total_pts,
        AVG(bp.points) as ppg,
        SUM(bp.fga) as total_fga,
        SUM(bp.fgm) as total_fgm,
        SUM(bp.fg2a) as total_fg2a,
        SUM(bp.fg2m) as total_fg2m,
        SUM(bp.fg3a) as total_fg3a,
        SUM(bp.fg3m) as total_fg3m,
        SUM(bp.fta) as total_fta,
        SUM(bp.ftm) as total_ftm,
        SUM(bp.trb) as total_trb,
        SUM(bp.ast) as total_ast,
        SUM(bp.stl) as total_stl,
        SUM(bp.blk) as total_blk,
        SUM(bp.tov) as total_tov
    FROM boxscore_player bp
    JOIN player p ON bp.player_id = p.player_id
    JOIN game g ON bp.game_id = g.game_id
    WHERE g.season_id = :season_id
      AND g.competition_id = :competition_id
      AND g.game_type = :game_type
      AND bp.player_id != 'PLY_None'
      AND (:as_of_date IS NULL OR g.game_date <= :as_of_date)
    GROUP BY bp.player_id, bp.team_id, p.canonical_name
    HAVING SUM(bp.seconds_played)/60.0 >= :min_minutes
)
SELECT 
    *,
    ROUND(total_pts * 40.0 / total_min, 1) as pts_per_40,
    ROUND(total_trb * 40.0 / total_min, 1) as reb_per_40,
    ROUND(total_ast * 40.0 / total_min, 1) as ast_per_40,
    ROUND(total_stl * 40.0 / total_min, 1) as stl_per_40,
    ROUND(total_blk * 40.0 / total_min, 1) as blk_per_40,
    ROUND((total_stl + total_blk) * 40.0 / total_min, 1) as def_disruption,
    ROUND(total_tov * 40.0 / total_min, 1) as tov_per_40,
    CASE WHEN total_tov > 0 THEN ROUND(total_ast * 1.0 / total_tov, 2) ELSE total_ast END as ast_to_tov,
    CASE WHEN total_fga > 0 THEN ROUND(total_fgm * 100.0 / total_fga, 1) ELSE NULL END as fg_pct,
    CASE WHEN total_fg3a > 0 THEN ROUND(total_fg3m * 100.0 / total_fg3a, 1) ELSE NULL END as fg3_pct,
    CASE WHEN (2 * (total_fga + 0.44 * total_fta)) > 0 THEN ROUND(total_pts * 100.0 / (2 * (total_fga + 0.44 * total_fta)), 1) ELSE NULL END as ts_pct,
    CASE WHEN total_fga > 0 THEN ROUND(total_fg3a * 100.0 / total_fga, 1) ELSE NULL END as f3a_rate,
    CASE WHEN total_fga > 0 THEN ROUND(total_fta * 100.0 / total_fga, 1) ELSE NULL END as ft_rate
FROM p_totals;
```

### 6.2. Parameterization in `DataService`
1. Update signature to:
   ```python
   def get_qualified_league_benchmark(
       self,
       season_id: str = "SEA_2025",
       competition_id: str = "CMP_JBBL",
       game_type: str = "OFFICIAL",
       min_minutes: float = 100.0,
       as_of_date: Optional[str] = None
   ) -> pd.DataFrame:
   ```
2. Update cache key to dictionary: `self._benchmarks_dict_cache[(season_id, competition_id, game_type, min_minutes, as_of_date)]`.
3. In `get_player_dossier(player_id, season_id)`: Pass `season_id=season_id` to `get_qualified_league_benchmark()`.

---

## 7. Resolution & Verification Status: ✅ RESOLVED

The recommended fixes have been implemented and verified:
1. **Full Season Isolation Implemented**: `get_qualified_league_benchmark()` now strictly filters by `game.season_id = ?`, completely eliminating multi-season pooling.
2. **Competition & Game Type Isolation Implemented**: Added `game.competition_id = ?` and `game.game_type = ?`.
3. **Synthetic Exclusion Implemented**: Added `bp.player_id != 'PLY_None'`.
4. **As-Of Date Parameter Implemented**: Optional `as_of_date` enforces cutoff before player minute qualification.
5. **Dossier & UI Updated**: Provenance metadata (`benchmark_meta`) is embedded in all dossiers and displayed in Streamlit cards/captions.
6. **Automated Regression Suite**: 8 dedicated regression tests in `tests/test_benchmark_temporal_isolation.py` (Tests A–H) pass with 100% success rate.

