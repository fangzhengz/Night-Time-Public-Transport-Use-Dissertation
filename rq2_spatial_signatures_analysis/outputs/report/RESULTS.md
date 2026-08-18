# RQ2 Spatial Signatures sidecar results

## Status and scope

This analysis keeps the adopted Rail K=5 and Bus K=4 labels fixed. Spatial
Signatures are an external area/context layer, not clustering inputs and not
passenger characteristics.

Source: Fleischmann and Arribas-Bel, Figshare article 16691575, DOI
`10.6084/m9.figshare.16691575.v3`. The source metadata states temporal coverage
2020 and OGL licensing. The source LSOA11 compositions were converted to London
LSOA21 using the ONS exact-fit V3 lookup, which preserves no-change, split and
merge relationships. All 4,994 London LSOA21s are covered; 22 combine more than
one LSOA11 source row.

## Coverage

- LSOA21: 4994/4994 (100.000%).
- Bus fitted sample: 3383/3383 (100.000%).
- Rail context-eligible sample: 387/403 (96.030%); the 16 excluded stations are outside the strict Greater London boundary, matching the existing RQ2 context universe.
- Rail catchment London coverage: mean 0.976, minimum 0.507.

## London dominant-type distribution

- `DUN` Dense urban neighbourhoods: 1086 London LSOA21s
- `LOU` Local urbanity: 848 London LSOA21s
- `DRN` Dense residential neighbourhoods: 785 London LSOA21s
- `CRN` Connected residential neighbourhoods: 493 London LSOA21s
- `ACS` Accessible suburbia: 457 London LSOA21s
- `WAL` Warehouse/Park land: 364 London LSOA21s
- `REU` Regional urbanity: 324 London LSOA21s
- `OPS` Open sprawl: 245 London LSOA21s
- `DIS` Disconnected suburbia: 177 London LSOA21s
- `URB` Urban buffer: 93 London LSOA21s
- `MEU` Metropolitan urbanity: 68 London LSOA21s
- `DIU` Concentrated urbanity: 24 London LSOA21s
- `GRQ` Gridded residential quarters: 24 London LSOA21s
- `HDU` Hyper concentrated urbanity: 4 London LSOA21s
- `COA` Countryside agriculture: 2 London LSOA21s

## Bus association

- Dominant type: Cramer's V = 0.234; unconditional permutation p = 0.001.
- Approximate centre-distance-conditioned permutation p = 0.001.
- Sparse expected cells (<5): 0.0%; interpret the permutation result and effect size rather than relying only on asymptotic chi-square p.
- Full-composition permutation R2 = 0.023, p = 0.001.

## Rail association

- Dominant type (equal-LSOA catchment composition): Cramer's V = 0.506; unconditional permutation p = 0.001.
- Approximate centre-distance-conditioned permutation p = 0.001.
- Sparse expected cells (<5): 61.7%.
- Equal-LSOA full-composition R2 = 0.143, p = 0.001.
- Intersection-area-weighted full-composition R2 = 0.133, p = 0.001.
- Equal-versus-area dominant-type agreement = 90.4%; ARI = 0.830.

## Interpretation boundary

Spatial Signatures describe urban form and function around Bus LSOAs and Rail
catchments. They may improve the CBD/airport/nightlife contextual description
relative to resident-only Census indicators, but they remain a 2020 area-level
classification. Association does not identify travellers, trip purposes, causal
mechanisms, unmet demand, or service deficiencies. The distance-band conditional
permutation is only a coarse centrality sensitivity and does not remove spatial
autocorrelation.
