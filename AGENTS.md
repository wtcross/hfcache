# Agent context router

`hfcache` archives complete revisions of Hugging Face model and dataset
repositories at resolved immutable commit SHAs onto NFS-backed ZFS storage, and
publishes them as immutable, manifest-verified ordinary-file trees. `README.md`
is the human overview; `docs/` holds the contracts the implementation is
written against.

This file is the entry point for coding agents — a router, not a manual. Read
what the task in front of you needs and nothing more: several documents below
are large, and each states its own authority. Paths are plain backticked
references deliberately, so nothing here forces them into context; read them
with your file tools when the map says to. `CLAUDE.md` is a symlink to this
file — edit this one.

## Every session, before anything else

1. `git log --oneline -20` and `git status` — trust the repository over any
   summary of prior sessions, including compacted context.
2. `docs/agents/plans/current.md` — the sole active-plan selector. If active, read
   that dated plan and its next task; load other tasks only for dependencies
   or relevant context. Task files own execution status. No active plan does
   not authorize starting an old backlog item.
3. Relevant recent entries in `docs/agents/progress.md`, **Operator handoff**, and
   the numbered **Decisions** log — historical evidence and outstanding
   operator/backlog context, not the active task queue.
4. `docs/agents/workflow.md` — how work is committed and recorded.
   Nothing lands outside that loop.

**This working copy may be on the production writer VM**
(`hfcachewriter.lab.example.com`), where `/srv/hfcache` is a live NFS
archive. Before touching anything outside the repository, read
`docs/agents/environment.md` and its hard limits. The three that matter most:
never write under `/srv/hfcache` outside the application's own code paths,
never weaken SELinux or systemd hardening to make something pass, and never
run `hfcache archive init` — the archive exists.

## Context map

| Task at hand | Read |
| --- | --- |
| Understand the system | `docs/invariants.md` navigation, then `docs/architecture.md` §1–§4: mission, decisions `AD-01`–`AD-21`, non-goals |
| Change code, any area | The affected sections of `docs/invariants.md`, the area contract (rows below), and `docs/agents/conventions.md`; use `docs/adr/README.md` to load only relevant decisions |
| Storage layout, atomicity, crash recovery | `docs/architecture.md` §5–§7 |
| Configuration keys or validation | `docs/configuration.md` |
| Durable JSON formats | `docs/schemas.md`, and `docs/agents/release.md` on the drill a format change requires |
| CLI surface, exit codes, error taxonomy | `docs/cli.md` |
| REST server, authentication, operation receipts, or API-backed CLI | `docs/api.md`, `docs/server.md`, `docs/api-client.md`; then the affected contract rows below |
| Read-only MCP transport, tools, or example client | `docs/mcp.md`, `docs/security.md`, `docs/consumers.md`; retain the nine-tool allowlist and whole-archive trust boundary |
| Threat model and controls | `docs/security.md` |
| Draft, activate, resume, or close a plan; add a task | `docs/agents/planning.md` and `docs/agents/invariants.md`, then `docs/agents/plans/current.md` and the relevant dated plan/task; implementation authorization permits activation, while a draft alone does not |
| A new feature or work package | The planning row above, affected `docs/invariants.md` sections, and relevant records from `docs/adr/README.md`; use `docs/agents/historical-contract-map.md` for former plan requirements |
| Introduce or change an invariant or architectural decision | `docs/agents/technical-record-policy.md`, `docs/invariants.md`, `docs/adr/README.md`, and `docs/agents/workflow.md`; update the register, affected ADRs, contracts, and tracker in the same work package |
| Cut or deploy a release | `docs/agents/release.md`, then `docs/deployment-centos-stream-10.md` §13–§14 |
| Operate or debug the live archive | `docs/operations.md`, `docs/recovery.md` |
| Consumer-side behaviour | `docs/consumers.md` and `examples/copy-revision.py` |
| The Cockpit plugin (`cockpit/`) | `docs/cockpit.md`; operator install/usage docs in `docs/cockpit-plugin/`; then the contract rows above for whatever it drives |
| Host, systemd, SELinux, rootless containers | `docs/containers.md`, `docs/deployment-centos-stream-10.md`, `packaging/`, `docs/agents/environment.md` |

## Non-negotiables

- **Docs are contracts.** Behaviour that contradicts `docs/` is changed by
  changing the contract first, in the same commit, with the reasoning recorded
  (`docs/architecture.md` §9; `docs/agents/workflow.md`).
- **Plan before implementation.** Keep one active plan selected by
  `docs/agents/plans/current.md`. Store plans as
  `docs/agents/plans/YYYY-MM-DD-plan-<slug>.md` and one task per work package in
  `docs/agents/plans/tasks/`, following `docs/agents/planning.md`. Create task records
  before execution, maintain them in the implementation commit, and preserve
  completed plans/tasks. Keep small changes proportional with a brief plan
  and one task. Existing backlog is activated only within authorized scope.
- **Tests parse the docs.** `tests/unit/test_transactions.py` parses the
  checkpoint tables in `docs/architecture.md` §7, and
  `tests/unit/test_verification.py` reads `docs/cli.md`. A documentation edit
  can fail the suite; run the gate.
- **Keep invariants and ADRs current.** Every change or plan being implemented
  must review the affected invariants and decisions. Add new invariants to
  `docs/invariants.md`; record new architectural decisions in `docs/adr/`,
  and amend or explicitly supersede affected records in the same commit.
  Start at each index and load relevant sections, not the entire ADR history.
- **The gate is `scripts/check.sh`** — lock check, format, lint, types, the
  default test suite, and a build. Every commit passes it.
- **Commits** are `<WORK-PACKAGE-ID>: <summary>`, one work package per commit,
  with task evidence, relevant plan/current updates, and the completed
  `docs/agents/progress.md` entry in the same commit.
- **No new runtime dependencies** without a recorded decision
  (`docs/architecture.md` `FW-03`/`FW-04`).
- **Never delete what you cannot explain** (`FS-19`, `AD-16`) — a rule for the
  archive, applied to this repository as well.

## Commands

```bash
uv sync --locked --extra server --extra mcp # full locked development environment
scripts/check.sh                 # the quality gate
scripts/check.sh --with-build    # plus a wheel install smoke test
uv run --locked --extra server --extra mcp pytest -m live  # opt-in: contacts Hub
uv run --locked --extra server --extra mcp pytest -m nfs   # opt-in: live NFS
uv run --locked --extra server --extra mcp pytest -m build # isolated wheel smoke
```

Both extras are required to collect the complete offline test suite. The base
reader CLI and REST-only production installations remain separate supported
profiles; see `docs/server.md` and `docs/mcp.md`. Live/NFS markers retain the
host and archive restrictions above.

## Agent docs

| Document | Contents |
| --- | --- |
| `docs/agents/workflow.md` | Session protocol, the work-package loop, decisions, pushing |
| `docs/agents/planning.md` | Plan/task authority, activation, lifecycle, templates, and resumption |
| `docs/agents/conventions.md` | Code, test, and documentation conventions, with reasons |
| `docs/agents/environment.md` | The writer VM, the live archive, and the hard limits there |
| `docs/agents/release.md` | Release checklist: gates, format drill, deploy, tag, push |
