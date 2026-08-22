# Bus 15-minute vs 1-hour fair stability validation

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run + validate
- Origin Date: 2026-07-02T23:20:22.772725+00:00
- Verification Status: ANALYZED
- Version Label: bus_resolution_fair_validation_v1

## Fairness audit

- Same-source analysis universe: 4,100 LSOAs.
- Feature shapes: 15-minute (4100, 288); 1-hour (4100, 72).
- Maximum total-activity difference after aggregation: 3.638e-11.
- Rebuilt-vs-existing maximum feature difference: 15-minute 0.000e+00; 1-hour 8.327e-17.

## Matched diagonal K=4

- Common-space silhouette: 15-minute labels 0.053; 1-hour labels -0.047.
- Across-seed ARI: 15-minute 0.612; 1-hour 0.720.
- Bootstrap ARI: 15-minute 0.406; 1-hour 0.635.
- LSOAs below 0.8 bootstrap assignment stability: 15-minute 42.1%; 1-hour 28.3%.
- Cross-resolution ARI=0.290; matched agreement=57.8%.
- LNWC Cramér's V: 15-minute 0.246; 1-hour 0.278.

## Interpretation

The fair comparison separates three questions: whether the labels are internally separated on a common feature space, whether assignments survive seed/bootstrap perturbation, and whether the resulting groups carry external substantive meaning. A resolution can be more interpretable while being less stable.

The tied-covariance sensitivity is treated as invalid when it produces a cluster smaller than 20 LSOAs or a dominant cluster above 90%. Such solutions can show artificially high silhouette values while carrying little typological information.

BIC is reported only within each resolution/covariance setting and is not compared across the 288- and 72-dimensional matrices.

## Decision boundary

Promotion of the 15-minute K=4 solution should require acceptable common-space separation and bootstrap stability in addition to stronger LNWC or behavioural contrasts. External interpretability alone is not sufficient because unstable LSOA assignments can produce a persuasive but non-reproducible typology.