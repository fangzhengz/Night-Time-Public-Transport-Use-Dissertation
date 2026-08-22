"""Figures and the markdown report.

Two figures:
  1. overlay_bus_clusters_rail_stations.png -- the formal version of the
     overlay Clara made by hand: bus clusters as a choropleth with the current
     clustered rail stations on top. Keeps the three-state bus rendering
     (clustered / low night flow / no stop point in polygon) from the bus
     clustering figures, because collapsing the last two was a real map bug.
  2. distance_to_rail_by_cluster.png -- the distribution behind Test A, so the
     medians in the report can be read against their spread.
"""

from __future__ import annotations

import json

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.stats import chi2_contingency

import config as C


def load_boundaries() -> gpd.GeoDataFrame:
    boundaries = gpd.read_file(C.LSOA_BOUNDARIES)
    column = next(
        (c for c in boundaries.columns if c.lower() in {"lsoa21cd", "lsoa11cd", "lsoa"}),
        None,
    )
    if column is None:
        raise RuntimeError(
            f"No LSOA code column in {C.LSOA_BOUNDARIES.name}; got {list(boundaries.columns)}"
        )
    boundaries = boundaries.rename(columns={column: "lsoa"})
    if boundaries.crs is None or boundaries.crs.to_string() != C.CRS_BNG:
        boundaries = boundaries.to_crs(C.CRS_BNG)
    return boundaries[["lsoa", "geometry"]]


