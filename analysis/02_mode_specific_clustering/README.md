# 02 · Mode-specific clustering

Fits the two adopted models — Rail K=5 (diagonal-covariance GMM) and Bus K=4
(CLR-transformed, full-covariance GMM) — from the long tables produced in
`01_data_preparation/`. Rail and Bus are modelled entirely separately; their
cluster identifiers are not comparable across modes.

## Bus (`bus/src/`)

1. `01_prepare_features.py` — build the min-direction-36 raw-share and CLR
   feature matrices.
2. `02_run_clustering.py` — full GMM diagnostic run for a given feature
   variant; refits the reported K=4 solution.
3. `06_cluster_names.py` — emit and verify the canonical cluster names.
4. `07_posterior_membership.py` — posterior membership / assignment-confidence
   diagnostic for the reported solution.
5. `08_seed_agreement.py` — random-seed agreement (mean pairwise ARI).
6. `config.py`, `map_style.py` — shared configuration and cluster-map
   rendering used by the scripts above.

## Rail (`rail/src/`)

1. `02_build_features_allmodes.py` — build the full-week, 440-dimensional
   direction/day/time composition per station.
2. `03_cluster_allmodes.py` (+ `03b_full_covariance_grid_check.py`) — fit the
   adopted diagonal-covariance GMM and check it against a full-covariance
   grid.
3. `08_k_selection_panel.py` — the official K-selection evidence panel
   (BIC, seed ARI, bootstrap ARI) behind the dissertation's main-text figure.
4. `09_cluster_names.py` — emit and verify the canonical cluster names.
5. `10_posterior_membership_summary.py` — summarise posterior membership
   confidence for the adopted K=5 solution.
6. `06_profiles_and_maps_allmodes.py` — temporal usage-profile charts and
   spatial cluster maps.

## Output

Cluster labels, names, and model-selection diagnostics that
`03_lnwc_context/` and `04_urban_context/` join against (never refit). See
[`docs/analysis_manifest.md`](../../docs/analysis_manifest.md) for the frozen
cluster sizes, BIC and ARI values reported in the dissertation.
