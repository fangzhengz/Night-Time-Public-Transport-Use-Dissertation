"""Figures: cluster profile heatmap, boxplots, correlation matrix.

Three views of the same variable table, each answering a different question:

  heatmap        -- which cluster is high or low on which variable, all at once.
                    The BtC-style figure: z-scores coloured, BH-corrected
                    significance starred. This is what cluster naming rests on.
  boxplots       -- the actual distributions behind the strongest variables.
                    A heatmap cell shows a mean shift; a boxplot shows whether
                    the groups genuinely separate or merely have different
                    centres inside heavily overlapping spreads.
  correlation    -- how far the variables duplicate each other. With 31
                    variables, several by construction near-collinear (the four
                    age bands sum to 1; private + social renting are two thirds
                    of a composition), this decides how much of the heatmap is
                    independent evidence and how much is the same signal
                    repeated.

Variables are drawn in themed blocks with separators, so the heatmap can be
read as "deprivation says X, housing says Y, facilities say Z" rather than as
an unordered list.
"""

from __future__ import annotations

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

import config as C

# (block label, variables). Order here is the order everywhere.
# Updated 2026-08 alongside the ANALYSIS_VARIABLES change in config.py -- see
# that list's own comment for why each variable is here.
BLOCKS = [
    ("Disadvantage", ["imd_education", "imd_health", "deprived_1plus_share"]),
    ("Housing", ["private_rented_share", "social_rented_share"]),
    # Re-added 2026-08-08 alongside their ANALYSIS_VARIABLES re-addition; kept
    # together deliberately -- age_20_34_share is a corroborating, independently
    # -sourced (TS007B) variable for the same "young, carless" profile that
    # no_car_household_share (TS045) measures directly, not a second
    # independent driver (Spearman rho 0.815 bus / 0.893 rail).
    ("Vehicle access & age", ["no_car_household_share", "age_20_34_share"]),
    ("Night labour, residence side (LNWC-aligned)",
     ["accom_food_share", "transport_storage_share", "admin_support_share", "wholesale_retail_share",
      "health_social_share", "manufacturing_share"]),
    # Workplace-side (BRES) pairs were tried and reverted, 2026-08 -- see
    # config.ANALYSIS_VARIABLES's "WORKPLACE-SIDE (BRES) TRIAL" comment.
    ("Ethnicity", ["asian_share", "black_share"]),
    ("Household & work", ["dependent_children_share", "unemployed_share"]),
    ("Facilities", ["log1p_poi_count", "shannon_group"]),
    ("Control", ["population_density"]),
]

PRETTY = {
    "imd_income": "IMD income", "imd_employment": "IMD employment",
    "imd_education": "IMD education", "imd_health": "IMD health",
    "imd_living_env": "IMD living environment",
    "deprived_1plus_share": "Deprived in 1+ dimension",
    "deprived_2plus_share": "Deprived in 2+ dimensions",
    "private_rented_share": "Private rented", "social_rented_share": "Social rented",
    "no_car_household_share": "No car/van household",
    "asian_share": "Asian", "black_share": "Black",
    "dependent_children_share": "Households with dependent children",
    "lone_parent_dependent_share": "Lone parent, dependent children",
    "one_person_share": "One-person household",
    "age_0_19_share": "Aged 0-19", "age_20_34_share": "Aged 20-34",
    "age_35_64_share": "Aged 35-64", "age_65plus_share": "Aged 65+",
    "self_employed_share": "Self-employed",
    "part_time_employee_share": "Part-time employee",
    "unemployed_share": "Unemployed",
    "log1p_poi_count": "POI count (log1p)",
    "shannon_group": "POI diversity (Shannon H)",
    "night_industry_share": "Night industries (residence)",
    "hospitality_industry_share": "Hospitality workers (residence)",
    "shiftwork_industry_share": "Shift-work sectors (residence)",
    "accom_food_share": "Accommodation & food (res.)",
    "transport_storage_share": "Transport & storage (res.)",
    "admin_support_share": "Admin & support services (res.)",
    "wholesale_retail_share": "Wholesale & retail (res.)",
    "health_social_share": "Health & social work (res.)",
    "manufacturing_share": "Manufacturing (res.)",
    "public_admin_share": "Public admin. & defence (res.)",
    "population_density": "Population density",
}
for section in C.BRES_SECTIONS:
    PRETTY[f"bres_{section}_share"] = "BRES " + section.replace("_", " ")


