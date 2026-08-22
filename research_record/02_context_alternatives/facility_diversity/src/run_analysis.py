"""Fixed-label RQ2 facility-count and facility-diversity sidecar."""

from __future__ import annotations

import argparse
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
from scipy.stats import kruskal

import config as C

GROUP_NAMES = {
    "01": "Accommodation, eating and drinking",
    "02": "Commercial services",
    "03": "Attractions",
    "04": "Sport and entertainment",
    "05": "Education and health",
    "06": "Public infrastructure",
    "07": "Manufacturing and production",
    "09": "Retail",
    "10": "Transport",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--poi", required=True, type=Path, help="OS Points of Interest GeoPackage or CSV")
    parser.add_argument("--layer", help="Optional layer name when the spatial file contains multiple layers")
    return parser.parse_args()


def resolve_column(frame: pd.DataFrame, candidates: list[str], required: bool = True):
    normalised = {str(column).strip().lower(): column for column in frame.columns}
    for candidate in candidates:
        if candidate.lower() in normalised:
            return normalised[candidate.lower()]
    if required:
        raise KeyError(f"None of {candidates} found. Available columns: {frame.columns.tolist()}")
    return None


def stream_sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_poi(path: Path, layer: str | None = None):
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        raw = pd.read_csv(path, low_memory=False)
        easting = resolve_column(raw, ["feature_easting", "easting", "x_coordinate", "x"])
        northing = resolve_column(raw, ["feature_northing", "northing", "y_coordinate", "y"])
        poi = gpd.GeoDataFrame(
            raw,
            geometry=gpd.points_from_xy(pd.to_numeric(raw[easting]), pd.to_numeric(raw[northing])),
            crs=C.CRS_BNG,
        )
    else:
        poi = gpd.read_file(path, layer=layer)
        if poi.crs is None:
            raise ValueError("POI spatial file has no CRS")
        poi = poi.to_crs(C.CRS_BNG)

    class_column = resolve_column(
        poi,
        ["pointx_classification_code", "pointx_class", "classification_code", "class_code", "classcode"],
    )
    id_column = resolve_column(
        poi,
        ["reference_number", "ref_no", "poi_reference", "uprn", "id", "objectid"],
        required=False,
    )
    poi = poi.loc[poi.geometry.notna() & ~poi.geometry.is_empty].copy()
    poi["poi_id"] = poi[id_column].astype(str) if id_column else poi.index.astype(str)
    raw_code = poi[class_column].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    poi["classification_code"] = raw_code.str.zfill(8)
    valid_code = poi["classification_code"].str.fullmatch(r"\d{8}")
    invalid_classification_rows = int((~valid_code).sum())
    poi = poi.loc[valid_code].copy()
    poi["group_code"] = poi["classification_code"].str[:2]
    poi["category_code"] = poi["classification_code"].str[:4]
    duplicate_ids = int(poi["poi_id"].duplicated().sum())
    poi = poi.drop_duplicates("poi_id", keep="first").copy()
    audit = {
        "source_path": str(path.resolve()),
        "source_sha256": stream_sha256(path),
        "source_layer": layer,
        "valid_unique_poi_rows": int(len(poi)),
        "invalid_classification_rows": invalid_classification_rows,
        "duplicate_identifier_rows_removed": duplicate_ids,
        "observed_group_count": int(poi["group_code"].nunique()),
        "observed_category_count": int(poi["category_code"].nunique()),
    }
    return poi[["poi_id", "group_code", "category_code", "geometry"]], audit


def shannon_from_counts(counts: pd.DataFrame):
    totals = counts.sum(axis=1)
    shares = counts.div(totals.replace(0, np.nan), axis=0)
    return -(shares * np.log(shares.where(shares > 0))).sum(axis=1).fillna(0.0)


def build_metrics(joined: pd.DataFrame, units: pd.DataFrame, unit_col: str):
    result = units[[unit_col, "cluster", "area_km2", "distance_centre_km"]].copy()
    if joined.empty:
        raise ValueError("No POIs were spatially assigned to the analysis units")
    joined = joined.drop_duplicates([unit_col, "poi_id"]).copy()

    def metrics_for_subset(frame: pd.DataFrame, suffix: str):
        total = frame.groupby(unit_col)["poi_id"].nunique().rename(f"poi_count{suffix}")
        group_counts = pd.crosstab(frame[unit_col], frame["group_code"])
        category_counts = pd.crosstab(frame[unit_col], frame["category_code"])
        values = pd.concat(
            [
                total,
                shannon_from_counts(group_counts).rename(f"shannon_group{suffix}"),
                shannon_from_counts(category_counts).rename(f"shannon_category{suffix}"),
                (group_counts > 0).sum(axis=1).rename(f"group_richness{suffix}"),
                (category_counts > 0).sum(axis=1).rename(f"category_richness{suffix}"),
            ],
            axis=1,
        )
        return values

    all_values = metrics_for_subset(joined, "")
    no_transport = metrics_for_subset(joined.loc[joined["group_code"] != C.TRANSPORT_GROUP_CODE], "_no_transport")
    result = result.merge(all_values, left_on=unit_col, right_index=True, how="left")
    result = result.merge(no_transport, left_on=unit_col, right_index=True, how="left")
    metric_columns = [column for column in result if column not in {unit_col, "cluster", "area_km2", "distance_centre_km"}]
    result[metric_columns] = result[metric_columns].fillna(0.0)
    for suffix in ("", "_no_transport"):
        result[f"log1p_poi_count{suffix}"] = np.log1p(result[f"poi_count{suffix}"])
        result[f"poi_density_km2{suffix}"] = result[f"poi_count{suffix}"] / result["area_km2"]
    return result


def facility_group_profile(joined: pd.DataFrame, units: pd.DataFrame, unit_col: str):
    counts = pd.crosstab(joined[unit_col], joined["group_code"])
    counts = counts.reindex(columns=sorted(GROUP_NAMES), fill_value=0)
    shares = counts.div(counts.sum(axis=1), axis=0).fillna(0.0)
    shares = units[[unit_col, "cluster"]].merge(
        shares, left_on=unit_col, right_index=True, how="left", validate="one_to_one"
    )
    shares[list(GROUP_NAMES)] = shares[list(GROUP_NAMES)].fillna(0.0)
    profile = shares.groupby("cluster")[list(GROUP_NAMES)].mean()
    profile = profile.rename(columns={code: f"{code} {name}" for code, name in GROUP_NAMES.items()})
    return profile


def distance_bands(values: pd.Series):
    return pd.qcut(values, q=5, labels=False, duplicates="drop").to_numpy()


def kw_stat(values: np.ndarray, clusters: np.ndarray):
    groups = [values[clusters == cluster] for cluster in np.unique(clusters)]
    return float(kruskal(*groups).statistic)


def bh_adjust(p_values: pd.Series):
    values = p_values.to_numpy(float)
    order = np.argsort(values)
    ranked = values[order]
    adjusted = np.minimum.accumulate((ranked * len(values) / np.arange(1, len(values) + 1))[::-1])[::-1]
    adjusted = np.minimum(adjusted, 1.0)
    output = np.empty_like(adjusted)
    output[order] = adjusted
    return output


def association_table(metrics: pd.DataFrame, unit_col: str, mode: str):
    primary_and_sensitivity = [
        "log1p_poi_count",
        "poi_density_km2",
        "shannon_group",
        "shannon_category",
        "log1p_poi_count_no_transport",
        "poi_density_km2_no_transport",
        "shannon_group_no_transport",
        "shannon_category_no_transport",
    ]
    clusters = metrics["cluster"].to_numpy()
    bands = distance_bands(metrics["distance_centre_km"])
    rng = np.random.default_rng(C.RANDOM_SEED)
    rows = []
    for variable in primary_and_sensitivity:
        values = metrics[variable].to_numpy(float)
        observed = kw_stat(values, clusters)
        groups = [values[clusters == cluster] for cluster in np.unique(clusters)]
        test = kruskal(*groups)
        n = len(values)
        k = len(groups)
        epsilon_squared = max(0.0, float((test.statistic - k + 1) / (n - k)))
        exceed = 0
        for _ in range(C.N_PERMUTATIONS):
            permuted = clusters.copy()
            for band in np.unique(bands):
                index = np.flatnonzero(bands == band)
                permuted[index] = rng.permutation(permuted[index])
            exceed += kw_stat(values, permuted) >= observed - 1e-12
        rows.append(
            {
                "mode": mode,
                "variable": variable,
                "n": n,
                "kw_h": float(test.statistic),
                "p_value": float(test.pvalue),
                "epsilon_squared": epsilon_squared,
                "distance_band_conditional_p": (exceed + 1) / (C.N_PERMUTATIONS + 1),
            }
        )
    table = pd.DataFrame(rows)
    table["q_value_bh"] = bh_adjust(table["p_value"])
    return table


def cluster_zmeans(metrics: pd.DataFrame, variables: list[str]):
    standardised = metrics[variables].apply(lambda x: (x - x.mean()) / x.std(ddof=0))
    standardised["cluster"] = metrics["cluster"].to_numpy()
    return standardised.groupby("cluster")[variables].mean()


def plot_heatmap(table: pd.DataFrame, mode: str, names_path: Path):
    names = pd.read_csv(names_path)
    name_map = dict(zip(names["cluster"], names["name_en"], strict=True))
    display = table.copy()
    display.index = [name_map.get(int(cluster), f"C{cluster}") for cluster in display.index]
    plt.figure(figsize=(12, max(4, 0.8 * len(display))))
    sns.heatmap(display, annot=True, fmt=".2f", center=0, cmap="RdBu_r", linewidths=0.4)
    plt.title(f"{mode}: standardised facility metrics by fixed RQ1 cluster")
    plt.xlabel("Facility metric")
    plt.ylabel("Fixed RQ1 cluster")
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / f"{mode.lower()}_facility_context_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close()


def build_bus(poi: gpd.GeoDataFrame):
    labels = pd.read_csv(C.BUS_LABELS)
    labels = labels.loc[labels["retained_for_fit"], ["lsoa", "cluster"]].copy()
    boundaries = gpd.read_file(C.LSOA21_BOUNDARIES).to_crs(C.CRS_BNG)
    boundaries = boundaries[["LSOA21CD", "geometry"]].merge(
        labels, left_on="LSOA21CD", right_on="lsoa", how="inner", validate="one_to_one"
    )
    boundaries["area_km2"] = boundaries.geometry.area / 1_000_000
    centroid = boundaries.geometry.centroid
    boundaries["distance_centre_km"] = np.sqrt(
        (centroid.x - C.CHARING_CROSS_EASTING) ** 2 + (centroid.y - C.CHARING_CROSS_NORTHING) ** 2
    ) / 1000
    joined = gpd.sjoin(
        poi, boundaries[["lsoa", "geometry"]], how="inner", predicate="within"
    ).drop(columns="index_right")
    unit_table = boundaries.drop(columns="geometry")
    metrics = build_metrics(joined, unit_table, "lsoa")
    profile = facility_group_profile(joined, unit_table, "lsoa")
    return metrics, profile, {"analysis_units": len(boundaries), "assigned_unique_poi": int(joined["poi_id"].nunique())}


def build_rail(poi: gpd.GeoDataFrame):
    catchments = gpd.read_file(C.RAIL_CATCHMENTS).to_crs(C.CRS_BNG)
    labels = pd.read_csv(C.RAIL_LABELS)[["unit", "cluster"]]
    check = catchments[["NLC", "cluster"]].merge(labels, left_on="NLC", right_on="unit", suffixes=("_catchment", "_label"), validate="one_to_one")
    if not (check["cluster_catchment"] == check["cluster_label"]).all():
        raise ValueError("Rail catchment clusters do not match the adopted fixed labels")
    catchments = catchments.loc[catchments["station_in_lnwc_extent"]].copy()
    catchments["area_km2"] = catchments.geometry.area / 1_000_000
    catchments["distance_centre_km"] = np.sqrt(
        (catchments["easting"] - C.CHARING_CROSS_EASTING) ** 2
        + (catchments["northing"] - C.CHARING_CROSS_NORTHING) ** 2
    ) / 1000
    joined = gpd.sjoin(
        poi, catchments[["NLC", "geometry"]], how="inner", predicate="within"
    ).drop(columns="index_right")
    duplicate_allocations = int(joined.duplicated("poi_id", keep=False).sum())
    if duplicate_allocations:
        joined = joined.drop_duplicates("poi_id", keep="first")
    units = catchments[["NLC", "cluster", "area_km2", "distance_centre_km"]]
    metrics = build_metrics(joined, units, "NLC")
    profile = facility_group_profile(joined, units, "NLC")
    return metrics, profile, {
        "fixed_cluster_rows": 404,
        "analysis_units": len(catchments),
        "assigned_unique_poi": int(joined["poi_id"].nunique()),
        "duplicate_boundary_allocations_removed": duplicate_allocations,
    }


def save_cluster_descriptives(metrics: pd.DataFrame, mode: str):
    variables = [
        "poi_count",
        "poi_density_km2",
        "shannon_group",
        "shannon_category",
        "poi_count_no_transport",
        "shannon_group_no_transport",
    ]
    summary = metrics.groupby("cluster")[variables].agg(["count", "mean", "median", "std"])
    summary.columns = [f"{variable}_{stat}" for variable, stat in summary.columns]
    summary.to_csv(C.DATA_OUT / f"{mode.lower()}_facility_cluster_descriptives.csv")


def main():
    args = parse_args()
    for required in (C.BUS_LABELS, C.RAIL_LABELS, C.RAIL_CATCHMENTS, C.LSOA21_BOUNDARIES):
        if not required.exists():
            raise FileNotFoundError(required)
    poi, source_audit = load_poi(args.poi, args.layer)
    bus, bus_profile, bus_audit = build_bus(poi)
    rail, rail_profile, rail_audit = build_rail(poi)
    bus.to_csv(C.DATA_OUT / "bus_facility_metrics_lsoa.csv", index=False)
    rail.to_csv(C.DATA_OUT / "rail_facility_metrics_station.csv", index=False)
    bus_profile.to_csv(C.DATA_OUT / "bus_facility_group_profile.csv")
    rail_profile.to_csv(C.DATA_OUT / "rail_facility_group_profile.csv")
    save_cluster_descriptives(bus, "Bus")
    save_cluster_descriptives(rail, "Rail")
    bus_stats = association_table(bus, "lsoa", "Bus")
    rail_stats = association_table(rail, "NLC", "Rail")
    stats = pd.concat([bus_stats, rail_stats], ignore_index=True)
    stats.to_csv(C.DATA_OUT / "facility_cluster_associations.csv", index=False)
    variables = [
        "log1p_poi_count",
        "poi_density_km2",
        "shannon_group",
        "shannon_category",
        "log1p_poi_count_no_transport",
        "shannon_group_no_transport",
    ]
    bus_z = cluster_zmeans(bus, variables)
    rail_z = cluster_zmeans(rail, variables)
    bus_z.to_csv(C.DATA_OUT / "bus_facility_cluster_zmeans.csv")
    rail_z.to_csv(C.DATA_OUT / "rail_facility_cluster_zmeans.csv")
    plot_heatmap(bus_z, "Bus", C.BUS_NAMES)
    plot_heatmap(rail_z, "Rail", C.RAIL_NAMES)
    audit = {"source": source_audit, "bus": bus_audit, "rail": rail_audit}
    (C.REPORT_OUT / "RUN_AUDIT.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    primary = stats.loc[stats["variable"].isin(["log1p_poi_count", "shannon_group"])]
    report = "# Facility diversity sidecar results\n\n" + primary.to_markdown(index=False) + "\n"
    (C.REPORT_OUT / "RESULTS.md").write_text(report, encoding="utf-8")
    print("Facility diversity sidecar completed")
    print(primary.to_string(index=False))


if __name__ == "__main__":
    main()
