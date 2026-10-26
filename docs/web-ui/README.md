# hfcache web interface

For read errors, see [troubleshooting](troubleshooting.md), including the
difference between a failed domain read and unavailable or unsupported evidence.

The replacement interface is implemented in unreleased source and can be enabled
explicitly with a matching protected asset release. Installed systems retain
their recorded release and the [existing Cockpit interface](../cockpit-plugin/README.md).
These guides do not install a release, enable a schedule or grant archive write
permission.

When enabled, open `/ui/` on the existing HTTPS endpoint, or
`/management/ui/` for an installation whose public prefix is `/management`.
The browser's native sign-in dialog uses the separately provisioned administrator
username and password. Follow the [operator deployment guide](deployment.md);
the page never asks for a REST or Hub token. All interface documents and assets
require administrator authentication. REST bearer and read-only MCP access remain
separate on the same Caddy endpoint.

After sign-in, **Administrator session** identifies the authenticated human.
**Configured archive** shows the UUID from installed policy; it does not mean
archive health, inventory or writability has been checked. The current interface
provides the [Library](library.md), permission explanations and
[original-operation observation and recovery](operations.md). Full repository
detail views and job forms are still under development:

| Workspace | Intended workflow |
| --- | --- |
| Library | [Find configured and archived models or datasets](library.md) using local ID/tag and technical filters. Keep scope, loaded rows, coverage and current/historical provenance distinct. |
| Operations | [Observe and recover original operation handles](operations.md), including after a connection interruption. Full job submission forms remain under development. |
| Maintenance | Review the scope of existing retention, repair and recovery actions before any separate Apply action. |
| Administration | Read [protected host status and permission reasons](administration.md); use the [configuration and tags API guide](configuration-and-tags.md) for installed intent, managed validation, exact previews and guarded application. |

Use the sidebar or **Open navigation** on a narrow screen to change workspace.
Direct links to Library, Operations, Maintenance and Administration survive a
reload. Library filter bookmarks use bounded URL fragments after `#`, not shell
query strings; filtering performs reads only. Administration lists each permission with its current reason; the
unimplemented host controls remain disabled. Guarded configuration application
is available through its separate API workflow and exact original preview. Configuration
read/validate/preview API availability does not imply a browser editor. A grant
alone does not make a feature available or remove a read-only guard.

**Check interface version** performs a read, without reloading automatically or
replaying an operation. A compatible API restart requires explicit reconnect
before resuming observation with fresh authenticated context; the original
handles keep their admitted scope. If **Interface update required** appears, preserve
original operation handles and unsaved work, then choose **Reload interface**
when ready. If startup stops at **Starting hfcache**, the inert explanation and
reload link remain available even when the application module could not load;
see [startup troubleshooting](troubleshooting.md#interface-startup-and-release-changes).
**Stop observing in this browser** stops local reads, never accepted backend
work. Keep and copy original handles before closing a recovery session.

Browser access uses HTTP Basic over verified HTTPS. The browser manages the
password and may cache it after a tab closes; Basic has no reliable application
logout. Use a dedicated trusted browser profile and close that profile/session
when finished. Never bypass a certificate warning.

A source-only developer preview can still show **Development preview** and
**Archive not connected**. That shell is not authenticated installed acceptance.
Building or testing it does not enable routes on an installed system. Developers
can use the [workspace checks](../development.md#web-workspace) to validate their
local source and build.

A publication identifies one immutable file tree by repository type, repository
ID, full commit SHA and publication ID. Repairs can create a different publication
at the same SHA. Current configuration tags describe operator curation; they do
not prove publication membership or verification. [README capture](readme-cards.md)
now retains bounded, sanitized upstream presentation in unreleased source through
the existing writer workflow. Its exact read API is available in that source;
browser display remains under development. The API adds no card view or external media.

Until the replacement passes its installed compatibility and functional checks,
Cockpit remains shipped. Production migration and rollback require separate
operator authorization. See [deployment profiles](../deployment-centos-stream-10.md),
[current installed scope](../deployment-status.md), and the
[documentation index](../README.md) for supported procedures today.
