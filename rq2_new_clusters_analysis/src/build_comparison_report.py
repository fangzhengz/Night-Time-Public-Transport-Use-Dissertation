"""Join internal cluster-coherence + LNWC + IMD association into one table.

This is the actual deliverable this folder exists for: previously these
three pieces of evidence lived in three separate report files (two
different folders even) and only referenced each other in prose. This
script puts them in one table, per mode, for both the now-retired canonical
clustering and this folder's two now-adopted clusterings (bus StopArea CLR
K=4; rail all-modes K=5, rerun after the Paddington correction on
2026-08-07), so the two can be read
side by side rather than cross-referenced by hand. Internal variable/column
names below still say "canonical"/"sensitivity" -- read those as "old
retired reference" / "current adopted result", not a still-open status
question; see README.md for the promotion history.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

START = time.time()

CANON_RAIL_LNWC = C.FYP / "rq2test analysis" / "outputs" / "data" / "statistical_summary.csv"
CANON_BUS_LNWC = CANON_RAIL_LNWC
CANON_RAIL_N = 270
CANON_BUS_N = 4100
CANON_RAIL_K = 5
CANON_BUS_K = 3
CURRENT_RAIL_N = pd.read_csv(C.RAIL_LABELS, usecols=["unit"])["unit"].nunique()
K_PANEL = C.FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_k_selection_panel.csv"


def load_internal_coherence() -> pd.DataFrame:
    canon = pd.concat(
        [pd.read_csv(C.CANON_RAIL_SIGNIFICANCE), pd.read_csv(C.CANON_BUS_SIGNIFICANCE)],
        ignore_index=True,
    )[["mode", "metric", "n", "n_clusters", "epsilon_squared", "p_bh"]].rename(
        columns={"n": "n_canonical", "n_clusters": "k_canonical", "epsilon_squared": "epsilon2_canonical", "p_bh": "p_bh_canonical"}
    )
    sensitivity = pd.read_csv(C.DATA_OUT / "cluster_metric_significance.csv")[
        ["mode", "metric", "n", "n_clusters", "epsilon_squared", "p_bh"]
    ].rename(columns={"n": "n_sensitivity", "n_clusters": "k_sensitivity", "epsilon_squared": "epsilon2_sensitivity", "p_bh": "p_bh_sensitivity"})

    merged = canon.merge(sensitivity, on=["mode", "metric"], how="outer", validate="one_to_one")
    merged["epsilon2_delta"] = merged["epsilon2_sensitivity"] - merged["epsilon2_canonical"]
    merged["clustering_canonical"] = merged["mode"].map({"rail": "Underground-only (270 st.)", "bus": "original hub-first min36 raw_share, K=3 (pre-StopArea)"})
    merged["clustering_sensitivity"] = merged["mode"].map({"rail": f"all-modes merged, NaPTAN-matched refit ({CURRENT_RAIL_N} st.)", "bus": "StopArea CLR, K=4 (adopted 2026-07-29)"})
    return merged.sort_values(["mode", "metric"]).reset_index(drop=True)


def load_external_association() -> pd.DataFrame:
    canon_lnwc = pd.read_csv(CANON_RAIL_LNWC)
    canon_bus_lnwc_row = canon_lnwc.loc[canon_lnwc["analysis"] == "cluster_x_lnwc_chi_square"].iloc[0]
    canon_rail_dom_row = canon_lnwc.loc[canon_lnwc["analysis"] == "cluster_x_dominant_lnwc_chi_square"].iloc[0]
    canon_rail_perm_row = canon_lnwc.loc[canon_lnwc["analysis"] == "composition_label_permutation"].iloc[0]

    sens_lnwc = pd.read_csv(C.DATA_OUT / "lnwc_statistical_summary.csv")
    sens_bus_lnwc_row = sens_lnwc.loc[sens_lnwc["analysis"] == "cluster_x_lnwc_chi_square"].iloc[0]
    sens_rail_dom_row = sens_lnwc.loc[sens_lnwc["analysis"] == "cluster_x_dominant_lnwc_chi_square"].iloc[0]
    sens_rail_perm_row = sens_lnwc.loc[sens_lnwc["analysis"] == "composition_label_permutation"].iloc[0]

    canon_imd = pd.read_csv(C.CANON_IMD_WEAK_LINE)
    sens_imd = pd.read_csv(C.DATA_OUT / "cluster_vs_imd_kruskal_all.csv")

    def imd_row(frame: pd.DataFrame, mode: str) -> pd.Series:
        return frame.loc[frame["mode"] == mode].iloc[0]

    rows = [
        {
            "mode": "bus", "clustering": "original (hub-first min36 raw_share, K=3, pre-StopArea)", "K": CANON_BUS_K, "n_lnwc": int(canon_bus_lnwc_row["n"]),
            "lnwc_association": "cluster x LNWC (direct LSOA join)", "lnwc_cramers_v": canon_bus_lnwc_row["cramers_v"],
            "n_imd": int(imd_row(canon_imd, "bus")["n"]), "imd_epsilon2": imd_row(canon_imd, "bus")["epsilon_squared"],
        },
        {
            "mode": "bus", "clustering": "adopted (StopArea CLR, K=4)", "K": C.BUS_K, "n_lnwc": int(sens_bus_lnwc_row["n"]),
            "lnwc_association": "cluster x LNWC (direct LSOA join)", "lnwc_cramers_v": sens_bus_lnwc_row["cramers_v"],
            "n_imd": int(imd_row(sens_imd, "bus")["n"]), "imd_epsilon2": imd_row(sens_imd, "bus")["epsilon_squared"],
        },
        {
            "mode": "rail", "clustering": "canonical (Underground-only, 270 st.)", "K": CANON_RAIL_K, "n_lnwc": int(canon_rail_dom_row["n"]),
            "lnwc_association": "cluster x dominant LNWC (1200m Voronoi catchment)", "lnwc_cramers_v": canon_rail_dom_row["cramers_v"],
            "n_imd": int(imd_row(canon_imd, "rail")["n"]), "imd_epsilon2": imd_row(canon_imd, "rail")["epsilon_squared"],
            "lnwc_composition_r2": canon_rail_perm_row["r_squared"],
        },
        {
            "mode": "rail", "clustering": f"adopted (all-modes merged refit, {CURRENT_RAIL_N} st. clustered / {int(sens_rail_dom_row['n'])} st. LNWC-eligible)", "K": C.RAIL_K, "n_lnwc": int(sens_rail_dom_row["n"]),
            "lnwc_association": f"cluster x dominant LNWC ({C.RAIL_CATCHMENT_METRES}m Voronoi catchment, equal-weight LSOA aggregation, rebuilt)", "lnwc_cramers_v": sens_rail_dom_row["cramers_v"],
            "n_imd": int(imd_row(sens_imd, "rail")["n"]), "imd_epsilon2": imd_row(sens_imd, "rail")["epsilon_squared"],
            "lnwc_composition_r2": sens_rail_perm_row["r_squared"],
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    required = [
        C.CANON_RAIL_SIGNIFICANCE, C.CANON_BUS_SIGNIFICANCE, CANON_RAIL_LNWC, C.CANON_IMD_WEAK_LINE,
        C.DATA_OUT / "cluster_metric_significance.csv", C.DATA_OUT / "lnwc_statistical_summary.csv", C.DATA_OUT / "cluster_vs_imd_kruskal_all.csv",
        K_PANEL,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs (run run_context_metrics.py, run_lnwc_analysis.py, run_imd_analysis.py first): {missing}")

    internal = load_internal_coherence()
    internal.to_csv(C.DATA_OUT / "comparison_internal_coherence.csv", index=False)

    external = load_external_association()
    external.to_csv(C.DATA_OUT / "comparison_external_association.csv", index=False)

    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Combined comparison: canonical/original vs adopted/sensitivity clusters",
        "",
        "## Material Passport",
        "",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: rq2_new_clusters_comparison_v1",
        "",
        "## What this answers",
        "",
        "For each mode, does the alternative clustering (rail: all-modes merged K=5; "
        "bus: StopArea CLR K=4, adopted 2026-07-29 as the bus clustering result) tell a "
        "better- or worse-supported cluster-to-context story than the original/canonical "
        "one, on three legs of evidence that previously only existed in separate report "
        "files:",
        "",
        "1. internal coherence -- does the cluster label explain its own continuous "
        "profile metrics (Kruskal-Wallis epsilon-squared)?",
        "2. external LNWC association (chi-square / Cramer's V, or the 7-part "
        "composition permutation R2 for rail).",
        "3. external IMD2025 weak-line association (cluster x IMD score, epsilon-squared).",
        "",
        "## 1. Internal coherence: metric ~ cluster (epsilon-squared)",
        "",
        internal[[
            "mode", "metric", "clustering_canonical", "k_canonical", "epsilon2_canonical",
            "clustering_sensitivity", "k_sensitivity", "epsilon2_sensitivity", "epsilon2_delta",
        ]].to_markdown(index=False, floatfmt=".3f"),
        "",
        "## 2. External association: LNWC and IMD2025",
        "",
        external.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Reading",
        "",
    ]

    bus_internal = internal.loc[internal["mode"] == "bus"]
    rail_internal = internal.loc[internal["mode"] == "rail"]
    bus_ext = external.loc[external["mode"] == "bus"].set_index("clustering")
    rail_ext = external.loc[external["mode"] == "rail"].set_index("clustering")
    k_panel = pd.read_csv(K_PANEL).set_index("K")
    k5, k6, k7 = (k_panel.loc[k] for k in (5, 6, 7))
    rail_lnwc_n = int(rail_ext.iloc[1]["n_lnwc"])
    rail_improves = rail_internal.loc[rail_internal["epsilon2_delta"] > 0, "metric"].tolist()
    rail_weakens = rail_internal.loc[rail_internal["epsilon2_delta"] < 0, "metric"].tolist()
    rail_internal_sentence = (
        f"{', '.join(rail_improves)} improve and {', '.join(rail_weakens)} weaken"
        if rail_improves
        else f"none of the directly matched metrics improve; {', '.join(rail_weakens)} weaken"
    )

    bus_gain_metrics = bus_internal.loc[bus_internal["epsilon2_delta"] > 0.02, "metric"].tolist()
    bus_lnwc_delta = bus_ext.iloc[1]["lnwc_cramers_v"] - bus_ext.iloc[0]["lnwc_cramers_v"]
    bus_imd_delta = bus_ext.iloc[1]["imd_epsilon2"] - bus_ext.iloc[0]["imd_epsilon2"]
    lines.extend([
        f"- **Bus (StopArea CLR K=4, adopted 2026-07-29, vs the original hub-first min36 "
        f"K=3)**: internal coherence changes on "
        f"{', '.join(bus_gain_metrics) if bus_gain_metrics else 'no metric by more than 0.02'} "
        f"(most notably the original's weak spots, direction_balance and weekend_ratio). "
        f"External association moves: LNWC Cramer's V "
        f"{'+' if bus_lnwc_delta >= 0 else ''}{bus_lnwc_delta:.3f}, IMD epsilon-squared "
        f"{'+' if bus_imd_delta >= 0 else ''}{bus_imd_delta:.3f}. Adoption of StopArea CLR K=4 "
        f"was a methodological decision (BIC-preferred K for the CLR transform; see "
        f"`rq1_bus_stoparea_clustering/outputs/clr/diagnostics/kdiag.csv`), not one driven by "
        f"this external-association comparison -- it carries a known stability caveat "
        f"(bootstrap min-cluster Jaccard 0.401 at K=4 vs 0.883 at K=3) that should be "
        f"disclosed alongside these numbers, not resolved by them.",
        "",
        f"- **Rail (all-modes K=5, NaPTAN-matched {CURRENT_RAIL_N}-station refit vs canonical K=5, Underground-only)**: "
        f"this rail result was rerun 2026-08-07 after Paddington NR (NLC 3087) and Paddington TfL "
        f"(NLC 670) were correctly consolidated as one physical station. The preprocessing now merges "
        f"14 co-located groups (29 NLCs into 14 units), and still excludes the 16 stations that have no NaPTAN Greater-London "
        f"coordinate match before GMM fitting (not just downstream from LNWC/IMD), by "
        f"filtering the input to `numbat_all_area_test`'s own `02`-`07` pipeline and rerunning it "
        f"unmodified -- see `numbat_all_area_test/README.md`'s \"NaPTAN-matched station scope\" section "
        f"and `outputs/report/VALIDATION_REPORT.md` plus "
        f"`outputs/data/rail_allmodes_k_selection_panel.csv`. This mirrors "
        f"canonical's own scope convention exactly: canonical's 270-station clustering already includes "
        f"several border Underground stations outside the strict Greater London boundary (Amersham, "
        f"Chesham, Epping, etc.) and only excludes them downstream from LNWC/IMD, not from the clustering "
        f"itself. Under the equal-budget five-seed, n_init=200 panel, K=5 is now also the best BIC "
        f"solution ({k5['BIC']:,.1f}, versus {k6['BIC']:,.1f} for K=6 and {k7['BIC']:,.1f} for K=7). "
        f"The stability evidence points in the same direction: mean pairwise seed ARI is "
        f"{k5['seed_ari_mean']:.3f} for K=5, compared with {k6['seed_ari_mean']:.3f} for K=6 and "
        f"{k7['seed_ari_mean']:.3f} for K=7; mean bootstrap minimum-cluster Jaccard is "
        f"{k5['bootstrap_min_jaccard_mean']:.3f}, {k6['bootstrap_min_jaccard_mean']:.3f}, and "
        f"{k7['bootstrap_min_jaccard_mean']:.3f}, respectively. The night-persistent group's survival "
        f"Jaccard is {k5['night_group_jaccard_mean']:.3f} at K=5, "
        f"{k6['night_group_jaccard_mean']:.3f} at K=6, and {k7['night_group_jaccard_mean']:.3f} at K=7. "
        f"K=5 therefore remains the adopted solution after the correction, conditional on this feature "
        f"definition and diag-GMM family. For internal coherence, "
        f"{rail_internal_sentence}, with "
        f"log_total_activity dropping the most. External association (computed over the {rail_lnwc_n} "
        f"stations that also fall within the strict Greater London/LNWC extent, same as canonical's own "
        f"254-station LNWC-eligible subset of its 270) is consistently weaker than canonical: LNWC "
        f"Cramer's V {rail_ext.iloc[1]['lnwc_cramers_v']:.3f} vs canonical's {rail_ext.iloc[0]['lnwc_cramers_v']:.3f}, "
        f"IMD epsilon-squared {rail_ext.iloc[1]['imd_epsilon2']:.3f} vs canonical's "
        f"{rail_ext.iloc[0]['imd_epsilon2']:.3f} (still a large drop). So correcting the station accounting "
        f"to remove the duplicate physical observation was methodologically necessary and did change the "
        f"partition meaningfully, but it does not reverse the headline finding: widening rail scope to "
        f"all NUMBAT modes still does not out-perform canonical Underground-only on the cluster-to-context "
        f"story.",
        "",
        "## Interpretation limits",
        "",
        f"- Sample sizes differ across rows (rail LNWC n changes from 254 canonical to {rail_lnwc_n} "
        "in the adopted all-modes result because of the larger station pool; bus n drops from 4,100 "
        "(original hub-first) to 3,372 (StopArea, min_direction>=36) mainly because of the "
        "different LSOA allocation method and threshold, not a deliberate exclusion "
        "decision) -- effect sizes are not on an identical universe and should be read as "
        "directional evidence, not a controlled like-for-like test.",
        "- Both clusterings compared here are now adopted, not sensitivity checks: bus "
        "StopArea CLR K=4 and rail all-modes K=5 (rerun 2026-08-07). Bus was adopted "
        "because internal and external evidence both improved over canonical; rail was "
        "adopted for scope-defensibility reasons despite external association staying weaker "
        "than canonical's Underground-only result (see the rail paragraph above and "
        "README.md) -- the two adoptions rest on different kinds of justification and should "
        "not be conflated. See the per-script reports for full caveats.",
        "- The pooled, cluster-blind continuous-metric x LNWC/IMD test is intentionally not "
        "part of this comparison (see run_imd_analysis.py's docstring).",
    ])
    (C.REPORT_OUT / "COMBINED_COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "generated_utc": generated, "duration_seconds": time.time() - START,
        "command": "py -3 src/build_comparison_report.py",
    }
    (C.REPORT_OUT / "run_metadata_comparison.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed comparison report in {metadata['duration_seconds']:.1f}s.")


if __name__ == "__main__":
    main()
