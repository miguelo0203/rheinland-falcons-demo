# Professional Coach UI & Evidence Presentation Layer — MVP
## Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Basketball Intelligence Platform

---

## 1. Executive Summary & Design Philosophy

The **Professional Coach UI & Evidence Presentation Layer** establishes a clean, dense, evidence-first decision-support interface for the coaching staff and technical directors of Rheinland Falcons Basketball.

The interface adheres strictly to the epistemic hierarchy:

```text
               DATA  ➔  CONTEXT  ➔  INTERPRETATION  ➔  ACTION
```

```text
┌────────────────────────────────────────────────────────────────────────┐
│               RHEINLAND FALCONS BASKETBALL · COACH DOSSIER                 │
│               Lukas Weber | Guard / Wing · 14.8 yrs · 175 cm           │
│               19 GP · 474.9 MIN · 25.0 MPG · 62.5% Rotation Share      │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   EXECUTIVE EVIDENCE KPI GRID (6 CARDS)                │
│  [ SCORING ]      [ EFFICIENCY ]   [ 3PT SHOOTING ]   [ REBOUNDING ]   │
│  25.0 PTS/40      64.0% TS         48.9% 3P           8.3 REB/40       │
│  85th %ile        94th %ile        100th %ile         50th %ile        │
│  ESTABLISHED      ESTABLISHED      EMERGING           ESTABLISHED      │
│  297 PTS·475 MIN  215 FGA·47 FTA   23/47 3PT·21.9%Ar  99 TRB·5.2 RPG   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             PROGRESSIVE DISCLOSURE EVIDENCE CARDS (DATA -> FILM)       │
│  • 1. Observed Production: 23 makes on 47 attempts (48.9% 3P)          │
│  • 2. Context: 100th %ile among N=34 qualified SEA_2025 JBBL peers     │
│  • 3. Interpretation: Strong observed conversion, but sample is        │
│       emerging rather than established high-volume shooting.           │
│  • 4. Volume Diet: 2.5 3PA/G (21.9% of total shot selection)           │
│  • 5. Tactical Film Question: Inspect assisted catch-and-shoot vs pull │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Global Visual Hierarchy & Design System

- **Primary Colors**:
  - FALCONS Primary Blue: `#0284c7` / `#0369a1`
  - Dark Navy / Slate Canvas: `#0f172a` / `#1e293b`
  - Subtle Gold Accent: `#d97706` / `#b45309`
  - Neutral Backgrounds: `#ffffff` / `#f8fafc` / `#f1f5f9`
- **Signal Badges**:
  - `🟢 ESTABLISHED SIGNAL`: High sample volume ($\ge 150	ext{ FGA}, \ge 200	ext{ 3PA}, \ge 250	ext{ MIN}$).
  - `🔵 USABLE SIGNAL`: Moderate sample volume ($75	ext{--}149	ext{ FGA}, 75	ext{--}199	ext{ 3PA}, 100	ext{--}249	ext{ MIN}$).
  - `🟡 EMERGING SIGNAL`: Small sample volume ($25	ext{--}74	ext{ FGA}, 25	ext{--}74	ext{ 3PA}, 40	ext{--}99	ext{ MIN}$).
  - `🔴 DESCRIPTIVE ONLY`: Very small sample ($< 25	ext{ attempts}, < 40	ext{ MIN}$).
- **Typography & Padding**: Clean sans-serif font stack (`Inter`, `system-ui`, `sans-serif`), compact metric spacing, zero wasted screen real-estate.

---

## 3. UI Component Architecture ([`app/components/ui.py`](file:///f:/Falcons%20Falcons%20Prueba/app/components/ui.py))

| Function | Purpose |
| :--- | :--- |
| `get_custom_css()` | Injects global styling, card shadows, pill badges, and typography resets |
| `render_app_header()` | Displays professional club branding, competition, season, and purpose |
| `render_player_identity()` | Renders scouting identity card (biometrics, games, total minutes, MPG, rotation load) |
| `render_kpi_card()` | Renders dense executive KPI card separating metric, percentile, stability, and volume |
| `render_evidence_card()` | Renders 4-tier progressive disclosure evidence card |
| `render_film_card()` | Renders video review hypothesis with prominent non-claim alert |
| `render_provenance_card()`| Renders official benchmark provenance, qualified population $N=34$, and data sync date |

---

## 4. Universal Context & Epistemic Rules Enforced

1. **Metric Value $
e$ Percentile $
e$ Sample Stability $
e$ Volume**:
   - Every card explicitly separates what the player averaged, where they rank in the league, how certain the sample is, and the underlying denominator.
2. **Volume vs. Efficiency**:
   - Differentiates volume-driven vs efficiency-driven profiles.
   - For example, high 3P% on 47 attempts is displayed as `100th percentile` + `EMERGING SIGNAL`.
3. **Advanced Metric Responsibility**:
   - Net Rating, ORTG, DRTG, and On/Off are presented as team performance during exposure rather than isolated individual grades.
4. **Tactical Video Hypotheses**:
   - Explicitly tagged with `📹 VIDEO HYPOTHESIS — NOT A STATISTICAL CLAIM`.

---

## 5. Verification Suite

Tested via [`tests/test_coach_ui_layer.py`](file:///f:/Falcons%20Falcons%20Prueba/tests/test_coach_ui_layer.py):
- `test_01_custom_css_structure`: Confirms CSS class selectors and color codes.
- `test_02_stability_badge_tiers`: Verifies distinct styling for all 4 stability tiers.
- `test_03_kpi_card_rendering`: Verifies KPI cards without `NaN` / `None` leakage.
- `test_04_evidence_card_rendering`: Verifies progressive disclosure sections.
- `test_05_film_card_rendering`: Verifies non-claim standard and video hypothesis rendering.
- `test_06_provenance_card_rendering`: Verifies provenance metadata display.
