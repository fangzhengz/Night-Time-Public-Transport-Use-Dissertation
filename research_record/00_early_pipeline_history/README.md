# From exploratory scripts to the final pipeline

The project did not begin with the final Rail and Bus workflows. Its earliest stage tested several temporal resolutions, clustering families and candidate-selection conventions in a shared script directory. Those trials were valuable because they revealed two problems that later shaped the dissertation: Rail and Bus could not be treated as interchangeable data structures, and apparently clear cluster maps could still rest on unstable temporal or spatial definitions.

This folder preserves the early analytical code as a historical layer. It includes the original preprocessing, feature-v2, KMeans/CLARA/GMM candidate and plotting scripts, but not the large duplicated output trees they generated. The 27 source output directories are listed in `legacy_output_inventory.csv`, while the wider source-to-destination decisions appear in `../SOURCE_COVERAGE.csv`. Their substantive successors are the full-week historical baseline, the grouped day-regime experiment, the 15-minute versus one-hour comparison and the adopted mode-specific pipelines.

## How to read this material

- `src/` is a chronological code record, not a runnable modern pipeline.
- File names retain their original numbering because that ordering shows how the analysis evolved.
- Early sample sizes, time windows and cluster labels are local to these scripts and must not be substituted for the final Rail n=403/K=5 or Bus n=3,383/K=4 results.
- KMeans, CLARA and early feature-v2 outputs are methodological antecedents, not omitted dissertation findings.

The purpose of this layer is therefore explanatory: it records why the later repository separated modes, formalised preprocessing checks and treated model stability as part of the evidence rather than as an afterthought.
