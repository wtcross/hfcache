# Code, test, and documentation conventions

The enforced part of these conventions lives in `pyproject.toml` — the Ruff
and Pyrefly configuration and the pytest options — and this document is the
part a linter cannot hold: the reasons, and the conventions that live in
judgement rather than rules. When a statement here and a tool's configuration
disagree, the configuration is the contract; change it deliberately or follow
it.

## Source

- **Raise, never assert, in `src/`.** An `assert` disappears under
  `python -O`; a safety check that can disappear is not a safety check. Ruff
  enforces this (`S101` is *not* ignored for `src/`); tests and operator
  scripts may assert, and their per-file ignores say why.
- **Every failure speaks the taxonomy.** Errors and warnings carry the stable
  codes of `docs/cli.md` §5 (`HFERR…`, `HFWRN…`, `HFVER…`, `HFTXN…`, `HFRET…`,
  `HFDEP…`) through `errors.py` and `taxonomy.py`. No stringly-typed failures.
- **Cite requirement IDs.** Comments, docstrings, and tests reference the
  architecture's stable identifiers (`AD-nn`, `FS-nn`, `TX-nn`, `NG-nn`,
  `FW-nn`) and decision numbers directly. A comment states a constraint the
  code cannot show; where the constraint has an ID, the ID is the citation.
- **Time is timezone-aware** (`DTZ` enforced), paths are `pathlib` (`PTH`),
  and `src/` never prints (`T20`) — CLI output goes through the documented
  envelope (`docs/cli.md` §4, §6).
- **Determinism is a feature.** Generated JSON arrays are ordered by the rules
  in `docs/architecture.md` §5.3; two runs over identical state must be
  byte-identical.
- **The runtime dependency set is closed** (`FW-03`): `huggingface-hub`,
  `pydantic`, `typer`, and the standard library. An addition needs a material
  correctness argument and a recorded decision (`FW-04`).
  [Decision 108](../adr/decision-108.md) permits incremental transport
  dependencies; [decision 109](../adr/decision-109.md) permits only the
  bounded non-resuming execution lane. [Decision 124](../adr/decision-124.md)
  adds the actual optional FastMCP protocol transport after committed REST
  acceptance, with independent base/server installs and no workflow authority.
  These scoped additions do not authorize other frameworks.

## Tests

- **The default suite is offline and hermetic.** `tests/conftest.py` strips
  ambient Hugging Face credentials (`docs/security.md` T-07); anything that
  needs network, the live mount, or a build sits behind an opt-in marker
  (`live`, `nfs`, `build`) and is deselected by default.
- **Fakes, not mocks, for the Hub** (`AD-08`). The Hub adapter is injectable
  and the suite uses deterministic fakes; do not monkeypatch
  `huggingface_hub` internals.
- **Every durable format has a golden fixture** (`docs/schemas.md` §11) under
  `tests/fixtures/schemas/`, built by `tests/fixtures/examples.py`. A format
  change updates the fixture in the same change.
- **Crash behaviour is tested by injection.**
  `tests/unit/test_crash_injection.py` interrupts transactions at named
  checkpoints; `tests/unit/test_failure_matrix.py` maps plan §26.6's injection
  points to the tests covering them and asserts that every name it holds still
  resolves — extend the matrix when adding a failure mode, and let its
  assertions catch renames.
- **Warnings are errors** (`filterwarnings = ["error"]`), markers and config
  are strict, and property-based tests (Hypothesis) cover grammar-shaped
  input spaces such as identifiers and repository paths.
- Coverage runs with branch measurement. `verification.py` and `reporting.py`
  stood at 100% branch coverage at 0.1.3; do not let core-module coverage
  regress.

## Documentation

- **`docs/` is normative.** `architecture.md`, `configuration.md`,
  `schemas.md`, `cli.md`, and `security.md` are contracts the implementation
  is written against; `operations.md`, `recovery.md`, `consumers.md`, and
  `deployment-centos-stream-10.md` are runbooks kept true to the deployment.
- **Invariants and decision records accompany implementation.** For every
  change or plan being implemented, review the affected sections of
  `docs/invariants.md` and the relevant records indexed by `docs/adr/README.md`.
  Add new invariants, maintain affected ones, and add or explicitly supersede
  ADRs in the same work package. Reuse existing requirement IDs; retain
  historical reasoning and link its replacement. The workflow and ADR index
  specify the record format and review obligations.
- **Plans and tasks have one authority each.** Follow
  `docs/agents/planning.md`: `docs/agents/plans/current.md` selects the active plan,
  the dated plan defines scope/order, and task files own execution status and
  acceptance evidence. Use existing work-package IDs and retain completed
  records. `docs/agents/progress.md` holds the completed audit, Decisions, and
  Operator handoff rather than duplicate active-task checkboxes.
- **Two tests read the docs at run time.**
  `tests/unit/test_transactions.py` parses the §7.3–§7.5 checkpoint tables of
  `docs/architecture.md` and requires the documented sequence to be the
  implemented sequence; `tests/unit/test_verification.py` reads
  `docs/cli.md`. Editing those regions is editing test input — run the gate.
- **Amendments, not rewrites, for historical records.** Where later reality
  makes standing plan text wrong, add a dated, attributed amendment beside it
  and record the decision; `docs/agents/history/plan.md` §30 and §36 carry the pattern.
  Living runbooks are edited directly.
- **Voice.** Dense, declarative, reasons attached. Tables hold enumerable
  facts; prose holds reasoning. Requirements say **must** and **never** and
  carry stable IDs so code and tests can cite them.

## Formatting

- `ruff format`; line length 100 for Python; docs wrap near 80 columns.
- Imports are absolute (`TID` bans relative imports); `tests` is first-party
  alongside `hfcache`.
- Module docstrings open by stating the contract the module implements and
  the document that holds it.
