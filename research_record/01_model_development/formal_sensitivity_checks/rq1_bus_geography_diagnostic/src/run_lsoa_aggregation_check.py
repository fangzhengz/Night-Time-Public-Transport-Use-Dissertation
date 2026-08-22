"""Is LSOA-level aggregation discarding real stop-to-stop heterogeneity?

Uses pre-aggregation stop-level BUSTO data to test whether stops inside the
same LSOA already behave similarly to each other (in which case aggregating
to LSOA before clustering loses little), or whether they are highly
heterogeneous (in which case aggregation could be manufacturing the weak
geography link found in run_geography_diagnostic.py).

Method: for each proxy metric, decompose stop-to-stop variance into
between-LSOA and within-LSOA components (one-way ANOVA on LSOA as the
grouping factor). A high eta^2(metric ~ LSOA) means most of the variance is
between LSOAs, i.e. stops in the same LSOA are already similar.

Stop-level 15-minute counts are first summed to hourly bins to match the
temporal grain actually used for the bus clustering (bus was kept hourly;
see the fair-resolution-sensitivity test in the RQ1/RQ2 consolidated note).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

STOP_PARQUET = FYP / "outputs" / "preprocessed_busto" / "busto_stop_qhr_night.parquet"
STOP_LSOA_LOOKUP = FYP / "outputs" / "preprocessed_busto" / "busto_stop_lsoa_lookup.csv"

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    aligned = numerator.reindex(denominator.index, fill_value=0)
    return aligned.div(denominator.replace(0, np.nan))


def eta_squared_oneway(values: pd.Series, groups: pd.Series) -> float:
    grand_mean = values.mean()
    ss_total = ((values - grand_mean) ** 2).sum()
    ss_between = sum(
        len(g) * (g.mean() - grand_mean) ** 2 for _, g in values.groupby(groups)
    )
    return float(ss_between / ss_total) if ss_total > 0 else float("nan")


def build_stop_metrics() -> pd.DataFrame:
    raw = pd.read_parquet(STOP_PARQUET).copy()
    raw["count"] = raw["boardings"].fillna(0) + raw["alightings"].fillna(0)
    # collapse 15-minute qhr bins to hourly, matching the hourly grain used
    # for the actual bus clustering
    raw["hour_bin"] = (raw["traffic_minute"] // 60) * 60
    hourly = (
        raw.groupby(["stopcode", "day_type", "hour_bin"], as_index=False)["count"]
        .sum()
    )

    total = hourly.groupby("stopcode")["count"].sum()
    post_midnight = (
        hourly.loc[hourly["hour_bin"].between(1440, 1799)]
        .groupby("stopcode")["count"]
        .sum()
    )
    day_total = (
        hourly.groupby(["stopcode", "day_type"])["count"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=["Weekday", "Saturday", "Sunday"], fill_value=0)
    )
    weekend_mean = day_total[["Saturday", "Sunday"]].mean(axis=1)

    metrics = pd.DataFrame(index=total.index)
    metrics["total_activity"] = total
    metrics["log_total_activity"] = np.log1p(total)
    metrics["post_midnight_share"] = safe_divide(post_midnight, total)
    metrics["weekend_ratio"] = safe_divide(weekend_mean, day_total["Weekday"])
    metrics.index.name = "stopcode"
    return metrics.reset_index()


def main() -> None:
    stop_metrics = build_stop_metrics()

    lookup = pd.read_csv(STOP_LSOA_LOOKUP)
    lookup["stopcode"] = lookup["stopcode"].astype(str)
    stop_metrics["stopcode"] = stop_metrics["stopcode"].astype(str)
    merged = stop_metrics.merge(lookup[["stopcode", "lsoa"]], on="stopcode", how="inner")

    stops_per_lsoa = merged.groupby("lsoa")["stopcode"].nunique()
    n_stops_total = merged["stopcode"].nunique()
    n_lsoa = merged["lsoa"].nunique()
    n_single_stop_lsoa = int((stops_per_lsoa == 1).sum())

    metric_cols = ["log_total_activity", "post_midnight_share", "weekend_ratio"]
    rows = []
    for metric in metric_cols:
        valid = merged.dropna(subset=[metric])
        eta2 = eta_squared_oneway(valid[metric], valid["lsoa"])
        rows.append(
            {
                "metric": metric,
                "n_stops": len(valid),
                "eta_squared_lsoa": eta2,
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(DATA / "bus_stop_lsoa_variance_decomposition.csv", index=False)

    audit = pd.DataFrame(
        [
            {"item": "n_stops_matched_to_lsoa", "value": n_stops_total},
            {"item": "n_lsoa_with_at_least_one_stop", "value": n_lsoa},
            {"item": "median_stops_per_lsoa", "value": float(stops_per_lsoa.median())},
            {"item": "n_lsoa_with_exactly_1_stop", "value": n_single_stop_lsoa},
        ]
    )
    audit.to_csv(DATA / "bus_stop_lsoa_audit.csv", index=False)

    lines = [
        "# Bus stop-to-LSOA aggregation variance decomposition",
        "",
        "Tests whether LSOA-level aggregation (used before bus clustering) discards",
        "real stop-to-stop heterogeneity. High eta_squared_lsoa means most of the",
        "stop-to-stop variance sits BETWEEN LSOAs, i.e. stops inside the same LSOA",
        "already behave similarly -- aggregation is not hiding real structure.",
        "",
        audit.to_markdown(index=False),
        "",
        result.to_markdown(index=False),
    ]
    (REPORT / "LSOA_AGGREGATION_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    print(audit)
    print(result)


if __name__ == "__main__":
    main()
