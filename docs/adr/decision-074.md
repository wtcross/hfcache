# Decision 074: The interpreter directory is part of the deployment and was outside every sweep

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `REL-002`.
- Source: [decision 74 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`install-release.sh` makes the release tree
root-owned and read-only to the service identity, because plan §21.4 wants
the account that runs the archive unable to modify the code that runs it. It
does that with `chown -R` and `chmod -R` over `${RELEASE}`.

`/opt/hfcache/python` is not under `${RELEASE}`. It holds the uv-managed
CPython 3.14.6 that `HOST-004` installed there precisely so the venv would not
depend on an interpreter under `/home` or on the distribution's 3.12, and it
is deliberately *not* rebuilt per release — one interpreter serves every
release, which is what makes a rollback a symlink switch. So the per-release
sweep never touches it, and `uv python install` leaves `.lock` at `0666`.

The exposure is small and worth stating precisely rather than dramatising: a
zero-byte lock file that uv uses to serialise interpreter installs, with the
interpreter binaries themselves root-owned `0755`. No code execution follows
from writing it. But it is a world-writable regular file inside the prefix
§21.4 says is root-owned, an unprivileged local user could interfere with a
future `uv python install`, and "the deployment contains nothing
world-writable" is a cheaper property to hold than to reason about each time.

Two things this changes. The mode is narrowed to `0644`, which costs nothing
because every caller of `uv python install` in this script is root and root
ignores the write bit. And the sweep is extended to the interpreter directory,
at `-maxdepth 1` so it corrects uv's own artifacts without walking 1 048
symlinks and several thousand files of standard library on every install.

The finding also says something about how the review found it. `find -perm
-o+w` returned 1 049 paths and 1 048 of them were symlinks, whose modes are
meaningless — a scan that reported "1 049 world-writable files" would have
been dismissed as noise. Filtering to `-type f` is what turned an unreadable
result into a one-line fix.

## Provenance and governing evidence

The source entry first appears in
[fa3818a](https://github.com/wtcross/hfcache/commit/fa3818afcde23b336d26dbffcac28fe1f599a4bb)
(2026-07-27, `REL-002: final quality and security gates`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md),
[docs/security.md](../security.md).

Implementation or shipped-artifact evidence:
[scripts/install-release.sh](../../scripts/install-release.sh).

Verification or recorded operational evidence:
[docs/agents/progress.md](../agents/progress.md).
