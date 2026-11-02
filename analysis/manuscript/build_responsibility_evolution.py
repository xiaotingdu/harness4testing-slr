"""Build the Section 5.1 overall-distribution and period heat-map figure."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle
from rq2_data import components, write, read, AUDIT


DATA = Path(__file__).resolve().parent / "proposed_system_components_154.csv"


def load() -> list[dict[str, str]]:
    return read(DATA)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "figures" / "responsibility_evolution.pdf"
PREVIEW = ROOT / "tmp" / "pdfs" / "responsibility_evolution.png"

ORDER = ("E", "T", "C", "L", "O", "V", "G")
NAMES = {
    "E": "Execution",
    "T": "Tool Interface",
    "C": "Context and Memory",
    "L": "Lifecycle",
    "O": "Observability",
    "V": "Verification",
    "G": "Governance",
}
INTERVALS = ("2024", "2025", "2026 through 30 June")
CMAP_NAME, CMAP_RANGE = "viridis_r", (0.0, 0.92)
BAR_COLOUR = "#31688E"  # viridis blue, shared with the heat map


def read_data() -> dict[str, dict[str, tuple[int, int, float]]]:
    values: dict[str, dict[str, tuple[int, int, float]]] = defaultdict(dict)
    rows = load()
    if {r["year"] for r in rows} != {interval[:4] for interval in INTERVALS}:
        raise ValueError("Unexpected publication years in RQ2 data")
    audit = []
    for interval in INTERVALS:
        papers = [r for r in rows if r["year"] == interval[:4]]
        for component in ORDER:
            members = [r["record_id"] for r in papers if component in components(r["engineering_components"])]
            n, d = len(members), len(papers)
            values[component][interval] = (n, d, 100 * n / d)
            audit.append(dict(publication_interval=interval, component=component,
                              paper_count=n, paper_denominator=d,
                              within_interval_percentage=f"{100*n/d:.1f}",
                              paper_ids="; ".join(sorted(members))))
    write(AUDIT / "responsibility_evolution_data.csv", audit)
    return values


def validate(values: dict[str, dict[str, tuple[int, int, float]]]) -> None:
    missing = [
        (component, interval)
        for component in ORDER
        for interval in INTERVALS
        if interval not in values[component]
    ]
    if missing:
        raise ValueError(f"Missing interval-component observations: {missing}")

    for interval in INTERVALS:
        denominator = values[ORDER[0]][interval][1]
        observed = {values[component][interval][1] for component in ORDER}
        if observed != {denominator}:
            raise ValueError(
                f"Unexpected denominator for {interval}: {sorted(observed)}"
            )


def main() -> None:
    values = read_data()
    validate(values)
    rows = load()
    overall = {
        component: sum(
            component in components(row["engineering_components"]) for row in rows
        )
        for component in ORDER
    }
    denominator = len(rows)
    if denominator != 154:
        raise ValueError(f"Unexpected proposed-system denominator: {denominator}")
    write(
        AUDIT / "responsibility_overall_data.csv",
        [
            dict(
                component=component,
                system_count=overall[component],
                system_denominator=denominator,
                system_percentage=f"{100 * overall[component] / denominator:.1f}",
            )
            for component in ORDER
        ],
    )
    percentages = np.array(
        [
            [values[component][interval][2] for interval in INTERVALS]
            for component in ORDER
        ]
    )

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "font.size": 10.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    # A truncated sequential blue scale keeps high-prevalence cells saturated
    # while avoiding near-white and near-black extremes in print.
    base = plt.get_cmap(CMAP_NAME)
    cmap = LinearSegmentedColormap.from_list(
        "journal_blues", base(np.linspace(*CMAP_RANGE, 256))
    )
    norm = Normalize(vmin=0, vmax=100)

    fig = plt.figure(figsize=(7.35, 4.35))
    grid = fig.add_gridspec(1, 2, width_ratios=(0.92, 1.08), wspace=0.25)
    bar_ax = fig.add_subplot(grid[0, 0])
    ax = fig.add_subplot(grid[0, 1])

    overall_percentages = np.array([100 * overall[component] / denominator for component in ORDER])
    # Bars take the heat-map colour of their percentage, so both panels share one encoding.
    bar_ax.barh(
        np.arange(len(ORDER)),
        overall_percentages,
        color=[cmap(norm(value)) for value in overall_percentages],
        edgecolor="#1F2F3D",
        linewidth=0.9,
        height=0.62,
        zorder=3,
    )
    bar_ax.set_facecolor("#FAFBFC")
    bar_ax.set_xlim(0, 124)
    bar_ax.set_ylim(len(ORDER) - 0.5, -0.5)
    bar_ax.set_yticks(np.arange(len(ORDER)), [rf"$\bf{{{component}}}$" for component in ORDER])
    bar_ax.set_xticks((0, 25, 50, 75, 100))
    bar_ax.set_xlabel("Systems containing component (%)", fontsize=9.2, labelpad=6)
    bar_ax.tick_params(axis="x", length=3, width=0.8, color="#394F60", labelsize=9.8)
    bar_ax.tick_params(axis="y", length=0, pad=7, labelsize=8.8)
    bar_ax.grid(axis="x", color="#C9D3DB", linewidth=0.6, linestyle=(0, (3, 3)), zorder=0)
    bar_ax.set_axisbelow(True)
    for spine in bar_ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#394F60")
        spine.set_linewidth(1.0)
    bar_ax.spines["right"].set_visible(False)  # value labels reach the right edge
    for row, component in enumerate(ORDER):
        bar_ax.text(
            overall_percentages[row] + 1.2,
            row,
            f"{overall[component]} ({overall_percentages[row]:.1f}%)",
            ha="left",
            va="center",
            fontsize=8.7,
            color="#172734",
            zorder=4,
            bbox=dict(facecolor="#FAFBFC", edgecolor="none", pad=0.6),  # keep grid lines off the labels
        )
    bar_ax.text(
        0.5,
        -0.18,
        "(a) Overall prevalence",
        transform=bar_ax.transAxes,
        ha="center",
        va="top",
        fontsize=9.0,  # same panel-label style as Fig. 5
    )
    for row in range(len(ORDER)):
        for column in range(len(INTERVALS)):
            ax.add_patch(
                Rectangle(
                    (column - 0.5, row - 0.5),
                    1,
                    1,
                    facecolor=cmap(norm(percentages[row, column])),
                    edgecolor="white",
                    linewidth=2.0,
                )
            )

    ax.set_xlim(-0.5, len(INTERVALS) - 0.5)
    ax.set_ylim(len(ORDER) - 0.5, -0.5)
    # Report each interval's denominator once, not in every heat-map cell.
    interval_labels = [
        f"{interval[:4]}\n$(n={values[ORDER[0]][interval][1]})$"
        for interval in INTERVALS
    ]
    ax.set_xticks(
        range(len(INTERVALS)),
        interval_labels,
        fontsize=10.6,
    )
    ax.set_yticks(
        range(len(ORDER)),
        [rf"$\bf{{{component}}}$" for component in ORDER],
        fontsize=10.5,
    )
    ax.tick_params(axis="x", length=0, pad=9)
    ax.tick_params(axis="y", length=0, pad=9)
    for spine in ax.spines.values():
        spine.set_visible(False)

    for row, component in enumerate(ORDER):
        for column, interval in enumerate(INTERVALS):
            count, _, percentage = values[component][interval]
            red, green, blue, _ = cmap(norm(percentage))
            luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
            text_colour = "#FFFFFF" if luminance < 0.53 else "#162633"
            ax.text(
                column,
                row - 0.13,
                f"{count}",
                ha="center",
                va="center",
                color=text_colour,
                fontsize=10.0,
            )
            ax.text(
                column,
                row + 0.19,
                f"{percentage:.1f}%",
                ha="center",
                va="center",
                color=text_colour,
                fontsize=10.7,
                fontweight="bold",
            )

    # A single outline directs attention to G's cross-interval change without
    # changing the percentage colour scale or introducing a third panel.
    governance_row = ORDER.index("G")
    ax.add_patch(
        Rectangle(
            (-0.5, governance_row - 0.5),
            len(INTERVALS),
            1,
            fill=False,
            edgecolor="#394F60",
            linewidth=1.25,
            clip_on=False,
            zorder=4,
        )
    )

    colour_scale = ScalarMappable(norm=norm, cmap=cmap)
    colour_scale.set_array([])
    colour_bar = fig.colorbar(colour_scale, ax=ax, fraction=0.035, pad=0.045)
    colour_bar.solids.set_rasterized(False)  # keep the colour bar vector so it stays sharp in print
    colour_bar.set_ticks((0, 20, 40, 60, 80, 100))
    colour_bar.ax.tick_params(labelsize=9.5, length=3)
    colour_bar.set_label("Prevalence (%)", fontsize=9.4, labelpad=7)
    colour_bar.outline.set_linewidth(0.7)
    colour_bar.outline.set_edgecolor("#6F7F89")
    ax.text(
        0.5,
        -0.18,
        "(b) By publication year",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9.0,
    )

    fig.subplots_adjust(left=0.03, right=0.97, top=0.96, bottom=0.25)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(PREVIEW, dpi=280, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"written {OUTPUT.name}")


if __name__ == "__main__":
    main()
