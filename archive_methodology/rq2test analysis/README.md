# RQ2 LNWC baseline test

This folder is an independent, reproducible trial linking the provisional
`cluster_clean_version_fullweek` RQ1 labels to the London Night Workers
Classification (LNWC). It does not modify any RQ1 input or output.

## Baseline specification

- Rail: provisional diagonal-GMM `K=6` labels.
- Bus: provisional full-GMM `K=4` labels.
- Bus spatial unit: LSOA, joined directly to LNWC by 2021 LSOA code.
- Rail spatial unit: 1,200 m station buffers clipped by Voronoi cells generated
  from the 270 Underground stations in the RQ1 universe.
- Rail LNWC context: area-weighted composition of LNWC groups within each
  catchment. Dominant LNWC is secondary; the seven-part composition is primary.
- Rail eligibility: the station point must fall within the Greater London/LNWC
  extent. Out-of-London Underground stations remain in the audit output but are
  excluded from the association estimates.
- Primary aggregation: equal weight per station/LSOA.
- Secondary rail aggregation: total-activity weighted.

The statistical tests are exploratory. In particular, ordinary chi-square tests
do not account for spatial autocorrelation among neighbouring LSOAs.

## Run

From this folder:

```powershell
py -3 src/run_analysis.py
node src/build_workbook.mjs
```

The exact Node executable and module path may differ by machine. The current
Codex run uses the bundled workspace Node runtime and a local `node_modules`
junction.

## Folder structure

```text
rq2test analysis/
├── README.md
├── src/
│   ├── config.py
│   ├── run_analysis.py
│   └── build_workbook.mjs
└── outputs/
    ├── data/
    ├── figures/
    ├── spatial/
    ├── report/
    └── workbook/
```

## Interpretation boundary

The outputs describe associations between transport-use profiles and the
surrounding area context. They do not identify the occupations or
socio-economic characteristics of individual passengers.

## Direct transport metrics × LNWC extension

The original baseline above tests `RQ1 cluster × LNWC`. A separate,
non-destructive extension now tests directly whether observed transport
indicators differ across the seven supplied LNWC area types:

```powershell
py -3 src/run_direct_metrics_analysis.py
node src/build_direct_metrics_workbook.mjs
```

Outputs are written only to `outputs/direct_metrics/`. Bus uses the direct LSOA
label. Rail uses the seven-part catchment composition and does not force the
station into one LNWC type for its primary analysis. Centrality-adjusted
omnibus tests are exploratory and use distance to Charing Cross as a single
baseline control.
