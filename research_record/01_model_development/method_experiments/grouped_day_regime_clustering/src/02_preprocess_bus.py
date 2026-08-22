# -*- coding: utf-8 -*-
"""02 · Bus preprocessing (BUSTO -> LSOA, hourly).

Input : reused validated stop-level table busto_stop_qhr_night.parquet
        (19,589 stops, Weekday/Saturday/Sunday, 18:00-06:00, 15-min,
        boardings+alightings already summed across routes/directions).
Steps :
  1. Point-in-polygon spatial join: each bus stop -> the LSOA that contains it
     (Bus_Stops.csv OS coords, EPSG:27700; London LSOA 2021 polygons).
  2. Map stops to LSOA, drop unmatched, aggregate to LSOA x day_type x hour
     (hourly = sum of the four 15-min bins).
Output:
  preprocessed/bus_lsoa_night_long.parquet  [day_type, direction, lsoa, hour_bin, count]
  preprocessed/bus_stop_lsoa_lookup.csv     [stopcode, lsoa]
  preprocessed/bus_lsoa_meta.csv            [lsoa, rep_stop, n_stops]
  preprocessed/bus_audit.txt
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def build_lookup() -> pd.DataFrame:
    stops = pd.read_csv(C.BUS_STOPS_CSV, dtype=str)
    stops["OS_EASTING"] = pd.to_numeric(stops["OS_EASTING"], errors="coerce")
    stops["OS_NORTHING"] = pd.to_numeric(stops["OS_NORTHING"], errors="coerce")
    stops = stops.dropna(subset=["OS_EASTING", "OS_NORTHING"]).copy()
    gstops = gpd.GeoDataFrame(
        stops[["STOP_CODE", "STOP_NAME"]],
        geometry=gpd.points_from_xy(stops["OS_EASTING"], stops["OS_NORTHING"]),
        crs=C.CRS_BNG,
    )
    lsoa = gpd.read_file(C.LSOA_GEOJSON)
    code_col = next(c for c in lsoa.columns if c.lower() == "lsoa21cd")
    lsoa = lsoa[[code_col, "geometry"]].to_crs(C.CRS_BNG)
    sj = gpd.sjoin(gstops, lsoa, how="left", predicate="within").rename(columns={code_col: "lsoa"})
    sj = sj.rename(columns={"STOP_CODE": "stopcode", "STOP_NAME": "stopname"})
    matched = sj["lsoa"].notna().sum()
    return sj[["stopcode", "stopname", "lsoa"]], matched, len(sj), len(lsoa)


def main() -> None:
    stop = pd.read_parquet(C.BUS_STOP_SRC)
    stop["stopcode"] = stop["stopcode"].astype(str)
    stop["day_type"] = stop["day_type"].astype(str)
    log = [f"stop rows: {len(stop)} | stops: {stop.stopcode.nunique()} | day_types: {sorted(stop.day_type.unique())}"]

    lookup, matched, n_stops_geo, n_lsoa = build_lookup()
    log.append(f"bus-stop geo file: {n_stops_geo} stops | LSOA polygons: {n_lsoa}")
    log.append(f"stops matched to an LSOA (point-in-polygon within): {matched}/{n_stops_geo} = {100*matched/n_stops_geo:.1f}%")

    code2lsoa = lookup.dropna(subset=["lsoa"])[["stopcode", "lsoa"]]
    merged = stop.merge(code2lsoa, on="stopcode", how="left")
    unmatched_rows = merged["lsoa"].isna().mean()
    unmatched_stops = merged.loc[merged.lsoa.isna(), "stopcode"].nunique()
    log.append(f"BUSTO stops with no LSOA: {unmatched_stops} (rows {100*unmatched_rows:.2f}% dropped)")
    merged = merged.dropna(subset=["lsoa"]).copy()

    # hourly aggregation (sum the four 15-min bins) then LSOA aggregation
    merged["hour_bin"] = (merged["traffic_minute"] // C.BUS_BIN) * C.BUS_BIN
    agg = (merged.groupby(["lsoa", "day_type", "hour_bin"], as_index=False)
           .agg(boardings=("boardings", "sum"), alightings=("alightings", "sum")))
    long = agg.melt(id_vars=["lsoa", "day_type", "hour_bin"],
                    value_vars=["boardings", "alightings"],
                    var_name="direction", value_name="count")
    long["count"] = long["count"].fillna(0.0)
    long = long[["day_type", "direction", "lsoa", "hour_bin", "count"]]
    log.append(f"LSOA-level long rows: {len(long)} | unique LSOAs: {long.lsoa.nunique()} | hour bins: {sorted(long.hour_bin.unique())}")

    # meta: busiest stop name + stop count per LSOA
    rep = (merged.groupby(["lsoa", "stopname"], as_index=False)
           .agg(a=("boardings", "sum")).sort_values("a", ascending=False)
           .drop_duplicates("lsoa")[["lsoa", "stopname"]].rename(columns={"stopname": "rep_stop"}))
    nst = code2lsoa.groupby("lsoa")["stopcode"].nunique().rename("n_stops").reset_index()
    meta = rep.merge(nst, on="lsoa", how="outer")

    long.to_parquet(C.PRE / "bus_lsoa_night_long.parquet", index=False)
    code2lsoa.to_csv(C.PRE / "bus_stop_lsoa_lookup.csv", index=False)
    meta.to_csv(C.PRE / "bus_lsoa_meta.csv", index=False)
    (C.PRE / "bus_audit.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))
    print("-> bus_lsoa_night_long.parquet, bus_stop_lsoa_lookup.csv, bus_lsoa_meta.csv")


if __name__ == "__main__":
    main()
