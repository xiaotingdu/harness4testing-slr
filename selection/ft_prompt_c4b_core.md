# Full-text assessment: harness as core contribution (C4b, strict reading)

You assess primary studies for a systematic review of LLM-based software-testing harnesses. A harness is the set of
runtime non-model mechanisms around the LLM: Execution environment (E), Tools (T), Context construction (C), Loop
control (L), Observation (O), Validation (V), Governance (G). Every record below already satisfies the other criteria,
including C4 (its own system feeds execution results or tool output back to the LLM at run time).

For each record ID listed at the end, read `fulltext_txt/<record_id>.txt`: the abstract, the introduction (including
any contribution list) and, where needed, the overview of the approach. Every page begins with `=== PAGE n ===`. Judge
only from that text. Work independently: do not open any other assessment file.

## Condition
- Satisfied: the abstract AND the introduction present an identifiable runtime harness mechanism (E, T, C, L, O, V or
  G), or an integration of such mechanisms, as a principal methodological novelty of the paper. A harness contribution
  that is explicitly co-primary with another contribution qualifies. Assess the contribution statements collectively,
  regardless of their order; when there is no contribution list, use the introduction's main "we propose" statement.
  Static analysis, symbolic execution or search techniques qualify only when their runtime integration with the LLM is
  itself a principal novelty. Automated runtime context construction that is central to the method qualifies, whether
  or not the injected knowledge was built offline (for example retrieval and injection of a mined or distilled
  knowledge base, or automatically extracted and reused information).
- Not satisfied: the principal novelty concerns prompt wording, a model or its training/fine-tuning, a dataset or
  benchmark, empirical findings, or a standalone analysis or search technique, with the harness only supporting that
  contribution. Naming a system or listing its components is not evidence that the harness is the core contribution.
  Context construction means automated runtime selection, transformation or updating of the LLM's context; fixed
  prompt wording does not count. When the principal contribution is an empirical comparison and the authors themselves
  describe the proposed framework as a simple pipeline or baseline, the harness is not a co-primary contribution. An
  ablation is not required.
- The verdict is `satisfied` or `not_satisfied`. A `satisfied` verdict must quote one sentence verbatim from the
  abstract and one from the contribution list or main proposal statement (each at most 40 words, copied exactly).

## Output
Output one JSON object per line (JSON Lines), one line per record, nothing else:
{"record_id": "S0001", "C4b_core": "satisfied" | "not_satisfied", "abstract_page": "1", "abstract_quote": "...",
 "contribution_page": "2", "contribution_quote": "...", "mechanism": "C,V", "rationale": "one sentence on why the
 mechanism is central or only supporting"}
For `not_satisfied`, quotes may be empty strings; give the principal novelty in `rationale`.
