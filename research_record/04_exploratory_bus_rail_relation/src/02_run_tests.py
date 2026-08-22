"""Test A (distance to rail nodes) and Test B (cluster co-occurrence).

TEST A -- do bus clusters sit at systematically different distances from rail
nodes? Kruskal-Wallis with epsilon-squared, run on all three StopArea->LSOA
distance aggregations so the answer cannot hinge on that choice. Kruskal-Wallis
is rank-based, so the heavy right skew in raw metres needs no transform.

The same test is run on distance-to-Charing-Cross, and the Spearman correlation
between the two distances is reported. This is the honest centrality check: if
bus clusters separate on distance-to-centre just as strongly as on
distance-to-rail, and the two distances are tightly correlated, then "bus
activity organises around rail" is not distinguishable from "bus activity
organises around the centre" and the write-up must say so.

TEST B -- do particular bus cluster types co-occur with particular rail cluster
types? A bus LSOA borrows the cluster label of the rail station that the most
bus night activity in it sits nearest to, capped at the catchment radius.

Significance here needs care. 3,372 bus LSOAs share only 403 rail labels in
the current 2026-08-07 run, so
each label is replicated across many rows and an ordinary chi-square p-value on
n=3372 is meaningless -- the effective sample size is nearer the number of
rail stations. So:
  * Cramer's V is reported as a descriptive effect size;
  * significance comes from a permutation test that reassigns cluster labels
    ACROSS THE CURRENT RAIL STATIONS and rebuilds the table each time, which preserves
    the many-LSOAs-per-station replication under the null;
  * V is also recomputed within distance-to-centre terciles, because both
    clusterings track centrality and an unstratified V would partly just be
    measuring that.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency

import config as C

DISTANCE_COLUMNS = {
    "dist_wmean_m": "activity-weighted mean StopArea distance (primary)",
    "dist_min_m": "minimum StopArea distance",
    "dist_mean_m": "unweighted mean StopArea distance",
}


def kruskal_epsilon_squared(values: pd.Series, groups: pd.Series) -> dict:
    frame = pd.DataFrame({"value": values, "group": groups}).dropna()
    samples = [g["value"].to_numpy() for _, g in frame.groupby("group", observed=True)]
    h_stat, p_value = stats.kruskal(*samples)
    n = len(frame)
    k = len(samples)
    epsilon2 = (h_stat - k + 1) / (n - k) if n > k else np.nan
    return {
        "n": int(n),
        "k": int(k),
        "kruskal_H": float(h_stat),
        "p_value": float(p_value),
        "epsilon_squared": float(epsilon2),
    }


def cramers_v(table: pd.DataFrame) -> tuple[float, float, float]:
    chi2, p_value, _, _ = chi2_contingency(table.to_numpy())
    n = table.to_numpy().sum()
    denominator = min(table.shape[0] - 1, table.shape[1] - 1)
    v = math.sqrt(chi2 / (n * denominator)) if denominator > 0 and n > 0 else np.nan
    return float(v), float(chi2), float(p_value)


def run_test_a(linked: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Distance to nearest rail node by bus cluster, plus centrality control."""
    rows = []
    for column, label in DISTANCE_COLUMNS.items():
        result = kruskal_epsilon_squared(linked[column], linked["bus_cluster"])
        result.update({"distance_measure": column, "description": label})
        rows.append(result)

    centrality = kruskal_epsilon_squared(
        linked["dist_centre_wmean_m"], linked["bus_cluster"]
    )
    centrality.update(
        {
            "distance_measure": "dist_centre_wmean_m",
            "description": "CONTROL: activity-weighted distance to Charing Cross",
        }
    )
    rows.append(centrality)
    tests = pd.DataFrame(rows)[
        ["distance_measure", "description", "n", "k", "kruskal_H", "p_value", "epsilon_squared"]
    ]

    per_cluster = (
        linked.groupby("bus_cluster_name", observed=True)
        .agg(
            n=("lsoa", "size"),
            dist_rail_median_m=("dist_wmean_m", "median"),
            dist_rail_q25_m=("dist_wmean_m", lambda s: s.quantile(0.25)),
            dist_rail_q75_m=("dist_wmean_m", lambda s: s.quantile(0.75)),
            dist_rail_min_median_m=("dist_min_m", "median"),
            dist_centre_median_m=("dist_centre_wmean_m", "median"),
        )
        .round(1)
        .sort_values("dist_rail_median_m")
        .reset_index()
    )

    rho, rho_p = stats.spearmanr(linked["dist_wmean_m"], linked["dist_centre_wmean_m"])
    confound = {
        "spearman_rho_rail_vs_centre": float(rho),
        "spearman_p": float(rho_p),
        "epsilon2_rail_distance": float(
            tests.loc[tests["distance_measure"] == "dist_wmean_m", "epsilon_squared"].iloc[0]
        ),
        "epsilon2_centre_distance": float(
            tests.loc[tests["distance_measure"] == "dist_centre_wmean_m", "epsilon_squared"].iloc[0]
        ),
    }
    return tests, per_cluster, confound


