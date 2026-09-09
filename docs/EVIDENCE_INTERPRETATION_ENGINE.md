# Universal Evidence & Statistical Interpretation Engine v2
## Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Basketball Intelligence Platform

---

## 1. Philosophy & Core Epistemic Principles

The **Universal Evidence & Statistical Interpretation Engine v2** transforms statistical presentation from isolated numbers and percentiles into an evidence-grounded, progressive disclosure workflow:

```text
               DATA FIRST  ➔  CONTEXT  ➔  INTERPRETATION  ➔  VIDEO HYPOTHESIS
```

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        RAW OBSERVED STATISTIC                          │
│                     e.g. 48.9% 3P (23 Makes / 47 Attempts)             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
┌──────────────┐          ┌──────────────────┐         ┌─────────────────┐
│ DENOMINATOR  │          │ LEAGUE BENCHMARK │         │   SAMPLE SIZE   │
│ & EXPOSURE   │          │  & PERCENTILE    │         │  RELIABILITY    │
│ 47 Attempts  │          │ 100th Percentile │         │ EMERGING SIGNAL │
│ 2.5 3PA/Game │          │  (Median: 25.0%) │         │  (N = 47 3PA)   │
│ (21.9% Diet) │          │ (N = 34 Peers)   │         │                 │
└──────────────┘          └──────────────────┘         └─────────────────┘
      │                            │                            │
      └────────────────────────────┼────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                STRUCTURED EVIDENCE REPRESENTATION                      │
│ - Observation: 23 makes on 47 attempts (48.9% 3P) across 474.9 min     │
│ - Context: 100th percentile among 34 qualified SEA_2025 JBBL peers     │
│ - Volume: 2.5 3PA/G (21.9% of total FGA diet)                          │
│ - Stability: EMERGING_SIGNAL (< 200 3PA stabilization threshold)       │
│ - Interpretation: Strong observed conversion efficiency, but sample is │
│   still emerging rather than established high-volume shooting.         │
│ - Limitations: Contested vs uncontested shot quality tracking absent.   │
│ - Film Question: Inspect assisted catch-and-shoot vs off-the-dribble.  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Metric Relationship Registry & Availability Taxonomy

The engine enforces an explicit availability taxonomy to prevent the fabrication of missing variables:

| Availability Status | Definition | Examples |
| :--- | :--- | :--- |
| **`AVAILABLE`** | Tracked directly in official boxscores / database | Points, FGM, FGA, 3PM, 3PA, FTM, FTA, TRB, AST, TOV, STL, BLK, Minutes |
| **`DERIVABLE`** | Computed via deterministic mathematical formulation | PTS/40, TS%, eFG%, AST/TOV, 3PAr, FTr, Net Rating, ORTG proxy |
| **`NOT_AVAILABLE`** | Not captured by current standard match protocols | Potential assists, hockey assists, deflections, contested rebound %, time of possession |
| **`NOT_IDENTIFIABLE`**| Cannot be causally isolated to an individual player alone | Individual defensive rating, individual plus/minus independent of 5-man lineup synergy |

### Metric Relationships Definition Table:
- **Scoring (`points`)**: Evaluated against FGA, FTA, Minutes, Usage Proxy, PTS/40, and TS%.
- **Perimeter Shooting (`three_pointers_made`)**: Evaluated against 3PA, 3P%, 3P Attempt Rate, and 3PA/Game.
- **Interior Scoring (`two_pointers_made`)**: Evaluated against 2PA, 2P%, and paint shot diet frequency.
- **Playmaking (`assists`)**: Evaluated against Minutes, APG, AST/40, AST/TOV, and Turnovers.
- **Rebounding (`rebounds`)**: Evaluated against Minutes, RPG, REB/40, ORB, DRB, and team glass volume.
- **Defensive Events (`steals`, `blocks`)**: Evaluated as volatile event rates with explicit stabilization cautions.
- **Advanced Ratings (`net_rating`, `ortg`, `drtg`, `on_off`)**: Evaluated strictly as team-level performance during exposure.

---

## 3. Foundational Epistemic Rules

### Rule 1: Volume vs. Efficiency
- **High Volume + High Efficiency**: Recognized as strong offensive production supported by efficient conversion.
- **High Volume + Low Efficiency**: Explicitly identified as volume-driven production rather than efficient shot-making.
- **Low Volume + High Efficiency**: Identified as strong observed conversion within a limited role; does not extrapolate that efficiency would persist under primary usage.

