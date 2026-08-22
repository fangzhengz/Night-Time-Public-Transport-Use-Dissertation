# Reproducibility Check

- Method: deterministic re-run with random state 42, diagonal
  covariance, n_init 20, reg_covar 1e-06, and
  max_iter 300.
- Verdict: REPRODUCIBLE

| K | BIC         | silhouette | ARI   | ARI_sd | BIC_refit   | AIC_refit   | log_likelihood_per_station | saved_vs_refit_ARI | converged | n_iter | BIC_diff | label_refit_status |
| - | ----------- | ---------- | ----- | ------ | ----------- | ----------- | -------------------------- | ------------------ | --------- | ------ | -------- | ------------------ |
| 5 | -974893.293 | 0.142      | 0.609 | 0.124  | -974893.293 | -987286.258 | 1841.063                   | 1.000              | True      | 26     | 0.000    | MATCH              |
| 6 | -975013.528 | 0.141      | 0.591 | 0.116  | -975013.528 | -989885.805 | 1848.429                   | 1.000              | True      | 35     | 0.000    | MATCH              |

Exact equality is expected for the deterministic reference refit in the current
recorded Python environment. Bootstrap distributions are stochastic analyses
made reproducible through the recorded master seed and parameters.
