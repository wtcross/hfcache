# Releasing hfcache

For agents assisting a maintainer with an explicitly authorized release.
[Deployment and rollback](../deployment-centos-stream-10.md) and the
[container contract](../containers.md) own the detailed profile procedures.
Implementation alone authorizes no deployment, tag, push or image publication.

## Prepare a reviewable release

1. Identify the supported profile, clean source commit, previous compatible
   release and authorized deployment scope. Record artifact identities and
   execution evidence externally or in the appropriate `docs/agents/` records.
   Preserve existing plans, task evidence, progress logs and snapshots.
2. Update `[project] version` in `pyproject.toml` and user-visible changes,
   compatibility and migration in `CHANGELOG.md`. README remains orientation;
   do not add a Status section, deployment ledger or progress report.
3. Run `scripts/check.sh --with-build`; for a full browser release use
   `--require-web` as well. Live/NFS checks need their own suitable environment
   and scope. A stopped or partially scoped gate is not a pass.
4. Commit the reviewed inputs, then build immutable artifacts from clean
   committed source. Keep artifacts, provenance and logs outside that source
   worktree. A later evidence-only commit does not change artifact identity.

## Durable compatibility

For a durable format change, perform the cross-format drill on a throwaway
archive with its own UUID, following [recovery](../recovery.md). Write the new
shape and read it with the actual previous release binary. Record observed
behavior as the release's rollback rule in the deployment guide. Apply the
schema-version policy in [schemas](../schemas.md); do not assume compatibility
from matching displayed versions. Scheduled handles, API/worker operation
stores and configuration formats also need applicable old-reader checks.

## Build and stage the selected profile

Native installation stages locked server dependencies; `--with-mcp` explicitly
includes MCP. It does not provision credentials, enable transport or modify an
existing switch target. Native tooling positively identifies source/current/
target layout and refuses rootless, mixed or unknown layouts.

Rootless releases require pinned UBI 10 micro base stages, verified interpreter,
binary and CA inputs, exact wheel/locked dependency closure and immutable
artifact indexes. Use the rootless installer and fixed host client. No runtime
resolution, auto-update, forced executor cleanup or automatic state deletion.
Only finite stateless observer clients may remove their own containers.

Full browser releases use `scripts/build-web-release.py --output <new-path>`
from clean committed source. Keep indexed UI/backend/helper artifacts and their
captured source together. Follow [web deployment](../web-ui/deployment.md) for
native index digests or rootless asset digests and web-input selection.

Stage non-secret runtime artifacts with readable directory/file permissions
and verify them as the actual service UID/GID. Keep private manifests and
backups protected. Preserve an unusable stage for diagnosis before any explained
restage. Build success proves neither installed usability nor production scope.

## Drain, select and verify

Before any switch, pause authorized timers and retain original operation and
scheduled handles. Prevent new API/private-worker activation, drain actual work,
and prove zero service PIDs/cgroup tasks and complete container drain. Hold the
noncreating original lock across the switch. Wrapper exit or an unlocked instant
does not prove completion. Unknown state blocks selection; never unlink a lock,
kill an executor or repeat an uncertain submission.

Back up required private state and configuration, retain predecessor artifacts,
and follow the profile-specific installer. For guarded rootless deployment,
transfer the original lock only after actual drain, preserving the independently
proven host read-only barrier and writer masks. Writer mode requires separate
protected authority and all supported startup prerequisites.

Verify installed runtime identity, TLS, credential separation, listener readiness,
actual worker isolation, applicable SELinux/NFS behavior, original-outcome
observation and rollback compatibility. Execute live verification or writer
pilots only within explicit scope. Record source tests, installed checks and
missing environmental acceptance separately. Never promote a source fixture
into installed or unattended-boot acceptance.

Static user-unit verification uses isolated runtime/bus/unit paths, never the
live user manager's `XDG_RUNTIME_DIR`; see
[container verification](../containers.md#static-user-unit-verification).

## Tagging, publication and rollback

Normal policy tags the deployed, tested artifact with an annotated
`v<version>` tag. Its note describes user-visible changes, compatibility,
rollback constraints and the actual scope of acceptance. An explicit no-tag
instruction takes precedence; preserve exact commit/artifact identities externally.
Push to both remotes only within publication authority and after the gate passes.
Keep previous releases as rollback targets.

Rollback uses the same guarded profile installer and full drain procedure.
Check the previous binary against retained durable state and pending handles.
Disable MCP deliberately before selecting a server-only/pre-MCP target; there
is no automatic fallback. Preserve original outcomes and write barriers.
No rollback may invent execution certainty or silently restore old store bytes.
