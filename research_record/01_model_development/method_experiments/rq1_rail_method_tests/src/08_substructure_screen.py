# -*- coding: utf-8 -*-
"""Uniform second-stage screen of EVERY level-one cluster, with characterisation.

Answers the "why did you split that cluster and not the others" objection by
not making a choice: every level-one cluster large enough to split is screened
under one protocol, and all results are reported whether or not they are
convenient.

PROTOCOL (fixed in advance, applied identically to every cluster)
  eligible      parent n >= MIN_PARENT_N
  sub-K         each of SUB_KS
  fitting       diag covariance, n_init=100, matching the level-one settings
  stability     mean pairwise ARI between the 10 seed fits
  reported      a split is called reproducible at STABILITY_THRESHOLD
  membership    cross-seed consensus, not a single fit

Characterisation uses external metrics that took no part in the fitting
(direction balance, Night-Tube extension, activity, distance to centre), so a
split's substantive meaning is assessed independently of what produced it.

This script only DESCRIBES. It deliberately emits no adopted label file --
whether the second level becomes an analytical variable is a separate decision.
"""
from __future__ import annotations

import json
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

warnings.filterwarnings("ignore", category=ConvergenceWarning)

MIN_PARENT_N = 25
SUB_KS = [2, 3]
N_INIT = 100
SEEDS = [42, 7, 123, 2026, 999, 55, 808, 1234, 31337, 64]
STABILITY_THRESHOLD = 0.90
CENTRE = (530034.0, 180381.0)
OUT = C.OUT / "substructure_screen"
OUT.mkdir(parents=True, exist_ok=True)

EXTERNAL = {
    "dir_balance": "direction_balance",
    "nt_extension": "night_tube_extension_share",
    "weekend": "weekend_common_ratio",
    "log_activity": "log_total_activity",
}


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = y.mean()
    total = float(((y - grand) ** 2).sum())
    if total <= 0:
        return float("nan")
    return float(
        sum(int((labels == c).sum()) * (y[labels == c].mean() - grand) ** 2
            for c in np.unique(labels)) / total
    )


def fit(X, k, seed):
    return GaussianMixture(
        k, covariance_type=C.PRIMARY_COVARIANCE, n_init=N_INIT,
        reg_covar=C.REG_COVAR, max_iter=C.MAX_ITER, random_state=seed,
    ).fit(X)


def consensus(X, members, k):
    """Co-assignment consensus across seeds, then a single representative fit.

    The representative fit is the seed whose partition best agrees with all the
    others (highest mean ARI to the rest) -- a medoid, so the reported roster is
    an actual partition rather than an average that might not be realisable.
    """
    labels = [pd.Series(fit(X, k, s).predict(X), index=members) for s in SEEDS]
    aris = np.zeros((len(SEEDS), len(SEEDS)))
    for i, j in combinations(range(len(SEEDS)), 2):
        value = adjusted_rand_score(labels[i], labels[j])
        aris[i, j] = aris[j, i] = value
    mean_pairwise = float(aris[np.triu_indices(len(SEEDS), 1)].mean())
    medoid = int(np.argmax(aris.sum(axis=1)))
    return labels[medoid], mean_pairwise


def main() -> None:
    X_frame = pd.read_parquet(C.FEATURES / "X_fullweek_unpadded.parquet")
    X_frame.index = X_frame.index.astype(str)
    canon = pd.read_csv(C.CANON_K5_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    metrics = pd.read_csv(C.RAIL_UNIT_METRICS, dtype={"NLC": str}).set_index("NLC")
    coords = pd.read_csv(
        C.FYP / "data_processing" / "rail_allmodes" / "outputs" / "data"
        / "rail_allmodes_coords.csv", dtype={"unit": str},
    ).set_index("unit")
    km = pd.Series(
        np.hypot(coords["easting"] - CENTRE[0], coords["northing"] - CENTRE[1]) / 1000.0,
        index=coords.index,
    )

    screen_rows, roster_rows = [], []
    for parent in sorted(canon.unique()):
        members = [u for u in X_frame.index if canon.get(u) == parent]
        if len(members) < MIN_PARENT_N:
            screen_rows.append(
                {"parent": f"C{parent}", "parent_n": len(members), "sub_k": None,
                 "seed_ari_mean": np.nan, "reproducible": False,
                 "note": f"below the n>={MIN_PARENT_N} size rule"}
            )
            print(f"C{parent} (n={len(members)}): below size rule, not split")
            continue
        X = X_frame.loc[members].to_numpy(dtype=float)
        for k in SUB_KS:
            labels, stability = consensus(X, members, k)
            row = {
                "parent": f"C{parent}", "parent_n": len(members), "sub_k": k,
                "seed_ari_mean": stability,
                "reproducible": stability >= STABILITY_THRESHOLD, "note": "",
            }
            for short, column in EXTERNAL.items():
                row[f"eta2_{short}"] = eta_squared(
                    metrics[column].reindex(members), labels.to_numpy()
                )
            row["eta2_km_to_centre"] = eta_squared(km.reindex(members), labels.to_numpy())
            screen_rows.append(row)

            if row["reproducible"]:
                print(f"\n=== C{parent} (n={len(members)}) split at sub-K={k} "
                      f"— seed ARI {stability:.3f} ===")
                for sub in sorted(labels.unique()):
                    part = labels.index[labels == sub]
                    ordered = sorted(part, key=lambda u: -metrics["total_activity"].get(u, 0))
                    entry = {
                        "parent": f"C{parent}", "sub_k": k, "sub": int(sub), "n": len(part),
                        "dir_balance": metrics["direction_balance"].reindex(part).mean(),
                        "nt_extension": metrics["night_tube_extension_share"].reindex(part).mean(),
                        "weekend": metrics["weekend_common_ratio"].reindex(part).mean(),
                        "median_activity": metrics["total_activity"].reindex(part).median(),
                        "km_to_centre": km.reindex(part).mean(),
                        "pct_LU": 100 * coords["is_lu"].reindex(part).mean(),
                        "top_stations": ", ".join(
                            str(coords["Station"].get(u, u)) for u in ordered[:5]
                        ),
                    }
                    roster_rows.append(entry)
                    print(
                        f"  sub{sub}  n={len(part):3d}  dir_bal={entry['dir_balance']:+.3f}  "
                        f"nt_ext={entry['nt_extension']:.3f}  wknd={entry['weekend']:.3f}  "
                        f"med_act={entry['median_activity']:>9,.0f}  km={entry['km_to_centre']:5.1f}  "
                        f"LU={entry['pct_LU']:5.1f}%"
                    )
                    print(f"        {entry['top_stations']}")

    screen = pd.DataFrame(screen_rows)
    screen.to_csv(OUT / "screen_table.csv", index=False)
    pd.DataFrame(roster_rows).to_csv(OUT / "subcluster_rosters.csv", index=False)
    (OUT / "protocol.json").write_text(
        json.dumps(
            {"min_parent_n": MIN_PARENT_N, "sub_ks": SUB_KS, "n_init": N_INIT,
             "seeds": SEEDS, "stability_threshold": STABILITY_THRESHOLD,
             "covariance": C.PRIMARY_COVARIANCE,
             "level_one_source": str(C.CANON_K5_LABELS)},
            indent=2,
        ),
        encoding="utf-8",
    )
    print("\n=== screen table ===")
    print(screen.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("\nSaved to", OUT)


if __name__ == "__main__":
    main()
