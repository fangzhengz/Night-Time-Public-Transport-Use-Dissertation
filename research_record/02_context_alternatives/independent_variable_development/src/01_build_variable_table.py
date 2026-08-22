"""Build the LSOA variable table and attach it to both clusterings.

Stage 1 (this version) uses only data already in the project: the IoD 2025
domain scores and a derived population density. The Census 2021 downloads
(TS045 car availability, TS060 industry) are picked up automatically once the
files land in ``data/`` -- see config.py. Nothing else changes when they do.

Two output tables:
  * bus_variables.csv   -- one row per fitted bus LSOA, direct join
  * rail_variables.csv  -- one row per clustered rail station, LSOA values
                           aggregated into an 800 m Voronoi-clipped catchment,
                           using an equal-weight arithmetic mean across the
                           intersecting LSOAs.

Why equal-weight LSOA means: the contextual variables use heterogeneous
denominators (households, residents, residents aged 16+, and employed
residents). Applying one population weight to every percentage is therefore
not denominator-consistent. The analysis is intended to characterise the
average LSOA context intersecting each station catchment, not to estimate the
precise population or household composition of that catchment. Each distinct
intersecting LSOA is consequently counted once, irrespective of overlap area.

OS POI variables follow the same spatial estimand. POI count and Shannon
diversity are first calculated for every London LSOA. Bus uses those values
directly; Rail uses the equal-weight mean across the LSOAs intersecting the
existing 800 m Voronoi-clipped catchment. The Rail count is log-transformed
only after aggregation, so it is log1p(mean LSOA count), not mean(log count).
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon

import config as C
from geo_utils import finite_voronoi_polygons


def shannon_from_counts(counts: pd.DataFrame) -> pd.Series:
    """Unnormalised Shannon H using natural logs, matching the BtC formula."""
    totals = counts.sum(axis=1)
    shares = counts.div(totals.replace(0, np.nan), axis=0)
    terms = shares.where(shares > 0)
    return -(terms * np.log(terms)).sum(axis=1).fillna(0.0)


def attach_facilities(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Attach OS POI total count and nine-Group Shannon H to all London LSOAs."""
    if not C.OS_POI.exists():
        raise FileNotFoundError(
            f"OS POI source is required by the formal variable set: {C.OS_POI}"
        )
    poi = gpd.read_file(C.OS_POI, layer=C.OS_POI_LAYER)
    required = ["ref_no", "pointx_class"]
    missing = [column for column in required if column not in poi.columns]
    if missing:
        raise RuntimeError(f"OS POI layer is missing expected columns: {missing}")
    if poi.crs is None:
        raise RuntimeError("OS POI layer has no CRS")
    poi = poi.to_crs(C.CRS_BNG)
    poi = poi.loc[poi.geometry.notna() & ~poi.geometry.is_empty, required + ["geometry"]].copy()
    poi["poi_id"] = poi["ref_no"].astype(str).str.strip()
    code = poi["pointx_class"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(8)
    valid = code.str.fullmatch(r"\d{8}")
    if not valid.all():
        raise RuntimeError(f"OS POI contains {(~valid).sum()} invalid classification codes")
    poi["group_code"] = code.str[:2]
    poi = poi.drop_duplicates("poi_id", keep="first")

    joined = gpd.sjoin(
        poi[["poi_id", "group_code", "geometry"]],
        frame[["lsoa", "geometry"]],
        how="inner",
        predicate="intersects",
    )
    # Boundary-coincident points can intersect two LSOAs. Assign once in a
    # deterministic order rather than double-counting the same facility.
    joined = joined.sort_values(["poi_id", "lsoa"]).drop_duplicates("poi_id", keep="first")
    counts = pd.crosstab(joined["lsoa"], joined["group_code"])
    facility = pd.DataFrame(index=frame["lsoa"])
    facility["poi_count"] = counts.sum(axis=1).reindex(facility.index, fill_value=0).astype(float)
    facility["shannon_group"] = shannon_from_counts(counts).reindex(facility.index, fill_value=0.0)
    facility = facility.reset_index()

    print(
        f"  OS POI: {len(poi):,} valid unique points; {len(joined):,} assigned "
        f"to {int((facility['poi_count'] > 0).sum()):,}/{len(facility):,} London LSOAs."
    )
    return frame.merge(facility, on="lsoa", how="left", validate="one_to_one")


def load_lsoa_variables() -> pd.DataFrame:
    """IMD domain scores + population + density, one row per London LSOA."""
    imd = pd.read_csv(C.IMD_FULL)
    keep = [C.IMD_LSOA_COLUMN, C.IMD_POPULATION_COLUMN] + list(C.IMD_DOMAINS)
    missing = [c for c in keep if c not in imd.columns]
    if missing:
        raise RuntimeError(f"IoD file is missing expected columns: {missing}")
    imd = imd[keep].rename(
        columns={C.IMD_LSOA_COLUMN: "lsoa", C.IMD_POPULATION_COLUMN: "population", **C.IMD_DOMAINS}
    )

    boundaries = gpd.read_file(C.LSOA_BOUNDARIES).to_crs(C.CRS_BNG)
    boundaries = boundaries.rename(columns={C.LSOA_BOUNDARY_CODE_COLUMN: "lsoa"})
    boundaries["area_km2"] = boundaries.geometry.area / 1e6

    frame = boundaries[["lsoa", "area_km2", "geometry"]].merge(
        imd, on="lsoa", how="left", validate="one_to_one"
    )
    unmatched = frame["population"].isna().sum()
    if unmatched:
        raise RuntimeError(
            f"{unmatched} London LSOA polygons have no IoD row -- the boundary file "
            "and the IoD file disagree about the LSOA 2021 geography."
        )
    frame["population_density"] = frame["population"] / frame["area_km2"]
    return frame


def attach_census(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Join every downloaded table that is present; skip cleanly if not.

    Driven by DOWNLOAD_SPEC so a new table in config needs no change here.
    """
    added: list[str] = []

    for spec in C.DOWNLOAD_SPEC:
        if not spec["path"].exists():
            print(f"  SKIP {spec['table']} -- {spec['path'].name} not downloaded yet")
            continue
        table = pd.read_csv(spec["path"])
        frame = frame.merge(table, on="lsoa", how="left", validate="one_to_one")
        added.extend(spec["variables"])

    if C.CENSUS_INDUSTRY.exists():
        industry = pd.read_csv(C.CENSUS_INDUSTRY)
        frame = frame.merge(industry, on="lsoa", how="left", validate="one_to_one")
        added.extend(c for c in industry.columns if c != "lsoa")
    else:
        print(f"  SKIP industry aggregates -- {C.CENSUS_INDUSTRY.name} not downloaded yet")

    if C.CENSUS_INDUSTRY_ALL_SECTIONS.exists():
        # Same source file 00_download_census.py already writes as a "reference
        # copy" of all 18 TS060 sections -- pull the four raw ones out by name
        # instead of the hospitality/shiftwork composites above. See
        # config.RESIDENCE_INDUSTRY_SECTIONS for why these four.
        all_sections = pd.read_csv(C.CENSUS_INDUSTRY_ALL_SECTIONS)
        all_sections = all_sections.rename(columns={all_sections.columns[0]: "lsoa"})
        missing_sections = [
            col for col in C.RESIDENCE_INDUSTRY_SECTIONS.values()
            if col not in all_sections.columns
        ]
        if missing_sections:
            raise RuntimeError(
                f"RESIDENCE_INDUSTRY_SECTIONS names not found in "
                f"{C.CENSUS_INDUSTRY_ALL_SECTIONS.name}: {missing_sections}\n"
                f"available: {list(all_sections.columns)}"
            )
        raw = all_sections[["lsoa"] + list(C.RESIDENCE_INDUSTRY_SECTIONS.values())].rename(
            columns={v: k for k, v in C.RESIDENCE_INDUSTRY_SECTIONS.items()}
        )
        frame = frame.merge(raw, on="lsoa", how="left", validate="one_to_one")
        added.extend(C.RESIDENCE_INDUSTRY_SECTIONS.keys())
    else:
        print(f"  SKIP raw industry sections -- {C.CENSUS_INDUSTRY_ALL_SECTIONS.name} not downloaded yet")

    if C.BRES_INDUSTRY.exists():
        bres = pd.read_csv(C.BRES_INDUSTRY)
        frame = frame.merge(bres, on="lsoa", how="left", validate="one_to_one")
        # Only the share columns enter the analysis for now; the per-km2 twins
        # are carried through the table so the denominator decision (still open,
        # 2026-07-31) can be revisited without re-downloading.
        added.extend(f"bres_{section}_share" for section in C.BRES_SECTIONS)
    else:
        print(f"  SKIP BRES -- {C.BRES_INDUSTRY.name} not downloaded yet")

    return frame, added


def build_rail_catchments(lsoa: gpd.GeoDataFrame, variables: list[str]) -> pd.DataFrame:
    """Equal-weight mean of distinct LSOAs intersecting each clipped catchment."""
    coords = pd.read_csv(C.RAIL_COORDS).rename(columns={"unit": "NLC"})
    coords["NLC"] = coords["NLC"].astype(str).str.strip()
    labels = pd.read_csv(C.RAIL_LABELS).rename(columns={"unit": "NLC"})
    labels["NLC"] = labels["NLC"].astype(str).str.strip()
    if len(labels) != C.EXPECTED_RAIL_UNITS:
        raise ValueError(
            f"Expected {C.EXPECTED_RAIL_UNITS} Rail labels, got {len(labels)}"
        )

    stations = labels[["NLC", "cluster"]].merge(
        coords[["NLC", "Station", "easting", "northing"]], on="NLC", validate="one_to_one"
    )
    points = stations[["easting", "northing"]].to_numpy(dtype=float)
    if len(np.unique(points, axis=0)) != len(points):
        raise ValueError("Duplicate rail coordinates prevent an unambiguous Voronoi diagram")

    regions, vertices = finite_voronoi_polygons(Voronoi(points), radius=100_000)
    geometries = []
    for (easting, northing), region in zip(points, regions):
        # Buffer clipped to the station's own Voronoi cell. Clipping is what
        # stops two nearby stations both claiming the same LSOA.
        cell = Polygon(vertices[region])
        geometries.append(
            Point(easting, northing).buffer(C.RAIL_CATCHMENT_METRES).intersection(cell)
        )

    catchments = gpd.GeoDataFrame(
        stations.drop(columns=["easting", "northing"]), geometry=geometries, crs=C.CRS_BNG
    )

    pieces = gpd.overlay(
        catchments[["NLC", "geometry"]],
        lsoa[["lsoa", "geometry"]],
        how="intersection",
        keep_geom_type=True,
    )
    pieces["piece_area_m2"] = pieces.geometry.area
    pieces = pieces.loc[pieces["piece_area_m2"] > 0].copy()

    # Overlay can return multiple geometry pieces for one station-LSOA pair.
    # The estimand is the mean across distinct intersecting LSOAs, so collapse
    # those pieces before attaching the contextual values.
    pieces = (
        pieces[["NLC", "lsoa"]]
        .drop_duplicates()
        .sort_values(["NLC", "lsoa"])
    )
    pieces = pieces.merge(
        lsoa.drop(columns="geometry")[["lsoa"] + variables],
        on="lsoa",
        how="left",
        validate="many_to_one",
    )

    rows = []
    for nlc, group in pieces.groupby("NLC"):
        record = {"NLC": nlc, "n_intersecting_lsoa": int(group["lsoa"].nunique())}
        for variable in variables:
            values = group[variable].to_numpy(dtype=float)
            valid = np.isfinite(values)
            record[variable] = float(values[valid].mean()) if valid.any() else np.nan
        rows.append(record)

    catchment_values = pd.DataFrame(rows)
    return stations[["NLC", "Station", "cluster"]].merge(
        catchment_values, on="NLC", how="left", validate="one_to_one"
    )


def main() -> None:
    print("Loading LSOA variables (IoD domains + density)...")
    lsoa = load_lsoa_variables()
    print(f"  {len(lsoa)} London LSOAs.")

    print("Attaching Census 2021 downloads...")
    lsoa, census_added = attach_census(lsoa)

    print("Attaching OS POI facility context...")
    lsoa = attach_facilities(lsoa)

    variables = (
        list(C.IMD_DOMAINS.values())
        + ["population_density"]
        + census_added
        + list(C.FACILITY_RAW_VARIABLES)
    )
    print(f"  Variables in this run ({len(variables)}):")
    for name in variables:
        print(f"    - {name}")

    # BRES per-km2 twins ride along in the LSOA table (and so into the rail
    # catchment aggregation) without entering `variables`.
    carried = [c for c in lsoa.columns if c.endswith("_per_km2") or c == "bres_total_jobs"]

    # --- bus: direct LSOA join ---
    print("\nJoining to bus clusters...")
    bus_labels = pd.read_csv(C.BUS_LABELS)
    bus_labels = bus_labels.loc[bus_labels["retained_for_fit"], ["lsoa", "cluster"]]
    if len(bus_labels) != C.EXPECTED_BUS_UNITS:
        raise ValueError(
            f"Expected {C.EXPECTED_BUS_UNITS} fitted Bus labels, got {len(bus_labels)}"
        )
    bus = bus_labels.merge(
        lsoa.drop(columns="geometry")[["lsoa", "population", "area_km2"] + variables + carried],
        on="lsoa", how="left", validate="one_to_one",
    )
    bus["cluster_name"] = bus["cluster"].map(C.BUS_CLUSTER_NAMES)
    bus["log1p_poi_count"] = np.log1p(bus["poi_count"])
    missing = bus[variables].isna().any(axis=1).sum()
    print(f"  {len(bus)} fitted bus LSOAs, {missing} with any missing variable.")
    bus.to_csv(C.DATA_OUT / "bus_variables.csv", index=False)

    # --- rail: equal-weight mean across distinct intersecting LSOAs ---
    print("\nBuilding rail catchments and aggregating...")
    rail = build_rail_catchments(lsoa, variables + carried)
    rail["cluster_name"] = rail["cluster"].map(C.RAIL_CLUSTER_NAMES)
    rail["log1p_poi_count"] = np.log1p(rail["poi_count"])
    print(f"  {len(rail)} clustered stations; "
          f"{rail[variables].isna().any(axis=1).sum()} with any missing variable.")
    print(f"  Intersecting LSOAs per matched station: median "
          f"{rail['n_intersecting_lsoa'].median():.0f}, "
          f"min {rail['n_intersecting_lsoa'].min():.0f}")
    rail.to_csv(C.DATA_OUT / "rail_variables.csv", index=False)

    print("\nBus cluster means:")
    print(bus.groupby("cluster_name")[variables].mean().round(3).to_string())
    print("\nRail cluster means:")
    print(rail.groupby("cluster_name")[variables].mean().round(3).to_string())


if __name__ == "__main__":
    main()
