"""Fast regression checks for the committed dissertation evidence."""
from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF_SHA256 = "5314d6511254ed0331ffcb712e27bdf7317fe6e1587aa7ab510522bda5f45963"

PAPER_FIGURE_MAP = {
    "v5_ch3_fig1.jpg": "research_framework.jpg",
    "v5_ch3_lnwcmap.png": "lnwc_spatial_distribution.png",
    "v5_ch3_voronoi.png": "rail_800m_voronoi_catchments.png",
    "v5_ch4_fig4.png": "rail_model_selection.png",
    "v5_ch4_fig5.png": "bus_model_selection.png",
    "v5_ch4_fig6.png": "rail_temporal_profiles.png",
    "v5_ch4_fig7.png": "rail_cluster_map.png",
    "v5_ch4_fig8.png": "rail_behavioural_descriptors.png",
    "v5_ch4_fig9.png": "bus_temporal_profiles.png",
    "v5_ch4_fig10.png": "bus_cluster_map.png",
    "v5_ch4_fig11.png": "bus_behavioural_descriptors.png",
    "v5_ch4_fig12.png": "rail_lnwc_enrichment.png",
    "v5_ch4_fig13.png": "bus_lnwc_enrichment.png",
    "v5_ch4_fig14.png": "rail_context_effect_ranking.png",
    "v5_ch4_fig15.png": "rail_context_profiles.png",
    "v5_ch4_fig16.png": "bus_context_effect_ranking.png",
    "v5_ch4_fig17.png": "bus_context_profiles.png",
    "appA_fig18.png": "rail_clusters_lnwc_map.png",
    "appA_fig19.png": "bus_clusters_lnwc_map.png",
    "appA_fig20.png": "behavioural_effect_sizes.png",
    "appA_fig21.png": "rail_feature_maps.png",
    "appA_fig22.png": "bus_feature_maps.png",
}

RECOMPUTED_FIGURES = {
    "rail_behavioural_descriptors.png", "bus_behavioural_descriptors.png",
    "rail_temporal_profiles.png", "bus_temporal_profiles.png",
    "rail_cluster_map.png", "bus_cluster_map.png",
    "rail_lnwc_enrichment.png", "bus_lnwc_enrichment.png",
    "rail_clusters_lnwc_map.png", "bus_clusters_lnwc_map.png",
    "rail_context_profiles.png", "bus_context_profiles.png",
    "rail_context_full_matrix.png", "bus_context_full_matrix.png",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate() -> list[str]:
    checks: list[str] = []
    pdf = ROOT / "paper" / "CASA0010_dissertation_FangzhengZhou.pdf"
    assert sha256(pdf) == PDF_SHA256, "Submitted PDF hash changed"
    checks.append("submitted PDF hash")

    rail = rows(ROOT / "results" / "tables" / "rail_cluster_labels.csv")
    assert len(rail) == 403
    assert Counter(int(item["cluster"]) for item in rail) == Counter({0: 89, 1: 26, 2: 90, 3: 31, 4: 167})
    checks.append("Rail n=403, K=5 and cluster sizes")

    bus_all = rows(ROOT / "results" / "tables" / "bus_cluster_labels.csv")
    bus = [item for item in bus_all if int(item["cluster"]) >= 0]
    assert len(bus) == 3383
    assert Counter(int(item["cluster"]) for item in bus) == Counter({0: 604, 1: 1134, 2: 1069, 3: 576})
    assert not any("36" in item["exclusion_reason"] for item in bus_all)
    checks.append("Bus n=3,383, K=4, cluster sizes and threshold labels")

    lnwc = rows(ROOT / "results" / "tables" / "lnwc_association_full.csv")
    rail_perm = next(item for item in lnwc if item["mode"] == "rail" and item["analysis"] == "composition_label_permutation")
    bus_chi = next(item for item in lnwc if item["mode"] == "bus")
    assert int(rail_perm["n"]) == 389
    assert abs(float(rail_perm["r_squared"]) - 0.26292022785410785) < 1e-12
    assert abs(float(rail_perm["p_value"]) - 0.001) < 1e-12
    assert int(bus_chi["n"]) == 3383
    assert abs(float(bus_chi["cramers_v"]) - 0.25258490410000495) < 1e-12
    checks.append("LNWC Rail R-squared/permutation p and Bus Cramer's V")

    context = rows(ROOT / "results" / "tables" / "context_omnibus_tests.csv")
    assert Counter(item["mode"] for item in context) == Counter({"rail": 20, "bus": 20})
    checks.append("20 contextual variables per mode")

    bus_signature = rows(ROOT / "results" / "tables" / "bus_behavioural_signature_z.csv")
    assert "deep_night_share" not in bus_signature[0]
    assert len(bus_signature[0]) - 1 == 5
    checks.append("five-metric formal Bus behavioural signature")

    source_dir = ROOT / "paper" / "source" / "figures"
    paper_dir = ROOT / "results" / "figures"
    for source_name, published_name in PAPER_FIGURE_MAP.items():
        source = source_dir / source_name
        published = paper_dir / published_name
        assert source.is_file(), f"Missing submitted source figure: {source_name}"
        assert published.is_file(), f"Missing paper-matched result figure: {published_name}"
        assert sha256(source) == sha256(published), f"Paper figure differs: {published_name}"
    checks.append("22 paper-matched figure hashes")

    recomputed_dir = ROOT / "results" / "recomputed_figures"
    recomputed_present = {path.name for path in recomputed_dir.glob("*")}
    missing_recomputed = RECOMPUTED_FIGURES - recomputed_present
    assert not missing_recomputed, f"Missing recomputed figures: {sorted(missing_recomputed)}"
    checks.append("14 separately stored recomputed figures")

    record = ROOT / "research_record"
    record_required = {
        "README.md",
        "STATUS.csv",
        "03_deferred_rq3_mismatch/STATUS.md",
        "03_deferred_rq3_mismatch/outputs/report/RESULTS_SUMMARY.md",
        "04_exploratory_bus_rail_relation/STATUS.md",
        "04_exploratory_bus_rail_relation/outputs/report/RESULTS.md",
    }
    missing_record = sorted(item for item in record_required if not (record / item).is_file())
    assert not missing_record, f"Missing research-record evidence: {missing_record}"
    record_index = rows(record / "STATUS.csv")
    assert len(record_index) == 22
    assert all(item["category"] and item["status"] and item["path"] for item in record_index)
    for active_script in (ROOT / "scripts" / "run_pipeline.py", ROOT / "scripts" / "publish_results.py"):
        assert "research_record" not in active_script.read_text(encoding="utf-8")
    checks.append("separate, indexed research record")
    return checks


def main() -> None:
    checks = validate()
    print(f"PASS: {len(checks)} repository evidence checks")
    for check in checks:
        print(f"  - {check}")


if __name__ == "__main__":
    main()
