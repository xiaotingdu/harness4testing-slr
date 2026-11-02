# Search string (frozen 2026-10-01)

Date rule: first public date between 2024-01-01 and 2026-06-30 (see "Date rule per source").
Fields: title, abstract, author keywords (where available).

## Search string

(A AND B) OR (H AND C)

A (LLM):
("large language model*" OR "language model*" OR LLM* OR GPT* OR ChatGPT
 OR "LLM-based agent*" OR "coding agent*" OR agentic)

B (testing tasks):
("software testing" OR "test generation" OR "test case generation" OR "unit test*" OR testcase*
 OR "test oracle*" OR "assertion generation" OR "metamorphic testing" OR "differential testing"
 OR "test amplification" OR "test migration" OR "test repair" OR "code coverage"
 OR fuzz* OR "test input generation" OR "test program generation"
 OR "GUI testing" OR "GUI exploration" OR "UI exploration" OR "mobile app testing" OR "Android testing"
 OR "web testing" OR "REST API testing" OR "end-to-end testing"
 OR "bug detection" OR "static analysis"
 OR "fault locali*" OR "bug locali*" OR "issue locali*" OR "defect locali*"
 OR "program reduction" OR "program repair" OR "bug fix*" OR "patch generation"
 OR "bug reproduc*" OR "issue reproduc*" OR "reproduction test*" OR "crash reproduction" OR "bug replay"
 OR "issue resolution"
 OR "GitHub issue*" OR "SWE-bench")

H (harness):
("harness engineering" OR "agent harness" OR "AI harness" OR "runtime harness")

C (software engineering context):
("software engineering" OR "software testing")

A AND B retrieves LLM-based work on testing tasks. H AND C retrieves work that names the harness concept in a
software engineering context without necessarily using the terms of A or B.

## Rendering notes

- "x locali*" matches localization/localisation/localize/localise. Databases that do not accept a wildcard
  inside a quoted phrase (arXiv) receive the expanded forms, e.g. "bug localization" OR "bug localisation";
  arXiv stems query terms, so singular forms also match plurals.
- Databases that cap the query length (IEEE Xplore: 25 terms; arXiv request length) receive A and B split into
  chunks of four terms; the union of all A-chunk AND B-chunk queries plus H AND C equals the full string.
- ACM DL: the string is entered in the Title, Abstract and Keyword fields of the ACM Full-Text Collection.
- Venue sweep: all main-track papers of the target venues are collected and the string is applied locally to
  title and abstract (03_manual/venue_fill_filter_v2.py).
  Abstracts come from Crossref, else OpenAlex; records with no abstract in either source (2,073 of 8,293)
  are matched on title only. Local matching has no keyword field and no stemming (plural forms and the
  wildcards of the string are handled by the regular expressions).

## Date rule per source

| Source | First public date |
|---|---|
| arXiv | submission date of the first version (API filter submittedDate) |
| IEEE Xplore | earliest of Online Date and the first day of Meeting Date |
| ACM DL, venue sweep | earliest of Crossref published-online, published-print and created |

Applied in 02_exports/v2/first_public_dates.py and merge_v2.py.

## Included papers of the current corpus not retrieved by the string

The string retrieves 117 of the 127 included papers (02_exports/v2/v2_corpus127_check.csv). The 10 papers below
are added through snowballing (backward/forward citation search), reported as such in the method section:

| Task | Paper | Why the string does not match |
|---|---|---|
| UTG | MuMuTestUp: Mutation-based Multi-Agent Test Case Update | no term of A in title/abstract ("multi-agent") |
| ORACLE | RAG-Driven multiple assertions generation with large language models | written "assertions generation" |
| FUZZ | CoverFuzz: A Coverage-Guided and General-Purpose Fuzzing Framework | abstract says "large models"; no term of A |
| FUZZ | DeepExploitor: LLM-Enhanced Automated Exploitation of DeepLink Attack in Hybrid Apps | no term of B (exploitation) |
| GUI | Using large language models to test voice user interfaces | no term of B (voice UI testing) |
| BUG | DeFiScope: Detecting Various DeFi Price Manipulations with LLM Reasoning | no term of B (DeFi price manipulation) |
| DEBUG | Face It Yourselves: An LLM-Based Two-Stage Strategy to Localize Configuration Errors via Logs | no term of B ("localize configuration errors") |
| DEBUG | Isolating Compiler Bugs by Generating Effective Witness Programs With Large Language Models | no term of B ("isolating compiler bugs") |
| DEBUG | Root Cause Analysis of RISC-V Build Failures via LLM and MCTS Reasoning | no term of B (root cause analysis) |
| APR | ReAPR: Automatic program repair via retrieval-augmented large language models | published in Software Quality Journal, which is outside the swept venues and the searched databases |
