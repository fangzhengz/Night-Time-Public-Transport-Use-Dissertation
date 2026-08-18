"""Rail RQ1 cluster x LOAC Supergroup catchment composition.

Mirrors ``rq2test analysis/src/run_analysis.py``'s ``build_rail_analysis``:
800 m Voronoi-clipped station catchments (radius per config.py, matching
``rq2_new_clusters_analysis``'s primary 800 m result), intersected directly
against LOAC's own OA-level geopackage (already EPSG:27700 -- no LSOA
intermediate needed). Rail clustering is ``numbat_all_area_test``'s all-modes
NaPTAN-matched 403-station K=5 refit (see config.py), matching
``rq2_new_clusters_analysis``'s choice.

Each station's own LOAC composition is an equal-weight average across the
distinct OAs its catchment intersects (fixed 2026-08-08; previously
area-weighted despite already being labelled "equal_weight" downstream).
"""

from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
from matplotlib.colors import ListedColormap
from scipy.spatial import Voronoi
from shapely.geometry import Polygon

from config import (
    CRS_BNG,
    DATA_OUT,
    FIGURE_OUT,
    LOAC_OA_GPKG,
    LOAC_SUPERGROUP_COLOURS,
    LOAC_SUPERGROUPS,
    N_PERMUTATIONS,
    RAIL_CATCHMENT_METRES,
    RAIL_COORDS,
    RAIL_K,
    RAIL_LABELS,
    RAIL_META,
    RANDOM_SEED,
    SPATIAL_OUT,
)
from geo_utils import finite_voronoi_polygons
from stats_utils import (
    association_outputs,
    composition_permutation_test,
    draw_heatmap,
    save_matrix,
    top_enrichments,
)

SHARE_COLUMNS = [f"loac_{sg}_share" for sg in LOAC_SUPERGROUPS]


