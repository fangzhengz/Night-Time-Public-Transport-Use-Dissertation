"""Cluster x variable association tests -- presentation style 1.

Kruskal-Wallis + epsilon-squared per variable per mode, Benjamini-Hochberg
corrected across variables within each mode.

Rank-based rather than ANOVA because none of these variables is close to
normal (IMD scores are bounded rates, density is heavily right-skewed) and
because it matches the established convention in this project.

Reading guide for the output:
  * population_density is a CONTROL. A strong bus association there is close to
    tautological -- the bus clustering is itself activity-volume driven and
    volume tracks density. Its job is to calibrate the others, not to be a
    finding.
  * epsilon-squared and Cramer's V answer different questions and should not
    be treated as interchangeable effect-size scales.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import config as C


def kruskal_epsilon_squared(values: pd.Series, groups: pd.Series) -> dict:
    frame = pd.DataFrame({"value": values, "group": groups}).dropna()
    samples = [g["value"].to_numpy() for _, g in frame.groupby("group", observed=True)]
    h_stat, p_value = stats.kruskal(*samples)
    n = len(frame)
    k = len(samples)
    return {
        "n": int(n),
        "k": int(k),
        "kruskal_H": float(h_stat),
        "p_value": float(p_value),
        "epsilon_squared": float((h_stat - k + 1) / (n - k)) if n > k else np.nan,
    }


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    ranked = p_values[order]
    m = len(p_values)
    adjusted = ranked * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    out = np.empty(m, dtype=float)
    out[order] = np.clip(adjusted, 0, 1)
    return out


def run_mode(frame: pd.DataFrame, variables: list[str], mode: str) -> pd.DataFrame:
    rows = []
    for variable in variables:
        result = kruskal_epsilon_squared(frame[variable], frame["cluster"])
        result.update({"mode": mode, "variable": variable})
        rows.append(result)
    tests = pd.DataFrame(rows)
    tests["p_bh"] = benjamini_hochberg(tests["p_value"].to_numpy())
    tests["is_control"] = tests["variable"].eq("population_density")
    return tests.sort_values("epsilon_squared", ascending=False)[
        ["mode", "variable", "n", "k", "kruskal_H", "p_value", "p_bh",
         "epsilon_squared", "is_control"]
    ]


def cluster_profile(frame: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Per-cluster medians, long format, for the report tables."""
    rows = []
    for variable in variables:
        overall = frame[variable].median()
        for cluster, group in frame.groupby("cluster_name", observed=True):
            rows.append({
                "cluster_name": cluster,
                "variable": variable,
                "n": int(group[variable].notna().sum()),
                "median": float(group[variable].median()),
                "mean": float(group[variable].mean()),
                "vs_overall_median": float(group[variable].median() - overall),
            })
    return pd.DataFrame(rows)


def main() -> None:
    bus = pd.read_csv(C.DATA_OUT / "bus_variables.csv")
    rail = pd.read_csv(C.DATA_OUT / "rail_variables.csv")

    # The reduced set (config.ANALYSIS_VARIABLES). The full 31-variable table is
    # still written by 01 and lives in bus_variables.csv / rail_variables.csv for
    # the appendix; only ANALYSIS_VARIABLES carry the formal analysis.
    variables = [column for column in C.ANALYSIS_VARIABLES if column in bus.columns]
    missing = [column for column in C.ANALYSIS_VARIABLES if column not in bus.columns]
    if missing:
        raise RuntimeError(f"ANALYSIS_VARIABLES not in the built table: {missing}")
    print(f"Testing {len(variables)} variables: {', '.join(variables)}\n")

    all_tests = []
    for mode, frame in (("bus", bus), ("rail", rail)):
        tests = run_mode(frame, variables, mode)
        all_tests.append(tests)
        print("=" * 78)
        print(f"{mode.upper()}  (K={C.BUS_K if mode == 'bus' else C.RAIL_K})")
        print("=" * 78)
        display = tests.copy()
        display["variable"] = np.where(
            display["is_control"], display["variable"] + "  [CONTROL]", display["variable"]
        )
        print(display[["variable", "n", "kruskal_H", "epsilon_squared", "p_bh"]]
              .round({"kruskal_H": 1, "epsilon_squared": 4, "p_bh": 6})
              .to_string(index=False))
        print()

        profile = cluster_profile(frame, variables)
        profile.to_csv(C.DATA_OUT / f"{mode}_cluster_profile.csv", index=False)

    combined = pd.concat(all_tests, ignore_index=True)
    combined.to_csv(C.DATA_OUT / "association_tests.csv", index=False)
    print(f"Wrote {C.DATA_OUT / 'association_tests.csv'}")

if __name__ == "__main__":
    main()
