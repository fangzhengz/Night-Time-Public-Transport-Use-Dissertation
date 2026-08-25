"""Preprocess full BUSTO total-demand CSVs with chunked reads.

This script is designed for the updated BUSTO folder containing multiple
large CSVs. It never concatenates the raw files in memory. Instead, it reads
each CSV in chunks, filters to the configured night window, aggregates each
chunk, and only combines the smaller aggregated tables at the end.

Primary output for RQ1:
    busto_stop_qhr_night.parquet/csv

Useful QA and interpretation outputs:
    busto_stop_meta.csv
    busto_stop_block.csv
    busto_route_block.csv
    busto_hourly_audit.csv
    busto_file_audit.csv
    busto_schema_audit.csv
    busto_preprocess_audit.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


LOGGER = logging.getLogger("preprocess_busto")

SCRIPT_PATH = Path(__file__).resolve()
FYP_ROOT = SCRIPT_PATH.parents[4]
SOURCE_ROOT = Path(os.environ.get("CASA_FYP_SOURCE_ROOT", FYP_ROOT / "authorised_data")).expanduser().resolve()
DEFAULT_INPUT_DIR = SOURCE_ROOT
DEFAULT_OUTPUT_DIR = FYP_ROOT / "outputs" / "preprocessed_busto_1805_min33"

RAW_COLUMNS = [
    "YEAR",
    "DAY_TYPE",
    "TIMEBAND",
    "QHr",
    "ROUTE",
    "DIRECTION",
    "STOPCODE",
    "STOPNAME",
    "STOPSEQUENCE",
    "Boardings",
    "Alightings",
    "Load",
    "Capacity",
    "Seats",
    "V/C",
]

RENAME_COLUMNS = {
    "YEAR": "year",
    "DAY_TYPE": "day_type",
    "TIMEBAND": "timeband",
    "QHr": "qhr",
    "ROUTE": "route",
    "DIRECTION": "direction",
    "STOPCODE": "stopcode",
    "STOPNAME": "stopname",
    "STOPSEQUENCE": "stopsequence",
    "Boardings": "boardings",
    "Alightings": "alightings",
    "Load": "load",
    "Capacity": "capacity",
    "Seats": "seats",
    "V/C": "v_c",
}

READ_DTYPES = {
    "YEAR": "Int16",
    "DAY_TYPE": "string",
    "TIMEBAND": "Int16",
    "QHr": "string",
    "ROUTE": "string",
    "DIRECTION": "Int8",
    "STOPCODE": "string",
    "STOPNAME": "string",
    "STOPSEQUENCE": "float32",
    "Boardings": "float64",
    "Alightings": "float64",
    "Load": "float64",
    "Capacity": "float64",
    "Seats": "float64",
    "V/C": "float64",
}

NIGHT_BLOCK_BINS = [18 * 60, 21 * 60, 24 * 60, 27 * 60, 29 * 60]
NIGHT_BLOCK_LABELS = [
    "18:00-21:00",
    "21:00-00:00",
    "00:00-03:00",
    "03:00-05:00",
]

# Cross-midnight continuation map. BUSTO ships calendar-day (midnight-to-
# midnight) totals, not a TfL "traffic day" (05:00-05:00) product like NUMBAT.
# To build the adopted 18:00-05:00 night window we must borrow each day-type's
# post-midnight hours from the file that is its TRUE chronological successor,
# not from its own file (that would splice a day-type's own early morning --
# which precedes that day-type's evening -- onto its own evening, mixing two
# unrelated nights). Weekday->Weekday is the best available approximation
# (Fri evening cannot be split out of the Weekday bucket), Saturday->Sunday
# and Sunday->Weekday are the genuine calendar successors.
NIGHT_CONTINUATION_SOURCE = {
    "Weekday": "Weekday",
    "Saturday": "Sunday",
    "Sunday": "Weekday",
}
NIGHT_CONTINUATION_TARGETS: dict[str, list[str]] = {}
for _target, _source in NIGHT_CONTINUATION_SOURCE.items():
    NIGHT_CONTINUATION_TARGETS.setdefault(_source, []).append(_target)


@dataclass
class FileAudit:
    """Per-file processing audit."""

    file: str
    size_mb: float
    inferred_day_type: str | None
    inferred_route_group: str | None
    rows_read: int
    rows_night: int
    unique_routes: int
    unique_stops: int
    day_types: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunked preprocessing for BUSTO total-demand CSV files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory to search recursively for BUSTO CSVs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for cleaned outputs.",
    )
    parser.add_argument(
        "--glob",
        default="*TOTAL DEMAND BY ROUTE BY QUARTER HOUR*.csv",
        help="Filename glob used to discover BUSTO total-demand files.",
    )
    parser.add_argument(
        "--sample-files",
        type=int,
        default=None,
        help="Process only the first N matching CSVs, useful for dry-runs.",
    )
    parser.add_argument(
        "--limit-rows-per-file",
        type=int,
        default=None,
        help="Read only the first N rows per file, useful for dry-runs.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500_000,
        help="Rows per pandas read_csv chunk.",
    )
    parser.add_argument(
        "--start-min",
        type=int,
        default=18 * 60,
        help="Night-window start in extended minutes; default 18:00.",
    )
    parser.add_argument(
        "--end-min",
        type=int,
        default=29 * 60,
        help="Night-window end in extended minutes; default 05:00 next day, "
             "matching the dissertation's adopted Rail and Bus window.",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Only inspect file headers and write schema audit.",
    )
    parser.add_argument(
        "--write-format",
        choices=["auto", "parquet", "csv"],
        default="auto",
        help="Format for the main stop-quarter-hour table.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def infer_day_type(path: Path) -> str | None:
    name = path.name.lower()
    for day_type in ["weekday", "saturday", "sunday"]:
        if day_type in name:
            return day_type.title()
    return None


def infer_route_group(path: Path) -> str | None:
    name = path.name
    if "Letter Prefix Routes" in name:
        return "Letter Prefix Routes"
    match = re.search(r"Routes\s+([0-9]+-[0-9]+|[0-9]+\+?)", name)
    if match:
        return f"Routes {match.group(1)}"
    return None


def find_busto_csvs(input_dir: Path, pattern: str) -> list[Path]:
    files = [
        path
        for path in sorted(input_dir.rglob(pattern))
        if path.is_file()
        and "__MACOSX" not in path.parts
        and not path.name.startswith("._")
    ]
    if not files:
        raise FileNotFoundError(f"No BUSTO CSV files found in {input_dir} with {pattern}")
    return files


def read_header(path: Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def build_schema_audit(files: Iterable[Path]) -> pd.DataFrame:
    rows = []
    expected = ",".join(RAW_COLUMNS)
    for path in files:
        header = read_header(path)
        rows.append(
            {
                "file": path.name,
                "size_mb": round(path.stat().st_size / 1024 / 1024, 3),
                "inferred_day_type": infer_day_type(path),
                "inferred_route_group": infer_route_group(path),
                "column_count": len(header),
                "matches_expected_order": header == RAW_COLUMNS,
                "header": ",".join(header),
                "expected_header": expected,
            }
        )
    audit = pd.DataFrame(rows)
    bad = audit.loc[~audit["matches_expected_order"]]
    if not bad.empty:
        raise ValueError(
            "At least one BUSTO CSV has an unexpected header. "
            f"See schema audit rows: {bad['file'].tolist()}"
        )
    return audit


def qhr_to_clock_fields(qhr: pd.Series) -> pd.DataFrame:
    """Parse QHr into real clock hour/minute + same-day base_minute (0-1439).

    No cross-midnight shifting here -- BUSTO is calendar-day data, so the
    correct "next day" source depends on which day-type we are building a
    night window FOR, which is resolved separately per NIGHT_CONTINUATION_SOURCE.
    """
    parts = qhr.astype("string").str.strip().str.extract(
        r"^(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::\d{2})?$"
    )
    hour = pd.to_numeric(parts["hour"], errors="coerce")
    minute = pd.to_numeric(parts["minute"], errors="coerce")
    return pd.DataFrame(
        {
            "hour": hour.astype("Int16"),
            "minute": minute.astype("Int16"),
            "base_minute": (hour * 60 + minute).astype("Int16"),
        }
    )


def assign_night_block(traffic_minute: pd.Series) -> pd.Series:
    return pd.cut(
        traffic_minute,
        bins=NIGHT_BLOCK_BINS,
        labels=NIGHT_BLOCK_LABELS,
        right=False,
        include_lowest=True,
    ).astype("string")


def prepare_chunk(raw: pd.DataFrame, start_min: int, end_min: int) -> pd.DataFrame:
    """Build the night-window rows for this chunk, correctly stitching the
    post-midnight tail onto each day-type's TRUE chronological successor
    (see NIGHT_CONTINUATION_SOURCE) instead of the day-type's own early
    morning.

    Evening rows (start_min <= clock time < 24:00) keep their own day_type
    and are emitted once, at their own base_minute.

    Morning rows (clock time < after_midnight_cutoff) are emitted once PER
    day-type that this file's day_type is the continuation source for (e.g.
    a Weekday file's morning rows are emitted both as Weekday's own
    continuation and, relabelled, as Sunday's continuation), shifted by
    +24h so they sort after that day-type's evening.
    """
    chunk = raw.rename(columns=RENAME_COLUMNS).copy()

    for col in ["day_type", "qhr", "route", "stopcode", "stopname"]:
        chunk[col] = chunk[col].astype("string").str.strip()
    chunk["route"] = chunk["route"].str.upper()

    clock = qhr_to_clock_fields(chunk["qhr"])
    chunk = pd.concat([chunk, clock], axis=1)

    after_midnight_cutoff = end_min % (24 * 60)

    pieces: list[pd.DataFrame] = []

    evening = chunk.loc[chunk["base_minute"] >= start_min].copy()
    if not evening.empty:
        evening["traffic_minute"] = evening["base_minute"].astype("Int16")
        pieces.append(evening)

    morning = chunk.loc[chunk["base_minute"] < after_midnight_cutoff].copy()
    if not morning.empty:
        morning["traffic_minute"] = (morning["base_minute"] + 24 * 60).astype("Int16")
        for source_day_type, sub in morning.groupby("day_type", observed=True):
            for target_day_type in NIGHT_CONTINUATION_TARGETS.get(source_day_type, []):
                relabelled = sub.copy()
                relabelled["day_type"] = target_day_type
                pieces.append(relabelled)

    if not pieces:
        empty = chunk.iloc[0:0].copy()
        empty["traffic_minute"] = pd.Series(dtype="Int16")
        chunk = empty
    else:
        chunk = pd.concat(pieces, ignore_index=True)

    chunk["night_block"] = assign_night_block(chunk["traffic_minute"])
    chunk["is_n_route"] = chunk["route"].str.startswith("N").fillna(False)
    chunk["route_prefix"] = (
        chunk["route"].str.extract(r"^([A-Z]+)", expand=False).fillna("").astype("string")
    )
    return chunk.drop(columns=["base_minute"])


def aggregate_stop_qhr(chunk: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        chunk.groupby(
            [
                "year",
                "day_type",
                "qhr",
                "hour",
                "minute",
                "traffic_minute",
                "night_block",
                "stopcode",
                "stopname",
            ],
            dropna=False,
            observed=True,
        )
        .agg(
            boardings=("boardings", "sum"),
            alightings=("alightings", "sum"),
        )
        .reset_index()
    )
    return grouped


def aggregate_stop_block(stop_qhr: pd.DataFrame) -> pd.DataFrame:
    return (
        stop_qhr.groupby(
            ["year", "day_type", "stopcode", "stopname", "night_block"],
            dropna=False,
            observed=True,
        )
        .agg(
            boardings_sum=("boardings", "sum"),
            alightings_sum=("alightings", "sum"),
        )
        .reset_index()
    )


def aggregate_route_block_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    return (
        chunk.groupby(
            ["year", "day_type", "route", "direction", "night_block", "is_n_route"],
            dropna=False,
            observed=True,
        )
        .agg(
            boardings_sum=("boardings", "sum"),
            alightings_sum=("alightings", "sum"),
            load_sum=("load", "sum"),
            load_count=("load", "count"),
            max_load=("load", "max"),
            v_c_sum=("v_c", "sum"),
            v_c_count=("v_c", "count"),
            max_v_c=("v_c", "max"),
        )
        .reset_index()
    )


def combine_stop_qhr(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    return aggregate_stop_qhr(combined)


def combine_route_block(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    grouped = (
        combined.groupby(
            ["year", "day_type", "route", "direction", "night_block", "is_n_route"],
            dropna=False,
            observed=True,
        )
        .agg(
            boardings_sum=("boardings_sum", "sum"),
            alightings_sum=("alightings_sum", "sum"),
            load_sum=("load_sum", "sum"),
            load_count=("load_count", "sum"),
            max_load=("max_load", "max"),
            v_c_sum=("v_c_sum", "sum"),
            v_c_count=("v_c_count", "sum"),
            max_v_c=("max_v_c", "max"),
        )
        .reset_index()
    )
    grouped["mean_load"] = grouped["load_sum"] / grouped["load_count"].replace(0, np.nan)
    grouped["mean_v_c"] = grouped["v_c_sum"] / grouped["v_c_count"].replace(0, np.nan)
    return grouped.drop(columns=["load_sum", "load_count", "v_c_sum", "v_c_count"])


def build_stop_meta(stop_route_pairs: pd.DataFrame) -> pd.DataFrame:
    if stop_route_pairs.empty:
        return pd.DataFrame()
    pairs = stop_route_pairs.drop_duplicates()
    flags = pairs.assign(is_daytime_route=~pairs["is_n_route"])
    meta = (
        flags.groupby(["stopcode", "stopname"], dropna=False, observed=True)
        .agg(
            route_count=("route", "nunique"),
            n_route_count=("is_n_route", "sum"),
            daytime_route_count=("is_daytime_route", "sum"),
        )
        .reset_index()
    )
    meta["route_mix"] = np.select(
        [
            (meta["n_route_count"] > 0) & (meta["daytime_route_count"] == 0),
            (meta["n_route_count"] == 0) & (meta["daytime_route_count"] > 0),
            (meta["n_route_count"] > 0) & (meta["daytime_route_count"] > 0),
        ],
        ["N_only", "daytime_only", "mixed"],
        default="unknown",
    )
    return meta


def write_table(df: pd.DataFrame, path_without_suffix: Path, write_format: str) -> Path:
    if write_format == "auto":
        write_format = "parquet" if importlib.util.find_spec("pyarrow") else "csv"

    if write_format == "parquet":
        output_path = path_without_suffix.with_suffix(".parquet")
        df.to_parquet(output_path, index=False)
        return output_path

    output_path = path_without_suffix.with_suffix(".csv")
    df.to_csv(output_path, index=False)
    return output_path


def process_files(args: argparse.Namespace, files: list[Path]) -> dict[str, str]:
    stop_qhr_frames: list[pd.DataFrame] = []
    route_block_frames: list[pd.DataFrame] = []
    stop_route_frames: list[pd.DataFrame] = []
    hourly_frames: list[pd.DataFrame] = []
    file_audits: list[FileAudit] = []

    for file_index, path in enumerate(files, start=1):
        LOGGER.info("Processing %s/%s: %s", file_index, len(files), path.name)
        rows_read = 0
        rows_night = 0
        route_values: set[str] = set()
        stop_values: set[str] = set()
        day_type_values: set[str] = set()

        reader = pd.read_csv(
            path,
            usecols=RAW_COLUMNS,
            dtype=READ_DTYPES,
            chunksize=args.chunk_size,
            nrows=args.limit_rows_per_file,
        )

        for chunk_index, raw_chunk in enumerate(reader, start=1):
            rows_read += len(raw_chunk)
            chunk = prepare_chunk(raw_chunk, args.start_min, args.end_min)
            rows_night += len(chunk)
            if chunk.empty:
                continue

            route_values.update(chunk["route"].dropna().astype(str).unique().tolist())
            stop_values.update(chunk["stopcode"].dropna().astype(str).unique().tolist())
            day_type_values.update(chunk["day_type"].dropna().astype(str).unique().tolist())

            stop_qhr_frames.append(aggregate_stop_qhr(chunk))
            route_block_frames.append(aggregate_route_block_chunk(chunk))
            stop_route_frames.append(
                chunk[["stopcode", "stopname", "route", "is_n_route"]].drop_duplicates()
            )
            hourly_frames.append(
                chunk.assign(route_class=np.where(chunk["is_n_route"], "N", "non_N"))
                .groupby(["day_type", "hour", "route_class"], dropna=False, observed=True)
                .agg(
                    boardings_sum=("boardings", "sum"),
                    alightings_sum=("alightings", "sum"),
                    rows=("route", "size"),
                )
                .reset_index()
            )
            LOGGER.debug(
                "Processed chunk %s from %s: raw=%s night=%s",
                chunk_index,
                path.name,
                len(raw_chunk),
                len(chunk),
            )

        file_audits.append(
            FileAudit(
                file=path.name,
                size_mb=round(path.stat().st_size / 1024 / 1024, 3),
                inferred_day_type=infer_day_type(path),
                inferred_route_group=infer_route_group(path),
                rows_read=rows_read,
                rows_night=rows_night,
                unique_routes=len(route_values),
                unique_stops=len(stop_values),
                day_types=";".join(sorted(day_type_values)),
            )
        )

    LOGGER.info("Combining aggregated chunks")
    stop_qhr = combine_stop_qhr(stop_qhr_frames)
    stop_block = aggregate_stop_block(stop_qhr)
    route_block = combine_route_block(route_block_frames)

    stop_routes = (
        pd.concat(stop_route_frames, ignore_index=True).drop_duplicates()
        if stop_route_frames
        else pd.DataFrame(columns=["stopcode", "stopname", "route", "is_n_route"])
    )
    stop_meta = build_stop_meta(stop_routes)

    hourly_audit = (
        pd.concat(hourly_frames, ignore_index=True)
        .groupby(["day_type", "hour", "route_class"], dropna=False, observed=True)
        .agg(
            boardings_sum=("boardings_sum", "sum"),
            alightings_sum=("alightings_sum", "sum"),
            rows=("rows", "sum"),
        )
        .reset_index()
        if hourly_frames
        else pd.DataFrame()
    )
    file_audit = pd.DataFrame([asdict(item) for item in file_audits])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    main_path = write_table(stop_qhr, args.output_dir / "busto_stop_qhr_night", args.write_format)
    stop_meta.to_csv(args.output_dir / "busto_stop_meta.csv", index=False)
    stop_block.to_csv(args.output_dir / "busto_stop_block.csv", index=False)
    route_block.to_csv(args.output_dir / "busto_route_block.csv", index=False)
    hourly_audit.to_csv(args.output_dir / "busto_hourly_audit.csv", index=False)
    file_audit.to_csv(args.output_dir / "busto_file_audit.csv", index=False)

    audit = {
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "files_processed": len(files),
        "sample_files": args.sample_files,
        "limit_rows_per_file": args.limit_rows_per_file,
        "chunk_size": args.chunk_size,
        "start_min": args.start_min,
        "end_min": args.end_min,
        "main_output": str(main_path),
        "stop_qhr_rows": int(len(stop_qhr)),
        "stop_meta_rows": int(len(stop_meta)),
        "stop_block_rows": int(len(stop_block)),
        "route_block_rows": int(len(route_block)),
        "route_mix_counts": stop_meta["route_mix"].value_counts(dropna=False).to_dict()
        if not stop_meta.empty
        else {},
    }
    with (args.output_dir / "busto_preprocess_audit.json").open("w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    return {key: str(value) for key, value in audit.items()}


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    args.input_dir = args.input_dir.resolve()
    args.output_dir = args.output_dir.resolve()

    files = find_busto_csvs(args.input_dir, args.glob)
    if args.sample_files is not None:
        files = files[: args.sample_files]

    LOGGER.info("Found %s BUSTO CSV files", len(files))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    schema_audit = build_schema_audit(files)
    schema_audit.to_csv(args.output_dir / "busto_schema_audit.csv", index=False)

    if args.schema_only:
        LOGGER.info("Schema-only mode complete: %s", args.output_dir / "busto_schema_audit.csv")
        return

    audit = process_files(args, files)
    LOGGER.info("Completed BUSTO preprocessing")
    LOGGER.info("Main output: %s", audit["main_output"])


if __name__ == "__main__":
    main()
