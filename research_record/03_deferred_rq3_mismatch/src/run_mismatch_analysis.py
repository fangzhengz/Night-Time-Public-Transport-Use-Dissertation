"""RQ3 mismatch analysis: does observed PT usage track general OD movement?

For each direction (origin-side: rail entries + bus boardings; destination-
side: rail exits + bus alightings), fits PT_total ~ OD_total across all MSOAs
with both-source coverage, and flags MSOAs with large negative standardised
residuals -- i.e. much less captured PT usage than their general night-time
movement level would predict -- as candidate service-gap areas. Closes the
loop back to the equity framing by checking whether those MSOAs are
disproportionately LNWC night-worker-dense area types.

Scope: baseline model only (PT_total ~ OD_total). Explaining the residual
further with car-ownership/income covariates is an explicitly optional
extension (per Esra, 11 Jun) and is out of scope for this pass.

Does not touch any RQ1/RQ2 input or output. See ../README.md.
"""

import logging
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2_contingency

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

DIRECTIONS = {
    "origin": {"pt_col": "origin_total", "od_col": "od_origin_total", "label": "Origin-side (entries + boardings) vs. OD trips starting here"},
    "destination": {"pt_col": "destination_total", "od_col": "od_destination_total", "label": "Destination-side (exits + alightings) vs. OD trips ending here"},
}

LNWC_LOOKUP_PATH = config.FYP / "rq2test analysis" / "outputs" / "data" / "lnwc_group_lookup.csv"


def load_merged_totals() -> pd.DataFrame:
    pt = pd.read_csv(config.DATA_OUT / "msoa_pt_totals.csv")
    od = pd.read_csv(config.DATA_OUT / "msoa_od_totals.csv")
    merged = pt.merge(od, on="MSOA11CD", how="inner")
    log.info("Merged PT+OD totals: %d MSOAs with coverage on both sides", len(merged))
    return merged


def dominant_lnwc_per_msoa() -> pd.DataFrame:
    """Aggregate LSOA-level LNWC group up to MSOA11 by simple mode.

    Fixed 2026-08: config.LNWC_LSOA now points at the real LNWC classification
    (lsoa21cd, lnc_grp). It previously pointed at a bus cluster-labels file
    with no lnc_grp column at all -- this function could not have run."""
    lnwc_lsoa = pd.read_csv(config.LNWC_LSOA)[["lsoa21cd", "lnc_grp"]].rename(
        columns={"lsoa21cd": "LSOA21CD"}
    )
    lookup = pd.read_csv(config.MSOA_LOOKUP, usecols=["LSOA21CD", "MSOA11CD"])
    joined = lnwc_lsoa.merge(lookup, on="LSOA21CD", how="inner").dropna(subset=["lnc_grp"])

    def mode_or_nan(s: pd.Series):
        m = s.mode()
        return m.iloc[0] if not m.empty else np.nan

    dominant = joined.groupby("MSOA11CD")["lnc_grp"].agg(mode_or_nan).rename("dominant_lnwc").reset_index()

    # How often is the "mode" actually a tie / weakly dominant? Logged, not resolved.
    def top_share(s: pd.Series) -> float:
        counts = s.value_counts()
        return float(counts.iloc[0] / counts.sum())

    purity = joined.groupby("MSOA11CD")["lnc_grp"].agg(top_share).rename("dominant_lnwc_purity").reset_index()
    dominant = dominant.merge(purity, on="MSOA11CD", how="left")

    log.info(
        "Dominant LNWC assigned for %d MSOAs (median purity of dominant group = %.2f)",
        len(dominant), dominant["dominant_lnwc_purity"].median(),
    )
    return dominant


def fit_mismatch(df: pd.DataFrame, pt_col: str, od_col: str) -> pd.DataFrame:
    """OLS in log1p space.

    Both totals are heavily right-skewed (a handful of very high-volume MSOAs
    dominate a raw-scale fit and distort the residuals for everywhere else).
    log1p keeps this consistent with the log-log scatter plot and is the
    standard treatment for this kind of volume/gravity comparison.
    """
    valid = df[(df[od_col] > 0)].copy()
    log_od = np.log1p(valid[od_col].to_numpy())
    log_pt = np.log1p(valid[pt_col].to_numpy())
    x = sm.add_constant(log_od)
    model = sm.OLS(log_pt, x).fit()
    log.info(
        "log1p(%s) ~ log1p(%s) : R^2=%.3f, slope=%.4f (p=%.4g), n=%d",
        pt_col, od_col, model.rsquared, model.params[1], model.pvalues[1], len(valid),
    )
    resid = model.resid
    valid["fitted_log"] = model.fittedvalues
    valid["residual_log"] = resid
    valid["std_residual"] = resid / resid.std(ddof=1)
    return valid, model


