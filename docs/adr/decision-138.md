# Transport guarded configuration bytes without NUL text frames

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

## 2026-10-21 protected-reader amendment

## Context and decision

## Rationale and alternatives

## Consequences and relationships

Amends [decision 122](decision-122.md) and [decision 134](decision-134.md), retaining
the original root configuration lock, fixed paths/launcher, exact-content guard,
ownership, backup and atomic installation. No API, authentication, credential,
archive, workload, cleanup or replay authority changes. An uncertain earlier
attempt remains preserved. A fresh independent disposable fixture is required
for subsequent candidate/bridge acceptance; changing a diagnostic cannot prove
the original installed problem fixed.

## Replacement UI design amendment (2026-10-20)

[Decision 141](decision-141.md) amends this record for the accepted
replacement design. Accepted future typed helper protocol replaces neither current framing nor original config evidence until implemented and tested. It preserves bounded exact bytes and the existing persistent lock.

## In-memory line parsing correction (2026-10-20)

Split the already bounded frame into its two encoded fields in memory and
require exact frame reconstruction before decoding. Remove the unnecessary
builtin-only asynchronous line producer and wait. Retain the bounded external
reader, decoder/encoder completion checks, canonical base64, UTF-8/NUL/size
validation and all original pre-effect guards. Here-string/tempfile parsing
would introduce file effects before validation and is not selected. No wire,
dependency, permission, lock or uncertainty contract changes.

The regression exercises the real rendered guard with a deterministic synthetic
line-reader wait failure; maximum-size and malformed frames retain their bounds.
Source gate and owned shell fixtures prove that correction, not a cause or fix
for an uninspected installed host. Production replacement remains separate.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
