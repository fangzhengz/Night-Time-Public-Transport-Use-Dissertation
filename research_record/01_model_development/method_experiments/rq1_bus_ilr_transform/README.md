# Bus clustering: ILR coordinate validation

CLR was adopted because the Bus features are compositions, yet CLR coordinates contain an exact sum constraint. The ILR experiment asks whether the chosen clusters depend on that redundant coordinate system or instead reflect the underlying compositional geometry. Reproducing the same partitions in a full-rank ILR space provided a numerical validation of the representation, while leaving the substantive K question open.

This is a side-by-side validation of `../rq1_bus_clr_transform`. It keeps the same
hub-first input, 3,365-LSOA modelling sample, alpha=1 empirical-prior zero
replacement, GMM grid, seed and bootstrap design. Only the log-ratio coordinate
representation is changed.

## Coordinate construction

1. Build the same posterior 36-bin composition separately for boardings and
   alightings.
2. Express each direction in a 35-coordinate Helmert ILR basis (70 columns).
3. Remove only exact sample-space redundancies with an orthogonal full-SVD PCA.
   The expected retained rank is 58 because the data also contain exact
   Weekday/Sunday post-midnight duplicates.
4. Fit the GMM in the distance-preserving rank-reduced ILR space.

The 70-coordinate ILR features, fitted 58-coordinate features, Helmert basis,
PCA parameters and distance audits are all saved. The PCA is not used as a
variance-selection device: every non-zero sample-space dimension is retained.

## Fixed design

- `total_activity >= 50`
- `min(boardings, alightings) >= 36`
- one-direction exception LSOAs excluded
- alpha=1 empirical-prior posterior before taking logs
- covariance families: spherical, diag, tied, full
- K=2..12, n_init=20, seed=42, reg_covar=1e-6
- bootstrap K=2..5, 20 replicates by default

## Run

```powershell
python src\01_run_ilr_clustering.py --bootstrap 20
python src\02_ilr_profiles_and_maps.py
python src\03_ilr_kdiag_figure.py
```

All files are written under this folder. No upstream parquet or CLR output is
copied or overwritten.

## Completed result

The 20-bootstrap run completed successfully on 2026-07-21.

- Standard ILR shape: 3,365 x 70; fitted exact-rank shape: 3,365 x 58.
- Retained variance: effectively 100%; maximum sampled ILR-to-rank distance
  error: `9.24e-14`.
- All 44 covariance-by-K fits converged.
- Full covariance remains the global BIC family; BIC prefers K=4.
- ILR K=3 and K=4 reproduce the corresponding CLR partitions exactly
  (`ARI=1.000` for both).
- K=3 bootstrap ARI is 0.862 and mean weakest-cluster Jaccard is 0.873;
  K=4 is 0.788 and 0.427 respectively.

This result confirms that ILR/rank reduction is a numerically cleaner coordinate
implementation of the existing CLR geometry, not a new substantive clustering
solution. K=3 versus K=4 remains a reporting decision between stability and BIC.

Primary reports:

- `outputs/report/ILR_RESULTS.md`
- `outputs/report/ILR_PROFILES_MAPS_GEOGRAPHIC.md`
