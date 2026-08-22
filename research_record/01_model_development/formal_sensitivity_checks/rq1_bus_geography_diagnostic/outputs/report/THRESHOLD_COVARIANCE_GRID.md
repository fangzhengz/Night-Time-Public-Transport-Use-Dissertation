# Does raising the activity threshold also fix K-selection instability?

For each activity threshold, BIC-best K is found independently for full and
diag covariance (same fit() settings as the adopted pipeline). threshold=0 is
the current adopted baseline (MIN_TOTAL=1, all 4,100 LSOAs).

|   threshold |   n_units | covariance   |   best_K | at_range_ceiling   |     best_BIC |
|------------:|----------:|:-------------|---------:|:-------------------|-------------:|
|           0 |      4100 | full         |        3 | False              | -2.29763e+06 |
|           0 |      4100 | diag         |       12 | True               | -2.17699e+06 |
|         100 |      3672 | full         |        3 | False              | -2.10471e+06 |
|         100 |      3672 | diag         |       12 | True               | -1.98245e+06 |
|         250 |      3072 | full         |        3 | False              | -1.786e+06   |
|         250 |      3072 | diag         |       12 | True               | -1.67902e+06 |
|         500 |      2340 | full         |        2 | False              | -1.38502e+06 |
|         500 |      2340 | diag         |       12 | True               | -1.29577e+06 |

## Reading

- If diag's best_K stops being at the range ceiling (12) once the threshold is
  raised, and full's best_K stays in a similar, low, stable range across
  thresholds, thresholding is close to sufficient on its own -- pick a threshold
  from the data-retention curve and proceed with a normal re-cluster + relabel.
- If diag keeps hitting the ceiling even at threshold=500 (43% of LSOAs excluded),
  the K-selection instability is not primarily about low-activity noise -- it is a
  property of the feature representation itself, and thresholding alone will not
  fully resolve it (Codex's coverage-tier design, or a change to the feature
  construction itself, would still be needed).