def station_permutation_test(
    frame: pd.DataFrame, rail_labels: pd.DataFrame, n_permutations: int, seed: int
) -> dict:
    """Permute cluster labels across stations, not across bus LSOAs.

    Shuffling the 3,372 LSOA-level labels would destroy the replication
    structure and produce an absurdly small p-value. Shuffling the station
    labels and rebuilding the table keeps every LSOA attached to the same
    station, so the null is "this station could have had any cluster label",
    which is the question actually being asked.
    """
    observed_table = pd.crosstab(frame["bus_cluster"], frame["nearest_rail_cluster"])
    observed_v, chi2, chi2_p = cramers_v(observed_table)

    rng = np.random.default_rng(seed)
    nlcs = rail_labels["NLC"].to_numpy()
    clusters = rail_labels["cluster"].to_numpy()
    assigned = frame["nearest_rail_nlc"].to_numpy()
    bus = frame["bus_cluster"].to_numpy()

    position = pd.Series(np.arange(len(nlcs)), index=nlcs)
    index_of = position.reindex(assigned).to_numpy()

    count = 0
    null_values = np.empty(n_permutations, dtype=float)
    for i in range(n_permutations):
        permuted = rng.permutation(clusters)
        table = pd.crosstab(bus, permuted[index_of])
        value, _, _ = cramers_v(table)
        null_values[i] = value
        if value >= observed_v:
            count += 1

    return {
        "n_lsoas": int(len(frame)),
        "n_stations_used": int(frame["nearest_rail_nlc"].nunique()),
        "cramers_v": observed_v,
        "chi_square": chi2,
        "naive_chi2_p": chi2_p,
        "permutation_p": float((count + 1) / (n_permutations + 1)),
        "null_v_mean": float(null_values.mean()),
        "null_v_p95": float(np.quantile(null_values, 0.95)),
        "n_permutations": int(n_permutations),
    }


def run_test_b(linked: pd.DataFrame, rail_labels: pd.DataFrame, radius: int) -> dict:
    within = linked.loc[linked[f"within_{radius}m"]].copy()
    result = station_permutation_test(
        within, rail_labels, C.N_PERMUTATIONS, C.RANDOM_SEED
    )
    result["radius_m"] = radius
    result["coverage"] = float(len(within) / len(linked))

    table = pd.crosstab(
        within["bus_cluster_name"], within["nearest_rail_cluster_name"]
    )
    row_pct = (table.div(table.sum(axis=1), axis=0) * 100).round(1)

    # Same association computed inside distance-to-centre terciles. If V
    # collapses here but is high overall, the overall number was largely a
    # shared centre-periphery gradient rather than a bus-rail relationship.
    within["centre_tercile"] = pd.qcut(
        within["dist_centre_wmean_m"], 3, labels=["inner", "middle", "outer"]
    )
    stratified = []
    for tercile, group in within.groupby("centre_tercile", observed=True):
        sub = pd.crosstab(group["bus_cluster"], group["nearest_rail_cluster"])
        if sub.shape[0] < 2 or sub.shape[1] < 2:
            continue
        value, _, _ = cramers_v(sub)
        stratified.append(
            {"centre_tercile": str(tercile), "n": int(len(group)), "cramers_v": round(value, 4)}
        )
    result["stratified_by_centrality"] = stratified
    return result, table, row_pct


def main() -> None:
    linked = pd.read_csv(C.DATA_OUT / "bus_rail_link_table.csv")
    rail_labels = pd.read_csv(C.RAIL_UNIT_METRICS)[["NLC", "cluster"]]
    rail_labels["NLC"] = rail_labels["NLC"].astype(str).str.strip()
    linked["nearest_rail_nlc"] = linked["nearest_rail_nlc"].astype(str).str.strip()

    print("=" * 72)
    print("TEST A -- distance to nearest rail station by bus cluster")
    print("=" * 72)
    tests_a, per_cluster, confound = run_test_a(linked)
    print(per_cluster.to_string(index=False))
    print()
    print(tests_a.round(4).to_string(index=False))
    print()
    print(
        f"Centrality check: Spearman rho(rail distance, centre distance) = "
        f"{confound['spearman_rho_rail_vs_centre']:.3f}; "
        f"epsilon2 rail={confound['epsilon2_rail_distance']:.3f} vs "
        f"centre={confound['epsilon2_centre_distance']:.3f}"
    )

    tests_a.to_csv(C.DATA_OUT / "test_a_distance_tests.csv", index=False)
    per_cluster.to_csv(C.DATA_OUT / "test_a_distance_by_cluster.csv", index=False)

    print()
    print("=" * 72)
    print("TEST B -- bus cluster x nearest rail cluster co-occurrence")
    print("=" * 72)
    results_b = {}
    for radius in (C.CATCHMENT_PRIMARY_M, C.CATCHMENT_SENSITIVITY_M):
        tag = "primary" if radius == C.CATCHMENT_PRIMARY_M else "sensitivity"
        result, table, row_pct = run_test_b(linked, rail_labels, radius)
        results_b[f"{radius}m"] = result

        print(f"\n--- {radius} m ({tag}) ---")
        print(
            f"n={result['n_lsoas']} LSOAs ({result['coverage']:.1%} of fitted), "
            f"{result['n_stations_used']} distinct stations"
        )
        print(f"Cramer's V = {result['cramers_v']:.3f}")
        print(
            f"  naive chi-square p = {result['naive_chi2_p']:.3g}  "
            f"<- INVALID (pseudo-replication), shown only for contrast"
        )
        print(
            f"  station-level permutation p = {result['permutation_p']:.4f}  "
            f"(null V mean {result['null_v_mean']:.3f}, 95th pct {result['null_v_p95']:.3f})"
        )
        print("  within centrality terciles: " + ", ".join(
            f"{s['centre_tercile']} V={s['cramers_v']:.3f} (n={s['n']})"
            for s in result["stratified_by_centrality"]
        ))
        print("\n  Row % (each bus cluster's split across rail clusters):")
        print(row_pct.to_string())

        table.to_csv(C.DATA_OUT / f"test_b_contingency_{radius}m.csv")
        row_pct.to_csv(C.DATA_OUT / f"test_b_row_pct_{radius}m.csv")

    payload = {"test_a_centrality_check": confound, "test_b": results_b}
    with open(C.DATA_OUT / "test_results.json", "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"\nWrote {C.DATA_OUT / 'test_results.json'}")


if __name__ == "__main__":
    main()
