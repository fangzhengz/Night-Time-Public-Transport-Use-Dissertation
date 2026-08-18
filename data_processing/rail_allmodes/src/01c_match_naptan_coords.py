from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

"""01c - Match every merged all-modes rail station to a coordinate.

Extracted 2026-07-24 from `numbat_all_area_test/src/05_build_allmodes_coords_and_map.py`
(that script's coordinate-matching half only -- the comparison-map plotting
half stays in `numbat_all_area_test`, since it needs cluster labels, which
this preprocessing folder deliberately does not produce). Runs directly on
`01b`'s merged station list (currently 456 stations), independent of any downstream
clustering or activity filtering -- coordinate matching depends only on
station name and mode, not on cluster membership or night-time activity
level.

Coordinate sources:
  - The 270 canonical LU stations: `Underground_Stations.csv`, using the
    exact same name/ATCO matching table as
    `FYP/analysis code/04_join_station_coords.py`.
  - Non-LU stations: `NaPTAN_data/490.xml` (StopType RSE = rail station
    entrance, TMU = tram/metro/underground access point), the mode-agnostic
    national stop dataset covering DLR/Overground/Elizabeth line/Tram
    entrances for Greater London. Matching is by a token-based
    normalisation (see `norm_token`), because NUMBAT and NaPTAN
    disambiguate same-named interchange points with different suffix
    conventions.

Any station that fails to match is listed explicitly in
`rail_allmodes_coords_unmatched.csv`, not silently dropped. Unmatched
stations are almost all physically outside Greater London (e.g. Reading,
Slough, Maidenhead, Watford Junction), which fall outside NaPTAN's area-490
(Greater London) extract for structural, not data-quality, reasons -- see
`01d_filter_naptan_matched.py`, which uses this script's output to build
the final analysis-ready station population.
"""

FYP_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"

NAPTAN_PATH = FYP_ROOT / "numbat_all_area_test" / "NaPTAN_data" / "490.xml"
UNDERGROUND_STATIONS_CSV = FYP_ROOT / "地铁进出站数据" / "地铁车站空间数据" / "Underground_Stations.csv"
NS = {"n": "http://www.naptan.org.uk/"}

MERGED_META = DATA_DIR / "numbat_allmodes_station_meta_merged.csv"
COORDS_OUTPUT = DATA_DIR / "rail_allmodes_coords.csv"
UNMATCHED_OUTPUT = DATA_DIR / "rail_allmodes_coords_unmatched.csv"

ATCO_OVERRIDE = {
    "Edgware Road (DIS)": "940GZZLUERC",
    "Edgware Road (Bak)": "940GZZLUERB",
    "Hammersmith (DIS)": "940GZZLUHSD",
    "Hammersmith (H&C)": "940GZZLUHSC",
    "Paddington TfL": "940GZZLUPAC",
}
NAME_OVERRIDE = {
    "Bank and Monument": "Bank",
}
NAPTAN_NAME_OVERRIDE = {
    "Cutty Sark": "Cutty Sark for Maritime Greenwich",
}

STOPWORDS = {
    "station", "stations", "underground", "overground", "rail", "dlr",
    "tram", "trams", "stop", "thameslink", "line", "el", "nr", "lo",
}


def norm_lu(s: str) -> str:
    s = str(s).lower().strip()
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = s.replace(" lu", "").replace("&", "and")
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def norm_token(s: str) -> str:
    s = str(s).lower().strip()
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", "", s)
    words = [w for w in s.split() if w not in STOPWORDS]
    return "".join(words)


def load_lu_lookup() -> dict:
    pts = pd.read_csv(UNDERGROUND_STATIONS_CSV)
    pts["ATCOCODE"] = pts["ATCOCODE"].astype(str).str.strip()
    real = pts["ATCOCODE"].ne("nan") & pts["ATCOCODE"].ne("")
    pts = pts[~(real & pts["ATCOCODE"].duplicated(keep="first"))].copy()
    pts["k"] = pts["NAME"].map(norm_lu)

    by_atco = pts.set_index("ATCOCODE")
    override_atcos = set(ATCO_OVERRIDE.values())
    ordinary = pts[~pts["ATCOCODE"].isin(override_atcos)]
    name_counts = ordinary["k"].value_counts()
    unique_name_lookup = (
        ordinary[ordinary["k"].isin(name_counts[name_counts == 1].index)]
        .set_index("k")[["X", "Y", "NAME", "ATCOCODE"]]
    )
    return {"by_atco": by_atco, "unique_name_lookup": unique_name_lookup}


