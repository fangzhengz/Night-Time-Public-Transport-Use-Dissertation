# -*- coding: utf-8 -*-
"""Build the four day-type-closure feature matrices (B1-B4).

Every matrix is 72 columns, ordered identically to the canonical
`X_bus_stoparea_*_min36.parquet` files (direction-major, then day type, then
hour), so a column-by-column comparison against the canonical run is a plain
join. The ONLY difference is the denominator:

    canonical   x[i, d, t, h] = c / sum over (t, h) within direction d
    here        x[i, d, t, h] = c / sum over (h)     within (direction d, day t)
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


def columns_for(direction: str, day_type: str) -> list[str]:
    return [f"{direction}_{day_type}_{hour}" for hour in C.HOURS]


def build_raw_counts(long: pd.DataFrame, keep: pd.Index) -> pd.DataFrame:
    """72-column raw count matrix, canonical column order."""
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        for day_type in C.DAY_TYPES:
            sub = long[(long["direction"] == direction) & (long["day_type"] == day_type)]
            wide = sub.pivot_table(
                index="lsoa", columns="hour_bin", values="count",
                aggfunc="sum", fill_value=0.0,
            )
            wide = wide.reindex(index=keep, columns=C.HOURS, fill_value=0.0).astype(float)
            wide.columns = columns_for(direction, day_type)
            blocks.append(wide)
    raw = pd.concat(blocks, axis=1)
    raw.index = pd.Index(raw.index.astype(str), name="lsoa")
    if raw.shape[1] != 72:
        raise RuntimeError(f"Unexpected raw-count width: {raw.shape}")
    return raw


def block_totals(raw_counts: pd.DataFrame) -> pd.DataFrame:
    """Per-(direction, day_type) totals -- the new denominators."""
    data = {}
    for direction in C.DIRECTIONS:
        for day_type in C.DAY_TYPES:
            data[f"{direction}_{day_type}"] = raw_counts[
                columns_for(direction, day_type)
            ].sum(axis=1)
    return pd.DataFrame(data, index=raw_counts.index)


def build_daytype_raw_share(raw_counts: pd.DataFrame) -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        for day_type in C.DAY_TYPES:
            columns = columns_for(direction, day_type)
            counts = raw_counts[columns]
            totals = counts.sum(axis=1)
            if (totals <= 0).any():
                n = int((totals <= 0).sum())
                raise RuntimeError(
                    f"{n} rows have an empty {direction}/{day_type} block; day-type "
                    "closure is undefined for them. Tighten the retention rule."
                )
            blocks.append(counts.div(totals, axis=0))
    X = pd.concat(blocks, axis=1)
    for direction in C.DIRECTIONS:
        for day_type in C.DAY_TYPES:
            block_sum = X[columns_for(direction, day_type)].sum(axis=1)
            if not np.allclose(block_sum, 1.0, atol=1e-10):
                raise RuntimeError(f"{direction}/{day_type} block does not sum to one.")
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise RuntimeError("Day-type raw-share features contain non-finite values.")
    return X


def build_fullweek_raw_share(raw_counts: pd.DataFrame) -> pd.DataFrame:
    """Canonical closure: each direction over its own 36-cell week.

    Identical logic to `rq1_bus_stoparea_clustering/src/01_prepare_features.py::
    build_raw_share`, reimplemented here only so the strict sample can be run
    under it. On the base sample it reproduces the canonical matrix, which
    `main` asserts.
    """
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        columns = [c for c in raw_counts.columns if c.startswith(f"{direction}_")]
        counts = raw_counts[columns]
        totals = counts.sum(axis=1)
        if (totals <= 0).any():
            raise RuntimeError(f"Non-positive {direction} week total.")
        blocks.append(counts.div(totals, axis=0))
    X = pd.concat(blocks, axis=1)
    for direction in C.DIRECTIONS:
        columns = [c for c in X.columns if c.startswith(f"{direction}_")]
        if not np.allclose(X[columns].sum(axis=1), 1.0, atol=1e-10):
            raise RuntimeError(f"{direction} week block does not sum to one.")
    return X


def build_daytype_clr(raw_counts: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Block-wise CLR: the prior is estimated WITHIN each 12-cell block.

    Using the canonical whole-direction prior here would leak the very
    cross-day-type mass balance that day-type closure is meant to remove.
    """
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        for day_type in C.DAY_TYPES:
            columns = columns_for(direction, day_type)
            counts = raw_counts[columns].to_numpy(dtype=float)
            totals = counts.sum(axis=1)
            column_mass = counts.sum(axis=0)
            if column_mass.sum() <= 0:
                raise RuntimeError(f"{direction}/{day_type} block is globally empty.")
            prior = column_mass / column_mass.sum()
            posterior = (counts + alpha * prior) / (totals[:, None] + alpha)
            if not np.all(posterior > 0):
                raise RuntimeError(f"Non-positive posterior in {direction}/{day_type}.")
            log_share = np.log(posterior)
            clr = log_share - log_share.mean(axis=1, keepdims=True)
            if not np.allclose(clr.sum(axis=1), 0.0, atol=1e-8):
                raise RuntimeError(f"{direction}/{day_type} CLR does not sum to zero.")
            blocks.append(pd.DataFrame(clr, index=raw_counts.index, columns=columns))
    X = pd.concat(blocks, axis=1)
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise RuntimeError("Day-type CLR features contain non-finite values.")
    return X


