## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: 2026-07-21
- Verification Status: VERIFIED
- Version Label: rail_ilr_reproducibility_v1

# Rail ILR reproducibility check

## Method

The complete experiment was run twice with the same inputs, package environment,
random state, GMM parameters, 200 bootstrap resamples, and 20 full-data seed
refits. The second run used the independent output root `outputs_repro` and did
not overwrite `outputs`.

## Verdict

**REPRODUCIBLE.** All 36 prespecified artifact groups matched exactly after
excluding expected wall-clock and timestamp/path fields.

## Exact comparisons

- 342-dimensional ILR feature matrix: exact numeric match;
- K=2 through K=12 label files, posterior maxima, and entropy: exact match;
- four-covariance BIC grid: exact match after excluding `fit_seconds`;
- diagonal K diagnostics and cluster silhouettes: exact match;
- all 200 bootstrap iteration and summary tables: exact match;
- all 20 seed-refit iteration and summary tables: exact match;
- raw-versus-ILR label comparison and station transition detail: exact match;
- transformation-driver eta-squared and distance correlations: exact match;
- coordinate audit and final result summary dictionaries: exact match;
- all nine PNG figures: byte-identical SHA-256 matches.

## Runtime

- Canonical run: 87.2 seconds;
- independent re-run: 79.4 seconds.

Runtime was not treated as a deterministic metric.

## Recorded anomaly

Both runs emitted NumPy runtime warnings while calculating posterior entropy
because `np.where` evaluates `log(0)` before selecting the zero-safe branch.
All saved entropy values are finite, and the warning occurs after model fitting;
it does not affect features, labels, likelihood diagnostics, bootstrap, seed
stability, or the study verdict.
