# RQ1 volume and context interpretation — provisional results

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-07-14T01:32:43.958567+00:00
- Verification Status: ANALYZED
- Version Label: rq1_context_metrics_v1

## Method boundary

The fixed RQ1 GMM labels are retained. Volume is added after clustering, not used to refit the clusters.
Rail metrics separate the 18:00–01:00 common window from the Friday/Saturday 01:00–05:00 Night Tube extension.
Bus metrics remain LSOA-level area-use measures.

## Rail cluster context

- Cluster 0 (n=119): median total activity 16,958.0; predominant volume band `medium`; exit/alighting leaning (median balance -0.432); median night_tube_extension_share=0.054; median weekend_common_ratio=0.772.
- Cluster 1 (n=15): median total activity 72,600.2; predominant volume band `high`; entry/boarding leaning (median balance 0.303); median night_tube_extension_share=0.042; median weekend_common_ratio=1.041.
- Cluster 2 (n=44): median total activity 36,595.6; predominant volume band `high`; exit/alighting leaning (median balance -0.140); median night_tube_extension_share=0.035; median weekend_common_ratio=0.963.
- Cluster 3 (n=38): median total activity 35,616.7; predominant volume band `high`; entry/boarding leaning (median balance 0.320); median night_tube_extension_share=0.013; median weekend_common_ratio=0.684.
- Cluster 4 (n=54): median total activity 6,162.6; predominant volume band `low`; exit/alighting leaning (median balance -0.545); median night_tube_extension_share=0.018; median weekend_common_ratio=0.682.

## Bus cluster context

- Cluster 0 (n=336): median total activity 235.1; predominant volume band `low`; exit/alighting leaning (median balance -0.053); median post_midnight_share=0.150; median weekend_ratio=0.823.
- Cluster 1 (n=2763): median total activity 1,140.2; predominant volume band `high`; exit/alighting leaning (median balance -0.124); median post_midnight_share=0.107; median weekend_ratio=0.790.
- Cluster 2 (n=1001): median total activity 139.4; predominant volume band `low`; exit/alighting leaning (median balance -0.177); median post_midnight_share=0.049; median weekend_ratio=0.737.

## Interpretation limits

- Volume bands are mode-specific tertiles and are not cross-mode equivalents.
- A high volume or late-night share is observed use, not evidence of unmet demand.
- Direction balance does not identify trip purpose or passenger occupation.
- Rail late-night extension partly reflects service availability; it is not a pure behavioural measure.