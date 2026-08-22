# -*- coding: utf-8 -*-
"""01 · Rail preprocessing (NUMBAT LU, 270 stations).

Input : reused validated long table numbat_lu_station_qhr_all_daytypes.parquet
        (270 LU stations, 5 day_types, entry/exit, full 96 15-min bins).
Steps :
  1. Build BtC day-times: weekday = mean(MON, TWT); Friday / Saturday / Sunday
     each as themselves.
  2. Slice each day-time to its night window (day-type specific; see config).
  3. Join station coordinates (EPSG:27700 + lon/lat) so maps need no later join.
Output:
  preprocessed/rail_station_night_long.parquet  [daytime, direction, NLC, ext_minute, count]
  preprocessed/rail_coords.csv                  [NLC, Station, Fare Zone, easting, northing, lon, lat]
  preprocessed/rail_audit.txt
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


# ---- coordinate matching (ported from the validated 04_join_station_coords) ----
ATCO_OVERRIDE = {
    "Edgware Road (DIS)": "940GZZLUERC", "Edgware Road (Bak)": "940GZZLUERB",
    "Hammersmith (DIS)": "940GZZLUHSD", "Hammersmith (H&C)": "940GZZLUHSC",
    "Paddington TfL": "940GZZLUPAC",
}
NAME_OVERRIDE = {"Bank and Monument": "Bank"}


def norm(s: str) -> str:
    s = str(s).lower().strip()
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = s.replace(" lu", "").replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", s)


def join_coords(station_meta: pd.DataFrame) -> pd.DataFrame:
    pts = pd.read_csv(C.RAIL_COORDS_CSV)
    pts["ATCOCODE"] = pts["ATCOCODE"].astype(str).str.strip()
    real = pts["ATCOCODE"].ne("nan") & pts["ATCOCODE"].ne("")
    pts = pts[~(real & pts["ATCOCODE"].duplicated(keep="first"))].copy()
    pts["k"] = pts["NAME"].map(norm)
    by_atco = pts.set_index("ATCOCODE")
    by_name = pts.drop_duplicates(subset="NAME", keep="first").set_index("NAME")
    override_atcos = set(ATCO_OVERRIDE.values())
    ordinary = pts[~pts["ATCOCODE"].isin(override_atcos)]
    counts = ordinary["k"].value_counts()
    uniq = ordinary[ordinary["k"].isin(counts[counts == 1].index)].set_index("k")[["X", "Y", "NAME", "ATCOCODE"]]

    recs = []
    for st in station_meta["Station"]:
        if st in ATCO_OVERRIDE:
            p = by_atco.loc[ATCO_OVERRIDE[st]]
            recs.append((float(p["X"]), float(p["Y"])))
        elif st in NAME_OVERRIDE:
            p = by_name.loc[NAME_OVERRIDE[st]]
            recs.append((float(p["X"]), float(p["Y"])))
        else:
            k = norm(st)
            if k in uniq.index:
                p = uniq.loc[k]
                recs.append((float(p["X"]), float(p["Y"])))
            else:
                recs.append((np.nan, np.nan))
    out = station_meta.copy()
    out[["easting", "northing"]] = pd.DataFrame(recs, index=out.index)
    try:
        from pyproj import Transformer
        tf = Transformer.from_crs(27700, 4326, always_xy=True)
        lon, lat = tf.transform(out["easting"].to_numpy(), out["northing"].to_numpy())
        out["lon"], out["lat"] = lon, lat
    except Exception:
        out["lon"], out["lat"] = np.nan, np.nan
    return out


def main() -> None:
    raw = pd.read_parquet(C.RAIL_LONG_SRC)
    raw["day_type"] = raw["day_type"].astype(str)
    raw["NLC"] = raw["NLC"].astype(str)
    raw["Fare Zone"] = raw["Fare Zone"].astype(str)
    log = [f"source rows: {len(raw)} | NLC: {raw.NLC.nunique()} | day_types: {sorted(raw.day_type.unique())}"]

    # 1+2. assemble day-times and slice night windows
    frames = []
    for daytime in C.RAIL_DAYTIME_ORDER:
        srcs = C.RAIL_DAYTIME_SOURCES[daytime]
        lo, hi = C.RAIL_WINDOWS[daytime]
        block = raw[raw.day_type.isin(srcs)].copy()
        block = block[(block.extended_minute >= lo) & (block.extended_minute < hi)]
        # average across source day_types (mean of MON & TWT for weekday)
        g = (block.groupby(["direction", "NLC", "extended_minute"], as_index=False)["count"]
             .mean() if len(srcs) > 1 else
             block.groupby(["direction", "NLC", "extended_minute"], as_index=False)["count"].sum())
        g["daytime"] = daytime
        frames.append(g)
        nbins = g.extended_minute.nunique()
        log.append(f"  {daytime}: window [{lo},{hi}) -> {nbins} bins, {g.NLC.nunique()} stations, src={srcs}")
    long = pd.concat(frames, ignore_index=True)[["daytime", "direction", "NLC", "extended_minute", "count"]]
    long = long.rename(columns={"extended_minute": "ext_minute"})

    # 3. station meta + coordinates
    meta = raw.drop_duplicates("NLC")[["NLC", "Station", "Fare Zone"]].reset_index(drop=True)
    coords = join_coords(meta)
    missing = coords["easting"].isna().sum()
    log.append(f"coords matched: {len(coords)-missing}/{len(coords)} (missing {missing})")
    if missing:
        log.append("  MISSING: " + ", ".join(coords.loc[coords.easting.isna(), "Station"].tolist()))

    long.to_parquet(C.PRE / "rail_station_night_long.parquet", index=False)
    coords.to_csv(C.PRE / "rail_coords.csv", index=False, encoding="utf-8-sig")
    (C.PRE / "rail_audit.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))
    print("-> rail_station_night_long.parquet, rail_coords.csv")


if __name__ == "__main__":
    main()
