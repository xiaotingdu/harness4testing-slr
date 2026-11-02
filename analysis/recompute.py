"""Recompute the data-derived numbers of the survey on the final 154-paper coded corpus (version 2).

Version 2 applies the first author's choice for every root cause of version 1 (see ROOT_CAUSES at the end):
six task categories; paper-level presence = union over the paper's own HCs plus the m1 proposed system;
directional matched comparisons = direction gain/loss/mixed; all primary claims with merged effectiveness;
metric families from m1 metric_classes and primary-claim properties; evidence items without statistical tests;
baseline HC counts removed; relation rates as coded; current dates; PACMSE split by Crossref (pacmse_split.py);
PRISMA with a venue-eligibility box; agreement statistics reported; timeline to be re-authored; all SWE-bench
variants merged into one family.

Inputs (read only):
  search_redo_2026/09_coding/final/m1_final.jsonl, m2_final.jsonl
  search_redo_2026/07_fulltext/ft_included.csv, 06_screening/record_ids.csv
  search_redo_2026/02_exports/v2/first_public_dates.csv, arxiv_v2.csv
  search_redo_2026/08_prisma/prisma_counts_20261026.txt, 07_fulltext/ta_stage_counts.txt
  search_redo_2026/09_coding/verify_stats_full.txt (mode-2 pass rates)
  search_redo_2026/10_recompute/tables/pacmse_split.csv (written by pacmse_split.py)
  temp/number_inventory.tsv, overleaf-paper/tools/timeline_milestones.csv

Outputs (search_redo_2026/10_recompute/): new_old_numbers.xlsx (sheets Numbers, Issues) and tables/*.csv.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SR = HERE.parent                      # search_redo_2026
ROOT = SR.parent                      # project root
TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)

COMPS = list("ETCLOVG")
TASKS = ["unit_test_generation", "test_oracle_generation", "system_test_input_generation",
         "bug_analysis", "debugging", "program_repair"]
# Testing-objective families of the taxonomy figure: construct/execute testing artefacts versus use testing
# evidence to analyse or resolve failures (main.tex l.210-213); the six categories map onto them one-to-one.
FAMILIES = {"construct or execute testing artefacts": TASKS[:3], "analyse or resolve failures": TASKS[3:]}
REL = {"C01": "TE", "C02": "VL", "C03": "LT", "C04": "LE", "C05": "CL", "C06": "GT", "C07": "GE", "C08": "GL",
       "D01": "EC", "D02": "EV", "D03": "VC", "D04": "OC", "D05": "OV", "D06": "TO", "D07": "EO", "D08": "VO"}
NAMES = {"E": "Execution", "T": "Tool Interface", "C": "Context", "L": "Lifecycle", "O": "Observability",
         "V": "Verification", "G": "Governance"}


def pct(n, d, nd=1):
    return f"{100.0 * n / d:.{nd}f}%" if d else "n/a"


def pv(n, d):
    return 100.0 * n / d if d else 0.0


def write(df: pd.DataFrame, name: str):
    df.to_csv(TAB / name, index=False, encoding="utf-8-sig")


# ---------------------------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------------------------
m1 = [json.loads(line) for line in open(SR / "09_coding/final/m1_final.jsonl", encoding="utf-8")]
m2 = {json.loads(line)["record_id"]: json.loads(line)
      for line in open(SR / "09_coding/final/m2_final.jsonl", encoding="utf-8")}
inc = pd.read_csv(SR / "07_fulltext/ft_included.csv", encoding="utf-8-sig")
N = len(m1)
ids = [r["record_id"] for r in m1]
assert N == 154 and set(ids) == set(inc.record_id) == set(m2), "corpus mismatch between m1, m2 and ft_included"
task_of = {r["record_id"]: r["task"] for r in m1}
sysname = {r["record_id"]: r["system_name"] for r in m1}

# Proposed-system view (m1)
present = {r["record_id"]: {c for c in COMPS if r["components"][c]["status"] == "present"} for r in m1}
signature = {k: "".join(c for c in COMPS if c in v) for k, v in present.items()}


def hc_letters(s) -> set:
    """Component letters of an m2 HC string; 'no-llm', 'not_reported' and '' contribute nothing."""
    return {x for x in str(s).split("+") if x in COMPS}


# Paper-level view: union over all of the paper's own HCs in m2, always including the m1 proposed system
paper_present = {k: set(present[k]).union(*[hc_letters(h["components"]) for h in m2[k]["hcs"]]) for k in ids}

# ---------------------------------------------------------------------------------------------
# 2. Publication dates and venues
# ---------------------------------------------------------------------------------------------
# Accepted rule: DOI first public date of the formal record (first_public_dates.csv), else arXiv first submission.
rid_doi = pd.read_csv(SR / "06_screening/record_ids.csv", encoding="utf-8-sig").set_index("record_id")["doi"]
fpd = pd.read_csv(SR / "02_exports/v2/first_public_dates.csv", encoding="utf-8-sig", keep_default_na=False)
doi_date = {str(r.key).lower(): r.first_public for r in fpd.itertuples() if r.source != "arXiv"}
arx = pd.read_csv(SR / "02_exports/v2/arxiv_v2.csv", encoding="utf-8-sig")
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
arx_by_title = {norm(t): str(p)[:10] for t, p in zip(arx.title, arx.published)}
date_rows = []
for rid, title in zip(inc.record_id, inc.title):
    doi = str(rid_doi.get(rid, "")).lower()
    if doi_date.get(doi):
        d, src = doi_date[doi], "DOI first public date of the formal record"
    elif norm(title) in arx_by_title:
        d, src = arx_by_title[norm(title)], "arXiv first submission (formal record has no dated DOI)"
    else:
        d, src = "", "missing"
    y, mth = (int(d[:4]), int(d[5:7])) if d else (None, None)
    date_rows.append({"record_id": rid, "system_name": sysname[rid], "task": task_of[rid], "date": d, "year": y,
                      "month": mth, "half_year": f"{y} H{1 if mth <= 6 else 2}" if d else "", "date_source": src})
dates = pd.DataFrame(date_rows)
write(dates, "publication_dates.csv")
year_of = dict(zip(dates.record_id, dates.year))
n_date_fallback = int((dates.date_source != "DOI first public date of the formal record").sum())
# Timeline reference (rows to be re-authored): new-corpus papers per publication interval with system names
write(dates.sort_values(["year", "date"])[["year", "date", "record_id", "system_name", "task"]],
      "timeline_reference_by_interval.csv")

# PACMSE split (public Crossref metadata; pacmse_split.py)
pac = pd.read_csv(TAB / "pacmse_split.csv", encoding="utf-8-sig", keep_default_na=False).set_index("record_id")
pac_unresolved = [k for k, v in pac.issue.items() if v not in ("FSE", "ISSTA")]


def norm_venue(rid: str, v: str) -> str:
    """Short outlet label for ft_included venue strings; PACMSE papers are split by Crossref issue."""
    s = v.lower()
    if "pacmse" in s or "proceedings of the acm on software engineering" in s:
        iss = pac.issue.get(rid, "")
        return iss if iss in ("FSE", "ISSTA") else "PACMSE (unresolved)"
    if "issta" in s or "software testing and analysis" in s:
        return "ISSTA"
    if "ase (journal)" in s:
        return "ASE journal"
    if "automated software engineering" in s or re.search(r"\base\b", s):
        return "ASE"
    if "transactions on software engineering and methodology" in s or "tosem" in s:
        return "TOSEM"
    if "transactions on software engineering" in s or re.search(r"\btse\b", s):
        return "TSE"
    if "icse" in s or "international conference on software engineering" in s:
        return "ICSE"
    if "icst" in s or "software testing, verification and validation" in s:
        return "ICST"
    for key, lab in [("saner", "SANER"), ("icsme", "ICSME"), ("iet software", "IET Software"), ("emse", "EMSE"),
                     ("journal of systems and software", "JSS"), ("jss", "JSS"), ("ist", "IST")]:
        if key in s:
            return lab
    return "UNMAPPED:" + v


inc["outlet"] = [norm_venue(r, v) for r, v in zip(inc.record_id, inc.venue)]
venue_counts = inc.outlet.value_counts()
write(venue_counts.rename_axis("outlet").reset_index(name="papers"), "venue_counts.csv")
assert not any(o.startswith("UNMAPPED") for o in venue_counts.index), venue_counts
vc = lambda o: int(venue_counts.get(o, 0))
# Old figure rule (figures/corpus_distribution_panels.py l.176): outlets with fewer than 3 papers form "Other venues"
other_venues = {o: int(n) for o, n in venue_counts.items() if n < 3}

# ---------------------------------------------------------------------------------------------
# 3. Tasks, presence (both views), signatures, co-presence
# ---------------------------------------------------------------------------------------------
task_n = Counter(task_of.values())
write(pd.DataFrame([{"task": t, "family": next(f for f, ts in FAMILIES.items() if t in ts), "papers": task_n[t],
                     "share": pct(task_n[t], N)} for t in TASKS]
                   + [{"task": "TOTAL", "family": "", "papers": sum(task_n.values()), "share": pct(N, N)}]),
      "task_distribution.csv")
fam_size = {f: sum(task_n[t] for t in ts) for f, ts in FAMILIES.items()}


def presence_counts(view):
    return {c: sum(c in view[k] for k in ids) for c in COMPS}


comp_n = presence_counts(present)            # proposed-system view
pcomp_n = presence_counts(paper_present)     # paper-level view
gap = {c: pv(pcomp_n[c], N) - pv(comp_n[c], N) for c in COMPS}
gap_max_c = max(COMPS, key=lambda c: gap[c])
gaps_le_1_5 = [c for c in COMPS if gap[c] <= 1.5 + 1e-9]
order_prop = sorted(COMPS, key=lambda c: -comp_n[c])
order_paper = sorted(COMPS, key=lambda c: -pcomp_n[c])
status_n = Counter((c, r["components"][c]["status"]) for r in m1 for c in COMPS)
write(pd.DataFrame([{"component": c, "proposed_system_present": comp_n[c], "proposed_share": pct(comp_n[c], N),
                     "paper_level_present": pcomp_n[c], "paper_level_share": pct(pcomp_n[c], N),
                     "gap_pp": round(gap[c], 1), "explicitly_absent_m1": status_n[(c, "explicitly_absent")],
                     "not_reported_m1": status_n[(c, "not_reported")]} for c in COMPS]), "component_presence_both_views.csv")


def task_matrix(view):
    return {t: {c: sum(1 for k in ids if task_of[k] == t and c in view[k]) for c in COMPS} for t in TASKS}


tc = task_matrix(paper_present)              # paper level (heatmap, cross-task table, appendix prose)
tc_prop = task_matrix(present)               # proposed system (appendix figure, l.1454)
for name, mat, tot in [("task_x_component_paper_level.csv", tc, pcomp_n), ("task_x_component_proposed_system.csv", tc_prop, comp_n)]:
    rows = []
    for t in TASKS:
        rows.append({"task": t, "N": task_n[t], **{c: mat[t][c] for c in COMPS},
                     **{c + "_pct": round(pv(mat[t][c], task_n[t]), 1) for c in COMPS}})
    rows.append({"task": "TOTAL", "N": N, **tot, **{c + "_pct": round(pv(tot[c], N), 1) for c in COMPS}})
    write(pd.DataFrame(rows), name)

# annual presence (paper level)
years = sorted(set(dates.year.dropna().astype(int)))
year_n = Counter(year_of[k] for k in ids)
rows = []
for y in years:
    row = {"interval": y, "n": year_n[y]}
    for c in COMPS:
        k_ = sum(1 for k in ids if year_of[k] == y and c in paper_present[k])
        row[c], row[c + "_pct"] = k_, round(pv(k_, year_n[y]), 1)
    rows.append(row)
rows.append({"interval": "Total", "n": N, **pcomp_n, **{c + "_pct": round(pv(pcomp_n[c], N), 1) for c in COMPS}})
annual = pd.DataFrame(rows)
write(annual, "annual_component_presence_paper_level.csv")
annual_i = annual.set_index("interval")
half_n = Counter(dates.half_year)
write(pd.DataFrame(sorted(half_n.items()), columns=["half_year", "papers"]), "half_year_distribution.csv")
incr = {c: float(annual_i.loc[2026, c + "_pct"]) - float(annual_i.loc[2024, c + "_pct"]) for c in COMPS}
largest_incr = max(COMPS, key=lambda c: incr[c])

# signatures (proposed system)
sig_n = Counter(signature.values())
sig_sorted = sorted(sig_n.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))
write(pd.DataFrame([{"rank": i + 1, "signature": s, "n_components": len(s), "papers": n, "share": pct(n, N),
                     "tasks": "; ".join(sorted({task_of[k] for k in ids if signature[k] == s}))}
                    for i, (s, n) in enumerate(sig_sorted)]), "signatures.csv")
n_sig = len(sig_sorted)
top3 = sig_sorted[:3]
top3_cov = sum(n for _, n in top3)
r4_8, tail = sig_sorted[3:8], sig_sorted[8:]
core_top3 = set(top3[0][0]).intersection(*[set(s) for s, _ in top3[1:]])
cnt = lambda s: sig_n.get(s, 0)
top_txt = ", ".join(f"{s} {n}" for s, n in top3)

cop = {(a, b): sum(1 for k in ids if a in present[k] and b in present[k]) for a, b in combinations(COMPS, 2)}
write(pd.DataFrame([{"pair": a + "-" + b, "papers": n, "share": pct(n, N)} for (a, b), n in cop.items()]),
      "component_copresence.csv")
co = lambda a, b: cop.get((a, b), cop.get((b, a)))

# ---------------------------------------------------------------------------------------------
# 4. Relations (m1; candidates = both endpoints present)
# ---------------------------------------------------------------------------------------------
rel_rows = []
for rid, (s, t) in REL.items():
    vals = [r["relations"][rid] for r in m1 if rid in r["relations"]]
    rel_rows.append({"relation": rid, "source": s, "target": t, "candidates": len(vals),
                     "established": vals.count("established"), "not_established": vals.count("not_established"),
                     "explicitly_not_used": vals.count("explicitly_not_used"),
                     "established_pct": round(pv(vals.count("established"), len(vals)), 1),
                     "both_endpoints_present": sum(1 for k in ids if s in present[k] and t in present[k])})
rel = pd.DataFrame(rel_rows).set_index("relation")
write(rel.reset_index(), "relations.csv")
rel_cand_total, rel_est_total = int(rel.candidates.sum()), int(rel.established.sum())
rel_enu_total = int(rel.explicitly_not_used.sum())
E_ = lambda r_: int(rel.loc[r_, "established"])
C_ = lambda r_: int(rel.loc[r_, "candidates"])
R_ = lambda r_: float(rel.loc[r_, "established_pct"])
rel_rank = rel.established_pct.sort_values(ascending=False)

# ---------------------------------------------------------------------------------------------
# 5. Implementation categories (coded for the m1 proposed system only)
# ---------------------------------------------------------------------------------------------
cat_n = Counter((c, cat) for r in m1 for c in COMPS for cat in r["components"][c]["categories"])
# Tier rule inferred from the old table: highest 'Rare' = 11/133 (8.3%), lowest 'Less common' = 12/133 (9.0%),
# highest 'Less common' = 39/133 (29.3%), lowest 'Common' = 50/133 (37.6%); cut points at the midpoints.


def tier(n):
    s = pv(n, N)
    return "Common" if s >= 33.45 else ("Less common" if s >= 8.65 else "Rare")


write(pd.DataFrame([{"component": c, "category": cat, "papers": n, "share": pct(n, N), "tier": tier(n)}
                    for (c, cat), n in sorted(cat_n.items(), key=lambda kv: (COMPS.index(kv[0][0]), -kv[1]))]),
      "implementation_categories.csv")

# ---------------------------------------------------------------------------------------------
# 6. Evaluation fields (m1, paper level)
# ---------------------------------------------------------------------------------------------
ev = [r["evaluation"] for r in m1]
art = Counter(e["artefact"] for e in ev)
rows = [{"field": "artefact", "value": v, "papers": art[v], "share": pct(art[v], N)} for v in "ALNU"]
for f in ["repeated_runs", "uncertainty_reported", "cost_reported"]:
    rows += [{"field": f, "value": v, "papers": n, "share": pct(n, N)} for v, n in Counter(e[f] for e in ev).most_common()]
for f in ["metric_classes", "verification_classes"]:
    rows += [{"field": f, "value": v, "papers": n, "share": pct(n, N)}
             for v, n in Counter(x for e in ev for x in e[f]).most_common()]
write(pd.DataFrame(rows), "evaluation_fields.csv")
mclass = Counter(x for e in ev for x in e["metric_classes"])

# ---------------------------------------------------------------------------------------------
# 7. Benchmark families (>= 3 papers). All SWE-bench variants form one family; HumanEval-derived sets count
#    as HumanEval; app stores and data sources of author-built datasets are not families.
# ---------------------------------------------------------------------------------------------
FAMILY_RULES = [
    ("Defects4J", r"defects4j"),
    ("SWE-bench (all variants)", r"swe-?bench|swe-rebench"),
    ("SWT-bench", r"swt-bench"), ("TDD-Bench", r"tdd-bench"),
    ("HumanEval", r"humaneval"), ("QuixBugs", r"quixbugs"), ("BugsInPy", r"bugsinpy"), ("ConDefects", r"condefects"),
    ("Methods2Test", r"methods2test"), ("GitBug-Java", r"gitbug-java"), ("Themis", r"themis"),
    ("CodaMosa benchmark", r"codamosa"), ("GHRB", r"ghrb"), ("GrowingBugs", r"growingbugs"),
    ("ReCDroid dataset", r"recdroid"), ("AndroR2", r"andror2"), ("ScopeDroid dataset", r"scopedroid"),
    ("FrUITeR dataset", r"fruiter"), ("CraftDroid dataset", r"craftdroid"), ("IDoFT", r"idoft"),
    ("VUL4J", r"vul4j"), ("VJBench", r"vjbench"), ("RWB", r"\brwb\b"), ("HITS dataset", r"hits dataset"),
    ("EvoMaster benchmark (EMB)", r"evomaster"), ("ARVO", r"arvo"), ("MAGMA", r"magma"), ("UNIFUZZ", r"unifuzz"),
    ("FuzzBench", r"fuzzbench"), ("SmartBugs-curated", r"smartbugs"), ("LeetCode-Java", r"leetcode-?java"),
    ("MoTIF", r"motif"), ("LocBench", r"locbench"), ("DebugBench", r"debugbench"), ("xCodeEval", r"xcodeeval"),
    ("DS-1000", r"ds-1000"), ("BugsC++", r"bugsc\+\+"), ("BugBench", r"^bugbench"), ("TypeBugs", r"typebugs"),
    ("Refactory", r"refactory"), ("SecBench.js", r"secbench"), ("CyberGym", r"cybergym"), ("TECO dataset", r"teco"),
    ("VulnLoc", r"vulnloc"), ("AFLGo dataset", r"aflgo"), ("OSS-Fuzz", r"oss-fuzz \(arvo"),
    # Added 2026-11-02 after full-text review of unmapped benchmark strings (temp/benchmark_review/):
    # published datasets, or subsets of them, count as public; datasets extended or assembled by the
    # authors stay study-specific (advisor ruling).
    ("ysoserial", r"ysoserial"), ("Gleipner", r"gleipner"), ("TARBENCH", r"tarbench"),
    ("Odin dataset", r"\bodin\b"), ("RegDroid dataset", r"regdroid"), ("UQ-AAS21", r"uq-aas21"),
    ("Imtiaz et al. web test repair dataset", r"imtiaz"), ("Benchmark-C (program reduction)", r"^benchmark-c$"),
    ("Benchmark-Rust (program reduction)", r"^benchmark-rust$"), ("Slither/SoMo/SPCon labelled cases", r"slither/somo/spcon"),
    ("SIR", r"^sir$"), ("Pecan benchmarks", r"pecan"), ("JaConTeBe", r"jacontebe"), ("PFix benchmarks", r"pfix benchmarks"),
    ("Sorald dataset", r"sorald"), ("ACPR", r"^acpr"), ("SAVER dataset", r"saver dataset"),
    ("ERAP", r"^erap$"), ("ESC", r"^esc$"), ("ReentrancyStudy-Data", r"reentrancystudy"),
    ("All Things Reentrancy", r"all things reentr"), ("Solidity Security by Example", r"solidity security by example"),
    ("Themis", r"su et al\. 2021 android bug benchmark"), ("CraftDroid dataset", r"^lin dataset$"),
    ("TEMdroid dataset", r"^tem dataset$"), ("TransformedD4J", r"transformedd4j"), ("Ye et al. dataset", r"ye et al\. dataset"),
    ("SelectFuzz dataset", r"selectfuzz"), ("DAFL dataset", r"^dafl dataset$"), ("GIFdroid suite", r"gifdroid"),
    ("V2S recordings", r"^v2s gui"), ("AndroTest", r"androtest"),
]
EXCLUDE_FAMILY = {("S0763", "TDD-Bench")}           # confirmed: only the TDD-Bench harness is used
bench_rows, fam_papers = [], defaultdict(set)
for r in m1:
    for b in r["evaluation"]["benchmarks"]:
        hits = [f for f, pat in FAMILY_RULES if re.search(pat, b.lower()) and (r["record_id"], f) not in EXCLUDE_FAMILY]
        for h in hits:
            fam_papers[h].add(r["record_id"])
        bench_rows.append({"record_id": r["record_id"], "task": r["task"], "benchmark_string": b, "families": "; ".join(hits)})
write(pd.DataFrame(bench_rows), "benchmark_string_to_family.csv")
fam_rows = []
for f_, ps in sorted(fam_papers.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    ts = Counter(task_of[p] for p in ps)
    fam_rows.append({"family": f_, "papers": len(ps), "recurring_ge3": len(ps) >= 3,
                     "principal_task": max(TASKS, key=lambda t: ts.get(t, 0)),
                     **{t: ts.get(t, 0) for t in TASKS}, "record_ids": "; ".join(sorted(ps))})
fam_df = pd.DataFrame(fam_rows)
write(fam_df, "benchmark_families_all.csv")
write(fam_df[fam_df.recurring_ge3].drop(columns=["recurring_ge3"]), "benchmark_families_recurring.csv")
recurring = {r_["family"]: fam_papers[r_["family"]] for r_ in fam_rows if r_["papers"] >= 3}
papers_with_recurring = set().union(*recurring.values()) if recurring else set()
fam = lambda name: len(fam_papers.get(name, set()))
fam_task = lambda name, t: sum(1 for p in fam_papers.get(name, set()) if task_of[p] == t)

# ---------------------------------------------------------------------------------------------
# 8. Mode 2
# ---------------------------------------------------------------------------------------------
HC = [(k, h) for k, r in m2.items() for h in r["hcs"]]
EC = [(k, e) for k, r in m2.items() for e in r["ecs"]]
CL = [(k, c) for k, r in m2.items() for c in r["claims"]]
MC = [(k, m) for k, r in m2.items() for m in r["matched_comparisons"]]
role_n = Counter(h["role"] for _, h in HC)
role_p = {ro: len({k for k, h in HC if h["role"] == ro}) for ro in role_n}
n_prop_papers_multi = sum(1 for r in m2.values() if sum(h["role"] == "proposed" for h in r["hcs"]) > 1)
extra_prop = role_n["proposed"] - N
write(pd.DataFrame([{"role": ro, "hcs": role_n[ro], "papers": role_p[ro]} for ro in ["proposed", "ablation", "variant"]]
                   + [{"role": "proposed beyond one per paper (co-primary systems)", "hcs": extra_prop, "papers": n_prop_papers_multi},
                      {"role": "TOTAL", "hcs": len(HC), "papers": len(m2)}]), "hc_roles.csv")
write(pd.DataFrame(Counter(h["focal"] for _, h in HC).most_common(), columns=["focal", "hcs"]), "hc_focal.csv")
write(pd.DataFrame(Counter(h["comparison_target"] for _, h in HC).most_common(), columns=["comparison_target", "hcs"]),
      "hc_comparison_target.csv")
write(pd.DataFrame(Counter(h["components"] for _, h in HC).most_common(), columns=["components", "hcs"]), "hc_component_strings.csv")
per_paper = pd.DataFrame([{"record_id": k, "task": task_of[k], "hcs": len(r["hcs"]), "ecs": len(r["ecs"]),
                           "claims": len(r["claims"]), "primary_claims": sum(c["importance"] == "primary" for c in r["claims"]),
                           "matched_comparisons": len(r["matched_comparisons"])} for k, r in m2.items()])
write(per_paper, "m2_counts_per_paper.csv")
write(per_paper.describe().reset_index(), "m2_counts_summary.csv")


def metric_list(c):
    """Claims whose metrics field is the string 'not_reported' (30 claims) have no metric entries."""
    return [m for m in c["metrics"] if isinstance(m, dict)] if isinstance(c["metrics"], list) else []


def metric_alignment(c):
    rel_ = {m["relevance"] for m in metric_list(c)}
    for key, lab in [("direct", "compatible metric present"), ("indirect", "partially compatible metric only"),
                     ("incompatible", "claim-incompatible metric only")]:
        if key in rel_:
            return lab
    return "no metric reported"


PRIM = [(k, c) for k, c in CL if c["importance"] == "primary"]
prim_papers = {k for k, _ in PRIM}
imp_n = Counter(c["importance"] for _, c in CL)
prop_prim = Counter(c["property"] for _, c in PRIM)
align_prim = Counter(c["alignment"] for _, c in PRIM)
malign_prim = Counter(metric_alignment(c) for _, c in PRIM)
FULL, PART, INCP, NONE, UNCL = ("fully-corroborated-within-reported-scope", "partially-corroborated",
                                "independent-evidence-present-but-claim-incompatible", "no-independent-corroboration", "unclear")
pa = Counter((c["property"], c["alignment"]) for _, c in PRIM)

# Claim-type mapping (old table rows <- new property values)
CLAIM_MAP = {"Effectiveness (task and diagnostic effectiveness merged)": ["effectiveness"],
             "Test adequacy": ["adequacy"], "Efficiency or cost": ["efficiency/cost"], "Fault revelation": ["fault revelation"],
             "Other evaluated properties": ["validity", "human/practical quality", "robustness/stability", "other"]}
claim_row = {lab: sum(prop_prim[p] for p in ps) for lab, ps in CLAIM_MAP.items()}
write(pd.DataFrame([{"old table row": lab, "new property values": "; ".join(ps), "primary_claims": claim_row[lab],
                     "share": pct(claim_row[lab], len(PRIM))} for lab, ps in CLAIM_MAP.items()]),
      "claim_type_mapping.csv")
write(pd.DataFrame([{"importance": i, "claims": n} for i, n in imp_n.most_common()]), "claims_by_importance.csv")
write(pd.DataFrame([{"property": p, "primary_claims": n, "share": pct(n, len(PRIM))} for p, n in prop_prim.most_common()]),
      "primary_claims_by_property.csv")
write(pd.DataFrame([{"alignment": a, "primary_claims": n, "share": pct(n, len(PRIM)),
                     "papers": len({k for k, c in PRIM if c["alignment"] == a})} for a, n in align_prim.most_common()]),
      "primary_claim_corroboration.csv")
write(pd.DataFrame([{"metric_alignment": a, "primary_claims": n, "share": pct(n, len(PRIM))}
                    for a, n in malign_prim.most_common()]), "primary_claim_metric_alignment.csv")
write(pd.DataFrame([{"property": p, "alignment": a, "primary_claims": n, "property_total": prop_prim[p],
                     "papers": len({k for k, c in PRIM if c['property'] == p and c['alignment'] == a})}
                    for (p, a), n in sorted(pa.items())]), "primary_claims_property_x_alignment.csv")
metric_rows_prim = sum(len(metric_list(c)) for _, c in PRIM)
claims_metric_str = [(k, c["claim_id"]) for k, c in CL if not isinstance(c["metrics"], list)]

# Metric families: papers from m1 metric_classes; ECs = distinct ECs linked by primary claims of the matching property
METRIC_FAM = [("Effectiveness (task and diagnostic)", "TE", "effectiveness"), ("Test adequacy", "SA", "adequacy"),
              ("Efficiency or cost", "EC", "efficiency/cost"), ("Fault revelation", "FR", "fault revelation"),
              ("Artefact validity", "AV", "validity"), ("Human or practical quality", "HPQ", "human/practical quality"),
              ("Diversity or stability", "DS", "robustness/stability")]
ec_prim = defaultdict(set)
for k, c in PRIM:
    ec_prim[c["property"]].update((k, e) for e in c["ec_ids"])
mf = {lab: (mclass[cls], len(ec_prim[prop])) for lab, cls, prop in METRIC_FAM}
write(pd.DataFrame([{"metric family": lab, "m1 metric class": cls, "papers (m1)": mf[lab][0],
                     "claim property": prop, "distinct ECs linked by primary claims": mf[lab][1]}
                    for lab, cls, prop in METRIC_FAM]), "metric_families.csv")

# Corroborating evidence items, excluding statistical tests
STAT = re.compile(r"statistical|effect-size|inter-rater|wilcoxon|mcnemar|anova", re.I)


def ev_kind(t: str) -> str:
    """Keyword mapping of the free-text evidence type to a closed list of kinds."""
    s = t.lower()
    if STAT.search(s):
        return "statistical test"
    if re.search(r"cve|security|vulnerab|advisory", s):
        return "security or vulnerability confirmation"
    if re.search(r"developer|maintainer|accepted|\bpr\b|commit|issue-tracker|community|fix", s):
        return "maintainer or developer confirmation"
    if "mutation" in s:
        return "mutation analysis"
    if re.search(r"manual|human|qualitative|case|inspection|interview|survey|participant|expert|reviewer|assessment", s):
        return "manual or human review"
    if re.search(r"reproduc|replay|trace", s):
        return "reproduction or trace replay"
    if re.search(r"benchmark|holdout|post-cutoff|temporal", s):
        return "external or temporal benchmark"
    if "llm judge" in s:
        return "LLM judge"
    if "alignment" in s:
        return "alignment with separate result"
    return "other"


items, claim_ev_pairs, ec_with_ev = {}, 0, set()
for k, c in CL:
    for e in (c["evidence"] if isinstance(c["evidence"], list) else []):
        if not isinstance(e, dict) or ev_kind(str(e.get("type", ""))) == "statistical test":
            continue
        t = str(e.get("type", ""))
        desc = str(e.get("description") or e.get("detail") or e.get("details") or "")
        items[(k, t.strip().lower(), desc.strip().lower(), str(e.get("page", "")).strip().lower())] = ev_kind(t)
        claim_ev_pairs += 1
        ec_with_ev.update((k, x) for x in c["ec_ids"])
kind_n = Counter(items.values())
kind_p = {kd: len({kk[0] for kk, v in items.items() if v == kd}) for kd in kind_n}
item_papers = {kk[0] for kk in items}
write(pd.DataFrame([{"evidence_kind": kd, "distinct_items": n, "papers": kind_p[kd]} for kd, n in kind_n.most_common()]
                   + [{"evidence_kind": "TOTAL (statistical tests excluded)", "distinct_items": len(items), "papers": len(item_papers)}]),
      "corroborating_evidence_items.csv")
prim_with_ev = align_prim[FULL] + align_prim[PART] + align_prim[INCP]

# Matched comparisons: directional = gain/loss/mixed
mc_dir = Counter(m["direction"] for _, m in MC)
DIR = [(k, m) for k, m in MC if m["direction"] in ("gain", "loss", "mixed")]
dir_papers = {k for k, _ in DIR}
dir_pairs = {(k, m["hc_a"], m["hc_b"]) for k, m in DIR}
all_pairs = {(k, m["hc_a"], m["hc_b"]) for k, m in MC}
TRADE = [(k, m) for k, m in MC if m["gain_and_loss"] is True]
trade_dir = [(k, m) for k, m in DIR if m["gain_and_loss"] is True]
trade_papers = {k for k, _ in TRADE}
n_letters = lambda cc: len(hc_letters(cc))
dir_single = sum(1 for _, m in DIR if n_letters(m["changed_components"]) == 1)
dir_bundle = sum(1 for _, m in DIR if n_letters(m["changed_components"]) > 1)
dir_noletter = len(DIR) - dir_single - dir_bundle
dir_task = Counter(task_of[k] for k in dir_papers)
write(pd.DataFrame([{"measure": "all comparison rows", "value": len(MC)},
                    {"measure": "papers with any comparison", "value": len({k for k, _ in MC})},
                    {"measure": "distinct HC pairs, all rows", "value": len(all_pairs)},
                    *[{"measure": f"direction={d}", "value": n} for d, n in mc_dir.most_common()],
                    {"measure": "directional rows (gain/loss/mixed)", "value": len(DIR)},
                    {"measure": "papers with directional rows", "value": len(dir_papers)},
                    {"measure": "distinct HC pairs with directional rows", "value": len(dir_pairs)},
                    {"measure": "trade-off rows (gain_and_loss = true)", "value": len(TRADE)},
                    {"measure": "trade-off rows among directional rows", "value": len(trade_dir)},
                    {"measure": "papers with trade-off rows", "value": len(trade_papers)},
                    {"measure": "directional rows changing one component letter", "value": dir_single},
                    {"measure": "directional rows changing several component letters (bundle)", "value": dir_bundle},
                    {"measure": "directional rows without a component letter", "value": dir_noletter}]),
      "matched_comparisons_summary.csv")
write(pd.DataFrame([{"task": t, "papers_with_directional_rows": dir_task[t],
                     "directional_rows": sum(1 for k, _ in DIR if task_of[k] == t),
                     "trade_off_rows": sum(1 for k, _ in TRADE if task_of[k] == t)} for t in TASKS]),
      "matched_comparisons_by_task.csv")
write(pd.DataFrame([{"record_id": k, "system_name": sysname[k], "task": task_of[k],
                     "directional_rows": sum(1 for kk, _ in DIR if kk == k),
                     "single_factor_rows": sum(1 for kk, m in DIR if kk == k and n_letters(m["changed_components"]) == 1),
                     "bundle_rows": sum(1 for kk, m in DIR if kk == k and n_letters(m["changed_components"]) > 1),
                     "trade_off_rows": sum(1 for kk, _ in TRADE if kk == k)} for k in sorted(dir_papers)]),
      "matched_comparisons_by_paper.csv")


def study(rid):
    rows_ = [m for k, m in DIR if k == rid]
    return {"rows": len(rows_), "single": sum(n_letters(m["changed_components"]) == 1 for m in rows_),
            "bundle": sum(n_letters(m["changed_components"]) > 1 for m in rows_),
            "trade": sum(1 for k, m in TRADE if k == rid),
            "factors": len({m["changed_factor"] for m in rows_})}


# ---------------------------------------------------------------------------------------------
# 9. PRISMA boxes (each number traced to a file)
# ---------------------------------------------------------------------------------------------
P_FILE = "search_redo_2026/08_prisma/prisma_counts_20261026.txt"
T_FILE = "search_redo_2026/07_fulltext/ta_stage_counts.txt"
prisma_txt = (SR / "08_prisma/prisma_counts_20261026.txt").read_text(encoding="utf-8")
ta_txt = (SR / "07_fulltext/ta_stage_counts.txt").read_text(encoding="utf-8")
grab = lambda pat, txt: int(re.search(pat, txt).group(1))
src_counts = {k: int(v) for k, v in re.findall(r"'(arXiv|IEEE|ACM|Venue)': (\d+)", prisma_txt)}
PR = {"identified": grab(r"\} (\d+) date removed", prisma_txt), "date_removed": grab(r"date removed (\d+)", prisma_txt),
      "after_date": grab(r"after date (\d+)", prisma_txt), "screened": grab(r"Records screened: (\d+)", ta_txt),
      "ta_duplicates": grab(r"Duplicates \(first-author review\): (\d+)", ta_txt),
      "ta_excluded": grab(r"Excluded at title/abstract: (\d+)", ta_txt), "sought": grab(r"Sought for full-text retrieval: (\d+)", ta_txt),
      "withdrawn": grab(r"withdrawn (\d+)", prisma_txt), "ft_duplicates": grab(r"ftdup (\d+)", prisma_txt),
      "venue_rows": grab(r"ve rows (\d+)", prisma_txt), "assessed": grab(r"assessed (\d+)", prisma_txt),
      "ft_excluded": grab(r"\} (\d+) \| included", prisma_txt), "included": grab(r"included (\d+)", prisma_txt)}
PR["dedup_removed"] = PR["after_date"] - PR["screened"]
PR["venue_ineligible"] = PR["venue_rows"] - PR["assessed"]
ve_cats = dict(re.findall(r"'([^']+)': (\d+)", prisma_txt.split("ve rows")[1].split("\n")[0]))
ft_reasons = re.search(r"ft excl reasons (\{.*?\})", prisma_txt).group(1)
assert PR["screened"] == 3942 and PR["included"] == N
assert PR["ta_excluded"] + PR["ta_duplicates"] + PR["sought"] == PR["screened"]
assert PR["sought"] - PR["withdrawn"] - PR["ft_duplicates"] == PR["venue_rows"]
assert PR["assessed"] - PR["ft_excluded"] == PR["included"]
prisma_boxes = [
    ("Records identified (arXiv / IEEE / ACM / venue sweep)", f"{PR['identified']:,} ({' / '.join(f'{v:,}' for v in src_counts.values())})", P_FILE),
    ("Removed: first public date outside 2024-01-01..2026-06-30", PR["date_removed"], P_FILE),
    ("Removed: duplicates at merge", f"{PR['dedup_removed']:,} (= {PR['after_date']:,} - {PR['screened']:,})", P_FILE),
    ("Records screened (title/abstract)", f"{PR['screened']:,}", T_FILE),
    ("Excluded at title/abstract", f"{PR['ta_excluded']:,}", T_FILE),
    ("Duplicates removed at title/abstract (first-author review)", PR["ta_duplicates"], T_FILE),
    ("Reports sought for retrieval", f"{PR['sought']:,}", T_FILE),
    ("Not retrieved: withdrawn", PR["withdrawn"], P_FILE),
    ("Removed: full-text duplicates", PR["ft_duplicates"], P_FILE),
    ("Reports assessed for venue eligibility (C5)", f"{PR['venue_rows']:,}", P_FILE),
    ("Excluded: venue not eligible (arXiv only / other venue / workshop or other track)",
     f"{PR['venue_ineligible']} ({ve_cats.get('arXiv only')} / {ve_cats.get('other venue')} / {ve_cats.get('workshop/companion/other track')})", P_FILE),
    ("Full texts assessed for eligibility", PR["assessed"], P_FILE),
    ("Excluded at full text (reasons)", f"{PR['ft_excluded']} {ft_reasons}", P_FILE),
    ("Studies included", PR["included"], P_FILE + "; search_redo_2026/07_fulltext/ft_included.csv"),
]
write(pd.DataFrame(prisma_boxes, columns=["box", "records", "source file"]), "prisma_boxes.csv")

# ---------------------------------------------------------------------------------------------
# 10. Agreement statistics (pre-adjudication; final, provided by the first author)
# ---------------------------------------------------------------------------------------------
AGREE = [("Task", "93.5%", "0.913", ""), ("Component presence", "93.2%", "0.794", "1,078 units"),
         ("Implementation categories", "89.0%", "0.778", "4,095 units"), ("Relations", "80.4%", "0.576", "1,468 units"),
         ("Metric classes", "91.7%", "0.834", ""), ("Verification classes", "89.5%", "0.789", ""),
         ("Repeated runs", "79.9%", "0.667", ""), ("Uncertainty reported", "98.1%", "0.954", ""),
         ("Cost reported", "96.8%", "0.879", ""), ("Artefact availability", "96.1%", "0.831", "")]
vtxt = (SR / "09_coding/verify_stats_full.txt").read_text(encoding="utf-8")
PASS = {lab: re.search(rf"^{key} (\d+) .*?pass ([0-9.]+)", vtxt, re.M).groups()
        for key, lab in [("H", "HC"), ("E", "EC"), ("K", "claims"), ("P", "matched comparisons"), ("all", "overall")]}
write(pd.DataFrame([{"item": a, "agreement": b, "kappa": c, "units": d, "source": "09_coding/compare_coding.py output"} for a, b, c, d in AGREE]
                   + [{"item": f"mode-2 verification: {lab}", "agreement": pct(float(p) * 100, 100), "kappa": "",
                       "units": f"{int(n):,} items", "source": "09_coding/verify_stats_full.txt"} for lab, (n, p) in PASS.items()]),
      "agreement_statistics.csv")
agree_txt = ("Pre-adjudication agreement (Opus vs Codex, all 154 papers): " + "; ".join(f"{a} {b} (kappa {c})" for a, b, c, _ in AGREE)
             + ". Mode-2 verification pass rates: " + "; ".join(f"{lab} {float(p) * 100:.1f}% ({int(n):,})" for lab, (n, p) in PASS.items()) + ".")

# Timeline membership of the old 34 systems (reference only)
tl = pd.read_csv(ROOT / "overleaf-paper/tools/timeline_milestones.csv", encoding="utf-8-sig")
m1_names = {norm(r["system_name"]): r["record_id"] for r in m1}
tl["in_new_corpus"] = tl.short_name.map(lambda s: m1_names.get(norm(s), ""))
write(tl[["short_name", "year", "cluster", "task", "in_new_corpus"]], "timeline_old_systems_membership.csv")
tl_hits = int((tl.in_new_corpus != "").sum())
interval_txt = "; ".join(f"{y}: {year_n[y]} papers" for y in years)

# ---------------------------------------------------------------------------------------------
# 11. Map the 711 inventory rows
# ---------------------------------------------------------------------------------------------
inv = pd.read_csv(ROOT / "temp/number_inventory.tsv", sep="\t", encoding="utf-8")
oldv = inv.set_index("id")["value"]
OUT: dict[str, dict] = {}


def put(i, new, rule, status=None, code="", issue=""):
    """Register the new value of inventory row Nxxx; status None = decide same/changed numerically."""
    i = i if isinstance(i, str) else f"N{i:03d}"
    new = f"{new:.1f}" if isinstance(new, float) else str(new)
    OUT[i] = {"new": new, "rule": rule, "status": status, "issue": issue, "code": code}


R_CORPUS = "Corpus size: records in m1_final.jsonl (= ft_included.csv)."
for i in [2, 26, 41, 44, 47, 48, 54, 58, 64, 69, 75, 76, 83, 96, 109, 111, 115, 198, 212, 215, 270, 271,
          478, 479, 636, 644, 649, 650]:
    put(i, N if i != 54 else f"{N} papers", R_CORPUS)
put(167, f"N={N}", R_CORPUS)
put(220, f"N={N}", R_CORPUS)

# -- PRISMA (choice 11)
for i in [1, 24, 55, 61, 648]:
    put(i, f"{PR['screened']:,}", f"Records screened at title/abstract ({T_FILE}).", code="PRISMA")
for i in [25, 62]:
    put(i, PR["assessed"], f"Full texts assessed for eligibility after the venue-eligibility box ({P_FILE}).", code="PRISMA")
put(56, f"{PR['ta_excluded'] + PR['ta_duplicates']:,} ({PR['ta_excluded']:,} excluded + {PR['ta_duplicates']} duplicates)",
    f"Records leaving at title/abstract = screened - sought ({T_FILE}); the venue box then removes {PR['venue_ineligible']}.",
    status="changed", code="PRISMA")
for i in [57, 63]:
    put(i, PR["ft_excluded"], f"Excluded at full-text eligibility among {PR['assessed']} assessed ({P_FILE}).", code="PRISMA")
put(59, 1, "Search design: 01_queries/search_strings.md defines one Boolean string (A AND B) OR (H AND C).", status="changed", code="PRISMA")
put(60, "1 (venue sweep); no snowballing", "Supplementary routes per search_redo_2026/README.md (venue sweep; 04_snowball empty).",
    status="changed", code="PRISMA")

# -- task scheme (choice 1)
for i in [3, 43, 46, 49, 194, 195, 218, 219, 257, 651, 669]:
    put(i, len(TASKS), "Number of primary-task categories (m1 task field).", status="scheme changed", code="TASK")
put(40, "three-level", "Taxonomy depth corpus -> two families -> six tasks -> papers.", status="same", code="TASK")
fam_txt = "; ".join(f"{f} ({'+'.join(ts)}: {fam_size[f]})" for f, ts in FAMILIES.items())
for i in [42, 45]:
    put(i, f"2 ({fam_txt})", "The two testing-objective families of main.tex l.210-213 contain the six categories one-to-one.",
        status="same", code="TASK")
put(67, "0 (coding manual v5 gives an explicit endpoint rule for all six categories)",
    "Categories outside the boundary-ruled ones; coding_prompt_v5.md section 1 defines a rule for each label.",
    status="scheme changed", code="TASK")
small_tasks = [t for t in TASKS if task_n[t] < 10]
T = lambda t: f"{t} {task_n[t]}"
put(196, len(small_tasks), "Tasks with fewer than ten papers: " + ", ".join(T(t) for t in small_tasks) + ".", status="scheme changed", code="TASK")
put(635, f"{min(task_n[t] for t in small_tasks)} to {max(task_n[t] for t in small_tasks)}",
    "Size range of tasks with fewer than ten papers.", status="scheme changed", code="TASK")
put(199, f"system_test_input_generation {task_n['system_test_input_generation']}; program_repair {task_n['program_repair']}",
    "Two largest new categories (m1 task).", status="scheme changed", code="TASK")
put(200, task_n["unit_test_generation"], "Papers with task unit_test_generation.", status="scheme changed", code="TASK")
put(201, "no separate category (issue resolution -> program_repair; issue reproduction -> unit or system test generation)",
    "The six-category scheme has no issue category.", status="scheme changed", code="TASK")
put(206, "no separate category (part of system_test_input_generation)", "GUI/mobile/system testing is part of system_test_input_generation.",
    status="scheme changed", code="TASK")
put(207, task_n["test_oracle_generation"], "Papers with task test_oracle_generation.", status="scheme changed", code="TASK")
put(208, task_n["bug_analysis"], "Papers with task bug_analysis.", status="scheme changed", code="TASK")
put(209, task_n["debugging"], "Papers with task debugging.", status="scheme changed", code="TASK")
top4 = sorted(TASKS, key=lambda t: -task_n[t])[:4]
top4_n = sum(task_n[t] for t in top4)
for i in [202, 210]:
    put(i, "4 of 6 (" + ", ".join(T(t) for t in top4) + ")", "Four largest of the six categories.", status="scheme changed", code="TASK")
put(213, "four of the six", "Four largest of the six categories.", status="scheme changed", code="TASK")
put(203, top4_n, "Papers in the four largest categories.", status="scheme changed", code="TASK")
for i in [204, 214]:
    put(i, pct(top4_n, N, 0), f"Share = {top4_n}/{N}.", status="scheme changed", code="TASK")
put(205, N - top4_n, "Papers in the other two categories (" + ", ".join(T(t) for t in TASKS if t not in top4) + ").",
    status="scheme changed", code="TASK")
put(671, sum(1 for t in TASKS if task_n[t] < 10), "Task groups with fewer than ten proposed systems (m1).", status="scheme changed", code="TASK")
for i, v in [(197, 10), (269, 10), (672, 10), (675, "N<10")]:
    put(i, v, "Threshold (design).", status="same")

# -- HC / EC / claim totals (choice 7)
for i in [4, 50, 65, 425]:
    put(i, len(HC), "Total HCs in m2_final (authors' own configurations: proposed + ablation + variant).", code="HCSCOPE")
for i in [5, 51, 66, 473, 480]:
    put(i, f"{len(EC):,}", "Total ECs in m2_final.", code="HCSCOPE")
for i in [6, 52, 74, 474, 481]:
    put(i, f"{len(CL):,}", "Total claims in m2_final (all importance levels).", code="HCSCOPE")
R_PS = "Proposed systems: one per paper in m1_final (mode 1)."
for i in [7, 8, 28, 70, 77, 79, 216, 272, 274, 276, 278, 283, 297, 320, 385, 637, 652, 668, 670, 673]:
    put(i, N, R_PS)
for i in [279, 386, 674]:
    put(i, f"N={N}", R_PS)
for i in [71, 78, 217, 273, 311, 316, 633]:
    put(i, 0, "Papers without a proposed system: every paper has one coded proposed system in m1.")
for i in [416, 653]:
    put(i, len(HC) - N, f"Comparative HCs = all HCs - one proposed system per paper = {len(HC)} - {N} "
                        f"(ablation {role_n['ablation']} + variant {role_n['variant']} + {extra_prop} further proposed HCs).", code="HCSCOPE")
put(417, role_n["ablation"], "m2 HCs with role ablation.", code="HCSCOPE")
put(418, role_p["ablation"], "Papers with at least one ablation HC.", code="HCSCOPE")
for i in [419, 420]:
    put(i, "removed: external baselines out of scope", "External baselines are not HCs in the new extraction.", status="removed", code="HCSCOPE")
put(421, role_n["variant"], "m2 HCs with role variant.", code="HCSCOPE")
put(422, role_p["variant"], "Papers with at least one variant HC.", code="HCSCOPE")
put(423, extra_prop, f"Other comparative roles = proposed HCs beyond one per paper (co-primary systems): {role_n['proposed']} - {N}.", code="HCSCOPE")
put(424, n_prop_papers_multi, "Papers with more than one proposed HC.", code="HCSCOPE")

# -- signatures (proposed system)
for i in [9, 27, 280, 321, 654]:
    put(i, n_sig, "Distinct proposed-system signatures (m1).")
put(10, cnt("ETCLOVG"), "Papers with m1 signature ETCLOVG.")
put(11, cnt("ETCLOV"), "Papers with m1 signature ETCLOV.")
put(29, f"top signatures: {top_txt}", "Most frequent m1 signatures.", status="changed")
put(275, 8, "Number of signatures shown individually (design).", status="same")
put(277, max(n_sig - 8, 0), "Signatures outside the top eight (aggregated bar).")
for i in [281, 322, 327]:
    put(i, f"3 ({top_txt})", "Three most frequent signatures (m1).",
        status="same" if [s for s, _ in top3] == ["ETCLOVG", "ETCLOV", "ETCLV"] else "changed")
for i in [282, 323]:
    put(i, top3_cov, f"Papers covered by the three most frequent signatures ({top_txt}).")
for i in [284, 324]:
    put(i, pct(top3_cov, N), f"Share = {top3_cov}/{N}.")
for i in [285, 325]:
    put(i, cnt("ETCLOVG") + cnt("ETCLOV"), "Papers with signature ETCLOVG or ETCLOV.")
for i in [286, 326]:
    put(i, pct(cnt("ETCLOVG") + cnt("ETCLOV"), N), f"Share = (ETCLOVG + ETCLOV)/{N}.")
rank_etclv = [s for s, _ in sig_sorted].index("ETCLV") + 1
put(287, cnt("ETCLV"), f"Papers with signature ETCLV (now rank {rank_etclv}).")
put(288, f"{len(core_top3)}-responsibility ({''.join(c for c in COMPS if c in core_top3)})", "Components shared by the top three signatures.")
put(289, len(r4_8), "Signatures ranked 4th-8th.")
put(290, sum(n for _, n in r4_8), "Papers covered by signatures ranked 4th-8th.")
put(291, len(tail), "Signatures ranked 9th and below.")
put(292, sum(n for _, n in tail), "Papers covered by signatures ranked 9th and below.")
put(293, max((n for _, n in tail), default=0), "Maximum papers sharing one signature ranked 9th or below.")
for i in [294, 328]:
    put(i, n_sig - 3, "Signatures outside the top three.")
put(295, "dozens", "Wording; top signatures occur in " + ", ".join(str(n) for _, n in top3) + " papers.", status="same")
le2 = [s for s, n in sig_n.items() if n <= 2]
put(329, len(le2), "Signatures occurring in no more than two papers.")
put(330, max((sig_n[s] for s in le2), default=0), "Maximum papers per signature among those with at most two papers.")

# -- presence: proposed-system view (m1) and paper-level view (union) (choice 2)
for i, c in [(296, "C"), (299, "T"), (301, "V"), (303, "E"), (305, "O"), (307, "L"), (309, "G")]:
    put(i, comp_n[c], f"m1 proposed systems with {NAMES[c]} present.")
    put(298 if c == "C" else i + 1, pct(comp_n[c], N), f"Share = {comp_n[c]}/{N}.")
put(312, f"{gap[gap_max_c]:.1f} ({gap_max_c}); all gaps: " + ", ".join(f"{c} {gap[c]:.1f}" for c in COMPS),
    "Largest gap in percentage points between paper-level (union over own HCs + m1) and proposed-system (m1) shares, both /154.",
    code="UNIT")
put(313, len(gaps_le_1_5), "Components whose paper-level and proposed-system shares differ by at most 1.5 pp: "
    + (", ".join(gaps_le_1_5) or "none") + ".", code="UNIT")
put(314, pct(pcomp_n["E"], N), f"Paper-level Execution share = {pcomp_n['E']}/{N}.", code="UNIT")
put(315, pct(comp_n["E"], N), f"Proposed-system Execution share = {comp_n['E']}/{N}.")
put(317, f"{pcomp_n['C']} of {N}", "Paper-level Context presence.", code="UNIT")
put(318, f"T {pcomp_n['T']}; V {pcomp_n['V']}", "Paper-level T and V presence.", code="UNIT")
put(319, pcomp_n["G"], "Paper-level Governance presence.", code="UNIT")

# -- dates (choice 9) and annual table (paper level)
DATE_RULE = "Publication date = DOI first public date of the formal record, else arXiv first submission (21 papers)."
for i, hy in zip(range(84, 89), ["2024 H1", "2024 H2", "2025 H1", "2025 H2", "2026 H1"]):
    put(i, half_n.get(hy, 0), f"Papers with publication date in {hy}. {DATE_RULE}", code="DATE")
    put(i + 19, half_n.get(hy, 0), f"Papers with publication date in {hy}. {DATE_RULE}", code="DATE")
from25 = sum(1 for k in ids if year_of[k] >= 2025)
for i in [110, 211]:
    put(i, from25, f"Papers published from January 2025 onward. {DATE_RULE}", code="DATE")
put(112, pct(from25, N), f"Share = {from25}/{N}.", code="DATE")
yv = lambda y: int(annual_i.loc[y, "n"])
for i, y in [(117, 2024), (119, 2025), (121, 2026), (183, 2026)]:
    put(i, yv(y), f"Papers in {y}. {DATE_RULE}", code="DATE")
for i, y in [(122, 2024), (137, 2025), (152, 2026)]:
    put(i, f"n={yv(y)}", f"Papers in {y}. {DATE_RULE}", code="DATE")
R_PL = "Paper-level presence = union of components over the paper's own m2 HCs plus the m1 proposed system."
for y, b_cnt, b_pct in [(2024, 123, 130), (2025, 138, 145), (2026, 153, 160)]:
    for j, c in enumerate(COMPS):
        put(b_cnt + j, int(annual_i.loc[y, c]), f"{R_PL} Papers in {y} with {c} / {yv(y)}.", code="UNIT")
        put(b_pct + j, float(annual_i.loc[y, c + "_pct"]), f"{R_PL} Share of {y} papers with {c}.", code="UNIT")
for j, c in enumerate(COMPS):
    put(168 + j, pcomp_n[c], f"{R_PL} Papers with {c} / {N}.", code="UNIT")
    put(175 + j, float(annual_i.loc["Total", c + "_pct"]), f"{R_PL} Share with {c}.", code="UNIT")
for i, y in [(116, 2024), (118, 2025), (120, 2026), (182, 2026)]:
    put(i, int(annual_i.loc[y, "G"]), f"{R_PL} Papers in {y} with G.", code="UNIT")
minECV = min(float(annual_i.loc[y, c + "_pct"]) for y in years for c in "ECV")
put(184, f"{minECV:.1f}%", "Minimum paper-level E, C, V share over the three years.", code="UNIT")
put(185, f"{float(annual_i.loc[2024, 'G_pct']):.1f}%", "Paper-level G share in 2024.", code="UNIT")
put(186, f"{float(annual_i.loc[2026, 'G_pct']):.1f}%", "Paper-level G share in 2026 (to 30 June).", code="UNIT")

# -- venues (choice 10)
for i in [89, 113]:
    put(i, 0, "Papers whose only outlet is arXiv (all 154 are at selected venues, venue_eligibility.csv).", code="VENUE")
for i in [90, 114]:
    put(i, N, "Papers with a formal venue.", code="VENUE")
put(91, vc("ASE"), "Papers at the ASE conference.", code="VENUE")
put(92, f"ISSTA {vc('ISSTA')}; TSE {vc('TSE')}", "ISSTA = ISSTA proceedings + PACMSE ISSTA issue (tables/pacmse_split.csv); TSE.",
    status="changed", code="VENUE")
put(93, vc("ICSE"), "Papers at ICSE.", code="VENUE")
put(94, vc("TOSEM"), "Papers at TOSEM.", code="VENUE")
six = vc("ASE") + vc("ISSTA") + vc("TSE") + vc("ICSE") + vc("TOSEM")
put(95, six, f"arXiv 0 + ASE {vc('ASE')} + ISSTA {vc('ISSTA')} + TSE {vc('TSE')} + ICSE {vc('ICSE')} + TOSEM {vc('TOSEM')} (FSE {vc('FSE')} not in the old list).", code="VENUE")
put(97, pct(six, N), f"Share = {six}/{N}.", code="VENUE")
put(98, vc("ICST"), "Papers at ICST.", code="VENUE")
put(99, f"SANER {vc('SANER')}; ICPC 0", "Papers at SANER and ICPC.", status="changed", code="VENUE")
put(100, sum(other_venues.values()), "Papers in outlets with fewer than 3 papers (old figure rule): "
    + ", ".join(f"{o} {n}" for o, n in other_venues.items()) + ".", code="VENUE")
put(101, "two each: " + ", ".join(o for o, n in other_venues.items() if n == 2) + "; IEEE Software 0",
    "Outlets with exactly two papers.", status="changed", code="VENUE")
put(102, "one each: " + ", ".join(o for o, n in other_venues.items() if n == 1), "Outlets with exactly one paper.", status="changed", code="VENUE")
put(108, "order: " + ", ".join(f"{o} {n}" for o, n in venue_counts.items()), "Venue ranking by paper count.", status="changed", code="VENUE")

# -- timeline (choice 13)
TL_NOTE = f"Reference: tables/timeline_reference_by_interval.csv ({interval_txt}); {tl_hits} of the 34 old systems are in the new corpus."
for i in [187, 188, 189, 190, 191, 192, 193, 646, 647]:
    put(i, "to be re-authored", "Timeline content is an authored selection rebuilt from the new corpus.",
        status="to be re-authored", code="AUTHORED", issue=TL_NOTE)
put(667, "to be re-authored", "tab:task-boundaries is an authored table; boundary pairs follow coding manual v5 section 1.",
    status="to be re-authored", code="AUTHORED")
for i in [53, 620, 632]:
    put(i, "4", "Authored research priorities (not a coded quantity).", status="same", code="AUTHORED")

# -- task x component (paper level for heatmap / cross-task table / appendix prose; m1 for l.1454)
TC_ROWS = {
    221: ("unit_test_generation", "N"), 222: ("unit_test_generation", "R"), 223: ("unit_test_generation", "V"),
    224: ("unit_test_generation", "EC"), 225: ("unit_test_generation", "L"), 226: ("unit_test_generation", "G"),
    227: ("test_oracle_generation", "N"), 228: ("test_oracle_generation", "R"), 229: ("test_oracle_generation", "ECV"),
    230: ("test_oracle_generation", "O"), 231: ("system_test_input_generation", "N"), 232: ("system_test_input_generation", "R"),
    233: ("system_test_input_generation", "EV"), 234: ("system_test_input_generation", "T"),
    235: ("system_test_input_generation", "N"), 236: ("system_test_input_generation", "R"),
    237: ("system_test_input_generation", "TC"), 238: ("system_test_input_generation", "EO"),
    239: ("bug_analysis", "N"), 240: ("bug_analysis", "R"), 241: ("bug_analysis", "TV"), 242: ("bug_analysis", "E"),
    243: ("bug_analysis", "G"), 244: ("debugging", "N"), 245: ("debugging", "R"), 246: ("debugging", "C"),
    247: ("debugging", "EV"), 248: ("program_repair", "N"), 249: ("program_repair", "R"), 250: ("program_repair", "V"),
    251: ("program_repair", "EC"), 252: ("program_repair", "N"), 253: ("program_repair", "R"), 254: ("program_repair", "C"),
    255: ("program_repair", "ETO"), 256: ("program_repair", "LV"), 264: ("debugging", "EV"), 265: ("debugging", "O"),
    266: ("debugging", "L"), 267: ("system_test_input_generation", "E"), 268: ("system_test_input_generation", "G"),
    693: ("unit_test_generation", "V"), 694: ("unit_test_generation", "EC"), 695: ("test_oracle_generation", "ECV"),
    696: ("test_oracle_generation", "T"), 697: ("system_test_input_generation", "EV"), 698: ("system_test_input_generation", "T"),
    699: ("system_test_input_generation", "TC"), 700: ("system_test_input_generation", "EO"), 701: ("bug_analysis", "TV"),
    702: ("bug_analysis", "CO"), 703: ("bug_analysis", "E"), 704: ("debugging", "C"), 705: ("debugging", "TO"),
    706: ("debugging", "EV"), 707: ("program_repair", "V"), 708: ("program_repair", "EC"), 709: ("program_repair", "C"),
    710: ("program_repair", "ETO"), 711: ("program_repair", "LV"),
}
MERGED_OLD = {235, 236, 237, 238, 699, 700, 252, 253, 254, 255, 256, 709, 710, 711}   # old GUI and issue rows
for i, (t, what) in TC_ROWS.items():
    note = "Old category merged into this new category." if i in MERGED_OLD else ""
    if what == "N":
        put(i, f"{t}: {task_n[t]}", "Task size (m1 task).", status="scheme changed", code="TASK", issue=note)
    elif what == "R":
        order_ = sorted(COMPS, key=lambda c: (-tc[t][c], COMPS.index(c)))
        put(i, f"{t}: " + ", ".join(f"{c} {tc[t][c]}" for c in order_[:4]), "Most documented components (paper level).",
            status="scheme changed", code="TASK", issue=note)
    else:
        put(i, f"{t}: " + "; ".join(f"{c} {tc[t][c]}/{task_n[t]}" for c in what), f"{R_PL} Within-task count / task size.",
            status="scheme changed", code="TASK", issue=note)
cov = lambda c: [pv(tc[t][c], task_n[t]) for t in TASKS]
put(258, f"{min(cov('C')):.0f}%", "Minimum within-task paper-level C share over six tasks.", status="scheme changed", code="TASK")
put(259, f"{max(cov('C')):.0f}%", "Maximum within-task paper-level C share over six tasks.", status="scheme changed", code="TASK")
put(260, f"{min(cov('T')):.0f}%", "Minimum within-task paper-level T share over six tasks.", status="scheme changed", code="TASK")
put(261, f"{max(cov('T')):.0f}%", "Maximum within-task paper-level T share over six tasks.", status="scheme changed", code="TASK")
EXE4 = ["unit_test_generation", "test_oracle_generation", "system_test_input_generation", "program_repair"]
minE4 = min(pv(tc[t]["E"], task_n[t]) for t in EXE4)
put(262, f"{minE4:.0f}%", "Minimum paper-level E share among unit, oracle, system-input and repair tasks.", status="scheme changed", code="TASK")
put(263, "; ".join(f"{t} {tc[t]['V']}/{task_n[t]}" for t in EXE4), "Paper-level V presence in the four executable-artefact tasks.",
    status="scheme changed", code="TASK")
put(369, tc_prop["debugging"]["E"], "Debugging proposed systems with E present (m1).", status="scheme changed", code="TASK")
put(370, task_n["debugging"], "Debugging proposed systems (m1).", status="scheme changed", code="TASK")

# -- implementation categories (m1 only; choice 2 defines presence views, categories exist only for m1)
CAT_ROWS = {334: ("E", "project_runtime"), 335: ("E", "contained_runtime"), 336: ("E", "emulator_device"),
            337: ("E", "state_management"), 338: ("E", "instrumented_runtime"), 339: ("T", "testing_analysis_tool"),
            340: ("T", "structured_api"), 341: ("T", "repository_interface"), 342: ("T", "ui_device_interface"),
            343: ("T", "shell_command"), 344: ("C", "execution_feedback"), 345: ("C", "task_sut_artifacts"),
            346: ("C", "retrieval"), 347: ("C", "retained_memory"), 348: ("C", "analysis_guided"),
            349: ("L", "staged_workflow"), 350: ("L", "iterative_workflow"), 351: ("L", "stopping_budget"),
            352: ("L", "model_directed"), 353: ("L", "role_separated"), 354: ("O", "execution_logs"),
            355: ("O", "interaction_traces"), 356: ("O", "decision_provenance"), 357: ("O", "coverage_history"),
            358: ("O", "state_history"), 359: ("V", "fault_revelation"), 360: ("V", "task_acceptance"),
            361: ("V", "validity_check"), 362: ("V", "structural_adequacy"), 363: ("V", "behavioural_oracle"),
            364: ("G", "resource_budget"), 365: ("G", "containment"), 366: ("G", "approval_gate"),
            367: ("G", "action_scope"), 368: ("G", "audit_policy"),
            371: ("E", "project_runtime"), 372: ("T", "testing_analysis_tool"), 373: ("E", "instrumented_runtime"),
            374: ("T", "shell_command"), 375: ("C", "execution_feedback"), 376: ("L", "iterative_workflow"),
            377: ("L", "stopping_budget"), 378: ("O", "decision_provenance"), 379: ("G", "resource_budget")}
CAT_NOTE = ("Implementation categories are coded only for the m1 proposed system, so the map covers proposed systems, "
            "not baselines or comparative configurations. Tier = share cut points inferred from the old table (Common >= 33.5%, Rare < 8.65%).")
for i, (c, cat) in CAT_ROWS.items():
    n_ = cat_n.get((c, cat), 0)
    put(i, f"{n_} ({tier(n_)})" if i <= 368 else n_, f"Papers whose m1 proposed system selects {c}: {cat}.", code="UNIT", issue=CAT_NOTE)
for i in [331, 332, 333]:
    put(i, N, "Papers in the implementation map (m1 proposed systems).", code="UNIT", issue=CAT_NOTE)

# -- co-presence and relations (choice 8)
for i, (a, b) in {380: "CV", 381: "TC", 382: "EV", 383: "LO", 30: "EV"}.items():
    put(i, co(a, b), f"m1 proposed systems with {a} and {b} both present.")
for i in [72, 73, 384, 387, 388, 389, 390, 391, 392, 393, 394, 467, 623, 645]:
    put(i, oldv[f"N{i:03d}"], "Design constant of the relation taxonomy (unchanged in coding manual v5).", status="same")
R_RELE = lambda r_: f"m1 proposed systems with {r_} ({REL[r_][0]}->{REL[r_][1]}) established."
R_RELC = lambda r_: f"Candidates for {r_}: both endpoints present in m1."
for i in [12, 31, 395, 655]:
    put(i, E_("D02"), R_RELE("D02"), code="REL")
for i in [13, 396, 656]:
    put(i, C_("D02"), R_RELC("D02"))
put(468, f"{E_('D02')} of {C_('D02')}", R_RELE("D02"), code="REL")
for (ie, ic), r_ in {(397, 398): "C01", (399, 400): "D01", (401, 402): "D03", (403, 404): "C02", (405, 406): "D06",
                     (407, 408): "D08", (409, 410): "C07", (411, 412): "C06"}.items():
    put(ie, E_(r_), R_RELE(r_), code="REL")
    put(ic, C_(r_), R_RELC(r_))
put(413, "No" if rel_enu_total == 0 else rel_enu_total, "Relations coded explicitly_not_used.", status="same" if rel_enu_total == 0 else "changed")
put(414, pct(E_("D03"), C_("D03")), "D03 (V->C) established / candidates.", code="REL")
put(415, pct(E_("C02"), C_("C02")), "C02 (V->L) established / candidates.", code="REL")
put(624, f"{rel_cand_total - rel_est_total:,}", "Pooled candidate relation rows not established (16 relations).", code="REL")
put(625, f"{rel_cand_total:,}", "Pooled candidate relation rows (16 relations).")
put(626, pct(rel_cand_total - rel_est_total, rel_cand_total), "Pooled not-established share.", code="REL")

# -- matched comparisons (choice 3)
R_DIR = "Directional rows = m2 matched comparisons with direction gain, loss or mixed."
for i in [15, 32, 429, 436, 439, 454, 459, 461, 466, 469, 598, 616, 621, 640, 657, 690]:
    put(i, f"{len(DIR):,}", R_DIR, code="MC")
for i in [14, 33, 437, 438, 450, 460, 470, 599, 617, 622, 641, 658]:
    put(i, len(dir_papers), "Papers with at least one directional row.", code="MC")
for i in [80, 427, 431, 684]:
    put(i, len(all_pairs), "Distinct HC pairs (paper, hc_a, hc_b) over all matched comparisons (no screening funnel).", code="MC")
put(685, len({p[0] for p in all_pairs}), "Papers with at least one matched comparison.", code="MC")
for i in [428, 432, 686]:
    put(i, f"{len(MC):,}", "All matched-comparison rows.", code="MC")
for i in [433, 687]:
    put(i, mc_dir.get("none", 0), "Rows without direction (direction = none).", code="MC")
for i in [434, 688, 435, 689]:
    put(i, "not computable", "Funnel exclusion sub-reason.", status="not computable", code="MC",
        issue="The new extraction has no claim-level exclusion reasons; the only non-directional rows are the "
              f"{mc_dir.get('none', 0)} rows with direction none, which cannot be split into the old sub-reasons.")
for i in [426, 465, 676, 677, 678, 679, 680, 681, 682, 683]:
    put(i, "not computable", "Screening-funnel quantity.", status="not computable", code="MC",
        issue="The chosen option uses the directly extracted comparisons without re-screening; no candidate-pair "
              "enumeration or exclusion reasons exist in m2_final.")
put(430, "not computable", "Number of boxes in fig:matched-analysis-transition.", status="not computable", code="MC",
    issue="The old figure shows the screening funnel, which does not exist under the chosen option; the new chain is "
          f"{len(HC)} HCs -> {len(MC):,} comparison rows -> {len(DIR):,} directional rows -> {len(TRADE)} trade-off rows.")
for i in [16, 34, 463, 471, 618, 642, 659, 692]:
    put(i, len(TRADE), f"Trade-off rows = gain_and_loss true ({len(trade_dir)} of them directional).", code="MC")
for i in [17, 35, 472, 619, 643, 660]:
    put(i, len(trade_papers), "Papers with at least one trade-off row.", code="MC")
put(464, len(DIR) - len(trade_dir), "Directional rows without a trade-off.", code="MC")
for i in [455, 691]:
    put(i, dir_single, "Directional rows changing exactly one component letter.", code="MC")
put(456, dir_bundle, f"Directional rows changing several component letters ({dir_noletter} rows name no letter).", code="MC")
STUDY = {440: ("S0182", "TELPA"), 441: ("S0190", "AdvScanner"), 442: ("S0229", "Neuro-symbolic repair"),
         443: ("S0799", "ChatAssert"), 444: (None, "Text-to-testcase"), 445: (None, "KeBugFix")}
for i, (rid, nm) in STUDY.items():
    if rid:
        put(i, study(rid)["rows"], f"Directional rows of {nm} ({rid}).", code="MC")
    else:
        put(i, "not computable", f"Directional rows of {nm}.", status="not computable", code="MC",
            issue=f"{nm} is not in the 154-paper corpus (no title or system-name match).")
s190, s229, s799 = study("S0190"), study("S0229"), study("S0799")
form = lambda s: ("Single + bundle" if s["single"] and s["bundle"] else "Single" if s["single"] else "Bundle") + f" ({s['single']} single, {s['bundle']} bundle)"
put(446, form(s190), "Change form of AdvScanner directional rows.", status="changed" if not (s190["single"] and s190["bundle"]) else "same", code="MC")
put(447, form(s229), "Change form of neuro-symbolic repair directional rows.", status="changed" if not (s229["single"] and s229["bundle"]) else "same", code="MC")
put(448, f"{'Yes' if s229['trade'] else 'No'} ({s229['trade']})", "Trade-off rows of S0229.", code="MC")
put(449, s799["factors"], "Distinct changed factors in ChatAssert (S0799) directional rows.", code="MC")
put(457, s190["bundle"], "AdvScanner bundled directional rows.", code="MC")
put(458, s229["bundle"], "Neuro-symbolic repair bundled directional rows.", code="MC")
put(462, len(trade_papers), "Papers reporting a trade-off row (old: a single study).", status="changed", code="MC")
put(451, dir_task["unit_test_generation"], "Unit-test papers with directional rows.", code="MC")
put(452, "; ".join(f"{t} {dir_task[t]}" for t in TASKS), "Papers with directional rows per task.", status="changed", code="MC")
put(453, "; ".join(f"{t} {dir_task[t]}" for t in ["system_test_input_generation", "debugging"]),
    "Directional papers in system-input and debugging tasks (old: none).", status="changed", code="MC")

# -- RQ4 claims (choice 4)
R_PRIM = "Primary claims = all m2 claims with importance primary."
for i in [18, 36, 81, 475, 483, 556, 569, 611, 628, 638, 662]:
    put(i, f"{len(PRIM):,}", R_PRIM, code="CLAIM")
for i in [82, 476, 482, 639]:
    put(i, len(prim_papers), "Papers with at least one primary claim.", code="CLAIM")
for i in [477, 634]:
    put(i, N - len(prim_papers), "Papers without a primary claim.", code="CLAIM")
put(484, "100.0%", "Denominator row.", status="same")
cmp_, par_, inc_, nom_ = (malign_prim[x] for x in ["compatible metric present", "partially compatible metric only",
                                                    "claim-incompatible metric only", "no metric reported"])
RM = f"Metric alignment of primary claims: direct > indirect > incompatible relevance ({nom_} primary claims have no metric)."
for i in [19, 37, 555, 570, 612, 661]:
    put(i, cmp_, RM, code="CLAIM")
put(571, pct(cmp_, len(PRIM)), f"Share = {cmp_}/{len(PRIM)}.", code="CLAIM")
for i in [557, 572]:
    put(i, par_, RM, code="CLAIM")
put(573, pct(par_, len(PRIM)), f"Share = {par_}/{len(PRIM)}.", code="CLAIM")
for i in [558, 574]:
    put(i, inc_, RM, code="CLAIM")
put(575, pct(inc_, len(PRIM)), f"Share = {inc_}/{len(PRIM)}.", code="CLAIM")
RA = f"Alignment of primary claims; {align_prim[UNCL]} are 'unclear' (outside the four old categories)."
for i in [20, 576, 664]:
    put(i, align_prim[FULL], RA, code="CLAIM")
for i in [21, 578, 665]:
    put(i, align_prim[PART], RA, code="CLAIM")
for i in [22, 39, 580, 601, 614, 630, 666]:
    put(i, align_prim[INCP], RA, code="CLAIM")
for i in [23, 582, 615, 627, 663]:
    put(i, f"{align_prim[NONE]:,}", RA, code="CLAIM")
for i in [38, 600, 613]:
    put(i, align_prim[FULL] + align_prim[PART], "Primary claims fully or partially corroborated.", code="CLAIM")
put(577, pct(align_prim[FULL], len(PRIM)), "Share fully corroborated.", code="CLAIM")
put(579, pct(align_prim[PART], len(PRIM)), "Share partially corroborated.", code="CLAIM")
put(581, pct(align_prim[INCP], len(PRIM)), "Share claim-incompatible.", code="CLAIM")
for i in [583, 629]:
    put(i, pct(align_prim[NONE], len(PRIM)), "Share with no corroboration.", code="CLAIM")
put(568, prim_with_ev, "Primary claims with fully, partially or incompatibly corroborating evidence.", code="CLAIM")
MAP_TXT = "; ".join(f"{lab} <- {', '.join(ps)}" for lab, ps in CLAIM_MAP.items())
EFF = claim_row["Effectiveness (task and diagnostic effectiveness merged)"]
put(485, EFF, f"Merged effectiveness row = primary claims with property effectiveness. Mapping: {MAP_TXT}.", code="CLAIM")
put(486, pct(EFF, len(PRIM)), f"Share = {EFF}/{len(PRIM)}.", code="CLAIM")
put(489, f"merged into the effectiveness row ({EFF})", "Diagnostic effectiveness is merged with task effectiveness.", status="changed", code="CLAIM")
put(490, f"merged ({pct(EFF, len(PRIM))})", "Diagnostic effectiveness is merged with task effectiveness.", status="changed", code="CLAIM")
for (ic, ip), lab in {(487, 488): "Test adequacy", (491, 492): "Efficiency or cost", (493, 494): "Fault revelation",
                      (495, 496): "Other evaluated properties"}.items():
    put(ic, claim_row[lab], f"Primary claims mapped to '{lab}' ({', '.join(CLAIM_MAP[lab])}).", code="CLAIM")
    put(ip, pct(claim_row[lab], len(PRIM)), f"Share = {claim_row[lab]}/{len(PRIM)}.", code="CLAIM")
put(585, prop_prim["fault revelation"], "Fault-revelation primary claims.", code="CLAIM")
put(584, pa[("fault revelation", PART)], "Fault-revelation primary claims partially corroborated.", code="CLAIM")
put(586, pa[("fault revelation", FULL)], "Fault-revelation primary claims fully corroborated.", code="CLAIM")
for i in [587, 588]:
    put(i, "not computable", "Safety/security primary claims.", status="not computable", code="CLAIM",
        issue="The new property field has no safety/security value; such claims are spread over 'validity', "
              "'robustness/stability' and 'other' and cannot be identified without recoding.")
put(589, pa[("adequacy", NONE)], "Adequacy primary claims without corroboration.", code="CLAIM")
put(590, prop_prim["adequacy"], "Adequacy primary claims.", code="CLAIM")
put(591, pa[("effectiveness", NONE)], "Effectiveness (merged) primary claims without corroboration.", code="CLAIM")
put(592, EFF, "Effectiveness (merged) primary claims.", code="CLAIM")
put(593, pa[("effectiveness", FULL)], "Effectiveness (merged) primary claims fully corroborated.", code="CLAIM")
put(594, EFF, "Effectiveness (merged) primary claims.", code="CLAIM")
put(595, pa[("effectiveness", PART)], "Effectiveness (merged) primary claims partially corroborated.", code="CLAIM")
inc_props = Counter(c["property"] for _, c in PRIM if c["alignment"] == INCP)
put(596, f"{inc_props.get('efficiency/cost', 0)} of {align_prim[INCP]} (" + ", ".join(f"{p} {n}" for p, n in inc_props.most_common()) + ")",
    "Property of the claim-incompatible primary claims.", status="changed", code="CLAIM")
put(597, len({k for k, c in PRIM if c["alignment"] == INCP}), "Papers with claim-incompatible primary claims.", code="CLAIM")

# -- metric families (choice 5)
for i in [533, 544]:
    put(i, f"{metric_rows_prim:,}", "Metric entries of primary claims (RQ4 population).", code="METRIC")
mfam = lambda lab: mf[lab]
EFL = "Effectiveness (task and diagnostic)"
for i in [534, 547]:
    put(i, f"merged with task effectiveness ({mfam(EFL)[1]} ECs)", "Diagnostic and task effectiveness are one family.", status="changed", code="METRIC")
for i in [535, 548]:
    put(i, f"merged with task effectiveness ({mfam(EFL)[0]} papers)", "No separate diagnostic class in m1.", status="changed", code="METRIC")
for (iec, ipa, iec2, ipa2), lab in {(536, 537, 545, 546): EFL, (538, 539, 549, 550): "Test adequacy",
                                     (540, 541, 551, 552): "Efficiency or cost", (542, 543, 553, 554): "Fault revelation"}.items():
    for i in (iec, iec2):
        put(i, mfam(lab)[1], f"Distinct ECs linked by primary claims of the matching property ({lab}).", code="METRIC")
    for i in (ipa, ipa2):
        put(i, mfam(lab)[0], f"Papers whose m1 metric_classes include the matching class ({lab}).", code="METRIC")

# -- corroborating evidence (choice 6)
EVR = "Distinct items = unique (paper, type, description, page) over all claims, statistical tests excluded; kinds by keyword mapping."
put(559, len(items), EVR, code="EVID")
put(560, len(item_papers), "Papers with at least one distinct item.", code="EVID")
for i, kd in {561: "manual or human review", 562: "maintainer or developer confirmation",
              563: "security or vulnerability confirmation", 564: "mutation analysis"}.items():
    put(i, f"{kind_n.get(kd, 0)} ({kind_p.get(kd, 0)} papers)", f"Items of kind '{kd}'. {EVR}", code="EVID")
put(565, "; ".join(f"{kd} {n} ({kind_p[kd]} papers)" for kd, n in kind_n.most_common()
                   if kd not in ("manual or human review", "maintainer or developer confirmation",
                                 "security or vulnerability confirmation", "mutation analysis")),
    f"Remaining kinds. {EVR}", status="changed", code="EVID")
put(566, f"{len(ec_with_ev):,}", "ECs linked through claims to at least one item.", code="EVID")
put(567, claim_ev_pairs, "Claim-evidence pairs (all claims, statistical tests excluded).", code="EVID")

# -- artefact availability
for i in [602, 603, 631]:
    put(i, art["A"], "Papers with artefact = A (m1).")
for (ic, ip), v in {(605, 606): "L", (607, 608): "N", (609, 610): "U"}.items():
    put(ic, art[v], f"Papers with artefact = {v} (m1).")
    put(ip, pct(art[v], N), f"Share = {art[v]}/{N}.")
put(604, pct(art["A"], N), f"Share = {art['A']}/{N}.")

# -- benchmarks (choice 14)
put(497, len(recurring), "Benchmark/dataset families with >= 3 papers (tables/benchmark_families_recurring.csv).", code="BENCH")
for i in [498, 501]:
    put(i, 3, "Threshold (design).", status="same")
put(499, len(papers_with_recurring), "Papers using at least one recurring family.", code="BENCH")
put(500, N - len(papers_with_recurring), "Papers using none of the recurring families.", code="BENCH")
OLD_FAM = {502: "Defects4J", 507: "SWE-bench (all variants)", 510: "HumanEval", 515: "QuixBugs", 517: "BugsInPy",
           521: "ConDefects", 524: "Methods2Test", 527: "GitBug-Java", 530: "Themis"}
for i, f_ in OLD_FAM.items():
    put(i, f"{fam(f_)}{'' if fam(f_) >= 3 else ' (below threshold)'}", f"Papers whose m1 benchmarks map to {f_}.", code="BENCH")
FT = {503: ("Defects4J", ["program_repair"]), 504: ("Defects4J", ["unit_test_generation"]),
      505: ("Defects4J", ["test_oracle_generation"]), 506: ("Defects4J", ["system_test_input_generation", "bug_analysis", "debugging"]),
      508: ("SWE-bench (all variants)", ["program_repair"]), 509: ("SWE-bench (all variants)", ["unit_test_generation", "debugging"]),
      511: ("HumanEval", ["program_repair"]), 512: ("HumanEval", ["unit_test_generation"]),
      513: ("HumanEval", ["test_oracle_generation"]), 514: ("HumanEval", ["system_test_input_generation"]),
      516: ("QuixBugs", ["program_repair"]), 518: ("BugsInPy", ["program_repair"]), 519: ("BugsInPy", ["unit_test_generation"]),
      520: ("BugsInPy", ["debugging"]), 522: ("ConDefects", ["program_repair"]), 523: ("ConDefects", ["debugging"]),
      525: ("Methods2Test", ["unit_test_generation"]), 526: ("Methods2Test", ["test_oracle_generation"]),
      528: ("GitBug-Java", ["program_repair"]), 529: ("GitBug-Java", ["program_repair"]),
      531: ("Themis", ["system_test_input_generation"]), 532: ("Themis", ["system_test_input_generation"])}
for i, (f_, tl_) in FT.items():
    split = "; ".join(f"{t} {fam_task(f_, t)}" for t in TASKS if fam_task(f_, t))
    put(i, f"{'+'.join(tl_)}: {sum(fam_task(f_, t) for t in tl_)} [full split: {split or 'none'}]",
        f"Papers using {f_} by new task.", status="scheme changed", code="TASK")

# -- agreement (choice 12)
put(68, "2 independent coders on all 154 papers + first-author adjudication; " + agree_txt,
    "Coding protocol and agreement (tables/agreement_statistics.csv).", status="changed", code="AGREE")

# ---------------------------------------------------------------------------------------------
# 12. "Statement still supported?" for rows whose sentence makes a number-dependent qualitative claim
# ---------------------------------------------------------------------------------------------
Q = {}


def q(ids_, verdict, why):
    for i in ids_:
        Q[f"N{i:03d}"] = (verdict, why)


sigs_all7_top = top3[0][0] == "ETCLOVG"
q([29], "no", f"The most frequent signature is {top3[0][0]} ({top3[0][1]}), ahead of ETCLOVG ({cnt('ETCLOVG')}) and ETCLOV ({cnt('ETCLOV')}).")
q([12, 30, 31], "no", f"E->V is established in {E_('D02')} of {C_('D02')} candidates ({pct(E_('D02'), C_('D02'))}), so co-presence of E and V almost always comes with the relation.")
q([655, 656, 657, 658], "no", f"E->V is established in {E_('D02')} of {C_('D02')} and there are {len(DIR):,} directional rows from {len(dir_papers)} papers, so neither the contrast nor the sparsity holds.")
q([395], "yes" if rel_rank.index[0] == "D02" else "no",
  f"E->V has the highest rate ({R_('D02')}%); next is {rel_rank.index[1]} ({rel_rank.iloc[1]}%).")
q([399, 400, 401, 402, 403, 404], "no", f"E->C {E_('D01')}/{C_('D01')}, V->C {E_('D03')}/{C_('D03')} and V->L {E_('C02')}/{C_('C02')} are established in most candidates.")
q([414, 415], "no", f"V->C and V->L are established in {pct(E_('D03'), C_('D03'))} and {pct(E_('C02'), C_('C02'))} of candidates.")
q([405, 406, 407, 408], "partly", f"T->O ({E_('D06')}/{C_('D06')}, {R_('D06')}%) and V->O ({E_('D08')}/{C_('D08')}, {R_('D08')}%) are no longer rare, though V->O stays below the pooled rate ({pct(rel_est_total, rel_cand_total)}).")
g_rel = {r_: R_(r_) for r_ in ["C06", "C07", "C08"]}
q([409, 410, 411, 412], "partly", f"G->E has the highest Governance rate ({E_('C07')}/{C_('C07')}, {R_('C07')}%) but G->L has the same count ({E_('C08')}/{C_('C08')}), and tool-scope control is no longer rare ({E_('C06')}/{C_('C06')}).")
q([413], "yes", "No relation is coded explicitly_not_used.")
q([624, 625, 626], "no", f"Only {rel_cand_total - rel_est_total:,} of {rel_cand_total:,} candidate rows ({pct(rel_cand_total - rel_est_total, rel_cand_total)}) are not established; most are established.")
ecv_ok = minECV > 85
q([184], "yes" if ecv_ok else "no", f"Minimum paper-level E, C, V share over the years is {minECV:.1f}%.")
q([115], "yes", "E, C and V stay widely documented at paper level in every year (" + ", ".join(f"{y}: E {annual_i.loc[y, 'E_pct']}%, C {annual_i.loc[y, 'C_pct']}%, V {annual_i.loc[y, 'V_pct']}%" for y in years) + ").")
g_txt = " -> ".join(f"{annual_i.loc[y, 'G_pct']}%" for y in years)
g_series = [float(annual_i.loc[y, "G_pct"]) for y in years]
g_monotonic = all(a <= b for a, b in zip(g_series, g_series[1:]))
q([116, 117, 118, 119, 120, 121, 185, 186], ("yes" if g_monotonic else "partly") if largest_incr == "G" else "no",
  f"Paper-level G share by year is {g_txt}; the largest 2024-2026 increase is {largest_incr} ({incr[largest_incr]:+.1f} pp).")
q([89, 90, 113, 114], "no", "No paper in the new corpus is preprint-only; all 154 have a formal venue.")
q([108], "no", "Venues are led by " + ", ".join(f"{o} ({n})" for o, n in list(venue_counts.items())[:3]) + "; there are no arXiv-only papers.")
q([199], "partly", f"Program repair ({task_n['program_repair']}) is among the two largest categories, but system test input generation ({task_n['system_test_input_generation']}) is larger and the counts differ.")
q([210], "yes", f"The four largest categories hold {top4_n} of {N} papers.")
q([196, 635], "partly", "Small task groups still exist but are two categories (" + ", ".join(T(t) for t in small_tasks) + ") with five to six papers.")
c_rng, t_rng = (min(cov("C")), max(cov("C"))), (min(cov("T")), max(cov("T")))
q([258, 259, 260, 261], "yes" if c_rng[0] >= 85 and t_rng[0] >= 85 else "partly",
  f"Across six tasks paper-level C ranges {c_rng[0]:.0f}-{c_rng[1]:.0f}% and T {t_rng[0]:.0f}-{t_rng[1]:.0f}%.")
v_all = all(tc[t]["V"] == task_n[t] for t in EXE4)
q([262, 263], "yes" if minE4 >= 95 and v_all else ("partly" if minE4 >= 85 else "no"),
  f"Minimum E share in the four tasks is {minE4:.0f}%; V: " + ", ".join(f"{t} {tc[t]['V']}/{task_n[t]}" for t in EXE4) + ".")
dbg = lambda c: f"{tc['debugging'][c]}/{task_n['debugging']}"
q([264], "no", f"Debugging papers document E in {dbg('E')} and V in {dbg('V')} at paper level, not a small minority.")
q([265, 266], "no", f"Debugging papers document L in {dbg('L')} and O in {dbg('O')}, so the O-without-L contrast does not hold.")
sti = lambda c: f"{tc['system_test_input_generation'][c]}/{task_n['system_test_input_generation']}"
q([267, 268], "yes" if tc["system_test_input_generation"]["E"] == task_n["system_test_input_generation"] else "partly",
  f"System-input papers document E in {sti('E')} and G in {sti('G')} at paper level.")
q([369, 370], "no", f"{tc_prop['debugging']['E']} of {task_n['debugging']} debugging proposed systems record Execution.")
q([325, 326], "partly", f"ETCLOVG and ETCLOV still differ only in G but cover {cnt('ETCLOVG') + cnt('ETCLOV')} systems ({pct(cnt('ETCLOVG') + cnt('ETCLOV'), N)}); ETCLV is the most frequent signature.")
q([327], "yes" if "".join(c for c in COMPS if c in core_top3) == "ETCLV" else "no", f"The top three signatures ({top_txt}) share an {''.join(c for c in COMPS if c in core_top3)} core.")
q([288], "yes", f"The top three share a {len(core_top3)}-responsibility core.")
q([293], "yes" if max((n for _, n in tail), default=0) <= 2 else "no", f"The largest signature ranked 9th or below occurs in {max((n for _, n in tail), default=0)} papers.")
q([294, 328, 329, 330], "partly", f"{n_sig - 3} signatures lie outside the top three and cover {N - top3_cov} systems; only {len(le2)} occur in at most two papers.")
q([311, 312, 313], "no", f"No paper is excluded; the largest paper-level vs proposed-system gap is {gap[gap_max_c]:.1f} pp ({gap_max_c}), and {len(gaps_le_1_5)} components differ by at most 1.5 pp.")
q([316], "yes" if order_prop == order_paper else "partly", f"Ordering proposed: {''.join(order_prop)}; paper level: {''.join(order_paper)}; no benchmark or comparative studies are set apart.")
q([71, 78, 217, 273, 274], "no", "Every paper has a proposed system in m1, so no benchmark or comparative studies are set apart.")
q([477, 478], "no", "All 154 papers contribute at least one primary claim.")
q([331], "no", "Implementation categories are coded only for proposed systems; baselines are not in the new data.")
q([371], "no", f"Instrumented runtimes ({cat_n[('E', 'instrumented_runtime')]}) and shell interfaces ({cat_n[('T', 'shell_command')]}) are no longer rare.")
q([379], "yes" if max((cat_n[('G', x)] for x in ['action_scope', 'approval_gate', 'audit_policy', 'containment'])) < cat_n[('G', 'resource_budget')] else "no",
  f"Resource budget is still the largest Governance category ({cat_n[('G', 'resource_budget')]} papers).")
q([18, 19, 20, 21, 22, 23, 36, 37, 38, 613, 614, 615, 661, 662, 663, 664, 665, 666, 582, 583], "partly",
  f"Most primary claims still lack corroboration ({pct(align_prim[NONE], len(PRIM))}), but aligned evidence covers {align_prim[FULL] + align_prim[PART]} claims ({pct(align_prim[FULL] + align_prim[PART], len(PRIM))}) rather than a handful.")
q([584], "no" if pa[("fault revelation", PART)] * 2 < prop_prim["fault revelation"] else "yes",
  f"{pa[('fault revelation', PART)]} of {prop_prim['fault revelation']} fault-revelation claims are partially and {pa[('fault revelation', FULL)]} fully corroborated.")
q([589, 590, 591, 592], "partly", f"Most adequacy ({pa[('adequacy', NONE)]}/{prop_prim['adequacy']}) and effectiveness ({pa[('effectiveness', NONE)]}/{EFF}) claims lack corroboration, but not nearly all.")
q([593, 594, 595], "yes", f"Effectiveness is the largest claim type ({EFF} of {len(PRIM)}); {pa[('effectiveness', FULL)]} fully and {pa[('effectiveness', PART)]} partially corroborated.")
q([596, 597], "no", f"Only {inc_props.get('efficiency/cost', 0)} of {align_prim[INCP]} incompatible cases are efficiency/cost claims, from {len({k for k, c in PRIM if c['alignment'] == INCP})} papers.")
q([462, 463], "no", f"{len(TRADE)} trade-off rows come from {len(trade_papers)} papers.")
q([14, 15, 16, 17, 32, 33, 34, 35, 436, 437, 469, 470, 471, 472, 616, 617], "no",
  f"There are {len(DIR):,} directional rows from {len(dir_papers)} papers and {len(TRADE)} trade-off rows from {len(trade_papers)} papers.")
q([455, 464], "no", f"Of {len(DIR):,} directional rows, {dir_single} change one component and {dir_bundle} a bundle; {len(DIR) - len(trade_dir)} have no trade-off.")
q([451, 453], "no", "Directional rows come from every task: " + ", ".join(f"{t} {dir_task[t]}" for t in TASKS) + ".")
q([68], "no", "All 154 papers were coded independently by two coders before adjudication, so agreement statistics are reported.")
q([187, 188, 189, 190], "no", "The task scheme now has six categories and the timeline must be rebuilt from the new corpus.")
q([269], "yes", "Groups below ten papers still exist (" + ", ".join(T(t) for t in small_tasks) + ").")
q([295], "yes", "The top signatures occur in " + ", ".join(str(n) for _, n in top3) + " papers.")
q([497, 498], "yes", f"{len(recurring)} families now meet the threshold (wording 'nine' must change).")
q([499, 500], "yes", f"{len(papers_with_recurring)} papers use a recurring family; the rest use other or new datasets.")
# appendix and cross-task 'All N papers document X' statements
for i, (t, what) in TC_ROWS.items():
    sent = inv.set_index("id").loc[f"N{i:03d}", "sentence"]
    if what not in ("N", "R") and re.search(r"\b[Aa]ll\b|every", sent) and str(oldv[f"N{i:03d}"]).lower().startswith(("all", "22", "28", "nine", "eight", "seven", "12", "19")) and f"N{i:03d}" not in Q:
        full = all(tc[t][c] == task_n[t] for c in what)
        Q[f"N{i:03d}"] = ("yes" if full and i not in MERGED_OLD else ("partly" if full else "no"),
                          f"In {t}: " + ", ".join(f"{c} {tc[t][c]}/{task_n[t]}" for c in what) + " (paper level).")
# tier labels of the implementation map
for i, (c, cat) in CAT_ROWS.items():
    if i > 368:
        continue
    sent = inv.set_index("id").loc[f"N{i:03d}", "sentence"]
    label = re.search(r"'(.*?)'", inv.set_index("id").loc[f"N{i:03d}", "quantity"]).group(1)
    pos = sent.find(label)
    before = sent[:pos]
    # "Common:" (capital C) does not match inside "Less common:", so the last label before the name is its tier
    old_tier = max([(before.rfind(k), k.rstrip(":")) for k in ["Common:", "Less common:", "Rare:"]])[1] if pos >= 0 else "?"
    new_tier = tier(cat_n.get((c, cat), 0))
    Q[f"N{i:03d}"] = ("yes" if old_tier == new_tier else "no", f"Tier label was '{old_tier}', now '{new_tier}' ({cat_n.get((c, cat), 0)}/{N}).")

# ---------------------------------------------------------------------------------------------
# 13. Assemble the workbook
# ---------------------------------------------------------------------------------------------
WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
WORDS.update({"thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "no": 0})


def first_num(s):
    s = str(s).replace("{,}", "").replace(",", "").replace("\\textbf", "").replace("\\%", "%").lower()
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if m:
        return float(m.group(0))
    m = re.search(r"([a-z]+)-([a-z]+)", s)
    if m and m.group(1) in WORDS and m.group(2) in WORDS:
        return float(WORDS[m.group(1)] + WORDS[m.group(2)])
    for w in re.findall(r"[a-z]+", s):
        if w in WORDS:
            return float(WORDS[w])
    return None


rows = []
for r in inv.itertuples():
    o = OUT.get(r.id, {"new": "", "rule": "", "status": "not computable", "issue": "UNMAPPED", "code": "UNMAPPED"})
    status = o["status"]
    if status is None:
        a, b = first_num(r.value), first_num(o["new"])
        status = ("same" if abs(a - b) < 1e-9 else "changed") if a is not None and b is not None else \
                 ("same" if str(r.value).strip() == o["new"].strip() else "changed")
    qv = Q.get(r.id, ("", ""))
    rows.append({"id": r.id, "line": r.line, "location": r.location, "sentence": r.sentence, "old value": r.value,
                 "new value": o["new"], "change": status, "rule used": o["rule"], "issue": o["issue"],
                 "statement still supported?": qv[0], "what the new data support": qv[1], "issue_code": o["code"]})
numbers = pd.DataFrame(rows)
unmapped = numbers[numbers.issue_code == "UNMAPPED"].id.tolist()

ROOT_CAUSES = [
    ("TASK", "Eight-to-six task scheme", "Six-category values; every task-level number and range statement recomputed on six categories; no crosswalk table."),
    ("UNIT", "Paper-level versus proposed-system unit", "Paper level = union over the paper's own m2 HCs plus m1; proposed system = m1; gaps recomputed."),
    ("MC", "Matched comparisons", "Directional rows = direction gain/loss/mixed; no re-screening; trade-off rows = gain_and_loss true."),
    ("CLAIM", "RQ4 primary claims and claim types", "All primary claims; task and diagnostic effectiveness merged; mapping in tables/claim_type_mapping.csv: " + MAP_TXT + "."),
    ("METRIC", "Metric families", "Papers from m1 metric_classes; ECs = distinct ECs linked by primary claims of the matching property (tables/metric_families.csv)."),
    ("EVID", "Corroborating evidence", "Distinct items excluding statistical tests, by keyword-mapped kind with paper counts."),
    ("HCSCOPE", "HC scope", "New totals reported; baseline-HC rows marked 'removed: external baselines out of scope'."),
    ("REL", "Relation rates", "New rates reported as coded (no audit)."),
    ("DATE", "Publication dates", f"DOI first public date of the formal record; arXiv first submission for {n_date_fallback} papers."),
    ("VENUE", "Venues", "PACMSE split into FSE and ISSTA by public Crossref metadata (tables/pacmse_split.csv)."),
    ("PRISMA", "PRISMA", "Venue-eligibility box between screening and full text; full text assessed = 335; boxes in tables/prisma_boxes.csv."),
    ("AGREE", "Agreement", "Agreement and kappa per item plus mode-2 pass rates reported (tables/agreement_statistics.csv)."),
    ("AUTHORED", "Authored items", "Timeline rows marked 'to be re-authored'; reference list in tables/timeline_reference_by_interval.csv."),
    ("BENCH", "Benchmark families", "All SWE-bench variants merged; HumanEval-derived sets under HumanEval; app stores and dataset sources excluded."),
]
issues = pd.DataFrame([{"root cause": t, "code": c, "chosen option (applied)": opt,
                        "rows affected": int((numbers.issue_code == c).sum()),
                        "rows still not computable": ", ".join(numbers[(numbers.issue_code == c) & (numbers.change == "not computable")].id),
                        "affected row ids": ", ".join(numbers[numbers.issue_code == c].id)} for c, t, opt in ROOT_CAUSES])

with pd.ExcelWriter(HERE / "new_old_numbers.xlsx", engine="openpyxl") as xw:
    numbers.drop(columns=["issue_code"]).to_excel(xw, sheet_name="Numbers", index=False)
    issues.to_excel(xw, sheet_name="Issues", index=False)
    for ws in xw.book.worksheets:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 18
        ws.freeze_panes = "A2"
numbers.to_csv(TAB / "new_old_numbers_flat.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------------------------
# 14. Sanity checks (reported, not fixed)
# ---------------------------------------------------------------------------------------------
checks = [("tasks sum to corpus", sum(task_n.values()) == N, ""),
          ("half-years sum to corpus", sum(half_n.values()) == N, ""),
          ("years sum to corpus", sum(year_n.values()) == N, str(dict(year_n))),
          ("signature counts sum to corpus", sum(sig_n.values()) == N, ""),
          ("venues sum to corpus", int(venue_counts.sum()) == N, ""),
          ("PACMSE papers resolved", not pac_unresolved, ", ".join(pac_unresolved)),
          ("artefact codes sum to corpus", sum(art.values()) == N, ""),
          ("paper-level presence >= proposed-system presence", all(pcomp_n[c] >= comp_n[c] for c in COMPS), ""),
          ("relation keys present iff both endpoints present", all(rel.loc[r_, "candidates"] == rel.loc[r_, "both_endpoints_present"] for r_ in REL), ""),
          ("primary claim alignment sums", sum(align_prim.values()) == len(PRIM), ""),
          ("claim-type mapping covers all primary claims", sum(claim_row.values()) == len(PRIM), ""),
          ("HC roles sum", sum(role_n.values()) == len(HC), str(dict(role_n))),
          ("directional + none = all comparisons", len(DIR) + mc_dir.get("none", 0) == len(MC), "")]
dangling = []
for k, r in m2.items():
    Es, Hs = {e["ec_id"] for e in r["ecs"]}, {h["hc_id"] for h in r["hcs"]}
    dangling += [f"{k} EC {e['ec_id']} -> missing {e['hc_id']}" for e in r["ecs"] if e["hc_id"] not in Hs]
    dangling += [f"{k} claim {c['claim_id']} -> missing {x}" for c in r["claims"] for x in c["ec_ids"] if x not in Es]
    dangling += [f"{k} pair {m['pair_id']} -> missing {m['hc_a']}/{m['hc_b']}" for m in r["matched_comparisons"] if m["hc_a"] not in Hs or m["hc_b"] not in Hs]
checks.append(("m2 cross-references resolve", not dangling, "; ".join(dangling)))
checks.append(("claims whose metrics field is a string", not claims_metric_str,
               f"{len(claims_metric_str)} claims in papers " + ", ".join(sorted({k for k, _ in claims_metric_str}))))
empty_hc = [f"{k} {h['hc_id']} ({h['role']})" for k, h in HC if not h["components"]]
checks.append(("HCs with empty components string", not empty_hc, "; ".join(empty_hc)))
checks.append(("unmapped inventory rows", not unmapped, ", ".join(unmapped)))
pd.DataFrame(checks, columns=["check", "passed", "detail"]).to_csv(TAB / "sanity_checks.csv", index=False, encoding="utf-8-sig")

print("rows by change status:", numbers.change.value_counts().to_dict())
print("statement verdicts:", numbers["statement still supported?"].value_counts().to_dict())
for c_, ok, d in checks:
    print(("OK  " if ok else "FAIL"), c_, "|", d[:200])
