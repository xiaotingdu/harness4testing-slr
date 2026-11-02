"""Generate the combination-by-task table for Section 6.1.

The five most frequent combinations are listed individually and the rest are
merged into one row. Input: tools/proposed_system_components_154.csv.
Output: tables/combination_task.tex.
Run from the repository root: python tools/build_combination_task_table.py
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ROOT / "tools" / "proposed_system_components_154.csv"
OUT = ROOT / "tables" / "combination_task.tex"
TOP = 5

TASKS = [
    ("unit_test_generation", "UT"),
    ("test_oracle_generation", "OR"),
    ("system_test_input_generation", "STI"),
    ("bug_analysis", "BA"),
    ("debugging", "DBG"),
    ("program_repair", "PR"),
]

with SYSTEMS.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
if len(rows) != 154:
    raise ValueError(f"Expected 154 systems, found {len(rows)}")

overall = Counter(row["engineering_components"] for row in rows)
top = [combo for combo, _ in sorted(overall.items(), key=lambda item: (-item[1], item[0]))[:TOP]]
cells = Counter((row["engineering_components"] if row["engineering_components"] in top else "other",
                 row["task"]) for row in rows)
task_totals = Counter(row["task"] for row in rows)


def line(label: str, key: str) -> str:
    counts = [cells[(key, task)] for task, _ in TASKS]
    return f"{label} & " + " & ".join(str(c) for c in counts) + f" & {sum(counts)} \\\\"


others = len(overall) - TOP
lines = [
    r"\begin{table}[!t]",
    r"\centering",
    r"\small",
    r"\caption{Systems using each component combination by software-testing task. UT: unit-test generation;"
    r" OR: test-oracle generation; STI: system-test-input generation; BA: bug analysis; DBG: debugging;"
    r" PR: program repair.}",
    r"\label{tab:combination-task}",
    r"\begin{tabular}{@{}lrrrrrrr@{}}",
    r"\toprule",
    "Combination & " + " & ".join(abbr for _, abbr in TASKS) + r" & Total \\",
    r"\midrule",
]
lines += [line(f"\\texttt{{{combo}}}", combo) for combo in top]
lines.append(line(f"Other {others} combinations", "other"))
lines.append(r"\midrule")
lines.append("Total & " + " & ".join(str(task_totals[task]) for task, _ in TASKS) + f" & {len(rows)} \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
OUT.write_text("\n".join(lines), encoding="utf-8")
print("written", OUT.name)
