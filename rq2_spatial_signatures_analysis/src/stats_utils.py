"""Statistical helpers for categorical and compositional association checks."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


def _chi_square_stat(labels: np.ndarray, categories: np.ndarray, category_order: list[str]):
    observed = pd.crosstab(labels, categories).reindex(
        index=sorted(np.unique(labels)), columns=category_order, fill_value=0
    )
    observed = observed.loc[:, observed.sum(axis=0) > 0]
    chi2, p_value, dof, expected_array = chi2_contingency(observed.to_numpy())
    expected = pd.DataFrame(expected_array, index=observed.index, columns=observed.columns)
    denominator = min(observed.shape[0] - 1, observed.shape[1] - 1)
    n = int(observed.to_numpy().sum())
    cramers_v = math.sqrt(chi2 / (n * denominator)) if denominator > 0 else np.nan
    return observed, expected, float(chi2), float(p_value), int(dof), float(cramers_v)


def categorical_association(
    labels: np.ndarray,
    categories: np.ndarray,
    category_order: list[str],
    strata: np.ndarray,
    permutations: int,
    seed: int,
):
    """Association tables plus unconditional and distance-stratified permutations."""
    observed, expected, chi2, asymptotic_p, dof, cramers_v = _chi_square_stat(
        labels, categories, category_order
    )
    row_pct = observed.div(observed.sum(axis=1), axis=0)
    universe = observed.sum(axis=0) / observed.to_numpy().sum()
    enrichment = row_pct.div(universe, axis=1)
    residual = (observed - expected) / np.sqrt(expected)

    rng = np.random.default_rng(seed)
    null = np.empty(permutations)
    conditional_null = np.empty(permutations)
    for i in range(permutations):
        permuted = rng.permutation(categories)
        null[i] = _chi_square_stat(labels, permuted, category_order)[2]

        conditional = categories.copy()
        for band in np.unique(strata):
            idx = np.flatnonzero(strata == band)
            conditional[idx] = rng.permutation(conditional[idx])
        conditional_null[i] = _chi_square_stat(labels, conditional, category_order)[2]

    stats = {
        "n": int(len(labels)),
        "chi_square": chi2,
        "degrees_of_freedom": dof,
        "asymptotic_p": asymptotic_p,
        "permutation_p": float((1 + (null >= chi2).sum()) / (permutations + 1)),
        "distance_band_conditional_p": float(
            (1 + (conditional_null >= chi2).sum()) / (permutations + 1)
        ),
        "cramers_v": cramers_v,
        "expected_cells_lt5_fraction": float((expected.to_numpy() < 5).mean()),
        "minimum_expected_count": float(expected.to_numpy().min()),
        "n_permutations": int(permutations),
    }
    return observed, expected, row_pct, enrichment, residual, stats


def composition_permutation_test(
    composition: np.ndarray,
    labels: np.ndarray,
    permutations: int,
    seed: int,
):
    """Euclidean between-cluster R2 for composition, with label permutation."""
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
    null = np.array([between_ss(rng.permutation(labels)) for _ in range(permutations)])
    return {
        "n": int(len(composition)),
        "r_squared": float(observed / total_ss) if total_ss > 0 else np.nan,
        "permutation_p": float((1 + (null >= observed).sum()) / (permutations + 1)),
        "n_permutations": int(permutations),
    }

