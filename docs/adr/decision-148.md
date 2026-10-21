# Configure socket ownership separately from inherited listener credentials

- Decision identity: 148.
- Status: Accepted.
- Date: 2026-10-20.

## Context

Native systemd activation creates and listens on the private socket before
passing named FD3 to the unprivileged worker. `SocketUser` assigns the filesystem
node to the service account. Linux retains the listener creator's credentials
for client `SO_PEERCRED`; accepting the inherited descriptor does not substitute
the worker's credentials. The worker separately requires its own filesystem UID.
One expected UID cannot express both authorities in this native arrangement.

## Decision and rationale

Add optional, strict, nonnegative `verification.expected_socket_owner_uid`.
Omission preserves the existing rule: resolve the expected owner to the resolved
`expected_peer_uid`, whose omission still uses the API's effective UID. An explicit
owner permits the existing service-owned native node and root-manager-created
listener to be authenticated separately. Both checks must pass; there is no
UID allowlist, guessed identity, automatic retry or alternate listener.

Retain protected parent traversal, no-follow lookup, socket type and mode checks,
exact inode comparison and the exact configured kernel peer. Retain the worker's
ownership validation, API-client credential check and strict named-FD3 bootstrap.
Rootless worker-created listeners keep their existing equal owner/peer identity.
The listener creator must never be reported as the actual accepting worker.

Changing native socket ownership, weakening peer checks, or using a user-manager
substitute would conceal the mismatch rather than represent the existing design.
The explicit optional setting preserves old configurations and direct calls.

## Consequences and evidence

Native operators configure peer UID `0` for the system manager and the actual
service-account UID for socket ownership. That numeric account UID is specific
to the installation. This is restart-only configuration, never request-selected
authority. Existing configurations retain their previous behavior; no running
configuration, service or production acceptance changes automatically.

Source tests must prove independent owner and peer refusals and exact legacy
omission behavior. Installed acceptance must exercise the original API client
and original unprivileged FD3 worker through the unchanged manager-owned node.
Source tests alone do not establish installed connectivity or confinement.

- [Private client settings](../server.md#private-verifier-client-settings)
- [Private protocol](../../src/hfcache/verification_protocol.py)
- [Worker listener validation](../../src/hfcache/verification_executor.py)
- [Native socket unit](../../packaging/systemd/hfcache-verification.socket)
- [Decision 115](decision-115.md), [decision 121](decision-121.md) and
  [decision 128](decision-128.md) retain their execution and bootstrap policies;
  this decision amends only the client's identity configuration.
- [Linux 6.12 Unix sockets](https://github.com/torvalds/linux/blob/v6.12/net/unix/af_unix.c)
  and [systemd 257 socket ownership](https://www.freedesktop.org/software/systemd/man/257/systemd.socket.html#SocketUser=)
  distinguish listener credentials from filesystem ownership.
