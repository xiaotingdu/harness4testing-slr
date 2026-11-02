# Coding manual: LLM-based software-testing harnesses (identical instructions for every coder)

You code primary studies for a systematic review of LLM-based software-testing harnesses. For each record ID listed at
the end, read `search_redo_2026/07_fulltext/fulltext_txt/<record_id>.txt` completely. Every page begins with
`=== PAGE n ===`. Judge only from that text. Work independently: do not open any other coding or assessment file.

## Unit
Code the paper's own proposed system (one harness configuration). Baselines, ablation variants and systems by others
are not coded.

## Evidence rule
Every positive code (task, a present component, each selected implementation category, an established or
explicitly-not-used relation) must cite the page and quote one supporting sentence verbatim (at most 40 words,
copied exactly). If you cannot cite such a passage, use the negative or not-reported code.

## 1. Primary testing task (one label)
Decide by the paper's principal evaluated endpoint and unit of work, not by intermediate activities (running tests,
locating code, generating candidate patches). Labels:
- `unit_test_generation`: unit-level tests; includes reproduction tests written as unit tests, and unit-level test
  update or evolution after code changes.
- `test_oracle_generation`: assertions, oracles, metamorphic relations, specifications used as oracles.
- `system_test_input_generation`: fuzzing, GUI, mobile, web, API, protocol and system-level test inputs or scripts;
  includes crash or bug reproduction through system-level inputs, exploit or proof-of-concept generation, and GUI test
  migration or repair of GUI test scripts.
- `bug_analysis`: endpoint is a defect or vulnerability judgement, classification or explanation (including static
  vulnerability detection), not a repair or a ranked location.
- `debugging`: endpoint is a suspicious program location or a diagnostic explanation of an observed failure
  (fault localisation, root-cause analysis, issue localisation).
- `program_repair`: endpoint is the correctness of a generated patch; includes repository-level issue resolution
  (e.g. SWE-bench) and repair of flaky or non-idempotent tests.

## 2. Components (ETCLOVG)
A component is `present` only when a concrete non-model mechanism of the proposed system fulfils the responsibility and
is active in the reported workflow. A conceptual mention or future work does not count. Components are defined by
responsibility, not by tool; one mechanism may fulfil several responsibilities.
- E Execution: runs the SUT or generated artefacts in a controlled state (build environments, containers, test runners,
  emulators, state reset, process isolation).
- T Tool interface: exposes testing operations to the model or workflow controller (compiler/testing APIs, coverage or
  mutation tools, debuggers, repository or AST interfaces, UI/device interfaces, shell commands).
- C Context and memory: automatically supplies task- and SUT-specific information to the model (retrieved code,
  specifications, bug reports, failing tests, execution feedback, analysis results, retained history). Fixed prompt
  wording alone does not count.
- L Lifecycle: controls ordering, repetition and termination (generate-execute-revise loops, retry policies, stopping
  rules, staged pipelines, multi-agent coordination).
- O Observability: makes runtime state and evidence inspectable or retained (model-call records, tool traces, execution
  logs, coverage histories, screenshots, decision histories, provenance). Only records that are stored and can be
  inspected or retrieved later count; execution output passed straight to the model is Context, not Observability.
- V Verification: decides within the workflow whether an artefact or action is valid and what SUT behaviour establishes
  (compilation/execution checks, assertion validation, differential or mutation testing, crash reproduction, regression
  validation). Analysis done only after all runs, for the paper's evaluation, is not V.
- G Governance: constrains operations and resources (permissions; command, file, network scopes; execution timeouts;
  token or cost caps enforced by a non-model harness mechanism; approval gates; sandbox containment as a constraint). A cap on the number of iterations, retries
  or repair rounds is a Lifecycle stopping rule (L: stopping_budget), not Governance.
Boundary rules (apply them before marking a component present):
- L requires a mechanism that controls ordering, repetition or termination: a repetition, retry or revision loop; a
  termination or stopping policy; a staged pipeline of two or more distinct stages (model or non-model) whose order the
  harness controls; or multi-agent coordination. Building a prompt and making one model call, with no further stage,
  is not L.
