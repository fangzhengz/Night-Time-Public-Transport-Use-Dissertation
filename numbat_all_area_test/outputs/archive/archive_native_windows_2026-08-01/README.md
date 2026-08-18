# archive_native_windows_2026-08-01

The all-modes rail result as adopted between 2026-07-30 and 2026-08-01, using
**native day-type windows**: MON/TWT/SUN 18:00-01:00 (28 quarter-hour bins) and
FRI/SAT 18:00-05:00 (44 bins), giving a 344-dimensional feature matrix.

## Why it was superseded

The native windows were designed for an Underground-only study, where the
network is closed after 01:00 on non-Night-Tube nights. Applied to the merged
all-modes population they discard real service: 0.18-0.24% of Monday,
Tuesday-Thursday and Sunday evening activity, present at 368 of the 404
stations, from operators (National Rail, Elizabeth line) that run past 01:00.
Every day type is now run over a common 18:00-05:00 window (440 features),
which also removes the "why are your windows unequal" question and matches the
bus pipeline, which already uses one window for all three of its day types.

## What changed, and what did not

The change was tested before adoption (`FYP/rq1_rail_method_tests/`, the
`fullweek_padded` cell and `06_robustness_padded.py`) at the converged
optimum:

- ARI against this archived result: **0.885**
- **16 of 404 stations (4.0%)** change cluster, all outer/mid-ring boundary
  cases moving between the two suburban clusters; no station in the central
  core moves
- cluster sizes 122/25/12/163/82 -> 118/26/12/166/82; the 12-station cluster
  is the **identical** twelve stations
- every eta-squared diagnostic moves by less than 0.01

So this archive and its replacement tell the same story. It is kept because
the numbers quoted in any document written before 2026-08-01 came from here.

## One methodological caveat that arose with the change

The padded 440-dim matrix does NOT converge at the `N_INIT = 20` used to
produce this archive; it needs >= 50. This archive's own 344-dim matrix does
converge at 20 (verified identical at n_init 20/50/100/200), so the labels here
are sound. The replacement is fitted at n_init = 100.
