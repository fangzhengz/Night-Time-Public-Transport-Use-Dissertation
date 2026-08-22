"""Bus RQ1 cluster x LOAC dominant-Supergroup association (direct LSOA join).

Mirrors ``rq2test analysis/src/run_analysis.py``'s ``build_bus_analysis``,
with LOAC's dominant Supergroup (from ``01_build_loac_lsoa.py``) substituted
for LNWC's category. Bus clustering is
``rq1_bus_stoparea_clustering``'s StopArea CLR K=4 (see
config.py), matching ``rq2_new_clusters_analysis``'s choice.
"""

from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap

from config import (
    BUS_CLUSTER_COLOURS,
    BUS_K,
    BUS_LABELS,
    DATA_OUT,
    FIGURE_OUT,
    LOAC_SUPERGROUP_COLOURS,
    LOAC_SUPERGROUPS,
    LSOA_BOUNDARIES,
    ROOT,
)
from stats_utils import association_outputs, draw_heatmap, save_matrix, top_enrichments

LOAC_LSOA = ROOT / "data" / "loac_lsoa_supergroup.csv"


def main() -> None:
    labels = pd.read_csv(BUS_LABELS).rename(columns={"lsoa": "LSOA21CD"})
    loac = pd.read_csv(LOAC_LSOA)

    bus = labels.merge(loac, on="LSOA21CD", how="left", validate="one_to_one")
    bus.to_csv(DATA_OUT / "bus_loac_lsoa.csv", index=False)

    fitted = bus.loc[bus["cluster"] != -1].copy()
    matched = fitted.dropna(subset=["loac_dominant_supergroup"]).copy()

    observed = pd.crosstab(matched["cluster"], matched["loac_dominant_supergroup"]).reindex(
        index=sorted(matched["cluster"].unique()), columns=LOAC_SUPERGROUPS, fill_value=0
    )
    expected, row_pct, col_pct, enrichment, residual, stats = association_outputs(
        observed, LOAC_SUPERGROUPS
    )

    save_matrix(observed, DATA_OUT, "bus_loac_crosstab_counts")
    save_matrix(expected, DATA_OUT, "bus_loac_crosstab_expected")
    save_matrix(row_pct, DATA_OUT, "bus_loac_crosstab_row_pct")
    save_matrix(col_pct, DATA_OUT, "bus_loac_crosstab_col_pct")
    save_matrix(enrichment, DATA_OUT, "bus_loac_enrichment")
    save_matrix(residual, DATA_OUT, "bus_loac_standardized_residuals")
    top_enrichments(enrichment).to_csv(DATA_OUT / "bus_loac_top_enrichments.csv", index=False)

    draw_heatmap(
        enrichment,
        f"Bus K={BUS_K}: LOAC Supergroup enrichment (coverage-universe baseline)",
        FIGURE_OUT / "bus_loac_enrichment_heatmap.png",
    )
    draw_heatmap(
        row_pct,
        f"Bus K={BUS_K}: LOAC Supergroup composition within cluster",
        FIGURE_OUT / "bus_loac_composition_heatmap.png",
    )

    lsoa = gpd.read_file(LSOA_BOUNDARIES).to_crs("EPSG:27700")
    lsoa = lsoa.rename(columns={"LSOA21CD": "LSOA21CD"})[["LSOA21CD", "geometry"]]
    map_data = lsoa.merge(
        bus[["LSOA21CD", "cluster", "loac_dominant_supergroup"]], on="LSOA21CD", how="left"
    )
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    map_data.plot(
        column="cluster",
        categorical=True,
        cmap=ListedColormap(BUS_CLUSTER_COLOURS[:BUS_K]),
        linewidth=0,
        missing_kwds={"color": "#EEEEEE"},
        ax=axes[0],
        legend=True,
    )
    axes[0].set_title(f"Bus RQ1 clusters (K={BUS_K}, StopArea CLR)")
    map_data.plot(
        column="loac_dominant_supergroup",
        categorical=True,
        cmap=ListedColormap([LOAC_SUPERGROUP_COLOURS[g] for g in LOAC_SUPERGROUPS]),
        linewidth=0,
        missing_kwds={"color": "#EEEEEE"},
        ax=axes[1],
        legend=True,
    )
    axes[1].set_title("Dominant LOAC Supergroup in the bus analysis universe")
    for axis in axes:
        axis.set_axis_off()
    plt.tight_layout()
    plt.savefig(FIGURE_OUT / "bus_clusters_loac_map.png", dpi=220, bbox_inches="tight")
    plt.close()

    audit = {
        "input_rows": int(len(bus)),
        "fitted_rows": int(len(fitted)),
        "matched_loac_rows": int(matched.shape[0]),
        "unmatched_loac_rows": int(fitted["loac_dominant_supergroup"].isna().sum()),
        "match_rate": float(matched.shape[0] / len(fitted)) if len(fitted) else float("nan"),
        "clusters": int(matched["cluster"].nunique()),
    }
    pd.Series(audit).to_json(DATA_OUT / "bus_loac_audit.json", indent=2)
    pd.DataFrame([{"analysis": "bus_cluster_x_loac_dominant_supergroup_chi_square", **stats}]).to_csv(
        DATA_OUT / "bus_loac_statistical_summary.csv", index=False
    )
    print("Bus x LOAC audit:", audit)
    print("Bus x LOAC stats:", stats)


if __name__ == "__main__":
    main()
