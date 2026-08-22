# RQ1 Clean Clustering Pipeline — GROUPED variant

Parallel to `cluster_clean_version/` (the BtC concatenated single-clustering
version). This folder splits clustering by **day-group**, motivated by service
regime, so the Night-Tube overnight signal is not diluted. Built 2026-06-23.

Everything except the day-handling is identical to the concatenated version
(BtC raw-share features, per-vector normalisation, GMM, 4-covariance BIC
selection, K not hard-picked). Preprocessing (steps 01/02 and the parquets in
`outputs/preprocessed/`) is reused unchanged; only `03/04/05` differ.

## Day groups (separate clusterings)
| Modality | weekday | weekend |
|---|---|---|
| **Rail** | MON+TWT (~01:00 close), 28 bins | **Fri+Sat pooled** (Night Tube → 05:00), 44 bins. **Sunday EXCLUDED** |
| **Bus** | Weekday | **Sat+Sun pooled** |

Within a group, member day-times are POOLED (counts summed → one night profile),
then per-vector normalised. Each (modality, group) is clustered on its own.

## Why split (vs the concatenated version)
In the 288-dim concatenated vector the weekday + Sunday early-decline blocks
(112 dims) diluted the Fri/Sat overnight tail, so the Night-Tube signal did not
drive the clustering. Splitting lets each group's own signal dominate.

## Headline results (2026-06-23)
| Dataset | X | BIC-best | silhouette K2 / K3 |
|---|---|---|---|
| rail_weekday | 270×56 | tied, K=2 | 0.49 / 0.28 |
| rail_weekend | 270×88 | tied, K=2 | 0.39 / 0.20 |
| bus_weekday | 3548×24 | full, K=5 | 0.18 / 0.08 |
| bus_weekend | 3742×24 | full, K=6 | 0.22 / 0.11 |

- Rail separation is markedly higher than in the concatenated version.
- **rail_weekend K=4 surfaces a nightlife/destination cluster (C2, n≈15)**: evening
  arrival, ~23:00 departure hump, overnight tail to 04:45 with a dawn bump,
  spatially concentrated in the Zone-1 core — the Night-Tube signal that was
  previously drowned out.
- Bus remains a weak continuum (silhouette negative for K≥6), as before.

## Pipeline (run from src/, in order)
`01_preprocess_rail.py` → `02_preprocess_bus.py` → `03_build_features.py`
→ `04_cluster.py` → `05_figures.py`. Outputs under `outputs/`
(`features/X_{modality}_{group}.parquet`, `diagnostics/`, `labels/`, `figures/`).
01/02 are reused from the concatenated version (same preprocessed parquets).
