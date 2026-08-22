# Night-Time Public Transport Use in London

London's public-transport system does not settle into a single pattern after dark. Rail stations and bus-served neighbourhoods remain active in different ways, at different times and in different urban settings. This repository follows the dissertation's attempt to describe that heterogeneity: first identifying recurring patterns of observed use within each mode, then asking how those patterns sit within London's night-work and wider socio-spatial geography.

The repository is both a guide to the submitted study and a reproducibility companion. Its main path follows the analysis ultimately used in the dissertation, while a separate research record preserves the alternatives, diagnostic checks and abandoned questions that helped shape that path. The original GitHub address cited in the dissertation is retained.

The immutable submitted dissertation is available at [`paper/CASA0010_dissertation_FangzhengZhou.pdf`](paper/CASA0010_dissertation_FangzhengZhou.pdf). Its SHA-256 is `5314d6511254ed0331ffcb712e27bdf7317fe6e1587aa7ab510522bda5f45963`.

## Adopted analytical specification

| Component | Adopted specification |
|---|---|
| Observation window | 18:00–05:00 |
| Rail analytical unit | 403 physical stations |
| Rail clustering | Gaussian mixture model, diagonal covariance, K=5 |
| Bus analytical unit | 3,383 LSOAs retained at at least 33 estimated boardings and 33 estimated alightings across the analysis week |
| Bus clustering | CLR-transformed temporal compositions, Gaussian mixture model, full covariance, K=4 |
| Rail context | 800 m circular catchments clipped by nearest-station Voronoi cells; equal-weight mean across distinct intersecting LSOAs |
| Context sample | Rail n=389; Bus n=3,383 |
| External context | Seven-part LNWC composition plus 20 individual area indicators |

Rail and Bus are modelled separately. Their cluster identifiers are mode-specific and are not directly comparable. All contextual findings are area-level associations; they do not identify passengers, trip purposes, causal effects, unmet demand or service deficiencies.

## Start here

- [`docs/analysis_manifest.md`](docs/analysis_manifest.md) maps each dissertation result to its input, code and output.
- [`docs/metric_dictionary.md`](docs/metric_dictionary.md) defines raw metrics, z-scores and inferential effect sizes.
- [`docs/data_provenance.md`](docs/data_provenance.md) states data sources, licence boundaries and required local paths.
- [`docs/reproducibility.md`](docs/reproducibility.md) separates the fast evidence check from the full raw-data rebuild.
- [`docs/full_rebuild_report.md`](docs/full_rebuild_report.md) records the completed end-to-end verification and reporting-layer consistency checks.
- [`results/tables/`](results/tables/) contains the compact machine-readable evidence reported in the dissertation.
- [`results/figures/`](results/figures/) contains descriptively named copies of the exact figures embedded in the submitted dissertation.
- [`results/recomputed_figures/`](results/recomputed_figures/) contains figures rebuilt from the adopted clean pipeline.
- [`research_record/`](research_record/) preserves method development, sensitivity and stability checks, deferred RQ3 work, and exploratory analyses that were not used as dissertation results.

## Pipeline order

```text
raw NUMBAT ──> Rail preprocessing ──> Rail K=5 clustering ──┐
                                                           ├─> behavioural summaries
raw BUSTO ──> StopArea/LSOA allocation ─> Bus K=4 CLR ─────┤
                                                           ├─> LNWC association
public/licensed context data ───────────────────────────────┴─> 20-variable context analysis
```

Run the committed-evidence checks with:

```bash
python scripts/validate_repository.py
```

Rebuild the behavioural z-score panels from the committed aggregate tables with:

```bash
python analysis/05_reporting/make_behavioural_figures.py
```

The full rebuild requires the raw/licensed datasets listed in [`docs/data_provenance.md`](docs/data_provenance.md). Those files are intentionally not redistributed. After configuring them locally, inspect the planned commands with `python scripts/run_pipeline.py --dry-run`, then run `python scripts/run_pipeline.py --full`.

## Repository layout

```text
analysis/01_data_preparation/    raw-to-analysis-ready Rail and Bus code
analysis/02_mode_specific_clustering/  adopted Rail K=5 and Bus K=4 models
analysis/03_lnwc_context/        behavioural summaries and LNWC analysis
analysis/04_urban_context/       20-variable contextual analysis
analysis/05_reporting/           final tables and figures
results/                         compact final evidence and reader-facing figures
paper/                           submitted PDF and its LaTeX source snapshot
docs/                            audit trail, definitions and reproducibility boundary
scripts/                         validation, reporting and orchestration
tests/                           frozen-result regression tests
```

Historical alternatives remain recoverable through Git history but are not part of this branch's active analytical path. Runtime products are excluded from Git; `scripts/publish_results.py` promotes adopted tables and diagnostics plus rebuilt figures into `results/recomputed_figures/`. It never overwrites the paper-matched figures in `results/figures/`.

The curated [`research_record/`](research_record/) makes the wider research process visible without mixing it into the adopted pipeline. Its files retain their historical assumptions and sample definitions; each study is status-labelled and should not be treated as a result reported in the submitted dissertation.

## Citation

Please cite the dissertation using [`CITATION.cff`](CITATION.cff).
