"""Deterministically refit the selected Hellinger solution and verify labels."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
OUT = ROOT / "outputs"
FEATURES = OUT / "features"
DIAGNOSTICS = OUT / "diagnostics"
LABELS = OUT / "labels"
REPORT = OUT / "report"

SEED = 42
N_INIT = 20
REG_COVAR = 1e-6
MAX_ITER = 300


def main() -> None:
    selection = json.loads((DIAGNOSTICS / "hellinger_selection.json").read_text(encoding="utf-8"))
    selected_k = int(selection["selected_k"])
    kdiag = pd.read_csv(DIAGNOSTICS / "hellinger_kdiag.csv")
    reference_row = kdiag[kdiag["K"] == selected_k].iloc[0]
    covariance = str(reference_row["covariance"])

    X = pd.read_parquet(FEATURES / "X_bus_fullweek_hellinger.parquet")
    X.index = X.index.astype(str)
    Xv = X.to_numpy(dtype=float)
    saved = pd.read_csv(LABELS / f"hellinger_k{selected_k}_labels.csv")
    saved["unit"] = saved["unit"].astype(str)
    saved_labels = saved.set_index("unit").loc[X.index, "cluster"].to_numpy(dtype=int)

    model = GaussianMixture(
        n_components=selected_k,
        covariance_type=covariance,
        n_init=N_INIT,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=SEED,
    ).fit(Xv)
    rerun_labels = model.predict(Xv)
    ari = float(adjusted_rand_score(saved_labels, rerun_labels))
    bic_diff = abs(float(model.bic(Xv)) - float(reference_row["BIC"]))
    exact_labels = bool(np.array_equal(saved_labels, rerun_labels))
    verified = exact_labels and bic_diff <= 1e-9

    result = {
        "selected_k": selected_k,
        "covariance": covariance,
        "same_seed_n_init": N_INIT,
        "label_ari": ari,
        "labels_exactly_equal": exact_labels,
        "bic_absolute_difference": bic_diff,
        "verdict": "REPRODUCIBLE" if verified else "NOT_REPRODUCIBLE",
    }
    (DIAGNOSTICS / "selected_solution_reproducibility.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    report = f"""## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: validate
- Verification Status: {'VERIFIED' if verified else 'ANALYZED'}
- Version Label: bus_hellinger_selected_reproducibility_v1

# Selected Hellinger solution reproducibility

{pd.DataFrame([result]).to_markdown(index=False)}

The selected solution was refitted from the saved Hellinger feature matrix with
the same seed, covariance family, K, n_init, regularisation, and iteration cap.
"""
    (REPORT / "REPRODUCIBILITY_CHECK.md").write_text(report, encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not verified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
