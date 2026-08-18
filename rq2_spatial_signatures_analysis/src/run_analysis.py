"""Run the fixed-label RQ2 Spatial Signatures sidecar analysis.

Outputs cover:
  * LSOA11 -> LSOA21 conversion and coverage audit;
  * direct Bus LSOA association;
  * Rail 800 m Voronoi-clipped catchments;
  * dominant-type chi-square/Cramer's V with permutation checks;
  * full-composition permutation R2;
  * equal-LSOA versus intersection-area Rail aggregation sensitivity.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shapely
from matplotlib.patches import Patch
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
from sklearn.metrics import adjusted_rand_score

import config as C
from geo_utils import finite_voronoi_polygons
from stats_utils import categorical_association, composition_permutation_test


def check_sources() -> None:
    required = [
        C.SIGNATURE_LSOA11,
        C.SIGNATURE_TYPES,
        C.SIGNATURE_META,
        C.LSOA11_LSOA21_LOOKUP,
        C.LSOA21_BOUNDARIES,
        C.BUS_LABELS,
        C.RAIL_LABELS,
        C.RAIL_COORDS,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")
    for name, expected in C.EXPECTED_MD5.items():
        path = C.SOURCE / name
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        if digest != expected:
            raise RuntimeError(f"Checksum mismatch for {path}: {digest} != {expected}")


def load_type_dictionary() -> tuple[list[str], dict[str, str]]:
    types = pd.read_csv(C.SIGNATURE_TYPES)
    code_to_name = dict(zip(types["type_code"], types["type_name"], strict=True))
    return types["type_code"].tolist(), code_to_name


def build_lsoa21_signatures(all_codes: list[str], code_to_name: dict[str, str]):
    source = pd.read_csv(C.SIGNATURE_LSOA11)
    lookup = pd.read_csv(C.LSOA11_LSOA21_LOOKUP)
    lookup = lookup.loc[lookup["LAD22CD"].astype(str).str.startswith("E09")].copy()
    lookup = lookup[["LSOA11CD", "LSOA21CD", "CHGIND"]]
    boundaries = gpd.read_file(C.LSOA21_BOUNDARIES).to_crs(C.CRS_BNG)
    boundary_code = "LSOA21CD" if "LSOA21CD" in boundaries.columns else "lsoa21cd"
    boundaries = boundaries.rename(columns={boundary_code: "LSOA21CD"})[
        ["LSOA21CD", "geometry"]
    ]

    # Exact-fit relationships intentionally repeat 2011 codes for splits and
    # 2021 codes for merges. This preserves all 2021 LSOAs, unlike a one-way
    # best-fit lookup that omits split descendants.
    merged = lookup.merge(source, on="LSOA11CD", how="left", validate="many_to_one")
    missing_source = int(merged[all_codes].isna().all(axis=1).sum())
    if missing_source:
        raise ValueError(f"{missing_source} London LSOA11 codes have no signature source row")

    grouped = merged.groupby("LSOA21CD", sort=True)[all_codes].mean()
    grouped = grouped.div(grouped.sum(axis=1).replace(0, np.nan), axis=0)
    grouped = grouped.dropna(how="all")
    grouped["n_lsoa11_sources"] = merged.groupby("LSOA21CD")["LSOA11CD"].nunique()
    grouped["signature_dominant_code"] = grouped[all_codes].idxmax(axis=1)
    grouped["signature_dominant_type"] = grouped["signature_dominant_code"].map(code_to_name)
    out = grouped.reset_index()

    boundary_codes = set(boundaries["LSOA21CD"])
    output_codes = set(out["LSOA21CD"])
    audit = {
        "source_lsoa11_rows": int(len(source)),
        "london_exact_fit_rows": int(len(lookup)),
        "london_lookup_unique_lsoa11": int(lookup["LSOA11CD"].nunique()),
        "london_lookup_unique_lsoa21": int(lookup["LSOA21CD"].nunique()),
        "change_indicator_counts": {
            str(key): int(value) for key, value in lookup["CHGIND"].value_counts().items()
        },
        "london_lsoa21_rows": int(len(boundaries)),
        "matched_lsoa21_rows": int(len(output_codes & boundary_codes)),
        "unmatched_lsoa21_rows": int(len(boundary_codes - output_codes)),
        "lsoa21_with_multiple_lsoa11_sources": int((out["n_lsoa11_sources"] > 1).sum()),
        "coverage_rate": float(len(output_codes & boundary_codes) / len(boundary_codes)),
    }
    if audit["coverage_rate"] < 0.95:
        raise RuntimeError(f"Spatial Signature LSOA21 coverage below acceptance threshold: {audit}")
    if not np.allclose(out[all_codes].sum(axis=1), 1.0, atol=1e-7):
        raise AssertionError("Converted LSOA21 signature compositions do not sum to one")

    out.to_csv(C.DATA_OUT / "spatial_signatures_lsoa21_london.csv", index=False)
    pd.Series(audit).to_json(C.DATA_OUT / "lsoa21_conversion_audit.json", indent=2)
    return out, boundaries, audit


def distance_km(x: pd.Series, y: pd.Series) -> pd.Series:
    return np.sqrt(
        (x - C.CHARING_CROSS_EASTING) ** 2 + (y - C.CHARING_CROSS_NORTHING) ** 2
    ) / 1000


def distance_bands(values: pd.Series) -> np.ndarray:
    return pd.qcut(values, q=5, labels=False, duplicates="drop").to_numpy()


def collapse_rare_categories(
    categories: pd.Series, london_counts: pd.Series, london_n: int
) -> tuple[pd.Series, list[str], set[str]]:
    threshold = max(20, int(np.ceil(0.01 * london_n)))
    rare = set(london_counts[london_counts < threshold].index)
    collapsed = categories.where(~categories.isin(rare), "OTHER_RARE")
    order = [code for code in london_counts.index if code not in rare]
    if collapsed.eq("OTHER_RARE").any():
        order.append("OTHER_RARE")
    return collapsed, order, rare


def save_association(prefix: str, result, cluster_name_map: dict[int, str]):
    observed, expected, row_pct, enrichment, residual, stats = result
    for name, matrix in {
        "counts": observed,
        "expected": expected,
        "row_pct": row_pct,
        "enrichment": enrichment,
        "standardized_residuals": residual,
    }.items():
        matrix.rename_axis(index="cluster", columns="spatial_signature").to_csv(
            C.DATA_OUT / f"{prefix}_{name}.csv"
        )
    pd.DataFrame([stats]).to_csv(C.DATA_OUT / f"{prefix}_statistical_summary.csv", index=False)

    display = enrichment.copy()
    display.index = [cluster_name_map.get(int(i), f"C{i}") for i in display.index]
    plt.figure(figsize=(max(11, 1.1 * len(display.columns)), max(4.5, 0.8 * len(display))))
    sns.heatmap(
        display,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=1,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Enrichment ratio"},
    )
    plt.title(f"{prefix.replace('_', ' ').title()}: dominant Spatial Signature enrichment")
    plt.xlabel("Spatial Signature code")
    plt.ylabel("Fixed RQ1 cluster")
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / f"{prefix}_enrichment_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close()
    return stats


def save_composition_heatmap(
    composition: pd.DataFrame,
    prefix: str,
    cluster_name_map: dict[int, str],
):
    display = composition.copy()
    display.index = [cluster_name_map.get(int(i), f"C{i}") for i in display.index]
    plt.figure(figsize=(max(12, 0.9 * len(display.columns)), max(4.5, 0.8 * len(display))))
    sns.heatmap(
        display,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"label": "Mean composition share"},
    )
    plt.title(f"{prefix.replace('_', ' ').title()}: mean Spatial Signature composition")
    plt.xlabel("Spatial Signature code")
    plt.ylabel("Fixed RQ1 cluster")
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / f"{prefix}_composition_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close()


def top_enrichments(enrichment: pd.DataFrame, mode: str) -> pd.DataFrame:
    rows = []
    for cluster, values in enrichment.iterrows():
        for code, ratio in values.sort_values(ascending=False).head(3).items():
            rows.append(
                {"mode": mode, "cluster": int(cluster), "signature_code": code, "enrichment": ratio}
            )
    return pd.DataFrame(rows)


def build_bus(
    signatures: pd.DataFrame,
    boundaries: gpd.GeoDataFrame,
    active_codes: list[str],
    london_counts: pd.Series,
):
    labels = pd.read_csv(C.BUS_LABELS)
    labels = labels.loc[labels["retained_for_fit"]].copy()
    names = pd.read_csv(C.BUS_CLUSTER_NAMES)
    cluster_name_map = dict(zip(names["cluster"], names["name_en"], strict=True))

    centroids = boundaries.copy()
    centroids["distance_centre_km"] = distance_km(
        centroids.geometry.centroid.x, centroids.geometry.centroid.y
    )
    bus = labels.merge(
        signatures, left_on="lsoa", right_on="LSOA21CD", how="left", validate="one_to_one"
    ).merge(
        centroids[["LSOA21CD", "distance_centre_km"]], on="LSOA21CD", how="left", validate="one_to_one"
    )
    eligible = bus[active_codes].notna().all(axis=1)
    valid = bus.loc[eligible].copy()
    collapsed, category_order, rare = collapse_rare_categories(
        valid["signature_dominant_code"], london_counts, len(signatures)
    )
    valid["signature_dominant_collapsed"] = collapsed

    association = categorical_association(
        valid["cluster"].to_numpy(),
        valid["signature_dominant_collapsed"].to_numpy(dtype=object),
        category_order,
        distance_bands(valid["distance_centre_km"]),
        C.N_PERMUTATIONS,
        C.RANDOM_SEED,
    )
    stats = save_association("bus_spatial_signature", association, cluster_name_map)

    cluster_composition = valid.groupby("cluster")[active_codes].mean()
    cluster_composition.to_csv(C.DATA_OUT / "bus_spatial_signature_composition.csv")
    benchmark = valid[active_codes].mean()
    enrichment = cluster_composition.div(benchmark, axis=1)
    enrichment.to_csv(C.DATA_OUT / "bus_spatial_signature_composition_enrichment.csv")
    save_composition_heatmap(cluster_composition, "bus_spatial_signature", cluster_name_map)
    composition_stats = composition_permutation_test(
        valid[active_codes].to_numpy(),
        valid["cluster"].to_numpy(),
        C.N_PERMUTATIONS,
        C.RANDOM_SEED,
    )
    pd.DataFrame([composition_stats]).to_csv(
        C.DATA_OUT / "bus_spatial_signature_composition_permutation.csv", index=False
    )
    valid.to_csv(C.DATA_OUT / "bus_spatial_signature_lsoa.csv", index=False)
    top_enrichments(enrichment, "bus").to_csv(
        C.DATA_OUT / "bus_spatial_signature_top_composition_enrichments.csv", index=False
    )

    audit = {
        "fixed_cluster_rows": int(len(labels)),
        "matched_rows": int(len(valid)),
        "unmatched_rows": int((~eligible).sum()),
        "coverage_rate": float(eligible.mean()),
        "rare_dominant_codes_collapsed": sorted(rare),
    }
    pd.Series(audit).to_json(C.DATA_OUT / "bus_spatial_signature_audit.json", indent=2)
    return valid, stats, composition_stats, audit, cluster_name_map


def build_rail(
    signatures: pd.DataFrame,
    boundaries: gpd.GeoDataFrame,
    active_codes: list[str],
    london_counts: pd.Series,
):
    labels = pd.read_csv(C.RAIL_LABELS)
    coords = pd.read_csv(C.RAIL_COORDS)
    meta = pd.read_csv(C.RAIL_META).rename(columns={"NLC": "unit"})
    names = pd.read_csv(C.RAIL_CLUSTER_NAMES)
    cluster_name_map = dict(zip(names["cluster"], names["name_en"], strict=True))

    rail = labels.merge(coords, on="unit", how="left", validate="one_to_one").merge(
        meta[["unit", "total_activity"]], on="unit", how="left", validate="one_to_one"
    )
    rail["distance_centre_km"] = distance_km(rail["easting"], rail["northing"])
    if rail[["easting", "northing"]].isna().any().any():
        raise ValueError("Rail labels contain units without coordinates")
    if rail.duplicated(["easting", "northing"]).any():
        raise ValueError("Duplicate Rail coordinates prevent Voronoi construction")

    stations = gpd.GeoDataFrame(
        rail, geometry=gpd.points_from_xy(rail["easting"], rail["northing"]), crs=C.CRS_BNG
    )
    points = np.column_stack([stations.geometry.x, stations.geometry.y])
    regions, vertices = finite_voronoi_polygons(Voronoi(points), radius=100_000)
    catchment_geometries = []
    for station_geometry, region in zip(stations.geometry, regions, strict=True):
        cell = Polygon(vertices[region])
        if not cell.is_valid:
            cell = shapely.make_valid(cell)
        catchment_geometries.append(
            station_geometry.buffer(C.RAIL_CATCHMENT_METRES).intersection(cell)
        )
    catchments = gpd.GeoDataFrame(
        stations.drop(columns="geometry"), geometry=catchment_geometries, crs=C.CRS_BNG
    )
    catchments["catchment_area_m2"] = catchments.geometry.area
    london_union = boundaries.geometry.union_all()
    catchments["station_in_london"] = stations.geometry.apply(london_union.covers).to_numpy()

    intersections = gpd.overlay(
        catchments[["unit", "geometry"]], boundaries, how="intersection", keep_geom_type=False
    )
    intersections["piece_area_m2"] = intersections.geometry.area
    intersections = intersections.loc[intersections["piece_area_m2"] > 0].copy()
    unit_lsoa = (
        intersections.groupby(["unit", "LSOA21CD"], as_index=False)["piece_area_m2"].sum()
        .merge(signatures[["LSOA21CD"] + active_codes], on="LSOA21CD", how="left", validate="many_to_one")
    )
    if unit_lsoa[active_codes].isna().any(axis=1).any():
        raise ValueError("A Rail catchment intersects an LSOA without Spatial Signature composition")

    equal = unit_lsoa.groupby("unit")[active_codes].mean()
    weighted_values = unit_lsoa[active_codes].mul(unit_lsoa["piece_area_m2"], axis=0)
    weighted_values["unit"] = unit_lsoa["unit"].to_numpy()
    area = weighted_values.groupby("unit")[active_codes].sum().div(
        unit_lsoa.groupby("unit")["piece_area_m2"].sum(), axis=0
    )
    equal = equal.div(equal.sum(axis=1), axis=0)
    area = area.div(area.sum(axis=1), axis=0)

    covered = unit_lsoa.groupby("unit")["piece_area_m2"].sum().rename("covered_area_m2")
    analysis = catchments.drop(columns="geometry").merge(
        equal.add_prefix("equal_"), left_on="unit", right_index=True, how="left", validate="one_to_one"
    ).merge(
        area.add_prefix("area_"), left_on="unit", right_index=True, how="left", validate="one_to_one"
    ).merge(covered, left_on="unit", right_index=True, how="left", validate="one_to_one")
    analysis["coverage_ratio"] = analysis["covered_area_m2"] / analysis["catchment_area_m2"]
    equal_cols = [f"equal_{code}" for code in active_codes]
    area_cols = [f"area_{code}" for code in active_codes]
    eligible = analysis["station_in_london"] & analysis[equal_cols].notna().all(axis=1)
    valid = analysis.loc[eligible].copy()
    valid["signature_dominant_equal"] = valid[equal_cols].idxmax(axis=1).str.removeprefix("equal_")
    valid["signature_dominant_area"] = valid[area_cols].idxmax(axis=1).str.removeprefix("area_")
    valid["signature_dominant_agreement"] = (
        valid["signature_dominant_equal"] == valid["signature_dominant_area"]
    )
    collapsed, category_order, rare = collapse_rare_categories(
        valid["signature_dominant_equal"], london_counts, len(signatures)
    )
    valid["signature_dominant_collapsed"] = collapsed

    association = categorical_association(
        valid["cluster"].to_numpy(),
        valid["signature_dominant_collapsed"].to_numpy(dtype=object),
        category_order,
        distance_bands(valid["distance_centre_km"]),
        C.N_PERMUTATIONS,
        C.RANDOM_SEED,
    )
    stats = save_association("rail_spatial_signature", association, cluster_name_map)

    equal_comp = valid.groupby("cluster")[equal_cols].mean()
    equal_comp.columns = active_codes
    area_comp = valid.groupby("cluster")[area_cols].mean()
    area_comp.columns = active_codes
    equal_comp.to_csv(C.DATA_OUT / "rail_spatial_signature_composition_equal_lsoa.csv")
    area_comp.to_csv(C.DATA_OUT / "rail_spatial_signature_composition_area_weighted.csv")
    benchmark = valid[equal_cols].mean()
    benchmark.index = active_codes
    enrichment = equal_comp.div(benchmark, axis=1)
    enrichment.to_csv(C.DATA_OUT / "rail_spatial_signature_composition_enrichment.csv")
    save_composition_heatmap(equal_comp, "rail_spatial_signature", cluster_name_map)
    top_enrichments(enrichment, "rail").to_csv(
        C.DATA_OUT / "rail_spatial_signature_top_composition_enrichments.csv", index=False
    )

    equal_stats = composition_permutation_test(
        valid[equal_cols].to_numpy(), valid["cluster"].to_numpy(), C.N_PERMUTATIONS, C.RANDOM_SEED
    )
    area_stats = composition_permutation_test(
        valid[area_cols].to_numpy(), valid["cluster"].to_numpy(), C.N_PERMUTATIONS, C.RANDOM_SEED
    )
    sensitivity = {
        "dominant_equal_area_agreement": float(valid["signature_dominant_agreement"].mean()),
        "dominant_equal_area_adjusted_rand": float(
            adjusted_rand_score(valid["signature_dominant_equal"], valid["signature_dominant_area"])
        ),
        "equal_composition_r_squared": equal_stats["r_squared"],
        "area_composition_r_squared": area_stats["r_squared"],
        "equal_composition_permutation_p": equal_stats["permutation_p"],
        "area_composition_permutation_p": area_stats["permutation_p"],
    }
    pd.DataFrame([sensitivity]).to_csv(
        C.DATA_OUT / "rail_spatial_signature_aggregation_sensitivity.csv", index=False
    )
    pd.DataFrame([equal_stats]).to_csv(
        C.DATA_OUT / "rail_spatial_signature_composition_equal_permutation.csv", index=False
    )
    pd.DataFrame([area_stats]).to_csv(
        C.DATA_OUT / "rail_spatial_signature_composition_area_permutation.csv", index=False
    )
    valid.to_csv(C.DATA_OUT / "rail_spatial_signature_station.csv", index=False)
    catchments.to_crs(C.CRS_WGS84).to_file(
        C.SPATIAL_OUT / f"rail_catchments_{C.RAIL_CATCHMENT_METRES}m.geojson", driver="GeoJSON"
    )

    audit = {
        "fixed_cluster_rows": int(len(labels)),
        "eligible_rows": int(len(valid)),
        "ineligible_rows": int((~eligible).sum()),
        "coverage_rate": float(eligible.mean()),
        "mean_catchment_london_coverage": float(valid["coverage_ratio"].mean()),
        "minimum_catchment_london_coverage": float(valid["coverage_ratio"].min()),
        "median_intersecting_lsoa": float(unit_lsoa.groupby("unit").size().median()),
        "rare_dominant_codes_collapsed": sorted(rare),
    }
    pd.Series(audit).to_json(C.DATA_OUT / "rail_spatial_signature_audit.json", indent=2)
    return valid, stats, equal_stats, area_stats, sensitivity, audit, cluster_name_map


def plot_maps(
    bus: pd.DataFrame,
    rail: pd.DataFrame,
    boundaries: gpd.GeoDataFrame,
    active_codes: list[str],
):
    palette = sns.color_palette("tab20", n_colors=len(active_codes)).as_hex()
    colour_map = dict(zip(active_codes, palette, strict=True))

    bus_map = boundaries.merge(
        bus[["LSOA21CD", "signature_dominant_code"]], on="LSOA21CD", how="left"
    )
    fig, ax = plt.subplots(figsize=(10, 10))
    for code in active_codes:
        subset = bus_map.loc[bus_map["signature_dominant_code"] == code]
        if len(subset):
            subset.plot(ax=ax, color=colour_map[code], linewidth=0, label=code)
    bus_map.loc[bus_map["signature_dominant_code"].isna()].plot(
        ax=ax, color="#eeeeee", linewidth=0
    )
    ax.set_axis_off()
    ax.set_title("Dominant Spatial Signature across fitted Bus LSOAs")
    bus_codes = [
        code for code in active_codes if bus_map["signature_dominant_code"].eq(code).any()
    ]
    bus_handles = [Patch(facecolor=colour_map[code], edgecolor="none", label=code) for code in bus_codes]
    ax.legend(handles=bus_handles, ncol=3, fontsize=8, loc="lower left")
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / "bus_spatial_signature_map.png", dpi=220, bbox_inches="tight")
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 10))
    boundaries.boundary.plot(ax=ax, color="#d9d9d9", linewidth=0.15)
    for code in active_codes:
        subset = rail.loc[rail["signature_dominant_equal"] == code]
        if len(subset):
            ax.scatter(
                subset["easting"], subset["northing"], s=20, color=colour_map[code], label=code
            )
    ax.set_axis_off()
    ax.set_title("Dominant Spatial Signature in 800 m Rail catchments")
    ax.legend(ncol=3, fontsize=8, loc="lower left")
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / "rail_spatial_signature_map.png", dpi=220, bbox_inches="tight")
    plt.close()


def write_report(
    type_names: dict[str, str],
    lsoa_audit: dict,
    bus_stats: dict,
    bus_comp: dict,
    bus_audit: dict,
    rail_stats: dict,
    rail_equal: dict,
    rail_area: dict,
    rail_sensitivity: dict,
    rail_audit: dict,
):
    active = pd.read_csv(C.DATA_OUT / "spatial_signatures_lsoa21_london.csv")
    active_counts = active["signature_dominant_code"].value_counts()
    type_lines = "\n".join(
        f"- `{code}` {type_names.get(code, code)}: {int(count)} London LSOA21s"
        for code, count in active_counts.items()
    )
    report = f"""# RQ2 Spatial Signatures sidecar results

