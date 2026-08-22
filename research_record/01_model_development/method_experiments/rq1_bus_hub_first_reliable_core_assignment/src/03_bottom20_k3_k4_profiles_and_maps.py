"""Temporal profile and spatial map figures for the bottom-20%-excluded,
full-covariance K=3 (clean, activity_eta2 < timing_mean_eta2) and K=4
(activity-dominated but higher bootstrap ARI) candidates from
02b_bottom20_full_covariance_kdiag.py.

Refits deterministically (same seed=42, n_init=20, same core sample) rather
than reusing in-memory models, since 02b did not persist per-LSOA labels.

Writes only inside rq1_bus_hub_first_reliable_core_assignment/outputs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
LSOA_GEOJSON = C.LSOA_GEOJSON

OUT = ROOT / "outputs"
LABELS = OUT / "labels"
FIGURES = OUT / "figures"
for directory in (LABELS, FIGURES):
    directory.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
EXCLUDE_QUANTILE = 0.20
CANDIDATE_KS = [3, 4]


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> None:
    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)

    cutoff = float(meta["total_activity"].quantile(EXCLUDE_QUANTILE))
    keep_mask = meta["total_activity"].to_numpy(dtype=float) >= cutoff
    all_units = X.index
    core_units = X.index[keep_mask]
    X_core = X.loc[core_units]
    Xv = X_core.to_numpy(dtype=float)
    log(f"n_core={len(Xv)} (cutoff={cutoff:.2f}); n_excluded={len(all_units) - len(core_units)}")

    labels_by_k: dict[int, np.ndarray] = {}
    for k in CANDIDATE_KS:
        model, _, seconds = base.fit_gmm(Xv, k, "full", C.RANDOM_STATE, C.N_INIT)
        labels = model.predict(Xv)
        labels_by_k[k] = labels
        sizes = np.bincount(labels, minlength=k)
        log(f"K={k}: sizes={sizes.tolist()} ({seconds:.1f}s)")
        pd.DataFrame({"lsoa": core_units, "cluster": labels}).to_csv(
            LABELS / f"bottom20_full_k{k}_labels.csv", index=False
        )

    log("Building temporal profile figures")
    for k in CANDIDATE_KS:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True)
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            mask = labels == cluster
            means = X_core.loc[mask].mean(axis=0)
            for column, day_type in enumerate(DAY_TYPES):
                ax = axes[cluster, column]
                for direction, color in [("boardings", "#4C78A8"), ("alightings", "#F58518")]:
                    cols = [c for c in X_core.columns if c.startswith(f"{direction}_{day_type}_")]
                    hours = sorted(int(c.rsplit("_", 1)[1]) for c in cols)
                    values = [means[f"{direction}_{day_type}_{h}"] for h in hours]
                    ax.plot(range(12), values, marker="o", markersize=2, color=color, label=direction)
                if cluster == 0:
                    ax.set_title(day_type)
                if column == 0:
                    ax.set_ylabel(f"C{cluster} (n={int(sizes[cluster])})")
                ax.grid(alpha=0.2)
        axes[-1, 1].set_xticks(
            range(12), ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"], rotation=45
        )
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(
            f"Bottom-20%-excluded hub-first bus (n_core={len(Xv)}), full covariance, K={k}\n"
            "mean share of each direction's own full-week total",
            y=1.01,
        )
        fig.tight_layout()
        fig.savefig(FIGURES / f"bottom20_full_profiles_k{k}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        log(f"  wrote bottom20_full_profiles_k{k}.png")

    log("Building spatial maps")
    try:
        import geopandas as gpd

        boundaries = gpd.read_file(LSOA_GEOJSON)
        code_col = next(c for c in boundaries.columns if c.lower() == "lsoa21cd")
        boundaries = boundaries[[code_col, "geometry"]].rename(columns={code_col: "LSOA21CD"})

        excluded_units = set(all_units) - set(core_units)
        for k in CANDIDATE_KS:
            label_frame = pd.DataFrame(
                {
                    "LSOA21CD": list(core_units) + list(excluded_units),
                    "status": (["core"] * len(core_units)) + (["excluded_or_not_in_sample"] * len(excluded_units)),
                    "cluster": list(labels_by_k[k].astype(int)) + ([-1] * len(excluded_units)),
                }
            )
            mapped = boundaries.merge(label_frame, on="LSOA21CD", how="left")
            fig, ax = plt.subplots(figsize=(8, 8))
            core_plot = mapped[mapped["status"] == "core"]
            excluded_plot = mapped[mapped["status"] != "core"]
            excluded_plot.plot(ax=ax, color="#e0e0e0", linewidth=0.0)
            core_plot.plot(ax=ax, column="cluster", categorical=True, cmap="tab10", linewidth=0.0, legend=True)
            ax.set_axis_off()
            ax.set_title(
                f"Bottom-20%-excluded hub-first bus clusters, full covariance, K={k}\n"
                "grey = excluded (bottom-20% activity, below-50 floor, or one-direction exception)"
            )
            fig.tight_layout()
            fig.savefig(FIGURES / f"bottom20_full_map_k{k}.png", dpi=180)
            plt.close(fig)
            log(f"  wrote bottom20_full_map_k{k}.png")
    except Exception as exc:  # pragma: no cover
        (FIGURES / "MAP_ERROR.txt").write_text(repr(exc), encoding="utf-8")
        log(f"  map generation failed: {exc!r}")

    log("Done")


if __name__ == "__main__":
    main()