- O requires stored, later-inspectable records of the run (model-call logs, tool or interaction traces, execution
  logs, coverage or state histories, decision histories, provenance). Such records count even when packaged in a final
  report. Saving a generated artefact (a test, patch or fuzz program) alone is not O.
- Classify budgets and checks by enforcement and workflow role. A resource constraint that the system enforces at
  runtime is G, even when its value is configured for an experiment. An externally imposed campaign duration alone is
  not G. Iteration, retry or repair caps are L. A check performed inside the workflow can be V; an assessment performed
  only for the paper's evaluation is not V.
- Automatic selection of task- or SUT-specific input (a candidate cut, top-k limit or retrieval scope) supports C. A
  context-size or retrieval-time rationale alone does not establish G. Also assign G when the paper evidences runtime
  enforcement of a resource or permission constraint; one mechanism may fulfil both responsibilities.
- A model or API generation setting alone (maximum output tokens, temperature, context-window size) does not establish
  G. G requires an evidenced non-model harness mechanism enforcing a resource or permission constraint, whether per
  operation or across a run. Caps on iterations, retries, repair rounds or actions per planning step are L;
  constraints on which actions are permitted are G.
For each component give `status`: `present`, `explicitly_absent` (the paper states the system does not use it), or
`not_reported`. For a present component choose one or more implementation categories:
- E: contained_runtime, emulator_device, instrumented_runtime, project_runtime, state_management
- T: repository_interface, shell_command, structured_api, testing_analysis_tool, ui_device_interface
- C: analysis_guided, execution_feedback, retained_memory, retrieval, task_sut_artifacts
- L: iterative_workflow, model_directed, role_separated, staged_workflow, stopping_budget
- O: coverage_history, decision_provenance, execution_logs, interaction_traces, state_history
- V: behavioural_oracle, fault_revelation, structural_adequacy, task_acceptance, validity_check
- G: action_scope, approval_gate, audit_policy, containment, resource_budget
Select a category only when you can cite a page and a verbatim sentence for that category; give one evidence entry per
selected category. Use `other` with a short description only when no category fits.

## 3. Directed relations
Assess only these 16 relations, and only when both endpoint components are present. A relation is `established` only
when the paper states or unambiguously depicts that the target directly consumes an output, observation or control
decision of the source; a path through an intermediate component is not a direct relation. `explicitly_not_used`
requires positive evidence. Otherwise use `not_established`. A fixed order of steps in a pipeline is not a control
relation: C03 (L->T) and C04 (L->E) require a lifecycle mechanism that selects, retries, resets or terminates the
target according to the current state. D06 (T->O) requires that tool calls or results are stored as records.
Decision rules for the relations coders most often disagree on:
- C01 T->E: established when a tool operation exposed to the model or controller (e.g. a run-test, build, shell or
  device command) starts or configures Execution. Not established when the harness simply runs the SUT as a fixed
  step without a tool interface between the decision and the execution.
- Before deciding C03 or D01 either way, actively seek qualifying evidence in the text or an unambiguous depiction; do
  not require literal state terminology or every element in one sentence. C03: identify the state-dependent tool
  selection, skipping or repetition. D01: identify the execution observation and the context or retained memory it
  directly updates; a path solely through Verification or another intermediate responsibility does not establish D01,
  and D03 is assessed independently. Accept positives that meet this standard; use `not_established` when support is
  insufficient and `explicitly_not_used` only for positive evidence of non-use.
- C03 L->T: established when the lifecycle chooses which tool to call, whether to call it, or calls it again,
  according to the current state (including a model-directed agent loop choosing tools). A tool invoked once at a
  fixed position is not.
- C04 L->E: established when the lifecycle re-executes, retries, resets or terminates Execution according to the
  current state (e.g. re-running tests after each repair, resetting the emulator after a crash). Executing once at a
  fixed position is not. Relations are direct: where L controls T and only T invokes E, C03 and C01 do not establish
  C04.
- D03 V->C: established when a workflow verification outcome, including the diagnostic evidence produced by that
  check (failing assertion, compile or oracle error), is added to Context or retained there; a separately worded
  judgement is not required. If the V outcome only decides whether to stop or retry, code C02 only. Code D01
  independently, only when a direct flow of execution observations into Context is evidenced.
