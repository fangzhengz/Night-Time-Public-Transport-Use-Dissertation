# Metric dictionary and reading guide

## Behavioural metrics

| Metric | Definition | Scale used in prose/tables |
|---|---|---|
| `log_total_activity` | natural log of one plus total activity in the adopted window | raw cluster summaries and z-score profiles |
| `direction_balance` | Rail: relative entry/exit balance; Bus: relative boarding/estimated-alighting balance | raw ratio and z-score profile |
| `post_2300_share` | share of adopted-window activity from 23:00 onwards | raw proportion and z-score profile |
| `post_midnight_persistence` | Bus activity after midnight relative to early-evening activity | raw ratio and z-score profile |
| `weekend_ratio` / `weekend_common_ratio` | weekend activity relative to the weekday comparator defined in the mode-specific code | raw ratio and z-score profile |

The formal Bus behavioural panel contains exactly these five metrics. Intermediate feature construction may calculate additional quantities for quality assurance, but they are not part of the formal descriptor set.

## Why a plotted z-score and a prose value can differ

A z-score answers “how far is this cluster mean above or below the mode-wide mean, in standard-deviation units?”. A raw value answers “what is the estimated level of this metric?”. For example, a Bus cluster can have raw post-midnight persistence of 0.155 while its plotted value is a positive z-score. These are two representations of the same underlying cluster summary, not competing estimates.

The evidence chain is:

```text
unit-level raw metric -> cluster mean/median -> mode-standardised z-score
                      -> omnibus test       -> cluster-versus-rest effect size
```

## Statistical quantities

- `R²` in the Rail LNWC composition test is the share of compositional dispersion attributable to the fixed cluster labels under the stated Euclidean composition statistic.
- The associated `p` is a 999-permutation label test (`p=0.001` is the minimum attainable value under the adopted plus-one convention).
- Cramer's V summarises the Bus cluster-by-LNWC contingency association.
- Epsilon-squared summarises a Kruskal–Wallis omnibus association for a continuous contextual variable.
- Rank-biserial correlation summarises a cluster-versus-rest Mann–Whitney contrast.

These effect sizes are not interchangeable and Rail and Bus are not pooled into one formal comparison.
