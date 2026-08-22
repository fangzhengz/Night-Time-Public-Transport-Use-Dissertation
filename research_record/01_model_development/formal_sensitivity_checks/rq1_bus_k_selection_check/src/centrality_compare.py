# -*- coding: utf-8 -*-
"""Distance-to-centre profile of each cluster, adopted versus best-likelihood.

The side-by-side map suggests the best-likelihood solution gives the two
low-flow clusters a cleaner concentric split: much of the adopted C0's outer
London membership moves to C3. This quantifies that instead of leaving it to the
eye, using straight-line distance from Charing Cross to each LSOA centroid.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]
SRC = FYP / "rq1_bus_stoparea_clustering"
sys.path.insert(0, str(SRC / "src"))
import config as C  # noqa: E402

OUT = ROOT / "outputs"

# Charing Cross, the conventional centre point for London distance measures.
CENTRE_LON, CENTRE_LAT = -0.1281, 51.5074
BRITISH_NATIONAL_GRID = 27700


def main() -> None:
    boundaries = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(columns={code_column: "lsoa"})
    boundaries = boundaries.to_crs(BRITISH_NATIONAL_GRID)

    centre = (
        gpd.GeoSeries.from_xy([CENTRE_LON], [CENTRE_LAT], crs=4326)
        .to_crs(BRITISH_NATIONAL_GRID)
        .iloc[0]
    )
    boundaries["km_from_centre"] = boundaries.geometry.centroid.distance(centre) / 1000.0
    distance = boundaries.set_index("lsoa")["km_from_centre"]

    adopted = (
        pd.read_csv(SRC / "outputs" / "clr" / "labels" / "k4_labels.csv", dtype={"lsoa": str})
        .set_index("lsoa")
    )
    adopted = adopted.loc[adopted["cluster"] >= 0, "cluster"]
    best = (
        pd.read_csv(OUT / "best_k4_labels.csv", dtype={"lsoa": str})
        .set_index("lsoa")["cluster"]
    )

    rows: list[dict] = []
    for name, labels in [("adopted", adopted), ("best_likelihood", best)]:
        frame = pd.DataFrame({"cluster": labels})
        frame["km"] = distance.reindex(frame.index)
        missing = int(frame["km"].isna().sum())
        for cluster, sub in frame.dropna(subset=["km"]).groupby("cluster"):
            rows.append(
                {
                    "solution": name,
                    "cluster": int(cluster),
                    "n": int(len(sub)),
                    "km_mean": float(sub["km"].mean()),
                    "km_median": float(sub["km"].median()),
                    "km_p10": float(sub["km"].quantile(0.10)),
                    "km_p90": float(sub["km"].quantile(0.90)),
                    "share_beyond_15km": float((sub["km"] > 15).mean()),
                }
            )
        if missing:
            print(f"[{name}] {missing} LSOAs had no boundary match and were dropped")

    result = pd.DataFrame(rows).round(3)
    result.to_csv(OUT / "centrality_by_cluster.csv", index=False)
    print(result.to_string(index=False))

    # Overall separation: how much of the distance variance each solution explains.
    for name, labels in [("adopted", adopted), ("best_likelihood", best)]:
        values = distance.reindex(labels.index).dropna()
        groups = labels.reindex(values.index)
        grand = values.mean()
        total = float(((values - grand) ** 2).sum())
        between = sum(
            len(values[groups == cluster]) * (values[groups == cluster].mean() - grand) ** 2
            for cluster in sorted(groups.unique())
        )
        print(f"{name}: distance-to-centre eta^2 = {between / total:.4f}")


if __name__ == "__main__":
    main()
