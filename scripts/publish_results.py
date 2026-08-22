"""Publish only adopted, compact outputs from a completed full rebuild."""
from __future__ import annotations

import csv
import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "results/generated_figures/Table_4_1_cluster_solution.csv": "results/tables/Table_4_1_cluster_solution.csv",
    "results/generated_figures/Table_4_2_behavioural_descriptor_tests.csv": "results/tables/Table_4_2_behavioural_descriptor_tests.csv",
    "results/generated_figures/Table_4_3_lnwc_association.csv": "results/tables/Table_4_3_lnwc_association.csv",
    "analysis/03_lnwc_context/outputs/data/lnwc_statistical_summary.csv": "results/tables/lnwc_association_full.csv",
    "analysis/04_urban_context/outputs/data/association_tests.csv": "results/tables/context_omnibus_tests.csv",
    "analysis/04_urban_context/outputs/data/per_cluster_tests.csv": "results/tables/context_cluster_vs_rest_tests.csv",
    "analysis/02_mode_specific_clustering/rail/outputs/data/rail_allmodes_k5_labels.csv": "results/tables/rail_cluster_labels.csv",
    "analysis/02_mode_specific_clustering/bus/outputs_1805_min33/clr/labels/k4_labels.csv": "results/tables/bus_cluster_labels.csv",
    "analysis/02_mode_specific_clustering/rail/outputs/data/rail_cluster_names.csv": "results/tables/rail_cluster_names.csv",
    "analysis/02_mode_specific_clustering/bus/outputs_1805_min33/data/bus_cluster_names.csv": "results/tables/bus_cluster_names.csv",
    "analysis/03_lnwc_context/outputs/data/rail_cluster_signature_z.csv": "results/tables/rail_behavioural_signature_z.csv",
    "analysis/03_lnwc_context/outputs/data/bus_cluster_signature_z.csv": "results/tables/bus_behavioural_signature_z.csv",
    "analysis/03_lnwc_context/outputs/data/rail_lnwc_composition_equal_weight.csv": "results/tables/rail_lnwc_composition_equal_weight.csv",
    "analysis/03_lnwc_context/outputs/data/rail_enrichment.csv": "results/tables/rail_lnwc_enrichment.csv",
    "analysis/03_lnwc_context/outputs/data/bus_enrichment.csv": "results/tables/bus_lnwc_enrichment.csv",
    "analysis/04_urban_context/outputs/data/rail_cluster_matrix_z.csv": "results/tables/rail_context_cluster_z.csv",
    "analysis/04_urban_context/outputs/data/bus_cluster_matrix_z.csv": "results/tables/bus_context_cluster_z.csv",
    "analysis/04_urban_context/outputs/data/rail_cluster_matrix_rb.csv": "results/tables/rail_context_effect_sizes.csv",
    "analysis/04_urban_context/outputs/data/bus_cluster_matrix_rb.csv": "results/tables/bus_context_effect_sizes.csv",
    "analysis/02_mode_specific_clustering/rail/outputs/data/rail_allmodes_k_selection_panel.csv": "results/diagnostics/rail/model_selection.csv",
    "analysis/02_mode_specific_clustering/rail/outputs/data/posterior_membership_summary.csv": "results/diagnostics/rail/posterior_membership_summary.csv",
    "analysis/02_mode_specific_clustering/bus/outputs_1805_min33/clr/diagnostics/kdiag.csv": "results/diagnostics/bus/model_selection.csv",
    "analysis/02_mode_specific_clustering/bus/outputs_1805_min33/clr/diagnostics/posterior_membership_summary.csv": "results/diagnostics/bus/posterior_membership_summary.csv",
    "results/generated_figures/Figure_4_2_rail_temporal_profiles.png": "results/recomputed_figures/rail_temporal_profiles.png",
    "results/generated_figures/Figure_4_3_rail_map.png": "results/recomputed_figures/rail_cluster_map.png",
    "results/generated_figures/Figure_4_4_bus_temporal_profiles.png": "results/recomputed_figures/bus_temporal_profiles.png",
    "results/generated_figures/Figure_4_5_bus_map.png": "results/recomputed_figures/bus_cluster_map.png",
    "results/generated_figures/Figure_4_6_rail_lnwc_enrichment.png": "results/recomputed_figures/rail_lnwc_enrichment.png",
    "results/generated_figures/Figure_4_7_bus_lnwc_enrichment.png": "results/recomputed_figures/bus_lnwc_enrichment.png",
    "results/generated_figures/rail_clusters_lnwc_map.png": "results/recomputed_figures/rail_clusters_lnwc_map.png",
    "results/generated_figures/bus_clusters_lnwc_map.png": "results/recomputed_figures/bus_clusters_lnwc_map.png",
    "analysis/04_urban_context/outputs/figures/rail_cluster_panels.png": "results/recomputed_figures/rail_context_profiles.png",
    "analysis/04_urban_context/outputs/figures/bus_cluster_panels.png": "results/recomputed_figures/bus_context_profiles.png",
    "analysis/04_urban_context/outputs/figures/rail_cluster_profile_heatmap.png": "results/recomputed_figures/rail_context_full_matrix.png",
    "analysis/04_urban_context/outputs/figures/bus_cluster_profile_heatmap.png": "results/recomputed_figures/bus_context_full_matrix.png",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest: list[dict[str, str]] = []
    missing = [source for source in FILES if not (ROOT / source).is_file()]
    if missing:
        raise SystemExit("Cannot publish incomplete rebuild; missing: " + ", ".join(missing))
    for source_name, destination_name in FILES.items():
        source = ROOT / source_name
        destination = ROOT / destination_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest.append({"published_file": destination_name, "rebuild_source": source_name, "sha256": digest(destination)})
        print(f"{source_name} -> {destination_name}")
    manifest_path = ROOT / "results" / "manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["published_file", "rebuild_source", "sha256"])
        writer.writeheader()
        writer.writerows(manifest)
    print(manifest_path)


if __name__ == "__main__":
    main()
