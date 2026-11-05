# REL-020: Restore exact committed legacy prune compatibility and prepare0.3.4

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | OPS-028 |
| Execution | Existing coordinator; no new agents or unrelated acceptance framework |

## Scope and acceptance

Necessary actual-host conformance follow-up within the original end-to-end scope.
Genuine installed technical-refresh pilot4050dbaa9aeecb8b0523ae43adf84c7f failed
HFVER007/exit40, originalresult/run a8ec217e preserved; never replay it automatically.
Read-only diagnosis identifies two valid committed prune journals from2026-07-26,
3be9fd9c706c461f8c8e82bdab21dd08 / ba5e084dc0824131a01b3f5220209f8d,
SHA d57c56be47d2c865440e4fa4491fd0198d8d1285cbdea316e3eeb9f40f161844 /
e26c540f5388c52aa2687af5a086d9cad4b29bad89a1e453169157e0fc769444.
Their exact10-checkpoint sequence is produced by5dc8d0a^, before RET008 added
containers_removed on2026-07-27. Do not edit/delete/rewrite old archive evidence.

Teach the checker only that exact old successful committed sequence with an
actual completion timestamp and no error. Do not change today's checkpoint
sequence, newwriter open-checkpoint enforcement, other impossible combinations,
unsupported schemas/identities, unfinished refusal or deletion/replay authority.
Complete full writer-guard regression, original bytes preservation, exact old
producer/history compatibility and strict release gate; prepare matching clean
immutable0.3.4 artifacts using existing tools. No new format, dependency, CIL,
permission, launcher/profile or browser behavior. Preserve original eight scope.
Actual protected local deployment, selected refresh/new distinct intent and
one bounded backfill remain OPS029 after fresh backup/drain/NFSRO/original-lock
handoff. Completed OPS028 original-request retirement stays intact.

## Contracts, invariants, and ADRs

Review TX03–TX07, INV018, architecture7.4, schemas10 and discovery capture guards.
Record exact original-source compatibility and amend decision068 with narrow
later interpretation; decision166 records the explicit compatibility exception. All immutable evidence remains unchanged.

## Validation

| Requirement | Smallest meaningful check | Gate | Result |
| --- | --- | --- | --- |
| Exact old successful committed form | Typed10-checkpoint fixture + full CatalogWriter capture, old bytes unchanged | scripts/check.sh --require-web --with-build | PASS focused and strict gate |
| Strict current/unknown/unfinished behavior | Current writer cannot skip containers_removed while open; failed/needs_operator/missingcompletion/error/othermissing/reordered/unknown reject | Same gate | PASS focused and strict gate |
| Matching immutable0.3.4 and deployed handoff | Existing clean source, pinned bundle/image/manifest siblings and actual new-image foundation; unchanged boundary evidence retains scope | Same gate + immutable receipts | PASS matching source/artifacts/foundation; actual deployment OPS029 |

## Execution notes and handoff

Original eight-package acceptance remains. Original stuck request is permanently
retired_unknown/f096fda0 with historical uncertainty/handles preserved. Genuine
selected Sync943f7560 succeeded/up-to-date, zero download/prune, HFWRN011 accurately
retained. Metadata pilot failed before supplemental record capture; backfill has
not begun. Read-only inventory156 current publications and immutable manifest
projections is prepared, five proposed32/32/32/32/28 batches. Current production
is manual-writer0.3.3/NFSRW/Enforcing, archive/configuration/Hubtrue, othergrantsfalse,
calendarsdisabled/nativewritersmasked, guard/bridgeinactive. Actual role startup/
preflight and oldnamespaceclosure/newkeeper434678 are qualified. No permission
reset, original request replay, manual archive write, init, reboot, disconnect,
NASsetting/otherhost/push/tag/registry publication is authorized.

## Completion evidence

Completed2026-11-05. Strict `scripts/check.sh --require-web --with-build`
PASS9948 backend/52 deselected, three locked install profiles,179 wire definitions,
3809 unit/4169 combined web,16 sandboxed built browser, actual200% zoom, real API
React read fixture and16 wheel cases.1671s overall;1287 frozen names/hashes
unchanged. Inner gate raw log SHA79c38bf188838dcef6ea46d523f2f3a3962d65aae1769fff2af673f8db7cd7c9; outer
shadow log4719850c records the isolation/UID scope separately. Focused165 pass
and authentic2-failure red reproduce the actual guard refusal. Source compatibility
branch permits only exact successful committed legacy sequence with nullerror and
valid completion; all new/open/unknown guards remain strict. No archive edits.

Clean source `9756c70f939f0a94aae28eb6c1a2d776c886b0e9`, tree
`343019d5d00de10f237d558048114fe8af3f66c1`. Reproducible wheel eb031be2,
UI40c4324a, app418edbe7; whole release source snapshot16aecd26 and unchanged
frontend-only snapshot1e53b9fa are deliberately distinct scopes. All93 nonapp
pins and124 other application wheel members match0.3.3; only transactions.py
changes. Existing worker/Caddy/launcher/CIL proofs retain original scope.
Actual new-image foundation PASS14.29s/loge227db97; web/backend reproducibility
PASS14.14s/log0312b7d4; image build PASS29.25s/log4064e210. Both33-input mode
siblings/pure renders prepared, expected47-file indexes27f6aa39/bea2840d.
OCI66341376B SHA0214a4d6. Full pins in
`/var/tmp/rel020-validation/release-handoff-candidate1.json`, SHA
`e8625328d089d86abb2575dfb6a582fcafe13484948849efc97a858eb31fb730`.
No publication/tag/push, production selection or completion inferred.

TX03–TX07/INV018, architecture7.4, schemas10, discovery and decisions068/166
reviewed/amended together. Current11-step checkpoint table and current writer
ordering remain unchanged; original2 journals and all immutable archive evidence
are preserved. Focused factual docs checks follow the frozen runtime gate.
OPS029 resumes protected compatibility deployment and fresh affected Sync/refresh
UI checks plus one bounded backfill. Original request retirement remains intact;
production still writer0.3.3/RW/Enforcing until separate reviewed host steps.


Focused red reproduces actual unsupported old-completed-sequence refusal in
both checkpoint checker and full CatalogWriter:2 expected failures/10 passes,
retained `/var/tmp/rel020-validation/focused-red1.log`. New exception is exact
committed10-step legacy form, nullerror and completion>=lastcheckpoint; current
open writer still cannot skip containers_removed. Original archive bytes untouched.
OPS029 defaultgate1 passed9935 backend/build/three locked profiles1358.63s,
1284 frozen names/hashes unchanged, log12d17fdf. Six scoped actual NFS readonly
checks passed2.20s. This is predecessor runtime evidence; new strict release gate
and actual successful refresh/backfill remain required. New ADR166 introducing
change is this commit; package identity stays in task/agent records to satisfy
public-document audience rules. Initial doccheck rejected an internal package
field in that new human ADR; remove it without changing the technical decision.

Focused checker/transaction/supplemental storage/refresh regression PASS165 in
12.28s, including13 new legacy-boundary cases; Ruff format/lint pass. Whole
CatalogWriter capture succeeds with old evidence unchanged; nonlegacy impossible
committed sequences still refuse. Strict release gate now required; source and
factual inputs will remain frozen for that run.

Final factual documentation alignment PASS217 human documents/29 helpers and69 focused docs checks; no runtime input changed after strict frozen gate.
