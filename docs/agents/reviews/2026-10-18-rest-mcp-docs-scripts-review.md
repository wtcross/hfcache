# REST/MCP documentation and script review

| Field | Value |
| --- | --- |
| Review date | 2026-10-18 |
| Repository | `wtcross/hfcache` |
| Branch | `feat/rest-api-and-mcp` |
| Pinned commit | `65b65714b29e835498138ec3122b5669571850cf` |
| Commit timestamp | 2026-10-18 19:22:21 UTC |
| Commit subject | `REL-014: record the deployed local 0.2.1 tag and close the plan` |
| Project version | `0.2.1` |
| Method | Static review of live GitHub files at the pinned commit; source/contract/template cross-checking |
| Limits | No application gate, production inspection, container execution, live Hub or NAS test performed |
| Related plan | [Correction plan](../plans/2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |

## Executive assessment

The feature branch has implemented the API-backed CLI and curated MCP interface,
and has subsequently introduced a guarded rootless deployment. Documentation often
retains each stage of that evolution as a new amendment while leaving the old
paragraphs and command blocks in place. The result is not merely excess prose:
readers can choose the wrong installer, interpreter, service manager, credential
source or listener model unless they reconcile later caveats themselves.

The user's additional requirement changes the documentation acceptance criterion:
all human-facing material must explain the product rather than how agents executed
its implementation. Planning/audit/process material must be preserved under
`docs/agents/`, not embedded in MCP/API/operator guides. A migration needs to
preserve normative requirements, task identities and completed evidence.

There are also concrete script/CLI problems worth correcting before rewriting the
related docs: invasive probes with inadequate ordering and broad denial-success
classification; quiet diagnostic suppression; inert color state; and likely unused
CLI migration helpers. Some older-looking artifacts are intentionally supported
or safety-critical and must not be deleted on appearance alone.

## Baseline and authority

The project metadata declares base HTTP client dependencies, optional FastAPI /
Uvicorn server dependencies, optional FastMCP and Python >=3.14. The public CLI
operational handlers use the typed API client. The MCP adapter registers nine
named tools against a narrow read port. The current selector says no plan is active.

Sources: [pyproject.toml](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/pyproject.toml), [src/hfcache/cli.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli.py),
[src/hfcache/cli_client.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli_client.py), [src/hfcache/mcp_tools.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/mcp_tools.py),
[docs/plans/current.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/plans/current.md).

The repository records a local 0.2.1 deployment with API-to-worker connectivity
acceptance, while retaining a read-only NAS mount, writer masks and separate
unperformed live-storage checks. These are repository-reported facts, not new
observations of the installation. New source work must not inherit the historic
rollout's permission to manipulate that host.

Sources: [README.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/README.md), [docs/containers.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/containers.md),
[docs/agents/environment.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/agents/environment.md).

## Findings

### F01 — Human guides act as implementation ledgers

**Type:** confirmed editorial/authority mismatch with the user's requirement.
**Scope:** human documentation broadly, not only the example paragraph.

The MCP introduction narrates packages, decisions, task-owned evidence and final
closure. The CLI introduction preserves multiple migration-stage amendments,
including earlier claims that operations remain local and MCP has no tools. The
README, server and operations guides likewise route readers through implementation
history. Later corrections do not make the earlier directions a useful current
reference.

**Correction:** rewrite each guide in current product terms; remove package IDs,
plan/task/progress links, execution ownership and phase chronology from all human
surfaces. Preserve the complete history internally under agents. Keep technical
ADR rationale, invariant/error identifiers and product planning commands where
useful. Add a gate with explicit positive tests for those legitimate concepts.

Sources: [docs/mcp.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/mcp.md) introduction; [docs/cli.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/cli.md) introduction;
[README.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/README.md) Status/Development; [docs/server.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/server.md) introduction;
[docs/operations.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/operations.md) opening sections. Owners: DOC-011–019 as scoped.

### F02 — Current-state claims are scattered and mutually confusing

**Type:** confirmed documentation drift.

The current selector reports a completed listener correction and no active plan.
The server opening still points to an “active plan”; the MCP introduction frames
final closure as a separate future concern. README and the environment/release
guides carry multiple baseline and later rollout statements. README also retains
a statement that no branch has been published remotely, inappropriate as an
unqualified current claim inside this remotely readable feature branch.

**Correction:** product guides describe capabilities, not execution state. Put
dated, scoped installation validation/restrictions in a small human status page.
Distinguish recorded evidence from freshly inspected facts. Preserve meaningful
rollback caveats, including the prior listener problem, without requiring task links.

Sources: [docs/plans/current.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/plans/current.md), [docs/server.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/server.md),
[docs/mcp.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/mcp.md), [README.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/README.md), [docs/agents/release.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/agents/release.md).
Owners: DOC-011, DOC-014–017.

### F03 — Native instructions lead despite a selected rootless profile

**Type:** confirmed guidance mismatch; profile-aware refusal is a recommended hardening.

The environment guide leads with `install-release.sh`, a host release `.venv`
command and native scheduling facts, only qualifying them later. The native
hardening wrapper invokes `/opt/hfcache/current/.venv/bin/python` and reads
system-manager unit content. The selected rootless path uses the fixed client
wrapper, a separate container installer, rootless user units and container-local
Python. The existing native quiescence checks can refuse a masked/active state;
this review does **not** claim they were bypassed or a live cross-profile switch
was reproduced.

**Correction:** make profiles explicit before command examples; lead agent guidance
with current restrictions. Add early, positive current/target profile validation
to native mutation/probe entrypoints, yielding a useful refusal before staging or
execution. Retain genuine native support; never silently reroute a command to
another manager or installer.

Sources: [docs/agents/environment.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/agents/environment.md), [docs/agents/release.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/agents/release.md),
[scripts/check-hardening.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check-hardening.sh), [scripts/install-release.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/install-release.sh),
[scripts/release-functions.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/release-functions.sh), [scripts/container-service.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/container-service.py),
[scripts/hfcache-client](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/hfcache-client). Owners: OPS-021, DOC-014–017.

### F04 — Container build and listener descriptions retain obsolete designs

**Type:** confirmed documentation/template mismatch.

The beginning of `docs/containers.md` describes a pinned slim-trixie Python image,
while the current Containerfile builds/runs on pinned UBI 10 micro with a separate
portable Python input and selected binary/CA donors. The early lifecycle summary
also says the user target starts a private-worker socket, while the later correction
explains worker service readiness and a deliberately dormant socket artifact.

**Correction:** describe one current rootless topology in the primary sections.
Explain UBI provenance and worker-created socket/readiness directly. Preserve
native FD3 activation and the dormant artifact's compatibility purpose in clearly
labeled technical sections. Move the implementation chronology away.

Sources: [docs/containers.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/containers.md) Roles and lifecycle / Build and image identity /
listener-correction sections; [packaging/containers/Containerfile](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/packaging/containers/Containerfile);
[packaging/containers/server.toml.in](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/packaging/containers/server.toml.in); [scripts/container-service.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/container-service.py).
Owners: OPS-021, DOC-015, DOC-017.

### F05 — Hardening workloads run before sufficient target proof

**Type:** confirmed source-level safety concern; not exercised against a host.

The hardening wrapper defaults its archive to `/srv/hfcache`. Its payload uses
decorators that execute checks when the module is loaded. `_writable_paths` writes
a scratch file directly under `ARCHIVE`; other probes create/rename/link objects
in the health area. `_nfs_identity` runs near the end, after those writes, and its
sentinel/directory read is not a complete mount/expected-UUID proof. Another denial
probe tries to write a real kernel tunable, which could change the host if the
protection under test is absent. Read-only rollout restrictions are documentary
preconditions rather than safe defaults of these workload entrypoints.

**Correction:** pure/import-safe functions, explicit modes/profile/target, no live
archive default for writes, fail-closed target preflight before mutation, no scratch
files in the archive root, safe owned cleanup and no real host-setting mutation as
a denial test. Split harmless inspection from separately authorized disposable
workloads. The selected restricted live deployment cannot run those workloads.

Sources: [scripts/check-hardening.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check-hardening.sh);
[scripts/hardening-probe.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/hardening-probe.py) `check`, `_writable_paths`, `_kernel_tunables`,
`_nfs`, `_setgid_directory`, `_hardlink`, `_nfs_identity`;
[docs/agents/environment.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/agents/environment.md). Owner: OPS-020.

### F06 — A failed prerequisite can be reported as successful isolation

**Type:** confirmed control-flow defect in evidence classification.

The probe's `denied` decorator marks every exception as a successful refusal.
An import error in a Hub/network check, DNS outage or unrelated exception can
therefore be labeled successful isolation. `_read_only_system` accepts any OSError,
which does not distinguish a read-only mount from ordinary permissions. The
seccomp check establishes that a filter exists, not that every intended rule is
active. Those checks can be useful observations, but their names/messages must
not overstate what they establish.

**Correction:** test prerequisites independently, classify expected denials per
check, report unexpected failure as failed/not-proven and distinguish action
refusal from proof of its enforcing control. Sanitize exceptions. Keep controlled
positive/negative fixtures, actual PID1/cgroup evidence and installed API-peer
acceptance distinct; do not substitute host-origin probes.

Sources: [scripts/hardening-probe.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/hardening-probe.py) `denied`, `_read_only_system`,
`_seccomp`, `_hub_api`, `_download`; [docs/containers.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/containers.md) probe/evidence
limitations. Owner: OPS-020.

### F07 — Public CLI help uses pre-HTTP local-process semantics

**Type:** confirmed help/dispatch mismatch.

`config_validate` says it touches nothing and makes no network request, although
its default branch connects to the API; `--local` is the actual exception.
`version` describes a configuration-independent local operation even though it
now has `--server`. Other command help describes work executed by server/worker
as though the CLI process does it. The command mutation table also needs an
explicit distinction between archive effects and local control receipts: several
read/preview operations are submitted as keyed jobs.

**Correction:** describe where work occurs and which side effects exist. Preserve
local help/version/explicit bootstrap behavior, keep operational `--config` and
Hub-token restrictions, and explain actual verification versus metadata/report
reading. This is not a reason to weaken authentication or add a local fallback.

Sources: [src/hfcache/cli.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli.py) `config_validate`, `version`, `plan`, `sync`,
`verify`, maintenance handlers; [docs/cli.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/cli.md);
[docs/operations.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/operations.md). Owners: API-018, DOC-012–017.

### F08 — CLI migration remnants are candidates for removal

**Type:** one apparent uncalled local helper plus candidates needing branch-wide proof.

The reviewed CLI defines `_emit` while its migrated handlers use `_show_result`;
no caller appears in the inspected CLI. `cli_client.run_job` appears to duplicate
the newer submit/observe path used by handlers. `_show_result` retains a
`ServiceResult` input route from the extraction period, while inspected public
callers supply Envelopes. `UNPROVABLE_READ_ONLY` is still re-exported from the CLI
without being used by its current command bodies.

**Correction:** search the entire branch, tests, examples, dynamic registration,
packaging and supported external interface before deletion. Remove proven-unused
helpers/re-exports/branches, and replace tests of migration seams with public
behavior tests. Retain `ServiceResult` itself, bootstrap envelope generation and
all real domain services. This static review did not establish absence of every
possible external import; these are not blanket deletions.

Sources: [src/hfcache/cli.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli.py) `_emit`, `_show_result`, imports/`__all__`;
[src/hfcache/cli_client.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli_client.py) `run_job` and submission helpers.
Owner: API-018. See the separate disposition inventory.

### F09 — Quiet, color and progress promises do not consistently match rendering

**Type:** confirmed source/control-flow mismatch; behavioral regression tests required.

`GlobalOptions.color` is set from `--no-color` and TTY state but is not consumed by
the reviewed output renderers. `_progress` suppresses events only for quiet mode,
while the CLI guide claims automatic non-TTY suppression. `_show_result` can
suppress errors for a partial failed result in quiet human mode and does not
consistently print warnings.

A direct logical counterexample for the error condition is `quiet=True`, nonempty
rows, errors and data: `refusal` is false, so the condition that prints errors is
false. This is control-flow analysis, not a claimed live test execution. JSON
Envelopes and nonzero exits still carry failure; the issue is human diagnostic
visibility and option-contract accuracy.

**Correction:** implement meaningful color control without breaking the public
flag; keep warnings/errors and safety handles on stderr even when quiet; make
progress policy match the human contract; explain that client verbosity does not
change a running daemon's log level. Test all combinations and partial outcomes.

Sources: [src/hfcache/cli.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli.py) `GlobalOptions`, `main`, `_progress`,
`_show_result`; [docs/cli.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/cli.md) global options and progress contract.
Owner: API-018.

### F10 — Credential setup needs profile-specific presentation

**Type:** confirmed usability/profile ambiguity, not a discovered authentication bypass.

The MCP guide presents native `--with-mcp` staging and `LoadCredentialEncrypted`
examples early. The selected rootless template enables MCP and points at distinct
`/run/secrets/` files, delivered by the fixed Podman role helper. Native settings,
rendered server configuration and remote reader settings must not be treated as
one file or credential source. The code deliberately separates REST writer,
REST reader, MCP reader and Hub authority.

**Correction:** explain each deployment profile and credential source explicitly;
keep optional package behavior separate from the selected fixed container profile.
Describe restart-only rotation, protected source rules, no OAuth provisioning and
whole-archive authorization in human terms. Do not reuse one bearer across classes
or add an undocumented environment-token shortcut.

Sources: [docs/mcp.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/mcp.md) enablement and rotation;
[packaging/containers/server.toml.in](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/packaging/containers/server.toml.in);
[scripts/container-service.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/container-service.py) `secret` and role mounts;
[docs/server.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/server.md). Owners: OPS-021, DOC-012, DOC-013, DOC-015–017.

### F11 — The local CLI is not exempt from HTTP result ceilings

**Type:** confirmed documentation/code mismatch.

The server guide retains a statement that local CLI queries have complete results
without HTTP ceilings. The public operational CLI now uses HTTP; `_collect` and
`_inventory` aggregate paginated results under the client response budget and can
raise `ClientProtocolError`. A page count/size does not make the underlying scan
unbounded, nor does it promise success for an arbitrarily large archive.

**Correction:** document bounded complete collection or explicit failure, including
identity changes, page/byte/scan limits and how to investigate failure. Do not
return silent partial data, raise confidence on budget exhaustion or add a direct
filesystem fallback to fulfill an obsolete promise.

Sources: [docs/server.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/server.md) Resource settings;
[src/hfcache/cli_client.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli_client.py) `_collect`, `_inventory`;
[src/hfcache/cli.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/cli.py) `status`, `list_repositories`.
Owners: API-018, DOC-012, DOC-014, DOC-017.

### F12 — Cockpit and consumer tools are not interchangeable API readers

**Type:** intentional boundaries that need clearer human presentation.

Cockpit's `archive.ts` still lists/reads run reports using service-identity
`runuser` with `ls`/`cat` on `/srv/hfcache/runs`; it calls this the documented
host-local exception. Its journal reader is likewise host-side. The rootless
profile preserves fixed CLI launch and blocks legacy manager controls; it does
not make every existing Cockpit action a remote REST client. Separately, NFS
copy/verification and serving promotion remain a consumer data path, not obsolete
code displaced by MCP metadata.

**Correction:** document the supported/blocked/host-local operation matrix. Do not
remove report browsing, journal access or consumer helpers as dead, and do not
claim the browser plugin runs on a mountless remote reader. A future migration of
the report browser requires a scoped replacement, not an accidental deletion.

Sources: [cockpit/src/api/archive.ts](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/cockpit/src/api/archive.ts);
[cockpit/src/api/journal.ts](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/cockpit/src/api/journal.ts); [docs/containers.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/containers.md);
[README.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/README.md) browser/consumer descriptions.
Owners: DOC-014, DOC-015, DOC-017.

### F13 — Script discoverability and deletion classification are incomplete

**Type:** confirmed README inventory drift; branch-wide dead-file proof not established.

The README describes scripts mainly as a gate, native installer and probe pair,
although the directory now contains 17 helpers covering container provenance,
rootless lifecycle/install/probes, fixed client/guard and independent consumers.
The tiny client wrapper and the dormant socket can look unnecessary but are
referenced by runtime and release-binding contracts. The old credential example
is now a migration/reset example, not a normal secret-provisioning recipe.

**Correction:** maintain a complete, checked human inventory with profile and
side-effect labels. Retain supported native helpers and safety artifacts. Remove
obsolete prose and confirmed dead symbols, not whole files merely because they
are old, short or inactive in this deployment. Rehome or delete an obsolete
migration-only example only after verifying install/docs/rollback references and
providing its replacement instructions.

Sources: [README.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/README.md) Repository layout; scripts tree at the pinned commit;
[scripts/hfcache-client](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/hfcache-client); [docs/containers.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/containers.md) binding contract;
[packaging/systemd/hfcache-sync.service.d/credential.conf.example](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/packaging/systemd/hfcache-sync.service.d/credential.conf.example).
Owners: OPS-021, DOC-015, DOC-017, DOC-018.

### F14 — Audience and technical alignment need a durable executable check

**Type:** required validation improvement; existing contract tests are not dismissed.

The repository already has tests that parse documentation and a substantial
provider-neutral gate. The user's new human-only documentation policy requires
an explicit checker and regression fixtures; a prose-only instruction will not
prevent another layer of staged amendments from accumulating. Historical plan
relocation can also lose normative coverage unless links and requirement mappings
are checked, not merely renamed.

**Correction:** integrate audience/link/inventory checks plus route/tool/config
fixtures and safe command parsing. Use the actual app and mounted MCP registry,
not just a hardcoded list copied into another file. Add deliberate-bad fixtures
and allow legitimate product planning/error/invariant terminology. Never execute
arbitrary markdown commands or claim opt-in host tests ran in the offline gate.

Sources: [scripts/check.sh](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/scripts/check.sh); [AGENTS.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/AGENTS.md) documentation-parsing
warning; [docs/agents/planning.md](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/docs/agents/planning.md);
[src/hfcache/api/app.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/api/app.py) registered resources;
[src/hfcache/mcp_tools.py](https://github.com/wtcross/hfcache/blob/65b65714b29e835498138ec3122b5669571850cf/src/hfcache/mcp_tools.py) registered tool boundary.
Owners: DOC-011, DOC-016, DOC-018, DOC-019.

## Removal and preservation policy

Remove obsolete **current-use guidance** after its valid technical content has a
current home. Preserve implementation history with a deliberate move under agents.
Remove a code symbol only with a usage/coverage disposition. Retain supported
native paths, real services, consumer helpers, observer state handling, the fixed
host guard and the dormant socket binding unless a separate replacement is
implemented and tested. No whole script was proven safe to delete by this static
review alone.

The [script inventory](2026-10-18-script-disposition.md) names every current helper
and the proposed disposition. It also records concrete CLI cleanup candidates.

## Research and execution limits

Primary evidence is the live connected GitHub content at the pinned commit; no
claim is based solely on the earlier main-branch plan. A container-side clone was
attempted but DNS access to GitHub was unavailable. The review therefore did not
run repository-wide searches, tests or executable app introspection locally.
Those are explicit acceptance requirements of the correction tasks.

For framework context only, the official
[FastMCP FastAPI integration](https://gofastmcp.com/integrations/fastapi) and
[Podman run documentation](https://docs.podman.io/en/latest/markdown/podman-run.1.html)
were checked. They are not substitutes for the repository's pinned SDK/runtime
contracts, nor a reason to upgrade dependencies during editorial work.

All tasks in the delivered plan are pending; the plan is draft. No remote files,
branches, issues, installation settings, credentials, containers or archive data
were changed by preparing this review.
