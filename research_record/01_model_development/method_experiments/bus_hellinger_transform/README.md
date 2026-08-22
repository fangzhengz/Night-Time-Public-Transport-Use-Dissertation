# Bus clustering: Hellinger (square-root share) sensitivity

CLR addressed the compositional nature of the Bus profiles, but it also required a strategy for zeros. Hellinger geometry offered a seemingly attractive alternative because it could preserve exact zeros without pseudo-count replacement. This experiment asks whether that change actually reduced the degree to which sparsity organised the clusters while retaining their temporal meaning. It did not pass its pre-declared adoption gate, making it an informative negative result rather than an abandoned file.

Side-by-side sensitivity test for the accepted hub-first bus sample. The test
keeps the same 3,365 LSOAs, 72 direction-by-day-by-hour cells, GMM search,
random seed, and bootstrap design used by the raw-share and CLR versions. The
only feature change is, independently within each 36-cell direction block:

```text
raw count -> direction-normalised share p -> sqrt(p)
```

The square-root transform retains exact zeros and therefore requires neither a
pseudo-count nor empirical-Bayes zero replacement. Euclidean distance between
the transformed rows is proportional to Hellinger distance.

## Run

```powershell
py -3 src\run_hellinger_analysis.py --bootstrap 20
py -3 src\verify_selected_solution.py
```

## Fixed experiment contract

- Input/sample: the official hub-first raw-share feature matrix, 3,365 LSOAs.
- Time structure: Weekday/Saturday/Sunday, 18:00-05:00, hourly.
- Directions: boardings and alightings normalised separately.
- Model search: GMM, covariance in spherical/diag/tied/full, K=2..12,
  `n_init=20`, `seed=42`, `reg_covar=1e-6`.
- Bootstrap: K=2..8, 20 resamples, `n_init=3`.
- Reporting K: lowest within-transform BIC among solutions with minimum cluster
  share >=5%, bootstrap ARI >=0.70, and weakest matched-cluster Jaccard >=0.50.
- Transform acceptance: the reporting solution must also reduce zero-bin eta2
  by at least 25% relative to CLR at the same K and retain at least 85% of CLR's
  mean timing eta2.

Absolute BIC is not compared across raw-share, CLR, and Hellinger spaces.

## Main outputs

- `outputs/report/HELLINGER_RESULTS.md`
- `outputs/report/HELLINGER_PROFILES_MAPS_GEOGRAPHIC.md`
- `outputs/figures/hellinger_kdiag_full.png`
- `outputs/figures/hellinger_selected_profiles.png`
- `outputs/figures/hellinger_selected_map.png`
- `outputs/figures/hellinger_selected_feature_heatmap.png`
- K=2..8 profile and map figures, matching the raw-share output coverage.