## Status and scope

This analysis keeps the adopted Rail K=5 and Bus K=4 labels fixed. Spatial
Signatures are an external area/context layer, not clustering inputs and not
passenger characteristics.

Source: Fleischmann and Arribas-Bel, Figshare article 16691575, DOI
`10.6084/m9.figshare.16691575.v3`. The source metadata states temporal coverage
2020 and OGL licensing. The source LSOA11 compositions were converted to London
LSOA21 using the ONS exact-fit V3 lookup, which preserves no-change, split and
merge relationships. All 4,994 London LSOA21s are covered; 22 combine more than
one LSOA11 source row.

## Coverage

- LSOA21: {lsoa_audit['matched_lsoa21_rows']}/{lsoa_audit['london_lsoa21_rows']} ({lsoa_audit['coverage_rate']:.3%}).
- Bus fitted sample: {bus_audit['matched_rows']}/{bus_audit['fixed_cluster_rows']} ({bus_audit['coverage_rate']:.3%}).
- Rail context-eligible sample: {rail_audit['eligible_rows']}/{rail_audit['fixed_cluster_rows']} ({rail_audit['coverage_rate']:.3%}); the 16 excluded stations are outside the strict Greater London boundary, matching the existing RQ2 context universe.
- Rail catchment London coverage: mean {rail_audit['mean_catchment_london_coverage']:.3f}, minimum {rail_audit['minimum_catchment_london_coverage']:.3f}.

