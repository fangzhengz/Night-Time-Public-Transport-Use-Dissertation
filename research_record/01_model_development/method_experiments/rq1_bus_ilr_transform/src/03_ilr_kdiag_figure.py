"""Complete 2x3 K-diagnostic panel for the fitted rank-reduced ILR features."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import calinski_harabasz_score

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FEATURES = ROOT / "outputs" / "features"
LABELS = ROOT / "outputs" / "labels"
DIAGNOSTICS = ROOT / "outputs" / "diagnostics"
FIGURES = ROOT / "outputs" / "figures"
PURPLE, GREEN, RED = "#500778", "#2F6B4F", "#9A3D3D"
K_RANGE = list(range(2, 13))


def main() -> None:
    feature_path = next(FEATURES.glob("X_bus_fullweek_ilr_rank*.parquet"))
    X = pd.read_parquet(feature_path)
    X.index = X.index.astype(str)
    values = X.to_numpy(dtype=float)
    kdiag = pd.read_csv(DIAGNOSTICS / "ilr_kdiag.csv")
    ch_rows = []
    for k in K_RANGE:
        labels = pd.read_csv(LABELS / f"ilr_k{k}_labels.csv")
        labels["unit"] = labels["unit"].astype(str)
        aligned = labels.set_index("unit").loc[X.index, "cluster"].to_numpy(dtype=int)
        ch_rows.append({"K": k, "calinski_harabasz": float(calinski_harabasz_score(values, aligned))})
    complete = kdiag.merge(pd.DataFrame(ch_rows), on="K", how="left")
    boot = pd.read_csv(DIAGNOSTICS / "ilr_bootstrap.csv")
    boot_summary = boot.groupby("K")["ARI"].agg(ARI_mean="mean", ARI_sd="std").reset_index()
    complete = complete.merge(boot_summary, on="K", how="left")
    complete.to_csv(DIAGNOSTICS / "ilr_kdiag_full.csv", index=False)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    panels = [
        ("silhouette", "Silhouette (higher=better)", PURPLE),
        ("calinski_harabasz", "Calinski-Harabasz (higher=better)", GREEN),
        ("davies_bouldin", "Davies-Bouldin (lower=better)", RED),
        ("BIC", "BIC (lower=better)", PURPLE),
    ]
    for axis, (column, title, colour) in zip(axes.flat[:4], panels):
        axis.plot(complete["K"], complete[column], "-o", color=colour)
        axis.set_title(title)
    axes.flat[4].errorbar(complete["K"], complete["ARI_mean"], yerr=complete["ARI_sd"], fmt="-o", color=PURPLE, capsize=3)
    axes.flat[4].set_title("Bootstrap stability ARI")
    axes.flat[4].set_ylim(0, 1.02)
    axes.flat[5].axis("off")
    for axis in axes.flat:
        if axis.has_data():
            axis.set_xlabel("K")
            axis.set_xticks(K_RANGE)
            axis.grid(color="#eee")
            axis.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"bus (full week, ILR rank-{values.shape[1]}) - K diagnostics", fontsize=14, y=1.0)
    fig.tight_layout()
    fig.savefig(FIGURES / "ilr_kdiag_full.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
