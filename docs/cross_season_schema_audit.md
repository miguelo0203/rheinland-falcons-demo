# Cross-Season Schema Stability Audit

## 1. Multi-Season Schema Comparison (Seasons 2017–2025)

An automated schema difference analysis was performed across REST endpoints and Socket.IO payloads spanning 8 consecutive seasons.

### Key Schema Findings:
1. **REST Endpoints (`/v2/schedule`, `/v2/teams`, `/v2/game/{id}`)**:
   - **Symmetric Difference**: **0 added / removed keys** between modern season 2025 and historical seasons 2017, 2021, 2023.
   - Endpoint parameter structure (`seasonId={YYYY}`) is 100% stable.
2. **Socket.IO Array Protocol (Packet Types 0, 1, 2, 3, 4, 7)**:
   - **Type 2 (`team_stats`)**: `P2_points` represents Made 2-Point field goals ($2\text{PM}$ count); `P3_points` represents Made 3-Point field goals ($3\text{PM}$ count) across all seasons.
   - **Type 4 (`player_stats`)**: `points` represents total points scored by athlete, while `P2_points` and `P3_points` represent made shot counts.
   - **Type 0 (`scorelist`)**: Modern seasons (2024, 2025) maintain live running scorelists; archival seasons (2017–2023) omit packet type 0 in stream history (relying on PBP action running scores).
3. **Biometric Field Units**:
   - `height` is consistently delivered as a floating-point number in meters (e.g. `1.96` $\to$ normalized to $196.0\text{ cm}$).
   - `weight` is delivered in kilograms (e.g. `84`).
   - `birthDate` is consistently formatted as ISO-8601 `YYYY-MM-DD`.