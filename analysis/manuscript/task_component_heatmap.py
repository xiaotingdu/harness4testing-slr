"""Generate the annotated task-by-component heatmap for Section 5.2."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Rectangle


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
from rq2_data import read, write, AUDIT

DATA = ROOT / "tools" / "proposed_system_components_154.csv"


def load() -> list[dict[str, str]]:
    return read(DATA)

OUTPUT = HERE / "task_component_heatmap.pdf"
PREVIEW = ROOT / "tmp" / "pdfs" / "task_component_heatmap.png"

COMPONENTS = ("E", "T", "C", "L", "O", "V", "G")
COMPONENT_LABELS = (
    "$\\mathbf{E}$\nExecution",
    "$\\mathbf{T}$\nTool interface",
    "$\\mathbf{C}$\nContext & memory",
    "$\\mathbf{L}$\nLifecycle",
    "$\\mathbf{O}$\nObservability",
    "$\\mathbf{V}$\nVerification",
    "$\\mathbf{G}$\nGovernance",
)
TASKS = [
    ("unit_test_generation", "Unit-test generation"),
    ("test_oracle_generation", "Test-oracle generation"),
    ("system_test_input_generation", "System-test-input generation"),
    ("bug_analysis", "Bug analysis"),
    ("debugging", "Debugging"),
    ("program_repair", "Program repair"),
]
BAND_COLOURS = ("#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B")


def parse_components(value: str) -> set[str]:
    return set(value) & set(COMPONENTS)


def build_matrix() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    rows = load()
    if len(rows) != 154:
        raise ValueError(f"Expected 154 systems, found {len(rows)}")
    counts: list[list[int]] = []
    denominators: list[int] = []
    labels: list[str] = []
    audit = []
    for raw_task, display_task in TASKS:
        papers = [row for row in rows if row["task"] == raw_task]
        expected = len(papers)
        if not expected:
            raise ValueError(f"No proposed systems classified as {raw_task}")
        encoded = [parse_components(row["engineering_components"]) for row in papers]
        counts.append(
            [sum(component in item for item in encoded) for component in COMPONENTS]
        )
        denominators.append(expected)
        labels.append(f"{display_task}  ($n={expected}$)")
        for component, count in zip(COMPONENTS, counts[-1]):
            audit.append(dict(testing_task=raw_task, component=component,
                              paper_count=count, paper_denominator=expected,
                              within_task_percentage=f"{100*count/expected:.1f}",
                              paper_ids="; ".join(sorted(r["record_id"] for r in papers if component in parse_components(r["engineering_components"])))))

    count_matrix = np.asarray(counts, dtype=int)
    denominator_array = np.asarray(denominators, dtype=int)
    if denominator_array.sum() != len(rows):
        raise ValueError("Task groups do not cover all RQ2 papers")
    percentages = 100.0 * count_matrix / denominator_array[:, None]
    totals = count_matrix.sum(axis=0).tolist()
    if totals != [134, 148, 154, 154, 81, 135, 59]:
        raise ValueError(f"Unexpected component totals: {totals}")
    write(AUDIT / "task_component_heatmap_data.csv", audit)
    return count_matrix, percentages, denominator_array, labels


def main() -> None:
    counts, percentages, denominators, row_labels = build_matrix()
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "font.size": 9.0,
            "text.color": "black",
            "axes.labelcolor": "black",
            "xtick.color": "black",
            "ytick.color": "black",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    # Use a wider light-to-dark range to distinguish the five prevalence bands.
    # Labels switch between black and white for maximum contrast.
    boundaries = (0, 25, 50, 75, 90, 100)
    palette = ListedColormap(BAND_COLOURS, name="prevalence_bands")
    # Internal boundaries enter the higher band; 100% stays in the last band.
    norm = BoundaryNorm(boundaries, palette.N, clip=True)
    fig, ax = plt.subplots(figsize=(9.60, 0.63 * len(TASKS) + 0.45))

    # Components follow the fixed ETCLOVG order with uniform spacing; no
    # additional hierarchy is imposed on the seven responsibilities.
    x_positions = np.arange(len(COMPONENTS), dtype=float)

    for row in range(counts.shape[0]):
        for column in range(counts.shape[1]):
            count = int(counts[row, column])
            percentage = float(percentages[row, column])
            fill = palette(norm(percentage))
            rgb = np.asarray(fill[:3])
            linear_rgb = np.where(
                rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4
            )
            luminance = float(linear_rgb @ np.array([0.2126, 0.7152, 0.0722]))
            black_contrast = (luminance + 0.05) / 0.05
            white_contrast = 1.05 / (luminance + 0.05)
            text_colour = "white" if white_contrast > black_contrast else "black"
            if max(black_contrast, white_contrast) < 4.5:
                raise ValueError("Insufficient text contrast in a heat-map cell")
            ax.add_patch(
                Rectangle(
                    (x_positions[column] - 0.5, row - 0.5),
                    1,
                    1,
                    facecolor=fill,
                    edgecolor="#FFFFFF",
                    linewidth=1.8,
                    zorder=1,
                )
            )
            ax.text(
                x_positions[column],
                row - 0.15,
                f"{percentage:.1f}%",
                ha="center",
                va="center",
                color=text_colour,
                fontsize=9.6,
                fontweight="normal",
                zorder=2,
            )
            ax.text(
                x_positions[column],
                row + 0.20,
                str(count),
                ha="center",
                va="center",
                color=text_colour,
                fontsize=9.6,
                fontweight="normal",
                zorder=2,
            )

    ax.set_xlim(-0.5, x_positions[-1] + 0.5)
    ax.set_ylim(len(TASKS) - 0.5, -0.5)
    ax.set_xticks([])
    ax.set_yticks(np.arange(len(TASKS)), row_labels, fontsize=8.8)
    ax.tick_params(axis="y", length=0, pad=8)

    for x, label in zip(x_positions, COMPONENT_LABELS):
        ax.text(x, -0.67, label, ha="center", va="bottom", fontsize=7.0,
                clip_on=False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    colour_scale = ScalarMappable(norm=norm, cmap=palette)
    colour_scale.set_array([])
    colour_bar = fig.colorbar(
        colour_scale,
        ax=ax,
        fraction=0.027,
        pad=0.035,
        boundaries=boundaries,
        ticks=boundaries,
        spacing="proportional",
        drawedges=True,
    )
    colour_bar.set_label("Within-task prevalence (%)", fontsize=9.0)
    colour_bar.ax.tick_params(labelsize=7.8, length=2.5)
    colour_bar.outline.set_linewidth(0.6)
    colour_bar.outline.set_edgecolor("#6F7F89")

    fig.subplots_adjust(left=0.34, right=0.94, top=0.90, bottom=0.04)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, bbox_inches="tight", pad_inches=0.035)
    fig.savefig(PREVIEW, dpi=260, bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)
    print(f"written {OUTPUT.name}")


if __name__ == "__main__":
    main()
