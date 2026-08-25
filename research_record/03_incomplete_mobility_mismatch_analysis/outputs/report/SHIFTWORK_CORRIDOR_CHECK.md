# RQ3 supplementary check -- shift-work-linked OD movement vs. PT mismatch

Conditions on the actual OD pair (which MSOA a place's movement connects to),
not just each MSOA's own marginal total. See this script's own docstring for
the full method rationale and the Mahfouz (2019/20 CASA dissertation) precedent
it is following the spirit of, at a much lighter weight (no PT routing engine).

Shift-work-heavy MSOA = top quartile of population-weighted transport_storage_share (TS060 section H). 246/982 MSOAs flagged.

## Origin

- n=979 MSOAs with both a computed linked-share and a baseline mismatch residual.
- Spearman(shiftwork_linked_share, std_residual) = -0.101 (p=0.001561).
- Top-quartile-linked MSOAs: median residual -0.205 vs +0.000 for the rest (Mann-Whitney rank-biserial=-0.129, p=0.002433).

## Destination

- n=979 MSOAs with both a computed linked-share and a baseline mismatch residual.
- Spearman(shiftwork_linked_share, std_residual) = -0.052 (p=0.1067).
- Top-quartile-linked MSOAs: median residual -0.218 vs -0.008 for the rest (Mann-Whitney rank-biserial=-0.093, p=0.02832).

## Reading this

A negative Spearman rho / negative rank-biserial means: MSOAs whose night-time movement is disproportionately linked to shift-work-heavy places have WORSE (more negative) PT-capture residuals than MSOAs whose movement is not -- i.e. the under-capture is concentrated specifically in shift-work-linked corridors, not spread evenly. A near-zero or positive result means the baseline model's residual pattern is not specifically about shift-work connectivity; it is closer to the general density/car-dependence gradient already found in the marginal-total version.

## Caveats (in addition to the baseline model's own, in RESULTS_SUMMARY.md)

- transport_storage_share is a RESIDENCE-side variable (where shift-transport/
  storage workers live), computed from 2021 Census, aggregated LSOA -> MSOA by
  population weight -- same vintage-mixing caveat as the rest of the project.
- "Linked" means the OTHER end of an OD pair is a shiftwork-heavy MSOA, not that
  the flow itself is made by shift workers -- OD data has no traveller attributes.
- Top-quartile threshold is a specific, disclosed choice (0.75); not tested for
  sensitivity to threshold placement in this pass.