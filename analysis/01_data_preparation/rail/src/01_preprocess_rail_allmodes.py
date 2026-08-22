from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


"""01 - Preprocess ALL NUMBAT rail-family modes (LU, DLR, LO, EZL, TRM).

Adapted from `FYP/analysis code/03_preprocess_numbat_lu_multiday.py`. The only
substantive change: that script keeps only stations where `has_lu == True`
(270 of 471 NLCs). This script keeps every NLC in the raw NUMBAT workbooks,
carrying `mode_label` through so downstream steps can see which stations are
Underground versus DLR/Overground/Elizabeth line/Tram-only.

This does not modify `FYP/analysis code/03_preprocess_numbat_lu_multiday.py`
or any of its outputs. It reads the same raw NUMBAT workbooks and writes to
a separate `outputs/` folder under this preprocessing directory.

Moved 2026-07-24 from `analysis/02_mode_specific_clustering/rail/src/` into its own
`data_processing/rail_allmodes/` folder (mirroring `data_processing/bus_stoparea/`'s
separation of preprocessing from clustering), so all-modes rail station
preprocessing/filtering has one home independent of any one downstream
clustering analysis. Only `FYP_ROOT`'s parent-directory depth changed;
logic is otherwise unmodified.
"""

NUMBAT_FILENAME_PATTERN = re.compile(r"^NBT24(?P<day_type>[A-Z]+)_outputs\.xlsx$")
TIME_COL_PATTERN = re.compile(r"^\d{4}-\d{4}$")
DAY_TYPE_ORDER = ["MON", "TWT", "FRI", "SAT", "SUN"]

FYP_ROOT = Path(__file__).resolve().parents[4]
RAIL_DATA_DIR = FYP_ROOT / "地铁进出站数据"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LONG_OUTPUT = OUTPUT_DIR / "numbat_allmodes_station_qhr_all_daytypes.parquet"
META_OUTPUT = OUTPUT_DIR / "numbat_allmodes_station_meta.csv"
AUDIT_OUTPUT = OUTPUT_DIR / "numbat_allmodes_multiday_audit.csv"
AUDIT_JSON_OUTPUT = OUTPUT_DIR / "numbat_allmodes_multiday_audit.json"
MODE_LOOKUP_OUTPUT = OUTPUT_DIR / "numbat_allmodes_mode_lookup.csv"


def locate_numbat_files(data_dir: Path) -> dict[str, Path]:
    """Locate NUMBAT workbooks and infer day type from filename."""
    files: dict[str, Path] = {}

    for path in sorted(data_dir.glob("NBT24*_outputs.xlsx")):
        if path.name.startswith("~$"):
            continue
        match = NUMBAT_FILENAME_PATTERN.fullmatch(path.name)
        if not match:
            continue
        files[match.group("day_type")] = path

    missing = [day for day in DAY_TYPE_ORDER if day not in files]
    if missing:
        raise FileNotFoundError(f"Missing NUMBAT day-type files: {missing}")

    return {day: files[day] for day in DAY_TYPE_ORDER}


def detect_time_columns(columns: list[str]) -> list[str]:
    """Return NUMBAT 15-minute columns in workbook order."""
    return [col for col in columns if TIME_COL_PATTERN.fullmatch(str(col))]


def parse_bin_start(bin_label: str) -> tuple[int, int, int]:
    """Parse a NUMBAT bin and return hour, minute, and extended traffic minute."""
    match = re.fullmatch(r"(?P<hour>\d{2})(?P<minute>\d{2})-\d{4}", str(bin_label))
    if not match:
        raise ValueError(f"Invalid NUMBAT bin label: {bin_label}")

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    clock_minute = hour * 60 + minute
    extended_minute = clock_minute if clock_minute >= 5 * 60 else clock_minute + 24 * 60

    return hour, minute, extended_minute


