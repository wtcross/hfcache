Historical onboarding reference before DOC-017; source identity and hash are in the sibling manifest.

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
  ([`docs/deployment-centos-stream-10.md`](../../../deployment-centos-stream-10.md))
  targets CentOS Stream 10 with SELinux enforcing; the SELinux steps are
  skippable on other distributions. The historical native application uses
  Python 3.14 managed by [uv](https://docs.astral.sh/uv/). In the selected
  [rootless profile](../../../containers.md), application Python 3.14.6 lives in the
  pinned image; reviewed host Python standard-library orchestrators manage
  containers without importing the application (also checked on host Python 3.12).
- **Storage** — any NFSv4.2 server that can provide the two exports and the
  identity mapping in
  [`docs/storage-requirements.md`](../../../storage-requirements.md) (the
  reference deployment uses TrueNAS). The archive root **must** be an NFS
  mount; preflight refuses anything else by design.
- **Consumers** — any authorized host that can mount the read-only export; the
  copy helper needs only Python 3. The export has no per-repository ACLs, so all
  consumers must be permitted to read every configured restricted repository.
- **Reader first?** The [quickstart](../../../quickstart.md) connects to a provisioned
  authenticated API without a local archive mount. Disposable writer setup and
  real storage requirements remain separate operator work.

## Status

**`0.2.1` is deployed locally with annotated tag `v0.2.1`.** All service
images now use pinned UBI 10 micro. The confined worker creates its own private
listener and sends actual readiness before API startup. The installed API
container's private probe passes under SELinux Enforcing, including after clean
drain/restart, closing the former worker-connectivity hold. Verified local TLS,
REST/authentication, the exact nine MCP tools and the fixed container client pass.
Native FD3 activation and existing hardening remain unchanged.

[REL-013](../../plans/tasks/rel-013-container-worker-artifacts.md) records exact clean
artifacts from immutable source `4088994`; [OPS-018](../../plans/tasks/ops-018-container-worker-rollout.md)
records the guarded deployment and actual installed acceptance.
[REL-014](../../plans/tasks/rel-014-container-worker-release.md) records the passing
final gate/local tag at deployment commit `156506f`; application source remains
`4088994`. Disposable complete
verification-mode tests use simulated NFS and do not establish live NAS readiness.
The NAS stays read-only, legacy writers remain masked and verification scheduling
stays disabled. No NAS file I/O/jobs or other-host/remote action is authorized.
See the [container contract](../../../containers.md),
[operator checklist](../../../deployment-centos-stream-10.md#acceptance-checklist)
and [current plan](../../plans/2026-10-18-plan-container-worker-listener.md).

The local annotated `v0.2.0` tag and its partial-acceptance history remain intact.
That deployment used application source `481fcc4` and evidence commit `11ddd55`;
its API-to-worker SELinux failure returns on rollback unless deliberately corrected.
The [completed feature plan](../../plans/2026-10-17-plan-rest-api-and-mcp.md) records
the breaking API-only operational CLI/optional read-only MCP boundary. No tag or
branch has been published remotely.

**Recorded deployment baseline: `0.1.10` — explicit quarantine cleanup release candidate.** This historical deployment demonstrated
operation against a live NFS-backed ZFS archive: syncing public, private, and
gated repositories, publishing, bounded revision retention, pruning,
verification, repair, recovery, and proven redundant quarantine cleanup,
under systemd with SELinux
enforcing and validated hardening. Release history is in
[`CHANGELOG.md`](../../../../CHANGELOG.md); the annotated tags carry the complete notes.

What remains is operator work that this project cannot perform for itself — the
read-only consumer export, snapshots and replication, the disjointness proof from
a second client, reboot persistence, and enabling the quarterly verification
timer. All of it is listed, with copy-pasteable instructions and acceptance
checks, under **Operator handoff** in `docs/agents/progress.md`.

[The current tracker](../../plans/current.md) records no active plan after the completed listener correction;
dated
plans and individual task files own scope and execution status.
`docs/agents/progress.md` retains completed work-package evidence, Decisions, Operator
handoff, and the unmigrated backlog. `docs/agents/history/plan.md` remains the historical
implementation plan and contract reference.

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/architecture.md`](../../../architecture.md) | Architecture decisions, filesystem layout and invariants, transaction and crash-recovery boundaries |
| [`docs/invariants.md`](../../../invariants.md) | Current invariant register, governing contracts, and implementation evidence |
| [`docs/adr/`](../../../adr/README.md) | Individual architectural decision records, provenance, amendments, and maintenance rules |
| [`docs/configuration.md`](../../../configuration.md) | Every configuration key, its constraints, and credential handling |
| [`docs/server.md`](../../../server.md) | Server configuration, bearer credentials and the incremental HTTP deployment boundary |
| [`docs/containers.md`](../../../containers.md) | Selected rootless Caddy/API/worker/client lifecycle, protected runtime profile and no-NAS-write limits |
| [`docs/api.md`](../../../api.md) | REST capability/operation matrix and implementation status |
| [`docs/api-client.md`](../../../api-client.md) | Independent reader/writer API setup, endpoint/credential precedence, TLS, finite observation and uncertainty |
| [`docs/schemas.md`](../../../schemas.md) | Durable JSON formats: manifests, references, catalog, reports, journals |
| [`docs/cli.md`](../../../cli.md) | Command surface, JSON output, exit codes, error taxonomy |
| [`docs/security.md`](../../../security.md) | Assets, trust boundaries, threats, and the control enforcing each |
| [`docs/quickstart.md`](../../../quickstart.md) | Use the authenticated API client, with separate writer setup and MCP guidance |
| [`docs/storage-requirements.md`](../../../storage-requirements.md) | What any NFSv4.2 server must provide: filesystem semantics, the two exports, identities |
| [`docs/deployment-centos-stream-10.md`](../../../deployment-centos-stream-10.md) | Building the writer host, installing, upgrading, and rolling back |
| [`docs/operations.md`](../../../operations.md) | Running it: sync, verify, prune, purge, status, timers, exit codes, measured performance |
| [`docs/recovery.md`](../../../recovery.md) | Corruption, repair, snapshot restore, lost writer, and the stopped-machine states |
| [`docs/consumers.md`](../../../consumers.md) | Copying and verifying a revision from a downstream host |
| [`docs/cockpit.md`](../../../cockpit.md) | The Cockpit plugin's contract: rules, privilege model, operation surface |
| [`docs/cockpit-plugin/`](../../../cockpit-plugin) | Installing and using the Cockpit plugin |
| [`docs/agents/history/plan.md`](../plan.md) | Original implementation plan and contract/history reference |
| [`docs/agents/plans/current.md`](../../plans/current.md) | Active-plan selector and next task |
| [`docs/agents/plans/`](../../plans/README.md) | Dated plans and individual work-package task records |
| [`docs/agents/progress.md`](../../progress.md) | Completed work-package audit, Decisions, operator handoff, and historical backlog |

[`docs/storage-requirements.md`](../../../storage-requirements.md) states what any
NFSv4.2 server must provide. `docs/truenas.md` — the reference deployment's
NAS-side runbook against those requirements — remains unwritten by design: it
belongs to whoever performs the NAS-side handoff items (`docs/agents/progress.md`,
operator handoff item 11), because none of its content can be made or verified
from the writer.

Coding agents start at [`AGENTS.md`](../../../../AGENTS.md) — a context router into these
documents and the agent-specific set under [`docs/agents/`](../..).
`CLAUDE.md` is a symlink to it.

## Browser administration

An optional Cockpit plugin under [`cockpit/`](../../../../cockpit) administers a
deployed writer from the browser: sync control with live activity, archive
browsing, configuration editing, schedule management, verification, run
reports, and maintenance. Every action is one of the runbook's own CLI
commands or systemd units — never a side channel — and the CLI remains the
plugin's current interface. The activated
[REST-first implementation plan](../../plans/2026-10-17-plan-rest-api-and-mcp.md)
introduces authenticated remote management incrementally;
[the API contract](../../../api.md) marks metadata, operation observation and typed
sync/verification/planning/diagnostic/installed-validation, maintenance and
candidate routes as implemented; API-012 migrates reader commands. Every route, health/schema/docs
and error surface authenticates; discovery preserves exact publication identity and
`published/`-relative reference locators. Bulk copies still use the read-only
export and independent verification in [the consumer runbook](../../../consumers.md).
[`docs/cockpit-plugin/`](../../../cockpit-plugin) covers installation and
usage; [`docs/cockpit.md`](../../../cockpit.md) is the contract it is written
against.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/hfcache/` | Domain services and CLI; base HTTP client with optional FastAPI/Uvicorn server dependencies |
| `cockpit/` | The Cockpit administration plugin: a browser UI over the CLI and the systemd units |
| `docs/` | The contracts and runbooks in the table above |
| `docs/agents/` | Agent-facing planning, workflow, conventions, environment, and release docs |
| `docs/agents/plans/` | Current-plan selector, dated plans, and individual task records |
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
in [`docs/server.md`](../../../server.md). API-006 implements authenticated metadata
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
The [protected-file example client](../../../../examples/mcp-client.py),
[setup/session/rotation guide](../../../mcp.md#connect)
and [cost/error limits](../../../mcp.md#resource-costs-and-troubleshooting) describe
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
[`docs/api-client.md`](../../../api-client.md) and
[`packaging/client.example.toml`](../../../../packaging/client.example.toml). The four new
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
not cancel accepted work. Use [the client runbook](../../../api-client.md#submit-detach-and-resume)
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
scripts/check.sh                 # the docs/agents/history/plan.md §8.4 gate
scripts/check.sh --with-build    # plus a wheel install smoke test
```

Three opt-in suites are deselected by default:

```bash
uv run --locked --extra server --extra mcp pytest -m live  # explicitly opted-in Hub tests
uv run --locked --extra server --extra mcp pytest -m nfs   # explicitly authorized real-NFS tests
uv run --locked --extra server --extra mcp pytest -m build # throwaway wheel smoke
```

## License

MIT ([`LICENSE`](../../../../LICENSE)), with one subtree different:
[`cockpit/`](../../../../cockpit) is LGPL-2.1-or-later — it derives from the Cockpit
starter kit — declared per file in SPDX headers (decision 90 in
`docs/agents/progress.md`).
