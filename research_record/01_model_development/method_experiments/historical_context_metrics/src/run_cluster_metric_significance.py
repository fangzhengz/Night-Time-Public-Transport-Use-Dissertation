"""Does the RQ1 shape-only cluster label explain its own continuous profile metrics?

Section 6.2 of the RQ1/RQ2 write-up hypothesises that LNWC associates weakly
with the raw bus shape-cluster label (Cramer's V = 0.215) but more strongly
with the continuous profile metrics (e.g. total_activity epsilon^2 = 0.149)
because LNWC is an intensity/business-mix measure while the cluster label is
shape-only by construction (direction-wise normalisation removes volume and
balance information).

That hypothesis is only useful if the cluster label is itself internally
meaningful for the very metrics it is supposed to be a shape-only sibling of.
This was never directly tested: metric ~ cluster (does cluster membership
explain variance in total_activity, direction_balance, timing shares?) is
missing from both rq1_context_metrics_analysis and rq2test analysis.

Run for both modes so the comparison is symmetric: if bus's metric~cluster
effect sizes are much smaller than rail's, that itself is informative about
why bus's external validation (vs LNWC) reads weaker than rail's.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

MODE_METRICS = {
    "bus": [
        "log_total_activity",
        "direction_balance",
        "post_midnight_share",
        "deep_night_share",
        "post_midnight_persistence",
        "weekend_ratio",
    ],
    "rail": [
        "log_total_activity",
        "direction_balance",
        "midnight_share_common_window",
        "night_tube_extension_share",
        "common_window_persistence",
        "weekend_common_ratio",
    ],
}


def kruskal_epsilon_squared(values: pd.Series, groups: pd.Series) -> tuple[float, float, float, int, int]:
    frame = pd.DataFrame({"value": values, "group": groups}).dropna()
    samples = [g["value"].values for _, g in frame.groupby("group")]
    h_stat, p_value = stats.kruskal(*samples)
    n = len(frame)
    k = len(samples)
    epsilon_sq = (h_stat - k + 1) / (n - k) if n > k else float("nan")
    return float(h_stat), float(p_value), float(epsilon_sq), n, k


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    ranked = p_values.rank(method="first")
    n = len(p_values)
    adjusted = p_values * n / ranked
    order = p_values.sort_values().index
    running_min = adjusted.loc[order][::-1].cummin()[::-1]
    return running_min.reindex(p_values.index).clip(upper=1.0)


def main() -> None:
    all_rows = []
    for mode, metrics in MODE_METRICS.items():
        frame = pd.read_csv(DATA / f"{mode}_unit_metrics.csv")
        for metric in metrics:
            h_stat, p_value, epsilon2, n, k = kruskal_epsilon_squared(
                frame[metric], frame["cluster"]
            )
            all_rows.append(
                {
                    "mode": mode,
                    "metric": metric,
                    "n": n,
                    "n_clusters": k,
                    "kruskal_H": h_stat,
                    "kruskal_p": p_value,
                    "epsilon_squared": epsilon2,
                }
            )
    result = pd.DataFrame(all_rows)
    result["p_bh"] = result.groupby("mode")["kruskal_p"].transform(benjamini_hochberg)
    result.to_csv(DATA / "cluster_metric_significance.csv", index=False)

    for mode in MODE_METRICS:
        result.loc[result["mode"] == mode].to_csv(
            DATA / f"{mode}_cluster_metric_significance.csv", index=False
        )

    lines = [
        "# Does the RQ1 cluster label explain its own continuous profile metrics?",
        "",
        "metric ~ cluster, Kruskal-Wallis + epsilon-squared, Benjamini-Hochberg",
        "corrected within mode. Compare against the external-validation effect",
        "sizes already reported: bus cluster x LNWC Cramer's V = 0.215 (weak),",
        "rail cluster x LNWC Cramer's V = 0.443 (moderate-strong).",
        "",
        result.to_markdown(index=False),
        "",
        "## Reading",
        "",
        "- High epsilon_squared here means cluster membership explains a large",
        "  share of that metric's own variance -- the clusters are internally",
        "  coherent groupings for that dimension, even if their external LNWC",
        "  association is weak (i.e. weak-vs-LNWC is a statement about what the",
        "  shape-only vector represents, not evidence the partition itself is",
        "  incoherent).",
        "- Low epsilon_squared across the board for a mode would be a genuine red",
        "  flag: it would mean the cluster label barely organises even the metrics",
        "  it is conceptually closest to, which a shape-vs-geography argument",
        "  alone could not explain away.",
    ]
    (REPORT / "CLUSTER_METRIC_SIGNIFICANCE.md").write_text("\n".join(lines), encoding="utf-8")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
