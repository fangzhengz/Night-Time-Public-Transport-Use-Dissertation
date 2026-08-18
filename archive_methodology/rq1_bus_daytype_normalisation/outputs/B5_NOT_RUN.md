# B5 (`fullweek_raw_share_strict`) — deliberately not run

The feature matrix `features/X_fullweek_raw_share_strict.parquet` exists and is
valid. Its builder is anchored: full-week closure applied to the base sample
reproduces the adopted `X_bus_stoparea_raw_share_min36.parquet` exactly (max
absolute difference 0.0, asserted in `src/01_prepare_features.py`). Only the
clustering battery was not run; a partial output directory from an interrupted
run was deleted rather than left to be mistaken for a result.

## Why the cell exists

B4 changed the closure **and** the sample at once relative to the canonical
result, so its striking numbers — activity eta² 0.138, zero-cell eta² 0.028 —
cannot be attributed to either. B5 is the missing cell of the 2x2:

|                 | full-week closure   | day-type closure |
|-----------------|---------------------|------------------|
| base, n=3,372   | canonical raw_share | B1               |
| strict, n=2,493 | **B5**              | B4               |

## Why it was stopped

User decision, 2026-08-01: day-type closure was frozen and full-week retained,
so the decomposition B5 would provide no longer informs a live decision.

## The consequence, which must be honoured

**B4's numbers stay confounded between closure and sample.** They must not be
quoted as a closure effect, nor as evidence that day-type closure fixes
zero-cell domination. If B4 is ever cited, run B5 first:

```bash
python src/02_run_clustering.py --variant fullweek_raw_share_strict --n-init 20 --bootstrap 20
```

## A second caveat on this whole folder

Every variant here was fitted at `n_init = 20`. The rail work later showed that
this can sit below the convergence point of a feature space, and that the
failure mode is an *attractive-looking* wrong answer rather than obviously
broken output — on the padded rail matrix, n_init=20 produced a cleaner, more
nameable typology than the correct optimum. Nothing in this folder has had an
n_init convergence check. Run one before interpreting any cluster structure
here. See `FYP/rq1_rail_method_tests/README.md` for the ladder that exposed it.
