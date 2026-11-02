# REL-016: Prepare a fresh full-web release source

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Production web migration](../2026-11-01-plan-production-web-migration.md) |
| Depends on | None |

## Scope and acceptance

Assign unused version 0.3.0 to the completed web/API/MCP source, update the lock,
changelog and human status without claiming deployment. Preserve pinned runtime
dependencies. Run the strict full web/build gate with NAS shadowed; commit clean
release inputs for OPS-024's detached immutable build. No host selection or tag
occurs in this package.

## Contracts, invariants, and ADRs

Reviewed the parent plan's release/configuration/security contracts, INV-001–003,
FS-19 and FS-21–23, and decisions 126–129, 140, 146–147, 158–159 and 161.
The package changes release metadata and human status only. No new invariant,
architectural decision, runtime dependency, operation or archive format is added;
the existing records remain applicable without artificial amendments.

## Validation

- `uv lock --check` passes with the same 94 packages. The lock diff changes only
  the project version from 0.2.2 to 0.3.0.
- `scripts/check.sh --require-web --with-build` passes: inner exit0 in
  1,819.604 seconds, outer exit0 in 1,820.207 seconds; all 1,227 tracked source
  inputs and their names remain unchanged through the gate.
- The private mount namespace proves an empty read-only tmpfs over
  `/srv/hfcache`, with nosuid/nodev/noexec, before dropping to login UID/GID1000
  and nice10. The host NFS mount is neither changed nor accessed by the gate.
- Passed: format, lint, types, documentation, 9,562 backend tests (52 explicit
  opt-in tests deselected), wheel/source build, three locked installation
  profiles, frozen frontend install/wire/lint/types, 23 authentication metadata
  and 18 functional metadata checks, 3,708 unit and 4,051 unique combined
  frontend tests, 95.02% line/90.13% branch coverage, fresh built assets, two
  owned Chromium checks, real HTTP/API React read fixture and 16 wheel smoke
  tests. No required frontend checks were skipped.
- Log: `.scratch/rel016-validation/gate1.log`, SHA256
  `8a083348ffb2b8c42f3b10e0a59c774ce1d4a427f2d61ce109a182f40321e0d1`.
  Inner/outer results and source freeze are retained beside it. The outer
  command was observed exited0 and reaped before finalization.
- Post-gate evidence-only record checks pass under the same private NFS shadow:
  212 human documents/29 helpers, nine plan tests and `git diff --check`.

## Execution notes and handoff

The installed 0.2.2 and untracked `node_modules/` remain preserved. Version 0.3.0
was absent from local tags and `/opt/hfcache/releases` at initial inventory.

README and changelog distinguish source candidate0.3.0 from installed0.2.2 and
record target-compatible server configuration, retained outcomes and independent
NFS/calendar holds. Gate artifacts are dirty-source validation outputs, not
immutable deployment artifacts. No service, credential, configuration, archive,
selection, tag or remote publication is performed by this package.

Migration preflight identified an existing rootless account-home layout that
needs a separate reviewed helper compatibility package before a full installed
helper rollout. That source correction and its acceptance are outside REL-016;
the candidate is not declared production-ready here.

## Completion evidence

2026-11-01, REL-016, this commit: unused0.3.0 metadata, unchanged dependency
closure, human candidate/rollback status, strict source/web/build gate and
invariant/ADR review complete. The parent plan and task records establish the
authorized local migration. OPS-024 has verified its protected local backup;
source compatibility, clean construction, guarded host selection and production
acceptance remain pending. See the
[completed progress entry](../../progress.md#local-web-migration-2026-11-01).
