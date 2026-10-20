# Transport guarded configuration bytes without NUL text frames

- Decision identity: 138.
- Status: Accepted; source regressions and actual disposable Cockpit framing/configuration acceptance passed; original installed symptom remains separate.
- Date: 2026-10-20.

## Context and decision

Independent read-only native Cockpit sessions reproduce a bridge interruption:
four ASCII input bytes reach an ordinary and a privileged host reader, while
four input bytes containing NUL disconnect the actual text bridge with the
original `problem: disconnected` and no exit status. Guarded candidate commands
previously joined their captured documents with NUL on that same text channel.
This proves a transport defect in the disposable environment. The earlier
uncertain candidate click and the original installed symptom remain separately
unresolved; do not reconstruct their missing stage evidence from this probe.

Keep Cockpit spawn output and error semantics as text. Send exactly two canonical
base64 lines, each LF terminated, containing candidate and installed-base UTF-8
bytes. Each decoded document retains the existing 1 MiB bound; candidate cannot
be empty, installed base can. Each encoded line is at most1,398,104 bytes and
the complete frame is at most2,796,210 bytes. The fixed host guard reads bounded
input, rejects embedded wire NUL and any extra/truncated data, decodes in memory,
requires exact canonical re-encoding, valid complete UTF-8, no decoded NUL and
the original byte bounds. Both documents pass before filesystem or lock actions.
All trailing newlines remain part of exact-content comparisons.

## Rationale and alternatives

Raw NUL text input demonstrably interrupts the bridge. Cockpit binary channels
also change stdout into byte arrays, requiring a broader change to bounded
Envelope/error collection. ASCII framing fixes the actual stdin boundary while
preserving existing output classification. Canonical re-encoding catches invalid
padding, decoded NUL and truncation without trusting a partial decoder result.
Existing Bash/coreutils suffice; no runtime dependency is added.

## Consequences and relationships

Amends [decision 122](decision-122.md) and [decision 134](decision-134.md), retaining
the original root configuration lock, fixed paths/launcher, exact-content guard,
ownership, backup and atomic installation. No API, authentication, credential,
archive, workload, cleanup or replay authority changes. An uncertain earlier
attempt remains preserved. A fresh independent disposable fixture is required
for subsequent candidate/bridge acceptance; changing a diagnostic cannot prove
the original installed problem fixed.

The [Cockpit contract](../cockpit.md), CP-11 in the
[invariant register](../invariants.md#cockpit-boundary),
[guard implementation](../../cockpit/src/lib/candidate-guard.ts) and
[filesystem regressions](../../cockpit/test/candidate-guard.test.ts) define and
enforce the byte boundary. Native read-only reproduction, source regression,
fresh disposable acceptance and later installed verification are separate evidence.
