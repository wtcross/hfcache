# Copy a separate native interpreter for each immutable web release

- Decision identity: 158.
- Status: Accepted; installed conformance remains separately required.
- Date: 2026-10-29.
- Introducing change: this commit.

## Context and decision

The native profile's managed CPython contains pip and ensurepip. A clean native
installation audit proved the UI, helper and application hashes, but correctly
refused to claim a runtime without package managers. Altering the shared managed
interpreter would change a retained or running release behind its immutable
selection. Merely excluding those files from an audit would leave them present
in the selected runtime.

Pin the source interpreter to CPython3.14.6. For an explicitly enabled full web
release, copy its managed interpreter into a fresh protected directory below
`/opt/hfcache/python`, named for the application version and exact source commit.
Use that copy's ordinary executable directly when building the release virtual
environment. Omit only the inspected pip launchers, pip package/distribution
metadata and ensurepip from the copy. Preserve the complete managed donor and
all previous runtimes unchanged as build inputs and rollback evidence.

The copy is local, bounded, protected and independent of cache hardlinks or
mutable source aliases. Symlinks must remain inside the copied interpreter tree.
An existing destination or an unexpected installer layout refuses; partial
copies remain for inspection. The native helper already supports a directly
indexed protected ordinary interpreter below the fixed Python root; retain its
exact target, executable hash, alias and capture rules.

Copy inspection permits at most32,768 entries,512MiB total,64MiB per ordinary
file,32 directory levels,4,096 path characters and40 contained symlink hops.
Owner/mode/type and retained byte/link inventories must agree before publication;
the donor is rechecked unchanged. An isolated copied-interpreter probe confirms
its relocated prefix, exact Python patch and missing pip/ensurepip before the
destination becomes service-readable. Only the inspected pip26.1.2 closure is
omitted; another installer layout refuses for review.
The copied-runtime name grammar additionally accepts `+` in standard terminal
database names. This does not change UI/source path grammars or permit external
or escaping links.

## Rationale and alternatives

A separate interpreter prevents a new full release from modifying the shared
donor used by older releases. Removing optional installers matches the existing
container runtime boundary while keeping uv as a separate build tool. Ordinary
copying also avoids filesystem reflink failures and shared-cache link authority.
Stripping the shared donor, reusing an unexplained directory, relaxing the audit,
and adding a deployed package manager were rejected.

## Consequences and compatibility

Full web native installations use additional local storage for their independent
runtime. Python-only installation remains supported without Node or UI inputs;
its existing managed-interpreter path is unchanged. No archive, operation,
credential or helper-protocol format changes. There is no runtime dependency,
privilege, host policy, schedule or automatic activation change. Native host OS
administration tools remain distinct from the shipped application runtime.

Construction and focused tests do not establish installed behavior. Require the
actual selected interpreter/virtual environment to have no Node, frontend
package managers, pip/ensurepip, compilers or browsers, and verify installed
application/UI/helper bytes plus actual service confinement separately.

## Evidence and relationships

Refines [separate immutable web artifacts](decision-143.md), the
[UBI runtime installer exclusion](decision-129.md),
[the Python toolchain pin](decision-007.md) and the protected native interpreter
contract in [host administration](../host-administration.md). See the
[native installer](../../scripts/install-release.sh),
[release verifier](../../scripts/web-release.py),
[deployment guide](../web-ui/deployment.md) and
[native installer tests](../../tests/unit/test_release_installer.py).
