"""External LNWC/IMD characterisation of the current bus CLR K=4 partition.

The script is deterministic and writes only inside ``new_bus_LNWC_IMD_test``.
K=3 is recomputed only as a same-sample sensitivity comparator. No clustering
is refitted and no LSOA is added to or removed from the accepted RQ1 sample.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import seaborn as sns
from matplotlib.patches import Patch
from scipy import stats
from scipy.stats import chi2_contingency, rankdata


START = time.time()
HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent

CLR_ROOT = FYP / "rq1_bus_clr_transform"
K4_LABELS = CLR_ROOT / "outputs" / "labels" / "clr_k4_labels.csv"
K3_LABELS = CLR_ROOT / "outputs" / "labels" / "clr_k3_labels.csv"
RAW_METRICS = CLR_ROOT / "outputs" / "features" / "raw_metrics.csv"
LNWC_INPUT = FYP / "night_time_work_data" / "london_night_workers_classification_data.csv"
LNWC_PORTRAITS = FYP / "night_time_work_data" / "lnwc_variable_dictionary_pen_portaits.csv"
IMD_INPUT = FYP / "IMDdata_2025" / "imd2025_lsoa21_london.csv"
BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

OUT = ROOT / "outputs"
DATA = OUT / "data"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
for directory in (OUT, DATA, FIGURES, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

LNWC_GROUPS = list(range(1, 8))
LNWC_COLOURS = {
    1: "#E78AC3",
    2: "#FFD92F",
    3: "#8DA0CB",
    4: "#66C2A5",
    5: "#FC8D62",
    6: "#A6D854",
    7: "#E5C494",
}
K4_TYPE = {
    0: "Low activity / early-stop",
    1: "High activity / full-night",
    2: "Partial-night transition",
    3: "Medium activity / continuing",
}
K4_ORDER = [1, 3, 2, 0]
K4_COLOURS = {1: "#6A3D9A", 3: "#1F9E89", 2: "#E6AB02", 0: "#3B75AF"}
PRIMARY_METRICS = [
    "total_activity",
    "log_total_activity",
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
    "direction_balance",
    "weekend_ratio",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bh_adjust(values: pd.Series) -> pd.Series:
    p = values.to_numpy(dtype=float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = ranked * len(p) / np.arange(1, len(p) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return pd.Series(result, index=values.index)


def load_labels(path: Path, k: int) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"unit", "cluster"}
    if not required.issubset(frame.columns):
        raise ValueError(f"{path} lacks required columns {sorted(required)}")
    frame = frame[["unit", "cluster"]].rename(columns={"unit": "lsoa21cd"})
    frame["lsoa21cd"] = frame["lsoa21cd"].astype(str)
    frame["cluster"] = frame["cluster"].astype(int)
    if frame["lsoa21cd"].duplicated().any():
        raise ValueError(f"Duplicate LSOA labels in {path}")
    if sorted(frame["cluster"].unique().tolist()) != list(range(k)):
        raise ValueError(f"Unexpected K={k} cluster IDs in {path}")
    return frame


def build_context(labels_path: Path, k: int) -> pd.DataFrame:
    labels = load_labels(labels_path, k)
    metrics = pd.read_csv(RAW_METRICS).rename(columns={"lsoa": "lsoa21cd"})
    metrics["lsoa21cd"] = metrics["lsoa21cd"].astype(str)
    if metrics["lsoa21cd"].duplicated().any():
        raise ValueError("Duplicate LSOAs in CLR raw metrics")
    if set(labels["lsoa21cd"]) != set(metrics["lsoa21cd"]):
        raise ValueError("Labels and raw metrics do not describe the exact same LSOA sample")

    lnwc = pd.read_csv(LNWC_INPUT)[["lsoa21cd", "lnc_grp"]].copy()
    lnwc["lsoa21cd"] = lnwc["lsoa21cd"].astype(str)
    imd = pd.read_csv(IMD_INPUT).copy()
    imd["lsoa21cd"] = imd["lsoa21cd"].astype(str)

    frame = labels.merge(metrics, on="lsoa21cd", validate="one_to_one")
    frame = frame.merge(lnwc, on="lsoa21cd", how="left", validate="one_to_one")
    frame = frame.merge(imd, on="lsoa21cd", how="left", validate="one_to_one")
    if frame[["lnc_grp", "imd_score"]].isna().any().any():
        missing = frame[["lnc_grp", "imd_score"]].isna().sum().to_dict()
        raise ValueError(f"Incomplete context join: {missing}")
    frame["lnc_grp"] = frame["lnc_grp"].astype(int)
    frame["imd_decile_int"] = frame["imd_decile_int"].astype(int)
    if k == 4:
        frame["cluster_type"] = frame["cluster"].map(K4_TYPE)
        frame["cluster_display"] = frame.apply(
            lambda row: f"C{row.cluster}: {row.cluster_type}", axis=1
        )
    return frame


def association_outputs(frame: pd.DataFrame, k: int) -> dict[str, object]:
    observed = pd.crosstab(frame["cluster"], frame["lnc_grp"]).reindex(
        index=range(k), columns=LNWC_GROUPS, fill_value=0
    )
    chi2, p_value, dof, expected_values = chi2_contingency(observed.to_numpy())
    expected = pd.DataFrame(expected_values, index=observed.index, columns=observed.columns)
    row_pct = observed.div(observed.sum(axis=1), axis=0)
    universe = observed.sum(axis=0) / observed.to_numpy().sum()
    enrichment = row_pct.div(universe, axis=1)
    residual = (observed - expected) / np.sqrt(expected)
    n = int(observed.to_numpy().sum())
    denominator = min(observed.shape[0] - 1, observed.shape[1] - 1)
    cramers_v = math.sqrt(float(chi2) / (n * denominator))
    return {
        "observed": observed,
        "expected": expected,
        "row_pct": row_pct,
        "enrichment": enrichment,
        "residual": residual,
        "chi_square": float(chi2),
        "p_value": float(p_value),
        "degrees_of_freedom": int(dof),
        "cramers_v": float(cramers_v),
        "n": n,
        "min_expected": float(expected.to_numpy().min()),
        "cells_expected_lt5": int((expected.to_numpy() < 5).sum()),
        "cells_expected_lt1": int((expected.to_numpy() < 1).sum()),
    }


def kruskal_imd(frame: pd.DataFrame, k: int) -> dict[str, float | int]:
    samples = [frame.loc[frame["cluster"] == cluster, "imd_score"].to_numpy() for cluster in range(k)]
    statistic, p_value = stats.kruskal(*samples)
    n = sum(len(sample) for sample in samples)
    epsilon_squared = max(0.0, (float(statistic) - k + 1) / (n - k))
    return {
        "kruskal_h": float(statistic),
        "degrees_of_freedom": k - 1,
        "p_value": float(p_value),
        "epsilon_squared": float(epsilon_squared),
        "n": int(n),
    }


def dunn_imd(frame: pd.DataFrame) -> pd.DataFrame:
    values = frame["imd_score"].to_numpy(dtype=float)
    groups = frame["cluster"].to_numpy(dtype=int)
    ranks = rankdata(values, method="average")
    n = len(values)
    _, tie_counts = np.unique(values, return_counts=True)
    tie_term = float(np.sum(tie_counts**3 - tie_counts))
    rank_variance = n * (n + 1) / 12.0 - tie_term / (12.0 * (n - 1))
    rows: list[dict[str, float | int]] = []
    for left, right in combinations(sorted(np.unique(groups)), 2):
        mask_left = groups == left
        mask_right = groups == right
        difference = float(ranks[mask_left].mean() - ranks[mask_right].mean())
        denominator = math.sqrt(
            rank_variance * (1.0 / mask_left.sum() + 1.0 / mask_right.sum())
        )
        z_value = difference / denominator
        rows.append(
            {
                "cluster_a": int(left),
                "cluster_b": int(right),
                "median_a": float(np.median(values[mask_left])),
                "median_b": float(np.median(values[mask_right])),
                "mean_rank_difference_a_minus_b": difference,
                "z": float(z_value),
                "p_value": float(2 * stats.norm.sf(abs(z_value))),
            }
        )
    result = pd.DataFrame(rows)
    result["p_fdr_bh"] = bh_adjust(result["p_value"])
    result["reject_fdr_0_05"] = result["p_fdr_bh"] < 0.05
    return result


def save_matrix(matrix: pd.DataFrame, name: str) -> None:
    matrix.rename_axis(index="cluster", columns="lnwc_group").to_csv(DATA / f"{name}.csv")


def cluster_summary(frame: pd.DataFrame, enrichment: pd.DataFrame, portraits: pd.DataFrame) -> pd.DataFrame:
    names = portraits.set_index("Cluster Group")["Name"].to_dict()
    rows = []
    for cluster in K4_ORDER:
        group = frame.loc[frame["cluster"] == cluster]
        top_lnwc = int(enrichment.loc[cluster].idxmax())
        row: dict[str, object] = {
            "cluster": cluster,
            "cluster_type": K4_TYPE[cluster],
            "n": len(group),
            "share": len(group) / len(frame),
            "top_enriched_lnwc": top_lnwc,
            "top_enriched_lnwc_name": names[top_lnwc],
            "top_enrichment_ratio": float(enrichment.loc[cluster, top_lnwc]),
        }
        for metric in PRIMARY_METRICS + ["imd_score", "imd_decile_int"]:
            row[f"{metric}_median"] = float(group[metric].median())
            row[f"{metric}_q1"] = float(group[metric].quantile(0.25))
            row[f"{metric}_q3"] = float(group[metric].quantile(0.75))
        rows.append(row)
    return pd.DataFrame(rows)


def plot_heatmaps(association: dict[str, object]) -> None:
    labels = [f"C{cluster}  {K4_TYPE[cluster]}" for cluster in range(4)]
    enrichment = association["enrichment"].copy()
    composition = association["row_pct"].copy()
    enrichment.index = labels
    composition.index = labels

    plt.figure(figsize=(11, 5.5))
    sns.heatmap(
        enrichment,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=1,
        linewidths=0.5,
        cbar_kws={"label": "Observed share / sample-wide share"},
    )
    plt.title("Bus CLR K=4: LNWC enrichment")
    plt.xlabel("LNWC group")
    plt.ylabel("Bus cluster")
    plt.tight_layout()
    plt.savefig(FIGURES / "k4_lnwc_enrichment_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(11, 5.5))
    sns.heatmap(
        composition,
        annot=True,
        fmt=".1%",
        cmap="Blues",
        linewidths=0.5,
        cbar_kws={"label": "Within-cluster share"},
    )
    plt.title("Bus CLR K=4: LNWC composition within cluster")
    plt.xlabel("LNWC group")
    plt.ylabel("Bus cluster")
    plt.tight_layout()
    plt.savefig(FIGURES / "k4_lnwc_composition_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close()


def plot_imd(frame: pd.DataFrame) -> None:
    order = [f"C{cluster}: {K4_TYPE[cluster]}" for cluster in K4_ORDER]
    plt.figure(figsize=(11, 6))
    sns.boxplot(
        data=frame,
        x="cluster_display",
        y="imd_score",
        order=order,
        hue="cluster_display",
        palette={f"C{k}: {K4_TYPE[k]}": K4_COLOURS[k] for k in K4_ORDER},
        legend=False,
        showfliers=False,
    )
    plt.title("Bus CLR K=4: IMD 2025 score by cluster")
    plt.xlabel("Bus temporal-activity type")
    plt.ylabel("IMD score (higher = more deprived)")
    plt.xticks(rotation=18, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "k4_imd_score_boxplot.png", dpi=220, bbox_inches="tight")
    plt.close()


def plot_context_map(frame: pd.DataFrame) -> None:
    boundaries = gpd.read_file(BOUNDARIES)
    code = "LSOA21CD" if "LSOA21CD" in boundaries.columns else "lsoa21cd"
    boundaries[code] = boundaries[code].astype(str)
    mapped = boundaries.merge(
        frame[["lsoa21cd", "cluster", "lnc_grp"]],
        left_on=code,
        right_on="lsoa21cd",
        how="left",
        validate="one_to_one",
    )
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    cluster_colour = mapped["cluster"].map(K4_COLOURS).fillna("#EEEEEE")
    mapped.plot(color=cluster_colour, linewidth=0, ax=axes[0])
    axes[0].set_title("Bus CLR K=4 (grey = outside retained sample)")
    axes[0].legend(
        handles=[Patch(facecolor=K4_COLOURS[k], label=f"C{k}: {K4_TYPE[k]}") for k in K4_ORDER],
        loc="lower left",
        fontsize=8,
    )
    lnwc_colour = mapped["lnc_grp"].map(LNWC_COLOURS).fillna("#EEEEEE")
    mapped.plot(color=lnwc_colour, linewidth=0, ax=axes[1])
    axes[1].set_title("London Night Workers Classification")
    axes[1].legend(
        handles=[Patch(facecolor=LNWC_COLOURS[g], label=f"LNWC {g}") for g in LNWC_GROUPS],
        loc="lower left",
        ncol=2,
        fontsize=8,
    )
    for axis in axes:
        axis.set_axis_off()
    plt.tight_layout()
    plt.savefig(FIGURES / "k4_clusters_lnwc_map.png", dpi=220, bbox_inches="tight")
    plt.close()


def plot_k_sensitivity(comparison: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].bar(comparison["K"].astype(str), comparison["lnwc_cramers_v"], color="#4C78A8")
    axes[0].set_title("Cluster × LNWC")
    axes[0].set_ylabel("Cramer's V")
    axes[0].set_xlabel("K")
    axes[1].bar(comparison["K"].astype(str), comparison["imd_epsilon_squared"], color="#F58518")
    axes[1].set_title("Cluster × IMD score")
    axes[1].set_ylabel("Kruskal-Wallis epsilon-squared")
    axes[1].set_xlabel("K")
    fig.suptitle("Same-sample external-characterisation sensitivity")
    plt.tight_layout()
    plt.savefig(FIGURES / "k3_k4_external_effect_sensitivity.png", dpi=220, bbox_inches="tight")
    plt.close()


def format_p(value: float) -> str:
    return f"{value:.3g}" if value >= 0.001 else f"{value:.2e}"


def markdown_cluster_summary(summary: pd.DataFrame) -> list[str]:
    lines = [
        "| Cluster | Type | n | Share | Activity median | Post-midnight median | IMD median | Top LNWC enrichment |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| C{row.cluster} | {row.cluster_type} | {row.n} | {row.share:.1%} | "
            f"{row.total_activity_median:.1f} | {row.post_midnight_share_median:.3f} | "
            f"{row.imd_score_median:.2f} | LNWC {row.top_enriched_lnwc} "
            f"({row.top_enrichment_ratio:.2f}×) |"
        )
    return lines


def markdown_crosswalk(crosswalk: pd.DataFrame) -> list[str]:
    lines = [
        "| K=3 cluster | K4 C0 | K4 C1 | K4 C2 | K4 C3 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for cluster, row in crosswalk.iterrows():
        lines.append(
            f"| C{cluster} | {int(row[0])} | {int(row[1])} | "
            f"{int(row[2])} | {int(row[3])} |"
        )
    return lines


def write_report(
    frame4: pd.DataFrame,
    summary: pd.DataFrame,
    association4: dict[str, object],
    imd4: dict[str, float | int],
    dunn: pd.DataFrame,
    comparison: pd.DataFrame,
    crosswalk: pd.DataFrame,
) -> None:
    generated = datetime.now(timezone.utc).isoformat()
    k3 = comparison.loc[comparison["K"] == 3].iloc[0]
    k4 = comparison.loc[comparison["K"] == 4].iloc[0]
    transition = summary.loc[summary["cluster"] == 2].iloc[0]
    significant_pairs = dunn.loc[dunn["reject_fdr_0_05"]]

    lines = [
        "# Bus CLR K=4 × LNWC / IMD 2025",
        "",
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite / experiment-agent",
        "- Origin Mode: run + validate",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED (see REPRODUCIBILITY_CHECK.md)",
        "- Version Label: bus_clr_k4_context_v1",
        "",
        "## Fixed design and coverage",
        "",
        "- RQ1 input is the accepted CLR K=4 partition; clustering is not refitted here.",
        "- K=3 is a same-sample sensitivity comparator, not an alternative data pipeline.",
        f"- {len(frame4):,}/{len(frame4):,} retained LSOAs matched to both LNWC and IMD 2025.",
        "- LNWC and IMD are external area-context variables and were not used to form the clusters.",
        "",
        "## K=4 cluster context summary",
        "",
    ]
    lines.extend(markdown_cluster_summary(summary))
    lines.extend(
        [
            "",
            "## LNWC association",
            "",
            f"- Chi-square({association4['degrees_of_freedom']})={association4['chi_square']:.2f}, "
            f"p={format_p(association4['p_value'])}, Cramer's V={association4['cramers_v']:.3f}, "
            f"n={association4['n']}.",
            f"- Minimum expected count={association4['min_expected']:.2f}; cells below 5="
            f"{association4['cells_expected_lt5']} and below 1={association4['cells_expected_lt1']}.",
            "- Cramer's V is the primary magnitude summary; chi-square p-values do not account for spatial dependence.",
            "",
            "## IMD association",
            "",
            f"- Kruskal-Wallis H({imd4['degrees_of_freedom']})={imd4['kruskal_h']:.2f}, "
            f"p={format_p(imd4['p_value'])}, epsilon-squared={imd4['epsilon_squared']:.3f}, "
            f"n={imd4['n']}.",
            f"- {len(significant_pairs)}/{len(dunn)} pairwise Dunn comparisons remain below 0.05 after BH correction.",
            "",
            "## Does K=4 add externally distinguishable information?",
            "",
            f"- LNWC effect size: K=3 V={k3.lnwc_cramers_v:.3f}; K=4 V={k4.lnwc_cramers_v:.3f}.",
            f"- IMD effect size: K=3 epsilon-squared={k3.imd_epsilon_squared:.3f}; "
            f"K=4 epsilon-squared={k4.imd_epsilon_squared:.3f}.",
            f"- Transition C2 has median activity={transition.total_activity_median:.1f}, "
            f"post-midnight share={transition.post_midnight_share_median:.3f}, "
            f"IMD score={transition.imd_score_median:.2f}, and its strongest LNWC enrichment is "
            f"group {transition.top_enriched_lnwc} ({transition.top_enrichment_ratio:.2f}×).",
            "- These external comparisons characterise the fourth component; they do not by themselves prove four natural classes.",
            "",
            "## K=3 × K=4 crosswalk",
            "",
        ]
    )
    lines.extend(markdown_crosswalk(crosswalk))
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "1. Results are LSOA-level associations, not evidence about the occupation or deprivation of individual passengers.",
            "2. Neither chi-square nor Kruskal-Wallis corrects for spatial autocorrelation; effect sizes and mapped structure carry more weight than very small p-values.",
            "3. The retained 3,365-LSOA sample excludes low-total and one-direction exception areas, so findings describe the accepted modelling sample rather than every London LSOA.",
            "4. K was explored before this external analysis. K=3 is therefore retained as a transparent sensitivity comparator to reduce post-selection overclaiming.",
            "5. IMD and LNWC are parallel external lenses. They are not fused into the RQ1 cluster definition and should not be read causally.",
            "",
            "## Statistical fallacy scan",
            "",
            "- Coverage: 11/11 checked.",
            "- Material cautions: ecological fallacy, selected-sample/Berkson-type distortion, look-elsewhere/forking paths, spatially dependent inference, correlation-versus-causation and reverse-causality language.",
            "- Not materially implicated by this cross-sectional design: regression to the mean, attrition/survivorship, diagnostic base-rate neglect and collider adjustment (no adjustment model is fitted here).",
        ]
    )
    (REPORT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    results_json = {
        "version": "bus_clr_k4_context_v1",
        "sample_n": len(frame4),
        "k4_cluster_sizes": frame4["cluster"].value_counts().sort_index().to_dict(),
        "lnwc": {key: value for key, value in association4.items() if not isinstance(value, pd.DataFrame)},
        "imd": imd4,
        "k_sensitivity": comparison.to_dict(orient="records"),
    }
    (REPORT / "results_summary.json").write_text(
        json.dumps(results_json, indent=2), encoding="utf-8"
    )


def main() -> None:
    required = [K4_LABELS, K3_LABELS, RAW_METRICS, LNWC_INPUT, LNWC_PORTRAITS, IMD_INPUT, BOUNDARIES]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")

    manifest = pd.DataFrame(
        [
            {"role": path.stem, "path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in required
        ]
    )
    manifest.to_csv(OUT / "input_manifest.csv", index=False)

    frame4 = build_context(K4_LABELS, 4)
    frame3 = build_context(K3_LABELS, 3)
    if frame4["lsoa21cd"].tolist() != frame3["lsoa21cd"].tolist():
        raise ValueError("K=3 and K=4 labels are not aligned to the same ordered sample")
    frame4.to_csv(DATA / "bus_k4_context_lsoa.csv", index=False)

    # The supplied LNWC portrait dictionary is Windows-1252 encoded.
    portraits = pd.read_csv(LNWC_PORTRAITS, encoding="cp1252")
    association_by_k: dict[int, dict[str, object]] = {}
    imd_by_k: dict[int, dict[str, float | int]] = {}
    comparison_rows = []
    for k, frame in [(3, frame3), (4, frame4)]:
        association = association_outputs(frame, k)
        imd = kruskal_imd(frame, k)
        association_by_k[k] = association
        imd_by_k[k] = imd
        comparison_rows.append(
            {
                "K": k,
                "n": len(frame),
                "lnwc_chi_square": association["chi_square"],
                "lnwc_df": association["degrees_of_freedom"],
                "lnwc_p_value": association["p_value"],
                "lnwc_cramers_v": association["cramers_v"],
                "lnwc_min_expected": association["min_expected"],
                "imd_kruskal_h": imd["kruskal_h"],
                "imd_df": imd["degrees_of_freedom"],
                "imd_p_value": imd["p_value"],
                "imd_epsilon_squared": imd["epsilon_squared"],
            }
        )
    comparison = pd.DataFrame(comparison_rows)
    comparison.to_csv(DATA / "k3_k4_external_effect_sensitivity.csv", index=False)

    association4 = association_by_k[4]
    save_matrix(association4["observed"], "k4_lnwc_crosstab_counts")
    save_matrix(association4["expected"], "k4_lnwc_crosstab_expected")
    save_matrix(association4["row_pct"], "k4_lnwc_crosstab_row_pct")
    save_matrix(association4["enrichment"], "k4_lnwc_enrichment")
    save_matrix(association4["residual"], "k4_lnwc_pearson_residuals")
    pd.DataFrame(
        [
            {
                key: value
                for key, value in association4.items()
                if not isinstance(value, pd.DataFrame)
            }
        ]
    ).to_csv(DATA / "k4_lnwc_association.csv", index=False)

    summary = cluster_summary(frame4, association4["enrichment"], portraits)
    summary.to_csv(DATA / "k4_cluster_context_summary.csv", index=False)
    dunn = dunn_imd(frame4)
    dunn.to_csv(DATA / "k4_imd_dunn_pairwise.csv", index=False)
    pd.DataFrame([imd_by_k[4]]).to_csv(DATA / "k4_imd_kruskal.csv", index=False)

    labels3 = frame3[["lsoa21cd", "cluster"]].rename(columns={"cluster": "k3_cluster"})
    labels4 = frame4[["lsoa21cd", "cluster"]].rename(columns={"cluster": "k4_cluster"})
    crosswalk = pd.crosstab(
        labels3.merge(labels4, on="lsoa21cd", validate="one_to_one")["k3_cluster"],
        labels3.merge(labels4, on="lsoa21cd", validate="one_to_one")["k4_cluster"],
    ).reindex(index=range(3), columns=range(4), fill_value=0)
    crosswalk.index.name = "K3"
    crosswalk.columns.name = "K4"
    crosswalk.to_csv(DATA / "k3_k4_crosswalk_counts.csv")

    plot_heatmaps(association4)
    plot_imd(frame4)
    plot_context_map(frame4)
    plot_k_sensitivity(comparison)
    write_report(frame4, summary, association4, imd_by_k[4], dunn, comparison, crosswalk)

    environment = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": time.time() - START,
        "command": "python src\\01_run_bus_context_analysis.py",
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "geopandas": gpd.__version__,
            "matplotlib": matplotlib.__version__,
            "seaborn": sns.__version__,
        },
    }
    (REPORT / "run_environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )
    print(
        f"Completed bus K=4 context analysis in {environment['duration_seconds']:.1f}s; "
        f"n={len(frame4)}, LNWC V={association4['cramers_v']:.3f}, "
        f"IMD epsilon2={imd_by_k[4]['epsilon_squared']:.3f}."
    )


if __name__ == "__main__":
    main()
