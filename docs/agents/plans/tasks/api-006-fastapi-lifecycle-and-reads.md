# API-006: Serve authenticated REST resources with a controlled lifespan

| Field | Value |
| --- | --- |
| Work package | `API-006` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-005](api-005-server-config-and-bearer-auth.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-006: serve authenticated FastAPI metadata resources` |

## Scope and acceptance

1. Build an injectable FastAPI app factory and `hfcache serve` bootstrap. Use one lifespan for dependencies, read-pool bounds, instance locking, startup checks, and shutdown. Importing the app must not start listeners, contact the Hub, mutate an archive, or initialize storage.
2. Expose version/capabilities/health, status, inventory/revision pages, exact references/manifests, existing report reads, verification estimates, and archive inspection through shared query services. Handle an uninitialized/unreachable archive diagnostically; authenticated health never repairs it.
3. Protect every REST route, error surface, OpenAPI document, and optionally enabled docs UI. Configure request/body/response limits, safe headers, trusted proxy/Host/Origin rules, and typed HTTP error translation. Test both path components of namespace/name repository IDs.
4. Offload blocking filesystem queries to a bounded pool so event-loop responsiveness is independent of archive scanning. Define deterministic pagination, identity checks, stale/vanished publication errors, and safe large-report streaming. Use one registry for Unix/TCP serving, not independent writer apps.

## Contracts, invariants, and ADRs

`FS-01`–`FS-03`, `FS-08`–`FS-12`, `FS-16`, `INV-003`, `INV-005`–`INV-008`; plan §§3–4.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Expand API resources/errors/pagination and server lifespan/listener documentation. Update README and consumers for published-relative locators and authenticated reader discovery. Document current route availability honestly before job routes land.

## Validation

Planned checks, not execution evidence:

ASGI factory/lifespan and real ephemeral local-socket smoke tests; auth across all routes including docs; no startup archive writes; missing/corrupt catalog; mount unavailable; malicious IDs/path traversal; concurrent read responsiveness; page boundary and large-report tests. Run `scripts/check.sh`.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Implementation authorized by the active plan and Tyler's 2026-10-17 instruction;
API-005 is completed in `1d31a3f`. Collaborators share this API-006 work-package
boundary: application/bootstrap, metadata/query containment and adversarial tests,
and documentation/records. No later task has begun.

Contract review includes FS-01–03/08–12/16, INV-003/005–008/012/013 and decisions
108/111/112. The metadata transport must retain exact publication identity and
published-relative reference locators, make missing/unreachable archive state
diagnosable without repairs, and preserve tolerant derived-catalog/unknown
verification behavior. Legacy status/list/catalog/latest-report paths are part
of the shared read boundary, not an exception to containment.

Implemented the injectable `create_app` read factory, strict `ReadResponse`/
`ApiProblem` wrapper metadata and authenticated resource set. All error/schema/
optional-docs/unknown-method/path surfaces authenticate before routing or body
processing. Host/Origin/proxy/prefix and request/query/header/response ceilings
fail safely; noncanonical slash paths do not redirect rejected secret queries.
Fresh policy snapshots run in a bounded copied-context pool. Its lease remains
held through both worker and request/stream completion. Health is diagnostic,
not archive integrity or initialization proof; budget failures still propagate.

Status/inventory/revisions/report-ID pages preserve deterministic ordering.
Cursors bind route/filters/policy and sanitized row contents; stale continuation
is 409, malformed syntax 422. Existing report run IDs survive wrapping; reference
locators explicitly remain `published/`-relative and manifest tree metadata says
`archive-root/`. Reports/manifests are parsed within finite source/aggregate
budgets and incrementally encoded in <=8192-byte chunks, with pre-counted encoded
ceiling. This retains a bounded parsed representation, not constant-memory raw
artifact transfer. Public remote CLI reconstruction remains API-011–013.

Shared `MetadataReader`/`QueryBounds` harden local status/list/latest-report/
catalog, inspection, health/cleanup and estimate paths with every-component
no-follow descriptor reads/stat/listing and visible budget refusal. Local CLI
default queries retain complete results. Missing/corrupt/unsafe catalog evidence
stays unknown; current confidence additionally requires valid matching references,
manifest/tree/generation. Reports validate archive UUID and filename/time/run;
the verification catalog has no UUID field. Sentinel inspection stays separate,
without pretending every metadata read proves or repairs it.

The explicit lazy `serve --server-config` bootstrap runs one locked Uvicorn
instance/lifespan for Unix/TCP, with verified direct TLS only on TCP and no raw
framework request logging. Runtime parents must preexist; startup never adopts
or unlinks an existing socket, and shutdown removes only its own unchanged socket
inode. The daemon lock inode is retained. Typed lifespan startup failures keep
their original code/exit despite Uvicorn's startup flag. Normal foreground daemon
execution has no success Envelope/stdout; `--json` preserves classified startup
failures. Real disposable-socket tests use OpenSSL-generated test certificates,
including CA rejection, with no production TLS or host change.

Decision 113 amends decision 112's deferred enforcement and records HFAPI005/
008/009/011 safety exit-20 overrides; other auth/config/request HFAPI cases stay
10. API/server/CLI/consumer, architecture/invariant/security, README and Unreleased
contracts identify eight implemented HTTP read parity rows; 21 remaining rows
stay planned. No dependency or durable schema changed. Job/candidate/config-
validation routes, receipts, write execution, client CLI migration, verifier
isolation and MCP remain later tasks. No production listener, deployment or
archive operation occurred. The final integrated gate passed; the next selected
task is API-007.

Validation in progress: focused app/config/auth/taxonomy tests passed 227 cases;
the final adversarial HTTP selection passed 76, metadata selection 181 and
bootstrap selection 9. First full-gate attempt stopped on formatting in the new
adversarial test file. The next attempt reached the Python suite: 2,126 passed,
one failed, 40 deselected. The failure is the existing damaged-reference estimate
regression (`test_estimate_exits_zero_on_a_damaged_archive`): secure reader
extraction double-counted a readable current reference whose per-SHA reference
was already unreadable. The correction keeps separately damaged/mismatched
current-reference diagnostics, places complete target resolution inside the
estimate's exit-0 diagnostic boundary and avoids a duplicate manifest read.
Four regressions were added; final estimate selection passed 22 tests, 82
deselected in 2.07s. The third full gate confirmed estimate parity, then found
a metadata lease callback race: an error response completed before the scheduled
worker-done callback released its capacity slot (2,130 passed, one failed).
Capacity accounting now uses the original concurrent Future's actual completion
state while retaining a truly running worker after disconnect. Deterministic
delayed-callback and cancelled-observer regressions pass; the final focused
HTTP/bootstrap selection passed 96 tests in 5.82s, with whole-project formatting,
lint and Pyrefly green. The fourth full gate passed completely. No build/install/
Cockpit success is claimed from either failed Python-suite attempt; final evidence
below records the successful complete run.

## Completion evidence

2026-10-17, API-006, this commit.

The injectable read application and lazy foreground bootstrap now serve the eight
metadata parity rows, plus authenticated health/schema/optional docs; the other
21 parity rows remain planned. Every HTTP surface authenticates before routing/
body/error processing, including unknown methods/paths. Tests cover strict Host,
duplicate Origin, trusted proxy/root prefix, raw query/header/body and normal/
streamed response bounds, no slash-query redirects, safe headers, sanitized typed
problems, authoritative IDs and role-capability discovery. ReadResponse preserves
schema-1 Envelope identity/outcomes; exact namespace/name/commit/publication
paths retain declared locator bases. Content-bound cursors refuse changed rows,
scope/policy or impossible offsets; complete ordered walks and stale refusal
are tested. Reports/manifests stream prevalidated bounded parsed evidence in
<=8192-byte chunks, retaining capacity until the stream/worker really finishes.

Shared no-follow metadata reads cover local and HTTP status/list/latest-report/
catalog/inspection/health/estimate paths, using descriptor-pinned directories,
ordinary files and metadata-only stats plus visible shared entry/byte budgets.
Unknown/corrupt/unsafe catalogs cannot create confidence or authorize repair.
Current confidence requires valid matching reference, manifest/tree and generation;
report UUID/filename/time/run identity is checked. Inspection diagnoses sentinel
state separately without writing or claiming every read proves it. CLI defaults
retain complete results without transport ceilings. Damaged estimates preserve
their existing exit-0 diagnostic semantics and avoid duplicate target counts.

One Uvicorn instance/lifespan, auth registry and pool serve private Unix/TCP;
real ephemeral-socket tests verify direct TCP TLS, local Unix HTTP and CA
rejection with disposable OpenSSL test certificates. No runtime directory is
created; existing socket names are refused, cleanup checks the exact created
inode and the daemon lock is never unlinked. Reserved addresses accept no
connections before successful TLS/lifespan startup. Startup failures preserve
their original code/exit and JSON failure Envelope; normal serve has no success
stdout Envelope. Worker context propagation, responsive independent version
reads, saturation, error cleanup, duplicate daemon refusal and restart are tested.
Both delayed-callback and cancelled-observer regressions prove exact capacity
ownership using the original concurrent Future.

Reviewed FS-01–03/08–12/16, INV-003/005–008/012/013 and decisions 108/111/112.
Added decision 113/index and decision-112 amendment; updated architecture,
invariants, API resources/matrix/wire/errors/pagination, server configuration/
lifespan/listeners, CLI taxonomy/serve exception, security, authenticated consumer
discovery, README, original plan and Unreleased notes. HFAPI005/008/009/011
explicitly classify service safety failures at exit 20; other HFAPI request/
auth/config cases retain 10. No new runtime dependency or durable archive schema.

Validation:

- Focused app/config/auth/taxonomy sweep: 227 passed in 6.37s; metadata sweep:
  181 passed in 6.79s; final adversarial HTTP suite: 76 passed. Bootstrap suite:
  9 passed in 1.65s. Final estimate regressions: 22 passed, 82 deselected in 2.07s.
  Final HTTP/bootstrap selection: 96 passed in 5.82s.
- `rtk proxy bash scripts/check.sh > .scratch/api-006-gate.log 2>&1`:
  final fourth attempt exits `0`. Lock/server-extra sync, 301 Python files
  formatted, lint and Pyrefly (0 errors), 2,133 Python tests (40 deselected,
  114.37s), wheel/sdist 0.1.10, real isolated locked base/server installation/
  import/help/version, Cockpit lint/styles/types, 45 tests and production build
  all pass. Three earlier stops are retained above: formatting only; damaged-ref
  estimate parity; and a real worker-completion/capacity race. Each was corrected
  and regression-tested before the successful complete run.
- `rtk proxy python .scratch/audit_records.py`: local documentation links,
  task dependencies/current pointer and API parity structure pass. Availability
  audit confirms eight implemented metadata rows and 21 planned rows. Numbered
  decision/ADR coverage passes all 113 records without duplicates;
  `rtk git diff --check` passes.

No opt-in live Hub/NFS, additional build-marker or installed-host acceptance ran;
required real local-socket/TLS and base/server wheel smoke checks did run.
No production listener, archive operation, deployment, push, merge or tag occurred.
Jobs/receipts, candidate validation, API-client CLI migration, isolated verification
and MCP remain their pending tasks; API-014/016 own installed acceptance and the
REST gate. A stale socket after a crash requires operator proof that it is unused
before cleanup. Completed
[progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17)
and current selection agree.
