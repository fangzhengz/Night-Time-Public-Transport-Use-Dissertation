# -*- coding: utf-8 -*-
"""Summarise posterior membership confidence for the canonical rail all-modes K=5 solution.

03_cluster_allmodes.py already calls predict_proba() and saves max_posterior /
entropy per station (see rail_allmodes_k5_labels.csv). Those columns were never
summarised or written up. This script adds nothing new to the model -- it only
reports the assignment-confidence diagnostic the pipeline already computed.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
K = 5
LABELS = ROOT / "outputs" / "data" / f"rail_allmodes_k{K}_labels.csv"
OUT = ROOT / "outputs" / "data" / "posterior_membership_summary.csv"
OUT_BY_CLUSTER = ROOT / "outputs" / "data" / "posterior_membership_by_cluster.csv"


def main() -> None:
    df = pd.read_csv(LABELS)
    max_posterior = df["max_posterior"]
    n = len(df)
    at_one = int((max_posterior >= 0.999999).sum())
    uncertain = max_posterior[max_posterior < 0.999999]

    thresholds = [0.999, 0.99, 0.95, 0.9]
    summary = {
        "K": K,
        "n": n,
        "share_at_1.0": at_one / n,
        **{f"share_ge_{t}": float((max_posterior >= t).mean()) for t in thresholds},
        "uncertain_n": int(len(uncertain)),
        "uncertain_share": len(uncertain) / n,
        "uncertain_min": float(uncertain.min()) if len(uncertain) else None,
        "uncertain_max": float(uncertain.max()) if len(uncertain) else None,
        "uncertain_median": float(uncertain.median()) if len(uncertain) else None,
        "overall_mean": float(max_posterior.mean()),
        "overall_min": float(max_posterior.min()),
    }
    pd.DataFrame([summary]).to_csv(OUT, index=False)
    print(f"Wrote {OUT}")

    by_cluster = df.groupby("cluster")["max_posterior"].agg(["count", "mean", "min"])
    by_cluster.to_csv(OUT_BY_CLUSTER)
    print(f"Wrote {OUT_BY_CLUSTER}")

    print(f"\nn = {n}")
    print(f"Share with max_posterior >= 0.999999 (effectively 1.0): {at_one} ({at_one/n*100:.1f}%)")
    for t in thresholds:
        print(f"Share with max_posterior >= {t}: {(max_posterior>=t).mean()*100:.1f}%")
    print(
        f"Remaining {len(uncertain)} stations ({len(uncertain)/n*100:.1f}%) range "
        f"{uncertain.min():.4f}-{uncertain.max():.4f} (median {uncertain.median():.4f})"
    )
    print()
    print(by_cluster)


if __name__ == "__main__":
    main()
