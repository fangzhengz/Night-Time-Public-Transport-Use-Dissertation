# Literature-grounded low-flow threshold decision

## Decision

Use `min(tot_boardings, tot_alightings) >= 36` as the primary low-flow
exclusion rule for the hub-first bus clustering sensitivity.  This retains
3,365 of 3,593 currently valid LSOAs (93.65%) and removes 228 (6.35%).

This is a conservative adaptation of the closest directly comparable bus-stop
time-series clustering study, not a universal statistical cutoff.  Keep the
bottom-20% exclusion as a sensitivity comparator rather than the primary rule.

## Closest direct precedent

Mariñas-Collado et al. (2022) analysed hourly boarding series for 272 urban bus
stops over 14 days (17 operating hours per day).  Before clustering, they
removed stops whose mean passenger count across the two weeks was below one.
Their four reported cluster sizes sum to 243, so 29/272 stops (10.66%) were
removed in that application.  The transferable element is the one-passenger-
per-observed-hour rule, not the resulting percentage.

- Source: https://doi.org/10.3390/math10152670

The present feature matrix contains 36 hourly profile cells per direction:
three typical day types multiplied by twelve night-time hours.  A mean of one
per cell therefore corresponds to a direction total of 36.  As boardings and
alightings are normalised separately and enter the 72-vector symmetrically, the
rule is applied to both directions rather than to boardings alone.

## Why the number is only an operational analogue

TfL describes BUSTO as estimated demand on a typical weekday, Saturday and
Sunday, rather than a file of independent raw transactions.  Its estimates can
be fractional and include scaling and inferred alightings.  Consequently,
`36` means an average estimated demand of one per represented hourly cell; it
must not be described as an effective sample size or a general minimum count.

- TfL open-data description: https://tfl.gov.uk/info-for/open-data-users/our-open-data?intcmp=3671
- BUSTO user guide: https://crowding.data.tfl.gov.uk/BUSTO/BUSTO%20User%20Guide%20and%20Data%20Dictionary%20v1.0.pdf

## Other primary studies checked

An analogous Nanjing urban-rail study excluded stations below 500 passengers
per day to avoid sensitivity to occasional changes, leaving 172 of 175
stations.  This demonstrates a count-based exclusion plus percentage-profile
normalisation, but its rail volume and full-day unit are not numerically
portable to the London night-bus LSOA data.

- Source: https://doi.org/10.3390/su16093568

The reviewed studies do not establish a standard rule such as deleting the
lowest 20%.  Therefore, a Pareto-based 20% cutoff should not be presented as
literature-derived.

## Result of the direct run

Fixed inputs were the hub-first, alpha=0, direction-normalised 72-vector and
the already-valid 3,593-LSOA sample.  Full-covariance GMMs used seed 42 and
20 initialisations.

| K | Cluster sizes | BIC decision | Central/outer total-variation distance | Random central/outer same-cluster probability |
|---:|:---|:---|---:|---:|
| 3 | 1283; 1621; 461 | BIC-best | 0.3690 | 0.3179 |
| 4 | 1147; 1062; 311; 845 | not BIC-best | 0.4254 | 0.2344 |

For K=4, cluster 1 contains 56.3% of retained Westminster LSOAs and 52.3% of
retained Camden LSOAs, but only 21.4% of Kingston and 22.4% of Richmond.
Conversely, cluster 0 contains 42.9% of Kingston and 51.8% of Richmond, but
only 8.1% of Westminster and 20.5% of Camden.  Thus the exact central-versus-
outer mixing criticised by Howard is materially reduced, although geographic
overlap remains because location is not a clustering feature.

The bottom-20% K=4 comparator has a stronger central/outer total-variation
distance (0.5197), but achieves it by excluding 719 LSOAs instead of 228.
This is evidence of a coverage-versus-separation trade-off, not evidence that
20% is the correct threshold.

## Recommended reporting position

1. Treat the threshold-36 K=4 result as the primary high-coverage candidate for
   substantive inspection, while reporting that within-threshold BIC prefers
   K=3.
2. Retain the bottom-20% K=4 result only as a stricter low-flow sensitivity.
3. Select between K=3 and K=4 using the temporal profiles, spatial diagnostic,
   stability and interpretability together; do not claim that the literature
   threshold itself determines K.
4. Do not return to posterior assignment or weighted EM unless this direct
   exclusion result fails the substantive map review.
