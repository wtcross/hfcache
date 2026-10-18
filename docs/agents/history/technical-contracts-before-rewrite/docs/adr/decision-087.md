> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 087: A Cockpit plugin in `cockpit/`, contracted by `docs/cockpit.md`, tracked as the `CPT` family

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.
Reader/candidate API integration is amended by [decision 119](../../../../../adr/decision-119.md).
API-backed Cockpit mechanisms are amended by [decision 122](../../../../../adr/decision-122.md).

- Original decision date: 2026-07-30.
- Original work package: `CPT-001`.
- Source: [decision 87 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The operator wants
browser administration of the deployed writer — sync control and live
activity, verification, archive browsing, configuration and schedule
editing — and Cockpit already serves this host. Decided: a Cockpit
package in this repository under `cockpit/`, a client of the contracts
that exist (the CLI's JSON envelope, the configuration schema, and the
shipped units are its whole API), with a normative contract of its own
and requirement IDs (`CP-01`–`CP-14`) the implementation and tests can
cite; the family is tracked outside plan §28's phase set exactly as
decision 80 did for `DOC`. **Rejected: a separate repository.** The UI
encodes runbook semantics — the `hfcache.target` unmount footgun, the
verify-timer reservation, the §8 warning responses — and an encoding
that cannot change in the same commit as the contract it encodes will
drift; that is the same argument that keeps docs and code in one tree.
**Rejected: a plain no-build package** in the style of Cockpit's pinger
example — no toolchain, but hand-rolled tables and dialogs instead of
PatternFly's, visual drift from the rest of Cockpit, and none of the
starter kit's lint and test scaffolding; the toolchain cost is paid
once, at build time only.

## Provenance and governing evidence

The source entry first appears in
[ebc112f](https://github.com/wtcross/hfcache/commit/ebc112f30995e70a1ad3c6d214ee53b803f43b7f)
(2026-07-30, `CPT-001: Cockpit plugin contract and work-package plan`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cockpit.md](../../../../../cockpit.md).

Implementation or shipped-artifact evidence:
[cockpit/src/app.tsx](../../../../../../cockpit/src/app.tsx),
[cockpit/src/api/hfcache.ts](../../../../../../cockpit/src/api/hfcache.ts).

Relevant verification:
[cockpit/test/command.test.ts](../../../../../../cockpit/test/command.test.ts).

## 2026-10-18 candidate pipeline amendment (API-012)

The CLI's reader and candidate modes now use authenticated REST. CP-11 retains
candidate → validation → preview → privileged atomic installation/backup. Pure
candidate validity is separate from installed authority compatibility; only a
compatible proposal can plan with installed credentials. REST grants no policy
installation authority. This package supplies those CLI/API semantics; API-015
still owns the shipped Cockpit caller and credential integration, without browser
bearers. See [decision 119](../../../../../adr/decision-119.md) and [Cockpit contract](../../../../../cockpit.md).


## 2026-10-18 Cockpit API integration amendment (API-015)

The plugin remains a CLI/systemd client, now with fixed local API settings and
API-only systemd `hfcache.api` authority. Strict bounded terminal Envelopes retain
command authority; separately validated bounded notices retain safe progress and
reconnection handles. No browser bearer/backend or direct archive mutation is
added. See [decision 122](../../../../../adr/decision-122.md) and [Cockpit](../../../../../cockpit.md).
