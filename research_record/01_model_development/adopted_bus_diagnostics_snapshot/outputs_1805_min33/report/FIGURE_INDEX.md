# Figure index: StopArea bus clustering

All figures are saved as publication-resolution PNG and vector PDF.

| Figure | Analytical purpose | Interpretation boundary |
|---|---|---|
| `01_sample_filtering` | Shows the both-directions>=33 rule and retained coverage. | The retained sample represents higher-evidence LSOAs, not all London LSOAs. |
| `02_full_covariance_delta_bic` | Shows within-variant K selection after setting each feature space's best BIC to zero. | Absolute BIC cannot be compared between raw-share and CLR spaces. |
| `03_candidate_diagnostics` | Compares silhouette, activity eta-squared, bootstrap ARI and weakest-cluster Jaccard for K=3/K=4. | No single metric settles K; activity eta-squared is a confounding diagnostic. |
| `04_bootstrap_stability` | Shows the distribution across 20 bootstrap resamples. | Stability does not establish substantive validity. |
| `05_raw_clr_partition_agreement` | Shows how raw-share clusters split under CLR on identical LSOAs. | Cluster numbers are arbitrary and CLR columns are reordered only for display. |
| `06_activity_by_cluster` | Makes the remaining activity association visible. | The fitted feature vectors omit total activity; these are external distributions. |
| `07_central_outer_comparison` | Compares external central/outer separation diagnostics. | Geography is not fitted by the GMM and is not an independent validation target. |

## Required core figures

Variant-specific figures under `outputs/raw_share/figures` and `outputs/clr/figures` reproduce the original two analyses' house style:

- Raw-share: `literature_mean1ph_full_map_k{3,4}`, `literature_mean1ph_full_profiles_k{3,4}`, and `literature_mean1ph_kdiag_full`.
- CLR: `clr_map_k{3,4}`, `clr_profiles_k{3,4}`, and `clr_kdiag_full`.
- Every core figure is saved as PNG and PDF; concise aliases (`map_k*`, `profiles_k*`, `kdiag_full`) are retained.
- The K-diagnostic is the original 2x3 silhouette, Calinski-Harabasz, Davies-Bouldin, BIC and bootstrap-ARI panel.
- `homogeneity_boxplots_k{3,4}`: four raw-metric dispersion panels.