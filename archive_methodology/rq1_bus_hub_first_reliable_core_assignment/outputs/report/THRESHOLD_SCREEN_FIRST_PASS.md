## Material Passport

- ID: `hub-first-core-threshold-screen-first_pass`
- Type: code experiment result
- Verification status: ANALYZED
- Created UTC: 2026-07-20T16:28:15.671986+00:00
- Scope: threshold screen with per-threshold BIC-driven K selection;
  no forced K, no posterior assignment yet

# Hub-first reliable-core threshold screen (v2: BIC picks K per threshold)

## Why this version does not fix K

The historical K=3 result comes from a pipeline this project has since
shown to be activity-noise-contaminated. Requiring K=3 to keep winning
after the contamination is removed would assume the answer. This script
instead lets BIC choose each threshold's own preferred K from an
exploratory scan (K=2..10, full covariance,
n_init=5), confirms the winning K at n_init=
20, and gates on that K. K=3 is refit and
shown alongside purely as a labelled reference point, never as a requirement.

## Fixed design

- Thresholds: [0.0, 50.0, 70.0, 90.0, 100.0, 110.0, 125.0, 150.0]
- K scan range: 2..10
- Full-covariance GMM; scan n_init=5; deep-dive n_init=20; seed=42
- Core criterion: min(total_boardings, total_alightings) >= threshold
- Features: fixed hub-first alpha=0 direction-normalized 72-vector
- Total elapsed seconds: 294.407

**BIC-best K shift away from K=3: threshold=90->K=2, threshold=100->K=2, threshold=110->K=2, threshold=125->K=2, threshold=150->K=2.**

## Threshold-level gate (own BIC-best K)

|   threshold |   pct_core |   bic_best_k | bic_best_k_differs_from_reference   |   bic_best_k_activity_eta2 |   bic_best_k_timing_mean_eta2 | gate_pass_at_bic_best_k   | part_of_consecutive_pass_run   | coverage_band            | strict_candidate   |   reference_k3_activity_eta2 | reference_k3_gate_pass   |
|------------:|-----------:|-------------:|:------------------------------------|---------------------------:|------------------------------:|:--------------------------|:-------------------------------|:-------------------------|:-------------------|-----------------------------:|:-------------------------|
|    0.000000 | 100.000000 |            3 | False                               |                   0.522216 |                      0.283973 | False                     | False                          | preferred_at_least_75pct | False              |                     0.522216 | False                    |
|   50.000000 |  89.841358 |            3 | False                               |                   0.491284 |                      0.274461 | False                     | False                          | preferred_at_least_75pct | False              |                     0.491284 | False                    |
|   70.000000 |  84.274979 |            3 | False                               |                   0.458252 |                      0.269116 | False                     | False                          | preferred_at_least_75pct | False              |                     0.458252 | False                    |
|   90.000000 |  79.265238 |            2 | True                                |                   0.440852 |                      0.027211 | False                     | False                          | preferred_at_least_75pct | False              |                     0.041100 | True                     |
|  100.000000 |  76.843863 |            2 | True                                |                   0.411835 |                      0.006670 | False                     | False                          | preferred_at_least_75pct | False              |                     0.092774 | True                     |
|  110.000000 |  75.062622 |            2 | True                                |                   0.392832 |                      0.004468 | False                     | False                          | preferred_at_least_75pct | False              |                     0.059212 | True                     |
|  125.000000 |  71.861954 |            2 | True                                |                   0.023125 |                      0.063995 | True                      | True                           | fallback_70_to_75pct     | False              |                     0.463860 | False                    |
|  150.000000 |  67.548010 |            2 | True                                |                   0.000562 |                      0.066675 | True                      | True                           | stress_below_70pct       | False              |                     0.450697 | False                    |

## Exploratory scan grid (all screened K, n_init=5)

Informational only -- not gating. Low n_init means individual cells can
be noisy; only the deep-dive-confirmed BIC-best K per threshold is used
for the decision above.

