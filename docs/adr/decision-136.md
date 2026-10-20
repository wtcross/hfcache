# Read run reports through REST and keep journals diagnostic

- Decision identity: 136.
- Status: Accepted; source and temporary CLI/component acceptance passed. Disposable Cockpit/PAM and installed acceptance remain separate.
- Date: 2026-10-20.

## Context and decision

The REST API already exposes authenticated bounded run inventory and exact report
reads. Cockpit instead lists and reads archive filenames through privileged host
commands. Retire that CP-01/09 exception. Add only `runs list` and `runs show
RUN_ID` to the fixed management CLI; no new HTTP route, payload-byte endpoint,
path, method, local fallback or browser credential surface follows.

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

## Consequences and relationships

Amends [decision 122](decision-122.md), [decision 134](decision-134.md), CP-01/09
and [the Cockpit contract](../cockpit.md). Preserves
[decision 135](decision-135.md), INV-005/006, durable report identity, whole-archive
authorization, fixed credentials, archive-byte/NFS separation and fourteen MCP
read tools. [CLI](../cli.md), [API client](../api-client.md),
[API](../api.md), [invariants](../invariants.md#cockpit-boundary),
[CLI source](../../src/hfcache/cli.py), [client](../../src/hfcache/client.py),
[report view](../../cockpit/src/reports.tsx) and
[host diagnostic adapter](../../cockpit/src/api/archive.ts) define the boundary.
Source/temporary fixtures never establish real Cockpit/PAM, installed symptom,
deployment or NAS/workload acceptance. No runtime dependency or durable format
change is introduced.
