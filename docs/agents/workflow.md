# Working in this repository

How work is performed, recorded, and pushed. Plan selection and task lifecycle
are defined by `docs/agents/planning.md`. This document carries
`docs/agents/history/plan.md` §36 — the Autonomous Implementation Protocol that governed the
0.1.x build-out — forward for the sessions after it. §36 stays as that run's
record; decision 82 in `docs/agents/progress.md` records the supersession.

## Session startup

1. `git log --oneline -20` and `git status`. The repository is the truth about
   what has happened; summaries of prior sessions are not.
2. Read `docs/agents/plans/current.md`. If it selects an active plan, read that plan
   and the next task, loading dependencies only as needed. Task files own
   execution status; reconcile them with git before resuming.
3. Read relevant recent completed evidence in `docs/agents/progress.md`, **Operator
   handoff**, and recent **Decisions**. Its pending historical backlog does
   not select the next task or authorize new work.
4. If source has changed since the last green gate, run `scripts/check.sh`
   before starting new work, and fix regressions first.

Do not begin by reading `docs/agents/history/plan.md` in full — that was §36.1's rule, for a
session that had to build everything. Route from `AGENTS.md`'s context map
instead. That original plan retains historical evidence. Use the human contracts mapped
by `docs/agents/historical-contract-map.md` for current technical authority. New plans live in `docs/agents/plans/`.

## Work packages

- `docs/agents/plans/current.md` selects the sole active plan. Dated plan files own
  scope and task order; individual files in `docs/agents/plans/tasks/` own task
  execution status, dependencies, acceptance criteria, and evidence.
  `docs/agents/progress.md` retains completed work-package evidence, chronological
  Decisions, Operator handoff, and unmigrated historical backlog. It is not
  a second mutable task queue.
- Work is done as packages
  with IDs like `VER-009` or `DOC-002`: continue an existing family where one
  fits (`ARC`, `CFG`, `STO`, `HUB`, `SYNC`, `RET`, `DEP`, `VER`, `REP`,
  `OBS`, `OPS`, `REL`, `DOC`, …) or open a new family deliberately.
- One package per commit. The commit message is
  `<WORK-PACKAGE-ID>: <summary>`. A task uses that same existing package ID;
  there is no independent task-ID sequence.
- The task's status/evidence, affected plan/current pointers, and completed
  progress entry are written in the same commit as the work:
  `- [x] ID Title (YYYY-MM-DD, this commit — evidence…)`. Entries carry
  evidence — what was run and what it reported — not just intent.

## The loop, for each package

1. **Select an authorized task.** Follow `docs/agents/planning.md` to create
   or resume the dated plan and its task records before implementation.
   An instruction to implement is sufficient activation authority; drafting
   alone is not. Record authorization and select the next unblocked task
   within that scope. Read-only and draft-only work need no activated plan.
2. **Contract first.** For every change or new plan being implemented, read
   the affected sections of `docs/invariants.md` and use `docs/adr/README.md`
   to find the relevant decisions. Review the proposed behaviour against both.
   Add any new invariant to the register, and update or explicitly supersede
   every affected invariant and ADR, in the same commit as implementation.
   A new architectural decision requires its own ADR. Changes that affect
   neither need no artificial register edit or decision record.
   If behaviour will change, amend the governing document
   in the same change, and record the reasoning as a decision. Where docs and
   code already disagree, fixing the doc to match built behaviour and fixing
   the code to match the doc are both legitimate; choose explicitly and say
   why (decision 77 is the worked example of that choice).
3. Implement, following `docs/agents/conventions.md`.
4. `scripts/check.sh` exits `0`. Run the opt-in suites when the change
   warrants them: `-m live` after Hub-adapter changes, `-m nfs` on the writer
   after storage or mount changes, `--with-build` at release boundaries.
5. Complete the task's acceptance criteria and evidence; update its dated
   plan and current selector as needed. Close the plan only when its scoped
   acceptance criteria are met; retain completed files. Update
   `docs/agents/progress.md` — the completed checkbox entry, plus **Decisions** for
   architectural choices and anything that deviates from a plan or contract,
   with links to the corresponding ADRs, plus **Operator handoff**
   for anything the session cannot perform itself.
6. Commit. Never squash away a package boundary; the history is the audit
   trail the tracker cites.

Before committing, check that the invariant register still states the current
rules, new decisions have individual ADRs and index entries, affected older
ADRs link to amendments or superseding records, task/plan/current pointers
agree, and task and completed work-package evidence record this review.
Review the same set when implementing an already accepted
plan: acceptance does not exempt its implementation from keeping these records
current. The area contracts remain the detailed specifications; the register
collects current constraints and ADRs retain the reasons for them.

This authority split supersedes the former progress-only task selection
(`DOC-010`, 2026-10-17, decision 107). Existing history and pending operator
work remain intact; nothing is migrated or activated just because it exists.

## Decisions

The **Decisions** section of `docs/agents/progress.md` is numbered, append-only, one
topic per decision. A decision states what was decided, the alternative that
lost, and why — future readers get the reasoning, not just the outcome. When a
decision makes standing text in `docs/agents/history/plan.md` or another contract wrong, the
same commit adds a dated, attributed amendment beside that text; the original
is never silently rewritten (plan §30's `OPS-001` note and §36's supersession
note are the pattern).

Every new architectural choice also has a standalone record under `docs/adr/`
and an entry in its index. Use `decision-NNN.md` for the matching numbered
progress decision. If a choice introduces an `AD-nn` requirement in
`docs/architecture.md`, add its `ad-nn.md` record too and cross-link the two;
these are the architectural rule and its implementation rationale. Existing
identifiers and historical decision text are never renumbered or deleted.
When a choice changes, write a new decision and update the older ADR's status
and amendment/supersession links, retaining the original reasoning. Follow the
record fields and provenance rules in `docs/agents/technical-record-policy.md`.

## Remotes and pushing

- `github` — `git@github.com:wtcross/hfcache.git` — the primary public
  repository.
- `forgejo` — `ssh://git@git.lab.example.com:2222/<user>/hfcache.git` —
  the lab mirror.

Pushing is the **maintainer's** step — it needs push access to both remotes,
which contributors do not have; a contribution stops at a proposed change,
and the maintainer lands it. Maintainers push `main` with `--follow-tags` to
both remotes at package boundaries and after every release:

```bash
git push github main --follow-tags
git push forgejo main --follow-tags
```

Never force-push either remote, and never push a tree whose gate is red.
Annotated release tags are pushed only after the deployment they describe
(`docs/agents/release.md`).

## What a session must not do

The hard limits live in `docs/agents/environment.md` and bind any session on
the writer VM: the live archive, the hardening, the timers, and the host are
not test surfaces. In-repository, the same discipline as the archive applies:
nothing is deleted that cannot be explained (`FS-19`, `AD-16`), and no runtime
dependency is added without a recorded decision (`FW-04`).
