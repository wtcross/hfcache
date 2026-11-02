# WEB-028: Preserve unsaved configuration during reload

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Protect unsaved configuration and streamline Library browsing](../2026-11-02-plan-web-drafts-and-library.md) |
| Depends on | None |
| Authorization | User authorized implementation and activation on 2026-11-02 |

## Scope and acceptance

Change manual installed-configuration reload so a failed read cannot erase
admitted unsaved work within the same authenticated authority.

1. When the configuration draft or an admitted local editor buffer is dirty,
   Reload opens an accessible decision with **Keep editing** and **Reload and
   replace draft**. Explain that edits are replaced only after a successful
   read. Keep editing receives initial focus; Escape cancels, focus stays in
   the dialog while open and returns to the invoking control after cancellation.
   Cancellation issues no GET or POST and changes no existing readiness.
   Bind the decision to the reviewed authentication and draft generation;
   dismiss it if either changes. A stale confirmation cannot replace newer work.
2. On confirmation, keep the exact original base, prepared intent, dirty state
   and visible raw repository/settings/JSON form values while the bounded GET
   runs. Disable edits, validation, preview and Apply during replacement, and
   retire prior validation/preview readiness. Navigation protection remains
   active. Keep one RAM-only draft; add no draft persistence or auto-merge.
3. Fully decode and scope-check the new configuration under the existing read
   budget before replacing base, prepared intent and editor buffer together.
   Reset the editor after success even if `base_revision` is unchanged. A fresh
   base token must never be attached to old edits, and old previews stay retired.
4. Transport, API/domain, malformed-protocol, identity-check and capacity failures
   preserve admitted original intent while its authenticated authority remains
   valid. Show a failed-reload notice and a usable return to editing; do not
   restore retired validation/preview readiness. Authentication loss, authority
   changes and disposal keep their existing invalidation behavior, so no late
   response restores cleared private values.
5. Preserve accepted preview/application handles and uncertain-effect blocks.
   A configuration GET cannot establish protected application outcome or unblock
   unknown effects. Keep the internal reload after confirmed Apply separate from
   manual replacement, including its safeguard for a newer draft.

Primary files are `web/src/components/ConfigurationEditor.tsx` and
`web/src/configuration/configuration-state.ts`. The mounted `EditorSession`
owns raw form text separately from prepared store intent: preserving the store
alone is insufficient. Keep that editor mounted during pending/failed reload,
and explicitly reset it on successful same-base replacement.

## Contracts, invariants, and ADRs

