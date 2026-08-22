## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: validate
- Origin Date: 2026-07-21
- Verification Status: VERIFIED
- Version Label: bus_hellinger_validation_v1

# Hellinger bus-clustering validation report

## Overall verdict

**The experiment is reproducible, but Hellinger fails as a replacement for the
current CLR treatment under the pre-declared construct-validity gate.**

The full-covariance Hellinger solution selects K=3 by within-transform BIC and
is stable under bootstrap. However, its labels track exact-zero hourly cells
more strongly than the CLR K=3 labels. The method therefore changes the
geometry without separating service/activity coverage from temporal demand
shape.

## Statistical findings

| Finding | Hellinger K=3 | Comparator | Confidence |
|---|---:|---:|---|
| Within-transform BIC choice | K=3, full covariance | K=2 is the only other solution passing all size/stability/Jaccard gates | SOLID |
| Silhouette | 0.0861 | raw 0.0546; CLR 0.1932; magnitudes are not directly comparable across transforms | CAUTION |
| Bootstrap ARI | 0.8724 | raw 0.6075; CLR 0.8618 | SOLID |
| Weakest matched-cluster Jaccard | 0.8541 | raw 0.3963; CLR 0.8729 | SOLID |
| Zero-bin eta-squared | 0.8590 | raw 0.5402; CLR 0.8282 | RED_FLAG for demand-shape interpretation |
| Activity eta-squared | 0.5619 | raw 0.5018; CLR 0.5585 | CAUTION |
| Mean timing eta-squared | 0.1702 | raw 0.2791; CLR 0.1893 | CAUTION |
| Zero-effect reduction versus CLR | -3.7% | required at least +25% | FAIL |
| Timing-effect retention versus CLR | 90.0% | required at least 85% | PASS |
| Central/outer total variation | 0.2876 | raw K=3 0.3690; CLR K=3 0.3565 | descriptive only |

## Cluster interpretation check

The K=3 signatures confirm that the main separation is zero/coverage related:

- C0 (n=1,136) averages 22.78 zero cells and has the lowest activity,
  post-midnight share, deep-night share, persistence, and weekend ratio.
- C1 (n=1,309) averages 0.48 zero cells and has the highest activity.
- C2 (n=920) averages 4.15 zero cells and has the largest deep-night share and
  persistence, but its temporal profile is otherwise close to C1.

The temporal figure therefore shows graded late-night persistence/coverage,
not three strongly distinct evening-demand archetypes.

## Reproducibility

- Method: deterministic refit of the selected K=3/full-covariance solution.
- Same saved Hellinger matrix, seed=42, n_init=20, reg_covar=1e-6,
  max_iter=300.
- Saved versus refitted labels: exact row-wise equality; ARI=1.0000.
- BIC absolute difference: 0.0.
- Verdict: **REPRODUCIBLE**.

## Output integrity

- BIC grid: 44/44 expected covariance-by-K rows.
- K diagnostics: 11/11 expected K rows.
- Bootstrap: 140/140 expected rows (K=2..8, 20 each).
- Labels: 11/11 expected K files.
- Temporal profiles: 7/7 expected K=2..8 figures.
- Spatial maps: 7/7 expected K=2..8 figures.
- Selected profile, map, and feature-heatmap figures: present and visually
  inspected; titles, axes, legends, sample sizes, and full London coverage render.
- Non-fatal environment warning: joblib could not identify physical-core count
  and used logical cores. It did not affect convergence or deterministic output.

## Fallacy scan

- Coverage: **11/11 statistical fallacy types checked**.

| Fallacy | Status | Current relevance |
|---|---|---|
| Simpson's paradox | NOTE | Profiles are displayed separately by day type; no aggregate-versus-day reversal is claimed. |
| Ecological fallacy | CAUTION | LSOA clusters cannot identify individual passengers or individual behaviour. |
| Berkson/selection bias | CAUTION | The retained sample excludes low-flow and one-direction-exception LSOAs; coverage is explicit. |
| Collider bias | NOTE | No covariate-adjusted causal model is fitted. |
| Base-rate neglect | NOTE | This is not a diagnostic-classification accuracy study. |
| Regression to the mean | NOTE | There is no selected-extreme pre/post comparison. |
| Survivorship bias | CAUTION | Interpretation applies to the retained 3,365 LSOAs, not all London LSOAs. |
| Look-elsewhere effect | CAUTION | Multiple K and transformations are examined; complete grids and failed gates are retained. |
| Garden of forking paths | CAUTION | Hellinger was motivated after observing CLR zero sensitivity; the fixed contract and failed acceptance gate must remain reported. |
| Correlation versus causation | CAUTION | Cluster associations with zero count, activity, or geography are descriptive, not causal. |
| Reverse causality | NOTE | No directional causal claim is made. |

## Decision boundary

Do not promote Hellinger K=3 to the final bus demand-shape model. Retain it as a
negative sensitivity result demonstrating that a zero-tolerant distance alone
does not solve the construct problem. The next method, if pursued, should
explicitly separate service/active-hour coverage from conditional temporal
demand shape rather than applying another coordinate transform to the same 72
cells.
