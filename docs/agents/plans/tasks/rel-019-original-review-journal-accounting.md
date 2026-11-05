# REL-019: Correct bounded original-review journal accounting and prepare 0.3.3

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | REL-018 |
| Execution | Existing coordinator; no new model or delegated acceptance framework |

## Scope and acceptance

Necessary conformance follow-up discovered during OPS-028 actual original-key
review, within the user's end-to-end implementation and credential-use authority.
Preserve the original eight packages and all their acceptance criteria. Correct
journal enumeration/read accounting so621 valid resolved journals can complete
review; explicitly cap at1024 journals,1MiB each/8MiB aggregate including sentinel.
Preserve whole-journal validation, unresolved/unknown refusal, deadline and all
locks/fences/permissions. No runtime dependency, durable/wire format or replay.
Prepare clean-source0.3.3 matching immutable release artifacts with existing tools;
never replace immutable0.3.2 trees. Actual deployment/recovery remains OPS-028,
then writer transition/pilots/backfill OPS-029. No push, tag or image publication.

## Contracts, invariants, and ADRs

Review/amend INV-023, original-intent contract and ADR164 with bounded accounting
and root-provisioned whole-host-history prerequisites. Existing architectural
choice is retained; no new decision or permission is introduced.

## Validation

| Requirement | Smallest meaningful check | Required gate | Result |
| --- | --- | --- | --- |
| Real621-journal shape and1024 boundary | Local fully typed committed journals, actual retirement/fence and unchanged journal evidence | `scripts/check.sh --require-web --with-build` | PASS focused red/green77; strict gate9935 backend |
| Limits and unresolved evidence |1025 journals, unfinished final journal and existing per-file/aggregate byte ceilings refuse without fence | Same gate | PASS focused limit/refusal checks and strict gate |
| Matching immutable0.3.3 source/artifacts | Existing clean source/build/manifest/image/foundation and changed-boundary checks; preserve/reuse unchanged worker/Caddy/browser proof scopes | Same gate plus release receipts | PASS matching artifacts/foundation; unchanged proof scopes retained |

## Execution notes and handoff

The actual installed0.3.2 reader reports621 transaction journals,2875196B total,
largest13907B, all JSON entries. Exact application `_archive_review` refuses
HFAPI005 because its shared1024 work budget charges621 enumeration plus621 reads
and sentinel. Original request remains unknown; no catalog-refresh replay or
manual archive/control-store edits. Earlier missing original host-history guard
and packaged empty roots were separately provisioned under full backup/drain/
original locks, preserving all grants and Enforcing/NFSRO. This task fixes the
remaining source defect and prepares a matching release; it does not claim those
production acceptance criteria are complete.

## Completion evidence

Completed2026-11-05. Strict `scripts/check.sh --require-web --with-build`
PASS9935 backend, three locked installations,179 wire definitions,3809 unit/
4169 combined web,16 built browser, actual200% zoom, real API React read fixture
and16 installed-wheel cases. Gate1645.03s, raw log SHA
`fec7fe00121bb8010f608620a56f2efa13249859efbabe123ce128adfbee0dc4`,
1284 frozen inputs/names unchanged. Outer shadow receipt17a744e7 is separate
from the inner gate log. Only factual completion records change afterwards.

Clean artifact source `1652b8f1df0d4b10f6b790c7225b3e7b8fdad0b5`, tree
`d33ca44352d6307b581d0c18faccc75010e387d8`, source snapshot
`1e53b9fae49c2cc0fc1f9a6dfb2d873db0bf58279d4026d706920d77c7869ef4`.
Matching wheel a9cba884, UIc9df46e1, app661da09f; full immutable pins in
`/var/tmp/rel019-validation/release-handoff-candidate1.json`, SHA
`0c06f4318cec6b06b6e76192bd8a395052bc8ab1c34b739fd07070f59c2374e5`.
Both47-file mode inputs/renders prepared; expected indexes f1c55ed2/a638f833.
OCI66333696B SHA8256c970 retained. Actual new-image foundation PASS23.98s,
log b533e346. Reproducible web/backend build and image build pass.
All93 nonapplication locked dependencies unchanged. Of125 application wheel
members only intent_routes.py changes. Worker/launcher/Caddy/CIL/peer inputs
are byte-identical; prior actual worker/Caddy proofs retain original scopes,
with fresh installed checks still required. No registry publication or tag.

INV023, ADR164 and original-review contract reviewed/amended together;
no new dependency, format, permission or architectural decision. OPS-028 resumes
for protected0.3.3 installation and genuine installed original-key retirement;
OPS-029 remains pending. NFSRO/Enforcing/archive=false still hold; production
original authority remains empty and historical outcome unknown.


Focused red reproduces the genuine621/1024 and late-unfinished-journal failure
as QueryLimitError in MetadataReader._consume; initial local fixture setup typo
snapshot.archive_id was corrected before this red proof and is not counted as
production defect reproduction. Red log `/var/tmp/rel019-validation/journal-red1.log`
is retained. Fix adds an explicit1024-journal count before body reads and budgets
1 sentinel +1024 enumeration +1024 reads, preserving1MiB/8MiB byte ceilings.
Final focused intent HTTP/store/review checks PASS77 in9.36s, including real
621/1024 retirement,1025 refusal, final unfinished evidence and both byte ceilings,
with original journal bytes preserved and no job receipts/replays. Matching
0.3.3 version metadata is prepared; strict source/web/build gate and matching
immutable artifact criteria now pass. Existing0.3.2 installation is untouched by
this source edit; original disposition authority is still empty/unknown.
