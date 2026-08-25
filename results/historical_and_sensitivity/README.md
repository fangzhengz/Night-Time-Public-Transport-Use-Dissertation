# Historical, diagnostic and sensitivity results

This page provides a reader-facing route into the comparisons that shaped the
final method. They include negative tests, superseded specifications and formal
stability checks. Their historical sample sizes and cluster labels belong only
to the experiment in which they were produced; they must not replace the final
Rail n=403/K=5 or Bus n=3,383/K=4 evidence.

The linked files remain in `research_record/` rather than being copied here.
Keeping one authoritative copy preserves the accompanying warning and prevents
an old output from being mistaken for a second final result.

## Early pipeline and temporal design

| Study | Result entry | Contribution to the final design |
|---|---|---|
| Earliest KMeans, CLARA, GMM and feature-v2 sequence | [Narrative and 27-directory output inventory](../../research_record/00_early_pipeline_history/) | Records the path from a shared early pipeline to separate mode-specific models; large duplicated runtime trees are indexed rather than copied |
| Bus 15-minute versus one-hour resolution | [Result summary](../../research_record/01_model_development/method_experiments/bus_time_resolution_15min_vs_1h/outputs/report/RESULTS_SUMMARY.md) | Controlled comparison on the same historical source universe |
| Grouped weekday/weekend clustering | [Complete record](../../research_record/01_model_development/method_experiments/grouped_day_regime_clustering/) | Superseded experiment that clustered day regimes separately |
| Rail weekend metric window | [Sensitivity report](../../research_record/01_model_development/formal_sensitivity_checks/rail_weekend_metric_window/outputs/report/REPORT.md) | Tests descriptor definitions without refitting the final clusters |

## Bus spatial units, transformations and model checks

| Study | Result entry | Status |
|---|---|---|
| StopArea-only isolation | [Comparison report](../../research_record/01_model_development/method_experiments/bus_stoparea_only_isolated_test/outputs/report/STOPAREA_ONLY_ISOLATED_COMPARISON.md) | Completed, not adopted |
| Hub and zero-direction audit | [Result summary](../../research_record/01_model_development/method_experiments/bus_hub_zero_audit/outputs/report/RESULTS_SUMMARY.md) | Preprocessing audit |
| Hub-first reorganisation | [Result summary](../../research_record/01_model_development/method_experiments/bus_hub_first_reorganisation/outputs/report/RESULTS_SUMMARY.md) | Completed superseded preprocessing |
| Fixed-sample alpha comparison | [Result report](../../research_record/01_model_development/method_experiments/bus_hub_first_alpha_fixed_sample/outputs/report/ALPHA_SENSITIVITY_RESULTS.md) | Completed, not adopted |
| Wider alpha grid | [Screen report](../../research_record/01_model_development/method_experiments/rq1_bus_hub_first_alpha_grid_screen/outputs/report/ALPHA_GRID_SCREEN.md) | Completed, not adopted |
| Hellinger transformation | [Result report](../../research_record/01_model_development/method_experiments/bus_hellinger_transform/outputs/report/HELLINGER_RESULTS.md) | Negative sensitivity; failed its predeclared gate |
| CLR-ILR coordinate validation | [Result report](../../research_record/01_model_development/method_experiments/rq1_bus_ilr_transform/outputs/report/ILR_RESULTS.md) | Validation on the tested historical sample |
| Geography and covariance diagnostics | [Result summary](../../research_record/01_model_development/formal_sensitivity_checks/rq1_bus_geography_diagnostic/outputs/report/RESULTS_SUMMARY.md) | Formal diagnostic, not a replacement cluster solution |
| K and seed sensitivity | [Complete record](../../research_record/01_model_development/formal_sensitivity_checks/rq1_bus_k_selection_check/) | Formal sensitivity |
| Alternative 05 cutoff | [Record](../../research_record/01_model_development/formal_sensitivity_checks/rq1_bus_05cutoff_sensitivity/) | Planned/partial; no completed verified result report was found |

## Rail scope, transformations and stability

| Study | Result entry | Status |
|---|---|---|
| Rail scope, K and stability battery | [Complete record](../../research_record/01_model_development/rail_scope_and_stability/) | Contains final support and clearly labelled pre-correction archives |
| Rail normalisation and padding tests | [Complete record](../../research_record/01_model_development/method_experiments/rq1_rail_method_tests/) | Completed sensitivity with one documented stale sub-branch |
| Historical Underground K5-K6 validation | [Complete record](../../research_record/01_model_development/method_experiments/historical_rail_k5_k6_validation/) | Historical 270-station validation, not the final model |
| Rail ILR transformation | [Complete record](../../research_record/01_model_development/method_experiments/rail_ilr_sensitivity/) | Negative sensitivity dominated by historical temporal zero patterns |

## Context-development history

| Study | Result entry | Status |
|---|---|---|
| LNWC 1,200 m to 800 m development | [Comparison report](../../research_record/02_context_alternatives/lnwc_radius_development/outputs/report/COMBINED_COMPARISON.md) | Only the final 800 m version belongs to the main evidence |
| Early facility-diversity implementation | [Archived method and results](../../research_record/02_context_alternatives/facility_diversity/) | `log1p_poi_count` and nine-Group `shannon_group` were adopted through the final LSOA-first 20-variable pipeline; this direct-catchment implementation and its additional variants remain a spatial-method sensitivity |
| Independent-variable development | [Result report](../../research_record/02_context_alternatives/independent_variable_development/outputs/report/RESULTS.md) | Supporting development record for the compact final 20-variable layer |
| Historical Bus CLR × LNWC/IMD | [Result summary](../../research_record/02_context_alternatives/historical_bus_clr_lnwc_imd/outputs/report/RESULTS_SUMMARY.md) | Superseded 3,365-LSOA result |
| Historical behavioural context metrics | [Result summary](../../research_record/01_model_development/method_experiments/historical_context_metrics/outputs/report/RESULTS_SUMMARY.md) | Superseded provisional descriptor layer |
| Historical standalone LNWC map | [Historical figure and script](../../research_record/02_context_alternatives/historical_lnwc_spatial_map/) | Superseded visual result; not byte-identical to the submitted figure and not a separate statistical finding |

The complete 36-study index is
[`research_record/STATUS.csv`](../../research_record/STATUS.csv), while the
workspace-level retention decisions are recorded in
[`research_record/SOURCE_COVERAGE.csv`](../../research_record/SOURCE_COVERAGE.csv).
