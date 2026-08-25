"""Hour-stratified robustness check for the RQ3 mismatch model.

run_mismatch_analysis.py fits log1p(PT_total) ~ log1p(OD_total) on totals
summed across the whole 18:00-06:00 window, per the design note in
../README.md (avoids OD's suppression-floor noise at fine granularity). This
script checks whether that pooled result is stable across the night or
concentrated in specific hours, using the hourly panels build_msoa_panels.py
already produces (msoa_pt_panel_hourly.csv, msoa_od_panel_hourly.csv).

Not a replacement for the main model -- a robustness/diagnostic check on it.
Does not touch any RQ1/RQ2 input or output. See ../README.md.
"""

import logging

import numpy as np
import pandas as pd
import statsmodels.api as sm

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

HOUR_ORDER = list(range(18, 24)) + list(range(0, 6))  # display order, matches config.NIGHT_HOURS
HOWARD_INTEREST_WINDOW = set(range(0, 6))  # "midnight to 6am is the one that is more interesting" -- Howard, 9 Jun


def load_hourly() -> pd.DataFrame:
    pt = pd.read_csv(config.DATA_OUT / "msoa_pt_panel_hourly.csv")
    od = pd.read_csv(config.DATA_OUT / "msoa_od_panel_hourly.csv")
    pt["origin_hourly"] = pt.get("rail_entry", 0.0) + pt.get("bus_boarding", 0.0)
    pt["destination_hourly"] = pt.get("rail_exit", 0.0) + pt.get("bus_alighting", 0.0)
    merged = pt.merge(od, on=["MSOA11CD", "hour"], how="inner")
    return merged


def fit_by_hour(df: pd.DataFrame, pt_col: str, od_col: str) -> pd.DataFrame:
    rows = []
    for hour in HOUR_ORDER:
        sub = df[(df["hour"] == hour) & (df[pt_col] > 0) & (df[od_col] > 0)]
        if len(sub) < 30:
            rows.append({"hour": hour, "n": len(sub), "r_squared": np.nan, "slope": np.nan})
            continue
        x = sm.add_constant(np.log1p(sub[od_col].to_numpy()))
        y = np.log1p(sub[pt_col].to_numpy())
        model = sm.OLS(y, x).fit()
        rows.append({"hour": hour, "n": len(sub), "r_squared": model.rsquared, "slope": model.params[1]})
    return pd.DataFrame(rows)


def main() -> None:
    merged = load_hourly()
    log.info("Hourly merged panel: %d rows across %d MSOAs, %d hours",
              len(merged), merged["MSOA11CD"].nunique(), merged["hour"].nunique())

    lines = [
        "# RQ3 hour-stratified robustness check",
        "",
        "The main model (run_mismatch_analysis.py) pools the whole 18:00-06:00 "
        "window into a single per-MSOA total before fitting `log1p(PT) ~ log1p(OD)`. "
        "This checks whether that relationship is stable hour-by-hour, or "
        "concentrated in specific hours, using the same log1p-OLS specification "
        "fit separately per hour (n < 30 valid MSOA-hour cells skipped -- OD's "
        "suppression floor makes some hours sparse at the per-MSOA-hour level).",
        "",
    ]

    for direction, pt_col, od_col in (
        ("origin", "origin_hourly", "od_origin"),
        ("destination", "destination_hourly", "od_destination"),
    ):
        by_hour = fit_by_hour(merged, pt_col, od_col)
        by_hour.to_csv(config.DATA_OUT / f"{direction}_r2_by_hour.csv", index=False)
        log.info("%s by hour:\n%s", direction, by_hour.to_string(index=False))

        lines.append(f"## {direction}")
        lines.append("")
        lines.append("| hour | n | R² | slope |")
        lines.append("|---|---|---|---|")
        for _, row in by_hour.iterrows():
            r2 = f"{row['r_squared']:.3f}" if pd.notna(row["r_squared"]) else "n/a (n<30)"
            slope = f"{row['slope']:.3f}" if pd.notna(row["slope"]) else "n/a"
            marker = " *" if int(row["hour"]) in HOWARD_INTEREST_WINDOW else ""
            lines.append(f"| {int(row['hour']):02d}:00{marker} | {int(row['n'])} | {r2} | {slope} |")
        lines.append("")
        valid = by_hour.dropna(subset=["r_squared"])
        lines.append(
            f"- R² across hours: min={valid['r_squared'].min():.3f}, "
            f"max={valid['r_squared'].max():.3f}, "
            f"mean={valid['r_squared'].mean():.3f}."
        )
        deep_night = valid[valid["hour"].isin(HOWARD_INTEREST_WINDOW)]
        evening = valid[~valid["hour"].isin(HOWARD_INTEREST_WINDOW)]
        if len(deep_night) and len(evening):
            lines.append(
                f"- Deep night (00:00-06:00, marked *, Howard's stated primary interest, "
                f"9 Jun): mean R²={deep_night['r_squared'].mean():.3f} vs. "
                f"evening (18:00-24:00): mean R²={evening['r_squared'].mean():.3f}."
            )
        lines.append("")

    (config.REPORT_OUT / "HOURLY_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote HOURLY_CHECK.md")


if __name__ == "__main__":
    main()
