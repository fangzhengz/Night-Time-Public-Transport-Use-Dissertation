# Incomplete mobility–public-transport mismatch analysis

This folder preserves an attempted comparison between area-level mobility/OD
activity and observed night-time public-transport use. The analysis was
considered during the research process but was not completed, implemented as a
formal dissertation question or reported in the submitted dissertation.

## Status: incomplete and not adopted

## Notes for archival

- **Code** (in `src/`): Preserved for reference and potential future work
- **Data** (in `data/`): Small reference lookups retained
- **Outputs** (in `outputs/`): Preserved as a stale historical snapshot so the attempted analysis remains inspectable; they are not valid final evidence

The bug in the original `config.py` (paths pointing at cluster labels instead of LNWC data) was fixed on 2026-08-08, but the retained outputs were generated on 2026-08-07, before that correction. They are kept to document what was attempted, not to support a claim or reproduce the submitted dissertation. A future reuse must rerun the corrected code from authorised inputs into a new output directory.

Several internal scripts and historical outputs retain the former working label
`RQ3`. That label records the chronology of development only; it does not refer
to a research question in the submitted dissertation.
