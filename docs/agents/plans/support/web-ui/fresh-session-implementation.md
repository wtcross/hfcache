# Resume the accepted product-focused Web UI plan

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `98f696cc0ae28a4dc4f55c9cb0fd2b06e22738642be174c27378d1a44f40ec87`,
original content SHA-256 `4328440b8d1aa1aa704df590cb81498be495d8226417900c5536ebb364dffe01`.
Historical proof hashes identify the original artifacts, not this edited record.

Resume implementation in `/home/tyler/Projects/hfcache` on `feat/web-ui`.
This prompt authorizes resuming the deliberately paused plan and completing
WEB-022 through WEB-026 in dependency order. WEB-021 is already complete at
`2c44f2d`; inspect current Git before relying on that baseline. Preserve all
uncommitted work, including the existing WEB-022 implementation. Leave the root
`node_modules/` directory untracked. Do not create a second goal if `/goal`
already supplied one.

## First actions

1. Follow `AGENTS.md`, including `rtk` prefixes, Git history/status, workflow,
   planning, current selector and relevant progress/decision/handoff records.
2. Read `docs/agents/plans/current.md` and
   `docs/agents/plans/2026-10-20-plan-web-ui.md`. Resume that paused plan as
   active under this instruction; WEB-022 remains `in_progress`, not completed.
3. Read the WEB-022 task, current testing strategy, acceptance matrix and the
   two existing acceptance JSON files under this directory. Read affected
   contracts/invariants/ADRs before further implementation.
4. Read `docs/agents/environment.md` before actions outside the repository.
   Preserve existing fixtures, credentials, original locks and unknown state.

## Accepted change: do not reopen the old blocker

The user explicitly accepted the product-focused proposal on November 1, 2026:
“i accept the new proposal”. It is now governing authorization, not a pending
question. The later pause is deliberate and does not revoke this acceptance.

The adopted proposal is
`.scratch/web-022-validation/web022-proportionate-acceptance-proposal.md`.
Its original text is preserved in the adjacent `.before-adoption.md` file.
The adoption checkpoint is
`.scratch/web-022-validation/root-source16-installed78-adoption16.json`.
Historical blocked audits are superseded by that explicit acceptance.

Retain all 85 behaviors owned through WEB-022 and all 95 at final acceptance.
Use appropriate unit/component, integration and direct installed workflow
evidence. Actual installed native/rootless Chromium, Firefox and WebKit checks
at root and `/management` remain required. Run deeper domain, fault and
privilege combinations where they matter, without repeating every scenario
in every profile/browser/prefix combination.

Mandatory normal-runner 85×18/95×18 acceptance has been replaced. The existing
instrumented runner, `--require-through`, `--final` and
`--with-web-functional` remain optional diagnostics with their strict protocol
unchanged. Do not expand their lifecycle machinery, invent a new schema,
framework, binder or evidence model, weaken security to admit a wrapper, or
claim an optional command passed when it did not run.

The full source/build gate remains required:

```bash
rtk proxy scripts/check.sh --require-web --with-build
```

Later2026-11-01 user direction supersedes legacy requirements in this historical
resume prompt: ignore the historical frontend plugin moving forward, deprecate it when the
new web UI is complete, and do no further plugin maintenance or validation.
WEB-025 is proportional deprecation/handoff; preserve legacy source/history,
licenses, shared helpers and the live installation. Reuse actual passing
evidence with a stated unchanged-subsystem justification. Retain original
failed exits, named passing clauses within failed runs, uncertainty and scope.
Missing product behavior still blocks completion. A passing continuation does
not turn an earlier failed aggregate into a passing run.

These changes are recorded in the active agent records, testing strategy,
acceptance matrix, development guide, existing ADR143/147 amendments, ADR index
and script inventory. Review the uncommitted changes; do not recreate them.

## Immediate implementation work

The ledger was not edited during the pause handoff. Through WEB-022 it contains
73 completed and 12 unfinished cases:

- AUTH-01 through AUTH-07: pending.
- ROUTE-02, ROUTE-03 and ROUTE-06: in progress.
- HOST-10 and RELEASE-04: pending.

The ten cases owned by later tasks remain pending. First reconcile these
12 entries against retained evidence using the existing JSON schema. Inspect
actual commands, exits, node/callback identities, source/artifact hashes and
observations before updating a status. Any test-layer adjustment needs an
explicit behavior-based justification, not a desire to make a row green.
Run another product test only for a concrete required clause still unproved.

Useful evidence and findings already identified:

- Current runtime is clean source
  `f829857ec045ce4616055e357e7d6aa7047287ca`, candidate `0.2.78`.
  Main source metadata remains distinct; do not rewrite it to the test-release
  version. The full last green source gate is Gate20:
  `.scratch/web-022-validation/gate20-result.json` (`fa2b6d86…`) and
  `gate20-shadow1-result.json`. It passed 9,645 backend, 4,051 frontend,
  581 historical frontend and 16 wheel checks, with 1,543 frozen files unchanged.
- The last installed execution checkpoint is
  `.scratch/web-022-validation/root-source16-installed78-checkpoint12.json`.
  It records current README, dataset, Administration, worker/MCP, client overlap
  and configuration scopes. Its old acceptance-basis blocker is historical.
