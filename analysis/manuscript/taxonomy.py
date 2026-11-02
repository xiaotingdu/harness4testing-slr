"""Generate the primary-task taxonomy figure of the 154-paper corpus.

Corpus -> primary testing task -> included papers; every paper appears exactly once.
Reference numbers are read from the compiled paper (main.aux). Run from the repository root:
    python figures/taxonomy.py
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch


HERE = Path(__file__).resolve().parent
CORPUS = HERE.parent / "tools" / "corpus_154.csv"
AUXILIARY = HERE.parent / "main.aux"
if not AUXILIARY.exists():
    AUXILIARY = HERE.parent / "build" / "main.aux"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "pdf.fonttype": 42,
    "axes.unicode_minus": False,
})

# One ColorBrewer Set2 colour per primary task; the root connects directly to
# the six primary tasks.
TASK_COLOURS = {
    "unit_test_generation": "#8DA0CB",
    "test_oracle_generation": "#FFD92F",
    "system_test_input_generation": "#66C2A5",
    "bug_analysis": "#E78AC3",
    "debugging": "#A6D854",
    "program_repair": "#FC8D62",
}

TASKS = [
    ("unit_test_generation", "Unit-test\ngeneration", 32),
    ("test_oracle_generation", "Test-oracle\ngeneration", 6),
    ("system_test_input_generation", "System-test-input\ngeneration", 53),
    ("bug_analysis", "Bug analysis", 5),
    ("debugging", "Debugging", 16),
    ("program_repair", "Program repair", 42),
]
TOTAL = 154

PAPER_COLUMNS = 3
PAPER_FONT_SIZE = 6.0
PAPER_FONT = FontProperties(family="DejaVu Serif", size=PAPER_FONT_SIZE)


def tint(hex_color: str, share: float) -> tuple[float, float, float]:
    """Mix a colour with white; share=1 returns the original colour."""
    value = hex_color.lstrip("#")
    rgb = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(1 - (1 - channel) * share for channel in rgb)


def fitted_label(name: str, reference: str, max_width_points: float) -> str:
    """Fit a paper label and its reference number inside one list column."""
    clean = re.sub(r"\s+", " ", name).strip()
    marker = "†" if clean.endswith("†") else ""
    clean = clean.removesuffix("†")
    suffix = f"{marker} [{reference}]"

    def rendered_width(value: str) -> float:
        width, _, _ = PAPER_RENDERER.get_text_width_height_descent(
            "• " + value + suffix, PAPER_FONT, ismath=False,
        )
        return width

    if rendered_width(clean) <= max_width_points:
        return clean + suffix
    while clean and rendered_width(clean + "…") > max_width_points:
        clean = clean[:-1].rstrip()
    return clean + "…" + suffix


with CORPUS.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
aux_text = AUXILIARY.read_text(encoding="utf-8")
key_numbers = dict(re.findall(r"\\bibcite\{([^}]+)\}\{\{(\d+)\}", aux_text))
missing = sorted({row["bib_key"] for row in rows} - set(key_numbers))
if missing:
    raise ValueError("compiled paper has no reference number for: " + ", ".join(missing))

assert len(rows) == TOTAL, f"expected {TOTAL} papers, found {len(rows)}"
by_task: dict[str, list[dict[str, str]]] = {task: [] for task, _, _ in TASKS}
for row in rows:
    by_task[row["task"]].append(row)
for task, _, expected in TASKS:
    assert len(by_task[task]) == expected, (task, len(by_task[task]), expected)
    by_task[task].sort(key=lambda row: row["label"].casefold())


def figure_label(row: dict[str, str]) -> str:
    return row["label"] + ("†" if row["descriptive"] == "yes" else "")


# Portrait layout: root -> six tasks -> paper-title leaves.
fig, ax = plt.subplots(figsize=(8.25, 10.35))
PAPER_RENDERER = fig.canvas.get_renderer()
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

TOP, BOTTOM = 0.965, 0.035
ROOT_X, ROOT_W = 0.008, 0.042
TASK_X, TASK_W = 0.080, 0.146
PAPER_X, PAPER_RIGHT = 0.240, 0.996
ROW_GAP = 0.006
PAPER_TEXT = "#23313B"
CONNECTOR = "#5A5A5A"


def rounded_box(x0: float, y0: float, width: float, height: float,
                face, edge, linewidth: float = 0.75,
                radius: float = 0.006, zorder: int = 2) -> None:
    ax.add_patch(FancyBboxPatch(
        (x0, y0), width, height,
        boxstyle=f"round,pad=0.0025,rounding_size={radius}",
        fc=face, ec=edge, lw=linewidth, zorder=zorder,
    ))


line_counts = {
    task: (len(by_task[task]) + PAPER_COLUMNS - 1) // PAPER_COLUMNS
    for task, _, _ in TASKS
}
total_lines = sum(line_counts.values())
usable_h = TOP - BOTTOM - ROW_GAP * (len(TASKS) - 1)
line_h = usable_h / total_lines

task_geometry: dict[str, tuple[float, float, float]] = {}
y_top = TOP
for task, _, _ in TASKS:
    row_h = line_counts[task] * line_h
    y0 = y_top - row_h
    task_geometry[task] = (y0, y_top, (y0 + y_top) / 2)
    y_top = y0 - ROW_GAP

# Root node and its branch to the six task nodes.
root_y = (BOTTOM + TOP) / 2
rounded_box(ROOT_X, root_y - 0.150, ROOT_W, 0.300,
            tint("#4C6584", 0.10), "#4C6584", 0.9, 0.008)
ax.text(ROOT_X + ROOT_W / 2, root_y,
        f"LLM-Based Testing Harnesses ({TOTAL} papers)",
        rotation=90, ha="center", va="center", fontsize=6.7,
        fontweight="bold", color="#25364A")

task_mids = [task_geometry[task][2] for task, _, _ in TASKS]
root_spine_x = 0.064
ax.plot([ROOT_X + ROOT_W, root_spine_x], [root_y, root_y],
        color=CONNECTOR, lw=0.72, zorder=0)
ax.plot([root_spine_x, root_spine_x], [min(task_mids), max(task_mids)],
        color=CONNECTOR, lw=0.72, zorder=0)

for task, display_name, expected in TASKS:
    y0, y1, y_mid = task_geometry[task]
    row_h = y1 - y0
    ax.plot([root_spine_x, TASK_X], [y_mid, y_mid],
            color=CONNECTOR, lw=0.72, zorder=0)

    task_h = min(0.058, max(0.040, row_h - 0.008))
    rounded_box(TASK_X, y_mid - task_h / 2, TASK_W, task_h,
                tint(TASK_COLOURS[task], 0.12), TASK_COLOURS[task], 0.82, 0.006)
    ax.text(TASK_X + TASK_W / 2, y_mid + 0.006,
            display_name, ha="center", va="center", fontsize=5.45,
            fontweight="bold", linespacing=0.90, color="#202020")
    ax.text(TASK_X + TASK_W / 2, y_mid - task_h / 2 + 0.008,
            f"{expected} papers", ha="center", va="center",
            fontsize=5.05, color="#555555")

    ax.plot([TASK_X + TASK_W, PAPER_X], [y_mid, y_mid],
            color=TASK_COLOURS[task], lw=0.72, zorder=0)
    rounded_box(PAPER_X, y0 + 0.002, PAPER_RIGHT - PAPER_X,
                row_h - 0.004, tint(TASK_COLOURS[task], 0.04), TASK_COLOURS[task], 0.62, 0.005)

    papers = by_task[task]
    lines = line_counts[task]
    col_w = (PAPER_RIGHT - PAPER_X - 0.016) / PAPER_COLUMNS
    label_width_points = (col_w - 0.012) * fig.get_figwidth() * 72
    for index, paper in enumerate(papers):
        column = index // lines
        line = index % lines
        x = PAPER_X + 0.008 + column * col_w
        y = y1 - (line + 0.5) * (row_h / lines)
        reference = key_numbers[paper["bib_key"]]
        label = fitted_label(figure_label(paper), reference, label_width_points)
        ax.text(x, y, "• " + label,
                ha="left", va="center", fontsize=PAPER_FONT_SIZE,
                color=PAPER_TEXT)

ax.text(0.505, 0.012,
        "Reported method or system names are used where available; \N{DAGGER} marks a descriptive label, and bracketed numbers refer to the bibliography.",
        ha="center", va="center", fontsize=5.7, color="#555555",
        style="italic")

fig.savefig(HERE / "taxonomy.pdf", bbox_inches="tight", pad_inches=0.018)
fig.savefig(HERE / "taxonomy_preview.png", dpi=240,
            bbox_inches="tight", pad_inches=0.018)
print("written taxonomy.pdf / taxonomy_preview.png")
