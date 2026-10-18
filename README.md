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
- **No NAS yet?** [`docs/quickstart.md`](docs/quickstart.md) runs everything
  on one machine with a loopback NFS export.

## Status

**`v0.1.10` — explicit quarantine cleanup release candidate.** The writer is complete
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
| [`docs/schemas.md`](docs/schemas.md) | Durable JSON formats: manifests, references, catalog, reports, journals |
| [`docs/cli.md`](docs/cli.md) | Command surface, JSON output, exit codes, error taxonomy |
| [`docs/security.md`](docs/security.md) | Assets, trust boundaries, threats, and the control enforcing each |
| [`docs/quickstart.md`](docs/quickstart.md) | Run everything on one machine with a loopback NFS export |
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
[the API contract](docs/api.md) now marks metadata reads as implemented and
job/write routes as planned. Every metadata route, health/schema/docs and error
surface authenticates; discovery preserves exact publication identity and
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
uv sync                      # create the locked development environment
uv run hfcache --help
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
automatically replayed; interrupted history is retained. Job/write submission
routes, heavy execution, API-backed CLI migration, systemd packaging and the isolated
verification executor remain later tasks. MCP stays behind the REST acceptance
gate and adds no dependency yet. Disposable-socket TLS tests use the OpenSSL CLI
as a development test tool; Python production dependencies remain locked.

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
uv run pytest -m live     # contacts the Hugging Face Hub
uv run pytest -m nfs      # requires the live NFS archive mount on the writer
uv run pytest -m build    # builds artifacts and installs into a throwaway venv
```

## License

MIT ([`LICENSE`](LICENSE)), with one subtree different:
[`cockpit/`](cockpit/) is LGPL-2.1-or-later — it derives from the Cockpit
starter kit — declared per file in SPDX headers (decision 90 in
`docs/progress.md`).