def ordered_variables(available: list[str]) -> tuple[list[str], list[tuple[str, int]]]:
    """Flat variable order plus (block label, row index of its first row)."""
    variables, marks = [], []
    for label, members in BLOCKS:
        present = [v for v in members if v in available]
        if not present:
            continue
        marks.append((label, len(variables)))
        variables.extend(present)
    return variables, marks


def draw_heatmap(mode: str) -> None:
    z = pd.read_csv(C.DATA_OUT / f"{mode}_cluster_matrix_z.csv", index_col=0)
    stars = pd.read_csv(C.DATA_OUT / f"{mode}_cluster_matrix_stars.csv", index_col=0).fillna("")
    variables, marks = ordered_variables(list(z.index))
    z = z.reindex(variables)
    stars = stars.reindex(variables).reindex(columns=z.columns).fillna("")

    height = 0.32 * len(variables) + 2.4
    fig, ax = plt.subplots(figsize=(2.1 * len(z.columns) + 4.5, height))
    limit = float(np.nanmax(np.abs(z.to_numpy()))) or 1.0
    norm = TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)
    image = ax.imshow(z.to_numpy(), cmap="RdBu_r", norm=norm, aspect="auto")

    for i in range(z.shape[0]):
        for j in range(z.shape[1]):
            value = z.iat[i, j]
            if not np.isfinite(value):
                continue
            marker = str(stars.iat[i, j])
            text = f"{value:+.2f}" + (f"\n{marker}" if marker else "")
            ax.text(j, i, text, ha="center", va="center", fontsize=7,
                    color="white" if abs(value) > limit * 0.6 else "black")

    ax.set_xticks(range(len(z.columns)))
    # Wrap on character width, not on comma position: several rail cluster
    # names have no comma at all (or use parentheses instead), so a
    # comma-only split left them as one long unwrapped line that overlapped
    # neighbouring columns.
    ax.set_xticklabels([textwrap.fill(c, width=16) for c in z.columns], fontsize=8)
    ax.set_yticks(range(len(variables)))
    ax.set_yticklabels([PRETTY.get(v, v) for v in variables], fontsize=8)

    for _, row in marks[1:]:
        ax.axhline(row - 0.5, color="black", linewidth=1.1)
    for label, row in marks:
        ax.text(-0.62, row - 0.42, label, fontsize=7.5, style="italic",
                color="#444444", ha="left", va="bottom",
                transform=ax.get_yaxis_transform(which="grid"))

    fig.colorbar(image, ax=ax, shrink=0.5, label="z-score vs all units in mode")
    ax.set_title(
        f"{mode.upper()} cluster area-context profile\n"
        "z-score of cluster mean; stars = cluster-vs-rest Mann-Whitney, BH-corrected "
        "(*** p<0.001, ** p<0.01, * p<0.05)",
        fontsize=10, pad=14,
    )
    fig.tight_layout()
    path = C.FIGURE_OUT / f"{mode}_cluster_profile_heatmap.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path.name}")