def load_mode_lookup(path: Path) -> pd.DataFrame:
    """Build a station-level mode lookup from Station_Boarders.

    Unlike the LU-only preprocessing script, this keeps every NLC regardless
    of which modes serve it -- `has_lu` / `is_tram_only` are retained as
    descriptive flags, not filters.
    """
    boarders = pd.read_excel(path, sheet_name="Station_Boarders", header=2, usecols=["NLC", "Mode"])
    boarders["NLC"] = boarders["NLC"].astype(str).str.strip()
    boarders["Mode"] = boarders["Mode"].astype(str).str.strip()

    mode_lookup = (
        boarders.dropna(subset=["NLC", "Mode"])
        .drop_duplicates(["NLC", "Mode"])
        .groupby("NLC")
        .agg(modes=("Mode", lambda values: sorted(set(values))))
        .reset_index()
    )
    mode_lookup["mode_label"] = mode_lookup["modes"].apply(lambda modes: ",".join(modes))
    mode_lookup["has_lu"] = mode_lookup["modes"].apply(lambda modes: "LU" in set(modes))
    mode_lookup["is_lu_only"] = mode_lookup["modes"].apply(lambda modes: set(modes) == {"LU"})
    mode_lookup["is_tram_only"] = mode_lookup["modes"].apply(lambda modes: set(modes) == {"TRM"})
    mode_lookup["is_dlr_only"] = mode_lookup["modes"].apply(lambda modes: set(modes) == {"DLR"})
    mode_lookup["is_lo_only"] = mode_lookup["modes"].apply(lambda modes: set(modes) == {"LO"})
    mode_lookup["is_ezl_only"] = mode_lookup["modes"].apply(lambda modes: set(modes) == {"EZL"})

    return mode_lookup[
        [
            "NLC",
            "mode_label",
            "has_lu",
            "is_lu_only",
            "is_tram_only",
            "is_dlr_only",
            "is_lo_only",
            "is_ezl_only",
        ]
    ]


