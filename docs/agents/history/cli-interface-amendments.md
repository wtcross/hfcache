# Historical CLI interface amendments

Preserved from `db55170:docs/cli.md` before API-018 replaces the accumulated
interface chronology with the current human reference. Relative links repaired;
this record is not current technical authority. See `docs/cli.md`.

# hfcache Command-Line Contract

| Field | Value |
| --- | --- |
| Status | Normative contract for implementation |
| Derived from | `docs/agents/history/plan.md` §11, §22.2, §24 |
| Work package | `ARC-005` |
| Entry point | `hfcache = "hfcache.cli:app"` |
| JSON envelope version | `1` |

The CLI is the only interface to the application. Scheduled runs use exactly the
same commands an operator types, so a behaviour that cannot be reproduced by hand
does not exist.

**2026-10-17 API-001 amendment:** the CLI-only statement above records the
historical interface. [Decision 108](../../adr/decision-108.md) and the activated
[API contract](../../api.md) introduce REST-backed CLI migration incrementally.
Existing CLI behavior remains until its migration packages; remote routes and
MCP are planned, not deployed. Local help/version remain independent.

**2026-10-17 API-006 amendment:** authenticated metadata REST and the foreground
`serve` bootstrap are implemented ([decision 113](../../adr/decision-113.md)). Existing
operational CLI commands still use local services; the API-backed client and all
job/write routes remain later tasks. No deployment is asserted.

**2026-10-17 API-009 amendment:** sync, every non-estimate verification mode,
installed planning, explicit read-only/probing diagnostics and installed
validation now have authenticated REST routes ([decision 116](../../adr/decision-116.md)).
The public operational CLI still uses local services until API-011–013; its
schema-1 output/exit behavior is unchanged. REST jobs return admission receipts
and expose their exact terminal Envelope through operation polling. Maintenance
routes and candidate HTTP/CLI integration remain later tasks; no deployment is
asserted.

**2026-10-17 API-010 amendment:** separate maintenance preview/apply routes,
exact-manifest repair and guarded initialization extend the REST surface
([decision 117](../../adr/decision-117.md)). The HTTP URL defines mode; no omitted
boolean or posted preview authorizes apply. Apply retains shared locked policy/
scope/evidence checks and exact terminal Envelopes. Initialization alone requires
the disabled-by-default server maintenance gate, strict confirmation and restated
configured root/UUID; ordinary maintenance does not use that switch. The public
CLI remains local until its migration packages; these routes are not a deployed
writer or authorization for production initialization.

**2026-10-17 API-011 amendment:** the independent synchronous typed client and
separate client configuration are implemented ([decision 118](../../adr/decision-118.md)).
The four API selection options below are parsed/stored without switching existing
operational commands to HTTP; API-012/013 own that migration. Local help/version
remain independent of configuration/credentials/server. The
[client contract](../../api-client.md) defines exact source/endpoint precedence, finite
observation, safe errors and retained-key uncertainty. No direct archive fallback
or automatic daemon startup is introduced.

**2026-10-18 API-012 amendment:** metadata reads, installed/candidate validation,
planning and explicitly read-only diagnostics now use the typed API client
([decision 119](../../adr/decision-119.md)). Remote rendering retains the exact server
Envelope IDs/timestamps/status/errors and walks complete pages within finite
aggregate limits. Help/local version and explicit `config validate --local` remain
local bootstrap; no API failure falls back to archive filesystem access. The
[client migration table](../../api-client.md#cli-dispatch) identifies migrated
modes while side-effecting CLI migration remains API-013. Candidate files are read
on the CLI host and uploaded as bounded TOML content, never interpreted as server
paths. Validity and installed-authority compatibility are reported separately.

**2026-10-18 API-013 amendment:** all operational CLI modes now submit typed API
requests; no operational command imports or invokes a local mutation backend.
Default job output is the exact terminal server Envelope. Explicit detach emits
identified admission data instead. Keys and accepted operation IDs are printed
to stderr even in quiet mode; interruption/timeout stops observation, never
accepted execution. [Decision 120](../../adr/decision-120.md) and
[operation observation](#operations) define the exception and resume behavior.

**2026-10-18 API-016 acceptance amendment:** the earlier amendments retain each
migration stage's history. All operational modes now use typed HTTP, with explicit
local help/version, `serve` and `config validate --local` bootstrap exceptions.
API-014 packages scheduled observers and API-015 integrates Cockpit. Native Unix
uses fixed unprefixed paths even with a public TCP prefix; public clients retain
their configured URL prefix/security. [Decision 123](../../adr/decision-123.md) and the
[complete parity matrix](../../api.md#routes-and-effects) govern REST acceptance;
MCP remains absent until API-016 passes and commits. No deployment is asserted.

**MCP-001 amendment (2026-10-18).** API-016 acceptance is committed; optional
MCP transport now has its own distinct credential and no curated tools yet.
The operational CLI remains the typed REST client, with no MCP command migration.
See [MCP enablement/limits](../../mcp.md) and [decision 124](../../adr/decision-124.md).


