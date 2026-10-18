# Decision 116 — Admit typed command routes without widening server authority

- Status: Accepted; implemented by API-009; maintenance extended by
  [decision 117](decision-117.md), candidates/readers by [119](decision-119.md).
- Date: 2026-10-17.
- Work package: API-009, this commit.
- Source: [progress decision 116](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-009-sync-verification-and-diagnostics-api.md).

## Context and decision

Expose explicit typed sync, verification, installed planning, diagnostics and
installed-config-validation routes over shared services. Authenticate transport
and bearer before receiving a body, require writer capability on known writer
routes before body processing, and authorize body-dependent capability before
service work. Parse one bounded strict JSON object with deliberate media/encoding
rules; reject duplicate keys, nonfinite numbers, invalid UTF-8, coercion, unknown
fields and inconsistent scope. No route dispatches a caller-selected command,
configuration path, credential source or Hub endpoint.

Long work uses the bounded lane and durable idempotency contract. Every job
requires a key, including semantic read-only plans/diagnostics, because its Hub,
resource and control-state effects outlast observation. A 202 response proves
durable admission, never domain success; retrieve the exact terminal Envelope
with the operation's result link. Matching canonical retries preserve the same
operation across policy changes. Normalize selector sets before hashing while
the actual sync still executes in installed configuration order.

Sync and every non-estimate verification require REST writer capability.
Verification always delegates through the private executor, with no HTTP-process
fallback. Installed planning and diagnostics explicitly selecting `read_only=true`
permit REST readers; probing diagnostics require writers and the shared lock.
The `read_only` field is required and strict: missing/invalid mode never silently
becomes an archive probe. Read-only diagnostics may contact the installed Hub and
use heavy resources, so they are not metadata or MCP reads. Installed validation
is a bounded immediate query with no arbitrary-path loading or key requirement.

Hub credentials come only from a trusted startup `serve --hub-token-file` or the
installed systemd source, using existing token-mode rules. The caller's API bearer
never becomes a Hub token. Candidate primitives validate bounded TOML content
without resolving credentials, touching archive paths, contacting the Hub or
installing policy. Authority compatibility compares installed root/UUID, endpoint,
token mode, credential name and expected account before any future candidate
planning. Changing those fields can be syntax-valid but cannot redirect the
installed credential. Current HTTP candidate fields remain rejected; API-012
owns the full CLI/Cockpit candidate pipeline.

## Rationale and alternatives

Explicit typed routes retain domain validation/refusal and avoid a second command
engine or a CLI subprocess adapter. A synchronous long request loses observation
without durable admission. Calling a semantic read ordinary metadata would hide
its Hub calls, credential resolution, resource budget and receipt writes. A 202
receipt rendered as a success Envelope would conceal later partial/domain failure.

Loading a caller-selected server file or resolving candidate-selected credentials
would let an authenticated reader redirect writer authority. Comparing only the
archive UUID misses endpoint/credential escape; comparing the complete installed
authority permits policy previews while preserving the secret boundary. Reject
generic command/path endpoints, request token overrides and implicit probe mode.

## Consequences and relationships

Implements the command-transport portion of [108](decision-108.md), bearer boundary
of [112](decision-112.md) and lane/private-worker controls of
[115](decision-115.md). AD-01–03/17–19, TX-07 and INV-004/006/007 retain complete
immutable snapshots, observation/retention, pre-Hub reconciliation, capacity,
producer joins, exact verification evidence and domain exit classifications.
No archive or receipt format, runtime dependency, MCP tool, configuration-install
API or production deployment is introduced.

[API](../api.md) defines routes, role/body rules, 202 models and polling;
[server](../server.md) defines the trusted startup Hub source and execution
boundary; [configuration](../configuration.md) defines candidate authority hooks.
Public maintenance/initialization routes remain API-010, client migration remains
API-011–013 and installed worker/no-IP acceptance remains API-014. The task
records exact validation and the final gate.

Implementation: [strict DTOs](../../src/hfcache/api/command_models.py),
[shared-service adapters](../../src/hfcache/api/commands.py),
[authenticated POST boundary](../../src/hfcache/api/app.py), and
[pure candidate assessment](../../src/hfcache/services/candidates.py).
Evidence: [model/authority tests](../../tests/unit/test_command_models.py),
[real HTTP/domain tests](../../tests/unit/test_api_commands.py),
[adversarial concurrency/disconnect tests](../../tests/unit/test_api_command_adversarial.py)
and the completed [task](../plans/tasks/api-009-sync-verification-and-diagnostics-api.md).

## API-012 candidate implementation amendment

[Decision 119](decision-119.md) wires bounded candidate content into writer-only
validate/plan. Pure syntax validity is independent of compatibility and credential
availability; valid incompatible content stays valid, and broken installed policy
permits unknown-compatibility syntax validation. Planning rechecks all six authority
fields before installed credential use after queue waiting, because credential
name is excluded from the policy fingerprint. Candidate policy cannot replace the
installed admitted fingerprint or become configuration-install authority. Omitting
the new field preserves historical installed-plan canonical key mappings; explicit
null is refused. No new durable shape/dependency is introduced.
