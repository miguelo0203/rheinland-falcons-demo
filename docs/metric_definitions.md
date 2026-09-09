# Derived Basketball Metrics — Formal Definitions, Formulas & Boundaries

## 1. Possession & Pace Framework

### Estimated Possessions (Pace Model)
$$\text{Possessions}_{\text{basic}} = \text{FGA} + 0.44 \times \text{FTA} - \text{OREB} + \text{TOV}$$

$$\text{Possessions}_{\text{exact}} = 0.5 \times \left[ (\text{FGA}_A + 0.44 \times \text{FTA}_A - \text{OREB}_A + \text{TOV}_A) + (\text{FGA}_B + 0.44 \times \text{FTA}_B - \text{OREB}_B + \text{TOV}_B) \right]$$

* **Assumptions**: The $0.44$ coefficient models and-one opportunities, technical free throws, and 3-shot fouls in FIBA youth basketball.
* **Limitations**: Dead-ball team rebounds and technical foul sequences may cause slight deviations from discrete play-by-play possession parsing.
* **Applicability to JBBL**: Fully applicable for team-level efficiency calculations in 40-minute games.

---

## 2. Four Factors Framework (Dean Oliver)

1. **Effective Field Goal Percentage (eFG%)**:
   $$\text{eFG\%} = \frac{\text{FGM} + 0.5 \times \text{3PM}}{\text{FGA}}$$
2. **Turnover Ratio (TOV%)**:
   $$\text{TOV\%} = \frac{\text{TOV}}{\text{FGA} + 0.44 \times \text{FTA} + \text{TOV}}$$
3. **Offensive Rebound Percentage (ORB%)**:
   $$\text{ORB\%} = \frac{\text{OREB}}{\text{OREB} + \text{Opponent DREB}}$$
4. **Free Throw Rate (FTr)**:
   $$\text{FTr} = \frac{\text{FTA}}{\text{FGA}}$$

---

## 3. Offensive & Defensive Ratings

* **Offensive Rating (ORtg)**:
  $$\text{ORtg} = 100 \times \frac{\text{Points Scored}}{\text{Possessions}}$$
* **Defensive Rating (DRtg)**:
  $$\text{DRtg} = 100 \times \frac{\text{Points Allowed}}{\text{Possessions}}$$
* **Net Rating (NetRtg)**:
  $$\text{NetRtg} = \text{ORtg} - \text{DRtg}$$

---

## 4. Individual Player Metrics

* **True Shooting Percentage (TS%)**:
  $$\text{TS\%} = \frac{\text{PTS}}{2 \times (\text{FGA} + 0.44 \times \text{FTA})}$$
* **Usage Percentage (USG%)**:
  $$\text{USG\%} = 100 \times \frac{(\text{FGA} + 0.44 \times \text{FTA} + \text{TOV}) \times (\text{Team Minutes} / 5)}{\text{Minutes} \times (\text{Team FGA} + 0.44 \times \text{Team FTA} + \text{Team TOV})}$$
* **Assists-to-Turnover Ratio (AST/TOV)**:
  $$\text{AST/TOV} = \frac{\text{AST}}{\max(1, \text{TOV})}$$