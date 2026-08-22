# RQ2 LOAC (London Output Area Classification) lens — results

## Scope

Third parallel socio-spatial lens alongside LNWC and IMD (per
Mikaella's original 2026-07-02 guidance to add Census/LOAC as a
separate layer, never previously built). Uses LOAC's composite
Supergroup label (7 categories, A-G) as-is -- not decomposed into
its 68 raw Census input variables. Clustering choice matches
`rq2_new_clusters_analysis` (bus StopArea CLR K=4, rail
all-modes NaPTAN-matched 403-station K=5), with the same 800 m
rail catchment radius as that folder's 800 m sidecar.

## LOAC Supergroups (official names)

- **A**: Professional Employment and Family Lifecycles
- **B**: The Greater London Mix
- **C**: Suburban Asian Communities
- **D**: Central Connected Professionals and Managers
- **E**: Social Rented Sector Families with Children
- **F**: Young Families and Mainstream Employment
- **G**: Older Residents in Owner-Occupied Suburbs

- Bus: K=4; direct LSOA join (LOAC aggregated from OA to
  LSOA via modal Supergroup across constituent OAs).
- Rail: K=5; 800 m Voronoi-clipped
  catchments intersected directly against LOAC's OA-level
  geopackage (no LSOA intermediate).

## Coverage

- Bus: 3383.0/3383.0 fitted LSOAs matched to a LOAC Supergroup (100.0%).
- Rail: 387.0/403.0 stations eligible for LOAC analysis; 16.0 station points fall outside the LOAC/Greater-London extent (the same known set of NaPTAN-matched-but-boundary stations flagged in the LNWC/IMD runs on this clustering).
- Mean rail catchment LOAC coverage ratio: 0.974 (minimum 0.511).

## Association statistics

- Bus cluster × LOAC dominant Supergroup: chi-square=504.22, Cramer's V=0.223, n=3383.
- Rail cluster × LOAC dominant Supergroup: chi-square=159.23, Cramer's V=0.321, n=387.
- Rail seven-part Supergroup composition: permutation R²=0.143, p=0.0010 (999 permutations).

These are exploratory categorical association tests (same caveat as
the LNWC treatment): ordinary chi-square/permutation tests here do
not account for spatial autocorrelation between neighbouring
units.

## Explicitly out of scope for this pass

- No continuous-metric/Freedman-Lane nested test (e.g. testing
  whether IMD's association survives controlling for LOAC) --
  deferred per the user's own request; this pass covers only the
  categorical/compositional lens, matching LNWC's Section 6
  treatment.
- No decomposition into LOAC's raw 68 input Census variables.
- No changes to any existing `rq2test analysis` or
  `rq2_new_clusters_analysis` files.