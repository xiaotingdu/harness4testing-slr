# -*- coding: utf-8 -*-
"""Generate the task-distribution figure from the 154-paper task classifications."""

import csv
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "tools" / "corpus_154.csv"


plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

TOTAL = 154
TASKS = [
    ("system_test_input_generation", "System-test-input generation"),
    ("program_repair", "Program repair"),
    ("unit_test_generation", "Unit-test generation"),
    ("debugging", "Debugging"),
    ("test_oracle_generation", "Test-oracle generation"),
    ("bug_analysis", "Bug analysis"),
]
# Same per-task ColorBrewer Set2 colours as the taxonomy figure.
TASK_COLOURS = {
    "Unit-test generation": "#8DA0CB",
    "Test-oracle generation": "#FFD92F",
    "System-test-input generation": "#66C2A5",
    "Bug analysis": "#E78AC3",
    "Debugging": "#A6D854",
    "Program repair": "#FC8D62",
}

with DATA.open(encoding="utf-8-sig", newline="") as handle:
    corpus = list(csv.DictReader(handle))
if len(corpus) != TOTAL:
    raise ValueError(f"Expected {TOTAL} papers, found {len(corpus)}")

task_counts = {
    raw_task: sum(row["task"] == raw_task for row in corpus)
    for raw_task, _ in TASKS
}
if sum(task_counts.values()) != TOTAL:
    raise ValueError("Task counts do not cover the full corpus exactly once")

# ``barh`` draws the first entry at the bottom, so reverse the descending
# ranking to display the largest category at the top of the finished figure.
ranked_tasks = sorted(
    ((display_task, task_counts[raw_task]) for raw_task, display_task in TASKS),
    key=lambda item: item[1],
    reverse=True,
)
labels = [display_task for display_task, _ in ranked_tasks][::-1]
counts = [count for _, count in ranked_tasks][::-1]


fig, ax = plt.subplots(figsize=(6.8, 3.25))
bars = ax.barh(
    labels,
    counts,
    color=[TASK_COLOURS[label] for label in labels],
    edgecolor="white",
    linewidth=0.8,
    height=0.62,
)

for bar, count in zip(bars, counts):
    ax.text(
        count + 0.8,
        bar.get_y() + bar.get_height() / 2,
        f"{count} ({100 * count / TOTAL:.1f}%)",
        va="center",
        ha="left",
        fontsize=7.5,
        color="#333333",
    )

ax.set_xlabel("Number of included studies ($N=154$)")
ax.set_xlim(0, 62)
ax.xaxis.grid(True, color="#E4E4E4", linewidth=0.6)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color("#8A8A8A")
ax.spines["bottom"].set_linewidth(0.7)
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", colors="#4A4A4A", width=0.6)
ax.tick_params(axis="y", colors="#222222")

fig.tight_layout(pad=0.4)
fig.savefig(HERE / "task_distribution.pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig(
    HERE / "task_distribution_preview.png",
    dpi=180,
    bbox_inches="tight",
    pad_inches=0.02,
)
