"""Orchestrate the adopted full analysis without modifying the submitted PDF."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

STAGES = [
    ("bus raw preprocessing", [PYTHON, "analysis/01_data_preparation/bus/src/preprocess_busto.py", "--input-dir", str(ROOT), "--output-dir", "outputs/preprocessed_busto_1805_min33", "--start-min", "1080", "--end-min", "1740"]),
    ("bus StopArea allocation", [PYTHON, "analysis/01_data_preparation/bus/src/build_stoparea_data.py"]),
    ("bus feature construction", [PYTHON, "analysis/02_mode_specific_clustering/bus/src/01_prepare_features.py"]),
    ("bus clustering", [PYTHON, "analysis/02_mode_specific_clustering/bus/src/02_run_clustering.py", "--variant", "clr"]),
    ("bus cluster descriptors", [PYTHON, "analysis/02_mode_specific_clustering/bus/src/06_cluster_names.py"]),
    ("bus posterior summary", [PYTHON, "analysis/02_mode_specific_clustering/bus/src/07_posterior_membership.py"]),
    ("bus seed agreement", [PYTHON, "analysis/02_mode_specific_clustering/bus/src/08_seed_agreement.py"]),
    ("rail raw preprocessing", [PYTHON, "analysis/01_data_preparation/rail/src/01_preprocess_rail_allmodes.py"]),
    ("rail co-location merge", [PYTHON, "analysis/01_data_preparation/rail/src/01b_merge_colocated_stations.py"]),
    ("rail coordinate match", [PYTHON, "analysis/01_data_preparation/rail/src/01c_match_naptan_coords.py"]),
    ("rail spatial filter", [PYTHON, "analysis/01_data_preparation/rail/src/01d_filter_naptan_matched.py"]),
    ("rail feature construction", [PYTHON, "analysis/02_mode_specific_clustering/rail/src/02_build_features_allmodes.py"]),
    ("rail clustering", [PYTHON, "analysis/02_mode_specific_clustering/rail/src/03_cluster_allmodes.py"]),
    ("rail covariance check", [PYTHON, "analysis/02_mode_specific_clustering/rail/src/03b_full_covariance_grid_check.py"]),
    ("rail profiles", [PYTHON, "analysis/02_mode_specific_clustering/rail/src/06_profiles_and_maps_allmodes.py"]),
    ("rail K-selection panel", [PYTHON, "analysis/02_mode_specific_clustering/rail/src/08_k_selection_panel.py"]),
    ("rail cluster descriptors", [PYTHON, "analysis/02_mode_specific_clustering/rail/src/09_cluster_names.py"]),
    ("rail posterior summary", [PYTHON, "analysis/02_mode_specific_clustering/rail/src/10_posterior_membership_summary.py"]),
    ("behavioural metrics", [PYTHON, "analysis/03_lnwc_context/src/run_context_metrics.py"]),
    ("LNWC analysis", [PYTHON, "analysis/03_lnwc_context/src/run_lnwc_analysis.py"]),
    ("context variable table", [PYTHON, "analysis/04_urban_context/src/01_build_variable_table.py"]),
    ("context omnibus tests", [PYTHON, "analysis/04_urban_context/src/02_run_association_tests.py"]),
    ("context cluster tests", [PYTHON, "analysis/04_urban_context/src/03_per_cluster_tests.py"]),
    ("context figures", [PYTHON, "analysis/04_urban_context/src/04_build_figures.py"]),
    ("context cluster panels", [PYTHON, "analysis/04_urban_context/src/06_build_cluster_panels.py"]),
    ("release figures", [PYTHON, "analysis/05_reporting/build_final_figures.py"]),
    ("publish adopted results", [PYTHON, "scripts/publish_results.py"]),
    ("behavioural figures", [PYTHON, "analysis/05_reporting/make_behavioural_figures.py"]),
    ("frozen-result validation", [PYTHON, "scripts/validate_repository.py"]),
]

REQUIRED_INPUTS = [
    "巴士数据/NaPTAN_data",
    "巴士数据/Bus_Stops.csv",
    "地铁进出站数据",
    "巴士数据/NaPTAN_data/490.xml",
    "map/London_LSOA_2021_Boundaries.geojson",
    "night_time_work_data/london_night_workers_classification_data.csv",
    "IMDdata_2025/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv",
    "data/raw/os_poi/poi_6438516.gpkg",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print preflight and commands only")
    parser.add_argument("--full", action="store_true", help="Run the adopted pipeline")
    parser.add_argument("--source-root", type=Path, default=ROOT, help="Local root containing restricted raw-data folders")
    parser.add_argument("--start-at", type=int, default=1, help="One-based stage number for a validated resume")
    args = parser.parse_args()
    if not args.dry_run and not args.full:
        parser.error("choose --dry-run or --full")

    source_root = args.source_root.resolve()
    STAGES[0][1][3] = str(source_root)
    missing = [item for item in REQUIRED_INPUTS if not (source_root / item).exists()]
    print("Input preflight:")
    for item in REQUIRED_INPUTS:
        print(f"  {'OK' if (source_root / item).exists() else 'MISSING'}  {item}")
    print("\nAdopted stages:")
    if not 1 <= args.start_at <= len(STAGES):
        parser.error(f"--start-at must be between 1 and {len(STAGES)}")
    for number, (name, command) in enumerate(STAGES, 1):
        print(f"  {number:02d}. {name}: {' '.join(command)}")
    if args.dry_run:
        return
    if missing:
        raise SystemExit("Full run blocked by missing local inputs: " + ", ".join(missing))
    for number, (name, command) in enumerate(STAGES[args.start_at - 1 :], args.start_at):
        print(f"\n[{number:02d}/{len(STAGES):02d}] {name}", flush=True)
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
