# RQ2 Spatial Signatures sidecar

The main contextual analysis relied on LNWC and a set of individual area indicators, but these sources do not fully describe urban form and function. Spatial Signatures offered a complementary way to ask whether the night-use clusters occupy recognisably different kinds of urban fabric. This side study therefore holds the Rail K=5 and Bus K=4 solutions fixed and looks outward, treating the classification as an interpretive lens rather than a new clustering input.

## Scope

- Spatial Signatures are joined **after** clustering.
- Existing clustering labels, features and samples are not modified or refit.
- Bus uses a direct LSOA21 join.
- Rail uses 800 m Voronoi-clipped catchments and reports both equal-LSOA and
  intersection-area-weighted signature compositions.
- Results are descriptive area associations, not passenger identities, trip
  purposes, causal mechanisms, demand, or service deficiencies.

## Source

Fleischmann, M. and Arribas-Bel, D., *Geographical Characterisation of
British Urban Form and Function using the Spatial Signatures Framework*.
Figshare DOI `10.6084/m9.figshare.16691575.v3`.

Downloaded source files are stored under `data/source/` with published MD5
checks enforced by the runner. The source metadata reports temporal coverage
2020 and OGL licensing. `lsoa_estimates.csv` uses LSOA11; the analysis converts
it to London LSOA21 using the official ONS exact-fit V3 lookup stored alongside
the source data. Unlike a one-way best-fit lookup, this retains all split and
merge relationships and covers all 4,994 London LSOA21s.

## Run

```powershell
cd D:\SDS2025_workspace\CASA_FYP\FYP\rq2_spatial_signatures_analysis
python src\run_analysis.py
```

The main audit and interpretation summary is written to
`outputs/report/RESULTS.md`.
