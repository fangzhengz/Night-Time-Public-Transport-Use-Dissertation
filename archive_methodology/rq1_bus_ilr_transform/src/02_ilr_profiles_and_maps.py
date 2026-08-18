"""Raw-share profiles, maps and Howard check for ILR-derived K=3/K=4 labels."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent
RAW_SHARE_X = FYP / "巴士聚类错误修改" / "outputs" / "features" / "X_bus_fullweek_alpha0.parquet"
LSOA_BOUNDARY = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_LAD_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"
CLR_ROOT = FYP / "rq1_bus_clr_transform"
TARGET_LADS = {
    "E09000033": "Westminster",
    "E09000007": "Camden",
    "E09000021": "Kingston upon Thames",
    "E09000027": "Richmond upon Thames",
}

OUT = ROOT / "outputs"
LABELS = OUT / "labels"
FIGURES = OUT / "figures"
DATA = OUT / "data"
REPORT = OUT / "report"
RUN_LOG = ROOT / "run_02.log"
for path in (FIGURES, DATA, REPORT):
    path.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
CANDIDATE_KS = [3, 4]


def log(message: str) -> None:
    print(message, flush=True)
    with RUN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def cluster_distribution(frame: pd.DataFrame, group: str, k: int) -> np.ndarray:
    counts = frame.loc[frame["area_group"] == group, "cluster"].value_counts()
    values = np.array([counts.get(cluster, 0) for cluster in range(k)], dtype=float)
    return values / values.sum() if values.sum() else values


def main() -> None:
    import geopandas as gpd

    RUN_LOG.write_text("", encoding="utf-8")
    X_raw = pd.read_parquet(RAW_SHARE_X)
    X_raw.index = pd.Index(X_raw.index.astype(str), name="lsoa")
    labels_by_k = {}
    units_by_k = {}
    for k in CANDIDATE_KS:
        frame = pd.read_csv(LABELS / f"ilr_k{k}_labels.csv")
        frame["unit"] = frame["unit"].astype(str)
        units_by_k[k] = pd.Index(frame["unit"], name="lsoa")
        labels_by_k[k] = frame["cluster"].to_numpy(dtype=int)

    for k in CANDIDATE_KS:
        units = units_by_k[k]
        X = X_raw.loc[units]
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True)
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            means = X.loc[labels == cluster].mean(axis=0)
            for column, day_type in enumerate(DAY_TYPES):
                axis = axes[cluster, column]
                for direction, color in [("boardings", "#4C78A8"), ("alightings", "#F58518")]:
                    cols = [name for name in X.columns if name.startswith(f"{direction}_{day_type}_")]
                    hours = sorted(int(name.rsplit("_", 1)[1]) for name in cols)
                    values = [means[f"{direction}_{day_type}_{hour}"] for hour in hours]
                    axis.plot(range(12), values, marker="o", markersize=2, color=color, label=direction)
                if cluster == 0:
                    axis.set_title(day_type)
                if column == 0:
                    axis.set_ylabel(f"C{cluster} (n={int(sizes[cluster])})")
                axis.grid(alpha=0.2)
        axes[-1, 1].set_xticks(range(12), ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"], rotation=45)
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(f"ILR-derived clusters, K={k}\nprofiles shown in raw-share space", y=1.01)
        fig.tight_layout()
        fig.savefig(FIGURES / f"ilr_profiles_k{k}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    boundaries = gpd.read_file(LSOA_BOUNDARY)
    code_col = next(column for column in boundaries.columns if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_col, "geometry"]].rename(columns={code_col: "LSOA21CD"})
    for k in CANDIDATE_KS:
        label_frame = pd.DataFrame({"LSOA21CD": units_by_k[k], "cluster": labels_by_k[k]})
        mapped = boundaries.merge(label_frame, on="LSOA21CD", how="left")
        fig, axis = plt.subplots(figsize=(8, 8))
        mapped[mapped["cluster"].isna()].plot(ax=axis, color="#e0e0e0", linewidth=0.0)
        mapped[mapped["cluster"].notna()].plot(ax=axis, column="cluster", categorical=True, cmap="tab10", linewidth=0.0, legend=True)
        axis.set_axis_off()
        axis.set_title(f"ILR-derived clusters, K={k}\ngrey = outside retained 3,365-LSOA modelling sample")
        fig.tight_layout()
        fig.savefig(FIGURES / f"ilr_map_k{k}.png", dpi=180)
        plt.close(fig)

    lookup = pd.read_csv(LSOA_LAD_LOOKUP, usecols=["LSOA21CD", "LAD22CD"])
    lookup["LSOA21CD"] = lookup["LSOA21CD"].astype(str)
    lookup["borough"] = lookup["LAD22CD"].map(TARGET_LADS)
    summaries = []
    borough_rows = []
    for k in CANDIDATE_KS:
        target = pd.DataFrame({"LSOA21CD": units_by_k[k], "cluster": labels_by_k[k]}).merge(
            lookup[["LSOA21CD", "borough"]], on="LSOA21CD", how="left"
        )
        target = target[target["borough"].notna()].copy()
        target["area_group"] = np.where(target["borough"].isin(["Westminster", "Camden"]), "central", "outer")
        central = cluster_distribution(target, "central", k)
        outer = cluster_distribution(target, "outer", k)
        summaries.append(
            {
                "K": k,
                "n_matched": len(target),
                "central_outer_total_variation": 0.5 * float(np.abs(central - outer).sum()),
                "central_outer_same_cluster_probability": float(np.dot(central, outer)),
            }
        )
        shares = target.groupby(["borough", "cluster"], observed=True).size().rename("n").reset_index()
        shares["within_borough_share"] = shares["n"] / shares.groupby("borough")["n"].transform("sum")
        shares.insert(0, "K", k)
        borough_rows.append(shares)
    summary = pd.DataFrame(summaries)
    summary.to_csv(DATA / "ilr_howard_central_outer.csv", index=False)
    pd.concat(borough_rows, ignore_index=True).to_csv(DATA / "ilr_howard_borough_cluster_shares.csv", index=False)

    comparisons = []
    for k in CANDIDATE_KS:
        clr_path = CLR_ROOT / "outputs" / "labels" / f"clr_k{k}_labels.csv"
        clr = pd.read_csv(clr_path).set_index("unit").loc[units_by_k[k], "cluster"].to_numpy(dtype=int)
        comparisons.append({"K": k, "ARI_ilr_vs_clr": float(adjusted_rand_score(labels_by_k[k], clr))})
    comparison = pd.DataFrame(comparisons)
    report = f"""# ILR profiles, maps and geographic validation

## Howard central-versus-outer check

{summary.to_markdown(index=False, floatfmt=".4f")}

## Direct CLR label agreement

{comparison.to_markdown(index=False, floatfmt=".6f")}

The Howard check is descriptive validation only; geography is not used as an
input feature. Cluster numbers and colours are not aligned across unrelated
models, so ARI rather than numeric label equality is used for comparison.
"""
    (REPORT / "ILR_PROFILES_MAPS_GEOGRAPHIC.md").write_text(report, encoding="utf-8")
    log(str(REPORT / "ILR_PROFILES_MAPS_GEOGRAPHIC.md"))


if __name__ == "__main__":
    main()
