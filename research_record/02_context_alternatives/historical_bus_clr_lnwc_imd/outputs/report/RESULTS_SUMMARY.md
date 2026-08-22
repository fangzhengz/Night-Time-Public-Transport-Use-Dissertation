# Bus CLR K=4 × LNWC / IMD 2025

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run + validate
- Origin Date: 2026-07-21T14:23:56.855088+00:00
- Verification Status: ANALYZED (see REPRODUCIBILITY_CHECK.md)
- Version Label: bus_clr_k4_context_v1

## Fixed design and coverage

- RQ1 input is the accepted CLR K=4 partition; clustering is not refitted here.
- K=3 is a same-sample sensitivity comparator, not an alternative data pipeline.
- 3,365/3,365 retained LSOAs matched to both LNWC and IMD 2025.
- LNWC and IMD are external area-context variables and were not used to form the clusters.

## K=4 cluster context summary

| Cluster | Type | n | Share | Activity median | Post-midnight median | IMD median | Top LNWC enrichment |
|---:|---|---:|---:|---:|---:|---:|---|
| C1 | High activity / full-night | 1132 | 33.6% | 2612.2 | 0.127 | 26.30 | LNWC 1 (2.05×) |
| C3 | Medium activity / continuing | 1068 | 31.7% | 623.8 | 0.105 | 19.95 | LNWC 6 (1.18×) |
| C2 | Partial-night transition | 607 | 18.0% | 502.3 | 0.083 | 20.71 | LNWC 7 (1.37×) |
| C0 | Low activity / early-stop | 558 | 16.6% | 244.4 | 0.055 | 18.59 | LNWC 7 (2.44×) |

## LNWC association

- Chi-square(18)=650.73, p=1.59e-126, Cramer's V=0.254, n=3365.
- Minimum expected count=34.82; cells below 5=0 and below 1=0.
- Cramer's V is the primary magnitude summary; chi-square p-values do not account for spatial dependence.

## IMD association

- Kruskal-Wallis H(3)=203.91, p=6.04e-44, epsilon-squared=0.060, n=3365.
- 3/6 pairwise Dunn comparisons remain below 0.05 after BH correction.

## Does K=4 add externally distinguishable information?

- LNWC effect size: K=3 V=0.304; K=4 V=0.254.
- IMD effect size: K=3 epsilon-squared=0.063; K=4 epsilon-squared=0.060.
- Transition C2 has median activity=502.3, post-midnight share=0.083, IMD score=20.71, and its strongest LNWC enrichment is group 7 (1.37×).
- These external comparisons characterise the fourth component; they do not by themselves prove four natural classes.

## K=3 × K=4 crosswalk

| K=3 cluster | K4 C0 | K4 C1 | K4 C2 | K4 C3 |
|---:|---:|---:|---:|---:|
| C0 | 0 | 1132 | 0 | 40 |
| C1 | 558 | 0 | 386 | 0 |
| C2 | 0 | 0 | 221 | 1028 |

## Interpretation boundary

1. Results are LSOA-level associations, not evidence about the occupation or deprivation of individual passengers.
2. Neither chi-square nor Kruskal-Wallis corrects for spatial autocorrelation; effect sizes and mapped structure carry more weight than very small p-values.
3. The retained 3,365-LSOA sample excludes low-total and one-direction exception areas, so findings describe the accepted modelling sample rather than every London LSOA.
4. K was explored before this external analysis. K=3 is therefore retained as a transparent sensitivity comparator to reduce post-selection overclaiming.
5. IMD and LNWC are parallel external lenses. They are not fused into the RQ1 cluster definition and should not be read causally.

## Statistical fallacy scan

- Coverage: 11/11 checked.
- Material cautions: ecological fallacy, selected-sample/Berkson-type distortion, look-elsewhere/forking paths, spatially dependent inference, correlation-versus-causation and reverse-causality language.
- Not materially implicated by this cross-sectional design: regression to the mean, attrition/survivorship, diagnostic base-rate neglect and collider adjustment (no adjustment model is fitted here).