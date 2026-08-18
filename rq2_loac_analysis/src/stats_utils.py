"""Shared statistical/plotting helpers for the LOAC association analyses.

Adapted from ``rq2test analysis/src/run_analysis.py``'s LNWC treatment
(``association_outputs``, ``composition_permutation_test``,
``save_matrix``, ``draw_heatmap``, ``top_enrichments``), generalised to take
an arbitrary category list rather than the hardcoded 1-7 LNWC groups, so the
same functions serve both the bus (categorical dominant-Supergroup) and
rail (compositional Supergroup share) tests.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import chi2_contingency


def association_outputs(observed: pd.DataFrame, categories: list):
    observed = observed.reindex(index=sorted(observed.index), columns=categories, fill_value=0)
    chi2, p_value, dof, expected_array = chi2_contingency(observed.to_numpy())
    expected = pd.DataFrame(expected_array, index=observed.index, columns=observed.columns)
    row_pct = observed.div(observed.sum(axis=1), axis=0)
    col_pct = observed.div(observed.sum(axis=0), axis=1)
    universe_share = observed.sum(axis=0) / observed.to_numpy().sum()
    enrichment = row_pct.div(universe_share, axis=1)
    std_residual = (observed - expected) / np.sqrt(expected)
    n = observed.to_numpy().sum()
    denominator = min(observed.shape[0] - 1, observed.shape[1] - 1)
    cramers_v = math.sqrt(chi2 / (n * denominator)) if denominator > 0 else np.nan
    stats = {
        "chi_square": float(chi2),
        "p_value": float(p_value),
        "degrees_of_freedom": int(dof),
        "cramers_v": float(cramers_v),
        "n": int(n),
    }
    return expected, row_pct, col_pct, enrichment, std_residual, stats


def composition_permutation_test(
    composition: np.ndarray, labels: np.ndarray, permutations: int, seed: int
):
    overall = composition.mean(axis=0)
    total_ss = float(((composition - overall) ** 2).sum())

    def between_ss(group_labels: np.ndarray) -> float:
        value = 0.0
        for group in np.unique(group_labels):
            group_values = composition[group_labels == group]
            value += len(group_values) * float(((group_values.mean(axis=0) - overall) ** 2).sum())
        return value

    observed = between_ss(labels)
    rng = np.random.default_rng(seed)
    null_values = np.empty(permutations)
    for index in range(permutations):
        null_values[index] = between_ss(rng.permutation(labels))
    p_value = (1 + int((null_values >= observed).sum())) / (permutations + 1)
    r_squared = observed / total_ss if total_ss > 0 else np.nan
    return {
        "pseudo_f_between_ss": observed,
        "total_ss": total_ss,
        "r_squared": float(r_squared),
        "permutation_p": float(p_value),
        "n_permutations": permutations,
        "n": int(len(composition)),
    }


def save_matrix(matrix: pd.DataFrame, data_out: Path, name: str, index_label: str = "cluster"):
    matrix.rename_axis(index=index_label, columns="loac_supergroup").to_csv(data_out / f"{name}.csv")


def draw_heatmap(matrix: pd.DataFrame, title: str, output: Path, fmt: str = ".2f"):
    plt.figure(figsize=(10, max(4.5, 0.8 * len(matrix))))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=fmt,
        cmap="RdBu_r",
        center=1 if "Enrichment" in title else None,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Ratio" if "Enrichment" in title else "Share"},
    )
    plt.title(title, pad=14)
    plt.xlabel("LOAC Supergroup")
    plt.ylabel("RQ1 cluster")
    plt.tight_layout()
    plt.savefig(output, dpi=220, bbox_inches="tight")
    plt.close()


def top_enrichments(enrichment: pd.DataFrame, top_n: int = 2):
    rows = []
    for cluster, values in enrichment.iterrows():
        for group, ratio in values.sort_values(ascending=False).head(top_n).items():
            rows.append(
                {
                    "cluster": cluster,
                    "loac_supergroup": group,
                    "enrichment_ratio": float(ratio),
                }
            )
    return pd.DataFrame(rows)
