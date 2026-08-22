# Hub-first bus alpha-grid screen

Empirical-prior smoothing was introduced to reduce the volatility of sparse temporal shares, but a stronger prior can also wash out the very rhythms the clustering is meant to detect. This screen traces that trade-off across a fixed sample and model. It asks not simply whether smoothing produces tidier clusters, but whether any gain in activity balance is purchased by weaker repeatability or excessive prior influence.

This is a thin, side-by-side experiment. It does not modify or copy the
canonical hub-first preprocessing or the existing alpha=0/5 outputs.

## Question

Can stronger direction-specific empirical-prior shrinkage reduce the
association between K=3 labels and activity volume without erasing temporal
rhythm or making low-activity labels mostly prior-driven?

## Fixed factors

- Exact 3,593-LSOA sample from `rq1_bus_hub_first_reclustering`
- Hub-first long-count input and one-direction exception logic
- 72 full-week features: 36 boarding shares + 36 alighting shares
- K=3, full covariance, n_init=20, seed=42, reg_covar=1e-6
- Same conditional multinomial count-resamples for every alpha

Only alpha varies: `0, 5, 20, 50, 100, 200`.

## Confirmed command

```powershell
py -3 src\run_alpha_grid_screen.py --alphas 0 5 20 50 100 200 --k 3 --covariance full --n-init 20 --seed 42 --replicates 20
```

The main report is `outputs/report/ALPHA_GRID_SCREEN.md`.

## Interpretation boundary

The count-resampling diagnostic measures conditional repeatability under a
multinomial sampling approximation with the fitted GMM held fixed. It is not
an external validation, a temporal holdout, or a replacement for the full
model/bootstrap analysis of a shortlisted alpha.