- C01 T->E tool operations invoke or configure Execution. C02 V->L verification outcomes determine continuation, retry,
  revision or termination. C03 L->T lifecycle control selects or schedules tool operations. C04 L->E lifecycle control
  schedules, retries, resets or terminates Execution. C05 C->L context or retained state is explicitly used in
  lifecycle decisions. C06 G->T governance constrains tool permissions, scope or invocation. C07 G->E governance
  constrains execution permissions, resources or environment. C08 G->L governance constrains lifecycle budgets,
  approvals or stopping.
- D01 E->C execution observations are added to or update context. D02 E->V execution observations are consumed by
  Verification. D03 V->C verification outcomes are added to or update context. D04 O->C recorded state or traces are
  retrieved into context. D05 O->V recorded state or traces are consumed by Verification. D06 T->O tool calls or results
  are recorded by Observability. D07 E->O execution state or outcomes are recorded by Observability. D08 V->O
  verification decisions or evidence are recorded by Observability.

## 4. Evaluation (paper level)
- benchmarks: names of benchmarks or subject sets used (list; [] if none named).
- metric_classes (one or more): AV artefact validity; TE task effectiveness; SA structural adequacy (coverage etc.);
  FR fault revelation; EC efficiency and cost; HPQ human or practical quality; DS diversity or stability.
- verification_classes, i.e. how the paper's evaluation experiments establish outcomes, not the system's internal
  Verification component (one or more). Select a class only when the paper's evaluation actually uses it to decide
  reported outcomes:
  SR static or reference comparison (matching outputs against ground-truth labels, reference locations, reference
  tests or text, without executing them); BE build or execution check (the evaluation compiles or runs the generated
  artefacts and counts compilation, execution or pass outcomes); TO task-specific acceptance oracle (a predefined
  oracle that decides task success, e.g. hidden or developer tests for patches, crash or bug reproduction against the
  known fault, a fail-before/pass-after check); SI strengthened independent evidence (mutation analysis, differential
  or cross-checking against an independent tool or second oracle); HE human confirmation (authors, participants,
  developers or maintainers inspect, rate or confirm outputs, including confirmed bug reports and CVE assignment);
  LJ LLM-based judgement.
  Coverage measurement alone is a metric (SA), not a verification class. Apply each class definition independently:
  executed acceptance tests can receive both BE and TO; add SR only for an actual static or reference comparison, not
  because the executed tests are reference tests; SI requires evidence that the check plays a strengthened,
  independent role, not merely the presence of a named technique.
- models: the LLMs (with version if stated) used by the proposed system.
- baselines: compared approaches (list; [] if none).
- repeated_runs: `yes` (multiple runs reported), `no`, or `not_reported`; uncertainty_reported: `yes` if variance,
  confidence intervals or statistical tests are reported, else `no`.
- cost_reported: `yes` if monetary, token or time cost of the proposed system is reported, else `no`.
- artefact: A available (code or data link to the proposed system), L limited (partial, on request, or only data),
  N unavailable (stated not released or proprietary), U unclear or unstated; give the URL if any.

## Output
Output one JSON object per line (JSON Lines), one line per record, nothing else:
{"record_id": "S0001", "system_name": "...",
 "task": {"label": "...", "page": "...", "quote": "..."},
 "components": {"E": {"status": "present", "page": "...", "quote": "...", "other": "",
                      "categories": [{"name": "project_runtime", "page": "...", "quote": "..."}]},
                "T": {...}, "C": {...}, "L": {...}, "O": {...}, "V": {...}, "G": {...}},
 "relations": {"C01": {"status": "established", "page": "...", "quote": "..."}, ...only relations whose endpoints are both present},
 "evaluation": {"benchmarks": [], "metric_classes": [], "verification_classes": [], "models": [], "baselines": [],
                "repeated_runs": "...", "uncertainty_reported": "...", "cost_reported": "...", "artefact": "A", "artefact_url": ""},
 "note": "one sentence on any hard decision"}
For negative codes, `page` and `quote` may be empty strings.
