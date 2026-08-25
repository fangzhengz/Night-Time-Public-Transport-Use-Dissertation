"""Supplementary RQ3 check: is PT capture worse for movement specifically
LINKED to shift-work-heavy places, not just movement in general?

MOTIVATION. The baseline model (run_mismatch_analysis.py) compares each
MSOA's PT total against its OD total -- both MARGINAL sums, collapsed across
every origin/destination that MSOA's movement touches. That comparison can
never say whether an MSOA's under-capture has anything to do with WHO its
movement connects to; it only sees "this place has more/less general
movement than its PT usage predicts". The user's suspicion, reading Mahfouz
(2019/20 CASA MSc dissertation, cycling infrastructure prioritisation), was
that this reduces an inherently relational OD dataset to just another volume
variable, redundant with population_density and log_total_activity, which
are already tested elsewhere in the project -- and that this is very
plausibly why the original result read as a generic density/car-dependence
gradient rather than a night-worker-specific signal.

Mahfouz's own method keeps every OD pair intact and ROUTES it onto the
street network, so demand and existing infrastructure are compared at the
same object (the road link). Building an equivalent PT routing engine is out
of scope here (no PT network graph exists in this project). This script
keeps the lighter-weight half of that lesson instead: it conditions
correctly on the ACTUAL origin-destination link rather than collapsing to
marginal totals, without needing a router.

METHOD. For each MSOA, split its total night-window OD movement (as an
origin, separately as a destination) into two parts: the share physically
linked, pair by pair, to a "shift-work-heavy" MSOA on the other end, and the
rest. Test whether that share predicts the MSOA's own baseline mismatch
residual (already computed by run_mismatch_analysis.py, not refit here).
This asks a genuinely different question from the baseline model: not "does
this place have more/less movement than its PT usage predicts" but "is a
place's under-capture concentrated in the fraction of its movement that
specifically touches shift-work-heavy places".

"Shift-work-heavy" = top quartile of transport_storage_share (TS060 section
H, residence-side), population-weighted LSOA -> MSOA. This is not an ad hoc
choice: it is the single strongest raw industry-section predictor of rail
cluster membership found in rq2_independent_variables (omnibus
epsilon-squared = 0.202, the highest of any non-car-ownership variable
tested there -- see rq2_independent_variables/outputs/report/RESULTS.md).
Composites (the old hospitality_industry_share / shiftwork_industry_share)
are deliberately not used here, for the same reason they were dropped from
rq2_independent_variables's ANALYSIS_VARIABLES: merging sections together
was found to dilute this specific signal.

Does not touch any RQ1/RQ2 input or output; reads rq2_independent_variables's
already-downloaded Census source files read-only. See ../README.md.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SHIFTWORK_SECTION_COLUMN = "H Transport and storage"
SHIFTWORK_TOP_QUARTILE = 0.75


def msoa_shiftwork_share() -> pd.DataFrame:
    """Population-weighted LSOA transport_storage_share -> MSOA11, all London MSOAs."""
    sections = pd.read_csv(config.TS060_INDUSTRY_SECTIONS)
    sections = sections.rename(columns={sections.columns[0]: "LSOA21CD"})
    sections = sections[["LSOA21CD", SHIFTWORK_SECTION_COLUMN]].rename(
        columns={SHIFTWORK_SECTION_COLUMN: "transport_storage_share"}
    )

    pop = pd.read_csv(
        config.IMD_POPULATION, usecols=[config.IMD_POPULATION_LSOA_COLUMN, config.IMD_POPULATION_COLUMN]
    ).rename(columns={
        config.IMD_POPULATION_LSOA_COLUMN: "LSOA21CD",
        config.IMD_POPULATION_COLUMN: "population",
    })

    lookup = pd.read_csv(config.MSOA_LOOKUP, usecols=["LSOA21CD", "MSOA11CD"])

    frame = sections.merge(pop, on="LSOA21CD", how="inner").merge(lookup, on="LSOA21CD", how="inner")
    frame = frame.dropna(subset=["transport_storage_share", "population", "MSOA11CD"])
    frame["weighted"] = frame["transport_storage_share"] * frame["population"]

    msoa = frame.groupby("MSOA11CD").agg(
        transport_storage_share=("weighted", "sum"),
        population=("population", "sum"),
        n_lsoa=("LSOA21CD", "count"),
    )
    msoa["transport_storage_share"] = msoa["transport_storage_share"] / msoa["population"]
    msoa = msoa.reset_index()

    threshold = msoa["transport_storage_share"].quantile(SHIFTWORK_TOP_QUARTILE)
    msoa["shiftwork_heavy"] = msoa["transport_storage_share"] >= threshold
    log.info(
        "MSOA transport_storage_share: %d MSOAs, top-quartile threshold=%.4f, %d flagged shiftwork_heavy",
        len(msoa), threshold, int(msoa["shiftwork_heavy"].sum()),
    )
    return msoa[["MSOA11CD", "transport_storage_share", "shiftwork_heavy"]]


def linked_share(od: pd.DataFrame, shiftwork: pd.DataFrame, direction: str) -> pd.DataFrame:
    """For each MSOA in `direction` (origin or destination), what share of its
    total night-window OD flow is linked to a shiftwork_heavy MSOA on the
    OTHER end of the pair. This is the pair-preserving step -- it cannot be
    computed from either side's marginal total alone."""
    self_col, other_col = (
        ("origin_msoa11cd", "destination_msoa11cd") if direction == "origin"
        else ("destination_msoa11cd", "origin_msoa11cd")
    )
    tagged = od.merge(
        shiftwork[["MSOA11CD", "shiftwork_heavy"]].rename(
            columns={"MSOA11CD": other_col, "shiftwork_heavy": "other_end_shiftwork_heavy"}
        ),
        on=other_col, how="left",
    )
    tagged["other_end_shiftwork_heavy"] = tagged["other_end_shiftwork_heavy"].fillna(False).astype(bool)

    totals = tagged.groupby(self_col)["flow_sum"].sum().rename("total_flow")
    linked = (
        tagged.loc[tagged["other_end_shiftwork_heavy"]]
        .groupby(self_col)["flow_sum"].sum().rename("linked_flow")
    )
    out = pd.concat([totals, linked], axis=1).fillna(0.0).reset_index()
    out = out.rename(columns={self_col: "MSOA11CD"})
    out["shiftwork_linked_share"] = np.where(
        out["total_flow"] > 0, out["linked_flow"] / out["total_flow"], np.nan
    )
    return out[["MSOA11CD", "total_flow", "linked_flow", "shiftwork_linked_share"]]


