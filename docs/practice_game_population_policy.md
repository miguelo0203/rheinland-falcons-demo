# Practice & Scrimmage Game Population Policy

## 1. Strict Mathematical Isolation Layer
1. **Official Competition Benchmarks**: All official league tables, standings, Four Factors, percentiles, and season win percentages are computed STRICTLY over `game_type == 'OFFICIAL'`.
2. **Practice / Scrimmage Inclusion**: Practice, scrimmage, and friendly fixtures are preserved and queryable for internal player development, workload tracking, and tactical experimentation.
3. **No Silent Mixing**: Every UI view explicitly presents its population denominator (e.g. `17 Official + 4 Practice`).