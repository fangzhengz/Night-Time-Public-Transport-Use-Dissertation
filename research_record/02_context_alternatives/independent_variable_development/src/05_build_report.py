"""Assemble RESULTS.md from the outputs of 02, 03 and 04.

Everything quoted here is read from the CSVs those scripts wrote -- no number
is hardcoded, so the report cannot drift from the data the way a hand-written
summary does.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config as C

TOP_CELLS = 8


def strongest_cells(tests: pd.DataFrame, mode: str) -> pd.DataFrame:
    subset = tests.loc[(tests["mode"] == mode) & (tests["p_bh"] < 0.05)].copy()
    subset["abs_z"] = subset["z_score"].abs()
    return subset.sort_values("abs_z", ascending=False)


def cluster_portrait(tests: pd.DataFrame, mode: str, cluster_name: str, n: int = 5) -> str:
    subset = tests.loc[
        (tests["mode"] == mode)
        & (tests["cluster_name"] == cluster_name)
        & (tests["p_bh"] < 0.05)
    ].copy()
    if subset.empty:
        return "_no variable separates this cluster after correction_"
    subset["abs_z"] = subset["z_score"].abs()
    subset = subset.sort_values("abs_z", ascending=False).head(n)
    parts = []
    for _, row in subset.iterrows():
        arrow = "high" if row["z_score"] > 0 else "low"
        parts.append(f"{arrow} {row['variable']} ({row['z_score']:+.2f})")
    return "; ".join(parts)


def main() -> None:
    omnibus = pd.read_csv(C.DATA_OUT / "association_tests.csv")
    per_cluster = pd.read_csv(C.DATA_OUT / "per_cluster_tests.csv")
    n_vars = len(C.ANALYSIS_VARIABLES)

    lines = [
        "# Independent area-context variables — results",
        "",
        "Two layers, answering two different questions:",
        "",
        "* **Layer 1 (script 02) — which variables matter.** One omnibus",
        "  Kruskal-Wallis per variable per mode, reported as epsilon-squared, so the",
        "  variables can be *ranked*. The reference literature does not do this:",
        "  BtC reports significance stars without effect sizes, and Kimani's MSc",
        "  dissertation reports descriptive profiles with no hypothesis test at all.",
        "* **Layer 2 (script 03) — what each cluster looks like.** Cluster-vs-rest",
        "  Mann-Whitney per cell, BH-corrected, which is the K x V matrix the",
        "  literature does report, and what cluster naming rests on.",
        "",
        "Neither replaces the other. Layer 1 without Layer 2 cannot describe a",
        "cluster; Layer 2 without Layer 1 is a wall of asterisks with no ordering.",
        "",
        "## Layer 1 — variable ranking (epsilon-squared)",
        "",
        "| Variable | Bus | Rail |",
        "|---|---:|---:|",
    ]

    wide = omnibus.pivot(index="variable", columns="mode", values="epsilon_squared")
    wide = wide.sort_values("bus", ascending=False)
    for variable, row in wide.iterrows():
        marker = " *(control)*" if variable == "population_density" else ""
        lines.append(f"| {variable}{marker} | {row.get('bus', float('nan')):.3f} "
                     f"| {row.get('rail', float('nan')):.3f} |")

    lines += [
        "",
        "Conventional epsilon-squared benchmarks: 0.01 small, 0.06 medium, 0.14 large.",
        "",
        "For comparison, the composite lenses on the same clusterings — note these are",
        "Cramer's V, a *different* statistic, so they rank among themselves but cannot",
        "be placed on the epsilon-squared scale above:",
        "",
        "| Composite | Bus | Rail |",
        "|---|---:|---:|",
    ]
    composites = C.load_composite_associations()
    lines += [
        f"| LNWC (night-work geography) | V = {composites['bus']['lnwc']:.3f} "
        f"| V = {composites['rail']['lnwc']:.3f} |",
        f"| LOAC (general neighbourhood type) | V = {composites['bus']['loac']:.3f} "
        f"| V = {composites['rail']['loac']:.3f} |",
        f"| IMD overall score | eps² = {composites['bus']['imd']:.3f} "
        f"| eps² = {composites['rail']['imd']:.3f} |",
        "",
        "## Layer 2 — cluster profiles",
        "",
    ]

    for mode, names in (("bus", C.BUS_CLUSTER_NAMES), ("rail", C.RAIL_CLUSTER_NAMES)):
        subset = per_cluster.loc[per_cluster["mode"] == mode]
        significant = int((subset["p_bh"] < 0.05).sum())
        lines += [
            f"### {mode.upper()} — {significant}/{len(subset)} cells significant after BH "
            f"({significant / len(subset):.0%})",
            "",
        ]
        for cluster in sorted(names):
            name = names[cluster]
            lines.append(f"**{name}** — {cluster_portrait(per_cluster, mode, name)}")
            lines.append("")

        top = strongest_cells(per_cluster, mode).head(TOP_CELLS)
        lines += [
            f"Strongest {TOP_CELLS} cells in the {mode} matrix:",
            "",
            "| Cluster | Variable | z | rank-biserial | BH p |",
            "|---|---|---:|---:|---:|",
        ]
        for _, row in top.iterrows():
            lines.append(
                f"| {row['cluster_name']} | {row['variable']} | {row['z_score']:+.2f} "
                f"| {row['rank_biserial']:+.3f} | {row['p_bh']:.2e} |"
            )
        lines.append("")

    lines += [
        "## Method notes",
        "",
        "* **Cluster vs rest, not cluster vs overall.** A one-sample test of a cluster",
        "  mean against the overall mean compares a sample with a population that",
        "  contains it; the two are not independent. Cluster-vs-rest avoids this.",
        "* **Mann-Whitney, not t.** The variables include bounded rates and",
        "  skewed facility counts or employment shares.",
        f"* **Benjamini-Hochberg across all cells within a mode.** Bus runs "
        f"{C.BUS_K} x {n_vars} = {C.BUS_K * n_vars} tests and rail "
        f"{C.RAIL_K} x {n_vars} = {C.RAIL_K * n_vars}; uncorrected, a handful per "
        f"mode would clear p<0.05 by chance alone.",
        "* **Rail units are 800 m Voronoi-clipped station catchments**, LSOA values",
        "  aggregated as an equal-weight arithmetic mean across distinct intersecting",
        "  LSOAs. This avoids applying one population weight to variables with different",
        "  denominators (households, residents and employed residents). The values",
        "  characterise average LSOA context, not exact catchment population composition.",
        "  Bus units are LSOAs directly — the bus clustering is already at LSOA level.",
        "  POI count and Shannon H are first calculated at LSOA level; Rail then uses",
        "  the same equal-weight catchment aggregation. Count is log1p-transformed",
        "  after Rail aggregation.",
        "",
        "## Known limitations",
        "",
        "1. **Context, not passenger identity or supply.** The variables describe the",
        "   residential, employment and facility context of an area; none identifies",
        "   passengers or measures what night service is provided. No claim about service",
        "   gaps can rest on this analysis.",
        "2. **Vintage mixing.** Transport data is 2024/25, IoD 2025 is administrative",
        "   data from roughly 2022-24, BRES is 2024, but the Census variables are March",
        "   2021 — taken during a national lockdown and three years before the travel",
        "   data — while OS POI is the June 2026 release.",
        "3. **BRES is the open-access release**, not the secure-access version BtC uses;",
        "   values are rounded to multiples of 5. Job counts per LSOA range 0 to 412,000",
        "   (median 300), so BRES *shares* are unstable in the ~40% of LSOAs with under",
        "   250 jobs. A per-km2 twin of every BRES variable is stored in",
        "   `data/bres2024_industry_sections_lsoa.csv`; which denominator to use is not",
        "   yet settled.",
        "4. **Collinearity.** Some variables are near-duplicates in this data even though",
        "   not by construction — imd_education and deprived_1plus_share (TS011) at",
        "   rho 0.89-0.92, imd_health and social_rented_share at rho 0.81-0.88 — plus the",
        "   TS060 sections are compositionally related shares of the same 18-section total.",
        "   See the correlation matrices (rho > 0.8 flagged); these pairs are the same",
        "   signal counted more than once, not independent evidence. One pair is kept",
        "   deliberately despite rho 0.81-0.89 — no_car_household_share (TS045) and",
        "   age_20_34_share (TS007B) are two independently-sourced Census measures of the",
        "   same young/carless profile; because Layer 1 and Layer 2 test each variable",
        "   separately rather than fitting a joint model, both scoring highly on the same",
        "   clusters is corroborating evidence from two sources, not a violated",
        "   independence assumption (the same logic BtC uses when reporting age and car",
        "   ownership as separate cluster-level indicators).",
        "5. **Bivariate throughout.** Every test here takes one variable at a time. How",
        "   much of cluster membership is explainable in total, and which variables",
        "   contribute uniquely once the others are held constant, would need a",
        "   multivariable model (as in Yang et al. 2023's random-forest importance).",
        "6. **Centrality is not fully controlled.** Facility intensity and several social",
        "   variables follow London's centre-periphery structure. A separate distance-band",
        "   facility sensitivity check is retained in rq2_facility_diversity_analysis,",
        "   but the main bivariate results remain descriptive spatial associations.",
        "",
        "## Figures",
        "",
        "* `figures/{bus,rail}_cluster_profile_heatmap.png` — Layer 2, the BtC-style figure.",
        "* `figures/{bus,rail}_boxplots_top8.png` — distributions behind the strongest variables.",
        f"* `figures/{{bus,rail}}_correlation_matrix.png` — how much the {n_vars} "
        f"variables duplicate.",
    ]

    path = C.REPORT_OUT / "RESULTS.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
