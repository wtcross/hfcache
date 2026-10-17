# Working in this repository

How work is selected, performed, recorded, and pushed. This document carries
`docs/plan.md` §36 — the Autonomous Implementation Protocol that governed the
0.1.x build-out — forward for the sessions after it. §36 stays as that run's
record; decision 82 in `docs/progress.md` records the supersession.

## Session startup

1. `git log --oneline -20` and `git status`. The repository is the truth about
   what has happened; summaries of prior sessions are not.
2. Read the tail of `docs/progress.md`: the current work section, **Operator
   handoff**, and the most recent entries under **Decisions**.
3. If source has changed since the last green gate, run `scripts/check.sh`
   before starting new work, and fix regressions first.

Do not begin by reading `docs/plan.md` in full — that was §36.1's rule, for a
session that had to build everything. Route from `AGENTS.md`'s context map
instead; the plan is read when the task needs it.

## Work packages

- `docs/progress.md` is the authoritative tracker. Work is done as packages
  with IDs like `VER-009` or `DOC-002`: continue an existing family where one
  fits (`ARC`, `CFG`, `STO`, `HUB`, `SYNC`, `RET`, `DEP`, `VER`, `REP`,
  `OBS`, `OPS`, `REL`, `DOC`, …) or open a new family deliberately.
- One package per commit. The commit message is
  `<WORK-PACKAGE-ID>: <summary>`.
- The tracker entry is written in the same commit as the work:
  `- [x] ID Title (YYYY-MM-DD, this commit — evidence…)`. Entries carry
  evidence — what was run and what it reported — not just intent.

## The loop, for each package

1. **Contract first.** For every change or new plan being implemented, read
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
2. Implement, following `docs/agents/conventions.md`.
3. `scripts/check.sh` exits `0`. Run the opt-in suites when the change
   warrants them: `-m live` after Hub-adapter changes, `-m nfs` on the writer
   after storage or mount changes, `--with-build` at release boundaries.
4. Update `docs/progress.md` — the checkbox entry, plus **Decisions** for
   architectural choices and anything that deviates from a plan or contract,
   with links to the corresponding ADRs, plus **Operator handoff**
   for anything the session cannot perform itself.
5. Commit. Never squash away a package boundary; the history is the audit
   trail the tracker cites.

Before committing, check that the invariant register still states the current
rules, new decisions have individual ADRs and index entries, affected older
ADRs link to amendments or superseding records, and the work-package entry
records this review. Review the same set when implementing an already accepted
plan: acceptance does not exempt its implementation from keeping these records
current. The area contracts remain the detailed specifications; the register
collects current constraints and ADRs retain the reasons for them.

## Decisions

The **Decisions** section of `docs/progress.md` is numbered, append-only, one
topic per decision. A decision states what was decided, the alternative that
lost, and why — future readers get the reasoning, not just the outcome. When a
decision makes standing text in `docs/plan.md` or another contract wrong, the
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
record fields and provenance rules in `docs/adr/README.md`.

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
