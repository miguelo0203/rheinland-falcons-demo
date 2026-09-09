# Statistical Safeguards & Epistemic Separation Protocol

1. **Epistemic Classifications**:
   - `DESCRIPTIVE`: Directly observed counting statistics and boxscore summaries.
   - `ASSOCIATIONAL`: Empirical regressions and correlation coefficients.
   - `HYPOTHESIS`: Tactical patterns requiring video clip review.
   - `INSUFFICIENT_DATA`: Samples below minimum statistical thresholds ($N < 4$).
2. **Multiple Testing Control**: Benjamini-Hochberg FDR at $q = 0.05$.
3. **Bootstrap Resampling**: 95% Confidence Intervals computed via 1,000 iterations.