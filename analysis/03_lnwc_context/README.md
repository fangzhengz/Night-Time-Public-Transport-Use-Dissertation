# 03 · LNWC context

Joins the fixed Rail K=5 / Bus K=4 cluster labels from
`02_mode_specific_clustering/` to (a) behavioural descriptors and (b) the
London Night-time Worker Classification (LNWC). Nothing here refits or
relabels either clustering.

## Scripts (`src/`)

- `run_context_metrics.py` — the formal behavioural descriptors (log total
  activity, directional balance, post-23:00 share, post-midnight persistence,
  weekend-to-weekday ratio for Bus; the Rail equivalent set) plus internal
  cluster-coherence tests.
- `run_lnwc_analysis.py` — the cluster × LNWC association: Rail uses an
  800m Voronoi-clipped catchment composition and a permutation R² test; Bus
  uses the dominant LNWC group per LSOA and a chi-square / Cramér's V test.
- `config.py` — shared paths and parameters for both scripts above.

## Output

`results/tables/lnwc_association_full.csv` and the behavioural summary
tables. See [`docs/analysis_manifest.md`](../../docs/analysis_manifest.md)
for the exact reported statistics (R², p, χ², Cramér's V) and
[`docs/metric_dictionary.md`](../../docs/metric_dictionary.md) for how each
descriptor is defined.
