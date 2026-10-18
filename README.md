# hfcache

Archive complete revisions of Hugging Face model and dataset repositories on
long-term storage, and publish them as immutable trees that downstream systems
can copy and verify. Public repositories work anonymously; private and gated
repositories use an explicit required systemd credential.

`hfcache` resolves a configured branch or tag to an immutable commit SHA,
downloads the complete repository snapshot at that SHA through the official
`huggingface_hub` client, SHA-256 verifies every newly introduced object, and
atomically publishes an ordinary-file tree. Consumers mount a server-enforced
read-only NFS export, read one small JSON reference, and copy the exact immutable
tree it names.

A revision is either completely published and verifiable, or it is not visible to
consumers at all.

## What it does

- **Immutable revisions.** Every download is pinned to a resolved 40-character
  commit SHA. Branch and tag names are resolved once per run, never trusted mid-flight.
- **Repository-complete.** Every file in the upstream repository at that SHA. No
  include or exclude filters exist, by design.
- **Verified before publication.** Newly introduced unique content is read and
  hashed locally. Upstream-supplied digests are comparison values, never substitutes.
- **Bounded retention.** Three unique revisions per repository by default, with
  five supported explicitly. A publication beyond the limit prunes the oldest
  eligible one; the current revision is never pruned.
- **Never destructive on error.** Upstream `403`, `404`, deletion, or removal from
  configuration preserves every local revision. Where a failure can leave more or
  less data, it leaves more.
- **Explicit lifecycle removal.** `purge` deletes only complete repositories that
  are already absent from configuration, after a reviewable dry-run, with
  transaction recovery and byte-for-byte manifest audit evidence.
- **Crash-safe.** Every mutation is a single atomic filesystem operation followed
  by a durable checkpoint. Every state a crash can leave has one correct resolution.
- **Content is data, never code.** Nothing from a repository is executed,
  imported, unpickled, or given `trust_remote_code`.
- **Restricted access is explicit.** `hub.token_mode = "required"` enables
  private and gated repositories only when a credential resolves. Every consumer
  of the shared publication export must be authorized to receive that content.

## Requirements

