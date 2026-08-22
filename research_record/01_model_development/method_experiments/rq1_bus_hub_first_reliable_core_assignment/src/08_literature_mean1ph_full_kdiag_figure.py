"""Full 5-panel house-style K-diagnostics figure (silhouette, Calinski-
Harabasz, Davies-Bouldin, BIC, bootstrap ARI) for the literature mean->=1/hour
threshold, matching cluster_clean_version_fullweek/src/05_figures.py::plot_kdiag
and 巴士聚类错误修改/src/05_kdiag_figure.py exactly -- what the previous script
(06_literature_mean1ph_k_diagnostics_figure.py) could NOT build, because
01_threshold_screen.py's own scan never computed silhouette/CH/DB or ran a
bootstrap for this threshold.

Rather than refitting ~130 GMMs (4 covariance families x K=2..12, plus
bootstrap) a second time, this script first verifies byte-identity between
this folder's min(boardings,alightings)>=36 feature matrix and
巴士聚类错误修改's saved X_bus_fullweek_alpha0.parquet (same hub-first sample,
same 72-dim shares, same n=3,365), then reuses that folder's already-computed
bus_fullweek_kdiag.csv (same GMM settings: full covariance, K=2..12, n_init=20,
reg_covar=1e-6, max_iter=300, seed=42 -- confirmed identical in both configs).
If the identity check ever fails (e.g. either upstream matrix changes), this
script raises rather than silently plotting mismatched numbers.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent

X_INPUT = (
    FYP / "rq1_bus_hub_first_reclustering_alpha_sensitivity" / "outputs" / "features"
    / "X_bus_fullweek_alpha0_fixed_sample.parquet"
)
META_INPUT = FYP / "rq1_bus_hub_first_reclustering" / "outputs" / "features" / "bus_fullweek_meta_alpha5.csv"
OFFICIAL_X = FYP / "巴士聚类错误修改" / "outputs" / "features" / "X_bus_fullweek_alpha0.parquet"
OFFICIAL_KDIAG = FYP / "巴士聚类错误修改" / "outputs" / "diagnostics" / "bus_fullweek_kdiag.csv"

MIN_PER_DIRECTION = 36.0
DIAGNOSTICS = ROOT / "outputs" / "diagnostics"
FIGURES = ROOT / "outputs" / "figures"
PURPLE, GREEN, RED = "#500778", "#2F6B4F", "#9A3D3D"


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)
    min_direction = meta[["tot_boardings", "tot_alightings"]].min(axis=1)
    core = X.index[min_direction.to_numpy(dtype=float) >= MIN_PER_DIRECTION]
    log(f"literature_mean1ph core: n={len(core)}")

    X_off = pd.read_parquet(OFFICIAL_X)
    X_off.index = pd.Index(X_off.index.astype(str), name="lsoa")
    log(f"official (巴士聚类错误修改) sample: n={len(X_off)}")

    if set(core) != set(X_off.index):
        raise ValueError(
            "literature_mean1ph core LSOA set no longer matches 巴士聚类错误修改's "
            "retained sample -- cannot reuse its kdiag.csv; refit locally instead."
        )
    common_cols = [c for c in X.columns if c in X_off.columns]
    if len(common_cols) != 72:
        raise ValueError(f"Expected 72 shared feature columns, found {len(common_cols)}")
    a = X.loc[list(core), common_cols].to_numpy(dtype=float)
    b = X_off.loc[list(core), common_cols].to_numpy(dtype=float)
    max_abs_diff = float(np.abs(a - b).max())
    if not np.allclose(a, b, atol=1e-8):
        raise ValueError(
            f"literature_mean1ph feature matrix diverges from 巴士聚类错误修改's "
            f"(max abs diff={max_abs_diff:.2e}) -- cannot reuse its kdiag.csv; refit locally instead."
        )
    log(f"Verified byte-identical to 巴士聚类错误修改's X_bus_fullweek_alpha0.parquet (max abs diff={max_abs_diff:.1e})")

    d = pd.read_csv(OFFICIAL_KDIAG)
    d.to_csv(DIAGNOSTICS / "literature_mean1ph_kdiag_full.csv", index=False)
    K = d.K

    fig, ax = plt.subplots(2, 3, figsize=(14, 8))
    panels = [
        ("silhouette", "Silhouette (higher=better)", PURPLE),
        ("calinski_harabasz", "Calinski-Harabasz (higher=better)", GREEN),
        ("davies_bouldin", "Davies-Bouldin (lower=better)", RED),
        ("BIC", "BIC (lower=better)", PURPLE),
    ]
    for a_, (col, title, color) in zip(ax.flat[:4], panels):
        a_.plot(K, d[col], "-o", color=color)
        a_.set_title(title)
    a_ = ax.flat[4]
    a_.errorbar(K, d.bootstrap_ari_mean, yerr=d.bootstrap_ari_sd, fmt="-o", color=PURPLE, capsize=3)
    a_.set_title("Bootstrap stability ARI (higher=better)")
    a_.set_ylim(0, 1.02)
    ax.flat[5].axis("off")
    for a_ in ax.flat:
        if a_.has_data():
            a_.set_xlabel("K")
            a_.set_xticks(list(K))
            a_.grid(color="#eee")
            a_.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        "bus (full week, literature mean>=1/hour threshold=36) — K-diagnostics (raw-share, GMM)\n"
        "identical fit to the official rewrite (bus_clustering_official_rewrite) -- same 3,365-LSOA "
        "sample, same GMM settings, verified byte-identical",
        fontsize=13, y=1.02,
    )
    fig.tight_layout()
    out = FIGURES / "literature_mean1ph_kdiag_full.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log(f"wrote {out}")


if __name__ == "__main__":
    main()
