"""Map and audit a literature-anchored low-flow exclusion rule.

The closest directly comparable bus-stop clustering study removed stops with
mean boardings below one passenger per observed hour.  The hub-first feature
matrix contains 36 typical-day hourly slots per direction (3 day types x 12
hours).  Because boardings and alightings are normalised independently and
enter the model symmetrically, this experiment retains LSOAs only when both
direction totals are at least 36.

This is a side-by-side experiment.  It does not overwrite the bottom-20%
variant or upstream hub-first outputs.
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
LSOA_LAD_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"
LSOA_GEOJSON = C.LSOA_GEOJSON

OUT = ROOT / "outputs"
LABELS = OUT / "labels"
FIGURES = OUT / "figures"
DATA = OUT / "data"
REPORT = OUT / "report"
for directory in (LABELS, FIGURES, DATA, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
MIN_PER_DIRECTION = 36.0
CANDIDATE_KS = [3, 4]
TARGET_LADS = {
    "E09000033": "Westminster",
    "E09000007": "Camden",
    "E09000021": "Kingston upon Thames",
    "E09000027": "Richmond upon Thames",
}


def log(message: str) -> None:
    print(message, flush=True)


def cluster_distribution(frame: pd.DataFrame, group: str, k: int) -> np.ndarray:
    counts = frame.loc[frame["area_group"] == group, "cluster"].value_counts()
    values = np.array([counts.get(cluster, 0) for cluster in range(k)], dtype=float)
    return values / values.sum() if values.sum() else values


def main() -> None:
    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)

    min_direction = meta[["tot_boardings", "tot_alightings"]].min(axis=1)
    keep_mask = min_direction.to_numpy(dtype=float) >= MIN_PER_DIRECTION
    all_units = X.index
    core_units = X.index[keep_mask]
    X_core = X.loc[core_units]
    Xv = X_core.to_numpy(dtype=float)
    log(f"n_retained={len(Xv)}; n_excluded={len(all_units) - len(core_units)}")

    lookup = pd.read_csv(LSOA_LAD_LOOKUP, usecols=["LSOA21CD", "LAD22CD"])
    lookup["LSOA21CD"] = lookup["LSOA21CD"].astype(str)
    lookup["borough"] = lookup["LAD22CD"].map(TARGET_LADS)

    summaries: list[dict[str, object]] = []
    borough_tables: list[pd.DataFrame] = []
    labels_by_k: dict[int, np.ndarray] = {}

    for k in CANDIDATE_KS:
        model, _, seconds = base.fit_gmm(Xv, k, "full", C.RANDOM_STATE, C.N_INIT)
        labels = model.predict(Xv).astype(int)
        labels_by_k[k] = labels
        sizes = np.bincount(labels, minlength=k)
        log(f"K={k}: sizes={sizes.tolist()} ({seconds:.1f}s)")

        label_frame = pd.DataFrame(
            {
                "lsoa": all_units,
                "retained_for_fit": keep_mask,
                "min_direction_activity": min_direction.to_numpy(dtype=float),
                "cluster": np.where(keep_mask, -2, -1),
            }
        )
        label_frame.loc[label_frame["retained_for_fit"], "cluster"] = labels
        label_frame.to_csv(LABELS / f"literature_mean1ph_full_k{k}_labels.csv", index=False)

        target = pd.DataFrame({"LSOA21CD": core_units, "cluster": labels}).merge(
            lookup[["LSOA21CD", "borough"]], on="LSOA21CD", how="left"
        )
        target = target[target["borough"].notna()].copy()
        target["area_group"] = np.where(
            target["borough"].isin(["Westminster", "Camden"]), "central", "outer"
        )

        cross = pd.crosstab(target["borough"], target["cluster"])
        cross = cross.reindex(index=list(TARGET_LADS.values()), columns=range(k), fill_value=0)
        shares = cross.div(cross.sum(axis=1), axis=0)
        table = cross.reset_index().melt(id_vars="borough", var_name="cluster", value_name="n")
        share_table = shares.reset_index().melt(
            id_vars="borough", var_name="cluster", value_name="within_borough_share"
        )
        table = table.merge(share_table, on=["borough", "cluster"])
        table.insert(0, "k", k)
        borough_tables.append(table)

        central = cluster_distribution(target, "central", k)
        outer = cluster_distribution(target, "outer", k)
        total_variation = 0.5 * float(np.abs(central - outer).sum())
        same_cluster_probability = float(np.dot(central, outer))
        summaries.append(
            {
                "k": k,
                "n_retained": len(core_units),
                "n_excluded": len(all_units) - len(core_units),
                "pct_excluded": 100.0 * (len(all_units) - len(core_units)) / len(all_units),
                "cluster_sizes": ";".join(str(int(value)) for value in sizes),
                "central_outer_total_variation": total_variation,
                "central_outer_same_cluster_probability": same_cluster_probability,
            }
        )

    pd.DataFrame(summaries).to_csv(DATA / "literature_mean1ph_k3_k4_spatial_audit.csv", index=False)
    pd.concat(borough_tables, ignore_index=True).to_csv(
        DATA / "literature_mean1ph_k3_k4_borough_cluster_shares.csv", index=False
    )

    log("Building temporal profiles")
    for k in CANDIDATE_KS:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True)
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            means = X_core.loc[labels == cluster].mean(axis=0)
            for column, day_type in enumerate(DAY_TYPES):
                ax = axes[cluster, column]
                for direction, color in [("boardings", "#4C78A8"), ("alightings", "#F58518")]:
                    cols = [name for name in X_core.columns if name.startswith(f"{direction}_{day_type}_")]
                    hours = sorted(int(name.rsplit("_", 1)[1]) for name in cols)
                    values = [means[f"{direction}_{day_type}_{hour}"] for hour in hours]
                    ax.plot(range(12), values, marker="o", markersize=2, color=color, label=direction)
                if cluster == 0:
                    ax.set_title(day_type)
                if column == 0:
                    ax.set_ylabel(f"C{cluster} (n={int(sizes[cluster])})")
                ax.grid(alpha=0.2)
        axes[-1, 1].set_xticks(
            range(12), ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"],
            rotation=45,
        )
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(
            f"Literature mean >=1/hour analogue (both directions >=36), full covariance, K={k}\n"
            "mean share of each direction's own full-week total",
            y=1.01,
        )
        fig.tight_layout()
        fig.savefig(FIGURES / f"literature_mean1ph_full_profiles_k{k}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    log("Building spatial maps")
    import geopandas as gpd

    boundaries = gpd.read_file(LSOA_GEOJSON)
    code_col = next(column for column in boundaries.columns if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_col, "geometry"]].rename(columns={code_col: "LSOA21CD"})
    excluded_units = set(all_units) - set(core_units)
    for k in CANDIDATE_KS:
        label_frame = pd.DataFrame(
            {
                "LSOA21CD": list(core_units) + list(excluded_units),
                "status": ["retained"] * len(core_units) + ["low_flow_excluded"] * len(excluded_units),
                "cluster": list(labels_by_k[k]) + [-1] * len(excluded_units),
            }
        )
        mapped = boundaries.merge(label_frame, on="LSOA21CD", how="left")
        fig, ax = plt.subplots(figsize=(8, 8))
        retained = mapped[mapped["status"] == "retained"]
        other = mapped[mapped["status"] != "retained"]
        other.plot(ax=ax, color="#e0e0e0", linewidth=0.0)
        retained.plot(ax=ax, column="cluster", categorical=True, cmap="tab10", linewidth=0.0, legend=True)
        ax.set_axis_off()
        ax.set_title(
            f"Literature mean >=1/hour analogue, full covariance, K={k}\n"
            "grey = below 36 in either direction or outside current valid sample"
        )
        fig.tight_layout()
        fig.savefig(FIGURES / f"literature_mean1ph_full_map_k{k}.png", dpi=180)
        plt.close(fig)

    summary = pd.DataFrame(summaries)
    borough = pd.concat(borough_tables, ignore_index=True)
    lines = [
        "# Literature mean-1-per-hour analogue: K=3/K=4 spatial check",
        "",
        f"- Rule: retain only `min(tot_boardings, tot_alightings) >= {MIN_PER_DIRECTION:.0f}`.",
        f"- Retained: {len(core_units):,}/{len(all_units):,} ({100 * len(core_units) / len(all_units):.2f}%).",
        f"- Excluded: {len(all_units) - len(core_units):,}/{len(all_units):,} "
        f"({100 * (len(all_units) - len(core_units)) / len(all_units):.2f}%).",
        "- Models: alpha=0 hub-first features, full-covariance GMM, seed=42, n_init=20.",
        "",
        "## Central-versus-outer diagnostic",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "`central_outer_total_variation` is 0 for identical cluster distributions and 1 for no overlap.",
        "`central_outer_same_cluster_probability` is the probability that one random central and one random outer LSOA receive the same cluster label.",
        "",
        "## Borough cluster composition",
        "",
        borough.to_markdown(index=False, floatfmt=".4f"),
        "",
        "This is a targeted diagnostic of Howard's central/outer mixing concern, not evidence that geographic distance was used in the GMM.",
    ]
    (REPORT / "LITERATURE_MEAN1PH_K3_K4_SPATIAL_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    log("Done")


if __name__ == "__main__":
    main()
