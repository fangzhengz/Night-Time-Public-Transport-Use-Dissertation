# Reproducibility check

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-07-21T14:23:57.147893+00:00
- Verification Status: VERIFIED
- Version Label: bus_clr_k4_context_repro_v1

## Re-run

- Historical command: `<local-python> D:\SDS2025_workspace\CASA_FYP\FYP\new_bus_LNWC_IMD_test\src\01_run_bus_context_analysis.py`
- Exit code: 0
- Determinism rule: exact SHA-256 match for all primary CSV artifacts.
- Figures, timestamps and environment metadata are intentionally excluded from byte comparison.

| File | Before SHA-256 | After SHA-256 | Match |
|---|---|---|---|
| bus_k4_context_lsoa.csv | `9c4ed130b1bdd094888b596998362adce87b61fb40907943e8dce00022b436ac` | `9c4ed130b1bdd094888b596998362adce87b61fb40907943e8dce00022b436ac` | YES |
| k4_cluster_context_summary.csv | `71d0e361f6c4dc1ae8ba66fda94767471997ea38a1310d172d94cc3bc4f33529` | `71d0e361f6c4dc1ae8ba66fda94767471997ea38a1310d172d94cc3bc4f33529` | YES |
| k4_lnwc_association.csv | `f538cf876df878ec69e315ca8923f5f30dc8e117fab115737c672242825a60da` | `f538cf876df878ec69e315ca8923f5f30dc8e117fab115737c672242825a60da` | YES |
| k4_lnwc_enrichment.csv | `b9299b90755122798fcc98125d3ec2e52526e028686576f98ced56aadfb86022` | `b9299b90755122798fcc98125d3ec2e52526e028686576f98ced56aadfb86022` | YES |
| k4_imd_kruskal.csv | `c68bf25dbee2d9c7dafe8ebadcfcdff1dd7228137afbbc19bc08d56d1c49ff05` | `c68bf25dbee2d9c7dafe8ebadcfcdff1dd7228137afbbc19bc08d56d1c49ff05` | YES |
| k4_imd_dunn_pairwise.csv | `86ab9eab36b90f94423d41d5c248c6fd16f3fe3fa6b9fa0a11ee0cdacb72c16d` | `86ab9eab36b90f94423d41d5c248c6fd16f3fe3fa6b9fa0a11ee0cdacb72c16d` | YES |
| k3_k4_external_effect_sensitivity.csv | `13aa4cf4af5f6603f41bf2b852d293e8606422535ddd70d2ce5c7a7400fcb098` | `13aa4cf4af5f6603f41bf2b852d293e8606422535ddd70d2ce5c7a7400fcb098` | YES |
| k3_k4_crosswalk_counts.csv | `d5caf5fdd82b70749a64f2c049a915b730b871a37715502456677fcddddcf9a8` | `d5caf5fdd82b70749a64f2c049a915b730b871a37715502456677fcddddcf9a8` | YES |