def load_station_flow(
    path: Path,
    day_type: str,
    sheet_name: str,
    direction: str,
    mode_lookup: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load one station entry/exit sheet and reshape to long 15-minute format.

    NO `has_lu` filter here -- every NLC present in the sheet is kept.
    """
    df = pd.read_excel(path, sheet_name=sheet_name, header=2)
    df.columns = [str(col).strip() for col in df.columns]

    for col in ["NLC", "ASC", "Station", "Fare Zone"]:
        df[col] = df[col].astype(str).str.strip()

    time_cols = detect_time_columns(list(df.columns))
    if len(time_cols) != 96:
        raise ValueError(f"{path.name} {sheet_name}: expected 96 time columns, got {len(time_cols)}")

    df = df.merge(mode_lookup, on="NLC", how="left", validate="many_to_one")

    raw_station_count = df["NLC"].nunique()
    unmatched_mode = df["mode_label"].isna().sum()

    id_cols = ["NLC", "ASC", "Station", "Fare Zone", "mode_label"]
    long_df = df.melt(
        id_vars=id_cols,
        value_vars=time_cols,
        var_name="bin_label",
        value_name="count",
    )
    long_df["day_type"] = day_type
    long_df["direction"] = direction
    long_df["count"] = pd.to_numeric(long_df["count"], errors="coerce").fillna(0.0)

    parsed = long_df["bin_label"].apply(parse_bin_start)
    long_df["hour"] = parsed.apply(lambda value: value[0])
    long_df["minute"] = parsed.apply(lambda value: value[1])
    long_df["extended_minute"] = parsed.apply(lambda value: value[2])
    long_df["clock_time"] = long_df["hour"].map("{:02d}".format) + ":" + long_df["minute"].map(
        "{:02d}".format
    )

    long_df = long_df[
        [
            "day_type",
            "direction",
            "NLC",
            "ASC",
            "Station",
            "Fare Zone",
            "mode_label",
            "bin_label",
            "clock_time",
            "hour",
            "minute",
            "extended_minute",
            "count",
        ]
    ]

    audit = {
        "day_type": day_type,
        "file": str(path),
        "sheet_name": sheet_name,
        "direction": direction,
        "raw_station_count": raw_station_count,
        "unmatched_mode_rows": int(unmatched_mode),
        "time_col_count": len(time_cols),
        "first_time_col": time_cols[0],
        "last_time_col": time_cols[-1],
        "row_count": len(long_df),
        "total_count": float(long_df["count"].sum()),
    }
    return long_df, audit


def build_station_meta(long_df: pd.DataFrame) -> pd.DataFrame:
    """Build one station metadata row per NLC."""
    meta_index = ["NLC", "ASC", "Station", "Fare Zone", "mode_label"]
    totals = (
        long_df.groupby(meta_index + ["direction"], as_index=False)
        .agg(total=("count", "sum"))
        .pivot_table(
            index=meta_index,
            columns="direction",
            values="total",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
    )
    totals.columns.name = None
    meta = totals.rename(columns={"entry": "total_entry", "exit": "total_exit"})
    meta["total_activity"] = meta["total_entry"] + meta["total_exit"]
    return meta


def main() -> None:
    print("FYP root:", FYP_ROOT)
    print("Rail data dir:", RAIL_DATA_DIR)
    print("Output dir:", OUTPUT_DIR)

    files = locate_numbat_files(RAIL_DATA_DIR)
    print("NUMBAT files:")
    for day_type, path in files.items():
        print(f"  {day_type}: {path}")

    mode_lookup = load_mode_lookup(files["TWT"])
    mode_lookup.to_csv(MODE_LOOKUP_OUTPUT, index=False)
    print("\nMode lookup counts (all NLCs, no has_lu filter):")
    print(mode_lookup["mode_label"].value_counts(dropna=False).sort_index())
    print("Total NLCs:", mode_lookup["NLC"].nunique())
    print("  with LU:", int(mode_lookup["has_lu"].sum()))
    print("  without LU:", int((~mode_lookup["has_lu"]).sum()))
    print("  DLR-only:", int(mode_lookup["is_dlr_only"].sum()))
    print("  LO-only:", int(mode_lookup["is_lo_only"].sum()))
    print("  EZL-only:", int(mode_lookup["is_ezl_only"].sum()))
    print("  TRM-only:", int(mode_lookup["is_tram_only"].sum()))

    frames = []
    audit_rows = []

    for day_type, path in files.items():
        for sheet_name, direction in [
            ("Station_Entries", "entry"),
            ("Station_Exits", "exit"),
        ]:
            print(f"Reading {day_type} {direction}...")
            long_df, audit = load_station_flow(path, day_type, sheet_name, direction, mode_lookup)
            frames.append(long_df)
            audit_rows.append(audit)

    all_long = pd.concat(frames, ignore_index=True)
    all_long["day_type"] = pd.Categorical(all_long["day_type"], categories=DAY_TYPE_ORDER, ordered=True)
    all_long = all_long.sort_values(
        ["day_type", "direction", "NLC", "extended_minute"]
    ).reset_index(drop=True)

    meta = build_station_meta(all_long)
    audit_df = pd.DataFrame(audit_rows)

    all_long.to_parquet(LONG_OUTPUT, index=False)
    meta.to_csv(META_OUTPUT, index=False)
    audit_df.to_csv(AUDIT_OUTPUT, index=False)

    audit_summary = {
        "fyp_root": str(FYP_ROOT),
        "rail_data_dir": str(RAIL_DATA_DIR),
        "output_dir": str(OUTPUT_DIR),
        "day_types": DAY_TYPE_ORDER,
        "long_output": str(LONG_OUTPUT),
        "meta_output": str(META_OUTPUT),
        "audit_output": str(AUDIT_OUTPUT),
        "long_shape": list(all_long.shape),
        "station_count": int(all_long["NLC"].nunique()),
        "day_type_counts": all_long["day_type"].value_counts().sort_index().to_dict(),
        "direction_counts": all_long["direction"].value_counts().to_dict(),
        "mode_label_counts": mode_lookup["mode_label"].value_counts(dropna=False).sort_index().to_dict(),
        "has_lu_count": int(mode_lookup["has_lu"].sum()),
        "without_lu_count": int((~mode_lookup["has_lu"]).sum()),
    }
    AUDIT_JSON_OUTPUT.write_text(json.dumps(audit_summary, indent=2), encoding="utf-8")

    print("\nSaved:")
    print(" ", LONG_OUTPUT)
    print(" ", META_OUTPUT)
    print(" ", AUDIT_OUTPUT)
    print(" ", AUDIT_JSON_OUTPUT)
    print(" ", MODE_LOOKUP_OUTPUT)
    print("\nLong shape:", all_long.shape)
    print("Station count:", all_long["NLC"].nunique())
    print(
        "Expected rows: 5 day types * 2 directions * {n} stations * 96 bins = {exp}".format(
            n=all_long["NLC"].nunique(),
            exp=5 * 2 * all_long["NLC"].nunique() * 96,
        )
    )


if __name__ == "__main__":
    main()
