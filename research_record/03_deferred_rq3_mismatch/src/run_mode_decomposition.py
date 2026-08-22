"""Mode decomposition: is the RQ3 mismatch driven by bus, by rail, or both?

run_mismatch_analysis.py fits PT_total (rail+bus combined) ~ OD_total, so its
residual cannot say whether a given MSOA's shortfall is a bus problem, a rail
problem, or both -- rail and bus are summed before the regression. This
script reuses the same totals (already computed in outputs/data/) to fit rail
and bus separately against the same OD totals, so the mode question can
actually be answered rather than left open.

Rail only exists in 196/981 MSOAs (most MSOAs have no Underground station at
all); bus exists in all 981. The two mode-specific models are therefore not
directly comparable in coverage -- this is reported, not glossed over.

Does not touch any RQ1/RQ2 input or output, or overwrite run_mismatch_analysis.py's
outputs. See ../README.md.
"""

import logging

import numpy as np
import pandas as pd
import statsmodels.api as sm

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

MODE_SPECS = {
    ("origin", "rail"): {"pt_col": "rail_entry_total", "od_col": "od_origin_total"},
    ("origin", "bus"): {"pt_col": "bus_boarding_total", "od_col": "od_origin_total"},
    ("destination", "rail"): {"pt_col": "rail_exit_total", "od_col": "od_destination_total"},
    ("destination", "bus"): {"pt_col": "bus_alighting_total", "od_col": "od_destination_total"},
}


def fit(df: pd.DataFrame, pt_col: str, od_col: str) -> tuple[pd.DataFrame, sm.regression.linear_model.RegressionResultsWrapper]:
    valid = df[(df[pt_col] > 0) & (df[od_col] > 0)].copy()
    x = sm.add_constant(np.log1p(valid[od_col].to_numpy()))
    y = np.log1p(valid[pt_col].to_numpy())
    model = sm.OLS(y, x).fit()
    resid = model.resid
    valid["std_residual"] = resid / resid.std(ddof=1)
    return valid, model


def main() -> None:
    pt = pd.read_csv(config.DATA_OUT / "msoa_pt_totals.csv")
    od = pd.read_csv(config.DATA_OUT / "msoa_od_totals.csv")
    merged = pt.merge(od, on="MSOA11CD", how="inner")

    log.info(
        "Coverage: %d/%d MSOAs have any rail activity; %d/%d have any bus activity",
        (merged["rail_entry_total"] > 0).sum(), len(merged),
        (merged["bus_boarding_total"] > 0).sum(), len(merged),
    )

    lines = [
        "# RQ3 mode decomposition: is the mismatch a bus story, a rail story, or both?",
        "",
        "Reuses the totals already computed by build_msoa_panels.py -- no new "
        "aggregation. Fits rail and bus separately against the same OD totals "
        "used in the combined model.",
        "",
        f"- Rail is present in {(merged['rail_entry_total'] > 0).sum()}/{len(merged)} MSOAs "
        f"(most MSOAs have no Underground station); bus is present in "
        f"{(merged['bus_boarding_total'] > 0).sum()}/{len(merged)}. The two mode-specific "
        "models below are fit on different, non-nested MSOA subsets and are not "
        "directly comparable in coverage -- read R² and residual patterns with that in mind.",
        "",
    ]

    results = {}
    for (direction, mode), spec in MODE_SPECS.items():
        valid, model = fit(merged, spec["pt_col"], spec["od_col"])
        results[(direction, mode)] = valid
        log.info(
            "%s / %s : log1p(%s) ~ log1p(%s), R^2=%.3f, slope=%.3f, n=%d",
            direction, mode, spec["pt_col"], spec["od_col"],
            model.rsquared, model.params[1], len(valid),
        )
        lines.append(
            f"- **{direction} / {mode}**: `log1p({spec['pt_col']}) ~ log1p({spec['od_col']})`, "
            f"R²={model.rsquared:.3f}, slope={model.params[1]:.3f}, n={len(valid)}."
        )
        valid[["MSOA11CD", spec["od_col"], spec["pt_col"], "std_residual"]].to_csv(
            config.DATA_OUT / f"{direction}_{mode}_mismatch.csv", index=False
        )

    # For MSOAs where both rail and bus are present, does the mode-specific
    # residual agree with the combined-model residual, or does one mode drive it?
    lines.append("")
    lines.append("## Where rail is present: does rail or bus track the combined-model gap better?")
    lines.append("")
    combined_scores = pd.read_csv(config.DATA_OUT / "msoa_mismatch_scores.csv")
    for direction in ("origin", "destination"):
        combined = combined_scores[combined_scores["direction"] == direction][["MSOA11CD", "std_residual"]].rename(
            columns={"std_residual": "std_residual_combined"}
        )
        rail_res = results[(direction, "rail")][["MSOA11CD", "std_residual"]].rename(
            columns={"std_residual": "std_residual_rail"}
        )
        bus_res = results[(direction, "bus")][["MSOA11CD", "std_residual"]].rename(
            columns={"std_residual": "std_residual_bus"}
        )
        both = combined.merge(rail_res, on="MSOA11CD", how="inner").merge(bus_res, on="MSOA11CD", how="inner")
        corr_rail = both["std_residual_combined"].corr(both["std_residual_rail"])
        corr_bus = both["std_residual_combined"].corr(both["std_residual_bus"])
        log.info(
            "%s: among %d MSOAs with both rail and bus, combined-residual correlates "
            "%.2f with rail-only residual, %.2f with bus-only residual",
            direction, len(both), corr_rail, corr_bus,
        )
        lines.append(
            f"- **{direction}** (n={len(both)} MSOAs with both modes present): combined-model "
            f"residual correlates r={corr_rail:.2f} with the rail-only residual, "
            f"r={corr_bus:.2f} with the bus-only residual."
        )

    (config.REPORT_OUT / "MODE_DECOMPOSITION.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote MODE_DECOMPOSITION.md")


if __name__ == "__main__":
    main()
