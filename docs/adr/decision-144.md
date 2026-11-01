# Retire shipped Cockpit only after complete replacement proof

- Decision identity: 144.
- Status: Amended by the2026-11-01 user directive; deprecation/handoff follows new-web acceptance, with no further plugin maintenance or validation. Earlier removal/porting proposal remains historical.
- Date: 2026-10-20.

## Context and proposed decision

The replacement SPA is intended to become hfcache's sole newly shipped management
UI. Retire Cockpit source/build/install/release dependencies only after exact
publication/configuration/operation behavior, supported host controls, old-client
compatibility, real installed functional acceptance, human documentation and
evidence-preserving rollback pass. Until then the current Cockpit contract,
packaging, tests and operator instructions remain authoritative for the shipped
plugin. Accepted SPA design does not itself satisfy any retirement prerequisite.

Preserve historical Cockpit plans, ADR reasoning, attribution and relevant
compatibility fixtures. Explain every removed source/packaging file. Source
retirement does not uninstall the live plugin, reload Caddy, change a production
service/timer/credential/guard, authorize archive access or deploy the replacement.
Those are separate operator actions with their own permission and acceptance.

## Rationale and alternatives

Removing Cockpit before proving its replacement would discard tested management
and recovery paths. Shipping two permanent newly supported UIs would duplicate
security and maintenance obligations. Conditional retirement allows one supported
future surface without pretending unfinished work is parity. Keeping historical
evidence and unknown state supports a reviewable rollback instead of deleting
new state until an old binary starts.

## Consequences and evidence

Retirement remains proposed at baseline
`6b8fae2e0997403ae5c716a2e92148af0a972af9`; this commit removes nothing.
Before accepting this decision, record actual required suite results, UI/backend/
helper artifact identities, native/rootless positive/negative host proof,
configuration/operation/card compatibility, documentation walkthrough and rollback
barriers. Production migration remains unperformed even after source acceptance.

## Relationships

Proposed eventual replacement of [087](decision-087.md), [088](decision-088.md),
[122](decision-122.md) and the Cockpit-only transport portions of
[134](decision-134.md)–[139](decision-139.md), while retaining all applicable
domain safety constraints. See [140](decision-140.md), [141](decision-141.md),
[142](decision-142.md), [143](decision-143.md),
[web UI status](../web-ui/README.md), [Cockpit contract](../cockpit.md) and
[recorded deployment status](../deployment-status.md).

## User-directed deprecation scope (2026-11-01)

[Decision160](decision-160.md) supersedes the earlier current-validation and
legacy inventory/porting/removal conditions by explicit user direction. Current
acceptance requires strict web/backend/docs/build checks; Cockpit is legacy
opt-in and is not validated for this goal. Preserve its history/source/licenses,
shared runtime helpers and live installation. All95 new-web behaviors and their
minimum layers remain required; deprecation and handoff follow guide acceptance.
