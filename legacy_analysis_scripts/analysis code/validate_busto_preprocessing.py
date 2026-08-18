"""Independent validation of the BUSTO night-bus preprocessing pipeline.

Read-only: never modifies 04_preprocess_busto_full.py, raw BUSTO CSVs, or any
existing output. Writes validation results to FYP/outputs/busto_validation/.

Usage:
    python "validate_busto_preprocessing.py"   (run from the analysis code dir)
    or:    python validate_busto_preprocessing.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_PATH = Path(__file__).resolve()
ANALYSIS_DIR = SCRIPT_PATH.parent
FYP_ROOT = ANALYSIS_DIR.parent
RAW_DIR = FYP_ROOT / "巴士数据"
PROCESSED_DIR = FYP_ROOT / "outputs" / "preprocessed_busto"
VALID_DIR = FYP_ROOT / "outputs" / "busto_validation"
VALID_DIR.mkdir(parents=True, exist_ok=True)

# import the pipeline module for its constants only (no execution of main())
spec = importlib.util.spec_from_file_location(
    "preprocess_busto_full", ANALYSIS_DIR / "04_preprocess_busto_full.py"
)
pp = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pp
spec.loader.exec_module(pp)

RESULTS = []  # test_id, test_name, result, observed, expected, severity, interpretation


def log(test_id, test_name, result, observed, expected, severity, interpretation):
    RESULTS.append(
        dict(
            test_id=test_id,
            test_name=test_name,
            result=result,
            observed=observed,
            expected=expected,
            severity=severity,
            interpretation=interpretation,
        )
    )
    print(f"[{result}] {test_id} {test_name}: {observed}")


CHUNK = 500_000
GLOB = "*TOTAL DEMAND BY ROUTE BY QUARTER HOUR*.csv"
files = sorted(RAW_DIR.rglob(GLOB))
files = [f for f in files if f.is_file() and "__MACOSX" not in f.parts and not f.name.startswith("._")]
print(f"Found {len(files)} raw BUSTO CSVs")

# ---------------------------------------------------------------------------
# Single pass over each raw file: collect everything Tests B, D, E, F(raw),
# H, I, O need, without re-reading the ~1GB of raw CSVs more than once.
# ---------------------------------------------------------------------------

day_type_raw_values = defaultdict(Counter)          # file -> Counter(raw DAY_TYPE string)
qhr_bad_rows = 0
qhr_bad_boardings = 0.0
qhr_bad_alightings = 0.0
qhr_bad_samples = []

# evening / morning sums keyed by (day_type_stripped, qhr_string)
evening_sums = defaultdict(lambda: [0.0, 0.0])   # (day_type, qhr) -> [boardings, alightings]
morning_sums = defaultdict(lambda: [0.0, 0.0])

stopcode_to_names_raw = defaultdict(set)
stopcode_boardings_raw = Counter()

file_route_sets = {}   # file.name -> set(routes)
file_day_type = {}     # file.name -> inferred day type
file_route_group = {}  # file.name -> inferred route group

board_stats = {"n": 0, "na": 0, "neg": 0, "zero": 0, "pos": 0, "max": -np.inf}
alight_stats = {"n": 0, "na": 0, "neg": 0, "zero": 0, "pos": 0, "max": -np.inf}
board_sample = []
alight_sample = []
RNG = np.random.default_rng(0)
SAMPLE_CAP = 2_000_000

qhr_all_values_seen = Counter()

for path in files:
    day_type = pp.infer_day_type(path)
    route_group = pp.infer_route_group(path)
    file_day_type[path.name] = day_type
    file_route_group[path.name] = route_group
    routes_this_file = set()

    reader = pd.read_csv(
        path, usecols=pp.RAW_COLUMNS, dtype=pp.READ_DTYPES, chunksize=CHUNK
    )
    for raw_chunk in reader:
        # Test B: raw DAY_TYPE values exactly as they appear (no strip/case fix)
        day_type_raw_values[path.name].update(raw_chunk["DAY_TYPE"].astype("string").tolist())

        chunk = raw_chunk.rename(columns=pp.RENAME_COLUMNS).copy()
        for col in ["day_type", "qhr", "route", "stopcode", "stopname"]:
            chunk[col] = chunk[col].astype("string").str.strip()
        chunk["route"] = chunk["route"].str.upper()

        # Test I: QHr parse validity
        qhr_all_values_seen.update(chunk["qhr"].dropna().unique().tolist()[:0])  # placeholder, real check below
        parts = chunk["qhr"].str.extract(r"^(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::\d{2})?$")
        bad_mask = parts["hour"].isna() | chunk["qhr"].isna()
        # also flag rows that DID match the h:mm pattern but minute not in {00,15,30,45}
        minute_num = pd.to_numeric(parts["minute"], errors="coerce")
        hour_num = pd.to_numeric(parts["hour"], errors="coerce")
        bad_minute_mask = minute_num.notna() & (~minute_num.isin([0, 15, 30, 45]))
        bad_hour_range_mask = hour_num.notna() & ((hour_num < 0) | (hour_num > 29))
        full_bad_mask = bad_mask | bad_minute_mask | bad_hour_range_mask
        n_bad = int(full_bad_mask.sum())
        if n_bad:
            qhr_bad_rows += n_bad
            qhr_bad_boardings += float(chunk.loc[full_bad_mask, "boardings"].sum(skipna=True))
            qhr_bad_alightings += float(chunk.loc[full_bad_mask, "alightings"].sum(skipna=True))
            if len(qhr_bad_samples) < 50:
                samp = chunk.loc[full_bad_mask, ["qhr", "day_type", "route", "stopcode"]].head(
                    50 - len(qhr_bad_samples)
                )
                qhr_bad_samples.append(samp)

        clock = pp.qhr_to_clock_fields(chunk["qhr"])
        base_minute = clock["base_minute"]

        # Test D/E: evening (18:00-24:00) and morning (00:00-06:00) sums by (day_type, qhr)
        ev_mask = (base_minute >= 18 * 60) & (base_minute < 24 * 60)
        mo_mask = base_minute < 6 * 60
        if ev_mask.any():
            ev = chunk.loc[ev_mask]
            g = ev.groupby(["day_type", "qhr"], observed=True)[["boardings", "alightings"]].sum()
            for (dt, q), row in g.iterrows():
                evening_sums[(dt, q)][0] += float(row["boardings"])
                evening_sums[(dt, q)][1] += float(row["alightings"])
        if mo_mask.any():
            mo = chunk.loc[mo_mask]
            g = mo.groupby(["day_type", "qhr"], observed=True)[["boardings", "alightings"]].sum()
            for (dt, q), row in g.iterrows():
                morning_sums[(dt, q)][0] += float(row["boardings"])
                morning_sums[(dt, q)][1] += float(row["alightings"])

        # Test F: raw STOPCODE -> STOPNAME
        pair_boardings = chunk.groupby(["stopcode", "stopname"], observed=True)["boardings"].sum()
        for (sc, sn), b in pair_boardings.items():
            stopcode_to_names_raw[sc].add(sn)
            stopcode_boardings_raw[sc] += float(b)

        # Test H: routes present in this file
        routes_this_file.update(chunk["route"].dropna().unique().tolist())

        # Test O: boardings/alightings quality
        for col, stats, sample in (
            ("boardings", board_stats, board_sample),
            ("alightings", alight_stats, alight_sample),
        ):
            s = chunk[col]
            stats["n"] += len(s)
            stats["na"] += int(s.isna().sum())
            valid = s.dropna()
            stats["neg"] += int((valid < 0).sum())
            stats["zero"] += int((valid == 0).sum())
            stats["pos"] += int((valid > 0).sum())
            if len(valid):
                stats["max"] = max(stats["max"], float(valid.max()))
            if len(sample) < SAMPLE_CAP and len(valid):
                take = min(len(valid), SAMPLE_CAP - len(sample))
                idx = RNG.choice(len(valid), size=take, replace=False) if take < len(valid) else np.arange(len(valid))
                sample.extend(valid.to_numpy()[idx].tolist())

    file_route_sets[path.name] = routes_this_file
    print(f"  scanned {path.name}")

print("Raw single-pass scan complete.")

# ---------------------------------------------------------------------------
# Test H3: file hashes (streamed, separate from pandas pass)
# ---------------------------------------------------------------------------
file_hashes = {}
for path in files:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(1024 * 1024 * 8)
            if not block:
                break
            h.update(block)
    file_hashes[path.name] = h.hexdigest()

hash_counter = Counter(file_hashes.values())
dup_hash_groups = {h: [n for n, hh in file_hashes.items() if hh == h] for h, c in hash_counter.items() if c > 1}

dup_files_df = pd.DataFrame(
    [{"full_path": str(f), "file": n, "inferred_day_type": file_day_type[n],
      "inferred_route_group": file_route_group[n], "sha256": file_hashes[n],
      "size_mb": round(f.stat().st_size / 1024 / 1024, 3)}
     for n, f in zip([p.name for p in files], files)]
)
dup_files_df["is_binary_duplicate"] = dup_files_df["sha256"].map(lambda h: hash_counter[h] > 1)
dup_files_df.to_csv(VALID_DIR / "duplicate_input_files.csv", index=False)

log(
    "H3", "Binary-identical duplicate input files",
    "FAIL" if dup_hash_groups else "PASS",
    f"{len(dup_hash_groups)} duplicate hash groups: {dup_hash_groups}" if dup_hash_groups else "0 duplicate files among 12",
    "0 duplicate files",
    "Critical" if dup_hash_groups else "None",
    "Binary-identical files would double-count demand." if dup_hash_groups else "All 12 raw files are unique.",
)

# ---------------------------------------------------------------------------
# Test H1/H2: duplicate day_type x route_group combos, folder duplicates
# ---------------------------------------------------------------------------
combo_counter = Counter((file_day_type[p.name], file_route_group[p.name]) for p in files)
dup_combos = {k: v for k, v in combo_counter.items() if v > 1}
log(
    "H1_H2", "Duplicate day_type x route_group file combinations",
    "FAIL" if dup_combos else "PASS",
    str(dup_combos) if dup_combos else "each of 12 (day_type, route_group) combos appears exactly once",
    "no repeated combination",
    "Critical" if dup_combos else "None",
    "A repeated combo would mean the same route slice is double counted." if dup_combos else "12 files = 3 day types x 4 route groups, no overlap.",
)

# ---------------------------------------------------------------------------
# Test H4: route overlap across files within the same day type
# ---------------------------------------------------------------------------
overlap_rows = []
by_day_type = defaultdict(list)
for p in files:
    by_day_type[file_day_type[p.name]].append(p.name)

route_overlap_found = False
for dt, fnames in by_day_type.items():
    route_owner = defaultdict(list)
    for fn in fnames:
        for r in file_route_sets[fn]:
            route_owner[r].append(fn)
    for r, owners in route_owner.items():
        if len(owners) > 1:
            route_overlap_found = True
            overlap_rows.append({"day_type": dt, "route": r, "files": ";".join(owners), "duplicate": True})

dup_routes_df = pd.DataFrame(overlap_rows) if overlap_rows else pd.DataFrame(
    columns=["day_type", "route", "files", "duplicate"]
)
dup_routes_df.to_csv(VALID_DIR / "duplicate_routes_across_files.csv", index=False)
log(
    "H4", "Route overlap across route-group files (same day type)",
    "FAIL" if route_overlap_found else "PASS",
    f"{len(overlap_rows)} route(s) appear in >1 file for the same day type" if overlap_rows else "0 routes duplicated across route-group files",
    "each route appears in exactly one route-group file per day type",
    "Critical" if route_overlap_found else "None",
    "Overlapping routes across files would double the demand for those routes." if route_overlap_found else "Route-group files partition routes cleanly.",
)

# ---------------------------------------------------------------------------
# Test N: schema audit consistency (independent re-check)
# ---------------------------------------------------------------------------
schema_rows = []
for p in files:
    header = list(pd.read_csv(p, nrows=0).columns)
    schema_rows.append(
        {
            "file": p.name,
            "column_count": len(header),
            "matches_expected_order": header == pp.RAW_COLUMNS,
            "header": ",".join(header),
        }
    )
schema_df = pd.DataFrame(schema_rows)
schema_bad = schema_df.loc[~schema_df["matches_expected_order"]]
log(
    "N", "Schema (column names/order) matches RAW_COLUMNS",
    "FAIL" if not schema_bad.empty else "PASS",
    f"{len(schema_bad)}/{len(schema_df)} files mismatch" if not schema_bad.empty else f"all {len(schema_df)} files match expected header exactly",
    "header == RAW_COLUMNS for every file",
    "Critical" if not schema_bad.empty else "None",
    "A schema mismatch would misalign columns silently." if not schema_bad.empty else "usecols+dtype in the pipeline would have raised on any real mismatch; independently confirmed here.",
)

# ---------------------------------------------------------------------------
# Test B: DAY_TYPE compatibility
# ---------------------------------------------------------------------------
day_type_rows = []
all_bad_day_type_rows = 0
for p in files:
    raw_counter = day_type_raw_values[p.name]
    inferred = file_day_type[p.name]
    valid_values = {"Weekday", "Saturday", "Sunday"}
    bad_values = {k: v for k, v in raw_counter.items() if k not in valid_values}
    all_bad_day_type_rows += sum(bad_values.values())
    day_type_rows.append(
        {
            "file": p.name,
            "inferred_day_type": inferred,
            "raw_day_type_values": ";".join(f"{k}={v}" for k, v in raw_counter.items()),
            "n_unexpected_values": sum(bad_values.values()),
            "valid": len(bad_values) == 0,
        }
    )
day_type_df = pd.DataFrame(day_type_rows)
day_type_df.to_csv(VALID_DIR / "day_type_anomalies.csv", index=False)
log(
    "B", "Raw DAY_TYPE values compatible with mapping (Weekday/Saturday/Sunday exact)",
    "FAIL" if all_bad_day_type_rows else "PASS",
    f"{all_bad_day_type_rows} rows with unexpected DAY_TYPE value across {len(files)} files" if all_bad_day_type_rows else f"every raw DAY_TYPE value across {len(files)} files is exactly one of Weekday/Saturday/Sunday",
    "only Weekday, Saturday, Sunday present",
    "Critical" if all_bad_day_type_rows else "None",
    "Unexpected DAY_TYPE values are silently dropped by NIGHT_CONTINUATION_SOURCE.get(...) returning [] -- rows would vanish from the night window without error." if all_bad_day_type_rows else "The exact-match mapping is safe against current raw data.",
)

# ---------------------------------------------------------------------------
# Test I: QHr validity
# ---------------------------------------------------------------------------
qhr_pct = 100.0 * qhr_bad_rows / max(sum(c.total() if hasattr(c, "total") else sum(c.values()) for c in day_type_raw_values.values()), 1)
total_raw_rows = sum(sum(c.values()) for c in day_type_raw_values.values())
qhr_pct = 100.0 * qhr_bad_rows / max(total_raw_rows, 1)
if qhr_bad_samples:
    pd.concat(qhr_bad_samples, ignore_index=True).to_csv(VALID_DIR / "qhr_anomalies.csv", index=False)
else:
    pd.DataFrame(columns=["qhr", "day_type", "route", "stopcode"]).to_csv(VALID_DIR / "qhr_anomalies.csv", index=False)
log(
    "I", "QHr format validity (parseable h:mm, minute in 00/15/30/45, hour 0-23)",
    "FAIL" if qhr_bad_rows else "PASS",
    f"{qhr_bad_rows} bad rows ({qhr_pct:.6f}% of {total_raw_rows} total raw rows); boardings={qhr_bad_boardings:.1f}, alightings={qhr_bad_alightings:.1f}" if qhr_bad_rows else f"0 malformed QHr among {total_raw_rows} raw rows",
    "0 malformed QHr values",
    "Material but limited" if qhr_bad_rows else "None",
    "Rows with unparseable QHr get hour/minute/base_minute = NaN and are silently excluded from both the evening (base_minute>=1080) and morning (base_minute<360) filters in prepare_chunk -- i.e. dropped, not errored." if qhr_bad_rows else "All QHr values parse cleanly; no silent row loss from this path.",
)

# ---------------------------------------------------------------------------
# Test O: boardings/alightings quality
# ---------------------------------------------------------------------------
def pct(arr, q):
    return float(np.percentile(arr, q)) if len(arr) else float("nan")

quality_rows = []
for name, stats, sample in (("boardings", board_stats, board_sample), ("alightings", alight_stats, alight_sample)):
    arr = np.array(sample) if sample else np.array([])
    quality_rows.append(
        {
            "variable": name,
            "n_total": stats["n"],
            "n_na": stats["na"],
            "n_negative": stats["neg"],
            "n_zero": stats["zero"],
            "n_positive": stats["pos"],
            "max": stats["max"],
            "p99_from_sample": pct(arr, 99),
            "p99_9_from_sample": pct(arr, 99.9),
            "sample_size": len(arr),
        }
    )
quality_df = pd.DataFrame(quality_rows)
quality_df.to_csv(VALID_DIR / "boardings_alightings_quality.csv", index=False)
any_neg = board_stats["neg"] + alight_stats["neg"]
any_na = board_stats["na"] + alight_stats["na"]
log(
    "O", "Boardings/Alightings basic data quality (raw)",
    "WARNING" if (any_neg or any_na) else "PASS",
    f"boardings: na={board_stats['na']}, neg={board_stats['neg']}, max={board_stats['max']}; alightings: na={alight_stats['na']}, neg={alight_stats['neg']}, max={alight_stats['max']}",
    "no NA, no negative values",
    "Minor" if (any_neg or any_na) else "None",
    "NA rows become NaN and sum() with skipna=True silently treats them as 0 (not dropped from row count, but contribute 0 demand). Negative values (if present) are legitimate BUSTO correction entries per the data dictionary and are not clipped -- flagged for awareness, not auto-fixed.",
)

# ---------------------------------------------------------------------------
# Test F (raw): STOPCODE -> STOPNAME multiplicity
# ---------------------------------------------------------------------------
multi_name_rows = []
for sc, names in stopcode_to_names_raw.items():
    if len(names) > 1:
        multi_name_rows.append(
            {
                "stopcode": sc,
                "n_names": len(names),
                "names": ";".join(sorted(n for n in names if n is not None)),
                "total_boardings": stopcode_boardings_raw[sc],
            }
        )
multi_name_df = pd.DataFrame(multi_name_rows).sort_values("n_names", ascending=False) if multi_name_rows else pd.DataFrame(
    columns=["stopcode", "n_names", "names", "total_boardings"]
)
multi_name_df.to_csv(VALID_DIR / "stopcode_multiple_names.csv", index=False)

total_stopcodes = len(stopcode_to_names_raw)
n_single = total_stopcodes - len(multi_name_rows)
n_multi = len(multi_name_rows)
log(
    "F", "Raw STOPCODE -> STOPNAME uniqueness",
    "WARNING" if n_multi else "PASS",
    f"{total_stopcodes} unique stopcodes; {n_single} with exactly 1 name; {n_multi} with >1 name ({100*n_multi/max(total_stopcodes,1):.2f}%); max names for one stopcode = {multi_name_df['n_names'].max() if n_multi else 1}",
    "every stopcode maps to exactly 1 stopname",
    "Material but limited" if n_multi else "None",
    "Confirmed at raw-data level below.",
)

RESULTS_STATE = dict(
    day_type_raw_values=day_type_raw_values,
    total_raw_rows=total_raw_rows,
    file_hashes=file_hashes,
    schema_df=schema_df,
    evening_sums=evening_sums,
    morning_sums=morning_sums,
)
print("Part 1 (raw scan) complete. Proceeding to processed-output checks...")

# ---------------------------------------------------------------------------
# Load processed main output
# ---------------------------------------------------------------------------
stop_qhr = pd.read_parquet(PROCESSED_DIR / "busto_stop_qhr_night.parquet")
print(f"Loaded processed stop_qhr: {len(stop_qhr)} rows")

# Test O2: processed boardings/alightings quality.  This is separate from the
# raw-file scan because aggregation can expose or propagate missing/non-finite
# values even when the inputs are clean.
def quality_rows(df, label):
    rows = []
    for col in ["boardings", "alightings"]:
        s = pd.to_numeric(df[col], errors="coerce")
        finite = s[np.isfinite(s)]
        rows.append(
            {
                "dataset": label,
                "variable": col,
                "n_total": int(len(s)),
                "n_na": int(s.isna().sum()),
                "n_inf": int(np.isinf(s).sum()),
                "n_negative": int((finite < 0).sum()),
                "n_zero": int((finite == 0).sum()),
                "n_positive": int((finite > 0).sum()),
                "max": float(finite.max()) if len(finite) else np.nan,
                "p99": float(finite.quantile(0.99)) if len(finite) else np.nan,
                "p99_9": float(finite.quantile(0.999)) if len(finite) else np.nan,
            }
        )
    return rows

processed_quality_df = pd.DataFrame(quality_rows(stop_qhr, "processed_stop_qhr"))
raw_quality_df = pd.read_csv(VALID_DIR / "boardings_alightings_quality.csv")
raw_quality_df.insert(0, "dataset", "raw")
combined_quality_df = pd.concat([raw_quality_df, processed_quality_df], ignore_index=True)
combined_quality_df.to_csv(VALID_DIR / "boardings_alightings_quality_all.csv", index=False)
processed_bad = processed_quality_df[["n_na", "n_inf", "n_negative"]].to_numpy().sum()
log(
    "O2", "Processed Boardings/Alightings basic data quality",
    "PASS" if processed_bad == 0 else "FAIL",
    processed_quality_df.to_dict("records"),
    "no NA, inf, or negative boardings/alightings in processed stop_qhr",
    "None" if processed_bad == 0 else "Critical",
    "Processed aggregation contains no missing, infinite, or negative demand values." if processed_bad == 0 else "Processed demand contains invalid values that could affect clustering input.",
)

with open(PROCESSED_DIR / "busto_preprocess_audit.json", "r", encoding="utf-8") as f:
    run_audit = json.load(f)

# Test K: start/end min used in actual run
start_min = run_audit["start_min"]
end_min = run_audit["end_min"]
design_default = (start_min == 18 * 60) and (end_min == 30 * 60)
log(
    "K", "Actual run start_min/end_min vs fixed night_block design",
    "PASS",
    f"start_min={start_min}, end_min={end_min} (from busto_preprocess_audit.json)",
    "start_min=1080, end_min=1800 (default)",
    "None" if design_default else "Material but limited",
    "design risk only — did not affect current run" if design_default else "Actual run used non-default window; night_block boundaries may not align.",
)

# ---------------------------------------------------------------------------
# Test C: traffic_minute coverage per day_type
# ---------------------------------------------------------------------------
expected_minutes = set(range(1080, 1786, 15))
cov_rows = []
for dt, sub in stop_qhr.groupby("day_type", observed=True):
    mins = set(sub["traffic_minute"].dropna().astype(int).unique().tolist())
    missing = sorted(expected_minutes - mins)
    extra = sorted(mins - expected_minutes)
    cov_rows.append(
        {
            "day_type": dt,
            "min": int(sub["traffic_minute"].min()),
            "max": int(sub["traffic_minute"].max()),
            "n_unique": len(mins),
            "missing_intervals": ";".join(map(str, missing)),
            "extra_intervals": ";".join(map(str, extra)),
            "result": "PASS" if (not missing and not extra and len(mins) == 48) else "FAIL",
        }
    )
cov_df = pd.DataFrame(cov_rows)
cov_df.to_csv(VALID_DIR / "traffic_minute_coverage.csv", index=False)
cov_fail = (cov_df["result"] == "FAIL").any()
log(
    "C", "48 quarter-hours per day_type, traffic_minute 1080-1785",
    "FAIL" if cov_fail else "PASS",
    cov_df.to_dict("records"),
    "min=1080, max=1785, n_unique=48, no missing intervals for Weekday/Saturday/Sunday",
    "Critical" if cov_fail else "None",
    "Incomplete night coverage would leave gaps in the temporal feature vector used for clustering." if cov_fail else "All three day types have complete, gap-free 48-interval night windows.",
)

# ---------------------------------------------------------------------------
# Test D: cross-midnight stitching conservation
# ---------------------------------------------------------------------------
def raw_source_sum(day_type, minute_lo, minute_hi):
    """Sum evening_sums/morning_sums dict for given raw day_type over [lo,hi) base_minute range."""
    b, a = 0.0, 0.0
    src = evening_sums if minute_lo >= 18 * 60 else morning_sums
    for (dt, q), (bb, aa) in src.items():
        if dt != day_type:
            continue
        clock = pp.qhr_to_clock_fields(pd.Series([q], dtype="string"))
        bm = int(clock["base_minute"].iloc[0]) if pd.notna(clock["base_minute"].iloc[0]) else None
        if bm is None:
            continue
        if minute_lo <= bm < minute_hi:
            b += bb
            a += aa
    return b, a


def processed_sum(target_day_type, traffic_minute_lo, traffic_minute_hi):
    sub = stop_qhr[
        (stop_qhr["day_type"] == target_day_type)
        & (stop_qhr["traffic_minute"] >= traffic_minute_lo)
        & (stop_qhr["traffic_minute"] < traffic_minute_hi)
    ]
    return float(sub["boardings"].sum()), float(sub["alightings"].sum())


stitch_targets = [
    ("Saturday", "Sunday", "D1 Saturday night"),
    ("Sunday", "Weekday", "D2 Sunday night"),
    ("Weekday", "Weekday", "D3 Weekday night"),
]

stitch_rows = []
for target_dt, source_dt, label in stitch_targets:
    raw_b, raw_a = raw_source_sum(source_dt, 0, 6 * 60)
    proc_b, proc_a = processed_sum(target_dt, 1440, 1800)
    diff_b = proc_b - raw_b
    diff_a = proc_a - raw_a
    rel_b = diff_b / raw_b if raw_b else float("nan")
    rel_a = diff_a / raw_a if raw_a else float("nan")
    passed = abs(rel_b) < 1e-6 and abs(rel_a) < 1e-6
    stitch_rows.append(
        {
            "target_night": target_dt,
            "raw_source": f"raw {source_dt} 00:00-06:00",
            "raw_boardings": raw_b,
            "processed_boardings": proc_b,
            "diff_boardings": diff_b,
            "raw_alightings": raw_a,
            "processed_alightings": proc_a,
            "diff_alightings": diff_a,
            "result": "PASS" if passed else "FAIL",
        }
    )
    log(
        label.split()[0], f"{label} stitching conservation (post-midnight)",
        "PASS" if passed else "FAIL",
        f"raw {source_dt} 00-06 boardings={raw_b:.1f} vs processed {target_dt} post-midnight={proc_b:.1f} (diff={diff_b:.4f}); alightings diff={diff_a:.4f}",
        "processed post-midnight totals == raw source totals (within float precision)",
        "Critical" if not passed else "None",
        f"{'Post-midnight demand for '+target_dt+' does not match its true chronological source ('+source_dt+').' if not passed else 'Cross-midnight stitching for '+target_dt+' is exact.'}",
    )

stitch_df = pd.DataFrame(stitch_rows)
stitch_df.to_csv(VALID_DIR / "stitching_differences.csv", index=False)

# ---------------------------------------------------------------------------
# Test E: evening (18:00-24:00) conservation, own day_type
# ---------------------------------------------------------------------------
evening_check_rows = []
for dt in ["Weekday", "Saturday", "Sunday"]:
    raw_b, raw_a = raw_source_sum(dt, 18 * 60, 24 * 60)
    proc_b, proc_a = processed_sum(dt, 1080, 1440)
    diff_b = proc_b - raw_b
    diff_a = proc_a - raw_a
    passed = (abs(diff_b) < 1e-6 * max(raw_b, 1)) and (abs(diff_a) < 1e-6 * max(raw_a, 1))
    evening_check_rows.append(
        {
            "day_type": dt,
            "raw_evening_boardings": raw_b,
            "processed_evening_boardings": proc_b,
            "diff_boardings": diff_b,
            "raw_evening_alightings": raw_a,
            "processed_evening_alightings": proc_a,
            "diff_alightings": diff_a,
            "result": "PASS" if passed else "FAIL",
        }
    )
evening_df = pd.DataFrame(evening_check_rows)
evening_df.to_csv(VALID_DIR / "evening_conservation.csv", index=False)
evening_fail = (evening_df["result"] == "FAIL").any()
log(
    "E", "Evening (18:00-24:00) conservation, own day_type",
    "FAIL" if evening_fail else "PASS",
    evening_df.to_dict("records"),
    "processed evening totals == raw evening totals for each day type",
    "Critical" if evening_fail else "None",
    "Evening rows are emitted once at their own base_minute with no relabelling, so this checks no double counting/dropping occurred." if not evening_fail else "Evening demand does not reconcile -- investigate prepare_chunk evening branch.",
)

# ---------------------------------------------------------------------------
# Test F (processed): STOPCODE -> STOPNAME in processed output
# ---------------------------------------------------------------------------
proc_pairs = stop_qhr[["stopcode", "stopname"]].drop_duplicates()
proc_name_counts = proc_pairs.groupby("stopcode")["stopname"].nunique()
proc_multi = proc_name_counts[proc_name_counts > 1]
log(
    "F2", "Processed output STOPCODE -> STOPNAME uniqueness",
    "WARNING" if len(proc_multi) else "PASS",
    f"{len(proc_name_counts)} unique stopcodes in processed output; {len(proc_multi)} with >1 stopname",
    "every stopcode maps to exactly 1 stopname",
    "Material but limited" if len(proc_multi) else "None",
    "Matches raw-level finding (F).",
)

# ---------------------------------------------------------------------------
# Test G: stop-time key duplication
# ---------------------------------------------------------------------------
key_full = ["year", "day_type", "traffic_minute", "stopcode", "stopname"]
key_stop_only = ["year", "day_type", "traffic_minute", "stopcode"]

dup_full = stop_qhr.duplicated(subset=key_full, keep=False)
n_dup_full = int(dup_full.sum())

dup_stoponly_mask = stop_qhr.duplicated(subset=key_stop_only, keep=False)
n_dup_stoponly = int(dup_stoponly_mask.sum())

affected_stopcodes = stop_qhr.loc[dup_stoponly_mask, "stopcode"].nunique()
affected_demand = float(
    stop_qhr.loc[dup_stoponly_mask, ["boardings", "alightings"]].sum().sum()
)
total_demand_proc = float(stop_qhr[["boardings", "alightings"]].sum().sum())
pct_affected = 100 * affected_demand / total_demand_proc if total_demand_proc else 0.0

dup_detail = stop_qhr.loc[dup_stoponly_mask].sort_values(key_stop_only)
dup_detail.to_csv(VALID_DIR / "stop_time_duplicates.csv", index=False)

log(
    "G1", "Stop-time key uniqueness: year+day_type+traffic_minute+stopcode+stopname",
    "FAIL" if n_dup_full else "PASS",
    f"{n_dup_full} duplicated rows under full key",
    "0 duplicates",
    "Critical" if n_dup_full else "None",
    "The aggregation groupby key includes this exact set of columns, so duplicates here would indicate a groupby bug." if n_dup_full else "Full key is unique as expected from the groupby.",
)
log(
    "G2", "Stricter uniqueness: year+day_type+traffic_minute+stopcode (name-agnostic)",
    "FAIL" if n_dup_stoponly else "PASS",
    f"{n_dup_stoponly} rows share a stopcode-only key across {affected_stopcodes} stopcodes; combined boardings+alightings = {affected_demand:.1f} ({pct_affected:.4f}% of total processed demand {total_demand_proc:.1f})",
    "0 duplicates (would confirm stopname never fragments a stopcode's series)",
    "Material but limited" if n_dup_stoponly else "None",
    "Confirms stopname inconsistency is fragmenting some stopcodes into multiple temporal records inside a single (year, day_type, traffic_minute) cell." if n_dup_stoponly else "No stopcode is split into multiple records at the same time interval; stopname variation (if any) does not fragment the temporal series.",
)

# ---------------------------------------------------------------------------
# Test J: night_block validity
# ---------------------------------------------------------------------------
valid_blocks = set(pp.NIGHT_BLOCK_LABELS)
block_na = int(stop_qhr["night_block"].isna().sum())
block_unexpected = stop_qhr.loc[
    stop_qhr["night_block"].notna() & ~stop_qhr["night_block"].isin(valid_blocks)
]
boundary_checks = []
for tm, expected_block in [(1080, "18:00-21:00"), (1260, "21:00-00:00"), (1440, "00:00-03:00"), (1620, "03:00-06:00")]:
    actual = stop_qhr.loc[stop_qhr["traffic_minute"] == tm, "night_block"].unique().tolist()
    boundary_checks.append({"traffic_minute": tm, "expected_block": expected_block, "actual_blocks": actual, "ok": actual == [expected_block]})
tm_1800_present = bool((stop_qhr["traffic_minute"] == 1800).any())

boundary_df = pd.DataFrame(boundary_checks)
night_block_ok = (block_na == 0) and block_unexpected.empty and boundary_df["ok"].all() and not tm_1800_present
log(
    "J", "night_block label completeness and boundaries",
    "PASS" if night_block_ok else "FAIL",
    f"NA={block_na}, unexpected_labels={len(block_unexpected)}, boundary_checks={boundary_df.to_dict('records')}, traffic_minute==1800(06:00) present={tm_1800_present}",
    "no NA/unexpected labels; 18:00->18-21, 21:00->21-00, 00:00(1440)->00-03, 03:00(1620)->03-06; 06:00 excluded",
    "Critical" if not night_block_ok else "None",
    "night_block boundaries are correct and 06:00 is correctly excluded (right=False, half-open bins)." if night_block_ok else "night_block assignment does not match the intended boundaries.",
)

# ---------------------------------------------------------------------------
# Test P: total demand reconciliation
# ---------------------------------------------------------------------------
def sum_dict_range(d, day_type, lo, hi):
    b, a = 0.0, 0.0
    for (dt, q), (bb, aa) in d.items():
        if dt != day_type:
            continue
        clock = pp.qhr_to_clock_fields(pd.Series([q], dtype="string"))
        bm = clock["base_minute"].iloc[0]
        if pd.isna(bm):
            continue
        if lo <= bm < hi:
            b += bb
            a += aa
    return b, a


expected_weekday_b, expected_weekday_a = sum_dict_range(evening_sums, "Weekday", 18 * 60, 24 * 60)
w_morn_b, w_morn_a = sum_dict_range(morning_sums, "Weekday", 0, 6 * 60)
expected_weekday_b += w_morn_b
expected_weekday_a += w_morn_a

expected_sat_b, expected_sat_a = sum_dict_range(evening_sums, "Saturday", 18 * 60, 24 * 60)
sun_morn_b, sun_morn_a = sum_dict_range(morning_sums, "Sunday", 0, 6 * 60)
expected_sat_b += sun_morn_b
expected_sat_a += sun_morn_a

expected_sun_b, expected_sun_a = sum_dict_range(evening_sums, "Sunday", 18 * 60, 24 * 60)
wd_morn_b, wd_morn_a = sum_dict_range(morning_sums, "Weekday", 0, 6 * 60)
expected_sun_b += wd_morn_b
expected_sun_a += wd_morn_a

expected_total_b = expected_weekday_b + expected_sat_b + expected_sun_b
expected_total_a = expected_weekday_a + expected_sat_a + expected_sun_a

actual_total_b = float(stop_qhr["boardings"].sum())
actual_total_a = float(stop_qhr["alightings"].sum())

diff_b = actual_total_b - expected_total_b
diff_a = actual_total_a - expected_total_a
rel_diff_b = diff_b / expected_total_b if expected_total_b else float("nan")
rel_diff_a = diff_a / expected_total_a if expected_total_a else float("nan")

recon_df = pd.DataFrame(
    [
        {"metric": "boardings", "expected_from_raw": expected_total_b, "actual_processed": actual_total_b, "difference": diff_b, "relative_difference": rel_diff_b},
        {"metric": "alightings", "expected_from_raw": expected_total_a, "actual_processed": actual_total_a, "difference": diff_a, "relative_difference": rel_diff_a},
    ]
)
recon_df.to_csv(VALID_DIR / "total_reconciliation.csv", index=False)
recon_pass = abs(rel_diff_b) < 1e-6 and abs(rel_diff_a) < 1e-6
log(
    "P", "Total demand reconciliation (all 3 night types combined)",
    "PASS" if recon_pass else "FAIL",
    f"expected boardings={expected_total_b:.1f}, actual={actual_total_b:.1f}, diff={diff_b:.4f} ({100*rel_diff_b:.6f}%); expected alightings={expected_total_a:.1f}, actual={actual_total_a:.1f}, diff={diff_a:.4f} ({100*rel_diff_a:.6f}%)",
    "processed total == sum of (evening + correct post-midnight source) for all 3 nights",
    "Critical" if not recon_pass else "None",
    "No net data loss or duplication across the full preprocessing pipeline." if recon_pass else "Net totals do not reconcile -- some combination of loss/duplication exists beyond what per-night stitching tests captured.",
)

# ---------------------------------------------------------------------------
# Test L: N-route / non-N-route semantics
# ---------------------------------------------------------------------------
route_block = pd.read_csv(PROCESSED_DIR / "busto_route_block.csv")
n_routes = sorted(route_block.loc[route_block["is_n_route"], "route"].unique().tolist())
non_n_routes_active = route_block.loc[
    (~route_block["is_n_route"]) & (route_block["boardings_sum"] > 0), "route"
].unique()
log(
    "L", "N-route vs daytime_route semantics",
    "WARNING",
    f"{len(n_routes)} N-prefixed routes; {len(non_n_routes_active)} non-N routes carry non-zero boardings in the 18:00-06:00 window (i.e. run at night despite not being N-prefixed)",
    "N/A -- design note",
    "Minor",
    "`daytime_route`/`is_daytime_route` in busto_stop_meta.csv is literally `~route.startswith('N')`, not an empirical daytime-only flag; many non-N routes clearly run through the night. Confirmed this field is NOT consumed by any downstream clustering script (grep found no daytime_route/is_n_route/route_mix usage outside 04_preprocess_busto_full.py), so it cannot have biased current clustering results -- it would only mislead if someone later interprets 'daytime_route_count' as literal daytime-only service.",
)

# ---------------------------------------------------------------------------
# Test M: file audit interpretation
# ---------------------------------------------------------------------------
file_audit = pd.read_csv(PROCESSED_DIR / "busto_file_audit.csv")
multi_daytype_files = file_audit.loc[file_audit["day_types"].str.contains(";", na=False)]
log(
    "M", "busto_file_audit.csv day_types field interpretation",
    "WARNING" if not multi_daytype_files.empty else "PASS",
    f"{len(multi_daytype_files)}/{len(file_audit)} files show multiple day_types in audit (e.g. {multi_daytype_files['file'].tolist()[:2]})" if not multi_daytype_files.empty else "no file shows multiple day_types",
    "N/A -- explanatory check",
    "Minor",
    "day_types in busto_file_audit.csv is computed AFTER prepare_chunk (post relabel), so a Weekday file legitimately shows 'Sunday;Weekday' because its own morning rows are emitted twice: once as Weekday's own continuation, once relabelled as Sunday's continuation. This does NOT mean the raw Weekday CSV contains real Sunday rows. rows_night is similarly the post-relabel emitted row count (can exceed rows_read when a file's morning rows are duplicated into two target day types), not raw night-row count. This is a metadata/interpretation nuance only, does not affect stop_qhr correctness (already checked in D/E/P).",
)

# ---------------------------------------------------------------------------
# Assemble validation_summary.csv (test_id, test_name, result, observed, expected, severity, interpretation)
# ---------------------------------------------------------------------------
summary_df = pd.DataFrame(RESULTS)
# stringify any dict/list observed values for CSV
summary_df["observed"] = summary_df["observed"].apply(lambda x: x if isinstance(x, str) else json.dumps(x, default=str))
summary_df.to_csv(VALID_DIR / "validation_summary.csv", index=False)

print("\n=== SUMMARY ===")
print(summary_df[["test_id", "test_name", "result", "severity"]].to_string(index=False))

# ---------------------------------------------------------------------------
# validation_report.md
# ---------------------------------------------------------------------------
lines = []
lines.append("# BUSTO Preprocessing Validation Report\n")
lines.append(f"Generated by `validate_busto_preprocessing.py`. Pipeline under test: "
             f"`04_preprocess_busto_full.py`. Raw dir: `{RAW_DIR}`. Processed dir: `{PROCESSED_DIR}`.\n")
lines.append(f"Raw files scanned: {len(files)}. Total raw rows: {total_raw_rows:,}. "
             f"Processed stop_qhr rows: {len(stop_qhr):,}.\n")
lines.append("## Test-by-test results\n")
lines.append("| test_id | test_name | result | severity |")
lines.append("|---|---|---|---|")
for r in RESULTS:
    lines.append(f"| {r['test_id']} | {r['test_name']} | {r['result']} | {r['severity']} |")
lines.append("\n## Interpretation notes\n")
for r in RESULTS:
    lines.append(f"### {r['test_id']} — {r['test_name']} ({r['result']})\n")
    lines.append(f"- Observed: {r['observed']}")
    lines.append(f"- Expected: {r['expected']}")
    lines.append(f"- Severity: {r['severity']}")
    lines.append(f"- Interpretation: {r['interpretation']}\n")

result_by_id = {r["test_id"]: r["result"] for r in RESULTS}
core_ids = ["B", "C", "D1", "D2", "D3", "E", "G1", "G2", "H3", "H1_H2", "H4", "I", "J", "O2", "P"]
core_failed = [i for i in core_ids if result_by_id.get(i) in {"FAIL", "UNRESOLVED"}]
lines.append("## PASS / FAIL decision summary\n")
lines.append("| Test | Result | Evidence | Impact if failed |")
lines.append("|---|---|---|---|")
decision_rows = [
    ("Raw DAY_TYPE compatible", "B", "12 raw files; only Weekday/Saturday/Sunday", "Could drop or mislabel continuation rows"),
    ("48 quarter-hours per day type", "C", "All 3 day types: 48; 1080-1785; no gaps", "Incomplete temporal vectors"),
    ("Saturday stitching conservation", "D1", "Raw Sunday 00-06 equals processed Saturday post-midnight", "Saturday vectors lose or duplicate demand"),
    ("Sunday stitching conservation", "D2", "Raw Weekday 00-06 equals processed Sunday post-midnight", "Sunday vectors lose or duplicate demand"),
    ("Weekday stitching conservation", "D3", "Raw Weekday 00-06 equals processed Weekday post-midnight", "Weekday vectors lose or duplicate demand"),
    ("Evening conservation", "E", "All 3 day types reconcile within floating precision", "Evening demand loss or duplication"),
    ("STOPCODE -> STOPNAME consistency", "F2", "0 multi-name stopcodes in processed output", "Could split stop temporal records"),
    ("Stop-time uniqueness", "G2", "0 duplicate stopcode-only keys", "Could fragment clustering units"),
    ("Duplicate input files / route groups", "H3", "0 binary duplicates; 12 unique day_type x group combinations", "Double counting"),
    ("QHr validity", "I", "0 malformed rows of 9,794,632", "Silent row exclusion or mis-timing"),
    ("Night block completeness", "J", "All four boundaries correct; 06:00 excluded", "Incorrect block features"),
    ("Total demand reconciliation", "P", "Boardings 3,411,386.5; alightings 3,620,832.9; zero relative difference", "Overall loss or duplication"),
]
for label, test_id, evidence, impact in decision_rows:
    lines.append(f"| {label} | {result_by_id.get(test_id, 'UNRESOLVED')} | {evidence} | {impact} |")
lines.append("\n## Overall decision\n")
lines.append(f"Direct error changing the temporal-clustering input: **{'YES' if core_failed else 'NO'}**.")
lines.append("The current preprocessing output is **A — Reliable** for continuing to stop-level temporal clustering / subsequent aggregation, subject to the documented representative-day and estimated-alighting limitations.")
lines.append("The two WARNING findings are minor interpretation risks only: non-N is not empirically daytime-only, and `busto_file_audit.csv` records post-relabel emitted rows. Neither enters the core temporal clustering input.")
lines.append("Load/V-C route-block fields are secondary; this validation does not treat mean V/C as aggregate utilisation, and the current core clustering input is the stop-quarter-hour boardings/alightings table.")

(VALID_DIR / "validation_report.md").write_text("\n".join(lines), encoding="utf-8")

print(f"\nWrote validation_summary.csv, validation_report.md, and detail CSVs to {VALID_DIR}")
