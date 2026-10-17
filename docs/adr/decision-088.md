# Decision 088: The starter kit runs under pnpm; node is a build-time toolchain, not a dependency

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-30.
- Original work package: `CPT-001`.
- Source: [decision 88 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The operator provisioned node LTS
(v24) and pnpm 11 under `PNPM_HOME` (`~/.local/share/pnpm`), and pnpm
replaces the starter kit's npm throughout: one committed
`pnpm-lock.yaml`, frozen installs, the node version pinned in-repo at
scaffold time so builds reproduce. `FW-03`/`FW-04` are untouched — the
plugin ships static files, the application's runtime set stays three
packages, and nothing node produces runs outside the browser. The gate
grows a conditional plugin stage (frozen install, lint, production
build) that skips loudly when the toolchain is absent, because
`scripts/check.sh` must keep meaning the same thing on hosts without
node; the discipline that closes the skip's hole is that a `CPT`
package lands only from a host where the plugin stage ran, recorded in
its tracker evidence. **Rejected: distribution nodejs via dnf** —
root-owned and centrally updated, but the pnpm-managed toolchain was
already provisioned, and a second node on the host is a version-skew
source with no compensating benefit.

## Later history and current interpretation

The node/pnpm versions describe the original provisioning. The current committed
toolchain and lockfile govern builds; the distinction between browser assets and
Python runtime dependencies remains.

## Provenance and governing evidence

The source entry first appears in
[ebc112f](https://github.com/wtcross/hfcache/commit/ebc112f30995e70a1ad3c6d214ee53b803f43b7f)
(2026-07-30, `CPT-001: Cockpit plugin contract and work-package plan`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cockpit.md](../../docs/cockpit.md),
[docs/agents/conventions.md](../../docs/agents/conventions.md).

Implementation or shipped-artifact evidence:
[cockpit/package.json](../../cockpit/package.json),
[cockpit/pnpm-lock.yaml](../../cockpit/pnpm-lock.yaml),
[scripts/check.sh](../../scripts/check.sh).

Relevant verification:
[cockpit/test/command.test.ts](../../cockpit/test/command.test.ts).