- **Writer host** — Linux with systemd. The runbook
  ([`docs/deployment-centos-stream-10.md`](docs/deployment-centos-stream-10.md))
  targets CentOS Stream 10 with SELinux enforcing; the SELinux steps are
  skippable on other distributions. Python 3.14 arrives via
  [uv](https://docs.astral.sh/uv/) — no system Python is used.
- **Storage** — any NFSv4.2 server that can provide the two exports and the
  identity mapping in
  [`docs/storage-requirements.md`](docs/storage-requirements.md) (the
  reference deployment uses TrueNAS). The archive root **must** be an NFS
  mount; preflight refuses anything else by design.
- **Consumers** — any authorized host that can mount the read-only export; the
  copy helper needs only Python 3. The export has no per-repository ACLs, so all
  consumers must be permitted to read every configured restricted repository.
- **Reader first?** The [quickstart](docs/quickstart.md) connects to a provisioned
  authenticated API without a local archive mount. Disposable writer setup and
  real storage requirements remain separate operator work.

## Status

The REST/CLI and optional read-only MCP feature is implemented on the local
`feat/rest-api-and-mcp` branch. The [completed plan](docs/plans/2026-10-17-plan-rest-api-and-mcp.md)
records all 21 work packages and final integration acceptance. Source version
`0.1.10` is unchanged metadata, not a new release or tag. The deployment record below predates this API/MCP rollout;
[operator acceptance](docs/deployment-centos-stream-10.md#17-rest-and-mcp-rollout-checklist-api-017)
is still required. No production installation is claimed.

**Recorded deployment baseline: `0.1.10` — explicit quarantine cleanup release candidate.** The writer is complete
and running against a live NFS-backed ZFS archive: it syncs public, private, and
gated repositories, publishes, retains a bounded revision history, prunes,
verifies, repairs, recovers, and cleans proven redundant quarantine entries,
under systemd with SELinux
enforcing and validated hardening. Release history is in
[`CHANGELOG.md`](CHANGELOG.md); the annotated tags carry the complete notes.

What remains is operator work that this project cannot perform for itself — the
read-only consumer export, snapshots and replication, the disjointness proof from
a second client, reboot persistence, and enabling the quarterly verification
timer. All of it is listed, with copy-pasteable instructions and acceptance
checks, under **Operator handoff** in `docs/progress.md`.

[The current tracker](docs/plans/current.md) selects the active plan; dated
plans and individual task files own scope and execution status.
`docs/progress.md` retains completed work-package evidence, Decisions, Operator
handoff, and the unmigrated backlog. `docs/plan.md` remains the historical
implementation plan and contract reference.

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/architecture.md`](docs/architecture.md) | Architecture decisions, filesystem layout and invariants, transaction and crash-recovery boundaries |
| [`docs/invariants.md`](docs/invariants.md) | Current invariant register, governing contracts, and implementation evidence |
| [`docs/adr/`](docs/adr/README.md) | Individual architectural decision records, provenance, amendments, and maintenance rules |
| [`docs/configuration.md`](docs/configuration.md) | Every configuration key, its constraints, and credential handling |
| [`docs/server.md`](docs/server.md) | Server configuration, bearer credentials and the incremental HTTP deployment boundary |
| [`docs/api.md`](docs/api.md) | REST capability/operation matrix and implementation status |
| [`docs/api-client.md`](docs/api-client.md) | Independent reader/writer API setup, endpoint/credential precedence, TLS, finite observation and uncertainty |
| [`docs/schemas.md`](docs/schemas.md) | Durable JSON formats: manifests, references, catalog, reports, journals |
| [`docs/cli.md`](docs/cli.md) | Command surface, JSON output, exit codes, error taxonomy |
| [`docs/security.md`](docs/security.md) | Assets, trust boundaries, threats, and the control enforcing each |
| [`docs/quickstart.md`](docs/quickstart.md) | Use the authenticated API client, with separate writer setup and MCP guidance |
| [`docs/storage-requirements.md`](docs/storage-requirements.md) | What any NFSv4.2 server must provide: filesystem semantics, the two exports, identities |
| [`docs/deployment-centos-stream-10.md`](docs/deployment-centos-stream-10.md) | Building the writer host, installing, upgrading, and rolling back |
| [`docs/operations.md`](docs/operations.md) | Running it: sync, verify, prune, purge, status, timers, exit codes, measured performance |
| [`docs/recovery.md`](docs/recovery.md) | Corruption, repair, snapshot restore, lost writer, and the stopped-machine states |
| [`docs/consumers.md`](docs/consumers.md) | Copying and verifying a revision from a downstream host |
| [`docs/cockpit.md`](docs/cockpit.md) | The Cockpit plugin's contract: rules, privilege model, operation surface |
| [`docs/cockpit-plugin/`](docs/cockpit-plugin/) | Installing and using the Cockpit plugin |
| [`docs/plan.md`](docs/plan.md) | Original implementation plan and contract/history reference |
| [`docs/plans/current.md`](docs/plans/current.md) | Active-plan selector and next task |
| [`docs/plans/`](docs/plans/README.md) | Dated plans and individual work-package task records |
| [`docs/progress.md`](docs/progress.md) | Completed work-package audit, Decisions, operator handoff, and historical backlog |

[`docs/storage-requirements.md`](docs/storage-requirements.md) states what any
NFSv4.2 server must provide. `docs/truenas.md` — the reference deployment's
NAS-side runbook against those requirements — remains unwritten by design: it
belongs to whoever performs the NAS-side handoff items (`docs/progress.md`,
operator handoff item 11), because none of its content can be made or verified
from the writer.

Coding agents start at [`AGENTS.md`](AGENTS.md) — a context router into these
documents and the agent-specific set under [`docs/agents/`](docs/agents/).
`CLAUDE.md` is a symlink to it.

## Browser administration

An optional Cockpit plugin under [`cockpit/`](cockpit/) administers a
deployed writer from the browser: sync control with live activity, archive
browsing, configuration editing, schedule management, verification, run
reports, and maintenance. Every action is one of the runbook's own CLI
commands or systemd units — never a side channel — and the CLI remains the
plugin's current interface. The activated
[REST-first implementation plan](docs/plans/2026-10-17-plan-rest-api-and-mcp.md)
introduces authenticated remote management incrementally;
[the API contract](docs/api.md) marks metadata, operation observation and typed
sync/verification/planning/diagnostic/installed-validation, maintenance and
candidate routes as implemented; API-012 migrates reader commands. Every route, health/schema/docs
and error surface authenticates; discovery preserves exact publication identity and
`published/`-relative reference locators. Bulk copies still use the read-only
export and independent verification in [the consumer runbook](docs/consumers.md).
[`docs/cockpit-plugin/`](docs/cockpit-plugin/) covers installation and
usage; [`docs/cockpit.md`](docs/cockpit.md) is the contract it is written
against.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/hfcache/` | Domain services and CLI; base HTTP client with optional FastAPI/Uvicorn server dependencies |
| `cockpit/` | The Cockpit administration plugin: a browser UI over the CLI and the systemd units |
| `docs/` | The contracts and runbooks in the table above |
| `docs/agents/` | Agent-facing planning, workflow, conventions, environment, and release docs |
| `docs/plans/` | Current-plan selector, dated plans, and individual task records |
| `packaging/` | systemd units and timers, journald and tmpfiles drop-ins |
| `scripts/` | `check.sh` (the quality gate), `install-release.sh`, and the hardening probe pair |
| `examples/` | A runnable `config.toml`, and `copy-revision.py` — the consumer-side helper |
| `tests/` | `unit/` (default, offline), `system/` (opt-in markers), `fixtures/` (golden schemas) |

## Development

Requires [uv](https://docs.astral.sh/uv/) and CPython 3.14.

```bash
git clone https://github.com/wtcross/hfcache.git
cd hfcache
uv sync --locked --extra server --extra mcp  # all implemented development extras
uv run --locked --extra server --extra mcp hfcache --help
```

The base installation includes the HTTP client and keeps CLI imports independent
of optional server packages. A writer's server environment requires the `server`
extra; provision it from this checkout's lock for development:

```bash
uv sync --locked --extra server
```

API-005 adds strict server configuration and bearer-capability primitives;
`packaging/server.toml` is the separate server configuration example, documented
in [`docs/server.md`](docs/server.md). API-006 implements authenticated metadata
routes and the explicit foreground `hfcache serve --server-config PATH` bootstrap.
Runtime directories and protected API credentials must already be provisioned;
installing the extra starts no listener and changes no deployed writer.
API-007 adds bounded local receipt/idempotency primitives and authenticated
operation observation. Control-state history survives client loss and is never
automatically replayed; interrupted history is retained. Reader CLI integration
is API-012, operational CLI/observation API-013, and systemd packaging API-014.
API-008 supplies one bounded execution lane and private verifier protocol/process
primitives. API-014 packages activation/no-IP policy; installed OS enforcement
remains operator acceptance. The library offline flag alone is insufficient.
REST acceptance is committed. MCP-001 adds standalone FastMCP only through the
optional `mcp` extra, alongside `server`; disabled installs need no MCP package
or credential. MCP-002 exposes nine curated metadata tools through a narrow read
protocol, with typed bounded pages and no jobs/Hub/probes or arbitrary file reads.
The [protected-file example client](examples/mcp-client.py),
[setup/session/rotation guide](docs/mcp.md#protected-file-example-client-mcp-004)
and [cost/error limits](docs/mcp.md#resource-costs-and-troubleshooting) describe
controlled internal metadata access. The MCP reader can see the whole archive,
including restricted metadata; it cannot use REST or create jobs. No OAuth
provisioning, browser bearer, file transfer or local archive fallback is supplied.
Disposable-socket TLS tests use the OpenSSL CLI as a development test tool; Python
production dependencies remain locked. All-extra development commands do not
change production profile selection or close installed-host acceptance holds.
API-009 exposes keyed command admission with HTTP 202 and authenticated status,
events and exact terminal results. Sync/actual verification require a writer;
installed planning and explicitly read-only diagnostics permit readers but may
contact the Hub. `serve --hub-token-file PATH` is a trusted startup development
source, separate from API bearers; requests cannot choose credentials or paths.
API-010 adds separate maintenance preview/apply URLs, exact-manifest repair and
explicit configured-target initialization. Every job is keyed; previews grant no
apply authority. Initialization alone requires the disabled-by-default maintenance
switch, writer confirmation and restated root/UUID, never automatic startup/recovery.
The existing production archive must not be initialized again. API-012 exposes
candidate validation/planning with installed authority and credentials.

API-011 adds the independent synchronous base client and separate strict reader
settings, with verified TLS/Unix transport, explicit API credentials, bounded
pages/polling and retained-key uncertainty. Reader hosts need no archive TOML,
mount, service UID, Hub credential or server extra. See
[`docs/api-client.md`](docs/api-client.md) and
[`packaging/client.example.toml`](packaging/client.example.toml). The four new
CLI endpoint/source options drive API-012/013 operational modes. No automatic daemon start, archive fallback or
POST replay is added.

API-012 routes status/list/inspection/estimate, installed/candidate validation,
planning and read-only diagnostics through the API, preserving exact server
Envelopes and complete finite inventory pages. `version --server` inspects the
writer; help/local version and `config validate --local` remain independent
bootstrap paths. `--config` means bounded local candidate content only for API
validate/plan; other migrated reads reject it and legacy Hub-token overrides.
Valid candidate syntax is separate from installed-authority compatibility, and
planning never redirects installed credentials. Configuration installation/backups
remain privileged host work; no reader fallback accesses a local archive.
The Unix client adapter closes failed connections through public HTTPX/HTTPCore
interfaces. HTTPCore becomes direct at its already-locked 1.0.9 version; no package
or version upgrade is added.

API-013 removes the CLI's direct operational backend. Jobs wait for exact server
results by default; explicit `--detach` identifies admission separately. Validated
submission keys and accepted operation IDs are printed even in quiet mode, with
bounded sanitized progress on stderr. `operations show`, `lookup` and `wait`
resume observation without submission; Ctrl-C/timeouts preserve handles and do
not cancel accepted work. Use [the client runbook](docs/api-client.md#submit-detach-and-resume-api-013)
for finite wait, same-key retry and uncertainty. Initialization keeps explicit
root/confirmation and the server's disabled gate; no-confirm inspection never
submits. API-014 packages systemd integration and API-015 integrates Cockpit's
API-only client; installed OS isolation proof remains operator work. This branch has
not been deployed.

API-014 packages activated API/private-verifier services and API-only scheduled
clients. One API socket feeds one application across Unix/optional loopback TCP.
The actual verifier carries offline/no-IP/credential-source policy; no-IP on a
client wrapper alone is insufficient. Private strict scheduled handles persist a
key before one POST and retain lookup-only recovery through finite observation
windows, preserving long-running oneshot behavior without replay. Unit names,
calendars, disabled verify timer and shared runtime locks remain. Installer dry-run
and disposable stage/drain/rollback tests do not establish installed cgroup,
credential, SELinux or NFS acceptance; those remain explicit deployment holds.
No production service or archive operation is performed by this implementation.

API-015 keeps Cockpit on the installed CLI/systemd boundary with API-only named
credentials, strict bounded terminal/progress parsing and validated reconnect
handles. Closing a page or stopping a client does not cancel accepted work.
Configuration changes bind exact candidate/base content under a root flock and
require compatible server assessment, required preview and exact installed
fingerprint confirmation; incompatible/unknown authority needs manual operator
installation. Full sync/verify units, sync-timer-only controls and no init UI
remain. Browser credentials, direct REST installs and MCP are not added.

API-016 reconciles all 29 REST modes with concrete CLI/API evidence and fresh
security, example, transport and build acceptance before MCP. Native Unix clients
can use fixed unprefixed paths alongside a public TCP prefix; both interfaces keep
authentication/security, and request-specific links/schema views cannot mutate
shared routing state. Installed-host checks remain separate deployment holds.

The quality gate is one script — lock check, formatting, lint, types, the
default test suite, a build and locked base/server wheel-install smoke checks —
and it is exactly what must pass from a
clean checkout:

```bash
scripts/check.sh                 # the docs/plan.md §8.4 gate
scripts/check.sh --with-build    # plus a wheel install smoke test
```

Three opt-in suites are deselected by default:

```bash
uv run --locked --extra server --extra mcp pytest -m live  # explicitly opted-in Hub tests
uv run --locked --extra server --extra mcp pytest -m nfs   # explicitly authorized real-NFS tests
uv run --locked --extra server --extra mcp pytest -m build # throwaway wheel smoke
```

## License

MIT ([`LICENSE`](LICENSE)), with one subtree different:
[`cockpit/`](cockpit/) is LGPL-2.1-or-later — it derives from the Cockpit
starter kit — declared per file in SPDX headers (decision 90 in
`docs/progress.md`).