|   threshold |   k |   bic_within_threshold |   activity_eta2 |   timing_mean_eta2 | gate_activity_below_timing   |   min_cluster_pct | converged   |
|------------:|----:|-----------------------:|----------------:|-------------------:|:-----------------------------|------------------:|:------------|
|    0.000000 |   2 |        -2040103.319811 |        0.445558 |           0.071159 | False                        |         31.060395 | True        |
|    0.000000 |   3 |        -2061869.222767 |        0.522235 |           0.283707 | False                        |         13.721124 | True        |
|    0.000000 |   4 |        -2051863.835623 |        0.565907 |           0.291478 | False                        |          4.842750 | True        |
|    0.000000 |   5 |        -2037251.097233 |        0.638844 |           0.310119 | False                        |          5.288060 | True        |
|    0.000000 |   6 |        -2018959.406723 |        0.603823 |           0.321508 | False                        |          3.200668 | True        |
|    0.000000 |   7 |        -2003971.805113 |        0.640525 |           0.377213 | False                        |          2.950181 | True        |
|    0.000000 |   8 |        -1987689.486543 |        0.604053 |           0.430961 | False                        |          2.087392 | True        |
|    0.000000 |   9 |        -1968154.718569 |        0.622863 |           0.409056 | False                        |          2.449207 | True        |
|    0.000000 |  10 |        -1951143.345814 |        0.619548 |           0.434846 | False                        |          2.170888 | True        |
|   50.000000 |   2 |        -1868508.113844 |        0.273554 |           0.000435 | False                        |         28.376704 | True        |
|   50.000000 |   3 |        -1874694.397480 |        0.491284 |           0.274461 | False                        |         13.816605 | True        |
|   50.000000 |   4 |        -1862804.307110 |        0.541641 |           0.303304 | False                        |          7.156134 | True        |
|   50.000000 |   5 |        -1845011.508874 |        0.552019 |           0.313766 | False                        |          5.916976 | True        |
|   50.000000 |   6 |        -1830726.648985 |        0.601416 |           0.324422 | False                        |          5.204461 | True        |
|   50.000000 |   7 |        -1813922.109713 |        0.546375 |           0.411695 | False                        |          3.376704 | True        |
|   50.000000 |   8 |        -1794346.559717 |        0.580148 |           0.377404 | False                        |          2.788104 | True        |
|   50.000000 |   9 |        -1779149.040382 |        0.569602 |           0.439777 | False                        |          1.703841 | True        |
|   50.000000 |  10 |        -1757462.071048 |        0.589070 |           0.437505 | False                        |          2.571252 | True        |
|   70.000000 |   2 |        -1761417.701187 |        0.464724 |           0.037622 | False                        |         46.235139 | True        |
|   70.000000 |   3 |        -1765758.851854 |        0.457880 |           0.269267 | False                        |         11.030383 | True        |
|   70.000000 |   4 |        -1753017.961858 |        0.499032 |           0.324761 | False                        |          5.911493 | True        |
|   70.000000 |   5 |        -1736555.957639 |        0.539947 |           0.339033 | False                        |          4.755614 | True        |
|   70.000000 |   6 |        -1720630.440052 |        0.526850 |           0.365064 | False                        |          3.401585 | True        |
|   70.000000 |   7 |        -1702654.730588 |        0.527122 |           0.373184 | False                        |          3.599736 | True        |
|   70.000000 |   8 |        -1686099.610973 |        0.565839 |           0.449304 | False                        |          2.344782 | True        |
|   70.000000 |   9 |        -1667496.836824 |        0.546920 |           0.387104 | False                        |          2.939234 | True        |
|   70.000000 |  10 |        -1648435.510143 |        0.544945 |           0.441306 | False                        |          2.212682 | True        |
|   90.000000 |   2 |        -1668041.230439 |        0.440852 |           0.027211 | False                        |         43.750000 | True        |
|   90.000000 |   3 |        -1654390.176037 |        0.040851 |           0.335783 | True                         |         11.060393 | True        |
|   90.000000 |   4 |        -1654296.900533 |        0.494783 |           0.342793 | False                        |          6.214888 | True        |
|   90.000000 |   5 |        -1637102.097320 |        0.498194 |           0.335501 | False                        |          5.898876 | True        |
|   90.000000 |   6 |        -1620583.479532 |        0.550683 |           0.348875 | False                        |          4.634831 | True        |
|   90.000000 |   7 |        -1603876.860491 |        0.501715 |           0.438609 | False                        |          2.808989 | True        |
|   90.000000 |   8 |        -1586210.657935 |        0.508688 |           0.434839 | False                        |          3.441011 | True        |
|   90.000000 |   9 |        -1568448.147667 |        0.507910 |           0.451123 | False                        |          1.544944 | True        |
|   90.000000 |  10 |        -1549155.508990 |        0.520049 |           0.424600 | False                        |          2.247191 | True        |
|  100.000000 |   2 |        -1621737.973668 |        0.411835 |           0.006670 | False                        |         38.536762 | True        |
|  100.000000 |   3 |        -1608092.101477 |        0.078477 |           0.267426 | True                         |         10.467222 | True        |
|  100.000000 |   4 |        -1605696.678646 |        0.482238 |           0.324289 | False                        |          8.149221 | True        |
|  100.000000 |   5 |        -1588551.744627 |        0.490575 |           0.354523 | False                        |          6.012314 | True        |
|  100.000000 |   6 |        -1571988.525228 |        0.497463 |           0.453618 | False                        |          3.802970 | True        |
|  100.000000 |   7 |        -1555127.470062 |        0.498892 |           0.435092 | False                        |          3.404564 | True        |
|  100.000000 |   8 |        -1537025.669350 |        0.490967 |           0.474161 | False                        |          2.861282 | True        |
|  100.000000 |   9 |        -1520258.315372 |        0.523004 |           0.473075 | False                        |          2.499095 | True        |
|  100.000000 |  10 |        -1498330.220460 |        0.523695 |           0.427545 | False                        |          2.281782 | True        |
|  110.000000 |   2 |        -1586475.430443 |        0.392832 |           0.004468 | False                        |         37.226548 | True        |
|  110.000000 |   3 |        -1572919.554749 |        0.059212 |           0.292047 | True                         |         10.493141 | True        |
|  110.000000 |   4 |        -1569578.256363 |        0.473590 |           0.328454 | False                        |          8.008899 | True        |
|  110.000000 |   5 |        -1553591.165955 |        0.489278 |           0.353325 | False                        |          4.560623 | True        |
|  110.000000 |   6 |        -1536365.024036 |        0.492137 |           0.468531 | False                        |          3.448276 | True        |
|  110.000000 |   7 |        -1518663.642753 |        0.493439 |           0.428259 | False                        |          3.522432 | True        |
|  110.000000 |   8 |        -1500359.440398 |        0.505823 |           0.420550 | False                        |          3.522432 | True        |
|  110.000000 |   9 |        -1484456.152913 |        0.509225 |           0.447746 | False                        |          1.631442 | True        |
|  110.000000 |  10 |        -1464237.461868 |        0.491708 |           0.480823 | False                        |          1.520208 | True        |
|  125.000000 |   2 |        -1524535.753048 |        0.023125 |           0.063995 | True                         |         17.157242 | True        |
|  125.000000 |   3 |        -1519161.685995 |        0.463860 |           0.117841 | False                        |          9.992254 | True        |
|  125.000000 |   4 |        -1505239.317452 |        0.464689 |           0.376973 | False                        |          5.925639 | True        |
|  125.000000 |   5 |        -1488669.557613 |        0.488891 |           0.373195 | False                        |          6.467854 | True        |
|  125.000000 |   6 |        -1471699.489513 |        0.490757 |           0.355778 | False                        |          4.996127 | True        |
|  125.000000 |   7 |        -1453691.617377 |        0.480480 |           0.404989 | False                        |          4.879938 | True        |
|  125.000000 |   8 |        -1436133.167194 |        0.487217 |           0.393198 | False                        |          4.105345 | True        |
|  125.000000 |   9 |        -1418825.435510 |        0.490447 |           0.496508 | True                         |          2.672347 | True        |
|  125.000000 |  10 |        -1398700.063345 |        0.496404 |           0.470754 | False                        |          2.478699 | True        |
|  150.000000 |   2 |        -1436752.778731 |        0.000562 |           0.066675 | True                         |         16.646065 | True        |
|  150.000000 |   3 |        -1425503.336046 |        0.085418 |           0.261384 | True                         |         10.589205 | True        |
|  150.000000 |   4 |        -1417909.559238 |        0.453984 |           0.348997 | False                        |          7.869798 | True        |
|  150.000000 |   5 |        -1400024.073959 |        0.487475 |           0.381881 | False                        |          6.180470 | True        |
|  150.000000 |   6 |        -1383417.683961 |        0.475709 |           0.420488 | False                        |          3.543469 | True        |
|  150.000000 |   7 |        -1365129.246867 |        0.464524 |           0.461532 | False                        |          4.120313 | True        |
|  150.000000 |   8 |        -1347591.409535 |        0.488910 |           0.437495 | False                        |          3.996704 | True        |
|  150.000000 |   9 |        -1328758.575666 |        0.468707 |           0.444399 | False                        |          3.337454 | True        |
|  150.000000 |  10 |        -1309924.438710 |        0.482458 |           0.464140 | False                        |          3.584672 | True        |

