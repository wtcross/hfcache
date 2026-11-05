# Validate the exact read-only service ACL on a protected credential

- Decision identity: 152.
- Status: Accepted.
- Date: 2026-10-22.
- Record introduced: `9af58cb23776302793271f86e01007f676c92a8e`.
- Amends credential-source validation only in [decision112](decision-112.md)
  and [decision146](decision-146.md).

## Context and decision

Systemd can retain root ownership and grant a service UID read access through
a POSIX ACL. Stat group bits then represent the ACL mask. A reader that requires
owning-group membership therefore rejects a legitimate named-user credential
even when the service can open it. The exception must prove the exact ACL rather
than infer access from readable group bits.

Preserve explicit sources, no-follow descriptor traversal, regular/trusted
inode, mode, single-link, size, bounded reads and stable metadata. Ordinary
group-authorized files retain their policy. Add one alternative for root:root
`0440` whose group is not an effective or supplementary service group: require
exactly this canonical Linux version-2 access ACL.

| Entry | ID | Permission |
| --- | --- | --- |
| Owner user | unqualified | read |
| Named user | effective service UID | read |
| Owning group | unqualified | none |
| Mask | unqualified | read |
| Other | unqualified | none |

Only root and the effective service UID can read under this exception. Require
five ordered little-endian entries, undefined IDs on unqualified entries and
exactly 44 bytes. Missing, unsupported, inaccessible, malformed, reordered,
extra-user/group, wrong-UID, writable or executable ACLs refuse this alternative
with generic `HFAPI003`. Read the ACL from the checked descriptor. Check initial
metadata, initial ACL, bounded content, identical final ACL, then final metadata
using all nine existing fields. Python's xattr retrieval has Linux's 64 KiB value
limit; 44 bytes is the accepted shape, not a retrieval-buffer parameter.
Authentication diagnostics publish no ACL, credential body or credential digest.

## Rationale and alternatives

The [systemd credential writer](https://github.com/systemd/systemd/blob/v257/src/core/exec-credential.c#L294-L339)
uses owner-read plus a named-UID read ACL, with ownership as fallback. Its
[ACL helper](https://github.com/systemd/systemd/blob/v257/src/shared/acl-util.c#L417-L460)
adds the entry and mask. The
[Linux ABI](https://github.com/torvalds/linux/blob/v6.12/include/uapi/linux/posix_acl_xattr.h)
and [entry tags](https://github.com/torvalds/linux/blob/v6.12/include/uapi/linux/posix_acl.h)
permit exact bytes comparison; the
[Python descriptor API](https://docs.python.org/3.14/library/os.html#os.getxattr)
requires no dependency or subprocess.

A global group-check bypass or blanket root-group/ACL admission would allow
unrelated readers. Permission changes, root-group membership and plaintext
copies change authority or secret lifecycle; reject them. General ACL auditing
of already admitted ordinary group-authorized files is separate scope.

## Consequences and required proof

### Directory traversal refinement (2026-10-24)

An `O_RDONLY` directory open can be denied even when the service can traverse
the protected parent and open its `0400` Basic record for reading. Directory
data and listings are unnecessary for descriptor-relative
no-follow traversal. Open only directory components with Linux `O_PATH`, retaining
`O_DIRECTORY`, `O_NOFOLLOW` and `O_CLOEXEC`; open the credential leaf with its
existing readable flags. Preserve every leaf, ACL, bound and metadata check.
This is an implementation refinement of the existing protected-source contract,
not a new source or authentication authority. It needs no directory-read MAC/DAC
grant, permission change, credential copy or runtime dependency. Retain the
search-only and readable-leaf regression coverage. Independently provision
parent search, leaf read and selected-role SELinux access; the reader grants
none of these permissions.

REST writer/reader, MCP reader and Basic share this protected reader. Source
grammar, classes, stable subject, authentication, CSRF, redaction and restart
lifetime remain. Hub/archive authority, operation identity and recovery remain.
No root API, capability, SELinux, systemd or filesystem permission grant follows.

Require shape/refusal, real owned ACL, descriptor/path replacement, ACL/metadata
race and existing bearer/Basic tests. Native and rootless credential delivery
must be verified under their actual hardening, followed by normal executor
closure; a synthetic ACL test alone cannot establish complete UI authentication.

This decision preserves INV-002/003 and FW-03/04. See the
[credential contract](../server.md#credentials-and-capabilities),
[security boundary](../security.md#t-14--a-management-caller-gains-unintended-authority),
[protected reader](../../src/hfcache/api/credential_sources.py) and
[adversarial tests](../../tests/unit/test_server_auth_adversarial.py) and
[ACL regression tests](../../tests/unit/test_credential_systemd_acl.py).
