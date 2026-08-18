# -*- coding: utf-8 -*-
"""Build the 2x2 rail feature matrices (closure x window).

`fullweek_unpadded` must reproduce the adopted `X_rail_allmodes.parquet`. That
is asserted here, not assumed: if this builder and the canonical builder ever
disagree, every comparison downstream is meaningless, so the run fails loudly
instead of quietly producing a plausible table.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def day_bins(windows: dict, day: str) -> list[int]:
    low, high = windows[day]
    return list(range(low, high, C.QUARTER))


def build_raw_counts(raw: pd.DataFrame, windows: dict) -> pd.DataFrame:
    """Direction-major, then day, then minute -- the canonical column order."""
    units = sorted(raw["NLC"].unique())
    blocks: list[pd.DataFrame] = []
    for direction in C.RAIL_DIRECTIONS:
        for day in C.RAIL_DAYS:
            bins = day_bins(windows, day)
            sub = raw[
                (raw["day_type"] == day)
                & (raw["direction"] == direction)
                & (raw["extended_minute"] >= bins[0])
                & (raw["extended_minute"] <= bins[-1])
            ]
            wide = sub.pivot_table(
                index="NLC", columns="extended_minute", values="count",
                aggfunc="sum", fill_value=0.0,
            )
            wide = wide.reindex(index=units, columns=bins, fill_value=0.0).astype(float)
            wide.columns = [f"{direction}_{day}_{minute}" for minute in bins]
            blocks.append(wide)
    counts = pd.concat(blocks, axis=1)
    counts.index = pd.Index(counts.index.astype(str), name="NLC")
    return counts


def close_fullweek(counts: pd.DataFrame) -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    for direction in C.RAIL_DIRECTIONS:
        columns = [c for c in counts.columns if c.startswith(f"{direction}_")]
        block = counts[columns]
        totals = block.sum(axis=1)
        blocks.append(block.div(totals.replace(0, np.nan), axis=0).fillna(0.0))
    return pd.concat(blocks, axis=1)


def close_daytype(counts: pd.DataFrame) -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    for direction in C.RAIL_DIRECTIONS:
        for day in C.RAIL_DAYS:
            columns = [c for c in counts.columns if c.startswith(f"{direction}_{day}_")]
            block = counts[columns]
            totals = block.sum(axis=1)
            if (totals <= 0).any():
                n = int((totals <= 0).sum())
                raise RuntimeError(
                    f"{n} stations have an empty {direction}/{day} block; day-type "
                    "closure is undefined for them."
                )
            blocks.append(block.div(totals, axis=0))
    return pd.concat(blocks, axis=1)


def main() -> None:
    raw = pd.read_parquet(C.RAW_LONG)
    raw["NLC"] = raw["NLC"].astype(str)
    raw["day_type"] = raw["day_type"].astype(str)
    raw["direction"] = raw["direction"].astype(str)

    # Retention uses the NATIVE window, exactly as the adopted run does, so the
    # station population is identical across all four cells.
    native_counts = build_raw_counts(raw, C.NATIVE_WINDOWS)
    keep = native_counts.index[native_counts.sum(axis=1) >= C.MIN_TOTAL]
    print(f"stations retained: {len(keep)} of {len(native_counts)}")

    counts_by_window = {
        False: native_counts.loc[keep],
        True: build_raw_counts(raw, C.PADDED_WINDOWS).loc[keep],
    }

    audit = {
        "raw_long_sha256": sha256(C.RAW_LONG),
        "n_stations": int(len(keep)),
        "python": sys.version,
        "platform": platform.platform(),
    }

    for name, spec in C.VARIANTS.items():
        counts = counts_by_window[spec["padded"]]
        closer = close_fullweek if spec["closure"] == "fullweek" else close_daytype
        X = closer(counts)
        if not np.isfinite(X.to_numpy(dtype=float)).all():
            raise RuntimeError(f"{name}: non-finite features.")
        X.to_parquet(C.FEATURES / f"X_{name}.parquet")
        audit[f"{name}_shape"] = list(X.shape)
        print(f"{name:20s} {X.shape}")

    # --- anchor check against the adopted matrix ---------------------------
    mine = pd.read_parquet(C.FEATURES / "X_fullweek_unpadded.parquet")
    canon = pd.read_parquet(C.CANON_X)
    canon.index = pd.Index(canon.index.astype(str), name="NLC")
    if set(mine.index) != set(canon.index):
        raise RuntimeError(
            f"Station sets differ: mine={len(mine)}, canonical={len(canon)}"
        )
    if set(mine.columns) != set(canon.columns):
        raise RuntimeError("Column sets differ from the adopted matrix.")
    aligned = canon.loc[mine.index, mine.columns]
    max_abs = float((mine - aligned).abs().to_numpy().max())
    audit["fullweek_unpadded_max_abs_diff_vs_canonical"] = max_abs
    if max_abs > 1e-9:
        raise RuntimeError(
            f"fullweek_unpadded does not reproduce the adopted matrix "
            f"(max abs diff {max_abs:.3e}); the 2x2 is not anchored."
        )
    print(f"\nanchor check PASSED: max abs diff vs adopted X = {max_abs:.3e}")

    # Rail has effectively no exact zeros (NUMBAT is a modelled dataset), so
    # the bus sidecar's zero_bin diagnostic is recorded but expected to be inert.
    zero_share = (counts_by_window[True] == 0).sum(axis=1) / counts_by_window[True].shape[1]
    zero_share.rename("zero_bin_share").to_csv(C.FEATURES / "zero_bin_share.csv")
    audit["zero_bin_share_mean"] = float(zero_share.mean())
    audit["zero_bin_share_max"] = float(zero_share.max())
    print(f"zero-cell share (padded): mean={zero_share.mean():.4f}, max={zero_share.max():.4f}")

    (C.FEATURES / "feature_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    print("Saved:", C.FEATURES / "feature_audit.json")


if __name__ == "__main__":
    main()
