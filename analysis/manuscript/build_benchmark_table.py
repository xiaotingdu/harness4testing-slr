"""Generate Table tab:benchmarks (public benchmarks by testing task) for Section 7.1.

Inputs: tools/benchmark_families_154.csv (benchmark families with per-task system
counts and record IDs) and tools/proposed_system_components_154.csv (task of each
system). Output: tables/benchmark_inventory_full.tex.
Run from the repository root: python tools/build_benchmark_table.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ROOT / "tools" / "benchmark_families_154.csv"
SYSTEMS = ROOT / "tools" / "proposed_system_components_154.csv"
OUT = ROOT / "tables" / "benchmark_inventory_full.tex"

TASKS = [
    ("unit_test_generation", "Unit-test generation"),
    ("test_oracle_generation", "Test-oracle generation"),
    ("system_test_input_generation", "System-test-input generation"),
    ("bug_analysis", "Bug analysis"),
    ("debugging", "Debugging"),
    ("program_repair", "Program repair"),
]

# Display name and source citation of each family; None means no citable source paper.
SOURCE = {
    "Defects4J": ("Defects4J", "just2014defects4j"),
    "SWE-bench (all variants)": ("SWE-bench", "jimenez2024swebench"),
    "HumanEval": ("HumanEval", "chen2021humaneval"),
    "QuixBugs": ("QuixBugs", "lin2017quixbugs"),
    "Themis": ("Themis", "su2021themis"),
    "CodaMosa benchmark": ("CodaMosa benchmark", "lemieux2023codamosa"),
    "ARVO": ("ARVO", "mei2024arvo"),
    "AndroR2": ("AndroR2", "wendland2021andror2"),
    "BugsInPy": ("BugsInPy", "widyasari2020bugsinpy"),
    "ReCDroid dataset": ("ReCDroid", "zhao2019recdroid"),
    "ConDefects": ("ConDefects", "wu2023condefects"),
    "EvoMaster benchmark (EMB)": ("EMB", "arcuri2023emb"),
    "FrUITeR dataset": ("FrUITeR", "zhao2020fruiter"),
    "GHRB": ("GHRB", "lee2024ghrb"),
    "GitBug-Java": ("GitBug-Java", "silva2024gitbugjava"),
    "GrowingBugs": ("GrowingBugs", None),
    "HITS dataset": ("HITS dataset", "wang2024hits"),
    "IDoFT": ("IDoFT", "lam2019idflakies"),
    "LeetCode-Java": ("LeetCode-Java", None),
    "MAGMA": ("Magma", "hazimeh2020magma"),
    "RWB": ("RWB", None),
    "SWT-bench": ("SWT-bench", "mundler2024swtbench"),
    "ScopeDroid dataset": ("ScopeDroid", "huang2023scopedroid"),
    "SmartBugs-curated": ("SmartBugs-Curated", "durieux2020smartbugs"),
    "TDD-Bench": ("TDD-Bench", "ahmed2024tddbench"),
    "VUL4J": ("Vul4J", "bui2022vul4j"),
    "AFLGo dataset": ("AFLGo benchmark", "bohme2017aflgo"),
    "BugBench": ("BugBench", None),
    "BugsC++": ("BugsC++", "an2023bugscpp"),
    "CraftDroid dataset": ("CraftDroid", "lin2019craftdroid"),
    "CyberGym": ("CyberGym", "wang2025cybergym"),
    "DS-1000": ("DS-1000", "lai2023ds1000"),
    "DebugBench": ("DebugBench", "tian2024debugbench"),
    "FuzzBench": ("FuzzBench", "metzman2021fuzzbench"),
    "LocBench": ("LocBench", "chen2025locagent"),
    "MoTIF": ("MoTIF", "burns2022motif"),
    "OSS-Fuzz": ("OSS-Fuzz", None),
    "Refactory": ("Refactory", "hu2019refactory"),
    "SecBench.js": ("SecBench.js", "bhuiyan2023secbenchjs"),
    "TECO dataset": ("TeCo", "nie2023teco"),
    "TypeBugs": ("TypeBugs", "oh2022pyter"),
    "UNIFUZZ": ("UNIFUZZ", "li2021unifuzz"),
    "VJBench": ("VJBench", "wu2023vjbench"),
    "VulnLoc": ("VulnLoc", "shen2021vulnloc"),
    "xCodeEval": ("xCodeEval", "khan2024xcodeeval"),
    # Families added by the 2026-11-02 benchmark review.
    "ysoserial": ("ysoserial", "frohoff2025ysoserial"),
    "Gleipner": ("Gleipner", "kreyssig2025gleipner"),
    "TARBENCH": ("TARBENCH", "yaraghi2025target"),
    "Odin dataset": ("Odin dataset", "xiong2023odin"),
    "RegDroid dataset": ("RegDroid dataset", "wang2022regdroid"),
    "UQ-AAS21": ("UQ-AAS21", "xie2023uqaas21"),
    "Imtiaz et al. web test repair dataset": ("Imtiaz et al.\\ web-test-repair dataset", "imtiaz2021webrepair"),
    "Benchmark-C (program reduction)": ("Benchmark-C", "tian2023caching,xu2023pushing,zhang2023ppr"),
    "Benchmark-Rust (program reduction)": ("Benchmark-Rust", "xu2023pushing"),
    "Slither/SoMo/SPCon labelled cases": ("Slither/SoMo/SPCon labelled cases", "feist2019slither,fang2023somo,liu2022spcon"),
    "SIR": ("SIR", "do2005sir"),
    "Pecan benchmarks": ("Pecan benchmarks", "pecan2011"),
    "JaConTeBe": ("JaConTeBe", "jacontebe2016"),
    "PFix benchmarks": ("PFix benchmarks", "pfix2018"),
    "Sorald dataset": ("Sorald dataset", "etemadi2023sorald"),
    "ACPR": ("ACPR", "dai2025acpr"),
    "SAVER dataset": ("SAVER dataset", "hong2020saver"),
    "ERAP": ("ERAP", "rodler2018sereum"),
    "ESC": ("ESC", "yu2021deescvhunter"),
    "ReentrancyStudy-Data": ("ReentrancyStudy-Data", "zheng2023rsd"),
    "All Things Reentrancy": ("All Things Reentrancy", "atr2024"),
    "Solidity Security by Example": ("Solidity Security by Example", "sse2024"),
    "TEMdroid dataset": ("TEMdroid dataset", "temdroid2025"),
    "TransformedD4J": ("TransformedD4J", "lecong2025transformedd4j"),
    "Ye et al. dataset": ("Ye et al.\\ dataset", "ye2015mapping"),
    "SelectFuzz dataset": ("SelectFuzz dataset", "luo2023selectfuzz"),
    "DAFL dataset": ("DAFL dataset", "kim2023dafl"),
    "GIFdroid suite": ("GIFdroid suite", "feng2022gifdroid"),
    "V2S recordings": ("V2S recordings", "bernalcardenas2020v2s"),
    "AndroTest": ("AndroTest", "choudhary2015androtest"),
}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


families = read(FAMILIES)
systems = read(SYSTEMS)
missing = sorted({row["family"] for row in families} - SOURCE.keys())
if missing:
    raise ValueError(f"No display entry for: {missing}")

task_of = {row["record_id"]: row["task"] for row in systems}

lines = [
    r"\begin{table}[!htbp]",
    r"\centering",
    r"\small",
    r"\caption{Public benchmarks and datasets used by the 154 proposed systems, by software-testing task."
    r" Numbers in parentheses give the systems that use each benchmark.}",
    r"\label{tab:benchmarks}",
    r"\setlength{\tabcolsep}{4pt}",
    r"\renewcommand{\arraystretch}{1.08}",
    r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.24\linewidth}",
    r"                    >{\raggedright\arraybackslash}p{\dimexpr0.76\linewidth-8pt\relax}@{}}",
    r"\toprule",
    r"Software-testing task & Public benchmarks and datasets (systems) \\",
    r"\midrule",
]
for index, (task, label) in enumerate(TASKS):
    used = [(int(row[task]), row["family"]) for row in families if int(row[task]) > 0]
    used.sort(key=lambda item: (-item[0], SOURCE[item[1]][0].lower()))
    cells = []
    for count, family in used:
        name, key = SOURCE[family]
        cells.append(f"{name}~\\cite{{{key}}} ({count})" if key else f"{name} ({count})")
    in_task = [rid for rid, t in task_of.items() if t == task]
    body = "; ".join(cells) if cells else "None"
    lines.append(f"{label} ($n={len(in_task)}$)")
    lines.append(f"  & {body}. \\\\")
    if index < len(TASKS) - 1:
        lines.append(r"\addlinespace[4pt]")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
OUT.write_text("\n".join(lines), encoding="utf-8")
print("written", OUT.name)
