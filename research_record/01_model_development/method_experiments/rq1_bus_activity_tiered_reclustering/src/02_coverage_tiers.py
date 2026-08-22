"""Classifies ALL 4,994 Greater London LSOAs into coverage tiers, not just
the 4,100 that entered the adopted RQ1 bus clustering.

Per the remediation Codex proposed (2026-07-19): label by what was
*observed*, never claim "no service" from usage data alone (BUSTO is
realised ridership, not timetable/frequency -- that would need GTFS data
this project does not have).

Tiers:
  0. no_recorded_activity   -- no BUSTO stop matched to this LSOA at all.
  1. matched_stop_no_activity -- a stop is matched, but recorded activity is
     effectively zero (excluded even under the current MIN_TOTAL=1 rule).
  2. below_reliable_threshold -- in the current 4,100-unit study, but below
     the reliable-core threshold chosen by 01_threshold_selection.py.
  3. reliable_core -- enters the reclustering in 03_recluster_reliable_core.py.

Threshold for tiers 2/3 is read from
`outputs/report/THRESHOLD_SELECTION.md`'s recommendation if
01_threshold_selection.py has already run; otherwise pass --threshold.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

sys.path.insert(0, str(FYP / "rq1_bus_geography_diagnostic" / "src"))
from run_geography_diagnostic import load_lsoa_coords  # noqa: E402

STOP_LSOA_LOOKUP = FYP / "outputs" / "preprocessed_busto" / "busto_stop_lsoa_lookup.csv"
X_BUS = FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "X_bus.parquet"
UNIT_METRICS = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"
THRESHOLD_GRID_CSV = ROOT / "outputs" / "data" / "threshold_selection_grid.csv"

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)


def resolve_threshold(cli_value: float | None) -> float:
    if cli_value is not None:
        return cli_value
    if THRESHOLD_GRID_CSV.exists():
        grid = pd.read_csv(THRESHOLD_GRID_CSV)
        grid["timing_mean_eta2"] = grid[
            ["eta2_post_midnight_share", "eta2_deep_night_share", "eta2_post_midnight_persistence"]
        ].mean(axis=1)
        resolved = grid[grid["eta2_log_total_activity"] < grid["timing_mean_eta2"]]
        if not resolved.empty:
            return float(resolved["threshold"].min())
    raise SystemExit(
        "No threshold available: run 01_threshold_selection.py first, or pass --threshold explicitly."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()
    threshold = resolve_threshold(args.threshold)

    coords = load_lsoa_coords()  # all 4,994 LSOAs
    all_lsoa = set(coords["lsoa"])

    lookup = pd.read_csv(STOP_LSOA_LOOKUP)
    matched_lsoa = set(lookup["lsoa"].astype(str))

    X = pd.read_parquet(X_BUS)
    studied_lsoa = set(X.index.astype(str))

    metrics = pd.read_csv(UNIT_METRICS)
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    activity = metrics.set_index("lsoa")["total_activity"]

    rows = []
    for lsoa in sorted(all_lsoa):
        if lsoa not in matched_lsoa:
            tier = "0_no_recorded_activity"
        elif lsoa not in studied_lsoa:
            tier = "1_matched_stop_no_activity"
        elif activity.get(lsoa, 0) < threshold:
            tier = "2_below_reliable_threshold"
        else:
            tier = "3_reliable_core"
        rows.append({"lsoa": lsoa, "tier": tier, "total_activity": activity.get(lsoa)})

    result = pd.DataFrame(rows)
    result.to_csv(DATA / "lsoa_coverage_tiers.csv", index=False)

    summary = (
        result["tier"].value_counts().sort_index().rename("n_lsoa").to_frame()
    )
    summary["pct_of_all_london_lsoa"] = (summary["n_lsoa"] / len(all_lsoa) * 100).round(1)
    summary.to_csv(DATA / "lsoa_coverage_tier_summary.csv")

    lines = [
        "# Bus LSOA coverage tiers (all 4,994 Greater London LSOAs)",
        "",
        f"Reliable-core threshold: total_activity >= {threshold}",
        "",
        "IMPORTANT: tier labels describe what was OBSERVED in BUSTO ridership",
        "data. They must not be read as \"no bus service\" -- BUSTO records",
        "realised boardings/alightings, not timetables or route frequency.",
        "A tier-0 LSOA may simply have no stop that BUSTO's stop-code table",
        "matched to a coordinate, not literally zero buses.",
        "",
        summary.to_markdown(),
        "",
        "## Tier definitions",
        "",
        "- **0_no_recorded_activity**: no BUSTO stop matched to this LSOA at all.",
        "- **1_matched_stop_no_activity**: a stop matched, but recorded activity",
        "  is effectively zero -- excluded even under the current MIN_TOTAL=1 rule.",
        "- **2_below_reliable_threshold**: in the 4,100-unit study, but below the",
        "  reliable-core threshold -- report descriptively (volume, IMD/LNWC",
        "  context), do not force into the shape-clustering.",
        "- **3_reliable_core**: enters `03_recluster_reliable_core.py`.",
    ]
    (REPORT / "COVERAGE_TIERS.md").write_text("\n".join(lines), encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
