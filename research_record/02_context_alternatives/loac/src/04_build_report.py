"""Consolidate the bus/rail LOAC outputs into a combined audit, input
manifest, and RESULTS_SUMMARY.md, following the same conventions as
``rq2test analysis``'s LNWC report.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import (
    BUS_K,
    BUS_LABELS,
    DATA_OUT,
    LOAC_LOOKUP,
    LOAC_OA_GPKG,
    LOAC_SUPERGROUP_NAMES,
    OA_LSOA_LOOKUP,
    RAIL_CATCHMENT_METRES,
    RAIL_COORDS,
    RAIL_K,
    RAIL_LABELS,
    RAIL_META,
    REPORT_OUT,
)

START_TIME = time.time()


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    bus_audit = json.loads((DATA_OUT / "bus_loac_audit.json").read_text())
    rail_audit = json.loads((DATA_OUT / "rail_loac_audit.json").read_text())
    bus_stats = pd.read_csv(DATA_OUT / "bus_loac_statistical_summary.csv").iloc[0].to_dict()
    rail_stats = pd.read_csv(DATA_OUT / "rail_loac_statistical_summary.csv")
    rail_dominant_stats = rail_stats.iloc[0].to_dict()
    rail_permutation_stats = rail_stats.iloc[1].to_dict()

    required_inputs = [
        LOAC_LOOKUP,
        LOAC_OA_GPKG,
        OA_LSOA_LOOKUP,
        BUS_LABELS,
        RAIL_LABELS,
        RAIL_META,
        RAIL_COORDS,
    ]
    manifest = pd.DataFrame(
        [
            {
                "role": path.stem,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in required_inputs
        ]
    )
    manifest.to_csv(DATA_OUT / "input_manifest.csv", index=False)

    audit_rows = [
        {"component": "bus", "metric": key, "value": value} for key, value in bus_audit.items()
    ] + [{"component": "rail", "metric": key, "value": value} for key, value in rail_audit.items()]
    pd.DataFrame(audit_rows).to_csv(DATA_OUT / "data_audit.csv", index=False)

    lines = [
        "# RQ2 LOAC (London Output Area Classification) lens — results",
        "",
        "## Scope",
        "",
        "Third parallel socio-spatial lens alongside LNWC and IMD (per",
        "Mikaella's original 2026-07-02 guidance to add Census/LOAC as a",
        "separate layer, never previously built). Uses LOAC's composite",
        "Supergroup label (7 categories, A-G) as-is -- not decomposed into",
        "its 68 raw Census input variables. Clustering choice matches",
        "`rq2_new_clusters_analysis` (bus StopArea CLR K=4, rail",
        "all-modes NaPTAN-matched 403-station K=5), with the same 800 m",
        "rail catchment radius as that folder's 800 m sidecar.",
        "",
        "## LOAC Supergroups (official names)",
        "",
    ]
    lines += [f"- **{code}**: {name}" for code, name in LOAC_SUPERGROUP_NAMES.items()]
    lines += [
        "",
        f"- Bus: K={BUS_K}; direct LSOA join (LOAC aggregated from OA to",
        "  LSOA via modal Supergroup across constituent OAs).",
        f"- Rail: K={RAIL_K}; {RAIL_CATCHMENT_METRES} m Voronoi-clipped",
        "  catchments intersected directly against LOAC's OA-level",
        "  geopackage (no LSOA intermediate).",
        "",
        "## Coverage",
        "",
        f"- Bus: {bus_audit['matched_loac_rows']}/{bus_audit['fitted_rows']} "
        f"fitted LSOAs matched to a LOAC Supergroup "
        f"({bus_audit['match_rate']:.1%}).",
        f"- Rail: {rail_audit['stations_eligible_for_loac_analysis']}/"
        f"{rail_audit['input_rows']} stations eligible for LOAC analysis; "
        f"{rail_audit['stations_outside_loac_extent']} station points fall "
        "outside the LOAC/Greater-London extent (the same known set of "
        "NaPTAN-matched-but-boundary stations flagged in the LNWC/IMD runs "
        "on this clustering).",
        f"- Mean rail catchment LOAC coverage ratio: "
        f"{rail_audit['mean_loac_coverage_ratio']:.3f} "
        f"(minimum {rail_audit['minimum_loac_coverage_ratio']:.3f}).",
        "",
        "## Association statistics",
        "",
        f"- Bus cluster × LOAC dominant Supergroup: chi-square="
        f"{bus_stats['chi_square']:.2f}, Cramer's V={bus_stats['cramers_v']:.3f}, "
        f"n={int(bus_stats['n'])}.",
        f"- Rail cluster × LOAC dominant Supergroup: chi-square="
        f"{rail_dominant_stats['chi_square']:.2f}, Cramer's V="
        f"{rail_dominant_stats['cramers_v']:.3f}, n={int(rail_dominant_stats['n'])}.",
        f"- Rail seven-part Supergroup composition: permutation R²="
        f"{rail_permutation_stats['r_squared']:.3f}, p="
        f"{rail_permutation_stats['p_value']:.4f} (999 permutations).",
        "",
        "These are exploratory categorical association tests (same caveat as",
        "the LNWC treatment): ordinary chi-square/permutation tests here do",
        "not account for spatial autocorrelation between neighbouring",
        "units.",
        "",
        "## Explicitly out of scope for this pass",
        "",
        "- No continuous-metric/Freedman-Lane nested test (e.g. testing",
        "  whether IMD's association survives controlling for LOAC) --",
        "  deferred per the user's own request; this pass covers only the",
        "  categorical/compositional lens, matching LNWC's Section 6",
        "  treatment.",
        "- No decomposition into LOAC's raw 68 input Census variables.",
        "- No changes to any existing `rq2test analysis` or",
        "  `rq2_new_clusters_analysis` files.",
    ]
    (REPORT_OUT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    run_metadata = {
        "started_utc": datetime.fromtimestamp(START_TIME, tz=timezone.utc).isoformat(),
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": time.time() - START_TIME,
        "python": sys.version,
        "platform": platform.platform(),
    }
    (REPORT_OUT / "run_metadata.json").write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT_OUT / 'RESULTS_SUMMARY.md'}")


if __name__ == "__main__":
    main()