## Deep-dive confirmatory fits (BIC-best K and K=3 reference, n_init=20)

|   threshold |   k | is_bic_best_k   |   bic_within_threshold |   activity_eta2 |   timing_mean_eta2 |   activity_to_timing_ratio | gate_activity_below_timing   |   min_cluster_pct | converged   |   fit_seconds |
|------------:|----:|:----------------|-----------------------:|----------------:|-------------------:|---------------------------:|:-----------------------------|------------------:|:------------|--------------:|
|    0.000000 |   3 | True            |        -2061871.955062 |        0.522216 |           0.283973 |                   1.838966 | False                        |         13.748956 | True        |      4.764075 |
|   50.000000 |   3 | True            |        -1874694.672430 |        0.491284 |           0.274461 |                   1.789995 | False                        |         13.816605 | True        |      7.682049 |
|   70.000000 |   3 | True            |        -1765763.122570 |        0.458252 |           0.269116 |                   1.702804 | False                        |         11.063408 | True        |      6.441839 |
|   90.000000 |   2 | True            |        -1668041.230439 |        0.440852 |           0.027211 |                  16.201113 | False                        |         43.750000 | True        |      3.129603 |
|   90.000000 |   3 | False           |        -1654925.221504 |        0.041100 |           0.323988 |                   0.126855 | True                         |         11.165730 | True        |      3.094946 |
|  100.000000 |   2 | True            |        -1621737.973668 |        0.411835 |           0.006670 |                  61.744569 | False                        |         38.536762 | True        |      3.540475 |
|  100.000000 |   3 | False           |        -1608118.737775 |        0.092774 |           0.247656 |                   0.374609 | True                         |         10.322347 | True        |      2.333113 |
|  110.000000 |   2 | True            |        -1586475.975578 |        0.392832 |           0.004468 |                  87.928402 | False                        |         37.226548 | True        |      5.643283 |
|  110.000000 |   3 | False           |        -1572919.554749 |        0.059212 |           0.292047 |                   0.202747 | True                         |         10.493141 | True        |      2.718848 |
|  125.000000 |   2 | True            |        -1524535.669281 |        0.023125 |           0.063995 |                   0.361351 | True                         |         17.157242 | True        |      6.285437 |
|  125.000000 |   3 | False           |        -1519162.122281 |        0.463860 |           0.117841 |                   3.936310 | False                        |          9.992254 | True        |      9.281859 |
|  150.000000 |   2 | True            |        -1436752.778731 |        0.000562 |           0.066675 |                   0.008431 | True                         |         16.646065 | True        |      5.964577 |
|  150.000000 |   3 | False           |        -1431508.833958 |        0.450697 |           0.118443 |                   3.805176 | False                        |          9.682736 | True        |      6.035251 |

## Automated verdict

No threshold passed the strict gate at its own BIC-best K.

BIC values are valid for comparing K values within the same threshold
and must not be used to rank different thresholds with different samples.