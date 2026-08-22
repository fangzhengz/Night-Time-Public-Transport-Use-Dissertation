"""Per-cluster tests -- which cluster is high or low on which variable.

The companion to 02. Where 02 asks "does this variable separate the clusters at
all" (one omnibus Kruskal-Wallis per variable, giving an effect size that lets
variables be RANKED), this script asks "is THIS cluster unusually high or low on
THIS variable" -- the K x V matrix the reference literature reports, which is
what lets each cluster be characterised and named.

Neither replaces the other. Without 02 you have a wall of asterisks and no way
to say which factors matter most; without 03 you know a variable matters but
not which cluster is unusually high or low.

TEST CHOICE -- cluster vs REST, Mann-Whitney U, not a one-sample t-test.
BtC's heatmap marks each cluster x variable cell with significance stars. If
those come from comparing a cluster's mean against the overall mean, the test
is compromised: the cluster is PART of the overall, so the two samples are not
independent. Comparing the cluster against the remaining clusters fixes that.
Mann-Whitney rather than t also drops the normality assumption, which none of
these variables satisfies -- they include bounded rates and heavily skewed
counts or employment shares.

MULTIPLE COMPARISONS. K x V depends on the current formal variable set.
Benjamini-Hochberg is applied across all cells within a mode so the correction
automatically follows any documented variable-set change.

TWO EFFECT SIZES, because they answer different questions:
  * z_score -- (cluster mean - overall mean) / overall SD. Directly comparable
    to BtC's heatmap colouring, and what makes a cluster profile readable.
  * rank_biserial -- from the Mann-Whitney U, bounded [-1, 1], non-parametric,
    and unlike z it does not assume the spread is meaningful on a normal scale.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import config as C


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    ranked = p_values[order]
    m = len(p_values)
    adjusted = np.minimum.accumulate((ranked * m / np.arange(1, m + 1))[::-1])[::-1]
    out = np.empty(m, dtype=float)
    out[order] = np.clip(adjusted, 0, 1)
    return out


def cluster_vs_rest(values: pd.Series, in_cluster: pd.Series) -> dict:
    frame = pd.DataFrame({"v": values, "c": in_cluster}).dropna()
    inside = frame.loc[frame["c"], "v"].to_numpy()
    outside = frame.loc[~frame["c"], "v"].to_numpy()
    if len(inside) < 3 or len(outside) < 3:
        return {"n_in": len(inside), "n_out": len(outside), "u": np.nan,
                "p_value": np.nan, "rank_biserial": np.nan}
    u_stat, p_value = stats.mannwhitneyu(inside, outside, alternative="two-sided")
    # Rank-biserial: 0 = no separation, +1 = every in-cluster value exceeds
    # every out-cluster value, -1 = the reverse.
    rank_biserial = 2.0 * u_stat / (len(inside) * len(outside)) - 1.0
    return {"n_in": int(len(inside)), "n_out": int(len(outside)), "u": float(u_stat),
            "p_value": float(p_value), "rank_biserial": float(rank_biserial)}


def run_mode(frame: pd.DataFrame, variables: list[str], mode: str) -> pd.DataFrame:
    rows = []
    for variable in variables:
        series = frame[variable]
        overall_mean = series.mean()
        overall_sd = series.std()
        overall_median = series.median()
        for cluster, group in frame.groupby("cluster", observed=True):
            result = cluster_vs_rest(series, frame["cluster"].eq(cluster))
            result.update({
                "mode": mode,
                "cluster": int(cluster),
                "cluster_name": C.BUS_CLUSTER_NAMES.get(int(cluster))
                if mode == "bus" else C.RAIL_CLUSTER_NAMES.get(int(cluster)),
                "variable": variable,
                "cluster_mean": float(group[variable].mean()),
                "cluster_median": float(group[variable].median()),
                "overall_mean": float(overall_mean),
                "overall_median": float(overall_median),
                "z_score": float((group[variable].mean() - overall_mean) / overall_sd)
                if overall_sd and np.isfinite(overall_sd) else np.nan,
            })
            rows.append(result)

    tests = pd.DataFrame(rows)
    valid = tests["p_value"].notna()
    tests.loc[valid, "p_bh"] = benjamini_hochberg(tests.loc[valid, "p_value"].to_numpy())
    tests["stars"] = pd.cut(
        tests["p_bh"], [-0.01, 0.001, 0.01, 0.05, 1.0], labels=["***", "**", "*", ""]
    ).astype(str).replace("nan", "")
    return tests[[
        "mode", "cluster", "cluster_name", "variable", "n_in", "n_out",
        "cluster_mean", "overall_mean", "cluster_median", "overall_median",
        "z_score", "u", "rank_biserial", "p_value", "p_bh", "stars",
    ]]


def analysis_variables(frame: pd.DataFrame) -> list[str]:
    missing = [c for c in C.ANALYSIS_VARIABLES if c not in frame.columns]
    if missing:
        raise RuntimeError(f"ANALYSIS_VARIABLES not in the built table: {missing}")
    return list(C.ANALYSIS_VARIABLES)


def main() -> None:
    bus = pd.read_csv(C.DATA_OUT / "bus_variables.csv")
    rail = pd.read_csv(C.DATA_OUT / "rail_variables.csv")
    variables = analysis_variables(bus)
    print(f"{len(variables)} variables x "
          f"({C.BUS_K} bus + {C.RAIL_K} rail) clusters = "
          f"{len(variables) * (C.BUS_K + C.RAIL_K)} cluster-vs-rest tests\n")

    frames = []
    for mode, frame in (("bus", bus), ("rail", rail)):
        tests = run_mode(frame, variables, mode)
        frames.append(tests)
        significant = (tests["p_bh"] < 0.05).sum()
        print(f"{mode.upper()}: {significant}/{len(tests)} cells significant after BH "
              f"({significant / len(tests):.0%})")

        # Strongest signed separations per cluster -- the raw material for naming.
        print(f"  strongest cell per cluster (|rank-biserial|):")
        for cluster, group in tests.groupby("cluster_name", observed=True):
            top = group.reindex(group["rank_biserial"].abs().sort_values(ascending=False).index).iloc[0]
            direction = "HIGH" if top["rank_biserial"] > 0 else "LOW"
            print(f"    {str(cluster)[:38]:38} {direction:4} {top['variable']:28} "
                  f"rb={top['rank_biserial']:+.3f} {top['stars']}")
        print()

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(C.DATA_OUT / "per_cluster_tests.csv", index=False)
    print(f"Wrote {C.DATA_OUT / 'per_cluster_tests.csv'}")

    # Wide matrices for the heatmap: variables as rows, clusters as columns.
    for mode in ("bus", "rail"):
        subset = combined.loc[combined["mode"] == mode]
        for value, suffix in (("z_score", "z"), ("rank_biserial", "rb")):
            matrix = subset.pivot(index="variable", columns="cluster_name", values=value)
            matrix = matrix.reindex(variables)
            matrix.to_csv(C.DATA_OUT / f"{mode}_cluster_matrix_{suffix}.csv")
        stars = subset.pivot(index="variable", columns="cluster_name", values="stars")
        stars.reindex(variables).to_csv(C.DATA_OUT / f"{mode}_cluster_matrix_stars.csv")
    print("Wrote per-mode z / rank-biserial / stars matrices for the heatmap.")


if __name__ == "__main__":
    main()
