"""Full 5-panel house-style K-diagnostics figure (silhouette, Calinski-
Harabasz, Davies-Bouldin, BIC, bootstrap ARI) for the bottom-20%-by-activity
exclusion comparator, matching literature_mean1ph_kdiag_full.png and
巴士聚类错误修改/outputs/figures/bus_fullweek_kdiag_full.png.

Unlike literature_mean1ph, this sample is NOT byte-identical to the official
rewrite's (different exclusion rule -- quantile cutoff vs the literature
threshold=36 -- different retained LSOAs), so its diagnostics cannot be
borrowed; they must be computed on their own sample.

02_bottom20_excluded_bic.py's kdiag used whichever covariance family had the
global BIC minimum, which turned out to be `tied` at a degenerate K=12
solution (min_cluster_n=1 -- see that file's bottom20_excluded_bic_grid.csv).
02b_bottom20_full_covariance_kdiag.py already redid K=2..12 diagnostics under
full covariance only, for a fair comparison against 巴士聚类错误修改 and
literature_mean1ph (both full-covariance). This script uses that
full-covariance line (bottom20_excluded_full_covariance_kdiag.csv /
_bootstrap.csv), refits the same K=2..12/full/n_init=20/seed=42 models ONCE
MORE only to add Calinski-Harabasz (the one metric neither 02 nor 02b
computed, since it needs labels but not a saved model object, and no
K=2..12 label file was ever written to disk), then plots the house-style
panel. Bootstrap_ari_sd is recovered from the already-saved per-replicate
bootstrap CSV; nothing bootstrap-related is refit.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import calinski_harabasz_score

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent
BASE_SRC = FYP / "rq1_bus_hub_first_reclustering" / "src"
sys.path.insert(0, str(BASE_SRC))
import config as C  # noqa: E402
import run_fullweek_first_pass as base  # noqa: E402

X_INPUT = (
    FYP / "rq1_bus_hub_first_reclustering_alpha_sensitivity" / "outputs" / "features"
    / "X_bus_fullweek_alpha0_fixed_sample.parquet"
)
META_INPUT = FYP / "rq1_bus_hub_first_reclustering" / "outputs" / "features" / "bus_fullweek_meta_alpha5.csv"

DIAGNOSTICS = ROOT / "outputs" / "diagnostics"
FIGURES = ROOT / "outputs" / "figures"
EXCLUDE_QUANTILE = 0.20
K_RANGE = list(range(2, 13))
PURPLE, GREEN, RED = "#500778", "#2F6B4F", "#9A3D3D"


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    started = time.time()
    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)

    cutoff = float(meta["total_activity"].quantile(EXCLUDE_QUANTILE))
    keep_mask = meta["total_activity"].to_numpy(dtype=float) >= cutoff
    Xv = X.loc[keep_mask].to_numpy(dtype=float)
    log(f"n_core={len(Xv)} (cutoff={cutoff:.2f}), matching 02b_bottom20_full_covariance_kdiag.py exactly")

    log("Refitting full covariance K=2..12, n_init=20 (only to recover Calinski-Harabasz)")
    ch_rows = []
    for k in K_RANGE:
        model, _, seconds = base.fit_gmm(Xv, k, "full", C.RANDOM_STATE, C.N_INIT)
        labels = model.predict(Xv)
        ch = float(calinski_harabasz_score(Xv, labels))
        ch_rows.append({"K": k, "calinski_harabasz": ch})
        log(f"  K={k:2d} calinski_harabasz={ch:.2f} ({seconds:.1f}s)")
    ch_df = pd.DataFrame(ch_rows)

    kdiag = pd.read_csv(DIAGNOSTICS / "bottom20_excluded_full_covariance_kdiag.csv")
    kdiag = kdiag.merge(ch_df, on="K", how="left")

    boot = pd.read_csv(DIAGNOSTICS / "bottom20_excluded_full_covariance_bootstrap.csv")
    boot_sd = boot.groupby("K", as_index=False)["ARI"].std().rename(columns={"ARI": "bootstrap_ari_sd"})
    kdiag = kdiag.merge(boot_sd, on="K", how="left")
    kdiag.to_csv(DIAGNOSTICS / "bottom20_excluded_kdiag_full.csv", index=False)
    log(str(DIAGNOSTICS / "bottom20_excluded_kdiag_full.csv"))

    K = kdiag.K
    fig, ax = plt.subplots(2, 3, figsize=(14, 8))
    panels = [
        ("silhouette", "Silhouette (higher=better)", PURPLE),
        ("calinski_harabasz", "Calinski-Harabasz (higher=better)", GREEN),
        ("davies_bouldin", "Davies-Bouldin (lower=better)", RED),
        ("BIC", "BIC (lower=better)", PURPLE),
    ]
    for a, (col, title, color) in zip(ax.flat[:4], panels):
        a.plot(K, kdiag[col], "-o", color=color)
        a.set_title(title)
    a = ax.flat[4]
    a.errorbar(K, kdiag.bootstrap_ari_mean, yerr=kdiag.bootstrap_ari_sd, fmt="-o", color=PURPLE, capsize=3)
    a.set_title("Bootstrap stability ARI (higher=better)")
    a.set_ylim(0, 1.02)
    ax.flat[5].axis("off")
    for a in ax.flat:
        if a.has_data():
            a.set_xlabel("K")
            a.set_xticks(list(K_RANGE))
            a.grid(color="#eee")
            a.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        "bus (full week, bottom-20%-by-activity excluded) — K-diagnostics (raw-share, full covariance, GMM)\n"
        f"n_core={len(Xv):,} (cutoff={cutoff:.1f}); sensitivity comparator, not the literature-anchored rule",
        fontsize=13, y=1.02,
    )
    fig.tight_layout()
    out = FIGURES / "bottom20_excluded_kdiag_full.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log(f"wrote {out}")
    log(f"Done in {time.time()-started:.1f}s")


if __name__ == "__main__":
    main()
