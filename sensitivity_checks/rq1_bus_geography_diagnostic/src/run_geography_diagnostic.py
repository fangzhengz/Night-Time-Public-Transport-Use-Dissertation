"""Test whether the fixed RQ1 bus cluster labels carry geographic structure.

Answers the question raised by Howard Wong (17 July 2026 supervisor meeting):
the bus K=3 LSOA map places central London (Westminster, Camden) and outer
suburbs (Kingston, Richmond Park) in the same cluster -- is that a real
feature of the data, or an artifact of K choice / classification noise?

Three checks, run for K in {3,4,5,6}:
  1. eta^2 of distance-to-Charing-Cross explained by cluster membership
     (one-way ANOVA style variance decomposition), plus a non-parametric
     Kruskal-Wallis / epsilon^2 cross-check.
  2. Does GMM assignment confidence (max_posterior) vary with location or
     activity volume? If mixing were driven by uncertain classification,
     confidence should be lower for "mixed" units.
  3. (K=3, the adopted solution) confidence broken down by activity tertile.

Centrality reference matches the existing RQ2 centrality control exactly:
Charing Cross, BNG (530134, 180379) -- see
`rq2test analysis/src/run_direct_metrics_analysis.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

LABELS_DIR = FYP / "cluster_clean_version_fullweek" / "outputs" / "labels"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
BUS_UNIT_METRICS = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

CHARING_CROSS_E = 530134.0
CHARING_CROSS_N = 180379.0
K_VALUES = [3, 4, 5, 6]


def load_lsoa_coords() -> pd.DataFrame:
    with open(LSOA_GEOJSON, encoding="utf-8") as f:
        geo = json.load(f)
    rows = []
    for feat in geo["features"]:
        props = feat["properties"]
        rows.append(
            {
                "lsoa": props["LSOA21CD"],
                "bng_e": float(props["BNG_E"]),
                "bng_n": float(props["BNG_N"]),
            }
        )
    coords = pd.DataFrame(rows)
    coords["distance_to_centre"] = np.sqrt(
        (coords["bng_e"] - CHARING_CROSS_E) ** 2
        + (coords["bng_n"] - CHARING_CROSS_N) ** 2
    )
    return coords


def eta_squared_oneway(values: pd.Series, groups: pd.Series) -> float:
    grand_mean = values.mean()
    ss_total = ((values - grand_mean) ** 2).sum()
    ss_between = sum(
        len(g) * (g.mean() - grand_mean) ** 2 for _, g in values.groupby(groups)
    )
    return float(ss_between / ss_total) if ss_total > 0 else float("nan")


def kruskal_epsilon_squared(values: pd.Series, groups: pd.Series) -> tuple[float, float, float]:
    samples = [g.values for _, g in values.groupby(groups)]
    h_stat, p_value = stats.kruskal(*samples)
    n = len(values)
    k = len(samples)
    epsilon_sq = (h_stat - k + 1) / (n - k) if n > k else float("nan")
    return float(h_stat), float(p_value), float(epsilon_sq)


def run_distance_by_k(coords: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in K_VALUES:
        labels = pd.read_csv(LABELS_DIR / f"bus_k{k}_labels.csv").rename(columns={"unit": "lsoa"})
        labels["lsoa"] = labels["lsoa"].astype(str)
        merged = labels.merge(coords, on="lsoa", how="inner", validate="one_to_one")
        missing = len(labels) - len(merged)

        eta2 = eta_squared_oneway(merged["distance_to_centre"], merged["cluster"])
        h_stat, p_value, epsilon2 = kruskal_epsilon_squared(
            merged["distance_to_centre"], merged["cluster"]
        )
        rows.append(
            {
                "k": k,
                "n_units": len(merged),
                "n_missing_coords": missing,
                "eta_squared_distance": eta2,
                "kruskal_H": h_stat,
                "kruskal_p": p_value,
                "kruskal_epsilon_squared": epsilon2,
            }
        )
    return pd.DataFrame(rows)


def run_confidence_checks() -> tuple[pd.DataFrame, pd.DataFrame]:
    coords = load_lsoa_coords()
    metrics = pd.read_csv(BUS_UNIT_METRICS)
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    merged = metrics.merge(coords, on="lsoa", how="inner", validate="one_to_one")

    corr_rows = [
        {
            "pair": "max_posterior vs distance_to_centre",
            "spearman_r": float(stats.spearmanr(merged["max_posterior"], merged["distance_to_centre"]).statistic),
        },
        {
            "pair": "max_posterior vs total_activity",
            "spearman_r": float(stats.spearmanr(merged["max_posterior"], merged["total_activity"]).statistic),
        },
        {
            "pair": "entropy vs distance_to_centre",
            "spearman_r": float(stats.spearmanr(merged["entropy"], merged["distance_to_centre"]).statistic),
        },
    ]
    corr_df = pd.DataFrame(corr_rows)

    tertile_df = (
        merged.groupby("volume_band")["max_posterior"]
        .agg(["median", "mean", "count"])
        .reindex(["low", "medium", "high"])
        .reset_index()
    )
    return corr_df, tertile_df


def main() -> None:
    coords = load_lsoa_coords()
    distance_by_k = run_distance_by_k(coords)
    distance_by_k.to_csv(DATA / "bus_distance_eta2_by_k.csv", index=False)

    confidence_corr, confidence_tertile = run_confidence_checks()
    confidence_corr.to_csv(DATA / "bus_confidence_correlations.csv", index=False)
    confidence_tertile.to_csv(DATA / "bus_confidence_by_volume_tertile.csv", index=False)

    lines = [
        "# Bus cluster geography diagnostic",
        "",
        "Reproduces (as a saved, citable script) the 17 July 2026 ad-hoc check of",
        "whether the bus K=3 LSOA cluster map's inner/outer London mixing is a real",
        "feature of the data or an artifact of K choice / classification noise.",
        "Centrality reference: Charing Cross, BNG (530134, 180379) -- same point",
        "used by the RQ2 centrality-adjusted LNWC/IMD tests.",
        "",
        "## 1. Does distance-to-centre organise cluster membership, and does raising K help?",
        "",
        distance_by_k.to_markdown(index=False),
        "",
        "## 2. Is the mixing caused by uncertain (low-confidence) classification?",
        "",
        confidence_corr.to_markdown(index=False),
        "",
        confidence_tertile.to_markdown(index=False),
        "",
        "## Reading",
        "",
        "- If eta_squared_distance stays low and roughly flat across K=3..6, raising K",
        "  does not resolve the inner/outer mixing -- it is not a coarse-K artifact.",
        "- If max_posterior correlations with distance/activity are close to zero and",
        "  medians are high across all volume tertiles, the mixing is not driven by",
        "  low-confidence/uncertain assignment.",
    ]
    (REPORT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("Done. See outputs/data and outputs/report/RESULTS_SUMMARY.md")
    print(distance_by_k)
    print(confidence_corr)
    print(confidence_tertile)


if __name__ == "__main__":
    main()