def test_direction(
    linked: pd.DataFrame, mismatch: pd.DataFrame, direction: str
) -> tuple[pd.DataFrame, dict]:
    resid = mismatch.loc[mismatch["direction"] == direction, ["MSOA11CD", "std_residual"]]
    frame = linked.merge(resid, on="MSOA11CD", how="inner").dropna(
        subset=["shiftwork_linked_share", "std_residual"]
    )

    rho, p_spearman = stats.spearmanr(frame["shiftwork_linked_share"], frame["std_residual"])

    frame["linked_share_quartile"] = pd.qcut(
        frame["shiftwork_linked_share"], 4, labels=["Q1_low", "Q2", "Q3", "Q4_high"], duplicates="drop"
    )
    top = frame.loc[frame["linked_share_quartile"] == "Q4_high", "std_residual"].to_numpy()
    rest = frame.loc[frame["linked_share_quartile"] != "Q4_high", "std_residual"].to_numpy()
    u_stat, p_mw = stats.mannwhitneyu(top, rest, alternative="two-sided")
    rank_biserial = 2.0 * u_stat / (len(top) * len(rest)) - 1.0

    stats_out = {
        "direction": direction, "n": int(len(frame)),
        "spearman_rho": float(rho), "spearman_p": float(p_spearman),
        "top_quartile_median_residual": float(np.median(top)),
        "rest_median_residual": float(np.median(rest)),
        "mannwhitney_rank_biserial": float(rank_biserial), "mannwhitney_p": float(p_mw),
    }
    log.info(
        "%s: spearman rho=%.3f (p=%.4g, n=%d) | top-quartile-linked median residual=%.3f "
        "vs rest=%.3f, rank-biserial=%+.3f (p=%.4g)",
        direction, rho, p_spearman, len(frame),
        stats_out["top_quartile_median_residual"], stats_out["rest_median_residual"],
        rank_biserial, p_mw,
    )
    return frame, stats_out


