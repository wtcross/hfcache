# Decision 122 — Preserve Cockpit authority through the API client and guarded candidates

- Status: Accepted; implemented by API-015 on 2026-10-18; deployed browser/
  credential/hardening acceptance remains an operator hold.
- Date: 2026-10-18.
- Work package: API-015, this commit.
- Source: [progress decision 122](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-015-cockpit-api-client-compatibility.md).
Native Unix/public-prefix routing is amended by [decision 123](decision-123.md).

## Context and decision

Cockpit continues to invoke the installed CLI and systemd under its existing
administrative/root/service separation. Transient CLI units import only the
named API credential `hfcache.api`, use fixed local client TOML/socket and omit
ordinary archive `--config`. Neither the page nor command arguments receive a
bearer; Hub credentials remain on the daemon. Full sync/verification retain their
installed service names. Schedule controls remain sync-timer only, with no init
UI, verify-timer enablement or target/mount manipulation.

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

Amends [087](decision-087.md), [089](decision-089.md), [091](decision-091.md),
[092](decision-092.md), [119](decision-119.md), [120](decision-120.md) and
[121](decision-121.md). Preserves CP-01–14 and INV-002/003/006, refining CP-02's
stderr display mechanism and CP-11's candidate authority guard. No archive or
operation schema, runtime dependency, MCP, production operation or deployment
authorization is added. The config lock is a retained lock inode, not a new JSON
format or operation journal. Real host credential/hardening/SELinux/NFS acceptance
remains operator work.

[Cockpit](../cockpit.md), [client](../api-client.md),
[configuration](../configuration.md), [security](../security.md) and
[invariants](../invariants.md) own detailed contracts. The task records actual
source APIs, acceptance and full-gate evidence as implementation settles.

Enforcement: [fixed command construction](../../cockpit/src/lib/command.ts),
[injected runner](../../cockpit/src/lib/runner.ts),
[bounded UTF-8 framing](../../cockpit/src/lib/stream.ts),
[typed progress notices](../../cockpit/src/lib/events.ts),
[terminal/envelope classification](../../cockpit/src/lib/envelope.ts),
[API adapter](../../cockpit/src/api/hfcache.ts),
[configuration adapter](../../cockpit/src/api/config.ts),
[exact config guard](../../cockpit/src/lib/candidate-guard.ts),
[readiness/confirmation pipeline](../../cockpit/src/lib/config-pipeline.ts) and
[unit-action boundary](../../cockpit/src/lib/systemd.ts).
Evidence: [command tests](../../cockpit/test/command.test.ts),
[runner tests](../../cockpit/test/runner.test.ts),
[framing tests](../../cockpit/test/stream.test.ts),
[event tests](../../cockpit/test/events.test.ts),
[envelope tests](../../cockpit/test/envelope.test.ts) and
[configuration tests](../../cockpit/test/config.test.ts). These fixtures do not
prove deployed browser/credential/hardening acceptance.
Candidate-specific evidence: [guarded file fixtures](../../cockpit/test/candidate-guard.test.ts)
and [pipeline tests](../../cockpit/test/config-pipeline.test.ts).


## 2026-10-18 native Unix prefix and REST acceptance amendment (API-016)

Cockpit's fixed local socket/client settings remain valid with a public TCP
prefix through the server's trusted native Unix path distinction. Browser code
gets no prefix/credential authority, and candidate/terminal/progress/uncertainty
controls are unchanged. Fresh complete REST acceptance, not installed-host proof,
gates MCP; see [decision 123](decision-123.md).


## 2026-10-18 explicit rootless runtime amendment (OPS-015)

[Decision 127](decision-127.md) selects explicit rootless USER services and a
system-to-user target bridge, fixed immutable runtime/container-client commands,
non-killing drain and actual container peer/FD/secret/isolation proof. It replaces
the initial Quadlet proposal to avoid generated replacement/forced cleanup/timeouts.
Selected-profile Cockpit retains outer privilege/candidate guards but API secret
delivery moves to the fixed Podman client launcher, without host ImportCredential.
NAS/other-host restrictions, exact operation truth and previous evidence remain;
OPS-015 fixtures bind no NAS and perform no production switch or release.
