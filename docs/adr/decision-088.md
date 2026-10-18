# Keep the Cockpit build toolchain separate from application runtime

- Decision identity: 088.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-30.

## Context, decision and consequences

Use one committed pnpm lock and frozen installs with the in-repository Node/pnpm
pins. Node builds static browser assets; it is not an application runtime dependency.
The gate executes lint, types, unit tests and production build when the toolchain
is present; a loud skip is not evidence of plugin validation.

The operator-managed pnpm toolchain was selected instead of a second distribution
Node installation because duplicate toolchains introduce version skew without a
compensating benefit. The committed current pins and lock govern builds, rather
than the versions originally provisioned on one host.

## Provenance and governing evidence

The source entry first appears in
[ebc112f](https://github.com/wtcross/hfcache/commit/ebc112f30995e70a1ad3c6d214ee53b803f43b7f)
(2026-07-30, `Cockpit integration: Cockpit plugin contract and integration design`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cockpit.md](../cockpit.md),
[recorded deployment scope](../deployment-status.md).

Implementation or shipped-artifact evidence:
[cockpit/package.json](../../cockpit/package.json),
[cockpit/pnpm-lock.yaml](../../cockpit/pnpm-lock.yaml),
[scripts/check.sh](../../scripts/check.sh).

Relevant verification:
[cockpit/test/command.test.ts](../../cockpit/test/command.test.ts).
