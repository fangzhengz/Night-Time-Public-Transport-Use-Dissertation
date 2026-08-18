## Material Passport

- ID: `hub-first-core-threshold-screen-stress`
- Type: code experiment result
- Verification status: ANALYZED
- Created UTC: 2026-07-20T15:59:36.548863+00:00
- Scope: threshold screen only; no final K selection or posterior assignment

# Hub-first reliable-core threshold screen

## Fixed design

- Thresholds: [175.0, 200.0, 250.0, 300.0]
- K values: [2, 3, 4, 5]
- Full-covariance GMM; n_init=5; seed=42
- Core criterion: min(total_boardings, total_alightings) >= threshold
- Features: fixed hub-first alpha=0 direction-normalized 72-vector
- Total elapsed seconds: 23.306

## Threshold-level gate

|   threshold |   n_core |   pct_core |   n_k_activity_below_timing | all_k_activity_below_timing   | part_of_consecutive_all_k_run   | coverage_band      | strict_first_pass_candidate   |   max_activity_eta2_across_k |   min_timing_mean_eta2_across_k |   max_activity_kw_epsilon2_across_k |   min_cluster_size_across_k |
|------------:|---------:|-----------:|----------------------------:|:------------------------------|:--------------------------------|:-------------------|:------------------------------|-----------------------------:|--------------------------------:|------------------------------------:|----------------------------:|
|  175.000000 |     2281 |  63.484553 |                           2 | False                         | False                           | stress_below_70pct | False                         |                     0.449447 |                        0.206350 |                            0.465773 |                         131 |
|  200.000000 |     2147 |  59.755079 |                           2 | False                         | False                           | stress_below_70pct | False                         |                     0.429117 |                        0.177270 |                            0.451811 |                         131 |
|  250.000000 |     1924 |  53.548567 |                           2 | False                         | False                           | stress_below_70pct | False                         |                     0.395301 |                        0.238534 |                            0.434049 |                         105 |
|  300.000000 |     1736 |  48.316170 |                           4 | True                          | False                           | stress_below_70pct | False                         |                     0.322447 |                        0.282428 |                            0.328610 |                         105 |

## K-specific results

|   threshold |   k |   n_core |   pct_core |   activity_eta2 |   timing_mean_eta2 |   activity_to_timing_ratio |   activity_kw_epsilon2 | gate_activity_below_timing   |   min_cluster_size | converged   |   fit_seconds |   bic_within_threshold |
|------------:|----:|---------:|-----------:|----------------:|-------------------:|---------------------------:|-----------------------:|:-----------------------------|-------------------:|:------------|--------------:|-----------------------:|
|  175.000000 |   2 |     2281 |  63.484553 |        0.026418 |           0.206350 |                   0.128025 |               0.040815 | True                         |                361 | True        |      3.199287 |        -1356802.107291 |
|  175.000000 |   3 |     2281 |  63.484553 |        0.035062 |           0.317305 |                   0.110498 |               0.028675 | True                         |                249 | True        |      0.673561 |        -1344140.684065 |
|  175.000000 |   4 |     2281 |  63.484553 |        0.427688 |           0.330078 |                   1.295719 |               0.465773 | False                        |                185 | True        |      2.095367 |        -1334739.763044 |
|  175.000000 |   5 |     2281 |  63.484553 |        0.449447 |           0.410225 |                   1.095609 |               0.465286 | False                        |                131 | True        |      2.530945 |        -1317276.947033 |
|  200.000000 |   2 |     2147 |  59.755079 |        0.028460 |           0.177270 |                   0.160548 |               0.045330 | True                         |                344 | True        |      0.782888 |        -1281370.328481 |
|  200.000000 |   3 |     2147 |  59.755079 |        0.021445 |           0.354430 |                   0.060505 |               0.014200 | True                         |                244 | True        |      0.653525 |        -1268167.985559 |
|  200.000000 |   4 |     2147 |  59.755079 |        0.423524 |           0.345326 |                   1.226446 |               0.451811 | False                        |                177 | True        |      1.757085 |        -1257923.452535 |
|  200.000000 |   5 |     2147 |  59.755079 |        0.429117 |           0.425832 |                   1.007714 |               0.443897 | False                        |                131 | True        |      1.875487 |        -1240442.997795 |
|  250.000000 |   2 |     1924 |  53.548567 |        0.010062 |           0.238534 |                   0.042184 |               0.019163 | True                         |                297 | True        |      0.751400 |        -1153223.442100 |
|  250.000000 |   3 |     1924 |  53.548567 |        0.018720 |           0.369236 |                   0.050700 |               0.010805 | True                         |                217 | True        |      0.543915 |        -1140234.347360 |
|  250.000000 |   4 |     1924 |  53.548567 |        0.395301 |           0.362141 |                   1.091565 |               0.434049 | False                        |                166 | True        |      2.109296 |        -1128625.060563 |
|  250.000000 |   5 |     1924 |  53.548567 |        0.353721 |           0.337579 |                   1.047817 |               0.376237 | False                        |                105 | True        |      2.644816 |        -1111448.012228 |
|  300.000000 |   2 |     1736 |  48.316170 |        0.000365 |           0.282428 |                   0.001292 |               0.001945 | True                         |                297 | True        |      0.342436 |        -1044188.779602 |
|  300.000000 |   3 |     1736 |  48.316170 |        0.019269 |           0.387366 |                   0.049744 |               0.008606 | True                         |                207 | True        |      0.386550 |        -1031292.384740 |
|  300.000000 |   4 |     1736 |  48.316170 |        0.270705 |           0.349021 |                   0.775612 |               0.289481 | True                         |                146 | True        |      0.956146 |        -1017487.399449 |
|  300.000000 |   5 |     1736 |  48.316170 |        0.322447 |           0.416425 |                   0.774320 |               0.328610 | True                         |                105 | True        |      1.641981 |        -1001275.247119 |

## Automated first-pass verdict

No threshold passed the strict first-pass gate.

The automated verdict is only a screening gate. BIC values are valid
for comparing K values within the same threshold and must not be used
to rank different thresholds with different samples.