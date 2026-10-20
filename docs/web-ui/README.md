# hfcache web interface

The standalone web interface is under development and is not yet available in a
release. Continue using the [existing Cockpit interface](../cockpit-plugin/README.md)
for installed systems. Creating these guides does not change an installed
service, enable a schedule, or grant archive write permission.

The replacement will provide four workspaces:

| Workspace | Purpose |
| --- | --- |
| Library | Find configured and archived models or datasets, inspect exact publications and distinguish metadata coverage from integrity evidence. |
| Operations | Submit supported jobs and observe their original operation handles, including after a connection interruption. |
| Maintenance | Review the scope of existing retention, repair and recovery actions before any separate Apply action. |
| Administration | Review configuration, tags, effective permissions and supported fixed host controls. |

The planned entrypoint is `/ui/` behind the same Caddy HTTPS endpoint that serves
REST and MCP. A deployment with public prefix `/management` will use
`/management/ui/`. No additional frontend server or port is needed. These paths
are reserved design targets; the current application does not serve them.

Browser access will use a separately provisioned administrator account with
HTTP Basic authentication over verified HTTPS. The browser manages the password;
the page will not ask for a REST or Hub token. Basic authentication has no reliable
application logout. Signing in will not remove a read-only guard or enable a
disabled host action. Existing REST and read-only MCP credentials remain separate.

A publication identifies one immutable file tree by repository type, repository
ID, full commit SHA and publication ID. Repairs can create a different publication
at the same SHA. Current configuration tags describe operator curation; they do
not prove publication membership or verification. An archived README will be
upstream-authored, bounded offline presentation data, with external media blocked.

Until the replacement passes its installed compatibility and functional checks,
Cockpit remains shipped. Production migration and rollback require separate
operator authorization. See [deployment profiles](../deployment-centos-stream-10.md),
[current installed scope](../deployment-status.md), and the
[documentation index](../README.md) for supported procedures today.