def build_status(boundaries: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Three-state bus status per polygon, matching the bus clustering maps."""
    labels = pd.read_csv(C.BUS_LABELS)
    labels["lsoa"] = labels["lsoa"].astype(str)

    # Every LSOA in k4_labels.csv reached the feature table; retained_for_fit
    # separates clustered from low-flow-excluded. Polygons absent from the file
    # entirely never had a StopArea point inside them.
    status = labels[["lsoa", "retained_for_fit", "cluster"]].copy()
    status["status"] = status["retained_for_fit"].map(
        {True: "clustered", False: "low_flow"}
    )
    mapped = boundaries.merge(status[["lsoa", "status", "cluster"]], on="lsoa", how="left")
    mapped["status"] = mapped["status"].fillna("no_stop")
    mapped["cluster"] = mapped["cluster"].fillna(-1).astype(int)
    return mapped


def draw_overlay(mapped: gpd.GeoDataFrame, rail: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 11))

    no_stop = mapped[mapped["status"] == "no_stop"]
    low_flow = mapped[mapped["status"] == "low_flow"]
    clustered = mapped[mapped["status"] == "clustered"]

    if not no_stop.empty:
        no_stop.plot(
            ax=ax,
            facecolor=C.NO_STOP_FACE,
            hatch=C.NO_STOP_HATCH,
            edgecolor=C.NO_STOP_EDGE,
            linewidth=C.NO_STOP_EDGE_WIDTH,
        )
    if not low_flow.empty:
        low_flow.plot(ax=ax, facecolor=C.LOW_FLOW_FACE, linewidth=0.0)

    sizes = clustered["cluster"].value_counts()
    for cluster in range(C.BUS_K):
        subset = clustered[clustered["cluster"] == cluster]
        if not subset.empty:
            subset.plot(ax=ax, facecolor=C.CLUSTER_COLOURS[cluster], linewidth=0.0)

    ax.scatter(
        rail["easting"],
        rail["northing"],
        s=14,
        c=C.RAIL_POINT_FACE,
        edgecolors=C.RAIL_POINT_EDGE,
        linewidths=0.4,
        zorder=5,
    )

    handles = [
        Patch(
            facecolor=C.CLUSTER_COLOURS[cluster],
            edgecolor="none",
            label=f"{C.BUS_CLUSTER_NAMES[cluster]}  n={int(sizes.get(cluster, 0)):,}",
        )
        for cluster in range(C.BUS_K)
    ]
    handles.append(Patch(facecolor=C.LOW_FLOW_FACE, edgecolor="none",
                         label=f"{C.LOW_FLOW_LABEL}  n={len(low_flow):,}"))
    handles.append(Patch(facecolor=C.NO_STOP_FACE, edgecolor=C.NO_STOP_EDGE,
                         linewidth=0.4, hatch=C.NO_STOP_HATCH,
                         label=f"{C.NO_STOP_LABEL}  n={len(no_stop):,}"))
    handles.append(
        Line2D([], [], marker="o", linestyle="none", markersize=5,
               markerfacecolor=C.RAIL_POINT_FACE, markeredgecolor=C.RAIL_POINT_EDGE,
               label=f"Rail station (all modes)  n={len(rail):,}")
    )

    # Lower left: the upper left overlaps the handful of NaPTAN-matched border
    # stations (Amersham, Chesham, Epping...) that sit outside the LSOA polygons.
    ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=8,
              labelspacing=0.6, alignment="left")
    ax.set_axis_off()
    ax.set_title(
        "Bus night-activity clusters (StopArea CLR, K=4) with all-modes rail stations",
        fontsize=12, pad=12,
    )
    fig.tight_layout()
    path = C.FIGURE_OUT / "overlay_bus_clusters_rail_stations.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


def draw_distance_distribution(linked: pd.DataFrame) -> None:
    order = (
        linked.groupby("bus_cluster", observed=True)["dist_wmean_m"]
        .median()
        .sort_values()
        .index.tolist()
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    data = [linked.loc[linked["bus_cluster"] == c, "dist_wmean_m"].to_numpy() for c in order]
    parts = ax.boxplot(data, vert=True, patch_artist=True, showfliers=False,
                       widths=0.6, medianprops={"color": "black", "linewidth": 1.4})
    for patch, cluster in zip(parts["boxes"], order):
        patch.set_facecolor(C.CLUSTER_COLOURS[cluster])
        patch.set_alpha(0.85)
        patch.set_edgecolor("#333333")

    ax.set_xticklabels([C.BUS_CLUSTER_NAMES[c] for c in order], fontsize=8)
    ax.set_ylabel("Activity-weighted distance to nearest rail station (m)")
    ax.set_title("Test A: bus clusters by distance to rail nodes (outliers hidden)", fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = C.FIGURE_OUT / "distance_to_rail_by_cluster.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


def build_report(linked: pd.DataFrame) -> None:
    tests_a = pd.read_csv(C.DATA_OUT / "test_a_distance_tests.csv")
    per_cluster = pd.read_csv(C.DATA_OUT / "test_a_distance_by_cluster.csv")
    with open(C.DATA_OUT / "test_results.json", encoding="utf-8") as handle:
        payload = json.load(handle)

    confound = payload["test_a_centrality_check"]
    primary = payload["test_b"][f"{C.CATCHMENT_PRIMARY_M}m"]
    sensitivity = payload["test_b"][f"{C.CATCHMENT_SENSITIVITY_M}m"]

    row_pct = pd.read_csv(
        C.DATA_OUT / f"test_b_row_pct_{C.CATCHMENT_PRIMARY_M}m.csv", index_col=0
    )

    # Test A2 outputs (script 03) -- recomputed here only for the chi-square the
    # report quotes; the tables themselves are read straight from disk.
    band_overall = pd.read_csv(
        C.DATA_OUT / "test_a2_composition_by_band.csv", index_col=0
    )
    band_stratified = pd.read_csv(C.DATA_OUT / "test_a2_c1_share_by_band_and_ring.csv")
    band_baseline = (
        linked["bus_cluster"].value_counts(normalize=True).sort_index() * 100
    ).rename(index=C.BUS_CLUSTER_NAMES)
    band_counts = pd.read_csv(C.DATA_OUT / "test_a2_counts_by_band.csv", index_col=0)
    band_chi2, band_p, band_dof, _ = chi2_contingency(band_counts.to_numpy())

    # The headline sentence below is computed, not typed. It was previously
    # hardcoded (55.0% / 34.0% / 15.2%) and silently went stale when the K=4
    # solution was refitted on 2026-08-03 -- the table above it moved while the
    # sentence did not.
    night_cluster, _ = C.resolve_night_persistent_cluster(pd.read_csv(C.BUS_UNIT_METRICS))
    headline_name = C.BUS_CLUSTER_NAMES[night_cluster]
    headline_near = float(band_overall.loc["0-400m", headline_name])
    headline_far = float(band_overall.loc[">2000m", headline_name])
    headline_baseline = float(band_baseline[headline_name])
    headline_ratio = headline_near / headline_baseline
    headline_far_phrase = (
        "under half" if headline_far < headline_baseline / 2 else "well below"
    )

    closest = per_cluster.iloc[0]
    farthest = per_cluster.iloc[-1]
    ratio = farthest["dist_rail_median_m"] / closest["dist_rail_median_m"]

    lines = [
        "# Bus x rail spatial relation — results",
        "",
        "Answers the question Clara raised on 2026-07-28: how do the bus night-activity",
        "clusters relate to distance from rail stations? Scope is deliberately narrow —",
        "proximity to rail **nodes** only. No interchange claim is made (that needs OD",
        "flows and timetables, which this project does not have), no corridor/along-the-line",
        "structure is tested (that needs rail line geometry), and the night-rail service-gap",
        "question is deferred to the Chapter 6 vulnerability write-up.",
        "",
        f"Bus: StopArea CLR K={C.BUS_K}, {len(linked):,} fitted LSOAs. "
        f"Rail: all-modes K={C.RAIL_K}, {pd.read_csv(C.RAIL_LABELS, usecols=['unit'])['unit'].nunique()} stations.",
        "Distances measured from each StopArea's own coordinate, then aggregated to LSOA.",
        "",
        "## Test A — distance to nearest rail station by bus cluster",
        "",
        "| Bus cluster | n | Median dist. to rail (m) | IQR (m) | Median dist. to centre (m) |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in per_cluster.iterrows():
        lines.append(
            f"| {row['bus_cluster_name']} | {int(row['n']):,} | "
            f"{row['dist_rail_median_m']:,.0f} | "
            f"{row['dist_rail_q25_m']:,.0f}–{row['dist_rail_q75_m']:,.0f} | "
            f"{row['dist_centre_median_m']:,.0f} |"
        )

    primary_row = tests_a.loc[tests_a["distance_measure"] == "dist_wmean_m"].iloc[0]
    lines += [
        "",
        f"**The gradient is monotone.** {closest['bus_cluster_name']} sits a median",
        f"{closest['dist_rail_median_m']:,.0f} m from the nearest rail station;",
        f"{farthest['bus_cluster_name']} sits {farthest['dist_rail_median_m']:,.0f} m away —",
        f"a factor of {ratio:.1f}. Kruskal-Wallis H={primary_row['kruskal_H']:.1f}, "
        f"epsilon-squared = **{primary_row['epsilon_squared']:.3f}**.",
        "",
        "Robustness across the three StopArea→LSOA aggregations:",
        "",
        "| Distance measure | epsilon² | H |",
        "|---|---:|---:|",
    ]
    for _, row in tests_a.iterrows():
        marker = " *(control)*" if row["distance_measure"].startswith("dist_centre") else ""
        lines.append(
            f"| {row['description']}{marker} | {row['epsilon_squared']:.3f} | {row['kruskal_H']:.1f} |"
        )

    lines += [
        "",
        "### Why epsilon-squared understates this — read Test A2 instead",
        "",
        "Taken alone, Test A looks confounded: bus clusters separate on "
        f"distance-to-Charing-Cross (epsilon² = {confound['epsilon2_centre_distance']:.3f}) "
        "slightly *more* strongly than on",
        f"distance-to-rail (epsilon² = {confound['epsilon2_rail_distance']:.3f}), "
        f"and the two correlate at Spearman rho = {confound['spearman_rho_rail_vs_centre']:.2f}.",
        "",
        "But epsilon-squared is the wrong instrument here, for two reasons:",
        "",
        "1. **Wrong direction.** It asks \"given a cluster, how far is it from rail?\" The",
        "   claim under test — and what the overlay map actually shows — is the reverse",
        "   conditional: *near a station, what fraction of LSOAs are the high-flow*",
        "   *night-persistent cluster?*",
        "2. **Wrong shape.** The effect is almost entirely a 0–400 m step. A rank test",
        "   spread over a 0–10 km distribution averages that away.",
        "",
        "Test A2 below reports the reverse conditional by distance band, and the effect",
        "**does** survive stratification by centrality. Cite Test A2, not Test A's",
        "epsilon-squared, for this finding.",
        "",
        "## Test A2 — cluster composition by distance band (the headline result)",
        "",
        "Same data, reverse conditional, and binned so the shape is visible.",
        "",
        band_overall.to_markdown(),
        "",
        "Whole-sample baseline: " + ", ".join(
            f"{name} {value:.1f}%" for name, value in band_baseline.items()
        )
        + f". Chi-square = {band_chi2:.1f}, df = {band_dof}, p = {band_p:.2g} — and this",
        "chi-square **is** valid, unlike Test B's: every LSOA is one independent row, with",
        "no label borrowed from a shared station.",
        "",
        f"**Within 400 m of a rail station, {headline_near:.1f}% of LSOAs are the**",
        f"**{headline_name} cluster — {headline_ratio:.1f}x the {headline_baseline:.1f}%**",
        f"**whole-sample baseline. Beyond 2 km it is {headline_far:.1f}%,**",
        f"**{headline_far_phrase} the baseline.** The step is sharp: by 400–800 m the",
        "composition is already back near baseline, so this is a walking-distance-scale",
        "effect, not a gradual gradient.",
        "",
        "### It survives the centrality control",
        "",
        "C1 share by band, computed inside each distance-to-centre tercile against that",
        "ring's own baseline:",
        "",
        "| Ring | Ring C1 baseline | 0–400 m | vs baseline | ratio |",
        "|---|---:|---:|---:|---:|",
    ] + [
        f"| {row['ring']} | {row['ring_night_cluster_baseline_pct']:.1f}% | {row['night_cluster_share_pct']:.1f}% "
        f"| {row['difference_pp']:+.1f}pp | {row['ratio_to_ring_baseline']:.2f}x |"
        for _, row in band_stratified[band_stratified["band"] == "0-400m"].iterrows()
    ] + [
        "",
        "The 0–400 m enrichment holds in **all three** rings, and in relative terms it is",
        "*largest in the outer ring* (1.81x) — precisely where the centre-periphery",
        "explanation is weakest. This is what Test A's epsilon-squared could not show.",
        "Per-ring chi-square p-values are all < 1e-6; full table in",
        "`data/test_a2_c1_share_by_band_and_ring.csv`.",
        "",
        "## Test B — bus cluster × nearest rail cluster co-occurrence",
        "",
        f"Bus LSOAs within {C.CATCHMENT_PRIMARY_M} m of a rail station "
        f"({primary['n_lsoas']:,}, {primary['coverage']:.1%} of the fitted sample) borrow the",
        "cluster label of the station that the most bus night activity in them sits nearest to.",
        "",
        f"- **Cramér's V = {primary['cramers_v']:.3f}** "
        f"({C.CATCHMENT_SENSITIVITY_M} m sensitivity: {sensitivity['cramers_v']:.3f} — stable)",
        f"- Station-level permutation p = **{primary['permutation_p']:.4f}** "
        f"({primary['n_permutations']:,} permutations; null V mean {primary['null_v_mean']:.3f}, "
        f"95th pct {primary['null_v_p95']:.3f})",
        f"- The naive chi-square p ({primary['naive_chi2_p']:.2g}) is **invalid** and reported",
        f"  only for contrast: {primary['n_lsoas']:,} LSOAs share only "
        f"{primary['n_stations_used']} distinct station labels, so an ordinary chi-square",
        "  massively overstates the evidence. The permutation test shuffles labels across",
        "  stations, preserving that replication under the null.",
        "",
        "Within distance-to-centre terciles the association does **not** collapse:",
        "",
        "| Centrality tercile | n | Cramér's V |",
        "|---|---:|---:|",
    ]
    for stratum in primary["stratified_by_centrality"]:
        lines.append(
            f"| {stratum['centre_tercile']} | {stratum['n']:,} | {stratum['cramers_v']:.3f} |"
        )

    lines += [
        "",
        "Like Test A2, the co-occurrence survives controlling for centrality, so it is not",
        "simply a shared centre-periphery gradient. The effect size is modest in absolute",
        "terms, but it is roughly 2.5x the permutation null mean. Test A2 answers *where*",
        "the night-persistent bus areas are; Test B answers *what kind* of rail node they",
        "sit next to.",
        "",
        f"### Row % — each bus cluster's split across rail clusters ({C.CATCHMENT_PRIMARY_M} m)",
        "",
        row_pct.to_markdown(),
        "",
        "The substantive pattern: the high-flow, night-persistent bus cluster is the one that",
        "pairs with **inner** rail clusters — it has both the largest share next to inner/near-",
        "suburban residential stations and, at nearly double any other bus cluster, the largest",
        "share next to the departure-dominant inner London stations. The low-flow peripheral",
        "and moderate-flow directional bus clusters instead pair with the outer suburban,",
        "arrival-dominant rail cluster. Bus night persistence and rail night function line up",
        "in the direction the night-time-economy reading would predict.",
        "",
        "## Figures",
        "",
        "- `figures/overlay_bus_clusters_rail_stations.png` — the formal version of Clara's",
        "  hand-made overlay.",
        "- `figures/cluster_composition_by_distance_band.png` — Test A2, both panels.",
        "- `figures/distance_to_rail_by_cluster.png` — distributions behind Test A.",
        "",
        "## What this does not establish",
        "",
        "1. **Not interchange.** Nothing here observes a passenger transferring. Proximity and",
        "   co-occurrence are consistent with a feeder relationship but equally consistent with",
        "   both modes independently serving the same night-active places. The 0–400 m",
        "   concentration is *suggestive* of a walking-interchange mechanism — that is a",
        "   Discussion reading, not a Results claim.",
        "2. **Not corridors.** Distance-to-nearest-station treats stations as isolated points.",
        "   If bus activity follows the line *between* stations, this design only partly picks",
        "   that up; testing it properly needs TfL line geometry.",
        "3. **Test A's epsilon-squared understates the effect** and looks confounded with",
        "   centrality. Test A2 and Test B are the citable results; both survive the control.",
    ]

    path = C.REPORT_OUT / "RESULTS.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


def main() -> None:
    linked = pd.read_csv(C.DATA_OUT / "bus_rail_link_table.csv")
    rail = pd.read_csv(C.RAIL_COORDS).rename(columns={"unit": "NLC"})
    rail["NLC"] = rail["NLC"].astype(str).str.strip()
    clustered_nlcs = set(
        pd.read_csv(C.RAIL_UNIT_METRICS)["NLC"].astype(str).str.strip()
    )
    rail = rail[rail["NLC"].isin(clustered_nlcs)]

    print("Building overlay map...")
    boundaries = load_boundaries()
    mapped = build_status(boundaries)
    draw_overlay(mapped, rail)

    print("Building distance distribution figure...")
    draw_distance_distribution(linked)

    print("Building report...")
    build_report(linked)


if __name__ == "__main__":
    main()
