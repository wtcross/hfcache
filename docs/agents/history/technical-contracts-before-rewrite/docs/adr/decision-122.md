> Historical technical reference preserved before consolidation. Current authority is the living contract.

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `cfdab17c941ac3c47a1e88d76b43e5aaccf759bc9a19d8f05d387813d4b51156`,
original content SHA-256 `bb8b37287e58949a16cce647cbc66e04b500e1e638a7b5725307f807ce8499b3`.
Historical proof hashes identify the original artifacts, not this edited record.

# Decision 122 — Preserve historical frontend authority through the API client and guarded candidates

- Status: Accepted; implemented by API-015 on 2026-10-18; deployed browser/
  credential/hardening acceptance remains an operator hold.
- Date: 2026-10-18.
- Work package: API-015, this commit.
- Source: [progress decision 122](../../../../progress.md#decisions),
  [active plan](../../../../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../../../removed-interface-records.md).
Native Unix/public-prefix routing is amended by [decision 123](../../../../../adr/decision-123.md).

## Context and decision

Require a bounded strict schema-1 terminal Envelope for command decisions.
Separately validate documented bounded CLI progress lines and nonsecret recovery
handles for display/reconnection; never infer outcomes, checkpoints or byte
percentages from progress. Unknown/malformed terminal output is a visible
observation failure, including on a nonzero process exit. Closing a page or
stopping a client does not cancel accepted work. Lost/uncertain observation
retains exact key/operation handles and offers authenticated lookup/wait; it never
proves recovery safe or launches automatic recovery. Explicit `work_may_continue`
and HFAPI013/015/019/020 preserve this uncertainty.
Use finite UTF-8 bounds: 16 MiB terminal JSON, 8 KiB partial progress line and
64 KiB retained diagnostics. Dropped oversized progress is explicit and does not
discard validated handles or the independent terminal collector.

Configuration installation remains privileged host work, never REST. A persistent
root-owned `0600` `/etc/hfcache/.configuration.lock` serializes the plugin's
candidate pipeline. Under that flock, compare exact candidate and loaded installed
base bytes before server validation/preview and again before atomic installation.
Pass bounded candidate bytes as inert stdin, never interpolate them into shell
code or accept generic executable/path authority. Form/text edits invalidate
validation/preview readiness. Retain predecessor and `0640 root:hfcache` metadata,
fsync before rename, and verify the expected fingerprint through installed API
validation before reporting success.
Fixed installed reads share the same bounded no-follow/metadata/flock guard.
Install/confirmation errors clear readiness and require reloading installed state,
because the rename may have completed even when observation failed.

Syntax validity, installed-authority compatibility, preview readiness and
installed confirmation are separate. Valid but incompatible or unknown authority
blocks plugin installation and presents privileged manual install/restart and
compatible-preview guidance. Candidate planning uses installed credentials only.
Failed required preview or confirmation cannot become success. New installed
policy affects future admissions; existing operations retain their admitted
snapshot and stale queued mutations refuse under the server's lock.

## Rationale and alternatives

Importing Hub authority into an API client duplicates the daemon's authority and
breaks the reader/client separation. Retain systemd credential delivery but change
its source to API-only; reject browser bearers, ambient secrets and direct REST
credential storage. Typed CLI output preserves the existing integration boundary.

Treating a stopped observer as a stopped writer would permit unsafe recovery or
duplicate work. Use retained operation evidence and existing executor drain rules.
A successful syntax check alone cannot authorize credential-bearing planning or
installation. Exact candidate/base guards prevent an edited proposal or replaced
installed policy from borrowing stale validation/preview results; the config flock
does not replace privileged operator review or server admission checks.

## Consequences and relationships

Amends [087](../../../removed-interface-records.md), [089](../../../../../adr/decision-089.md), [091](../../../removed-interface-records.md),
[092](../../../../../adr/decision-092.md), [119](../../../../../adr/decision-119.md), [120](../../../../../adr/decision-120.md) and
[121](../../../../../adr/decision-121.md). Preserves CP-01–14 and INV-002/003/006, refining CP-02's
stderr display mechanism and CP-11's candidate authority guard. No archive or
operation schema, runtime dependency, MCP, production operation or deployment
authorization is added. The config lock is a retained lock inode, not a new JSON
format or operation journal. Real host credential/hardening/SELinux/NFS acceptance
remains operator work.

Enforcement: [fixed command construction](../../../removed-interface-records.md),
[injected runner](../../../removed-interface-records.md),
[bounded UTF-8 framing](../../../removed-interface-records.md),
[typed progress notices](../../../removed-interface-records.md),
[terminal/envelope classification](../../../removed-interface-records.md),
[API adapter](../../../removed-interface-records.md),
[configuration adapter](../../../removed-interface-records.md),
[exact config guard](../../../removed-interface-records.md),
[readiness/confirmation pipeline](../../../removed-interface-records.md) and
[unit-action boundary](../../../removed-interface-records.md).
Evidence: [command tests](../../../removed-interface-records.md),
[runner tests](../../../removed-interface-records.md),
[framing tests](../../../removed-interface-records.md),
[event tests](../../../removed-interface-records.md),
[envelope tests](../../../removed-interface-records.md) and
[configuration tests](../../../removed-interface-records.md). These fixtures do not
prove deployed browser/credential/hardening acceptance.
Candidate-specific evidence: [guarded file fixtures](../../../removed-interface-records.md)
and [pipeline tests](../../../removed-interface-records.md).

## 2026-10-18 native Unix prefix and REST acceptance amendment (API-016)

## 2026-10-18 explicit rootless runtime amendment (OPS-015)
