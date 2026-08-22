"""Build the formal behavioural z-score panels from committed aggregates."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "tables"
OUTPUT = ROOT / "results" / "recomputed_figures"

LABELS = {
    "log_total_activity": "Night-time activity (log)",
    "direction_balance": "Directional balance",
    "post_2300_share": "Post-23:00 share",
    "post_midnight_persistence": "Post-midnight persistence",
    "weekend_ratio": "Weekend-to-weekday ratio",
    "weekend_common_ratio": "Weekend-to-weekday ratio",
}

COLOURS = {
    "rail": ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9"],
    "bus": ["#4C93D3", "#D1284B", "#00A6A6", "#1B3A6B"],
}


def build(mode: str) -> Path:
    table = pd.read_csv(SOURCE / f"{mode}_behavioural_signature_z.csv").set_index("cluster")
    metrics = list(table.columns)
    if mode == "bus" and len(metrics) != 5:
        raise RuntimeError(f"Expected five formal Bus metrics, found {metrics}")
    if mode == "rail" and len(metrics) != 4:
        raise RuntimeError(f"Expected four formal Rail metrics, found {metrics}")

    fig, axes = plt.subplots(len(table), 1, figsize=(10.5, 2.0 * len(table) + 1.2), sharex=True)
    if len(table) == 1:
        axes = [axes]
    limit = max(1.0, float(table.abs().to_numpy().max()) * 1.12)
    for position, (cluster, row) in enumerate(table.iterrows()):
        ax = axes[position]
        values = row.to_numpy(float)
        colours = [COLOURS[mode][position] if value >= 0 else "#2C7FB8" for value in values]
        ax.barh(range(len(metrics)), values, color=colours, height=0.62)
        ax.axvline(0, color="#222222", linewidth=1.5)
        ax.set_yticks(range(len(metrics)), [LABELS[item] for item in metrics])
        ax.invert_yaxis()
        ax.set_xlim(-limit, limit)
        ax.grid(axis="x", color="#E6E6E6", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_title(f"C{cluster}", loc="left", color=COLOURS[mode][position], weight="bold")
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
    axes[-1].set_xlabel(f"Z-score relative to {mode.title()}-wide mean")
    fig.suptitle(
        f"Post-clustering behavioural descriptors of the {len(table)} {mode.title()} usage types",
        fontsize=14,
        weight="bold",
    )
    fig.tight_layout()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / f"{mode}_behavioural_descriptors.png"
    fig.savefig(destination, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return destination


def main() -> None:
    for mode in ("rail", "bus"):
        print(build(mode))


if __name__ == "__main__":
    main()
