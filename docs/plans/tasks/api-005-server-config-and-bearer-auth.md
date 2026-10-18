# API-005: Add server dependencies, strict configuration, and bearer capabilities

| Field | Value |
| --- | --- |
| Work package | `API-005` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-004](api-004-isolate-execution-context.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-005: add strict server configuration and bearer capabilities` |

## Scope and acceptance

1. Add the recorded HTTP-client dependency and FastAPI/Uvicorn `server` extra with compatible Python 3.14 versions; update the lock and gate provisioning. Do not add FastMCP yet. Reader imports must not require server packages.
2. Introduce versioned immutable ServerConfig independent of archive TOML. Define private socket/loopback/TLS policy, credential sources, limits, maintenance flag, server startup settings, and reload boundaries. Unknown keys/coercion/invalid paths are rejected without exposing input secrets.
3. Implement distinct REST writer/reader credential validation, using explicit files/systemd credentials, bounded input and constant-time comparisons. Missing writer credentials fail startup; optional unprovisioned reader capability is disabled. Reject ambiguous duplicate secrets. No Hub token reuse or ambient credential lookup.
4. Implement reusable authenticated-principal/capability checks with stable 401 challenge and 403 responses. Register redaction for opaque tokens and test config fingerprints/receipts never contain their values. MCP credential support is a future interface, not an active endpoint.

## Contracts, invariants, and ADRs

`FW-03`/`FW-04`, `AD-21`, `INV-001`–`INV-003`, `INV-010`; plan §3.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Create concrete `docs/server.md` config/auth sections and server config examples. Update configuration/security contracts, FW dependency decision and index, API authentication matrix, README writer installation, and Unreleased changelog.

## Validation

Planned checks, not execution evidence:

Config and credential validation/property tests, token-class matrix, empty/wrong/malformed bearer, invalid file modes/types/symlinks, missing credentials, opaque-token redaction, and Python 3.14 lock/install tests. Ensure base CLI help/version imports without the server extra. Run the gate with the server extra installed.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
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
API-004 is completed in `3626b60`. Collaborators share this API-005 work-package
boundary on the selected feature branch. No later task has begun.

Added direct base HTTPX plus the optional FastAPI/Uvicorn `server` extra without
upgrading existing locked versions. Decision 112 records the material HTTP/TLS,
security and ASGI correctness rationale, Python 3.14 lock and official sources.
The gate installs the implemented extra and performs real isolated locked
base/server wheel smoke installations. The base CLI/auth core do not require
FastAPI/Uvicorn; neither installation includes FastMCP. A bounded verified
HTTPX-construction primitive sends no request; endpoint/auth/response behavior
remains API-011 scope.

Added strict frozen schema-1 `ServerConfig`, separate from archive TOML, and
`packaging/server.toml`. Private Unix and loopback TCP settings default enabled;
explicit enable booleans support TOML selection without null/sentinel paths.
Both disabled is refused. TLS/proxy, Host/Origin, path-prefix and control-character
settings validate before future listener wiring. Required source-only writer
credentials and optional reader/MCP sources remain restart-only. Resource settings
are bounded; admission/route enforcement stays with API-006/007/008.
`InstalledPolicy.snapshot()` reloads immutable archive snapshots and existing
nonsecret fingerprints while pinning startup root/UUID. No hot switch, candidate
installation or server fingerprint format is introduced.

Credential loading pins no-follow directory/file descriptors, validates protected
owner/group/mode/single-inode metadata and bounded bearer content, and refuses
changes to the read inode. Exact opaque secrets register before use; registry
state holds only fixed-size digests. All three capability slots use constant-time
comparison, including disabled dummies. Hub-style tokens, duplicate class values,
configured-but-unusable sources and cross-interface authentication refuse safely.
`Principal` exposes only a fixed nonsecret credential class/capability set.
`BearerAuthentication`/`RequireCapability` are reusable optional FastAPI adapters,
not runtime routes. Central `HFAPI001`–`HFAPI004` retain exit 10 and stable
401 Bearer challenge/403 behavior. Receipt absence is explicit; API-007 must
store only nonsecret principal/correlation metadata.

Reviewed FW-03/FW-04, AD-21, INV-001/002/003/010/013 and decisions 108/111.
Decision 112 and predecessor/index amendments accompany architecture/invariants,
configuration/security, API capability matrix, concrete server keys/credentials,
CLI taxonomy, README installation and Unreleased changes. Existing archive
schemas, Hub credentials and whole-archive authorization remain. No app factory,
runtime endpoint, listener start, MCP import/dependency, production operation,
deployment, push, merge or tag is introduced. Required local acceptance and the
full gate passed; the next selected task is API-006.

## Completion evidence

2026-10-17, API-005, this commit.

Strict frozen server models reject unknown/coerced fields, invalid normalized
paths, literal-secret input echoes, unsafe exposure/proxy combinations and
control/percent-escaped URL prefixes. Property tests exercise safe diagnostics.
Root/UUID pinning, fresh immutable policy reloads and unchanged archive-only
fingerprints are covered. Explicit Unix/TCP enable flags preserve both-enabled
private/loopback defaults and provide valid TOML ways to disable one listener.
Both disabled, off-host plaintext and implicit proxy trust refuse configuration.
Late review found `Literal[int]` accepted a floating-point socket mode despite
strict mode; an exact-integer validator and regression close that coercion.

Adversarial tests cover regular/single-hardlink protected files, every permitted
mode, owner/group restrictions, symlink components, special files, malformed/
oversized/Hub-style tokens, descriptor races and malformed systemd credential
directories. Pathname replacement stays on the checked inode; modifications of
that inode refuse loading. Writer/reader/future-MCP class and capability matrices
prove cross-interface isolation, required-writer/optional-source behavior,
distinct values and three equal-sized constant-time comparisons. Opaque token
values never enter diagnostics, policy fingerprints or principals. No receipts
exist yet; their nonsecret metadata requirement remains API-007 scope.

FastAPI adapter tests retain one bounded original Authorization field, reject
duplicates and cookie/query substitutes, and preserve sanitized 401 challenge/
403 capability responses. Central HFAPI001–004 and taxonomy/doc parity cover
exit-10 classification. The HTTPX helper tests verify explicit TLS, Unix
transport, disabled environment discovery/redirects/retries and finite limits;
it makes no application API request. Actual isolated locked wheel installations
prove base CLI/auth imports and help/schema-1 local version work without server
packages, the server adapter imports with its extra, and FastMCP is absent.

Reviewed FW-03/FW-04, AD-21, INV-001/002/003/010/013 and decisions 108/111.
Added decision 112/index; amended decision 108 and FW rationale. Updated
architecture/invariants, configuration/security (T-14), concrete server keys,
API capability matrix, CLI error taxonomy, original-plan amendment, README
writer-extra installation and Unreleased notes. Locked HTTPX 0.28.1 is now
direct; FastAPI 0.143.3, Uvicorn 0.54.0, Starlette 1.8.0 and opentelemetry-api
1.45.1 are the four added runtime packages. Existing locked versions remain.
No durable archive schema changed; no app factory, runtime route, listener,
MCP import/dependency, isolated executor or host installation is implemented.

Validation:

- `rtk uv run --locked --extra server pytest tests/unit/test_server_config.py tests/unit/test_server_auth_adversarial.py tests/unit/test_api_security.py tests/unit/test_http_transport.py tests/unit/test_taxonomy.py tests/unit/test_credentials.py tests/unit/test_logging.py tests/unit/test_cli.py -q`:
  360 passed in 2.77s. Ruff formatting/checks pass (291 files); Pyrefly reports
  0 errors.
- `rtk proxy bash scripts/check.sh > .scratch/api-005-gate.log 2>&1`:
  exit `0` on the first full attempt, with no gate-cycle failures/fixes. Lock
  check and locked server-extra sync, formatting/lint/types, 2,009 Python tests
  (40 deselected, 109.51s), wheel/sdist 0.1.10, real isolated locked base/server
  wheel installation/import/help/version checks, Cockpit lint/styles/types,
  45 tests (0 failed/skipped) and production build all pass. The isolated wheel
  installs run offline against the populated locked cache.
- `rtk proxy python .scratch/audit_records.py`: changed-document local links,
  task dependencies/current pointer and API parity-table structure pass.
  Numbered decision/ADR coverage passes all 112 records without duplicates;
  `rtk git diff --check` passes.

No opt-in live Hub/NFS, additional build-marker or installed-host checks ran;
the required base/server wheel smoke checks are part of the default gate and
did run. No production archive operation, listener start, deployment, push,
merge or tag occurred. Runtime route protection and host/executor acceptance
remain explicitly pending in API-006/008/014. Completed
[progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17)
and current pointer agree.
