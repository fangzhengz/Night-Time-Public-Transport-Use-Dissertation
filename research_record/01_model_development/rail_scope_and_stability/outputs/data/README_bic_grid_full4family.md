# `rail_allmodes_bic_grid_full4family.csv` — read this before quoting its BIC

This file is produced by `src/03b_full_covariance_grid_check.py`, which is a
**covariance-family screen**, not a source of reported fits. It answers one
question: does `diag` beat `spherical`, `tied` and `full` on this data?

It is fitted at `N_INIT = 20`, while the reported clustering
(`src/03_cluster_allmodes.py`) uses `N_INIT = 100`. So the two disagree on the
absolute BIC of the same model:

| source | covariance | K | BIC |
|---|---|---|---|
| `03b` family screen, n_init=20 | diag | 5 | −1,903,182.4 |
| `03` reported fit, n_init=100 | diag | 5 | **−1,903,892.1** |

**−1,903,892.1 is the correct value.** The 440-dimensional feature matrix does
not converge at n_init=20 — it lands on a local optimum 709.7 worse — which is
precisely why `03` was raised to 100 on 2026-08-01.

`03b` was deliberately left at 20 because raising it would cost roughly an hour
of `full`/`tied` fitting to confirm a conclusion that does not change: `full`
and `tied` collapse to K=2 on the current 403-station, 344-dimension sample regardless of
restarts, and `diag` wins by a margin far larger than the convergence gap.

**Quote `03`'s BIC, not this file's.** Use this file only for the family
comparison it exists to make.
