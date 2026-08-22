# -*- coding: utf-8 -*-
"""Cluster-map rendering, self-contained copy for bus_clr_test.

Deliberately duplicated rather than imported from
`rq1_bus_stoparea_clustering/src/map_style.py`: that folder's own upstream
paths broke once sibling analysis folders were archived
(rq1_bus_clr_transform hit exactly this on 2026-07-29), so this test does not
import code from any other analysis folder. All constants it needs are
defined here.

Three states, matching the StopArea test's map style:
1. clustered   -- in the fitted sample, carries a cluster colour
2. low flow    -- has night bus demand but below the retention rule
3. no stop     -- this table has zero rows for the LSOA at all
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.patches import Patch

CLUSTERED = "clustered"
LOW_FLOW = "low_flow_excluded"
NO_STOP = "no_stop_in_lsoa"

# Okabe-Ito colourblind-safe, no grey and no black (tab10's grey at index 7
# would be indistinguishable from the excluded-area grey at K=8).
CLUSTER_COLOURS = [
    "#0072B2", "#E69F00", "#009E73", "#CC79A7",
    "#56B4E9", "#D55E00", "#F0E442", "#785EF0",
]
LOW_FLOW_FACE = "#6e6e6e"
NO_STOP_FACE = "#ffffff"
NO_STOP_HATCH = "///"
NO_STOP_EDGE = "#000000"
NO_STOP_EDGE_WIDTH = 0.15
LOW_FLOW_LABEL = "Low night flow, excluded"
NO_STOP_LABEL = "No demand recorded for LSOA"


def cluster_colour(cluster: int) -> str:
    return CLUSTER_COLOURS[cluster % len(CLUSTER_COLOURS)]


def build_status_frame(boundaries, clustered_units, labels, all_input_units) -> pd.DataFrame:
    clustered_units = [str(unit) for unit in clustered_units]
    all_input = {str(unit) for unit in all_input_units}
    status = pd.DataFrame(
        {"lsoa": clustered_units, "status": CLUSTERED, "cluster": np.asarray(labels, dtype=int)}
    )
    low_flow = sorted(all_input - set(clustered_units))
    if low_flow:
        status = pd.concat(
            [status, pd.DataFrame({"lsoa": low_flow, "status": LOW_FLOW, "cluster": -1})],
            ignore_index=True,
        )
    mapped = boundaries.merge(status, on="lsoa", how="left")
    mapped["status"] = mapped["status"].fillna(NO_STOP)
    mapped["cluster"] = mapped["cluster"].fillna(-1).astype(int)
    return mapped


def draw_cluster_map(ax, mapped, k: int, legend: bool = True, legend_fontsize: int = 8):
    no_stop = mapped[mapped["status"] == NO_STOP]
    low_flow = mapped[mapped["status"] == LOW_FLOW]
    clustered = mapped[mapped["status"] == CLUSTERED]

    if not no_stop.empty:
        no_stop.plot(
            ax=ax, facecolor=NO_STOP_FACE, hatch=NO_STOP_HATCH,
            edgecolor=NO_STOP_EDGE, linewidth=NO_STOP_EDGE_WIDTH,
        )
    if not low_flow.empty:
        low_flow.plot(ax=ax, facecolor=LOW_FLOW_FACE, linewidth=0.0)

    sizes = clustered["cluster"].value_counts()
    total_clustered = int(sizes.sum())
    for cluster in range(k):
        subset = clustered[clustered["cluster"] == cluster]
        if subset.empty:
            continue
        subset.plot(ax=ax, facecolor=cluster_colour(cluster), linewidth=0.0)

    ax.set_axis_off()
    if not legend:
        return None

    handles = []
    for cluster in range(k):
        n = int(sizes.get(cluster, 0))
        share = n / total_clustered * 100 if total_clustered else 0.0
        handles.append(
            Patch(facecolor=cluster_colour(cluster), edgecolor="none", label=f"C{cluster}  n={n:,} ({share:.1f}%)")
        )
    handles.append(Patch(facecolor=LOW_FLOW_FACE, edgecolor="none", label=f"{LOW_FLOW_LABEL}  n={len(low_flow):,}"))
    handles.append(
        Patch(facecolor=NO_STOP_FACE, edgecolor=NO_STOP_EDGE, linewidth=0.4, hatch=NO_STOP_HATCH,
              label=f"{NO_STOP_LABEL}  n={len(no_stop):,}")
    )
    return ax.legend(
        handles=handles, loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False,
        fontsize=legend_fontsize, handlelength=1.4, handleheight=1.0, labelspacing=0.5,
        title=f"K={k} clusters (sized by LSOA count)", title_fontsize=legend_fontsize, alignment="left",
    )