def main() -> None:
    labels = pd.read_csv(RAIL_LABELS)
    coords = pd.read_csv(RAIL_COORDS)
    meta = pd.read_csv(RAIL_META).rename(columns={"NLC": "unit"})

    rail = labels.merge(coords, on="unit", how="left", validate="one_to_one")
    rail = rail.merge(meta[["unit", "total_activity"]], on="unit", how="left", validate="one_to_one")
    if rail[["easting", "northing"]].isna().any().any():
        missing = rail.loc[rail["easting"].isna(), "unit"].tolist()
        raise ValueError(f"Missing coordinates for units: {missing}")
    if rail.duplicated(["easting", "northing"]).any():
        raise ValueError("Duplicate rail coordinates prevent an unambiguous Voronoi diagram")

    stations = gpd.GeoDataFrame(
        rail, geometry=gpd.points_from_xy(rail["easting"], rail["northing"]), crs=CRS_BNG
    )
    points = np.column_stack([stations.geometry.x, stations.geometry.y])
    regions, vertices = finite_voronoi_polygons(Voronoi(points), radius=100_000)

    loac_oa = gpd.read_file(LOAC_OA_GPKG).to_crs(CRS_BNG)
    loac_oa["geometry"] = loac_oa.geometry.make_valid()
    loac_union = loac_oa.geometry.union_all()

    catchment_geometries = []
    for station_geometry, region in zip(stations.geometry, regions, strict=True):
        cell = Polygon(vertices[region])
        if not cell.is_valid:
            cell = shapely.make_valid(cell)
        catchment = station_geometry.buffer(RAIL_CATCHMENT_METRES).intersection(cell)
        catchment_geometries.append(catchment)

    catchments = gpd.GeoDataFrame(
        stations.drop(columns="geometry"), geometry=catchment_geometries, crs=CRS_BNG
    )
    catchments["catchment_area_m2"] = catchments.geometry.area
    catchments["station_in_loac_extent"] = stations.geometry.apply(loac_union.covers).to_numpy()

    intersections = gpd.overlay(
        catchments[["unit", "geometry"]],
        loac_oa[["OA21CD", "SG", "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    intersections["piece_area_m2"] = intersections.geometry.area
    intersections = intersections.loc[intersections["piece_area_m2"] > 0].copy()
    # Coverage stays area-based (data-completeness diagnostic: how much of the
    # catchment geometry is covered by a matched OA). The LOAC composition
    # itself is an equal-weight average across distinct intersecting OAs --
    # one vote per OA regardless of overlap area -- matching the estimand used
    # for LNWC (rq2_new_clusters_analysis) and the continuous variables
    # (rq2_independent_variables). Changed 2026-08-08, user decision: this was
    # previously area-weighted (piece_area_m2-weighted) despite being labelled
    # "equal_weight" downstream, where that name in fact only ever described
    # the separate station-level averaging within a cluster (see
    # ``equal_composition`` below), not this OA-level step.
    covered_area = intersections.groupby("unit")["piece_area_m2"].sum().rename("covered_area_m2")
    intersections = intersections.merge(covered_area, on="unit", validate="many_to_one")
    distinct_oa = intersections[["unit", "OA21CD", "SG"]].drop_duplicates()
    distinct_oa["equal_share"] = 1.0 / distinct_oa.groupby("unit")["OA21CD"].transform("nunique")

    shares = (
        distinct_oa.pivot_table(
            index="unit", columns="SG", values="equal_share", aggfunc="sum", fill_value=0
        )
        .reindex(columns=LOAC_SUPERGROUPS, fill_value=0)
        .rename(columns={sg: f"loac_{sg}_share" for sg in LOAC_SUPERGROUPS})
    )
    rail_analysis = catchments.drop(columns="geometry").merge(
        shares, left_on="unit", right_index=True, how="left", validate="one_to_one"
    )
    rail_analysis = rail_analysis.merge(
        covered_area, left_on="unit", right_index=True, how="left", validate="one_to_one"
    )
    rail_analysis["loac_coverage_ratio"] = (
        rail_analysis["covered_area_m2"] / rail_analysis["catchment_area_m2"]
    )
    valid_composition = rail_analysis[SHARE_COLUMNS].notna().all(axis=1)
    analysis_eligible = rail_analysis["station_in_loac_extent"] & valid_composition
    rail_analysis["analysis_eligible"] = analysis_eligible
    rail_analysis["dominant_loac_supergroup"] = pd.Series(pd.NA, index=rail_analysis.index, dtype="object")
    dominant_idx = rail_analysis.loc[analysis_eligible, SHARE_COLUMNS].to_numpy().argmax(axis=1)
    rail_analysis.loc[analysis_eligible, "dominant_loac_supergroup"] = [
        LOAC_SUPERGROUPS[i] for i in dominant_idx
    ]

    share_sums = rail_analysis.loc[valid_composition, SHARE_COLUMNS].sum(axis=1)
    if not np.allclose(share_sums, 1.0, atol=1e-6):
        raise AssertionError("Rail LOAC shares do not sum to one")

    rail_analysis.to_csv(DATA_OUT / "rail_loac_station.csv", index=False)
    catchments.to_crs("EPSG:4326").to_file(
        SPATIAL_OUT / f"rail_catchments_{RAIL_CATCHMENT_METRES}m.geojson", driver="GeoJSON"
    )

    rail_valid = rail_analysis.loc[analysis_eligible].copy()
    equal_composition = rail_valid.groupby("cluster")[SHARE_COLUMNS].mean()
    equal_composition.columns = LOAC_SUPERGROUPS
    benchmark = rail_valid[SHARE_COLUMNS].mean()
    benchmark.index = LOAC_SUPERGROUPS
    enrichment = equal_composition.div(benchmark, axis=1)

    save_matrix(equal_composition, DATA_OUT, "rail_loac_composition_equal_weight")
    save_matrix(enrichment, DATA_OUT, "rail_loac_enrichment")
    top_enrichments(enrichment).to_csv(DATA_OUT / "rail_loac_top_enrichments.csv", index=False)

    dominant = pd.crosstab(rail_valid["cluster"], rail_valid["dominant_loac_supergroup"]).reindex(
        index=sorted(rail_valid["cluster"].unique()), columns=LOAC_SUPERGROUPS, fill_value=0
    )
    (
        dominant_expected,
        dominant_row_pct,
        dominant_col_pct,
        dominant_enrichment,
        dominant_residual,
        dominant_stats,
    ) = association_outputs(dominant, LOAC_SUPERGROUPS)
    save_matrix(dominant, DATA_OUT, "rail_dominant_loac_counts")
    save_matrix(dominant_row_pct, DATA_OUT, "rail_dominant_loac_row_pct")

    permutation = composition_permutation_test(
        rail_valid[SHARE_COLUMNS].to_numpy(),
        rail_valid["cluster"].to_numpy(),
        N_PERMUTATIONS,
        RANDOM_SEED,
    )

    draw_heatmap(
        enrichment,
        f"Rail K={RAIL_K}: catchment LOAC Supergroup enrichment ({RAIL_CATCHMENT_METRES} m, equal weighting)",
        FIGURE_OUT / "rail_loac_enrichment_heatmap.png",
    )
    draw_heatmap(
        equal_composition,
        f"Rail K={RAIL_K}: mean LOAC Supergroup composition by station cluster",
        FIGURE_OUT / "rail_loac_composition_heatmap.png",
    )

    catchment_map = catchments.merge(
        rail_analysis[["unit", "dominant_loac_supergroup"]], on="unit", validate="one_to_one"
    )
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    catchment_map.plot(
        column="cluster", categorical=True, cmap="tab10", linewidth=0.2, edgecolor="white", ax=axes[0], legend=True
    )
    stations.plot(column="cluster", categorical=True, cmap="tab10", markersize=6, ax=axes[0])
    axes[0].set_title(f"Rail RQ1 clusters and {RAIL_CATCHMENT_METRES} m Voronoi catchments (K={RAIL_K}, all-modes)")
    catchment_map.dropna(subset=["dominant_loac_supergroup"]).plot(
        column="dominant_loac_supergroup",
        categorical=True,
        cmap=ListedColormap([LOAC_SUPERGROUP_COLOURS[g] for g in LOAC_SUPERGROUPS]),
        linewidth=0.2,
        edgecolor="white",
        ax=axes[1],
        legend=True,
    )
    axes[1].set_title("Dominant LOAC Supergroup within each rail catchment")
    for axis in axes:
        axis.set_axis_off()
    plt.tight_layout()
    plt.savefig(FIGURE_OUT / "rail_catchments_clusters_loac_map.png", dpi=220, bbox_inches="tight")
    plt.close()

    lowest_eligibility_cluster = (
        rail_analysis.groupby("cluster")["analysis_eligible"].mean().idxmin()
    )
    audit = {
        "input_rows": int(len(rail_analysis)),
        "stations_eligible_for_loac_analysis": int(analysis_eligible.sum()),
        "stations_outside_loac_extent": int((~rail_analysis["station_in_loac_extent"]).sum()),
        "stations_inside_without_loac_coverage": int(
            (rail_analysis["station_in_loac_extent"] & ~valid_composition).sum()
        ),
        "mean_loac_coverage_ratio": float(
            rail_analysis.loc[analysis_eligible, "loac_coverage_ratio"].mean()
        ),
        "minimum_loac_coverage_ratio": float(
            rail_analysis.loc[analysis_eligible, "loac_coverage_ratio"].min()
        ),
        "lowest_eligibility_cluster": int(lowest_eligibility_cluster),
        "clusters": int(rail_analysis["cluster"].nunique()),
    }
    pd.Series(audit).to_json(DATA_OUT / "rail_loac_audit.json", indent=2)
    pd.DataFrame(
        [
            {"analysis": "rail_cluster_x_loac_dominant_supergroup_chi_square", **dominant_stats},
            {
                "analysis": "rail_loac_composition_permutation",
                "chi_square": np.nan,
                "p_value": permutation["permutation_p"],
                "degrees_of_freedom": np.nan,
                "cramers_v": np.nan,
                "n": permutation["n"],
                "r_squared": permutation["r_squared"],
            },
        ]
    ).to_csv(DATA_OUT / "rail_loac_statistical_summary.csv", index=False)
    print("Rail x LOAC audit:", audit)
    print("Rail x LOAC dominant-Supergroup stats:", dominant_stats)
    print("Rail x LOAC composition permutation:", permutation)


if __name__ == "__main__":
    main()
