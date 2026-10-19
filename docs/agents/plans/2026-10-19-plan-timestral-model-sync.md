# Add Timestral models to the installed archive policy and trigger sync

| Field | Value |
| --- | --- |
| Status | completed |
| Created | 2026-10-19 |
| Authorization | Tyler's 2026-10-19 instruction to add four dependency-free Timestral models to this host's live deployment, validate configuration, and trigger sync |
| Tracker | [Current plan](current.md) |

## Outcome and scope

Add enabled `model` entries for `mistralai/Timestral-5M`,
`mistralai/Timestral-28M`, `mistralai/Timestral-123M`, and
`mistralai/Timestral-209M`, each tracking `main` with
`declared_dependencies = []`. Preserve all other installed policy. Validate an
authority-compatible candidate and its scoped plan before protected atomic
installation, confirm the installed fingerprint, then trigger one sync restricted
to these four models and retain its exact admission and observed execution state.

The new request authorizes these supported live application actions despite the
earlier documentation plan's prohibition on production operations. It grants no
guard release, writable remount, manual archive operation, archive initialization,
service/image/unit/schedule change, secret change, hardening relaxation, or action
on another host. Preserve the independent read-only guard, original lock inodes,
NAS read-only state, writer masks, disabled calendars, both operation stores and
existing observation handles. A guard refusal or pending lock wait must remain
visible; trigger admission is not a claim of downloaded or published models.

## Contracts and decisions

Review [configuration](../../configuration.md), [operations](../../operations.md),
[API client](../../api-client.md), [server policy reload](../../server.md#archive-policy-reload),
[protected configuration editing](../../cockpit.md#6-configuration-editing),
[deployment status](../../deployment-status.md), and [host limits](../environment.md).
Preserve technical invariants `INV-002`, `INV-003`, `INV-004`, `INV-014`, `FS-02`,
and `AD-07`, plus [planning invariant `INV-011`](../invariants.md).
Decisions [119](../../adr/decision-119.md), [122](../../adr/decision-122.md),
[126](../../adr/decision-126.md), and [127](../../adr/decision-127.md) retain
candidate authority, exact configuration guards, live deployment restrictions,
and rootless confinement. This operational policy edit changes no invariant,
architectural decision, application source, dependency, image, or durable schema.

## Tasks

| Order | Work package and task file | Depends on |
| --- | --- | --- |
| 1 | [OPS-022: Configure Timestral models and trigger a scoped live sync](tasks/ops-022-timestral-model-sync.md) | None |

## Acceptance and validation

Require protected predecessor evidence, exact unrelated-policy preservation,
successful compatible candidate validation and four-model preview, atomic policy
replacement under the retained cooperative configuration flock, and successful
installed fingerprint confirmation. Submit one scoped sync with a retained
idempotency key; record its operation ID and exact observed status/result. Pending
or refused execution under the unchanged guard is reported explicitly without
claiming archive publication or repeating the mutation with a new key.

Run `scripts/check.sh` before the work-package commit. Link real operational
evidence in the task and completed progress entry, preserve deployment barriers,
then reconcile plan/task/current. No initial duplicate gate is required before
the policy action because application source remains the already validated
`45f91c3` tree; the eventual documentation commit receives its required gate.

## Lifecycle and amendments

- 2026-10-19: Activated directly from the user's live configuration and scoped
  sync request. No historical backlog or production acceptance hold is activated.
- 2026-10-19: Completed OPS-022 after protected installation, compatible validation,
  four-model preview, one admitted sync and observed `waiting_lock`, plus the
  passing repository gate. The requested trigger is complete; downloads remain
  blocked by the preserved guard/NAS-ro and are not claimed as accepted.
