"""The integrated figure: one row per cluster, three panels across.

Until now the three things a reader needs to connect have lived in three
different places -- the temporal curves in the RQ1 clustering folder, the
behavioural metrics in analysis/03_lnwc_context, and the area-context profile
here. A reader had to hold three figures in their head to connect the night
curve with the wider social, employment and facility setting.

This puts them on one row:

  [ entry/exit night curve ] [ behavioural metrics ] [ area-context profile ]
       what the rhythm            how it scores           area context
        actually is          on mode-specific metrics    (the formal set)

Panel 1 plots boardings and alightings (bus) or entries and exits (rail)
separately rather than summed, because the entry/exit split is the strongest
single thing the rail clustering found (direction_balance epsilon-squared
0.560) and summing it away would hide the origin-versus-destination story
the whole chapter turns on.

Panels 2 and 3 are z-scores against all units in the mode, so the three
panels share an interpretation: bars right of the line are above the London
average for that mode, bars left are below.
"""

from __future__ import annotations

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as C

BEHAVIOUR_METRICS = {
    "bus": ["log_total_activity", "direction_balance", "post_2300_share",
            "post_midnight_persistence", "weekend_ratio"],
    # Keep this list in sync with the adopted Rail behavioural metrics.
    # Since 2026-08-06 both modes use the same 23:00 threshold while retaining
    # their own complete source windows (both modes use 18:00-05:00).
    "rail": ["log_total_activity", "direction_balance", "post_2300_share",
             "weekend_common_ratio"],
}
METRIC_LABEL = {
    "log_total_activity": "activity (log)",
    "post_2300_share": "post-23:00 share",
    "post_midnight_persistence": "post-midnight persistence",
    "weekend_ratio": "weekend ratio",
    "direction_balance": "direction balance",
    "weekend_common_ratio": "weekend ratio",
}
VARIABLE_LABEL = {
    "imd_income": "IMD income deprivation",
    "imd_education": "IMD education deprivation",
    "imd_health": "IMD health deprivation",
    "deprived_1plus_share": "deprived in 1+ dimension (TS011)",
    "hospitality_industry_share": "hospitality workers (res.)",
    "shiftwork_industry_share": "shift-work sectors (res.)",
    "accom_food_share": "accommodation & food (res.)",
    "transport_storage_share": "transport & storage (res.)",
    "admin_support_share": "admin & support services (res.)",
    "wholesale_retail_share": "wholesale & retail (res.)",
    "health_social_share": "health & social work (res.)",
    "manufacturing_share": "manufacturing (res.)",
    "public_admin_share": "public admin. & defence (res.)",
    "bres_accom_food_share": "accommodation & food (work.)",
    "bres_transport_storage_share": "transport & storage (work.)",
    "bres_admin_support_share": "admin & support services (work.)",
    "bres_wholesale_retail_share": "wholesale & retail (work.)",
    "bres_health_social_share": "health & social work (work.)",
    "bres_manufacturing_share": "manufacturing (work.)",
    "private_rented_share": "private rented",
    "social_rented_share": "social rented",
    "asian_share": "Asian", "black_share": "Black",
    "dependent_children_share": "households w/ children",
    "self_employed_share": "self-employed",
    "unemployed_share": "unemployed",
    "log1p_poi_count": "POI count (log1p)",
    "shannon_group": "POI diversity (Shannon H)",
    "population_density": "population density (control)",
}

POSITIVE = "#C0392B"   # above the mode average
NEGATIVE = "#2E86C1"   # below


def profile_from_long(long: pd.DataFrame, unit: str, labels: pd.DataFrame) -> pd.DataFrame:
    """Mean hourly share per cluster x day x direction, normalised over the WEEK.

    Normalisation matches the clustering's own feature construction
    (analysis/02_mode_specific_clustering/rail/src/02_build_features_allmodes.py: "normalise each
    direction over the whole week"): every hour is divided by that unit's
    week-long total for that direction, NOT by its total within the day being
    plotted.

    That distinction matters and an earlier version of this script got it wrong.
    Normalising inside each day makes every day's curve sum to 1, so the panels
    look comparable in height even when one day carries far more travel -- which
    erases the single most important fact about Friday and Saturday nights. With
    a week-long denominator the panel heights are directly comparable and the
    Night Tube shows up as extra area rather than being normalised away.

    Still read the curve as "what fraction of this unit's week falls in this
    hour". It is a shape, not a volume: C3 and C4 carry 80% of all Night Tube
    passengers but, being high-volume inner stations, devote a smaller share of
    their own week to the small hours than C1 does.
    """
    frame = long.groupby([unit, "day_type", "direction", "hour_bin"], observed=True)["count"].sum()
    frame = frame.reset_index()
    week_total = frame.groupby([unit, "direction"], observed=True)["count"].transform("sum")
    frame["share"] = frame["count"] / week_total.replace(0, np.nan)
    frame = frame.merge(labels, on=unit, how="inner")
    return (
        frame.groupby(["cluster", "day_type", "direction", "hour_bin"], observed=True)["share"]
        .mean()
        .reset_index()
    )


