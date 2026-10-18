# Decision 091: `smol-toml` is bundled for configuration round-tripping

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.
API-backed Cockpit mechanisms are amended by [decision 122](decision-122.md).

- Original decision date: 2026-07-30.
- Original work package: `CPT-008`.
- Source: [decision 91 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Form mode must parse the installed document to populate its
controls and serialize a candidate, and TOML is the configuration
contract's format. `smol-toml` (MIT, TOML 1.0, parse and stringify, no
dependencies of its own) is added as a browser-bundled dependency —
build-time resolved, shipped inside `dist/`, nothing in the
application's runtime set (`FW-03` untouched, `CP-14`). **Rejected:
hand-rolling a parser** — a second TOML implementation in this
repository would be a validation-drift source against the `tomllib` the
application reads with, for no saving. **Rejected: a JSON side-channel**
(teaching the CLI to emit or accept configuration as JSON for the
plugin's convenience) — a new CLI surface grown to match a UI inverts
decision 89's direction. Comment loss in form mode is stated in the
generated header and in the UI; text mode exists precisely so an
operator who keeps comments can.

## Provenance and governing evidence

The source entry first appears in
[c843979](https://github.com/wtcross/hfcache/commit/c843979fe05d9b1de686cbd19f541d34a176b56c)
(2026-07-30, `CPT-008: configuration editor — form and text modes over the
validate-install pipeline`). The decision text above preserves the complete
reasoning in the current historical log, including its recorded alternatives and
consequences.

Current governing documents: [docs/cockpit.md](../../docs/cockpit.md),
[docs/configuration.md](../../docs/configuration.md).

Implementation or shipped-artifact evidence:
[cockpit/src/lib/config.ts](../../cockpit/src/lib/config.ts),
[cockpit/package.json](../../cockpit/package.json).

Relevant verification:
[cockpit/test/config.test.ts](../../cockpit/test/config.test.ts).


## 2026-10-18 Cockpit API integration amendment (API-015)

Bundled TOML still serves form/text editing, without a Python dependency.
Readiness now binds exact candidate and installed-base bytes under the root config
flock, with server syntax/authority assessment, required preview and exact installed
fingerprint confirmation. Edits invalidate readiness; incompatible/unknown authority
requires manual operator installation/restart rather than plugin install. See
[decision 122](decision-122.md).