## London dominant-type distribution

{type_lines}

## Bus association

- Dominant type: Cramer's V = {bus_stats['cramers_v']:.3f}; unconditional permutation p = {bus_stats['permutation_p']:.3f}.
- Approximate centre-distance-conditioned permutation p = {bus_stats['distance_band_conditional_p']:.3f}.
- Sparse expected cells (<5): {bus_stats['expected_cells_lt5_fraction']:.1%}; interpret the permutation result and effect size rather than relying only on asymptotic chi-square p.
- Full-composition permutation R2 = {bus_comp['r_squared']:.3f}, p = {bus_comp['permutation_p']:.3f}.

## Rail association

- Dominant type (equal-LSOA catchment composition): Cramer's V = {rail_stats['cramers_v']:.3f}; unconditional permutation p = {rail_stats['permutation_p']:.3f}.
- Approximate centre-distance-conditioned permutation p = {rail_stats['distance_band_conditional_p']:.3f}.
- Sparse expected cells (<5): {rail_stats['expected_cells_lt5_fraction']:.1%}.
- Equal-LSOA full-composition R2 = {rail_equal['r_squared']:.3f}, p = {rail_equal['permutation_p']:.3f}.
- Intersection-area-weighted full-composition R2 = {rail_area['r_squared']:.3f}, p = {rail_area['permutation_p']:.3f}.
- Equal-versus-area dominant-type agreement = {rail_sensitivity['dominant_equal_area_agreement']:.1%}; ARI = {rail_sensitivity['dominant_equal_area_adjusted_rand']:.3f}.

