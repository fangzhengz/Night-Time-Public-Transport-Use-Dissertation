# Results

This directory gathers the evidence at the end of the dissertation's analytical journey. The tables move from mode-specific cluster membership and behavioural interpretation to LNWC composition and the wider urban context; the figures provide the corresponding visual account. It is deliberately compact so that a reader can understand the findings without navigating the many intermediate experiments preserved elsewhere.

Two figure collections are kept because they answer different reproducibility questions. `figures/` lets a reader see exactly what appeared in the submitted dissertation, whereas `recomputed_figures/` shows what the adopted clean pipeline produces from the committed aggregates. Keeping them side by side makes provenance visible without allowing a later rebuild to rewrite the submitted record.

- `tables/` contains final cluster labels and descriptors, behavioural signatures, LNWC results and the 20-variable contextual tests.
- `diagnostics/` contains the Rail and Bus model-selection and posterior-membership summaries.
- `figures/` contains descriptively named, byte-identical copies of the figures embedded in the submitted dissertation.
- `recomputed_figures/` contains figures rebuilt from the adopted clean pipeline and committed aggregate tables.
- `exploratory/` is a reader-facing index to completed side analyses, deferred RQ3 work and context alternatives that were not used as dissertation results.
- `historical_and_sensitivity/` is a reader-facing index to model-development, stability, sensitivity and superseded-result records.
- `manifest.csv` records the exact pipeline source and SHA-256 hash for each published rebuild output in the recomputed layer.

The two non-final indexes contain links rather than duplicate copies. Their
underlying files remain in `research_record/`, where each study's original
status, sample and cautions are preserved in one authoritative location.

Runtime intermediates stay under `analysis/**/outputs*` and are excluded from Git. A complete local run ends by executing `scripts/publish_results.py`, which refreshes the tables, diagnostics and `recomputed_figures/` before validation.

The source copies of the submitted figures remain under `paper/source/figures/`. Validation compares their SHA-256 hashes with `results/figures/`, so a rebuild cannot silently replace the paper-matched layer.
