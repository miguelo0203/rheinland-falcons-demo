# Statistical Safety & Analysis Protocol

## 1. Epistemic Category Separation

To avoid misleading coaches or fabricating conclusions from observational basketball data, all future analytical insights must strictly distinguish between four distinct epistemic categories:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. DESCRIPTIVE ("What actually happened?")                  │
│    - Factual summaries: Points, Pace, Shot Zone Splits      │
│    - Requires exact counting and mathematical truthfulness   │
├─────────────────────────────────────────────────────────────┤
│ 2. ASSOCIATIONAL ("What variables correlate with winning?") │
│    - Regressions, correlations, Four Factors contributions  │
│    - Must report Confidence Intervals and Effect Sizes      │
├─────────────────────────────────────────────────────────────┤
│ 3. PREDICTIVE ("Can this predict unseen performance?")      │
│    - Out-of-sample testing, cross-validation                │
│    - Strict separation of Training and Test sets            │
├─────────────────────────────────────────────────────────────┤
│ 4. CAUSAL ("What interventions cause outcomes?")            │
│    - PROHIBITED without randomized controlled trials or     │
│      defensible quasi-experimental structural models        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Mandatory Statistical Guidelines

1. **Zero Causal Overreach**: Observational correlation between higher 3PA and win percentage must NEVER be described as *"shooting more 3s causes more wins"*.
2. **Uncertainty Quantification**: All per-possession ratings and player development curves must report sample sizes ($N$), standard errors, or 95% bootstrap confidence intervals.
3. **Small Sample Warnings**: In youth basketball ($N < 10$ games), rate metrics are subject to extreme variance; minimum possession thresholds ($N \ge 100$ possessions) are required before ranking players.
4. **Multiple Comparison Corrections**: When testing hypotheses across 30+ player features, Benjamini-Hochberg FDR correction must be applied.