def match_lu_station(station_name: str, lookup: dict):
    if station_name in ATCO_OVERRIDE:
        p = lookup["by_atco"].loc[ATCO_OVERRIDE[station_name]]
        return float(p["X"]), float(p["Y"]), p["NAME"], "underground_stations_csv"
    if station_name in NAME_OVERRIDE:
        target_name = NAME_OVERRIDE[station_name]
        k = norm_lu(target_name)
        if k in lookup["unique_name_lookup"].index:
            p = lookup["unique_name_lookup"].loc[k]
            return float(p["X"]), float(p["Y"]), p["NAME"], "underground_stations_csv"
    k = norm_lu(station_name)
    if k in lookup["unique_name_lookup"].index:
        p = lookup["unique_name_lookup"].loc[k]
        return float(p["X"]), float(p["Y"]), p["NAME"], "underground_stations_csv"
    return None, None, None, None


def load_naptan_lookup() -> pd.DataFrame:
    tree = ET.parse(NAPTAN_PATH)
    root = tree.getroot()
    rows = []
    for sp in root.iter("{http://www.naptan.org.uk/}StopPoint"):
        stop_type = sp.findtext(".//n:StopClassification/n:StopType", default=None, namespaces=NS)
        if stop_type not in ("RSE", "TMU"):
            continue
        name = sp.findtext("n:Descriptor/n:CommonName", default=None, namespaces=NS)
        easting = sp.findtext(".//n:Location/n:Translation/n:Easting", default=None, namespaces=NS)
        northing = sp.findtext(".//n:Location/n:Translation/n:Northing", default=None, namespaces=NS)
        lon = sp.findtext(".//n:Location/n:Translation/n:Longitude", default=None, namespaces=NS)
        lat = sp.findtext(".//n:Location/n:Translation/n:Latitude", default=None, namespaces=NS)
        if easting is None or northing is None:
            continue
        rows.append(
            {"name": name, "easting": float(easting), "northing": float(northing),
             "lon": float(lon), "lat": float(lat)}
        )
    naptan = pd.DataFrame(rows)
    naptan["k"] = naptan["name"].map(norm_token)
    grouped = (
        naptan.groupby("k")
        .agg(easting=("easting", "mean"), northing=("northing", "mean"),
             lon=("lon", "mean"), lat=("lat", "mean"),
             example_name=("name", "first"), n_points=("name", "count"))
        .reset_index()
    )
    return grouped.set_index("k")


def match_non_lu_station(station_name: str, naptan_lookup: pd.DataFrame):
    lookup_name = NAPTAN_NAME_OVERRIDE.get(station_name, station_name)
    k = norm_token(lookup_name)
    if k in naptan_lookup.index:
        p = naptan_lookup.loc[k]
        return float(p["easting"]), float(p["northing"]), float(p["lon"]), float(p["lat"]), p["example_name"], "naptan_rse_tmu"
    return None, None, None, None, None, None


def main() -> None:
    meta = pd.read_csv(MERGED_META, dtype={"NLC": str})
    meta["unit"] = meta["NLC"]
    meta["is_lu"] = meta["mode_label"].str.contains("LU")

    lu_lookup = load_lu_lookup()
    naptan_lookup = load_naptan_lookup()
    print("NaPTAN RSE/TMU normalised name entries:", len(naptan_lookup))

    try:
        from pyproj import Transformer

        tf = Transformer.from_crs(27700, 4326, always_xy=True)
    except Exception:
        tf = None

    records = []
    for _, row in meta.iterrows():
        if row["is_lu"]:
            x, y, matched_name, source = match_lu_station(row["Station"], lu_lookup)
            lon = lat = None
            if x is not None and tf is not None:
                lon, lat = tf.transform(x, y)
        else:
            x, y, lon, lat, matched_name, source = match_non_lu_station(row["Station"], naptan_lookup)

        records.append(
            {
                "unit": row["unit"], "Station": row["Station"], "mode_label": row["mode_label"],
                "is_lu": row["is_lu"], "easting": x, "northing": y, "lon": lon, "lat": lat,
                "matched_name": matched_name, "coord_source": source,
            }
        )

    coords = pd.DataFrame(records)
    coords.to_csv(COORDS_OUTPUT, index=False, encoding="utf-8-sig")

    unmatched = coords[coords["easting"].isna()]
    unmatched.to_csv(UNMATCHED_OUTPUT, index=False, encoding="utf-8-sig")

    print(f"Total merged stations: {len(coords)}")
    print(f"Matched: {coords['easting'].notna().sum()}")
    print(f"Unmatched: {len(unmatched)}")
    if len(unmatched):
        print("Unmatched station list (mode_label):")
        for _, r in unmatched.iterrows():
            print(f"  {r['Station']} ({r['mode_label']})")
    print("Saved:", COORDS_OUTPUT)
    print("Saved:", UNMATCHED_OUTPUT)


if __name__ == "__main__":
    main()
