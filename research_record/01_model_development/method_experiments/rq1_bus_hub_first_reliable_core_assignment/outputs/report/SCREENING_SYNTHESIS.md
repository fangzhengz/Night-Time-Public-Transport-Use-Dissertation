## Material Passport

- ID: `hub-first-core-threshold-screen-synthesis`
- Type: experiment synthesis
- Status: completed
- Verification status: VERIFIED for deterministic T=100, K=3 reproduction
- Scope: threshold screening only

# Screening synthesis

## Outcome

No threshold satisfied the pre-specified strict gate while retaining at least
75% of the 3,593 hub-first LSOAs.

The preferred 20%--25% exclusion range behaved as follows:

| weaker-direction threshold | core coverage | K values passing activity < timing |
|---:|---:|:---|
| 90 | 79.3% | 3 |
| 100 | 76.8% | 3 |
| 110 | 75.1% | 3 |

Thus, the useful result at K=3 is not invariant to K. K=2, K=4 and K=5 still
produced activity-dominated partitions in the preferred coverage range.

Across the wider screen:

| weaker-direction threshold | core coverage | K values passing activity < timing |
|---:|---:|:---|
| 0 | 100.0% | none |
| 50 | 89.8% | none |
| 70 | 84.3% | none |
| 90 | 79.3% | 3 |
| 100 | 76.8% | 3 |
| 110 | 75.1% | 3 |
| 125 | 71.9% | 2 |
| 150 | 67.5% | 2, 3 |
| 175 | 63.5% | 2, 3 |
| 200 | 59.8% | 2, 3 |
| 250 | 53.5% | 2, 3 |
| 300 | 48.3% | 2, 3, 4, 5 |

Threshold 300 was the first screened value at which all four K values passed,
but it retained only 1,736 LSOAs (48.3%). It therefore fails the coverage rule
before the adjacent-threshold confirmation rule is considered.

## Key numeric evidence

At threshold 100:

| K | activity eta2 | timing mean eta2 | gate |
|---:|---:|---:|:---|
| 2 | 0.4118 | 0.0067 | fail |
| 3 | 0.0785 | 0.2674 | pass |
| 4 | 0.4822 | 0.3243 | fail |
| 5 | 0.4906 | 0.3545 | fail |

At threshold 300:

| K | activity eta2 | timing mean eta2 | gate |
|---:|---:|---:|:---|
| 2 | 0.0004 | 0.2824 | pass |
| 3 | 0.0193 | 0.3874 | pass |
| 4 | 0.2707 | 0.3490 | pass |
| 5 | 0.3224 | 0.4164 | pass |

## Reproducibility and execution checks

- All 48 main and stress fits converged.
- The T=100, K=3, n_init=5 fit was repeated with the same seed.
- All numeric output fields matched exactly, excluding runtime.
- Main output: 32 threshold-by-K rows and 8 threshold summaries.
- Stress output: 16 threshold-by-K rows and 4 threshold summaries.
- All expected output files were non-empty.
- A non-fatal joblib warning reported that physical core count could not be
  detected; joblib used the logical core count instead.

## Interpretation boundary

This run does not show that reliable-core clustering is generally invalid. It
shows that the stringent K=2..5-invariant gate cannot be met with the desired
75% coverage under the fixed hub-first alpha=0 full-covariance GMM design.

No final K has been selected, no bootstrap validation has been run for a final
candidate, and no low-information LSOA has been assigned. Proceeding to
posterior assignment would therefore be premature under the agreed gate.

