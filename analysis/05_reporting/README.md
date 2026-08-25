# 05 · Reporting

A presentation-only layer: reads the locked cluster labels and the formal
output tables from stages 02–04, and never fits, refits, or recomputes a
statistical test itself.

## Scripts

- `build_final_figures.py` — builds the Chapter 4 main-text candidate
  figure/table set.
- `make_behavioural_figures.py` — rebuilds the formal behavioural z-score
  panels from the committed aggregate tables (the script referenced in the
  main [README](../../README.md) quick-start).

## Output

Local build products land in `results/generated_figures/`;
[`scripts/publish_results.py`](../../scripts/publish_results.py) then
promotes adopted rebuilds into
[`results/recomputed_figures/`](../../results/recomputed_figures/) without
ever overwriting the paper-matched figures in
[`results/figures/`](../../results/figures/). See
[`results/README.md`](../../results/README.md) for how the two figure
collections relate.
