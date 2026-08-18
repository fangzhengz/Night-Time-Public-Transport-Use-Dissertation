## Material Passport

- Origin: Claude Code, follow-up to rq1_bus_hub_first_alpha_grid_screen
- Verification Status: ANALYZED
- Version Label: bic_k_search_by_alpha_v1

# Does the BIC-preferred K move away from 3 as shrinkage increases?

## Motivation

`ALPHA_GRID_SCREEN.md` forced K=3 at every alpha to isolate the shrinkage
effect cheaply. That design cannot detect whether suppressing low-count
compositional noise changes the natural cluster count. This is a known
precedent in this project: the unrelated reliable-core reclustering
(`rq1_bus_activity_tiered_reclustering`) found BIC-best K=2 once low-activity
units were excluded, even though bootstrap stability still favoured K=3.

## Stage 1: exploratory BIC scan (full covariance, K=2..12, n_init=5)

BIC-best K by alpha:

|   alpha |   bic_best_K |   bic_best_value |
|--------:|-------------:|-----------------:|
|       5 |            3 |     -2.07951e+06 |
|      20 |            3 |     -2.11313e+06 |
|      50 |            2 |     -2.16379e+06 |
|     100 |            2 |     -2.22919e+06 |
|     200 |            2 |     -2.31418e+06 |

**BIC-preferred K shift vs the established K=3 reference: alpha=50->K=2, alpha=100->K=2, alpha=200->K=2.**

Full scan grid: `outputs/diagnostics/bic_k_search_scan_grid.csv`.
Adjacent-K purity/ARI at every alpha: `outputs/diagnostics/bic_k_search_adjacent_k.csv`.

## Stage 2: confirmatory deep dive (full covariance, n_init=20)

Only K=3 and each alpha's BIC-best K (deduplicated) were refit at full
n_init. `resample_below450_ari_vs_reference` compares against the
alpha=5/K=3 reference (0.598), which
is the same quantity Gate 4 in `ALPHA_GRID_SCREEN.md` used.

|   alpha |   K | is_bic_best_K   |          BIC |   silhouette |   min_cluster_share |   kw_epsilon2_log_total_activity |   eta2_log_total_activity |   timing_mean_eta2 |   timing_retention_vs_reference |   resample_below450_ari_mean |   resample_below450_ari_vs_reference | alternate_k_adopts   |
|--------:|----:|:----------------|-------------:|-------------:|--------------------:|---------------------------------:|--------------------------:|-------------------:|--------------------------------:|-----------------------------:|-------------------------------------:|:---------------------|
|       5 |   3 | True            | -2.07951e+06 |    0.0497006 |           0.13749   |                       0.582918   |                 0.517979  |           0.298943 |                        1        |                     0.597582 |                            0         | False                |
|      20 |   3 | True            | -2.11313e+06 |    0.0364368 |           0.119677  |                       0.530036   |                 0.480058  |           0.29501  |                        0.986845 |                     0.529957 |                           -0.0676258 | False                |
|      50 |   2 | True            | -2.16379e+06 |    0.127575  |           0.16393   |                       0.00985558 |                 0.0138258 |           0.266612 |                        0.891849 |                     0.499052 |                           -0.0985308 | False                |
|      50 |   3 | False           | -2.16081e+06 |    0.035139  |           0.0873922 |                       0.28389    |                 0.276231  |           0.345851 |                        1.15691  |                     0.517054 |                           -0.0805281 | False                |
|     100 |   2 | True            | -2.22919e+06 |    0.158885  |           0.13749   |                       0.0240829  |                 0.0291187 |           0.21612  |                        0.722947 |                     0.466601 |                           -0.130981  | False                |
|     100 |   3 | False           | -2.22138e+06 |    0.0653496 |           0.0943501 |                       0.0773498  |                 0.0753476 |           0.402653 |                        1.34692  |                     0.531068 |                           -0.0665142 | False                |
|     200 |   2 | True            | -2.3142e+06  |    0.227152  |           0.124409  |                       0.0490909  |                 0.0546221 |           0.187683 |                        0.627821 |                     0.455635 |                           -0.141947  | False                |
|     200 |   3 | False           | -2.30376e+06 |    0.108246  |           0.0940718 |                       0.0846021  |                 0.0864221 |           0.399787 |                        1.33733  |                     0.52224  |                           -0.0753426 | False                |

## Decision rule (pre-declared before reading Stage 2 results)

An alternate K at a given alpha is only a candidate replacement for the
K=3 reference if, relative to the alpha=5/K=3 baseline:

1. activity ANOVA eta-squared stays below the mean of the three timing
   metrics' eta-squared at that (alpha, K);
2. mean timing eta-squared retains at least 85% of the alpha=5/K=3 baseline;
3. every cluster contains at least 5% of LSOAs;
4. the below-450 conditional-resampling ARI is at least 0.05 higher than the
   alpha=5/K=3 baseline (not just higher than the same alpha forced to K=3;
   it must beat the original reference outright).

Adopting an alternate K also requires it to be the alpha's BIC-best K, not a
manually chosen runner-up.

**(alpha, K) pairs meeting all four conditions: None.**

## Reading

This resolves the open question directly: within the alphas already
screened, structure does move
(see the shift above), but that alone does not automatically justify adopting the new K
-- Gate 4's failure mode in `ALPHA_GRID_SCREEN.md` (low-activity resampling
stability not improving) is evaluated again here at each alpha's own
BIC-best K, not only at a forced K=3. If the adopted-pairs list above is
empty, the conclusion is that stronger shrinkage does not unlock a more
defensible structure in the range tested; if it is non-empty, that (alpha, K)
pair is the next candidate for the full historical-comparison and profile
work already done for K=3.

## Warnings and limitations

- Stage 1 uses n_init=5 for tractability; BIC differences smaller than
  run-to-run BIC noise at that n_init should not be over-interpreted --
  Stage 2 exists precisely to re-check the surviving candidates at n_init=20.
- The conditional multinomial resampling diagnostic still only measures
  count-sampling repeatability with the GMM held fixed; it does not include
  refitting uncertainty (same limitation as `ALPHA_GRID_SCREEN.md`).
- Comparing BIC across different alpha values remains invalid; BIC is only
  used within a fixed alpha to choose K here.
- Six alphas were not exhaustively re-swept in Stage 2 -- only K=3 and each
  alpha's own BIC-best K were confirmed. A K that is second-best by BIC but
  more stable is not evaluated by this script.

---

Started 2026-07-20T14:25:15.291901+00:00; elapsed 294.0s.
