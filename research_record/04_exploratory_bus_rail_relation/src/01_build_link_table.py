"""Build the single link table every test in this folder reads.

One row per bus LSOA that was retained in the bus clustering fit, carrying:
  * the bus cluster label and its night metrics,
  * how far that LSOA's bus stops sit from the nearest rail station, under
    three aggregations (see below),
  * which rail station is nearest and that station's cluster, and
  * distance to Charing Cross as the centrality control.

WHY MEASURE FROM StopArea POINTS, NOT LSOA CENTROIDS
The bus cluster labels live at LSOA level, but LSOAs in outer London are large
enough that their centroid is a poor stand-in for where the bus stops actually
are. So distances are measured from each StopArea's own coordinate and only
then aggregated up to the LSOA.

THREE AGGREGATIONS, ON PURPOSE
Aggregating StopArea distances to an LSOA is a real modelling choice, not a
detail, so all three are computed and carried through:
  * dist_min_m       -- the closest any bus stop in this LSOA gets to rail.
                        "Access" semantics.
  * dist_mean_m      -- unweighted mean over stops. "Geometry" semantics.
  * dist_wmean_m     -- mean weighted by each stop's night activity. "Typical
                        passenger" semantics.
dist_wmean_m is the headline because the claim under test is about where the
bus ACTIVITY sits relative to rail, not where the stop points sit. The other
two are reported alongside so the finding cannot be an artefact of this choice.

Activity weight = boardings + alightings summed over all quarter-hour night
bins and all three day_types, matching the (unweighted-by-day_type) convention
the bus clustering itself used in rq1_bus_stoparea_clustering.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import config as C


def load_rail() -> pd.DataFrame:
    """Current clustered rail stations with BNG coordinates and cluster labels."""
    coords = pd.read_csv(C.RAIL_COORDS)
    metrics = pd.read_csv(C.RAIL_UNIT_METRICS)

    coords = coords.rename(columns={"unit": "NLC"})
    coords["NLC"] = coords["NLC"].astype(str).str.strip()
    metrics["NLC"] = metrics["NLC"].astype(str).str.strip()

    rail = metrics.merge(
        coords[["NLC", "easting", "northing", "mode_label", "is_lu"]],
        on="NLC",
        how="left",
        validate="one_to_one",
    )
    missing = rail[["easting", "northing"]].isna().any(axis=1).sum()
    if missing:
        raise RuntimeError(
            f"{missing} of {len(rail)} clustered rail stations have no coordinate; "
            "the coords file and the clustering have drifted apart."
        )
    expected = pd.read_csv(C.RAIL_LABELS, usecols=["unit"])["unit"].nunique()
    if len(rail) != expected:
        raise RuntimeError(
            f"Rail metrics contain {len(rail)} stations but current labels contain {expected}."
        )
    return rail


def load_stopareas() -> pd.DataFrame:
    """StopArea-level night activity with coordinates and parent LSOA."""
    qhr = pd.read_parquet(C.STOPAREA_NIGHT_QHR)
    qhr["activity"] = qhr["boardings"].astype(float) + qhr["alightings"].astype(float)
    stoparea = (
        qhr.groupby(
            ["stoparea_unit_code", "stoparea_lsoa", "unit_easting", "unit_northing"],
            observed=True,
            as_index=False,
        )["activity"]
        .sum()
        .rename(columns={"stoparea_lsoa": "lsoa"})
    )
    if stoparea["stoparea_unit_code"].duplicated().any():
        raise RuntimeError(
            "A StopArea appears with more than one coordinate or parent LSOA; "
            "the crosswalk is not one-to-one."
        )
    return stoparea


def nearest_rail(stoparea: pd.DataFrame, rail: pd.DataFrame) -> pd.DataFrame:
    """Attach nearest-rail-station distance, NLC and cluster to each StopArea."""
    tree = cKDTree(rail[["easting", "northing"]].to_numpy(dtype=float))
    distances, indices = tree.query(
        stoparea[["unit_easting", "unit_northing"]].to_numpy(dtype=float), k=1
    )
    out = stoparea.copy()
    out["dist_m"] = distances
    out["nearest_rail_nlc"] = rail["NLC"].to_numpy()[indices]
    out["nearest_rail_cluster"] = rail["cluster"].to_numpy()[indices]
    out["dist_centre_m"] = np.hypot(
        out["unit_easting"].to_numpy(dtype=float) - C.CENTRE_EASTING,
        out["unit_northing"].to_numpy(dtype=float) - C.CENTRE_NORTHING,
    )
    return out


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    total = float(weights.sum())
    if total <= 0:
        return float(np.mean(values)) if len(values) else np.nan
    return float(np.average(values, weights=weights))


def aggregate_to_lsoa(stoparea: pd.DataFrame) -> pd.DataFrame:
    """Collapse StopArea rows to one row per LSOA."""
    rows = []
    for lsoa, group in stoparea.groupby("lsoa", observed=True):
        distances = group["dist_m"].to_numpy(dtype=float)
        weights = group["activity"].to_numpy(dtype=float)

        # Which rail station does the most bus night activity in this LSOA sit
        # nearest to? Activity-weighted rather than a plain count, so a cluster
        # of tiny stops cannot outvote the LSOA's main interchange.
        by_station = (
            group.groupby(["nearest_rail_nlc", "nearest_rail_cluster"], observed=True)["activity"]
            .sum()
            .sort_values(ascending=False)
        )
        dominant_nlc, dominant_cluster = by_station.index[0]

        rows.append(
            {
                "lsoa": lsoa,
                "n_stopareas": int(len(group)),
                "bus_activity": float(weights.sum()),
                "dist_min_m": float(distances.min()),
                "dist_mean_m": float(distances.mean()),
                "dist_wmean_m": weighted_mean(distances, weights),
                "nearest_rail_nlc": dominant_nlc,
                "nearest_rail_cluster": int(dominant_cluster),
                "dist_centre_wmean_m": weighted_mean(
                    group["dist_centre_m"].to_numpy(dtype=float), weights
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    print("Loading rail stations...")
    rail = load_rail()
    print(f"  {len(rail)} clustered rail stations with coordinates.")

    print("Loading bus StopArea night activity...")
    stoparea = load_stopareas()
    print(f"  {len(stoparea)} StopAreas across {stoparea['lsoa'].nunique()} LSOAs.")

    print("Computing nearest rail station per StopArea...")
    stoparea = nearest_rail(stoparea, rail)

    print("Aggregating StopArea distances to LSOA...")
    lsoa = aggregate_to_lsoa(stoparea)

    print("Joining bus cluster labels and metrics...")
    bus_labels = pd.read_csv(C.BUS_LABELS)
    bus_labels = bus_labels.loc[bus_labels["retained_for_fit"]].copy()
    bus_labels = bus_labels[["lsoa", "cluster"]].rename(columns={"cluster": "bus_cluster"})

    bus_metrics = pd.read_csv(C.BUS_UNIT_METRICS)
    metric_columns = [
        c
        for c in [
            "log_total_activity",
            "direction_balance",
            "post_midnight_share",
            "deep_night_share",
            "post_midnight_persistence",
            "weekend_ratio",
        ]
        if c in bus_metrics.columns
    ]
    bus_metrics = bus_metrics[["lsoa"] + metric_columns]

    linked = bus_labels.merge(lsoa, on="lsoa", how="left", validate="one_to_one")
    linked = linked.merge(bus_metrics, on="lsoa", how="left", validate="one_to_one")

    unmatched = linked["dist_wmean_m"].isna().sum()
    if unmatched:
        # A retained LSOA with no StopArea row would mean the clustering and the
        # StopArea preprocessing disagree about which LSOAs have bus activity.
        raise RuntimeError(
            f"{unmatched} retained bus LSOAs have no StopArea geometry -- the bus "
            "labels and the StopArea crosswalk have drifted apart."
        )

    # Within-radius flags. These only gate the co-occurrence test (test B):
    # beyond the radius an LSOA has no plausible rail node and must not borrow
    # a distant station's cluster label. Test A uses uncapped distances.
    for radius in (C.CATCHMENT_PRIMARY_M, C.CATCHMENT_SENSITIVITY_M):
        linked[f"within_{radius}m"] = linked["dist_min_m"] <= radius

    linked["bus_cluster_name"] = linked["bus_cluster"].map(C.BUS_CLUSTER_NAMES)
    linked["nearest_rail_cluster_name"] = linked["nearest_rail_cluster"].map(
        C.RAIL_CLUSTER_NAMES
    )

    out_path = C.DATA_OUT / "bus_rail_link_table.csv"
    linked.to_csv(out_path, index=False)
    print(f"\nWrote {out_path} ({len(linked)} bus LSOAs).")

    stoparea_out = C.DATA_OUT / "stoparea_nearest_rail.csv"
    stoparea.to_csv(stoparea_out, index=False)
    print(f"Wrote {stoparea_out} ({len(stoparea)} StopAreas).")

    print("\nCoverage within each radius:")
    for radius in (C.CATCHMENT_PRIMARY_M, C.CATCHMENT_SENSITIVITY_M):
        n_in = int(linked[f"within_{radius}m"].sum())
        print(f"  {radius:>5} m: {n_in}/{len(linked)} LSOAs ({n_in / len(linked):.1%})")

    print("\nActivity-weighted distance to nearest rail station, by bus cluster:")
    summary = (
        linked.groupby("bus_cluster_name")["dist_wmean_m"]
        .agg(["count", "median", "mean"])
        .round(1)
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()