- AUTH-05: retain the 44 named passing clauses in the raw failed
  `.scratch/web-022-rootless-fixture4/rootless76-auth-writeguard1-reuse-result.json`
  (`2465c78e…`), the passing `rootless76-auth-origin-protocol2-reuse-result.json`
  (`cb1644c6…`), passing `rootless76-auth-cross-origin4-reuse-result.json`
  (`a905ca44…`), and current authenticated TLS/ASGI tests from Gate20.
  Preserve Firefox response-event/body uncertainty and the unobserved Basic
  attribution of cross-origin form cases. Do not restart multipart, response-body
  collector or HTTP-event diagnostic loops.
- ROUTE cases: current three-engine/two-prefix installed model/README/dataset
  runs supply actual pinned detail, Files, header and reload/back-forward
  observations. Native dataset2 passes six cells; rootless dataset1 retains
  two passing Chromium cells inside a failed aggregate, and dataset2 passes
  only the four unfinished Firefox/WebKit cells. Preserve that distinction.
- HOST-10 / RELEASE-04: use the actual native activation
  `.scratch/web-022-fresh-fixture2/native16-phaseC1-result.json`
  (`0fba94fe…`), current rootless activation records, current bootstrap/asset
  observations and executed hardening/install tests. Validate exact artifacts
  and role boundaries; metadata or source review alone is insufficient.
- Existing native76 maintenance, Repair, schedule and observer effects already
  have real qualifications. Relevant implementations were compared from
  `d4d99f8d` to current `f829857e`; maintenance/Repair/command, HostControls,
  schedule and observer core paths are unchanged. Reuse only with that precise
  justification. Anchors include M10 qualification `5e5b7ee4…`, Repair3
  `68b2e41a…`, schedule union `cd798799…`, observer `e9a78770…` / `d08b35d9…`
  and completion UI `42e758a2…`. Do not repeat their accepted effects.
- Configuration's original Apply/conflict/reload and explicit dirty-discard
  follow-ups can cover separate clauses together. Preserve the original failed
  aggregate; a clean single aggregate is not the newly accepted requirement.
  The earlier Library lookup failure remains unexplained despite a successful
  bounded query attempt. Preserve it without claiming a fix or repeating the
  diagnostic merely to obtain a green aggregate.

No gate, build or browser run was started after adoption. Existing
`run-gate21.py` and `run-gate21-shadow1.py` under the validation scratch directory
are prepared derivatives of the successful gate launcher, not executed results.
No Gate21 TMPDIR or final source freeze was created. Review/reuse them only
after source owners release their edits and inexpensive checks pass. They run
as the login user with the production NAS hidden by an empty read-only mount
inside a private mount namespace. Do not run the gate against the live archive.
Include these new handoff files and all other intended new source files in the
final gate inventory; the prepared launcher must not silently omit untracked
documents. Keep the unrelated root dependency directory excluded.

Run these existing inexpensive checks after record changes, before an expensive
gate; do not repeat gates without changed behavior, failure or a task requirement:

```bash
rtk uv run --locked --extra server --extra mcp python scripts/check-docs.py
rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_web_plan.py
rtk git diff --check
```

## Fixture and preservation limits

Root coordinates all guest/protected/browser mutations. Delegate source-only
work with disjoint file ownership. Revalidate ownership, boot and current state
before any guest reuse; old PIDs and ports are locators, not authority.

- Native2 records: `.scratch/web-022-fresh-fixture2/`, SSH46323,
  boot `9b4dcb96-6fdc-4d56-bc65-49f4aee47278`.
  Last browser source SHA is `6a681b7e…`; it was stopped with exit0.
  The original scheduled SDK pending file inode95048553 remains unknown;
  preserve its content/inode and never replay or delete it.
- Rootless4 records: `.scratch/web-022-rootless-fixture4/`, SSH46325,
  boot `9cac37cb-e191-4111-be19-166eda4d9f11`.
  Last browser source SHA is `d407d495…`; it was stopped with exit0.
  Preserve original guard/lock1790 and NFS read-only. Final config has29
  disabled repositories, SHA `df9b4a7c…`, with all seven publications intact.
- Never replay native operation `5a4d8703327836302d722708537d08ab`, or rootless
  Applies `1dc6b7fd053c10caa558f4cb7c3c32a9`,
  `74c9794a906b4f2eaf098cf4b894b079`,
  `c00f41e4b2bf4d2d63f6afadae90658d`,
  `21f81fd4609c79f0fde586fdbe1e0277`.
- Other old VMs/containers include unresolved operations. Do not stop, reset,
  replay or delete them, their original locks, stores or disks. Preserve user
  download caches retained under `/var/tmp/web022-retained-hf-download-cache1/`
  and their original HOME aliases. PEM/key/token/credential paths are
  metadata-only; never hash or print private key bodies.
- Root has about1.5GB free and home about250MB at pause. Recheck before builds.
  No new VM/image/model download is needed for ledger reconciliation. Never
  delete uncertain evidence to create space.
- No production/NAS workload or change, installed predecessor interface uninstall, security
  weakening, archive initialization, force kill, merge, push or tags.

## Continue through completion

Finish only when WEB-022–026 are completed and committed, the plan is completed
and its active selector cleared, with all95 behaviors accounted for and all
production/operator holds honest. Report commit IDs, principal checks and
artifact/evidence locations. If genuinely blocked after resumption, start a fresh
blocked audit; do not inherit the old three-turn count or reopen the already
accepted proposal as an unanswered question.