def bus_profiles(labels: pd.DataFrame) -> pd.DataFrame:
    long = pd.read_parquet(
        C.FYP / "analysis" / "01_data_preparation" / "bus" / "outputs_1805_min33" / "preprocessed"
        / "bus_lsoa_night_long.parquet"
    )
    # BUSTO distinguishes only Weekday / Saturday / Sunday -- Friday sits inside
    # "Weekday". So the Friday-night effect that is plainly visible in the rail
    # data CANNOT be isolated for bus. This is a data limitation to state in
    # Chapter 3, not an analytical choice, and it means the two modes cannot be
    # compared symmetrically on Friday behaviour.
    return profile_from_long(long, "lsoa", labels)


def rail_profiles(labels: pd.DataFrame) -> pd.DataFrame:
    long = pd.read_parquet(
        C.FYP / "analysis" / "01_data_preparation" / "rail" / "outputs" / "preprocessed"
        / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
    )
    long["NLC"] = long["NLC"].astype(str).str.strip()
    # Uniform 18:00-05:00 window for every day type, matching the clustering's
    # own feature construction since the 2026-08-02 padded-window adoption
    # (analysis/02_mode_specific_clustering/rail/src/02_build_features_allmodes.py). Before that date
    # MON/TWT/SUN were capped at 01:00 because no Night Tube runs those nights;
    # the cap is gone from the model, so it is removed here too. MON/TWT/SUN
    # still carry almost no real activity after ~01:00 -- that is now a
    # (near-)zero tail in the padded window rather than a hard cut-off.
    windows = {"MON": (1080, 1740), "TWT": (1080, 1740), "SUN": (1080, 1740),
               "FRI": (1080, 1740), "SAT": (1080, 1740)}
    keep = np.zeros(len(long), dtype=bool)
    for day_type, (start, end) in windows.items():
        keep |= (long["day_type"] == day_type) & long["extended_minute"].between(start, end - 1)
    long = long.loc[keep].copy()
    long["hour_bin"] = (long["extended_minute"] // 60) * 60
    profiles = profile_from_long(long, "NLC", labels)

    # MON/TWT/SUN have no real service past ~01:00, so no rows exist there at
    # all -- reindex to the full uniform window and fill with 0 so the curve
    # draws a flat tail out to 05:00 instead of stopping with a blank gap.
    hour_bins = list(range(1080, 1740, 60))
    day_types = sorted(windows)
    directions = ["entry", "exit"]
    clusters = sorted(profiles["cluster"].unique())
    full_index = pd.MultiIndex.from_product(
        [clusters, day_types, directions, hour_bins],
        names=["cluster", "day_type", "direction", "hour_bin"],
    )
    profiles = (
        profiles.set_index(["cluster", "day_type", "direction", "hour_bin"])
        .reindex(full_index, fill_value=0.0)
        .reset_index()
    )
    return profiles


def zscores(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = {}
    for column in columns:
        series = frame[column]
        out[column] = (
            frame.groupby("cluster", observed=True)[column].mean() - series.mean()
        ) / series.std()
    return pd.DataFrame(out)


def clock(minute: int) -> str:
    return f"{int(minute // 60) % 24:02d}"


def build(mode: str) -> None:
    names = C.BUS_CLUSTER_NAMES if mode == "bus" else C.RAIL_CLUSTER_NAMES
    variables = pd.read_csv(C.DATA_OUT / f"{mode}_variables.csv")

    if mode == "bus":
        labels = variables[["lsoa", "cluster"]]
        profiles = bus_profiles(labels)
        metrics_source = pd.read_csv(
            C.FYP / "analysis" / "03_lnwc_context" / "outputs" / "data" / "bus_unit_metrics.csv"
        )
        # Both tables carry their own `cluster`; drop the incoming one so the
        # merge does not rename ours to cluster_x and break the groupby.
        metrics_source = metrics_source.drop(columns=["cluster"], errors="ignore")
        metrics = variables[["lsoa", "cluster"]].merge(metrics_source, on="lsoa", how="left")
        first, second = "boardings", "alightings"
    else:
        labels = variables[["NLC", "cluster"]].copy()
        labels["NLC"] = labels["NLC"].astype(str).str.strip()
        profiles = rail_profiles(labels)
        metrics_source = pd.read_csv(
            C.FYP / "analysis" / "03_lnwc_context" / "outputs" / "data" / "rail_unit_metrics.csv"
        )
        metrics_source["NLC"] = metrics_source["NLC"].astype(str).str.strip()
        metrics_source = metrics_source.drop(columns=["cluster"], errors="ignore")
        metrics = labels.merge(metrics_source, on="NLC", how="left")
        first, second = "entry", "exit"

    behaviour_z = zscores(metrics, [m for m in BEHAVIOUR_METRICS[mode] if m in metrics.columns])
    context_z = zscores(variables, C.ANALYSIS_VARIABLES)

    # Friday and Saturday kept apart on the user's suggestion (2026-08-01): some
    # stations change function at the weekend, and Friday is a working day that
    # ends in going out whereas Saturday is leisure throughout.
    day_groups = (["Weekday", "Saturday", "Sunday"] if mode == "bus"
                  else ["TWT", "FRI", "SAT"])
    n_days = len(day_groups)
    clusters = sorted(names)
    fig, axes = plt.subplots(
        len(clusters), n_days + 2, figsize=(4.4 * n_days + 8.0, 2.9 * len(clusters)),
        gridspec_kw={"width_ratios": [1.15] * n_days + [0.95, 1.2]},
    )
    axes = np.atleast_2d(axes)
    # Shared y-limit across every curve panel so the weekday/weekend and
    # between-cluster comparisons are visual, not arithmetic.
    ymax = profiles["share"].max() * 100 * 1.08

    for row, cluster in enumerate(clusters):
        colour = C.cluster_colours(mode)[cluster % len(C.cluster_colours(mode))]
        n_units = int((variables["cluster"] == cluster).sum())
        subset = profiles.loc[profiles["cluster"] == cluster]

        # --- curve panels: one per day type, entry/exit kept apart ---
        for column, day_group in enumerate(day_groups):
            ax = axes[row, column]
            piece_all = subset.loc[subset["day_type"] == day_group]
            for direction, style in ((first, "-"), (second, "--")):
                piece = piece_all.loc[piece_all["direction"] == direction].sort_values("hour_bin")
                ax.plot(piece["hour_bin"], piece["share"] * 100, style, color=colour,
                        linewidth=1.9, label=direction)
            ax.axvline(1440, color="#888888", linewidth=0.8, linestyle=":")
            ticks = list(range(1080, 1741, 120))
            ax.set_xticks(ticks)
            ax.set_xticklabels([clock(t) for t in ticks], fontsize=7)
            ax.set_ylim(0, ymax)
            ax.grid(alpha=0.25)
            ax.tick_params(labelsize=7)
            if column == 0:
                ax.set_ylabel("% of unit's\nweek total", fontsize=7)
                ax.legend(fontsize=7, frameon=False, loc="upper right")
                # Wrap the cluster name onto its own line(s) so long names
                # (e.g. C2, C4) don't overflow past this column's width and
                # collide with the next column's "FRI"/"SAT" title.
                wrapped_name = textwrap.fill(f"{names[cluster]}  (n={n_units:,})", width=34)
                ax.set_title(f"{wrapped_name}\n{day_group}",
                             fontsize=9, loc="left", color=colour, fontweight="bold")
            else:
                ax.set_yticklabels([])
                ax.set_title(day_group, fontsize=9, loc="left", color=colour)

        # --- bar panels: z-scores, shared reading ---
        for column, (ax_, table, labeller, title) in enumerate((
            (axes[row, n_days], behaviour_z, METRIC_LABEL, "night behaviour"),
            (axes[row, n_days + 1], context_z, VARIABLE_LABEL, "area context"),
        ), start=n_days):
            values = table.loc[cluster]
            positions = np.arange(len(values))[::-1]
            ax_.barh(positions, values.to_numpy(),
                     color=[POSITIVE if v > 0 else NEGATIVE for v in values],
                     height=0.68)
            ax_.axvline(0, color="black", linewidth=0.8)
            ax_.set_yticks(positions)
            ax_.set_yticklabels([labeller.get(i, i) for i in values.index], fontsize=7)
            ax_.set_xlim(-1.15, 1.15)
            ax_.grid(axis="x", alpha=0.25)
            ax_.tick_params(labelsize=7)
            if row == 0:
                ax_.set_title(title + "  (z vs mode mean)", fontsize=9, loc="left")

        if row == len(clusters) - 1:
            for column in range(n_days):
                axes[row, column].set_xlabel(
                    "hour (extended clock, dotted = midnight)", fontsize=7
                )

    note = (
        "bus: BUSTO has no separate Friday — it sits inside 'Weekday', so Friday-night "
        "behaviour cannot be isolated for this mode"
        if mode == "bus"
        else "rail: uniform 18:00–05:00 window applied to every day type; MON/TWT/SUN "
             "carry almost no activity after ~01:00 (no Night Tube service)"
    )
    fig.suptitle(
        f"{mode.upper()} clusters — night rhythm by day type, behaviour and context\n"
        f"curves share a week-long denominator, so panel heights are comparable · {note}",
        fontsize=11, y=0.997,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    path = C.FIGURE_OUT / f"{mode}_cluster_panels.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path.name}")


def main() -> None:
    for mode in ("bus", "rail"):
        build(mode)


if __name__ == "__main__":
    main()
