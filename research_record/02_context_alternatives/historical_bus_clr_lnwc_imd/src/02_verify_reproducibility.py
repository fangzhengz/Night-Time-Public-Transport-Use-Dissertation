"""Re-run the deterministic analysis and compare primary tabular artifacts."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
MAIN = ROOT / "src" / "01_run_bus_context_analysis.py"

KEY_FILES = [
    DATA / "bus_k4_context_lsoa.csv",
    DATA / "k4_cluster_context_summary.csv",
    DATA / "k4_lnwc_association.csv",
    DATA / "k4_lnwc_enrichment.csv",
    DATA / "k4_imd_kruskal.csv",
    DATA / "k4_imd_dunn_pairwise.csv",
    DATA / "k3_k4_external_effect_sensitivity.csv",
    DATA / "k3_k4_crosswalk_counts.csv",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    missing = [str(path) for path in KEY_FILES if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Run the main analysis first; missing: {missing}")
    before = {path.name: sha256(path) for path in KEY_FILES}
    completed = subprocess.run(
        [sys.executable, str(MAIN)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    after = {path.name: sha256(path) for path in KEY_FILES}
    rows = []
    for path in KEY_FILES:
        name = path.name
        rows.append((name, before[name], after[name], before[name] == after[name]))
    verified = completed.returncode == 0 and all(row[3] for row in rows)
    lines = [
        "# Reproducibility check",
        "",
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite / experiment-agent",
        "- Origin Mode: validate",
        f"- Origin Date: {datetime.now(timezone.utc).isoformat()}",
        f"- Verification Status: {'VERIFIED' if verified else 'MISMATCH'}",
        "- Version Label: bus_clr_k4_context_repro_v1",
        "",
        "## Re-run",
        "",
        f"- Command: `{sys.executable} {MAIN}`",
        f"- Exit code: {completed.returncode}",
        "- Determinism rule: exact SHA-256 match for all primary CSV artifacts.",
        "- Figures, timestamps and environment metadata are intentionally excluded from byte comparison.",
        "",
        "| File | Before SHA-256 | After SHA-256 | Match |",
        "|---|---|---|---|",
    ]
    for name, old, new, match in rows:
        lines.append(f"| {name} | `{old}` | `{new}` | {'YES' if match else 'NO'} |")
    if completed.stderr.strip():
        lines.extend(["", "## Re-run stderr", "", "```text", completed.stderr.strip(), "```"])
    (REPORT / "REPRODUCIBILITY_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Reproducibility verdict: {'VERIFIED' if verified else 'MISMATCH'}")
    if not verified:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
