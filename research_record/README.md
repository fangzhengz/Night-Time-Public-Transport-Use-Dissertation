# Research record

The final pipeline is only the last stage of a longer research process. Questions about spatial units, low-flow observations, temporal normalisation, cluster number and contextual geography were not resolved in a single step; they were clarified through a sequence of comparisons, failed gates, sensitivity checks and revised interpretations. This directory preserves that sequence so the final choices can be understood rather than merely accepted.

The record remains separate from `analysis/` and `results/`. Nothing here is executed by the main pipeline or promoted into the dissertation evidence layer. A file's presence means that an approach was genuinely investigated; it does not mean that its numerical results were adopted.

## How to read the record

| Directory | Contents | Relationship to the dissertation |
|---|---|---|
| `01_model_development/` | Early baselines, alternative feature definitions, covariance/K checks, bootstrap and seed stability, low-flow thresholds, CLR/ILR validation, Rail scope and time-window tests, plus the fuller adopted-Bus diagnostic snapshot | Some checks informed final choices; their historical outputs retain the sample and specification used when they were run |
| `02_context_alternatives/` | The 1,200 m to 800 m LNWC development path, independent-variable development, facility diversity, LOAC, Spatial Signatures and earlier RQ2 implementations | Separates the final 800 m evidence ancestry from context side analyses not used in the final Results structure |
| `03_deferred_rq3_mismatch/` | Planned mobility-versus-public-transport mismatch RQ3 | Formally dropped; preserved code and stale historical outputs require the warnings in its `STATUS.md` |
| `04_exploratory_bus_rail_relation/` | Distance-to-rail and Bus-cluster/Rail-cluster spatial co-occurrence tests | Completed exploratory side analysis, not reported as a formal dissertation result |

`STATUS.csv` is the study-level index. Read it before opening an output. The original READMEs, code, tables, reports and figures are retained as evidence of what was actually attempted, including negative findings and explicitly unexecuted stages.

## Evidence boundary

- The adopted specification remains documented in the repository root and `docs/analysis_manifest.md`.
- Historical cluster labels and sample sizes are local to their experiment. They must not replace the final Rail n=403/K=5 or Bus n=3,383/K=4 evidence.
- The primary Rail contextual radius is 800 m. Any 1,200 m result in this record is a sensitivity or an earlier specification.
- Cross-mode work is descriptive and spatial. It does not establish interchange flows, passenger identity, causality, unmet demand or service deficiency.
- `historical`, `superseded`, `partial`, `not_run`, `deferred` and `exploratory` are substantive status labels, not quality rankings.

## Reproducibility status

This is an archival snapshot, not a second end-to-end pipeline. Many scripts retain their original relative paths and require data that cannot be redistributed. Reports and compact outputs are included so decisions remain auditable. Before reusing an old study, update its paths, verify input hashes and sample definitions, and rerun it in isolation; do not connect it directly to the adopted pipeline.