## Interpretation boundary

Spatial Signatures describe urban form and function around Bus LSOAs and Rail
catchments. They may improve the CBD/airport/nightlife contextual description
relative to resident-only Census indicators, but they remain a 2020 area-level
classification. Association does not identify travellers, trip purposes, causal
mechanisms, unmet demand, or service deficiencies. The distance-band conditional
permutation is only a coarse centrality sensitivity and does not remove spatial
autocorrelation.
"""
    (C.REPORT_OUT / "RESULTS.md").write_text(report, encoding="utf-8")


def main():
    check_sources()
    all_codes, type_names = load_type_dictionary()
    signatures, boundaries, lsoa_audit = build_lsoa21_signatures(all_codes, type_names)
    active_codes = [code for code in all_codes if signatures[code].sum() > 1e-12]
    london_counts = signatures["signature_dominant_code"].value_counts()

    bus, bus_stats, bus_comp, bus_audit, _ = build_bus(
        signatures, boundaries, active_codes, london_counts
    )
    rail, rail_stats, rail_equal, rail_area, rail_sensitivity, rail_audit, _ = build_rail(
        signatures, boundaries, active_codes, london_counts
    )
    plot_maps(bus, rail, boundaries, active_codes)
    write_report(
        type_names,
        lsoa_audit,
        bus_stats,
        bus_comp,
        bus_audit,
        rail_stats,
        rail_equal,
        rail_area,
        rail_sensitivity,
        rail_audit,
    )
    manifest = {
        "fixed_bus_labels": str(C.BUS_LABELS),
        "fixed_rail_labels": str(C.RAIL_LABELS),
        "signature_source": str(C.SIGNATURE_LSOA11),
        "lsoa11_lsoa21_exact_fit_lookup": str(C.LSOA11_LSOA21_LOOKUP),
        "validated_source_md5": C.EXPECTED_MD5,
        "signature_source_doi": "10.6084/m9.figshare.16691575.v3",
        "signature_temporal_coverage": 2020,
        "signature_license": "OGL",
        "rail_catchment_metres": C.RAIL_CATCHMENT_METRES,
        "n_permutations": C.N_PERMUTATIONS,
        "seed": C.RANDOM_SEED,
        "active_signature_codes": active_codes,
    }
    (C.REPORT_OUT / "RUN_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("Spatial Signatures sidecar completed.")
    print("Bus dominant association:", bus_stats)
    print("Bus composition:", bus_comp)
    print("Rail dominant association:", rail_stats)
    print("Rail equal composition:", rail_equal)
    print("Rail area composition:", rail_area)
    print("Rail aggregation sensitivity:", rail_sensitivity)


if __name__ == "__main__":
    main()
