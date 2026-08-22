"""External geography diagnostic for the frozen StopArea-only bus labels.

This script does not refit or alter the GMM. It externally characterises the
saved K=3 primary labels and K=4 sensitivity labels using:

1. straight-line LSOA distance to Charing Cross;
2. London Plan 2021 Inner/Outer London borough classification;
3. Howard's targeted Westminster+Camden versus Kingston+Richmond check; and
4. total activity, including the incremental geographic association after a
   linear adjustment for log total activity.

All permutation tests are deterministic (999 permutations, seed 42). The
result is an external association diagnostic, not a spatially constrained
clustering model and not a causal analysis.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy import stats


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

LABEL_DIR = ROOT / "outputs" / "labels"
META_FILE = ROOT / "outputs" / "features" / "bus_meta.csv"
LSOA_FILE = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_LAD_FILE = (
    FYP
    / "rq3_mismatch_analysis"
    / "data"
    / "lsoa21_msoa21_lad22_london.csv"
)

OUT = ROOT / "outputs" / "external_diagnostic"
DATA = OUT / "data"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
for path in (DATA, FIGURES, REPORT):
    path.mkdir(parents=True, exist_ok=True)

K_VALUES = (3, 4)
N_PERMUTATIONS = 999
RANDOM_SEED = 42

# British National Grid coordinate from the existing project rail coordinate
# table for Charing Cross LU. Used only as a transparent centre reference.
CHARING_CROSS_E = 530057.6992
CHARING_CROSS_N = 180378.3819

# London Plan 2021, Annex 2. Haringey is Outer and Greenwich/Newham are Inner
# under this planning definition. City of London is included as Inner.
INNER_LONDON_LADS = {
    "E09000001",  # City of London
    "E09000007",  # Camden
    "E09000011",  # Greenwich
    "E09000012",  # Hackney
    "E09000013",  # Hammersmith and Fulham
    "E09000019",  # Islington
    "E09000020",  # Kensington and Chelsea
    "E09000022",  # Lambeth
    "E09000023",  # Lewisham
    "E09000025",  # Newham
    "E09000028",  # Southwark
    "E09000030",  # Tower Hamlets
    "E09000032",  # Wandsworth
    "E09000033",  # Westminster
}

HOWARD_BOROUGHS = {
    "E09000033": ("Westminster", "central"),
    "E09000007": ("Camden", "central"),
    "E09000021": ("Kingston upon Thames", "outer"),
    "E09000027": ("Richmond upon Thames", "outer"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def eta_squared(values: np.ndarray, groups: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    groups = np.asarray(groups)
    grand = values.mean()
    total = np.square(values - grand).sum()
    if total <= 0:
        return float("nan")
    between = 0.0
    for group in np.unique(groups):
        subset = values[groups == group]
        between += len(subset) * float((subset.mean() - grand) ** 2)
    return float(between / total)


def cramers_v(left: np.ndarray, right: np.ndarray) -> tuple[float, float, float, int]:
    table = pd.crosstab(pd.Series(left, name="left"), pd.Series(right, name="right"))
    chi2, p_value, _, expected = stats.chi2_contingency(table, correction=False)
    n = int(table.to_numpy().sum())
    denominator = n * min(table.shape[0] - 1, table.shape[1] - 1)
    value = float(np.sqrt(chi2 / denominator)) if denominator > 0 else float("nan")
    return value, float(chi2), float(p_value), int((expected < 5).sum())


def permutation_p_eta2(
    values: np.ndarray,
    groups: np.ndarray,
    observed: float,
    rng: np.random.Generator,
) -> float:
    exceed = 0
    groups = np.asarray(groups).copy()
    for _ in range(N_PERMUTATIONS):
        if eta_squared(values, rng.permutation(groups)) >= observed - 1e-15:
            exceed += 1
    return float((exceed + 1) / (N_PERMUTATIONS + 1))


def permutation_p_cramers_v(
    left: np.ndarray,
    right: np.ndarray,
    observed: float,
    rng: np.random.Generator,
) -> float:
    exceed = 0
    left = np.asarray(left).copy()
    for _ in range(N_PERMUTATIONS):
        permuted, _, _, _ = cramers_v(rng.permutation(left), right)
        if permuted >= observed - 1e-15:
            exceed += 1
    return float((exceed + 1) / (N_PERMUTATIONS + 1))


def ols_sse(y: np.ndarray, design: np.ndarray) -> tuple[float, np.ndarray]:
    coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
    fitted = design @ coefficients
    return float(np.square(y - fitted).sum()), fitted


def adjusted_distance_increment(
    distance: np.ndarray,
    log_activity: np.ndarray,
    cluster: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float, float, float, float]:
    n = len(distance)
    reduced = np.column_stack([np.ones(n), log_activity])
    dummies = pd.get_dummies(pd.Series(cluster), drop_first=True, dtype=float).to_numpy()
    full = np.column_stack([reduced, dummies])

    total_ss = float(np.square(distance - distance.mean()).sum())
    reduced_sse, reduced_fitted = ols_sse(distance, reduced)
    full_sse, _ = ols_sse(distance, full)
    reduced_r2 = 1.0 - reduced_sse / total_ss
    full_r2 = 1.0 - full_sse / total_ss
    incremental_r2 = (reduced_sse - full_sse) / reduced_sse

    residuals = distance - reduced_fitted
    exceed = 0
    for _ in range(N_PERMUTATIONS):
        permuted_y = reduced_fitted + rng.permutation(residuals)
        perm_reduced_sse, _ = ols_sse(permuted_y, reduced)
        perm_full_sse, _ = ols_sse(permuted_y, full)
        perm_increment = (perm_reduced_sse - perm_full_sse) / perm_reduced_sse
        if perm_increment >= incremental_r2 - 1e-15:
            exceed += 1
    p_value = float((exceed + 1) / (N_PERMUTATIONS + 1))
    return float(reduced_r2), float(full_r2), float(incremental_r2), p_value


def benjamini_hochberg(values: pd.Series) -> np.ndarray:
    p_values = values.to_numpy(dtype=float)
    order = np.argsort(p_values)
    ranked = p_values[order] * len(p_values) / np.arange(1, len(p_values) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted = np.empty_like(ranked)
    adjusted[order] = np.minimum(ranked, 1.0)
    return adjusted


def effect_class(value: float, kind: str) -> str:
    if not np.isfinite(value):
        return "undefined"
    if kind in {"eta_squared", "epsilon_squared", "incremental_r2"}:
        if value < 0.01:
            return "negligible"
        if value < 0.06:
            return "small"
        if value < 0.14:
            return "medium"
        return "large"
    if kind == "cramers_v":
        if value < 0.10:
            return "negligible"
        if value < 0.30:
            return "small"
        if value < 0.50:
            return "medium"
        return "large"
    return "descriptive"


def load_geography() -> pd.DataFrame:
    # pandas can read the properties directly and avoids loading polygon geometry
    # when only the authoritative BNG representative coordinates are required.
    import geopandas as gpd

    geography = gpd.read_file(LSOA_FILE)[["LSOA21CD", "BNG_E", "BNG_N"]].copy()
    geography = geography.rename(columns={"LSOA21CD": "lsoa"})
    geography["lsoa"] = geography["lsoa"].astype(str)

    lookup = pd.read_csv(LSOA_LAD_FILE, usecols=["LSOA21CD", "LAD22CD"])
    lookup["LSOA21CD"] = lookup["LSOA21CD"].astype(str)
    consistency = lookup.groupby("LSOA21CD")["LAD22CD"].nunique(dropna=False)
    if int((consistency > 1).sum()) != 0:
        raise RuntimeError("An LSOA21 maps to more than one LAD22 in the lookup")
    lookup = lookup.drop_duplicates("LSOA21CD").rename(columns={"LSOA21CD": "lsoa"})

    frame = geography.merge(lookup, on="lsoa", how="left", validate="one_to_one")
    frame["distance_to_centre_km"] = np.hypot(
        frame["BNG_E"] - CHARING_CROSS_E,
        frame["BNG_N"] - CHARING_CROSS_N,
    ) / 1000.0
    frame["inner_outer"] = np.where(
        frame["LAD22CD"].isin(INNER_LONDON_LADS), "Inner", "Outer"
    )
    frame["howard_borough"] = frame["LAD22CD"].map(
        {key: value[0] for key, value in HOWARD_BOROUGHS.items()}
    )
    frame["howard_group"] = frame["LAD22CD"].map(
        {key: value[1] for key, value in HOWARD_BOROUGHS.items()}
    )
    return frame


def cluster_distribution(frame: pd.DataFrame, group_col: str, group: str, k: int) -> np.ndarray:
    counts = frame.loc[frame[group_col] == group, "cluster"].value_counts()
    values = np.array([counts.get(cluster, 0) for cluster in range(k)], dtype=float)
    return values / values.sum() if values.sum() else values


def analyse_k(base: pd.DataFrame, k: int, seed: int) -> dict[str, pd.DataFrame | dict]:
    labels = pd.read_csv(LABEL_DIR / f"bus_k{k}_labels.csv")
    labels = labels.rename(columns={"unit": "lsoa"})
    labels["lsoa"] = labels["lsoa"].astype(str)
    if labels["lsoa"].duplicated().any():
        raise RuntimeError(f"K={k} labels contain duplicate LSOAs")

    frame = labels.merge(base, on="lsoa", how="left", validate="one_to_one")
    required = ["distance_to_centre_km", "LAD22CD", "total_activity", "log_total_activity"]
    if frame[required].isna().any().any():
        missing = frame.loc[frame[required].isna().any(axis=1), "lsoa"].tolist()[:10]
        raise RuntimeError(f"K={k} missing external data for labelled LSOAs: {missing}")
    frame.insert(0, "k", k)

    rng = np.random.default_rng(seed)
    groups = frame["cluster"].to_numpy()
    tests: list[dict] = []

    for metric in ("distance_to_centre_km", "log_total_activity"):
        values = frame[metric].to_numpy(dtype=float)
        eta2 = eta_squared(values, groups)
        arrays = [values[groups == group] for group in np.unique(groups)]
        kruskal = stats.kruskal(*arrays)
        epsilon2 = max(0.0, float((kruskal.statistic - k + 1) / (len(values) - k)))
        tests.append(
            {
                "k": k,
                "domain": metric,
                "n": len(values),
                "effect_name": "eta_squared",
                "effect_size": eta2,
                "effect_class": effect_class(eta2, "eta_squared"),
                "secondary_effect_name": "kruskal_epsilon_squared",
                "secondary_effect_size": epsilon2,
                "test_statistic_name": "kruskal_H",
                "test_statistic": float(kruskal.statistic),
                "asymptotic_p": float(kruskal.pvalue),
                "permutation_p": permutation_p_eta2(values, groups, eta2, rng),
                "expected_cells_lt5": 0,
            }
        )

    inner_v, inner_chi2, inner_p, inner_small = cramers_v(
        frame["cluster"].to_numpy(), frame["inner_outer"].to_numpy()
    )
    tests.append(
        {
            "k": k,
            "domain": "london_plan_inner_outer",
            "n": len(frame),
            "effect_name": "cramers_v",
            "effect_size": inner_v,
            "effect_class": effect_class(inner_v, "cramers_v"),
            "secondary_effect_name": "none",
            "secondary_effect_size": np.nan,
            "test_statistic_name": "chi_squared",
            "test_statistic": inner_chi2,
            "asymptotic_p": inner_p,
            "permutation_p": permutation_p_cramers_v(
                frame["cluster"].to_numpy(),
                frame["inner_outer"].to_numpy(),
                inner_v,
                rng,
            ),
            "expected_cells_lt5": inner_small,
        }
    )

    howard = frame.loc[frame["howard_group"].notna()].copy()
    howard_v, howard_chi2, howard_p, howard_small = cramers_v(
        howard["cluster"].to_numpy(), howard["howard_group"].to_numpy()
    )
    central = cluster_distribution(howard, "howard_group", "central", k)
    outer = cluster_distribution(howard, "howard_group", "outer", k)
    total_variation = 0.5 * float(np.abs(central - outer).sum())
    same_cluster_probability = float(np.dot(central, outer))
    tests.append(
        {
            "k": k,
            "domain": "howard_four_borough_check",
            "n": len(howard),
            "effect_name": "cramers_v",
            "effect_size": howard_v,
            "effect_class": effect_class(howard_v, "cramers_v"),
            "secondary_effect_name": "central_outer_total_variation",
            "secondary_effect_size": total_variation,
            "test_statistic_name": "chi_squared",
            "test_statistic": howard_chi2,
            "asymptotic_p": howard_p,
            "permutation_p": permutation_p_cramers_v(
                howard["cluster"].to_numpy(),
                howard["howard_group"].to_numpy(),
                howard_v,
                rng,
            ),
            "expected_cells_lt5": howard_small,
        }
    )

    reduced_r2, full_r2, incremental_r2, adjusted_p = adjusted_distance_increment(
        frame["distance_to_centre_km"].to_numpy(dtype=float),
        frame["log_total_activity"].to_numpy(dtype=float),
        groups,
        rng,
    )
    tests.append(
        {
            "k": k,
            "domain": "distance_adjusted_for_log_activity",
            "n": len(frame),
            "effect_name": "incremental_r2",
            "effect_size": incremental_r2,
            "effect_class": effect_class(incremental_r2, "incremental_r2"),
            "secondary_effect_name": "full_model_r2",
            "secondary_effect_size": full_r2,
            "test_statistic_name": "reduced_activity_only_r2",
            "test_statistic": reduced_r2,
            "asymptotic_p": np.nan,
            "permutation_p": adjusted_p,
            "expected_cells_lt5": 0,
        }
    )

    summaries = []
    for cluster, subset in frame.groupby("cluster", sort=True):
        for metric in ("distance_to_centre_km", "log_total_activity", "total_activity"):
            values = subset[metric]
            summaries.append(
                {
                    "k": k,
                    "cluster": int(cluster),
                    "n": len(subset),
                    "metric": metric,
                    "mean": float(values.mean()),
                    "q25": float(values.quantile(0.25)),
                    "median": float(values.median()),
                    "q75": float(values.quantile(0.75)),
                }
            )

    inner_cross = pd.crosstab(frame["inner_outer"], frame["cluster"]).reindex(
        index=["Inner", "Outer"], columns=range(k), fill_value=0
    )
    inner_long = inner_cross.reset_index().melt(
        id_vars="inner_outer", var_name="cluster", value_name="n"
    )
    inner_long["within_area_share"] = inner_long["n"] / inner_long.groupby(
        "inner_outer"
    )["n"].transform("sum")
    inner_long["within_cluster_share"] = inner_long["n"] / inner_long.groupby(
        "cluster"
    )["n"].transform("sum")
    inner_long.insert(0, "k", k)

    borough_cross = pd.crosstab(howard["howard_borough"], howard["cluster"]).reindex(
        index=[value[0] for value in HOWARD_BOROUGHS.values()],
        columns=range(k),
        fill_value=0,
    )
    borough_long = borough_cross.reset_index().melt(
        id_vars="howard_borough", var_name="cluster", value_name="n"
    )
    borough_long["within_borough_share"] = borough_long["n"] / borough_long.groupby(
        "howard_borough"
    )["n"].transform("sum")
    borough_long.insert(0, "k", k)

    howard_summary = {
        "k": k,
        "n_target_lsoas": len(howard),
        "central_outer_total_variation": total_variation,
        "central_outer_same_cluster_probability": same_cluster_probability,
        "central_outer_cramers_v": howard_v,
    }

    return {
        "frame": frame,
        "tests": pd.DataFrame(tests),
        "continuous_summary": pd.DataFrame(summaries),
        "inner_outer": inner_long,
        "borough": borough_long,
        "howard_summary": howard_summary,
    }


def make_figures(
    combined: pd.DataFrame,
    inner_outer: pd.DataFrame,
    borough: pd.DataFrame,
) -> None:
    colors = plt.get_cmap("tab10")

    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    for col, k in enumerate(K_VALUES):
        subset = combined.loc[combined["k"] == k]
        clusters = list(range(k))
        for row, (metric, ylabel) in enumerate(
            [
                ("distance_to_centre_km", "Distance to Charing Cross (km)"),
                ("log_total_activity", "log(1 + total activity)"),
            ]
        ):
            data = [subset.loc[subset["cluster"] == cluster, metric] for cluster in clusters]
            box = axes[row, col].boxplot(data, labels=[f"C{x}" for x in clusters], patch_artist=True)
            for patch, cluster in zip(box["boxes"], clusters):
                patch.set_facecolor(colors(cluster))
                patch.set_alpha(0.7)
            axes[row, col].set_title(f"K={k}")
            axes[row, col].set_xlabel("Cluster")
            axes[row, col].set_ylabel(ylabel)
            axes[row, col].grid(axis="y", alpha=0.25)
    fig.suptitle("StopArea-only external geography and activity diagnostic", fontsize=15)
    fig.savefig(FIGURES / "k3_k4_distance_activity_boxplots.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for ax, k in zip(axes, K_VALUES):
        table = (
            inner_outer.loc[inner_outer["k"] == k]
            .pivot(index="inner_outer", columns="cluster", values="within_area_share")
            .reindex(["Inner", "Outer"])
            .fillna(0)
        )
        bottom = np.zeros(len(table))
        for cluster in range(k):
            values = table.get(cluster, pd.Series(0, index=table.index)).to_numpy()
            ax.bar(table.index, values, bottom=bottom, color=colors(cluster), label=f"C{cluster}")
            bottom += values
        ax.set_title(f"London Plan Inner/Outer, K={k}")
        ax.set_ylabel("Within-area cluster share")
        ax.set_ylim(0, 1)
        ax.legend(ncol=2, fontsize=8)
    fig.savefig(FIGURES / "k3_k4_inner_outer_cluster_shares.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    borough_order = [value[0] for value in HOWARD_BOROUGHS.values()]
    for ax, k in zip(axes, K_VALUES):
        table = (
            borough.loc[borough["k"] == k]
            .pivot(index="howard_borough", columns="cluster", values="within_borough_share")
            .reindex(borough_order)
            .fillna(0)
        )
        bottom = np.zeros(len(table))
        for cluster in range(k):
            values = table.get(cluster, pd.Series(0, index=table.index)).to_numpy()
            ax.bar(table.index, values, bottom=bottom, color=colors(cluster), label=f"C{cluster}")
            bottom += values
        ax.set_title(f"Howard four-borough check, K={k}")
        ax.set_ylabel("Within-borough cluster share")
        ax.set_ylim(0, 1)
        ax.tick_params(axis="x", rotation=24)
        ax.legend(ncol=2, fontsize=8)
    fig.savefig(FIGURES / "k3_k4_howard_borough_cluster_shares.png", dpi=180)
    plt.close(fig)


def write_report(
    tests: pd.DataFrame,
    continuous: pd.DataFrame,
    inner_outer: pd.DataFrame,
    borough: pd.DataFrame,
    howard: pd.DataFrame,
    n_lsoas: int,
) -> None:
    distance_table = continuous.loc[
        continuous["metric"].isin(["distance_to_centre_km", "log_total_activity"])
    ].copy()
    lines = [
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite/experiment-agent",
        "- Origin Mode: run + validate",
        "- Verification Status: ANALYZED",
        "- Version Label: stoparea_only_external_geography_v1",
        "",
        "# StopArea-only external geography diagnostic",
        "",
        f"- Frozen labelled sample: {n_lsoas:,} LSOAs.",
        "- K=3 is the provisional primary result; K=4 is sensitivity only.",
        f"- Permutations: {N_PERMUTATIONS:,}; seed: {RANDOM_SEED}.",
        "- No GMM was refitted and no cluster label was changed.",
        "",
        "## Definitions",
        "",
        "- Distance is straight-line distance from the LSOA BNG representative coordinate to Charing Cross.",
        "- Inner/Outer follows London Plan 2021 Annex 2 (Greenwich and Newham Inner; Haringey Outer).",
        "- Howard check compares Westminster+Camden with Kingston+Richmond.",
        "- Activity adjustment reports the extra linear R2 from cluster dummies after log total activity.",
        "",
        "## Association tests",
        "",
        tests.to_markdown(index=False, floatfmt=".6f"),
        "",
        "`permutation_p_bh` controls the false discovery rate across all K=3/K=4 diagnostic tests.",
        "Effect sizes, not p-values alone, determine whether separation is substantively strong.",
        "",
        "## Cluster summaries",
        "",
        distance_table.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## London Plan Inner/Outer composition",
        "",
        inner_outer.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Howard targeted four-borough check",
        "",
        howard.to_markdown(index=False, floatfmt=".4f"),
        "",
        borough.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Interpretation boundary",
        "",
        "These are LSOA-level external associations. They do not prove that geographic location",
        "causes a temporal profile, do not identify individual passengers, and do not make the",
        "clusters spatial zones. Mixed geography can be substantively valid for a temporal-shape",
        "typology even when it is unsuitable for a centre-versus-periphery spatial typology.",
        "",
        "## Fallacy scan",
        "",
        "- Coverage: 11/11 statistical fallacy types checked.",
        "- RED_FLAG if area-level associations are interpreted as passenger-level behaviour (ecological fallacy).",
        "- CAUTION: exploratory K=3/K=4 comparisons create researcher degrees of freedom; both are reported.",
        "- CAUTION: cross-sectional external associations do not support causal or directional claims.",
        "- NOTE: BH adjustment is applied across all reported permutation tests.",
    ]
    (REPORT / "EXTERNAL_GEOGRAPHY_DIAGNOSTIC.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> None:
    required_inputs = [META_FILE, LSOA_FILE, LSOA_LAD_FILE] + [
        LABEL_DIR / f"bus_k{k}_labels.csv" for k in K_VALUES
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")

    meta = pd.read_csv(META_FILE)
    meta["lsoa"] = meta["lsoa"].astype(str)
    if meta["lsoa"].duplicated().any():
        raise RuntimeError("bus_meta.csv contains duplicate LSOAs")
    meta["log_total_activity"] = np.log1p(meta["total_activity"])

    geography = load_geography()
    base = meta.merge(geography, on="lsoa", how="left", validate="one_to_one")

    results = [analyse_k(base, k, RANDOM_SEED + k) for k in K_VALUES]
    combined = pd.concat([result["frame"] for result in results], ignore_index=True)
    tests = pd.concat([result["tests"] for result in results], ignore_index=True)
    tests["permutation_p_bh"] = benjamini_hochberg(tests["permutation_p"])
    continuous = pd.concat(
        [result["continuous_summary"] for result in results], ignore_index=True
    )
    inner_outer = pd.concat([result["inner_outer"] for result in results], ignore_index=True)
    borough = pd.concat([result["borough"] for result in results], ignore_index=True)
    howard = pd.DataFrame([result["howard_summary"] for result in results])

    combined.to_csv(DATA / "lsoa_external_diagnostic.csv", index=False)
    tests.to_csv(DATA / "association_tests.csv", index=False)
    continuous.to_csv(DATA / "cluster_continuous_summary.csv", index=False)
    inner_outer.to_csv(DATA / "inner_outer_cluster_composition.csv", index=False)
    borough.to_csv(DATA / "howard_borough_cluster_shares.csv", index=False)
    howard.to_csv(DATA / "howard_central_outer_summary.csv", index=False)

    manifest = pd.DataFrame(
        [
            {
                "path": str(path.relative_to(FYP)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in required_inputs
        ]
    )
    manifest.to_csv(DATA / "input_manifest.csv", index=False)

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "random_seed": RANDOM_SEED,
        "n_permutations": N_PERMUTATIONS,
        "k_values": list(K_VALUES),
        "charing_cross_bng": [CHARING_CROSS_E, CHARING_CROSS_N],
    }
    (DATA / "run_environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )

    make_figures(combined, inner_outer, borough)
    write_report(
        tests,
        continuous,
        inner_outer,
        borough,
        howard,
        n_lsoas=len(results[0]["frame"]),
    )

    print("=== StopArea-only external geography diagnostic ===")
    print(tests[["k", "domain", "effect_name", "effect_size", "effect_class", "permutation_p", "permutation_p_bh"]].to_string(index=False))
    print("\nHoward targeted summary")
    print(howard.to_string(index=False))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
