# hfcache web interface

Open the provisioned HTTPS URL and sign in with your administrator username and
password. Ask the operator for the URL, credentials and certificate trust setup.
Browser access requires an enabled web interface with matching backend/assets;
local builds do not change an installed service.

When enabled, open `/ui/` on the existing HTTPS endpoint, or
`/management/ui/` for an installation whose public prefix is `/management`.
The browser's native sign-in dialog uses the separately provisioned administrator
username and password. Follow the [operator deployment guide](deployment.md);
the page never asks for a REST or Hub token. All interface documents and assets
require administrator authentication. REST bearer and read-only MCP access remain
separate on the same Caddy endpoint.

For a reviewed build and operator transition, use the
[build and deployment procedure](deployment.md#operate-the-web-interface).

For an interface transition or release rollback, follow the
[migration and compatibility guide](migration-and-rollback.md). Preserve original
operation handles, protected configuration and compatible observers before switching.

After sign-in, **Administrator session** identifies the authenticated human.
**Configured archive** shows the UUID from installed policy; it does not mean
archive health, inventory or writability has been checked. The current interface
provides the [Library](library.md), permission explanations and
[jobs, operation/report history and original recovery](operations.md), with
[exact-publication repository details](repository-details.md). The bounded
[README view](readme-cards.md) provides formatted and sanitized-source display.
[Configuration and tags](configuration-and-tags.md) adds structured managed
editing. [Maintenance](maintenance.md) provides reviewed retention, recovery,
quarantine cleanup and finding-based repair. Operations composes supported job
forms with original-handle recovery:

| Workspace | Intended workflow |
| --- | --- |
| Library | [Find configured and archived models or datasets](library.md) using local ID/tag and technical filters. Keep scope, loaded rows, coverage and current/historical provenance distinct. |
| Repository details | [Inspect a selected exact publication](repository-details.md), attributed model/dataset metadata, files, revisions, integrity and loaded history; open current configuration tag editing separately. |
| Operations | [Submit supported jobs, inspect bounded operation/run history and recover original handles](operations.md). Preserve effects, result classification and original identity through interruption. |
| Maintenance | [Preview and review retention, recovery and quarantine cleanup, or check repair evidence from an exact finding](maintenance.md), before a separately confirmed archive effect. |
| Administration | Inspect [archive/readiness/verification observations, warnings and independent host permissions](administration.md); use reviewed configuration, diagnostics, fixed sync schedule/observer controls, bounded journals and original-operation recovery as permitted by the installed profile. |

Use the sidebar or **Open navigation** on a narrow screen to change workspace.
See [browser and keyboard use](browser-and-keyboard.md) for focus, table navigation,
zoom, hidden-tab observation and practical large-library limits.
Direct links to Library, Operations, Maintenance and Administration survive a
reload. Recognized type-aware repository paths also survive reload, with a
paired full SHA/publication selection and fixed tab in a bounded fragment.
Library filter bookmarks use bounded URL fragments after `#`, not shell query
strings; filtering and detail navigation perform reads only. Administration lists
each permission with its current reason; unavailable or denied host controls
remain disabled. The guarded rootless profile does not substitute user-manager
units for unproved system schedule/observer bindings. Configuration editing uses
its independent grants and original preview, not host-read as an extra
prerequisite. Opening or reading the editor starts no
job; explicit preview/Apply retains its original handles. Neither editing nor
job permission evidence changes protected authority or removes a read-only guard.
A grant alone never proves readiness.

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
supports bounded, sanitized upstream presentation through the existing writer
workflow in matching releases. The exact read API preserves publication identity;
the interface adds a bounded Rendered README and Sanitized source
view in Overview. Neither view loads external media.

For access, read or permission errors, use [troubleshooting](troubleshooting.md).
Operators can follow [deployment](deployment.md) and
[migration and rollback](migration-and-rollback.md) for profile-specific procedures.
