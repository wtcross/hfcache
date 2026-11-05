# Transport guarded configuration bytes without NUL text frames

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 138.
- Status: Historical framing decision; current helper transport follows decision 150.
- Date: 2026-10-20.

## Context and decision

The removed interface's text channel could disconnect on NUL input before any
process exit evidence arrived. Its candidate guard therefore used two canonical
LF-terminated base64 fields, preserving exact candidate and installed-base UTF-8
bytes without putting NUL on the text wire. Both decoded documents retained a
1 MiB bound; candidate was nonempty, base could be empty. Encoded lines were
bounded to 1,398,104 bytes and the complete frame to 2,796,210 bytes. Validation
of both fields preceded filesystem or lock effects and preserved trailing
newlines in exact-content comparisons.

## Rationale and alternatives

Changing the text bridge to a binary channel would also change stdout/error
collection. Bounded ASCII framing repaired the input boundary while retaining
classified terminal output. Canonical re-encoding, complete UTF-8 and NUL/size
checks rejected truncation and partial decoder success. No secret source,
archive authority or runtime dependency was added. The later in-memory parsing
correction below removed a false asynchronous-reader completion dependency.

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
replacement design. The independent typed Unix helper protocol supersedes the removed interface transport while preserving bounded exact bytes, the persistent configuration lock and original uncertain evidence. Its framing is specified in [host administration](../host-administration.md).

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

The historical framing rationale is paraphrased from the pre-removal record in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
