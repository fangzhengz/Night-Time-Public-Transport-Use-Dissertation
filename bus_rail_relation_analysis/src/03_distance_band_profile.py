"""Test A2 -- cluster composition by distance band. The reverse conditional.

WHY THIS EXISTS
Test A (02_run_tests.py) asks "given a bus cluster, how far is it from rail?"
and answers with Kruskal-Wallis epsilon-squared = 0.099. That is a correct
number and a bad instrument for the question actually being asked, for two
reasons the user spotted by looking at the overlay map:

1. Wrong direction. The eye reads the map as "near a station, what fraction of
   LSOAs are the high-flow night-persistent cluster?" -- the reverse
   conditional. Epsilon-squared cannot express that.
2. Wrong shape. The effect turns out to be almost entirely a 0-400 m
   phenomenon: by 400-800 m the composition is already back to baseline. A
   rank test spread over a 0-10 km distribution averages that sharp local step
   away to nearly nothing.

So this script reports cluster composition by distance band instead, both
overall and stratified by distance-to-centre tercile. The stratified version is
the load-bearing one: it is what shows the 0-400 m enrichment is not just the
centre-periphery gradient in disguise.

Note the chi-square here IS valid, unlike in Test B. Every LSOA contributes one
independent row -- nothing is borrowed from a shared station label, so the
pseudo-replication problem that invalidates Test B's naive chi-square does not
arise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

import config as C

BAND_EDGES = [0, 400, 800, 1200, 2000, np.inf]
BAND_LABELS = ["0-400m", "400-800m", "800-1200m", "1200-2000m", ">2000m"]
MIN_CELL = 25  # below this a band x ring cell is too thin to report a share for


def add_bands(linked: pd.DataFrame) -> pd.DataFrame:
    out = linked.copy()
    # dist_min_m -- "the closest any bus stop in this LSOA gets to rail" -- is
    # the right measure for a proximity/access question. The activity-weighted
    # mean used in Test A answers a different one.
    out["band"] = pd.cut(out["dist_min_m"], BAND_EDGES, labels=BAND_LABELS, right=False)
    out["ring"] = pd.qcut(
        out["dist_centre_wmean_m"], 3, labels=["inner", "middle", "outer"]
    )
    return out


def composition_table(frame: pd.DataFrame) -> pd.DataFrame:
    counts = pd.crosstab(frame["band"], frame["bus_cluster"]).reindex(
        index=BAND_LABELS, fill_value=0
    )
    shares = (counts.div(counts.sum(axis=1), axis=0) * 100).round(1)
    shares.columns = [C.BUS_CLUSTER_NAMES[c] for c in counts.columns]
    shares.insert(0, "n", counts.sum(axis=1).astype(int))
    return shares


def main() -> None:
    linked = add_bands(pd.read_csv(C.DATA_OUT / "bus_rail_link_table.csv"))
    baseline = linked["bus_cluster"].value_counts(normalize=True).sort_index() * 100

    print("=" * 74)
    print("TEST A2 -- bus cluster composition by distance-to-rail band")
    print("=" * 74)
    overall = composition_table(linked)
    print(overall.to_string())
    print("\nWhole-sample baseline: " + ", ".join(
        f"{C.BUS_CLUSTER_NAMES[c]} {v:.1f}%" for c, v in baseline.items()
    ))

    counts = pd.crosstab(linked["band"], linked["bus_cluster"])
    chi2, p_value, dof, _ = chi2_contingency(counts.to_numpy())
    print(f"\nchi-square = {chi2:.1f}, df = {dof}, p = {p_value:.3g} "
          f"(valid here: one independent row per LSOA, no borrowed labels)")
    overall.to_csv(C.DATA_OUT / "test_a2_composition_by_band.csv")
    # Raw counts as well as shares -- the report needs these to quote the same
    # chi-square this script printed. Reconstructing counts from the rounded
    # percentages gave a slightly different value (345.7 vs 346.1).
    counts_out = counts.copy()
    counts_out.columns = [C.BUS_CLUSTER_NAMES[c] for c in counts.columns]
    counts_out.to_csv(C.DATA_OUT / "test_a2_counts_by_band.csv")

    # --- stratified by centrality: the load-bearing check ---
    print("\n" + "=" * 74)
    # Resolve the night-persistent cluster from its PROFILE, never from its id
    # (GMM component numbering is arbitrary across refits, so the former
    # hardcoded `== 1` kept running and kept printing a plausible percentage
    # for whatever cluster happened to be numbered 1). Raises if the top two
    # clusters are too close for the label to be well defined.
    night_cluster, night_ranking = C.resolve_night_persistent_cluster(
        pd.read_csv(C.BUS_UNIT_METRICS)
    )
    print(f"Night-persistent bus cluster resolved to C{night_cluster} "
          f"({C.NIGHT_PERSISTENT_METRIC} means: {night_ranking.round(4).to_dict()})")
    print("Stratified by distance-to-centre tercile")
    print("=" * 74)
    rows = []
    for ring, group in linked.groupby("ring", observed=True):
        ring_baseline = (group["bus_cluster"] == night_cluster).mean() * 100
        sub_counts = pd.crosstab(group["band"], group["bus_cluster"])
        sub_chi2, sub_p, _, _ = chi2_contingency(
            sub_counts.loc[sub_counts.sum(axis=1) >= MIN_CELL].to_numpy()
        )
        print(f"\n{ring} ring -- C{night_cluster} baseline {ring_baseline:.1f}%, "
              f"chi-square p = {sub_p:.3g}")
        for band in BAND_LABELS:
            cell = group[group["band"] == band]
            if len(cell) < MIN_CELL:
                print(f"   {band:>12}: too thin to report (n={len(cell)})")
                continue
            share = (cell["bus_cluster"] == night_cluster).mean() * 100
            print(f"   {band:>12}: C{night_cluster} {share:5.1f}%  (n={len(cell):>4}, "
                  f"{share - ring_baseline:+.1f}pp vs ring baseline)")
            rows.append({
                "ring": str(ring), "band": band, "n": int(len(cell)),
                "night_cluster_share_pct": round(share, 1),
                "ring_night_cluster_baseline_pct": round(ring_baseline, 1),
                "difference_pp": round(share - ring_baseline, 1),
                "ratio_to_ring_baseline": round(share / ring_baseline, 2)
                if ring_baseline else np.nan,
            })
    stratified = pd.DataFrame(rows)
    stratified.to_csv(C.DATA_OUT / "test_a2_c1_share_by_band_and_ring.csv", index=False)

    # --- figure ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    x = np.arange(len(BAND_LABELS))
    bottom = np.zeros(len(BAND_LABELS))
    for cluster in range(C.BUS_K):
        values = overall[C.BUS_CLUSTER_NAMES[cluster]].to_numpy(dtype=float)
        ax.bar(x, values, bottom=bottom, color=C.CLUSTER_COLOURS[cluster],
               label=C.BUS_CLUSTER_NAMES[cluster], width=0.75)
        bottom += values
    ax.set_xticks(x)
    ax.set_xticklabels(BAND_LABELS, fontsize=8)
    ax.set_ylabel("% of LSOAs in band")
    ax.set_ylim(0, 100)
    ax.set_title("Cluster composition by distance to nearest rail station", fontsize=10)
    ax.legend(fontsize=7, loc="lower right", framealpha=0.9)

    ax = axes[1]
    for ring, marker in zip(["inner", "middle", "outer"], ["o", "s", "^"]):
        sub = stratified[stratified["ring"] == ring]
        positions = [BAND_LABELS.index(b) for b in sub["band"]]
        ax.plot(positions, sub["night_cluster_share_pct"], marker=marker, label=f"{ring} ring")
        ax.axhline(sub["ring_night_cluster_baseline_pct"].iloc[0], linestyle=":", linewidth=0.8,
                   color=ax.get_lines()[-1].get_color())
    ax.set_xticks(np.arange(len(BAND_LABELS)))
    ax.set_xticklabels(BAND_LABELS, fontsize=8)
    ax.set_ylabel(f"% of LSOAs that are {C.BUS_CLUSTER_NAMES[night_cluster]}")
    ax.set_title(f"{C.BUS_CLUSTER_NAMES[night_cluster].split(' ', 1)[0]} share by band, "
                 "within centrality terciles\n(dotted = that ring's own baseline)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    path = C.FIGURE_OUT / "cluster_composition_by_distance_band.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
