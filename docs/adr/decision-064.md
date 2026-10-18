# Decision 064: The event log is emitted, not returned; and its vocabulary is closed

Status: amended by [decision 111](decision-111.md) for execution correlation and
[decision 124](decision-124.md) for bounded MCP diagnostics;
accepted when recorded and retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `OBS-002`.
- Source: [decision 64 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Two choices carry this module, and both were
between something testable and something merely tidy.

**A module-level logger rather than a threaded-through object.** The
alternative was an `EventLog` instance passed from the CLI down through
`sync`, `publication`, `retention`, and `recovery`. That is the design that
survives a second concurrent run in one process — and `AD-17` says there is
exactly one writer and the lock is local, so a second run in one process is
not a state this application has. What the threaded version would actually
have bought is an extra parameter on eleven functions whose signatures plan
§13.2 already fixes, and `# noqa: PLR0913` on several of them. The module
keeps its state resettable and `reset()` is what the suite uses between
tests, so the usual objection — leakage — is closed where it could bite.

**`emit` raises on an unknown name.** A logger that quietly accepts any
string is the normal shape, and it is wrong here. The names are the
interface: `docs/cli.md` §6 tells an operator to filter on
`event=publication.completed`, and a typo would produce a line that looks
right in a terminal and matches nothing. Every call site is in this
repository and covered, so the raise cannot reach production; what it does
reach is the test run of whoever adds the fourteenth event.

**Where `retention.deferred` had to go.** §7.4 lists a `cleanup_deferred`
checkpoint and `transactions.py` accepts the name, but nothing in
`retention.py` records one — the post-commit steps run inline and a failure
there leaves a tombstone rather than a marker. So there is no moment in a
prune at which "cleanup was deferred" is known. The tombstone found later by
`recovery._deferred_warnings` is the only real signal, and the event is
emitted there, beside the `HFWRN002` it already raises. The checkpoint name
is left in place: it describes the state §7.4 intends, and closing that gap
is a durable-contract change rather than a logging one.

**One incoherence fixed in passing.** `emit_envelope` minted a fresh run id
for any command that wrote no durable report, and its own docstring claimed
this "still ties the envelope to that invocation's log lines" — which was
true of nothing, because there were no log lines. Now that there are, the
envelope reports the id `configure` bound, and the claim is true.

## Later history and current interpretation

[Decision 77](decision-077.md) supersedes the temporary retained permit for
`cleanup_deferred`: the name is removed because an open post-commit journal
already expresses deferred work. The logging vocabulary remains closed.

[Decision 111](decision-111.md) (`API-004`, 2026-10-17, this commit) amends
the one-run-per-process assumption. A daemon can interleave metadata requests
with a guarded writer without creating a second archive writer. Correlation
therefore uses an immutable context-scoped snapshot, captured at event emission
and copied into worker submissions. Scoped exit restores earlier bindings;
daemon logger configuration is startup-only. The module-level event API,
stderr output and closed vocabulary remain. Shared exact-value registration
also extends redaction to opaque credentials and exception/problem diagnostics.

## Provenance and governing evidence

The source entry first appears in
[78f373c](https://github.com/wtcross/hfcache/commit/78f373ca627cf94fa9143a82051edcb2d41ae9b8)
(2026-07-27, `OBS-002: implement §24's structured event log`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/logging.py](../../src/hfcache/logging.py),
[src/hfcache/reporting.py](../../src/hfcache/reporting.py).

Relevant verification:
[tests/unit/test_logging.py](../../tests/unit/test_logging.py).

## 2026-10-18 optional MCP diagnostic amendment (MCP-001)

[Decision 124](decision-124.md) adds the stable warning event `mcp.diagnostic`
to the closed `EVENTS` vocabulary. The lifespan-scoped bridge suppresses SDK
messages below WARNING and emits fixed diagnostic text through ordinary `emit()`,
preserving authoritative captured correlation, original lowercase `sdk_level`
and sanitized `sdk_logger` bounded to 256 characters. It never formats SDK
messages/arguments/exceptions, which can contain rejected values. It does
not forward raw rejected values/tracebacks through arbitrary logger messages or
reconfigure the daemon per request. Original SDK handlers/propagation are restored
on exit. This is operational transport evidence, never an archive checkpoint,
command outcome or job receipt. Existing event names remain stable.