def association_outputs(observed: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Chi-square + Cramer's V + location-quotient enrichment for a contingency table.

    Mirrors rq2test analysis/src/run_analysis.py's association_outputs, adapted
    for a (mismatch quartile) x (LNWC group) table.
    """
    chi2, p_value, dof, expected_array = chi2_contingency(observed.to_numpy())
    row_pct = observed.div(observed.sum(axis=1), axis=0)
    universe_share = observed.sum(axis=0) / observed.to_numpy().sum()
    enrichment = row_pct.div(universe_share, axis=1)
    n = observed.to_numpy().sum()
    denominator = min(observed.shape[0] - 1, observed.shape[1] - 1)
    cramers_v = math.sqrt(chi2 / (n * denominator)) if denominator > 0 else np.nan
    stats = {
        "chi_square": float(chi2), "p_value": float(p_value),
        "degrees_of_freedom": int(dof), "cramers_v": float(cramers_v), "n": int(n),
    }
    return enrichment, stats


def plot_scatter(valid: pd.DataFrame, od_col: str, pt_col: str, direction: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    has_lnwc = valid["dominant_lnwc"].notna()
    scatter = ax.scatter(
        valid.loc[has_lnwc, od_col], valid.loc[has_lnwc, pt_col],
        c=valid.loc[has_lnwc, "dominant_lnwc"], cmap="tab10", vmin=1, vmax=7,
        s=14, alpha=0.75, edgecolors="none",
    )
    ax.scatter(
        valid.loc[~has_lnwc, od_col], valid.loc[~has_lnwc, pt_col],
        c="lightgrey", s=10, alpha=0.5, edgecolors="none", label="no LNWC match",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(f"OD night-time movement ({od_col})")
    ax.set_ylabel(f"Observed PT usage ({pt_col})")
    ax.set_title(f"{direction}: PT usage vs. OD movement, by MSOA\n(colour = dominant LNWC group)")
    fig.colorbar(scatter, ax=ax, label="Dominant LNWC group", ticks=range(1, 8))
    fig.tight_layout()
    fig.savefig(config.FIGURE_OUT / f"{direction}_pt_vs_od_scatter.png", dpi=150)
    plt.close(fig)


def main() -> None:
    merged = load_merged_totals()
    lnwc = dominant_lnwc_per_msoa()
    lnwc_names = pd.read_csv(LNWC_LOOKUP_PATH).set_index("lnc_grp")["lnwc_name"].to_dict() if LNWC_LOOKUP_PATH.exists() else {}

    merged = merged.merge(lnwc, on="MSOA11CD", how="left")
    n_no_lnwc = int(merged["dominant_lnwc"].isna().sum())
    log.info("%d/%d MSOAs have no dominant LNWC assignment (outside LNWC's LSOA extent)", n_no_lnwc, len(merged))

    all_results = []
    summary_lines = [
        "# RQ3 mismatch analysis -- night-time PT usage vs. OD movement (provisional)",
        "",
        "## Method boundary",
        "",
        "Baseline model only: `log1p(PT_total) ~ log1p(OD_total)` (OLS), one model per "
        "direction. Both totals are heavily right-skewed (a few very high-volume MSOAs "
        "dominate a raw-scale fit), so log1p keeps the regression consistent with the "
        "log-log scatter plots and is the standard treatment for this kind of volume "
        "comparison. Large negative standardised residual = MSOA has much less captured "
        "PT usage than its general OD movement level predicts = candidate mismatch/gap. "
        "Explaining residuals further with car-ownership/income covariates is an "
        "explicitly optional next step (Esra, 11 Jun 2026), not attempted here.",
        "",
        "## Coverage and caveats",
        "",
        f"- MSOAs with both PT and OD night-window ({config.NIGHT_HOURS[0]}:00-06:00) coverage: {len(merged)}.",
        f"- MSOAs with no dominant-LNWC assignment (outside LNWC's LSOA extent): {n_no_lnwc}.",
        "- OD flow data is 2019; NUMBAT/BUSTO are 2024/25 (5-6 year vintage gap).",
        "- OD flow data is not mode-specific: a gap could reflect car/walk/cycle use, "
        "not necessarily unmet PT demand specifically.",
        "- OD flow data has a suppression floor (flow_sum >= 10) and covers only the "
        "most prevalent MSOA pairs, not a complete flow census -- likely undercounts "
        "peripheral/low-volume MSOAs more than central ones.",
        "- OD data has no weekday/weekend split; compared here against a weekday-only "
        "(rail TWT, bus Weekday) PT slice.",
        "- Rail-to-MSOA assignment is simple point-in-polygon (station -> containing "
        "LSOA21 -> MSOA11), not catchment-weighted; 16 rail stations outside the LSOA21 "
        "extent are excluded (same 16 excluded from RQ2's LNWC analysis).",
        "",
    ]

    for direction, spec in DIRECTIONS.items():
        valid, model = fit_mismatch(merged, spec["pt_col"], spec["od_col"])
        valid["direction"] = direction
        all_results.append(valid)

        valid["mismatch_quartile"] = pd.qcut(valid["std_residual"], 4, labels=["Q1_most_negative", "Q2", "Q3", "Q4_most_positive"])
        plot_scatter(valid, spec["od_col"], spec["pt_col"], direction)

        summary_lines.append(f"## {direction.capitalize()}: {spec['label']}")
        summary_lines.append("")
        summary_lines.append(
            f"- OLS `log1p({spec['pt_col']}) ~ log1p({spec['od_col']})`: R²={model.rsquared:.3f}, "
            f"slope={model.params[1]:.4f} (p={model.pvalues[1]:.4g}), n={len(valid)}."
        )

        ct = valid.dropna(subset=["dominant_lnwc"]).groupby(["mismatch_quartile", "dominant_lnwc"], observed=True).size().unstack(fill_value=0)
        if ct.shape[0] > 1 and ct.shape[1] > 1:
            enrichment, stats = association_outputs(ct)
            summary_lines.append(
                f"- Mismatch quartile x dominant LNWC: chi-square={stats['chi_square']:.2f}, "
                f"df={stats['degrees_of_freedom']}, Cramer's V={stats['cramers_v']:.3f}, "
                f"p={stats['p_value']:.4g}, n={stats['n']}."
            )
            q1_enrich = enrichment.loc["Q1_most_negative"].sort_values(ascending=False)
            top3 = q1_enrich.head(3)
            summary_lines.append(
                "- Largest-mismatch quartile (Q1, most negative residual) LNWC enrichment "
                "(location quotient, >1 = over-represented): "
                + ", ".join(f"LNWC{int(g)} ({lnwc_names.get(int(g), '?')})={v:.2f}" for g, v in top3.items())
            )
        summary_lines.append("")

        bottom20 = valid.nsmallest(20, "std_residual")[
            ["MSOA11CD", spec["od_col"], spec["pt_col"], "std_residual", "dominant_lnwc"]
        ]
        bottom20.to_csv(config.DATA_OUT / f"{direction}_top20_mismatch_msoas.csv", index=False)

    results = pd.concat(all_results, ignore_index=True)
    results.to_csv(config.DATA_OUT / "msoa_mismatch_scores.csv", index=False)
    log.info("Wrote msoa_mismatch_scores.csv (%d rows)", len(results))

    summary_lines += [
        "## Interpretation limits",
        "",
        "- Residuals describe MSOA-level association, not individual travel behaviour.",
        "- A negative residual is a *candidate* mismatch signal, not proof of unmet "
        "transit demand -- see caveats above (mode, vintage, suppression).",
        "- Top/bottom-20 tables are saved per direction in outputs/data/ for "
        "face-validity review before treating any specific MSOA as a finding.",
    ]
    (config.REPORT_OUT / "RESULTS_SUMMARY.md").write_text("\n".join(summary_lines), encoding="utf-8")
    log.info("Wrote RESULTS_SUMMARY.md")


if __name__ == "__main__":
    main()
