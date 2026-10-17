# Decision 090: `cockpit/` carries LGPL-2.1-or-later beside the repository's MIT

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-30.
- Original work package: `CPT-002`.
- Source: [decision 90 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The plugin tree is a derivative of
cockpit-project/starter-kit @ `a099cb10` and consumes cockpit's `pkg/lib`
(fetched at build time, never committed), both LGPL-2.1-or-later. The
derived and adapted files keep that license with per-file SPDX headers,
and original plugin code added under `cockpit/` uses the same license so
the subtree has one answer rather than a file-by-file puzzle. The
top-level MIT `LICENSE` is unchanged and continues to cover everything
outside `cockpit/`. The alternative — relicensing the derived scaffolding
under MIT — is not this project's call to make.

## Later history and current interpretation

This is the subtree license decision. The original scaffolding provenance and
source SPDX notices govern the derived Cockpit files; the top-level MIT license
does not relicense that subtree.

## Provenance and governing evidence

The source entry first appears in
[e0d1f2c](https://github.com/wtcross/hfcache/commit/e0d1f2cedc5572f53b97d086cccbb4ec95872b03)
(2026-07-30, `CPT-002: scaffold cockpit/ from the starter kit under pnpm`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cockpit.md](../../docs/cockpit.md),
[LICENSE](../../LICENSE).

Implementation or shipped-artifact evidence:
[cockpit/README.md](../../cockpit/README.md),
[cockpit/package.json](../../cockpit/package.json).

Relevant verification: [cockpit/src/app.tsx](../../cockpit/src/app.tsx).
