## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: 2026-07-21T16:03:55.376006+00:00
- Verification Status: ANALYZED
- Version Label: rail_ilr_transform_driver_v1

# Rail ILR transformation-driver diagnostic

## Verdict

The alpha=1 ILR sensitivity is dominated by temporal zero-pattern structure.
It validly shows that raw K=5 does not survive this exact transformation, but
it does **not** by itself establish that raw K=5 is substantively invalid or
that ILR K=4 should replace it.

## Cluster-level association

| representation | K | metric             | eta_squared |
| -------------- | - | ------------------ | ----------- |
| raw            | 4 | log_total_activity | 0.338       |
| raw            | 4 | zero_total         | 0.049       |
| raw            | 5 | log_total_activity | 0.407       |
| raw            | 5 | zero_total         | 0.177       |
| raw            | 6 | log_total_activity | 0.397       |
| raw            | 6 | zero_total         | 0.242       |
| ilr            | 4 | log_total_activity | 0.450       |
| ilr            | 4 | zero_total         | 0.942       |
| ilr            | 5 | log_total_activity | 0.488       |
| ilr            | 5 | zero_total         | 0.942       |
| ilr            | 6 | log_total_activity | 0.523       |
| ilr            | 6 | zero_total         | 0.943       |

For K=5, zero-bin-count eta-squared rises from `0.177` under the
raw-share labels to `0.942` under the ILR labels.

## Pairwise distance drivers

| representation | driver                           | spearman_rho | p_value | station_pairs |
| -------------- | -------------------------------- | ------------ | ------- | ------------- |
| raw_euclidean  | absolute_log_activity_difference | 0.313        | 0.000   | 36315         |
| raw_euclidean  | absolute_zero_count_difference   | 0.112        | 0.000   | 36315         |
| raw_euclidean  | zero_pattern_hamming_difference  | 0.111        | 0.000   | 36315         |
| ilr_euclidean  | absolute_log_activity_difference | 0.023        | 0.000   | 36315         |
| ilr_euclidean  | absolute_zero_count_difference   | 0.866        | 0.000   | 36315         |
| ilr_euclidean  | zero_pattern_hamming_difference  | 0.885        | 0.000   | 36315         |

The Spearman correlation between station distance and zero-pattern Hamming
difference rises from `0.111` in raw-share space to
`0.885` in ILR space. Across stations, zero-bin count and log total
activity have Spearman rho `-0.429`.

## Interpretation

The empirical-prior posterior is strictly positive and mathematically valid,
but an observed zero receives a share proportional to the aggregate prior and
inversely related to the station's direction total. With 6,989 zero cells, log
ratios strongly magnify differences in which bins are zero. The resulting
clusters therefore combine temporal shape with sparsity/reliability structure.

## Decision boundary

1. Report the ILR run as a failed robustness check for the current K=5 labels.
2. Do not treat ILR K=4 as a new substantive station typology from this run.
3. A replacement compositional primary model would require a prespecified zero
   treatment/reliability sensitivity and a coordinate-invariant or otherwise
   justified covariance strategy.
