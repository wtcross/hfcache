# Script and code-removal disposition inventory

Review: 2026-10-18, `feat/rest-api-and-mcp` at `65b65714b29e835498138ec3122b5669571850cf`.
This is an agent review artifact. The implemented human `docs/scripts.md` must
use plain purpose/profile/usage language, not these task/finding labels.

## All existing scripts

The branch tree contains the following 17 script entries. Classifications are
based on code inspected where relevant and the repository's current build/runtime
references. This is not a claim that each helper was executed. The implementing
agent must perform the complete reference/install/test inventory before deletion.

| Script | Disposition | Purpose | Side effects / improvement |
| --- | --- | --- | --- |
| [build-caddy-container.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/build-caddy-container.py) | Retain — build | Build/prove the selected Caddy derivative and its image identity. | Local engine/image/context effects; no startup pull/push. Document exact pinned inputs and provenance. |
| [build-container.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/build-container.py) | Retain — build | Build the locked application image on current UBI inputs. | Local context/image work. Correct stale base description; document portable-Python, wheel and closure inputs. |
| [check-container-foundation.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check-container-foundation.py) | Retain — opt-in fixture | NAS-free proof of an exact local UBI Python image. | Starts retained named fixture containers; not a harmless status command. Never call it installed-worker/NAS proof. |
| [check-container-worker.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check-container-worker.py) | Retain — opt-in fixture | Private worker/PID1/peer/isolation fixture checks. | Container/process/local evidence effects. Separate fixture/host-peer/actual-installed-API proof. |
| [check-hardening.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check-hardening.sh) | Retain, restrict and repair — native probe | Native executor hardening wrapper; not the rootless installed-process probe. | Unsafe to treat as routine read-only status. Add profile/mode/target guard and safe help/dry-run. |
| [check-installations.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check-installations.py) | Retain — test/build | Verify locked base, server and server+MCP installation profiles. | Throwaway environments/package installation; consumed by the gate. Not dead because --with-build also exists. |
| [check.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check.sh) | Retain and extend — quality gate | Provider-neutral lint/types/tests/build/installation/Cockpit gate. | Development environment/build effects. Add safe documentation/interface checks; distinguish skipped stages. |
| [consumer-serve-hfcache-model.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/consumer-serve-hfcache-model.sh) | Retain — consumer | Serve an explicitly verified consumer-side revision. | Serving/container operation, not archive management. Keep ownership and immutable-promotion separation. |
| [container-service.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/container-service.py) | Retain — rootless runtime | Closed role launcher and non-killing drain using a protected profile. | Service/container/state effects. Keep fixed role/engine/mount/secret boundaries and unknown-state refusal. |
| [fetch-container-python.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/fetch-container-python.py) | Retain — build input | Obtain/verify the portable Python input required by the UBI build. | External fetch/local artifact effects; never a runtime dependency resolver. Document trust/provenance. |
| [hardening-probe.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/hardening-probe.py) | Retain, restructure — native workload | Exercise explicit sandbox/workload checks. | Currently import-time/invasive and overbroad denial handling. Make import-safe and correct ordering/classification. |
| [hfcache-client](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/hfcache-client) | Retain — rootless client entrypoint | Fixed host wrapper for the client role launcher. | Referenced deployed entrypoint; short length is not deadness. No generic engine escape or local operational fallback. |
| [hold-readonly-guard.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/hold-readonly-guard.py) | Retain — independent safety policy | Hold the original local lock and establish the host read-only barrier. | Critical host process/lock policy independent of current release. Never remove as deployment residue. |
| [install-container-release.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/install-container-release.py) | Retain — selected installer | Stage/select protected immutable container release artifacts. | Privileged release-binding/selection work under guards. Not to be run by this source-only plan. |
| [install-release.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/install-release.sh) | Retain with explicit native guard | Supported native staging/switch path; not the selected rootless installer. | Privileged staging/select work. Refuse container/mixed targets early; label all human recipes by profile. |
| [release-functions.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/release-functions.sh) | Retain — native library | Shared quiescence, handle compatibility and atomic switch functions. | Sourced by native installer/tests. No standalone workload; preserve lock/state/rollback semantics. |
| [setup-hfcache-consumer-model-store.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/setup-hfcache-consumer-model-store.sh) | Retain — consumer provisioning | Provision consumer store ownership and separate serving promotion. | Host filesystem/ownership work, not metadata/API setup. Keep independent consumer contract. |

Every newly added checker/helper must also appear in the human inventory. A file
being absent from the selected rootless runtime is insufficient evidence that it
is unsupported or unused.

