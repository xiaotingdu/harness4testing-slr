# Title/abstract screening criteria (identical for the human screener and the LLM; C1/C2 wording fixed 2026-10-01)

Judge each record from its title and abstract only.

Decision values:
- Include: all four conditions are satisfied or cannot be ruled out.
- Exclude: at least one condition is clearly not met. Give the first condition that fails (C1, C2, C3 or C4).
- Uncertain: the title and abstract do not allow a decision (the record goes to full-text assessment).

Conditions:
- C1 Primary research: the paper proposes a method, tool, system, framework or operational workflow, or it
  empirically evaluates an LLM-based workflow or agent on a software-testing task (empirical studies and
  benchmark papers that run such workflows count). Surveys, position papers, tutorials, editorials, proceedings
  front matter and keynotes do not satisfy C1.
- C2 LLM at inference time: the workflow calls a generative LLM (e.g. GPT, Llama, Claude, DeepSeek, Qwen) or an
  agent built on one. Work that only uses smaller pre-trained code models such as CodeBERT or CodeT5, or where the
  LLM is only the system under test, does not satisfy C2.
- C3 Software-testing task: the workflow performs one of unit-test generation; test oracle and assertion
  generation; input generation and fuzzing; GUI, mobile and system testing; bug analysis; debugging and fault
  localisation; program repair; issue reproduction and resolution; or it produces a testing artefact, action or
  judgement. Code generation, code completion, documentation and similar tasks do not satisfy C3.
- C4 Harness mechanism: the abstract mentions at least one operational mechanism such as execution feedback,
  tool use, iterative refinement, verification, sandboxing, memory or context management. A pure one-shot prompt
  with no execution or feedback step does not satisfy C4; if the abstract gives too little information, choose
  Uncertain.

Duplicates: if two records are versions of the same paper, the later-listed one is marked DUP with the record_id of
the other.
