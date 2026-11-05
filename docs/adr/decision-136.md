# Read run reports through REST and keep journals diagnostic

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

## Context and decision

`runs list [--limit N] [--cursor TOKEN]` requests one page, default min(100,
authenticated server page limit), bounded
1–10,000 and by existing server/client limits. `runs show RUN_ID` requests one
exact 32-character lowercase hexadecimal domain run ID. Inventory contains IDs, not invented start
times or filenames. Validate response wrapper, command, payload and archive
identity; detail additionally binds requested ID, Envelope ID and durable report
ID/archive. Historical report policy fingerprints need not equal current policy.
Both commands reject job/candidate/local modes before effect or credential use.

Keep stdout `--json` as the exact original schema-1 server Envelope, including
valid nonzero results. A successful read emits exactly one bounded machine line
on stderr before the Envelope: `Run read metadata: ` followed by compact JSON.
Its exact fields are `schema_version=1`, `command` (`runs` or `runs read`),
`run_id`, `request_id`, `archive_id`, `config_fingerprint`, `next_cursor`.
IDs/fingerprint come from validated response metadata; successful report reads
require nonnull archive/policy identities. Cursor is null for detail and otherwise
the bounded opaque original cursor. Bound the line to 2 KiB, reject secret-bearing
or unsafe metadata and emit it even in quiet mode. Failure needs no metadata.
This line is read correlation/page metadata, never an operation receipt/result.

The plugin independently collects that one validated line outside display
truncation and binds it to the terminal Envelope. Missing, duplicate, conflicting
or malformed metadata refuses successful presentation. Failed Envelopes retain
their original classification without requiring success-only fields. Display one
page of 50 IDs with explicit Next/Return-first navigation; replace rather than
accumulate pages. Bind detail and navigation to the listed archive identity.
Session/refresh/navigation invalidates old list/detail evidence and late results.
Serialize detail reads per mounted view, including while navigation discards the
pending result. Repeated clicks never create overlapping readers or close a CLI
observer as a shortcut.

Remove direct host archive `ls`/`cat` after CLI/API and component parity. Optional
journal display remains a fixed host-local diagnostic and cannot prevent report
reads or establish outcome. Query only fixed sync/verify system units or fixed
API/verification user-unit journal fields, a seven-day horizon and at most 201
newest entries. The privileged query is bounded by an owned five-second process
deadline (one-second termination grace), with a six-second client deadline and raw
256 KiB cap. Retain at most 200 lines/64 KiB with 8 KiB line bounds and explicit
truncation/unavailable state. Only validated closed event/level and exact literal
run-ID correlation render; arbitrary MESSAGE prose/unknown fields are withheld.
Closing only this owned read diagnostic never closes a CLI operation observer.

## Rationale and alternatives

Another REST endpoint or generic forwarding would duplicate existing authority.
Returning a bare ReadResponse violates the CLI Envelope contract. Rewriting list
success data to carry a cursor would lose exact server-envelope parity. A bounded
separate read-metadata line preserves that parity and explicit pagination without
unbounded reconstruction. Raw host filenames and arbitrary journal messages are
unnecessary browser authority. Complete inventory accumulation and automatic
cursor restart are rejected; stale/refused reads stay visible.

## Application Operations/report composition (2026-10-26)

The application-owned browser reuses existing typed operation/run reads and exact
report/result identities. Its separate25-row operation/run pages retain at most32
cursor positions and explicit stale-cursor restart; local25-row report collections
are presentation of already validated bounded data. Loaded history is never a
complete archive/repository audit. Events/journals stay diagnostic and do not
replace classified domain results. See [Operations](../web-ui/operations.md).
No endpoint, report format, archive-path access or execution authority changes.

## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