## Concrete source cleanup candidates

| Candidate | Evidence and confidence | Required action |
| --- | --- | --- |
| `src/hfcache/cli.py::_emit` | Defined but no caller in the inspected CLI; handlers use `_show_result`. High local-file confidence, repository-wide search still required. | Remove once source/tests/examples/registration check confirms no supported caller; preserve bootstrap `emit_envelope`. |
| `src/hfcache/cli_client.py::run_job` | Older submit-and-observe convenience path; current inspected CLI calls the richer submit/observe helpers. Candidate, not proven globally dead. | Search all consumers. Remove only if unused or test-only with equivalent public behavior coverage. |
| `cli._show_result` legacy `ServiceResult` input path | Inspected public callers deliver Envelopes; union path appears to date from migration. Candidate. | Simplify after caller proof. Do not remove actual `ServiceResult` domain type or its use in bootstrap/envelope generation. |
| `GlobalOptions.color` | Stored from `--no-color`/TTY but not consumed by reviewed renderers. Inert implementation state. | Wire the supported public option to real rendering, then delete inert state. Do not silently remove `--no-color`. |
| `cli.UNPROVABLE_READ_ONLY` re-export | Imported/exported but not used by current CLI bodies; potential old test/compatibility seam. Candidate. | Check supported imports, migrate implementation-only test imports to the defining module, and remove only if safe. |
| Old native credential drop-in example | Contains a reset/migration warning, not the old Hub-token import. Intentionally historical; not proven dead. | Give it a clear migration-only home/name or remove after references and replacement instructions are verified. Do not delete an installed drop-in automatically. |

Sources: [src/hfcache/cli.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli.py), [src/hfcache/cli_client.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli_client.py),
[packaging/systemd/hfcache-sync.service.d/credential.conf.example](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/packaging/systemd/hfcache-sync.service.d/credential.conf.example).

## Obsolete documentation to remove from the human surface

- Repeated implementation-stage amendments, task-owned acceptance narratives,
  active-plan tables and progress backlinks in human docs, including the full MCP
  introduction supplied by the user.
- Native direct-writer `$H`/`$D` command aliases as current runnable guidance.
  Preserve useful captured outputs as historical agent evidence before rewriting.
- Current slim-trixie/Debian image descriptions and worker-socket startup summaries
  contradicted by the UBI/worker-created-listener implementation.
- Human navigation entries for implementation plans/progress/agent workflow;
  move their records under `docs/agents`, not into another public backlog guide.
- Obsolete inventory text that presents the script directory as only the old native
  installer/gate/probe pair.
- Process-only ADR and invariant material from the human architecture surface,
  after preserving their identities/rationale in the agent area.

Delete duplicate obsolete prose only after checking whether it contains a unique
technical requirement. Do not erase compatibility caveats, command side effects,
security limits or user-facing release history together with task references.

## Explicit retain list

Keep the dormant `packaging/containers/hfcache-verification.socket` and its protected
release binding unless a new design changes that contract. It is not the active
container listener. Keep native socket activation, `scheduled_client.py`, native
scheduled services and pending-handle logic. Keep actual domain service modules,
MCP authentication/lifespan helpers and no-replay receipt stores.

Keep `cockpit/src/api/archive.ts` and its host-local report browsing until a scoped
replacement exists; it is an intentional exception, not unused code. Keep
`examples/copy-revision.py`, consumer store/serving helpers and their tests: REST/MCP
metadata do not replace the NFS content path or complete local verification.

Keep `hold-readonly-guard.py`, exact lock paths/inodes, masks, state retention and
all independent host safety policy. This source cleanup must not alter their
installed instances or treat production artifacts as repository dead files.

## Deletion proof required at implementation

For every proposed removal, record tracked path/symbol; all direct/dynamic
references; packaging/installed-entrypoint and rollback uses; whether it is a
supported API; replacement or reason none is needed; tests preserving meaningful
behavior; and an explicit remove/retain outcome. Search before editing and again
after deletion. Failing tests that only exercised a dead implementation seam may
be replaced by stronger public-contract checks, not simply dropped.

No whole script was established as safely removable by this static review.
That is a limit on deletion evidence, not a reason to retain confirmed dead symbols
or obsolete human-facing prose.

## Final implementation disposition

The pinned review above is preserved. The [final acceptance ledger](2026-10-18-alignment-acceptance.md)
records every candidate’s outcome, all 19 supported helpers and the migration-only
credential example rename. Human instructions live in the current script catalog
and deployment guides.
