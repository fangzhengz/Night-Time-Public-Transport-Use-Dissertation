# rq1_bus_daytype_normalisation — FROZEN 2026-08-01

Sidecar test of the **normalisation denominator** on the bus leg. Read-only:
`rq1_bus_stoparea_clustering` was never modified and remains the adopted result
(StopArea CLR K=4).

**Outcome: full-week closure retained.** This folder is the evidence and the
appendix material for that choice, not a candidate pipeline.

## Why it was built

The canonical matrices close each direction over the whole 36-cell week. That was
believed to be Clara's 2026-06-25 instruction; re-reading the transcript
(`FYP/meeting/Fangzheng + Clara Catch Up.docx`, ~18:00) she asked for the full-week
*vector* and deferred the denominator to what was already in place. Her own paper
(Peiret-García, Kimani & Suel, *Beyond the Commute*, `FYP/参考文献/BtC_paper.pdf`,
§3.1 Eqs. 1-2) closes per day type. So the denominator was an undocumented
extension with no cited precedent, and needed testing rather than assuming.

## Variants (all on the canonical 3,372 LSOAs unless noted)

| id | variant | what it isolates |
|----|---------|------------------|
| B1 | `daytype_raw_share` | the closure change, nothing else |
| B2 | `daytype_clr_a1` | block-wise CLR, α=1, block-internal prior |
| B3 | `daytype_clr_a033` | α=0.33 — α's effective strength triples under block closure, so this separates smoothing from closure |
| B4 | `daytype_raw_share_strict` | every direction×day-type block ≥36 (n=2,493) |

## What it found

- Day-type closure is feasible (0 empty blocks of 20,232) and day-type mass is
  near-balanced (38/35/27%).
- **B1 is the only variant that separates on shape.** B2/B3 reproduce the known
  CLR pathology (zero-cell η² 0.87-0.92 against canonical CLR's 0.92); lowering α
  makes it worse. The problem is the data's zero density, not the coordinate
  system.
- The plain swap is not a free win: zero-cell η² rises 0.54→0.79 and central/outer
  total variation falls 0.376→0.197, i.e. Howard's mixing objection gets worse.
- Day-type closure is *more* bootstrap-stable (ARI 0.901 vs 0.786 at K=4). It was
  not rejected for instability.
- ARI vs adopted labels 0.36-0.58, so a switch would have invalidated every
  cluster name in all seven downstream folders.

## Known gap if ever resumed

**B5 = full-week closure on the strict 2,493 sample was never run.** Without it,
B4's striking numbers (activity η² 0.138, zero-cell η² 0.028) are confounded
between closure and sample and must not be quoted as a closure effect.

## Run order

```bash
python src/01_prepare_features.py
python src/02_run_clustering.py --variant daytype_raw_share      # and the other three
python src/03_compare.py
python src/04_figures.py --variant daytype_clr_a1
```
