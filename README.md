# Replication package

This repository accompanies the article *Harness Engineering for LLM-Based Software Testing: A Systematic Literature Review*.
It contains the search protocol, the study-selection decisions, the final corpus of 154 papers, the coding manual and the
final coding data, and the scripts that recompute the statistics, tables, and figures reported in the article.

## Contents

| Folder | Files | Article section |
|---|---|---|
| `search/` | Search strings, venue list, and per-source search log | Section 3.1 (literature search) |
| `selection/` | Title/abstract screening decisions of the human screeners and the LLM screener, first-author adjudication, agreement report, stage counts, full-text eligibility criteria and decisions of the two models, PRISMA counts | Section 3.1, Fig. 3 |
| `corpus/` | The 154 included papers with citation keys, primary testing task, and ETCLOVG component signature | Section 3.1, Appendix A |
| `coding/` | Coding manual (`coding_prompt_v5.md`) and the adjudicated coding data: `m1_final.jsonl` (task, components, implementation categories, directed relations, evaluation fields) and `m2_final.jsonl` (harness configurations, evaluation configurations, claims, and matched comparisons) | Section 3.2, Sections 4 to 8 |
| `analysis/` | `recompute.py`, which recomputes every reported number from the coding data, the resulting tables in `analysis/tables/`, and the scripts that build the manuscript tables and figures in `analysis/manuscript/` | Sections 4 to 8 |

## Notes

- Screeners are anonymised as `author2` to `author5`; `author1` is the first author, who adjudicated all disagreements.
- Abstracts of screened records and the full texts of the included papers are not redistributed because they are
  copyrighted by their publishers. Each record keeps its title, venue, and link.
- The scripts were written for the authors' working directory. They read the files in this repository, but some paths
  may need to be adjusted to the local layout before running them.
- Statistics in the article can be checked against `analysis/tables/current_numbers_flat.csv` and
  `analysis/tables/agreement_statistics.csv`.
