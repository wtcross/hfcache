# Verify one protected administrator without widening legacy credential classes

- Decision identity: 146.
- Asset/bootstrap refinement: [decision147](decision-147.md).
- Status: Amended; bounded Basic is implemented, with UI-only serving refined below.
- Date: 2026-10-20.
- Introducing evidence: 24625fc; source and isolated acceptance are separate.

## Context and decision

[Decision140](decision-140.md) accepts Basic browser authentication inside the
existing application. Concrete provider, source, work admission and key ownership
must preserve bearer/MCP compatibility and avoid event-loop starvation.

Reuse the already locked cryptography50.0.2 package as a direct optional-server
requirement, constrained to its reviewed major release. Base readers do not gain
that dependency. Use public Argon2id PHC derive/verify APIs; do not implement a
password hash or add another wrapper around an already available implementation.
The maintained package supports the selected Python/CentOS wheel platform; actual
profile installs and the exact verification benchmark remain required evidence.

An optional restart-only `basic` object contains one canonical HTTPS `origin`
and `administrator` CredentialSource (exactly one protected `file` or
`systemd_name`). Its origin must also occur in listener.allowed_origins. Absence
disables Basic without reading a record. A configured unusable source fails
startup; required writer and optional REST/MCP bearers keep existing semantics.
The protected strict JSON record has exactly `schema_version:1`, `subject`,
`username` and `password_hash`. It is at most8192bytes, rejects duplicate/unknown
fields, coercion and source races, and inherits descriptor-pinned no-follow,
regular/single-link/owner/group/mode checks. Stable subject is a nonempty ASCII
identifier matching `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`; username is nonempty printable UTF-8, at most
128bytes, without colon. Neither is a password or a bearer substitute.

Before any hash work, validate canonical ASCII PHC algorithm argon2id/version19,
exact ordered m65536/t3/p1, unpadded canonical standard Base64 salt16/hash32.
Unknown parameters, encodings or resource choices refuse startup. Provision a
fresh random salt from protected non-echoing input; never accept a password in
arguments/environment/files or emit it in diagnostics. Actual verification uses
the one validated configured hash even for a wrong username. Combine constant-time
username equality with that result only after equivalent hash work.

One dedicated two-thread executor has eight explicit waiting slots. Keep its
work independent of metadata/operation observation and off the event loop. A
bounded monotonic global deque tracks at most30 failures in60seconds. Reserve
active attempts under the same short lock, recheck/prune when queued work starts,
and refuse expensive work when completed failures plus reservations reach30.
Request cancellation retains admission until actual work completes. Stop new
admission, drain every accepted job and join exact workers under lifespan
cancellation deferral. Capacity/throttle refusal is HFAPI021/HTTP429/exit20;
provider failure/drain is unavailable, never a successful login or empty result.
Wrong credentials retain HFAPI001/401 and forbidden capabilities HFAPI002/403.

Preserve `Principal(CredentialClass)` and its legacy `.capabilities` values.
Add internal authentication method, stable subject and a separate immutable
administrative set: config-read/config-write/host-read/schedule-write/observer-stop.
Bearer principals have no administrative grants. Basic projects publicly as
rest-writer/read+write but never authenticates MCP. Helper proof still intersects
administrative grants before host effects; login alone grants no protected host
policy, archive writability, Hub credential or scheduling permission.

Version Basic original-key ownership as SHA256 of
`hfcache\0idempotency\0basic-subject\0v1\0`, then u32 big-endian UTF-8 subject
byte length, subject bytes, u32 big-endian ASCII key length and original key bytes.
Validate the unchanged printable key grammar first. Bearer remains byte-identical
SHA256(original ASCII key). Never translate to a printable surrogate key. No
fields or attribution sidecars join old strict receipts; historical class labels
identify no person. A future private attribution record must version separately.

The outer boundary dispatches one bounded Authorization scheme with no fallback.
Cheap header/query/body-length/work bounds for configured Basic and its TLS
transport proof precede expensive verification. Bearer/missing/disabled-provider
authentication retains its old precedence over work-bound errors; bounds apply
to every successfully authenticated request. Authentication and permissions
precede routing/body parsing/domain work. MCP retains bearer-only
verification. Basic challenges permit native browser retry/reuse, while explicit
bearer and MCP failures retain their challenge. Missing REST credentials when
Basic is enabled may advertise both supported schemes; UI-only Basic serving is
separate. Every unsafe Basic method, including unknown/denied paths, requires
exact configured Origin, JSON and exactly `X-Hfcache-Request:1`. No-Origin bearer
compatibility remains. Off-host Basic requires verified TLS/trusted proxy proof;
authenticated native Unix access remains separately corroborated.

Scrub Basic Authorization text unconditionally, independently of exact secret
registration. Never register failed supplied passwords in the global redaction
set. Expose only coarse problems and stable nonsecret identity; keep passwords out
of logs, traces, browser JavaScript, fixtures and persistent state. Browser-managed
Basic lifetime has no reliable application logout. Native encrypted credentials
and the rootless API's existing protected `/etc/hfcache/credentials` directory view
are distinct delivery profiles. Worker/client masks cover that directory and
Caddy has no such bind. Any later fixed API-only Podman secret delivery must be
explicitly indexed and tested in release packaging; no unconditional new secret
requirement joins backend-only deployments. Caddy, worker and clients receive no
administrator record.

## Rationale, consequences and evidence

Reusing the locked maintained verifier avoids adding two Argon2 wrapper packages
and another bundled implementation. Constructor defaults are insufficient: encoded
PHC parameters otherwise select work, so independent canonical inspection is
mandatory. A shared metadata/default executor would let password floods starve
operation observation. Unbounded IP maps and early cancellation release would
invalidate admission bounds. Class-only Basic key ownership would collide with
bearer recovery; printable translated keys would leave that namespace forgeable.

Real TCP/Unix, cancellation/concurrency/flood and old-client tests are required.
Three actual native browser challenges and trusted-CA positives/untrusted negatives
must pass without per-request Authorization injection or certificate bypass.
Test-only Noble browser dependencies may run in a fresh isolated CentOS guest;
shipped application/Caddy UBI and native profiles remain separate. No source test,
benchmark or fixture implies production or NAS acceptance. Shared Caddy/static
conformance remains part of the serving design.

Amends [140](decision-140.md), [112](decision-112.md), [113](decision-113.md) and
[114](decision-114.md), preserving [111](decision-111.md), [123](decision-123.md),
INV-001/002/003/013/014/019 and FW-03/04. See
[public verifier API](https://cryptography.io/en/50.0.2/hazmat/primitives/key-derivation-functions/#argon2id),
[supported installations](https://cryptography.io/en/50.0.2/installation/),
[release metadata](https://pypi.org/project/cryptography/50.0.2/) and
[Basic authentication specification](https://www.rfc-editor.org/rfc/rfc7617).

## Authenticated asset and bootstrap amendment (2026-10-20)

[Decision147](decision-147.md) amends this record. This refinement makes every enabled UI route, asset, alias and error Basic-only while leaving REST Basic/bearer and MCP bearer policy separate. It does not change protected records, Argon2id/admission budgets, stable-subject key ownership, native browser credential handling or existing legacy public classes.
