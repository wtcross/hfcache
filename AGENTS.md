# Agent context router

`hfcache` archives complete revisions of public Hugging Face model and dataset
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
2. The tail of `docs/progress.md` — current state, **Operator handoff**, and
   the numbered **Decisions** log. It is the authoritative work-package
   tracker.
3. `docs/agents/workflow.md` — how work is selected, committed, and recorded.
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
| Understand the system | `docs/architecture.md` §1–§4: mission, decisions `AD-01`–`AD-18`, non-goals |
| Change code, any area | The contract for that area (rows below), then `docs/agents/conventions.md` |
| Storage layout, atomicity, crash recovery | `docs/architecture.md` §5–§7 |
| Configuration keys or validation | `docs/configuration.md` |
| Durable JSON formats | `docs/schemas.md`, and `docs/agents/release.md` on the drill a format change requires |
| CLI surface, exit codes, error taxonomy | `docs/cli.md` |
| Threat model and controls | `docs/security.md` |
| A new feature or work package | `docs/plan.md` (start at its Plan Map) and the Decisions log in `docs/progress.md` |
| Cut or deploy a release | `docs/agents/release.md`, then `docs/deployment-centos-stream-10.md` §13–§14 |
| Operate or debug the live archive | `docs/operations.md`, `docs/recovery.md` |
| Consumer-side behaviour | `docs/consumers.md` and `examples/copy-revision.py` |
| Host, systemd, SELinux | `docs/deployment-centos-stream-10.md`, `packaging/`, `docs/agents/environment.md` |

## Non-negotiables

- **Docs are contracts.** Behaviour that contradicts `docs/` is changed by
  changing the contract first, in the same commit, with the reasoning recorded
  (`docs/architecture.md` §9; `docs/agents/workflow.md`).
- **Tests parse the docs.** `tests/unit/test_transactions.py` parses the
  checkpoint tables in `docs/architecture.md` §7, and
  `tests/unit/test_verification.py` reads `docs/cli.md`. A documentation edit
  can fail the suite; run the gate.
- **The gate is `scripts/check.sh`** — lock check, format, lint, types, the
  default test suite, and a build. Every commit passes it.
- **Commits** are `<WORK-PACKAGE-ID>: <summary>`, one work package per commit,
  with `docs/progress.md` updated in the same commit.
- **No new runtime dependencies** without a recorded decision
  (`docs/architecture.md` `FW-03`/`FW-04`).
- **Never delete what you cannot explain** (`FS-19`, `AD-16`) — a rule for the
  archive, applied to this repository as well.

## Commands

```bash
uv sync                          # locked dev environment (uv, CPython 3.14)
scripts/check.sh                 # the quality gate
scripts/check.sh --with-build    # plus a wheel install smoke test
uv run pytest -m live            # opt-in: contacts the Hugging Face Hub
uv run pytest -m nfs             # opt-in: needs the live NFS mount (writer only)
uv run pytest -m build           # opt-in: builds artifacts in a throwaway venv
```

## Agent docs

| Document | Contents |
| --- | --- |
| `docs/agents/workflow.md` | Session protocol, the work-package loop, decisions, pushing |
| `docs/agents/conventions.md` | Code, test, and documentation conventions, with reasons |
| `docs/agents/environment.md` | The writer VM, the live archive, and the hard limits there |
| `docs/agents/release.md` | Release checklist: gates, format drill, deploy, tag, push |