def main() -> None:
    od = pd.read_csv(config.OD_FLOWS)
    od = od[od["hour"].isin(config.NIGHT_HOURS)]
    mismatch = pd.read_csv(config.DATA_OUT / "msoa_mismatch_scores.csv")
    shiftwork = msoa_shiftwork_share()

    report_lines = [
        "# RQ3 supplementary check -- shift-work-linked OD movement vs. PT mismatch",
        "",
        "Conditions on the actual OD pair (which MSOA a place's movement connects to),",
        "not just each MSOA's own marginal total. See this script's own docstring for",
        "the full method rationale and the Mahfouz (2019/20 CASA dissertation) precedent",
        "it is following the spirit of, at a much lighter weight (no PT routing engine).",
        "",
        f"Shift-work-heavy MSOA = top quartile of population-weighted "
        f"transport_storage_share (TS060 section H). "
        f"{int(shiftwork['shiftwork_heavy'].sum())}/{len(shiftwork)} MSOAs flagged.",
        "",
    ]

    results = []
    for direction in ("origin", "destination"):
        linked = linked_share(od, shiftwork, direction)
        frame, stats_out = test_direction(linked, mismatch, direction)
        results.append(stats_out)
        frame.merge(shiftwork, on="MSOA11CD", how="left").to_csv(
            config.DATA_OUT / f"{direction}_shiftwork_linked_mismatch.csv", index=False
        )

        report_lines += [
            f"## {direction.capitalize()}",
            "",
            f"- n={stats_out['n']} MSOAs with both a computed linked-share and a baseline "
            f"mismatch residual.",
            f"- Spearman(shiftwork_linked_share, std_residual) = {stats_out['spearman_rho']:+.3f} "
            f"(p={stats_out['spearman_p']:.4g}).",
            f"- Top-quartile-linked MSOAs: median residual {stats_out['top_quartile_median_residual']:+.3f} "
            f"vs {stats_out['rest_median_residual']:+.3f} for the rest "
            f"(Mann-Whitney rank-biserial={stats_out['mannwhitney_rank_biserial']:+.3f}, "
            f"p={stats_out['mannwhitney_p']:.4g}).",
            "",
        ]

    pd.DataFrame(results).to_csv(config.DATA_OUT / "shiftwork_corridor_tests.csv", index=False)

    report_lines += [
        "## Reading this",
        "",
        "A negative Spearman rho / negative rank-biserial means: MSOAs whose night-time "
        "movement is disproportionately linked to shift-work-heavy places have WORSE "
        "(more negative) PT-capture residuals than MSOAs whose movement is not -- i.e. "
        "the under-capture is concentrated specifically in shift-work-linked corridors, "
        "not spread evenly. A near-zero or positive result means the baseline model's "
        "residual pattern is not specifically about shift-work connectivity; it is closer "
        "to the general density/car-dependence gradient already found in the marginal-total "
        "version.",
        "",
        "## Caveats (in addition to the baseline model's own, in RESULTS_SUMMARY.md)",
        "",
        "- transport_storage_share is a RESIDENCE-side variable (where shift-transport/",
        "  storage workers live), computed from 2021 Census, aggregated LSOA -> MSOA by",
        "  population weight -- same vintage-mixing caveat as the rest of the project.",
        "- \"Linked\" means the OTHER end of an OD pair is a shiftwork-heavy MSOA, not that",
        "  the flow itself is made by shift workers -- OD data has no traveller attributes.",
        "- Top-quartile threshold is a specific, disclosed choice (0.75); not tested for",
        "  sensitivity to threshold placement in this pass.",
    ]
    (config.REPORT_OUT / "SHIFTWORK_CORRIDOR_CHECK.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )
    log.info("Wrote SHIFTWORK_CORRIDOR_CHECK.md")


if __name__ == "__main__":
    main()