def draw_boxplots(mode: str, frame: pd.DataFrame, top_n: int = 8) -> None:
    tests = pd.read_csv(C.DATA_OUT / "association_tests.csv")
    tests = tests.loc[tests["mode"] == mode].sort_values("epsilon_squared", ascending=False)
    chosen = [v for v in tests["variable"] if v in frame.columns][:top_n]

    names = C.BUS_CLUSTER_NAMES if mode == "bus" else C.RAIL_CLUSTER_NAMES
    colours = C.cluster_colours(mode)
    clusters = sorted(frame["cluster"].unique())
    # Three columns rather than four: with top_n=8 this leaves one spare grid
    # cell, used for a proper legend box instead of cramming full cluster
    # names into a single crowded line above the whole figure (modelled on
    # Kimani, 2025, MSc dissertation, same department).
    columns = 3
    rows = int(np.ceil((len(chosen) + 1) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(4.2 * columns, 3.6 * rows))
    axes = np.atleast_1d(axes).ravel()

    for ax, variable in zip(axes, chosen):
        data = [frame.loc[frame["cluster"] == c, variable].dropna().to_numpy() for c in clusters]
        parts = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.6,
                           medianprops={"color": "black", "linewidth": 1.3})
        fmt = "{:,.0f}" if variable == "population_density" else "{:.2f}"
        for position, (patch, cluster) in enumerate(zip(parts["boxes"], clusters), start=1):
            patch.set_facecolor(colours[int(cluster) % len(colours)])
            patch.set_alpha(0.85)
            patch.set_edgecolor("#333333")
            mean_value = frame.loc[frame["cluster"] == cluster, variable].mean()
            ax.text(position, 0.95, f"μ={fmt.format(mean_value)}",
                    transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=6.5,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor="#888888", linewidth=0.6))
        eps = tests.loc[tests["variable"] == variable, "epsilon_squared"].iloc[0]
        ax.set_title(f"{PRETTY.get(variable, variable)}\nepsilon²={eps:.3f}", fontsize=9)
        ax.set_xticklabels([f"C{int(c)}" for c in clusters], fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    # Spare grid cell: a proper legend, not a squeezed title line.
    legend_ax = axes[len(chosen)]
    legend_ax.axis("off")
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=colours[int(k) % len(colours)],
                       edgecolor="#333333", alpha=0.85)
        for k, _ in sorted(names.items())
    ]
    labels = [v for _, v in sorted(names.items())]
    legend_ax.legend(handles, labels, loc="center", title=f"{mode.upper()} cluster types",
                      fontsize=8, title_fontsize=9.5, frameon=True)
    for ax in axes[len(chosen) + 1:]:
        ax.set_visible(False)

    fig.suptitle(f"{mode.upper()} — distributions behind the {top_n} strongest variables",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = C.FIGURE_OUT / f"{mode}_boxplots_top{top_n}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path.name}")


def draw_correlation(mode: str, frame: pd.DataFrame) -> None:
    variables, marks = ordered_variables(list(frame.columns))
    corr = frame[variables].corr(method="spearman")
    corr.to_csv(C.DATA_OUT / f"{mode}_variable_correlations.csv")

    size = 0.30 * len(variables) + 3.0
    fig, ax = plt.subplots(figsize=(size, size))
    image = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [PRETTY.get(v, v) for v in variables]
    ax.set_xticks(range(len(variables)))
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_yticks(range(len(variables)))
    ax.set_yticklabels(labels, fontsize=7)
    for _, row in marks[1:]:
        ax.axhline(row - 0.5, color="black", linewidth=0.9)
        ax.axvline(row - 0.5, color="black", linewidth=0.9)
    fig.colorbar(image, ax=ax, shrink=0.6, label="Spearman rho")
    ax.set_title(f"{mode.upper()} — variable correlation matrix\n"
                 "block lines separate themes; strong within-block correlation is "
                 "expected (compositional), strong across-block is duplication",
                 fontsize=10, pad=12)
    fig.tight_layout()
    path = C.FIGURE_OUT / f"{mode}_correlation_matrix.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Flag the pairs worth knowing about before reading the heatmap.
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    strong = upper[upper.abs() > 0.8].sort_values(key=abs, ascending=False)
    print(f"Wrote {path.name}  ({len(strong)} variable pairs with |rho| > 0.8)")
    for (a, b), value in strong.head(8).items():
        print(f"    {value:+.2f}  {a}  <->  {b}")


def main() -> None:
    bus = pd.read_csv(C.DATA_OUT / "bus_variables.csv")
    rail = pd.read_csv(C.DATA_OUT / "rail_variables.csv")
    for mode, frame in (("bus", bus), ("rail", rail)):
        print(f"\n--- {mode} ---")
        draw_heatmap(mode)
        draw_boxplots(mode, frame)
        draw_correlation(mode, frame)


if __name__ == "__main__":
    main()