Review INV-001 and INV-021 in the [register](../../../invariants.md),
[ADR145](../../../adr/decision-145.md#structured-managed-edit-composition-clarification-2026-10-26),
[ADR153](../../../adr/decision-153.md#structured-editor-composition-clarification-2026-10-26)
and [ADR154](../../../adr/decision-154.md#browser-application-and-recovery-composition-clarification-2026-10-26).
Amend the [configuration guide](../../../web-ui/configuration-and-tags.md#compare-concurrent-changes-without-losing-intent)
and [keyboard guide](../../../web-ui/browser-and-keyboard.md) to replace immediate
discard wording with explicit successful replacement and failed-read retention.
Record the affected invariant/ADR clarification in this implementation commit.

## Validation

- Extend configuration-state/editor/navigation/recovery tests for cancellation,
  stale decisions, pending reads, same-base/different-base success and each
  failure category.
  Cover prepared changes and raw repository, settings and supported JSON edits
  separately; assert exact retained values, original base and dirty protection.
- Exercise an edit/late-response race, session invalidation, departure/disposal,
  confirmed-Apply reload and an uncertain application. Assert no replay, no
  inferred host outcome and no old preview becoming usable.
- Run a built-browser dirty-reload cancellation/failure/success and keyboard
  workflow on owned fixtures under the existing CSP. Record engine scope and
  request methods; ordinary reload/cancellation must submit no operation.
- Update human guidance and run the required `rtk scripts/check.sh` gate before
  the `WEB-028` commit. Completed executions and retained failures are recorded below.

## Execution notes and handoff

Activated 2026-11-02. The previous investigation's scratch reproduction is a useful
failure example, not acceptance for this change. No live configuration,
application submission or host operation is needed to implement this package.

## Completion evidence

Implementation activated under the user's 2026-11-02 instruction. The mounted
editor uses an explicit replacement revision, independently of base revision;
replacement is admitted under the existing retention bound before publication.
One-use reload reviews bind the draft/auth generation. Confirmed reads retire
readiness while keeping original preview/application handles and unknown-effect
blocks. Explicit navigation discard retires a pending read; Stay preserves it.
Disposal and authentication invalidation clear private forms and fence new/late
reads. Independent source review resolved focus-return, pending navigation,
disposal and capacity-notice findings; no material findings remain.

Contract review: INV-001/021 and ADR145/153/154 reviewed; INV-001 and those ADRs
clarify successful manual replacement and retained failed reads. Configuration,
keyboard and troubleshooting guides amended before source changes. No new
architecture, runtime dependency, durable format, persistence or authority.

Focused source validation passes 64/64 with exit 0:
`rtk node node_modules/vitest/vitest.mjs run test/configuration-state.unit.test.ts test/ConfigurationEditor.component.test.tsx test/configuration-navigation.component.test.tsx test/configuration-recovery.component.test.tsx --reporter=json --outputFile=.artifacts/web028-focused-4.json`
from `web/`; report `web/.artifacts/web028-focused-4.json`. Exact original base,
prepared intent, repository/settings/JSON raw buffers, same/different-base
replacement, all failure families, shared capacity refusal, ready-preview
cancellation, operation/unknown-effect retention, session/disposal and pending
navigation are covered. Scoped TypeScript and ESLint pass; final focused replay covers the lint-clean source. Failed focused reports 1/2
are retained separately: test-helper typo and insufficient capacity-fixture
pressure, respectively. An initial unreported run exposed an outdated post-Apply
phase expectation; the corrected test asserts the preserved original base.

Final built-browser source-fixture workflow passes 5/5 (three draft cases plus
existing startup/fallback) in 31.7s via `rtk pnpm --dir web run build` and
`rtk pnpm --dir web run test:browser`. Retained run:
`web/.artifacts/browser-MseYq6/report.json`; manifest
`648ab2d9cc8d976638edac6c0a75871c3c20f969f7eb2b534e8bc3f0c571ff54`,
source `1e081051fa5cbbcf110de0a5bce4702305210803012a0c4e677c6dc350ee90f1`.
Sandboxed Chromium at 1440×1000, actual built bundle, manifest-bound synthetic
HTTPS/bootstrap/API bodies: each repository/settings/JSON case records config
GET counts 1 initial, 1 after Escape, 1 after Keep editing, 2 pending/failed,
3 after same-base success. All requests are GET; no external requests, CSP or
page errors; axe finds no serious/critical violations. Dialog focus/trap/return
and dirty-navigation Stay during replacement pass. Failed-read screenshots and
request/build/phase attachments are retained. Browser and listener closure are
observed. This is owned source-fixture acceptance, not installed native/rootless
or production acceptance. Earlier import-failure runs `browser-j3OWZ2` and
`browser-KZRYL5` remain separate; interim passes `browser-ydYl1F` and
`browser-w3EnPc` are not substituted for the final build.

First strict gate is retained as a failure, not acceptance:
`web028-gate1-result.json` / `web028-gate1.log` under
`.scratch/web-drafts-library-validation/`: exit 1, 19 failures, 9 errors and
9,562 passed. The newly introduced long temporary prefix made actual socket
paths 116 bytes; 27 failures/errors directly report `AF_UNIX path too long`.
One unrelated-group unclosed-socket warning is qualified spillover pending the
full retry. All 1,240 source files/names stayed unchanged. Full log SHA256
`8e148d4d733457e01220f9e5c16972ff868cafc5f56ec8c2c23e6c8fe65de7b9`;
shadow-wrapper log SHA256
`b95fb67a69a474ee9d929acb2d3fd2cc38ab26729fc2fe484b35c687993119e5`.
Only the owned validation wrapper's temporary naming is corrected, without
changing application code, test expectations or gate checks. Under the same
private archive shadow and login UID, the five affected verification/worker
files pass 114/114 with `/var/tmp/.w28p`; configuration integration and fixed-host
routes pass 9/9 with `/var/tmp/.w28q`. Exact commands/results and separate raw
logs are in `web028-socket-probe1-result.json` and
`web028-socket-probe2-result.json`. The failed gate's owned temporary tree is preserved in
`.scratch/web028-gate1-retirement/`: 159,284 source entries / 159,285 members,
288,047,960 regular bytes, every regular hash, symlink, FIFO and socket metadata
verified against unchanged source with no live owners. Archive SHA256
`528c0dc49a47f56b4e5bfac3a2894ab7a5e3398e23fa192a81534c345dc3423c`;
manifest SHA256
`7515c21a5567a3592e79c7154aeb15646c27e0d89d0063c3d3dd97a9bb5db4dc`.
The first quadratic archive verifier was interrupted by exact PID after preserving
its recipe and attempt record; indexed verification passes. Exact-root retirement
re-verified source, archive and absent live owners, then removed only this
throwaway tree (retirement-result.json); all logs/results/archive/manifest remain. The full strict retry passes as recorded below.


Strict retry `rtk scripts/check.sh --require-web --with-build` (executed through
`rtk proxy` under the reviewed private archive shadow, login UID1000/nice10)
passes exit0 in 1593.858s. `web028-gate2-result.json` records all1,240 inputs/names
unchanged; log SHA256 `77f8a4c104792c74767af1e5422ec37b60a09af3dc4dd723591718ba7cc90fe9`.
All9,590 backend tests,4,069 combined frontend tests (3,719 unit subset),16 wheel
smokes, three locked installation profiles, generated contracts, lint/types,
build, five Chromium workflows and real HTTP/API React fixture pass. No required
frontend skips;95.07% lines/90.07% branches. Gate browser evidence
`web/.artifacts/browser-VhD0bi` rebuilds the exact final source/manifest above.
All first-run failures and the socket-finalization warning disappear under the
short owned temporary path, with application/test behavior unchanged. This is
source/owned-fixture acceptance; no installed native/rootless or production
acceptance, deployment, live service/archive access, dependency addition, draft
persistence, replay, tag or push follows. Human guides/contracts and independent
review are current; completed progress and next-task selector accompany this
commit. No remaining scoped acceptance criteria.
