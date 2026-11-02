"""Build the standard UpSet plot used as Figure 9."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
from rq2_data import read, components as decode_components, write, AUDIT


DATA = Path(__file__).resolve().parent / "proposed_system_components_154.csv"


def load() -> list[dict[str, str]]:
    return read(DATA)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "figures" / "focal_configuration_profiles.pdf"
MAIN_OUTPUT = ROOT / "figures" / "focal_configuration_profiles_beautified.pdf"
PREVIEW = ROOT / "tmp" / "pdfs" / "focal_configuration_profiles.png"

COMPONENTS = ("E", "T", "C", "L", "O", "V", "G")
COMPONENT_LABELS = {
    "E": "Execution (E)",
    "T": "Tool Interface (T)",
    "C": "Context and Memory (C)",
    "L": "Lifecycle (L)",
    "O": "Observability (O)",
    "V": "Verification (V)",
    "G": "Governance (G)",
}
TOTAL = 154

INK = "#3D4248"
MUTED_INK = "#6F757B"
BACKGROUND_DOT = "#D9DDE1"
GRID = "#D7DADD"
ACCENT = "#0072B2"  # Okabe-Ito blue, shared with Figs. 6 and 8


def parse_components(value: str) -> set[str]:
    """Read the comma-separated component field in the system-level data."""
    return {item.strip() for item in value.split(",") if item.strip()}


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "font.size": 8.6,
            "axes.labelsize": 8.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    rows = load()
    grouped = defaultdict(list)
    for row in rows:
        signature = "".join(c for c in COMPONENTS if c in decode_components(row["engineering_components"]))
        grouped[signature].append(row["record_id"])
    records = [dict(components=c, focal_hc_count=len(ids),
                    prevalence_of_154=f"{100*len(ids)/len(rows):.1f}",
                    paper_ids="; ".join(sorted(ids))) for c, ids in grouped.items()]
    summary = pd.DataFrame(records).sort_values(
        ["focal_hc_count", "components"], ascending=[False, True]
    )
    systems = pd.DataFrame({"components": [", ".join(c for c in COMPONENTS if c in decode_components(r["engineering_components"])) for r in rows]})
    write(AUDIT / "configuration_upset_data.csv", summary.to_dict("records"))
    # All combinations are plotted, including those used by a single system.
    recurring = summary.reset_index(drop=True)

    if len(recurring) != len(grouped):
        raise ValueError("Combination partition mismatch")
    if int(summary["focal_hc_count"].sum()) != TOTAL or len(systems) != TOTAL:
        raise ValueError(f"Configuration counts do not sum to {TOTAL}")

    combinations = recurring["components"].astype(str).tolist()
    counts = recurring["focal_hc_count"].astype(int).to_numpy()

    x = np.arange(len(combinations))
    y = np.arange(len(COMPONENTS))

    fig = plt.figure(figsize=(8.25, 4.75))
    grid = fig.add_gridspec(
        2,
        1,
        height_ratios=(1.65, 1.85),
        left=0.215,
        right=0.985,
        top=0.955,
        bottom=0.20,
        hspace=0.10,
    )
    intersections = fig.add_subplot(grid[0, 0])
    matrix = fig.add_subplot(grid[1, 0], sharex=intersections)

    bar_colours = [ACCENT if index < 3 else INK for index in range(len(combinations))]
    bars = intersections.bar(x, counts, width=0.64, color=bar_colours, edgecolor="none")
    for index, (bar, count) in enumerate(zip(bars, counts)):
        percentage = 100.0 * count / TOTAL
        value_label = f"{count}\n({percentage:.1f}%)"
        intersections.text(
            bar.get_x() + bar.get_width() / 2,
            count + 0.65,
            value_label,
            ha="center",
            va="bottom",
            fontsize=8.0,
            fontweight="semibold" if index < 3 else "normal",
            color=ACCENT if index < 3 else INK,
            linespacing=0.9,
        )
    intersections.text(
        -0.32,
        52.0,
        f"Top three: {sum(counts[:3])} systems ({100*sum(counts[:3])/TOTAL:.1f}%)",
        ha="left",
        va="bottom",
        fontsize=8.6,
        color=ACCENT,
        fontweight="semibold",
    )
    intersections.set_ylim(0, 58)
    intersections.set_xlim(-0.55, len(combinations) - 0.45)
    intersections.set_ylabel("Systems with the\nexact combination", fontsize=8.8)
    intersections.tick_params(axis="x", bottom=False, labelbottom=False)
    intersections.set_yticks((0, 10, 20, 30, 40))
    intersections.grid(axis="y", color=GRID, linewidth=0.55)
    intersections.set_axisbelow(True)
    intersections.tick_params(axis="y", length=2.5, labelsize=7.8)
    for spine in ("top", "right"):
        intersections.spines[spine].set_visible(False)
    intersections.spines["left"].set_color(MUTED_INK)
    intersections.spines["bottom"].set_color(MUTED_INK)

    for row in y:
        if row % 2 == 0:
            matrix.axhspan(row - 0.5, row + 0.5, color="#F3F5F7", zorder=0)
        matrix.scatter(x, np.full(len(x), row), s=30, color=BACKGROUND_DOT, edgecolor="none", zorder=1)
    for column, combination in enumerate(combinations):
        combination_colour = ACCENT if column < 3 else INK
        present_rows = [row for row, component in enumerate(COMPONENTS) if component in combination]
        if len(present_rows) > 1:
            matrix.plot(
                [column, column],
                [min(present_rows), max(present_rows)],
                color=combination_colour,
                linewidth=1.6,
                solid_capstyle="round",
                zorder=2,
            )
        matrix.scatter(
            np.full(len(present_rows), column),
            present_rows,
            s=49,
            color=combination_colour,
            edgecolor="none",
            zorder=3,
        )
    matrix.set_xlim(-0.55, len(combinations) - 0.45)
    matrix.set_ylim(len(COMPONENTS) - 0.5, -0.5)
    matrix.set_xticks(x, combinations, rotation=45, ha="right", fontsize=8.2)
    for index, label in enumerate(matrix.get_xticklabels()):
        label.set_color(ACCENT if index < 3 else INK)
        label.set_fontweight("semibold" if index < 3 else "normal")
    matrix.set_yticks(y, [COMPONENT_LABELS[component] for component in COMPONENTS], fontsize=8.5)
    matrix.tick_params(axis="y", length=0, pad=8)
    matrix.tick_params(axis="x", length=0, pad=7)
    for spine in matrix.spines.values():
        spine.set_visible(False)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(MAIN_OUTPUT, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(PREVIEW, dpi=280, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"written {OUTPUT.name} and {MAIN_OUTPUT.name}")


if __name__ == "__main__":
    main()
