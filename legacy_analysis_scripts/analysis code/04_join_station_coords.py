"""Join TfL/OS station coordinates onto the 270-station GMM cluster labels.

Keeps the analysis set fixed at 270 LU stations. Coordinate matching is by
station name, with an explicit override table for the handful of interchange
stations whose naming differs between NUMBAT and the TfL coordinate file.

Outputs, next to each labels file:
    weekday_k5_labels_xy.csv
    weekend_k6_labels_xy.csv
with easting/northing (EPSG:27700) and lon/lat (EPSG:4326).
"""
from pathlib import Path
import re
import pandas as pd

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
PTS = ROOT / "地铁进出站数据" / "地铁车站空间数据" / "Underground_Stations.csv"
JOBS = [
    ROOT / "outputs" / "lu_rail_2000_diag" / "weekday" / "weekday_k5_labels.csv",
    ROOT / "outputs" / "lu_rail_2000_diag" / "weekend" / "weekend_k6_labels.csv",
]

# label Station -> ATCOCODE in the coordinate file (interchange disambiguation)
ATCO_OVERRIDE = {
    "Edgware Road (DIS)": "940GZZLUERC",   # Circle/District/H&C side
    "Edgware Road (Bak)": "940GZZLUERB",   # Bakerloo side
    "Hammersmith (DIS)":  "940GZZLUHSD",   # District & Piccadilly
    "Hammersmith (H&C)":  "940GZZLUHSC",   # Hammersmith & City
    "Paddington TfL":     "940GZZLUPAC",   # main Paddington (drop dup + H&C variant)
}
# label Station -> exact NAME in the coordinate file
NAME_OVERRIDE = {
    "Bank and Monument": "Bank",           # NUMBAT merges Bank+Monument; use Bank point
}


def norm(s: str) -> str:
    s = str(s).lower().strip()
    s = re.sub(r"\s*\(.*?\)", "", s)          # drop "(DIS)", "(H&C)", ...
    s = s.replace(" lu", "").replace("&", "and")
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def main() -> None:
    pts = pd.read_csv(PTS)
    pts["ATCOCODE"] = pts["ATCOCODE"].astype(str).str.strip()
    # Drop only genuine duplicate ATCOCODEs (e.g. the doubled Paddington row).
    # Rows with a blank/NaN code (Nine Elms, Battersea Power Station) must be kept.
    real = pts["ATCOCODE"].ne("nan") & pts["ATCOCODE"].ne("")
    pts = pts[~(real & pts["ATCOCODE"].duplicated(keep="first"))].copy()
    pts["k"] = pts["NAME"].map(norm)

    by_atco = pts.set_index("ATCOCODE")
    by_name = pts.drop_duplicates(subset="NAME", keep="first").set_index("NAME")

    # name lookup for the ordinary stations: keep only names that are unique once
    # the override stations are removed from contention
    override_atcos = set(ATCO_OVERRIDE.values())
    ordinary = pts[~pts["ATCOCODE"].isin(override_atcos)]
    name_counts = ordinary["k"].value_counts()
    unique_name_lookup = (
        ordinary[ordinary["k"].isin(name_counts[name_counts == 1].index)]
        .set_index("k")[["X", "Y", "NAME", "ATCOCODE"]]
    )

    try:
        from pyproj import Transformer
        tf = Transformer.from_crs(27700, 4326, always_xy=True)
    except Exception:
        tf = None

    for job in JOBS:
        lab = pd.read_csv(job)
        recs = []
        for _, row in lab.iterrows():
            st = row["Station"]
            if st in ATCO_OVERRIDE:
                p = by_atco.loc[ATCO_OVERRIDE[st]]
                recs.append((float(p["X"]), float(p["Y"]), p["NAME"], ATCO_OVERRIDE[st]))
            elif st in NAME_OVERRIDE:
                p = by_name.loc[NAME_OVERRIDE[st]]
                recs.append((float(p["X"]), float(p["Y"]), NAME_OVERRIDE[st], p["ATCOCODE"]))
            else:
                k = norm(st)
                if k in unique_name_lookup.index:
                    p = unique_name_lookup.loc[k]
                    recs.append((float(p["X"]), float(p["Y"]), p["NAME"], p["ATCOCODE"]))
                else:
                    recs.append((None, None, None, None))

        coords = pd.DataFrame(recs, columns=["easting", "northing", "coord_name", "atcocode"])
        out = pd.concat([lab.reset_index(drop=True), coords], axis=1)

        if out["easting"].isna().any():
            print("  MISSING:", out.loc[out["easting"].isna(), "Station"].tolist())
        out["atcocode"] = out["atcocode"].replace({"nan": pd.NA, "": pd.NA})
        missing = out["easting"].isna().sum()
        dup_atco = out["atcocode"].dropna().duplicated().sum()
        assert missing == 0, f"{job.name}: {missing} stations missing coords"
        assert dup_atco == 0, f"{job.name}: {dup_atco} duplicate coordinate points"

        if tf is not None:
            lon, lat = tf.transform(out["easting"].to_numpy(), out["northing"].to_numpy())
            out["lon"], out["lat"] = lon, lat

        dest = job.with_name(job.stem + "_xy.csv")
        out.to_csv(dest, index=False, encoding="utf-8-sig")
        print(f"{job.name}: {len(out)} stations, all matched, no dups -> {dest.name}")


if __name__ == "__main__":
    main()