### Rule 2: Raw Production vs. Rate Production
- Never interpret counting stats (e.g. 18.0 PPG, 6.0 APG, 10.5 RPG) without exposure normalization (MPG, PTS/40, AST/40, REB/40).
- High raw totals in 35 MPG are distinguished from identical totals produced in 20 MPG.

### Rule 3: Makes vs. Attempts
- Every positive counting event (e.g. 40 3PM) is connected to its attempt denominator.
- $40	ext{ 3PM} / 80	ext{ 3PA} = 50.0\%$ (high efficiency) produces a completely different interpretation from $40	ext{ 3PM} / 200	ext{ 3PA} = 20.0\%$ (volume/diet driven).

### Rule 4: Percentile $
e$ Evidentiary Certainty
- A player can rank in the **100th percentile** in 3P% while having an **`EMERGING_SIGNAL`** due to small attempt volume ($N=47$).
- Percentile describes current ranking; stability describes empirical reliability.

### Rule 5: Responsible Advanced Rating Attribution
- **Net Rating**: Describes team scoring margin per 100 possessions during floor time. Never formulated as an isolated measure of individual talent.
- **ORTG / DRTG**: Team-level points scored/allowed during exposure. Limitations regarding 5-man spacing, lineup effects, and opponent quality are explicitly attached.
- **On/Off**: Describes observed differential splits without asserting individual causality.

---

## 4. Sample Stability Thresholds

| Domain | `DESCRIPTIVE_ONLY` | `EMERGING_SIGNAL` | `USABLE_SIGNAL` | `ESTABLISHED_SIGNAL` |
| :--- | :--- | :--- | :--- | :--- |
| **Field Goals (FGA)** | $< 25$ FGA | $25	ext{--}74$ FGA | $75	ext{--}149$ FGA | $\ge 150$ FGA |
| **3-Pointers (3PA)** | $< 25$ 3PA | $25	ext{--}74$ 3PA | $75	ext{--}199$ 3PA | $\ge 200$ 3PA |
| **True Shooting (TSA)**| $< 30$ TSA | $30	ext{--}89$ TSA | $90	ext{--}179$ TSA | $\ge 180$ TSA |
| **Free Throws (FTA)** | $< 20$ FTA | $20	ext{--}49$ FTA | $50	ext{--}99$ FTA | $\ge 100$ FTA |
| **Minutes / Playing Time** | $< 40$ min | $40	ext{--}99$ min | $100	ext{--}249$ min | $\ge 250$ min |
| **Defensive Events (STL/BLK)** | $< 50$ min | $50	ext{--}119$ min | $120	ext{--}299$ min | $\ge 300$ min |
| **Team Ratings (Possessions)** | $< 150$ Poss | $150	ext{--}399$ Poss | $400	ext{--}799$ Poss | $\ge 800$ Poss |

---

## 5. Structured Output Architecture

Every interpretation is generated as a structured object before being converted into natural language:

```python
@dataclass
class StructuredEvidenceInterpretation:
    category: str
    metric_name: str
    headline: str
    observation: Dict[str, Any]
    context: Dict[str, Any]
    volume_context: Dict[str, Any]
    efficiency_context: Dict[str, Any]
    stability_tier: str
    interpretation: str
    limitations: List[str]
    film_questions: List[str]
    evidence_level: str = "INTERPRETATION"
```

---

## 6. Verification Suite

The engine is validated by [`tests/test_evidence_interpretation_engine.py`](file:///f:/Falcons%20Falcons%20Prueba/tests/test_evidence_interpretation_engine.py):
- **Test A**: Makes vs Attempts Distinction (40/80 vs 40/200 3PT)
- **Test B**: High Efficiency on Emerging Sample (23/47 3PT)
- **Test C**: High Scoring + High Volume
- **Test D**: High Scoring + High Efficiency
- **Test E**: Assists Contextualization (APG + AST/40 + AST/TOV)
- **Test F**: Rebounds Contextualization (RPG + REB/40 + Glass splits)
- **Test G**: Net Rating Responsible Team Attribution
- **Test H**: ORTG / DRTG Contextual Limitations
- **Test I**: Percentile vs Stability Separation
- **Test J**: Missing Context Handling without Fabrication
- **Test K**: Determinism of Output
- **Test L**: Complete Evidence Hierarchy Validation
