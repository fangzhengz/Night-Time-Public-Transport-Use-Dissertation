# -*- coding: utf-8 -*-
"""Shared cluster-map rendering for the StopArea bus clustering figures.

Every London LSOA falls into exactly one of three states, and before
2026-07-29 the map collapsed the last two into a single light grey:

1. clustered            -- in the fitted sample, carries a cluster colour
2. low night flow       -- has night bus demand but below the retention rule
3. no stop within LSOA  -- no StopArea representative point falls inside the
                           polygon at all, so the LSOA never entered the input

State 3 is not missing data and not a service gap: the median distance from
such an LSOA's boundary to the nearest StopArea unit is 27 m and every one of
them is within 400 m. Bus stops sit on arterial roads, and arterial roads are
typically LSOA boundaries, so a small LSOA enclosed by them has its serving
stops allocated to a neighbour. The effect concentrates in dense inner
boroughs (Hammersmith & Fulham 40.9%, Tower Hamlets 35.5%) and is weakest in
outer ones (Bromley 9.0%) -- the opposite of a coverage story. Rendering it as
its own category keeps that distinction legible instead of implying the two
kinds of blank area mean the same thing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


CLUSTERED = "clustered"
LOW_FLOW = "low_flow_excluded"
NO_STOP = "no_stop_in_lsoa"


def cluster_colour(cluster: int) -> str:
    """Colour for a cluster index, cycling if K exceeds the palette."""
    return C.CLUSTER_COLOURS[cluster % len(C.CLUSTER_COLOURS)]


def build_status_frame(
    boundaries,
    clustered_units,
    labels,
    all_input_units,
) -> "pd.DataFrame":
    """Attach a three-state status and a cluster id to every boundary polygon.

    `all_input_units` is every LSOA that reached the feature table (i.e. that
    had at least one StopArea unit allocated to it). Boundary polygons absent
    from it are state 3; polygons present but not in `clustered_units` are
    state 2.
    """
    clustered_units = [str(unit) for unit in clustered_units]
    all_input = {str(unit) for unit in all_input_units}
    status = pd.DataFrame(
        {
            "lsoa": clustered_units,
            "status": CLUSTERED,
            "cluster": np.asarray(labels, dtype=int),
        }
    )
    low_flow = sorted(all_input - set(clustered_units))
    if low_flow:
        status = pd.concat(
            [
                status,
                pd.DataFrame({"lsoa": low_flow, "status": LOW_FLOW, "cluster": -1}),
            ],
            ignore_index=True,
        )
    mapped = boundaries.merge(status, on="lsoa", how="left")
    # Polygons that matched nothing never entered the input at all.
    mapped["status"] = mapped["status"].fillna(NO_STOP)
    mapped["cluster"] = mapped["cluster"].fillna(-1).astype(int)
    return mapped


def draw_cluster_map(ax, mapped, k: int, legend: bool = True, legend_fontsize: int = 8):
    """Render the three states and a size-annotated legend onto `ax`."""
    no_stop = mapped[mapped["status"] == NO_STOP]
    low_flow = mapped[mapped["status"] == LOW_FLOW]
    clustered = mapped[mapped["status"] == CLUSTERED]

    if not no_stop.empty:
        no_stop.plot(
            ax=ax,
            facecolor=C.NO_STOP_FACE,
            hatch=C.NO_STOP_HATCH,
            edgecolor=C.NO_STOP_EDGE,
            linewidth=C.NO_STOP_EDGE_WIDTH,
        )
    if not low_flow.empty:
        low_flow.plot(ax=ax, facecolor=C.LOW_FLOW_FACE, linewidth=0.0)

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
            Patch(
                facecolor=cluster_colour(cluster),
                edgecolor="none",
                label=f"C{cluster}  n={n:,} ({share:.1f}%)",
            )
        )
    handles.append(
        Patch(
            facecolor=C.LOW_FLOW_FACE,
            edgecolor="none",
            label=f"{C.LOW_FLOW_LABEL}  n={len(low_flow):,}",
        )
    )
    handles.append(
        Patch(
            facecolor=C.NO_STOP_FACE,
            edgecolor=C.NO_STOP_EDGE,
            linewidth=0.4,
            hatch=C.NO_STOP_HATCH,
            label=f"{C.NO_STOP_LABEL}  n={len(no_stop):,}",
        )
    )
    return ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.0, 1.0),
        frameon=False,
        fontsize=legend_fontsize,
        handlelength=1.4,
        handleheight=1.0,
        labelspacing=0.5,
        title=f"K={k} clusters (sized by LSOA count)",
        title_fontsize=legend_fontsize,
        alignment="left",
    )