def zero_bin_share(raw_counts: pd.DataFrame) -> pd.Series:
    """Fraction of the 72 raw cells that are exactly zero.

    The diagnostic behind the 2026-07-23 finding that canonical CLR clusters
    were mostly service-continuity tiers rather than shape types. Defined on
    RAW COUNTS, so it is identical across variants on a shared sample and can
    be compared between them without qualification.
    """
    return (raw_counts == 0).sum(axis=1) / raw_counts.shape[1]


def main() -> None:
    long = pd.read_parquet(C.LONG_INPUT)
    long["lsoa"] = long["lsoa"].astype(str)
    long["direction"] = long["direction"].astype(str)
    long["day_type"] = long["day_type"].astype(str)
    long["hour_bin"] = long["hour_bin"].astype(int)

    metrics = pd.read_csv(C.SAMPLE_METRICS, dtype={"lsoa": str}).set_index("lsoa")
    base_keep = pd.Index(
        metrics.index[metrics["retained_for_fit"].astype(bool)], name="lsoa"
    )

    raw_counts = build_raw_counts(long, base_keep)
    totals = block_totals(raw_counts)
    zeros = zero_bin_share(raw_counts)

    # The strict sample: every one of the six blocks must clear the threshold.
    strict_mask = (totals >= C.STRICT_MIN_BLOCK).all(axis=1)
    strict_keep = raw_counts.index[strict_mask]

    audit = {
        "input_long": str(C.LONG_INPUT),
        "input_long_sha256": sha256(C.LONG_INPUT),
        "sample_metrics_sha256": sha256(C.SAMPLE_METRICS),
        "n_base_sample": int(len(base_keep)),
        "n_strict_sample": int(len(strict_keep)),
        "strict_dropped": int(len(base_keep) - len(strict_keep)),
        "block_count_median": float(totals.stack().median()),
        "block_count_p05": float(totals.stack().quantile(0.05)),
        "blocks_below_36_share": float((totals.stack() < 36).mean()),
        "blocks_below_20_share": float((totals.stack() < 20).mean()),
        "zero_bin_share_mean": float(zeros.mean()),
        "python": sys.version,
        "platform": platform.platform(),
    }

    raw_counts.to_parquet(C.FEATURES / "raw_counts_min36.parquet")
    totals.to_csv(C.FEATURES / "block_totals.csv")
    zeros.rename("zero_bin_share").to_csv(C.FEATURES / "zero_bin_share.csv")

    for name, spec in C.VARIANTS.items():
        index = strict_keep if spec["strict"] else base_keep
        counts = raw_counts.loc[index]
        closure = spec.get("closure", "daytype")
        if closure == "fullweek":
            X = build_fullweek_raw_share(counts)
        elif spec["kind"] == "raw_share":
            X = build_daytype_raw_share(counts)
        else:
            X = build_daytype_clr(counts, float(spec["alpha"]))
        if list(X.columns) != list(raw_counts.columns):
            raise RuntimeError(f"{name}: column order drifted from the canonical order.")
        X.to_parquet(C.FEATURES / f"X_{name}.parquet")
        audit[f"{name}_shape"] = list(X.shape)
        print(f"{name:28s} {X.shape}  n={len(X):,}")

    # Anchor: full-week closure on the BASE sample must reproduce the adopted
    # raw_share matrix. B5 is only interpretable if this builder agrees with the
    # canonical one, so the run fails rather than quietly producing a
    # comparison against a re-implementation that has drifted.
    canonical_path = (
        C.CANONICAL / "outputs" / "features" / "X_bus_stoparea_raw_share_min36.parquet"
    )
    if canonical_path.exists():
        mine = build_fullweek_raw_share(raw_counts.loc[base_keep])
        canon = pd.read_parquet(canonical_path)
        canon.index = pd.Index(canon.index.astype(str), name="lsoa")
        if set(mine.index) != set(canon.index) or set(mine.columns) != set(canon.columns):
            raise RuntimeError("Full-week anchor: index or column sets differ from canonical.")
        max_abs = float((mine - canon.loc[mine.index, mine.columns]).abs().to_numpy().max())
        audit["fullweek_anchor_max_abs_diff_vs_canonical"] = max_abs
        if max_abs > 1e-9:
            raise RuntimeError(
                f"Full-week closure does not reproduce the adopted matrix "
                f"(max abs diff {max_abs:.3e}); B5 would not be comparable."
            )
        print(f"full-week anchor PASSED: max abs diff vs canonical = {max_abs:.3e}")
    else:
        audit["fullweek_anchor_max_abs_diff_vs_canonical"] = None
        print("WARNING: canonical raw_share matrix not found; anchor check skipped.")

    (C.FEATURES / "feature_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    print()
    print(f"base sample   n={len(base_keep):,}")
    print(f"strict sample n={len(strict_keep):,}  (dropped {len(base_keep)-len(strict_keep):,})")
    print(f"blocks < 36 counts: {audit['blocks_below_36_share']:.2%}")
    print("Saved:", C.FEATURES / "feature_audit.json")


if __name__ == "__main__":
    main()
