# Bus hub-first full-week clustering: stability synthesis

## Scope

This synthesis compares three side-by-side, non-overwriting workspaces:

1. `rq1_bus_hub_first_reclustering`: alpha=5 first pass in the historical
   `cluster_clean_version_fullweek` 72-column representation;
2. `rq1_bus_hub_first_reclustering_rank58`: exact-rank and covariance-family
   sensitivity;
3. `rq1_bus_hub_first_reclustering_alpha_sensitivity`: fixed-sample alpha=0
   versus alpha=5 sensitivity.

## Correct historical baseline

The accepted historical interpretation version is
`cluster_clean_version_fullweek`. It uses one bus model for the full week. Each
LSOA has one 36-bin boardings vector and one 36-bin alightings vector, ordered
Weekday / Saturday / Sunday and normalised over the full week per direction.
Boardings and alightings do not share a denominator.

## Data entry used here

- hub-first official StopArea assembly and final LSOA assignment;
- 3,790 input LSOAs;
- full-week total activity >=50 leaves 3,597;
- the union of 14 documented group-level one-direction-zero exception LSOAs is
  excluded; four of these would otherwise pass the threshold;
- final fixed clustering sample: 3,593 LSOAs (94.8% of the hub-first input).

## Cross-midnight construction

The identical Weekday/Sunday post-midnight columns are intentional. BUSTO is a
calendar-day typical-day product: Weekday night uses Weekday morning as its best
available continuation, Saturday night uses Sunday morning, and Sunday night
uses Weekday morning (Monday). This is not a recurrence of the earlier wrong-day
extraction bug.

The construction nevertheless creates 12 exactly duplicated hourly columns;
with the two per-direction sum-to-one constraints, the 72-column matrix has rank
58. An SVD projection to the 58-dimensional observed subspace preserved sampled
pairwise distances to numerical precision (maximum absolute error 4.44e-16).

## What the rank audit proves

- Raw-72 full covariance: BIC minimum K=3.
- Rank-58 full covariance: BIC minimum K=3.
- Raw-72 versus rank-58 full K=3 labels: ARI=1.000.
- Bootstrap results are effectively identical in both representations.

Therefore the full-covariance family-internal K=3 result and its instability are
not caused by the exact redundant axes.

The cross-family BIC choice is not invariant: in an SVD basis, diagonal K=12 has
the lowest BIC, but K>=5 has negative silhouette and rapidly failing small-cluster
recovery. Diagonal covariance is coordinate-dependent, so this is evidence that
automatic covariance-family selection is fragile, not evidence for K=12.

## What the alpha audit proves

Both alpha=0 and alpha=5 use the same 3,593 LSOAs.

- Both variants select full covariance, K=3 in the original 72-column coordinate
  representation.
- K=3 alpha=0 versus alpha=5 ARI=0.813.
- Weakest cross-alpha matched-cluster Jaccard=0.843.
- The alpha=5 late-persistent cluster has 494 LSOAs; 452 (91.5%) remain together
  in its alpha=0 counterpart, with 42 boundary exchanges.
- alpha=0 bootstrap K=3: ARI=0.710; weakest-cluster Jaccard=0.555.
- alpha=5 bootstrap K=3: ARI=0.696; weakest-cluster Jaccard=0.513.

Thus smoothing does not create K=3, but alpha=5 does not improve stability.

## K decision

K>=4 is not defensible in the current full-covariance bus analysis: BIC worsens
after K=3 within the full family, silhouettes are approximately zero or negative,
and the weakest cluster's bootstrap recovery collapses as K increases.

K=3 is the only currently plausible multi-type candidate, but it should be
described as a soft typology rather than three sharply separated natural groups:

- a high-activity, intermediate-late-persistence group;
- a low-activity, early-fading group;
- a smaller late-persistent group.

The smaller late-persistent group is substantively recognisable and stable across
alpha choices, but its bootstrap boundary is only moderate. Spatial coherence is
also modest rather than strong.

## Recommended primary/sensitivity roles

- Primary candidate: hub-first + exception exclusion + full-week total>=50 +
  alpha=0 + full covariance, K=3.
- Low-flow sensitivity: identical sample and model with alpha=5.
- Do not use BIC alone to claim K, do not adopt diagonal K=12, and do not describe
  posterior probabilities near one as evidence of external reliability.
- Before final dissertation writing, descriptive cluster names should replace
  arbitrary numeric labels and the moderate bootstrap uncertainty of the
  late-persistent group must be stated explicitly.

