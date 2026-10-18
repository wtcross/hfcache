# Scope execution correlation and offline process initialization

- Decision identity: 111.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.


## Context, decision and rationale

A concurrent API process cannot safely use mutable process-global run identity,
verbosity or temporary offline environment toggles. Use immutable scoped execution
context for request/operation/domain run identities, capture correlation when a
record is emitted and explicitly copy context into worker threads. Daemon logging
configuration is startup-only; client verbosity remains local. Invocation mode
identifies execution host, not timer/submitter origin or an individual person.

Register exact credentials before use and sanitize nested diagnostics and public
output, including exception paths, without echoing rejected input. Known-token
redaction is defense in depth, not a claim to recognize arbitrary unknown secrets.
Dedicated offline-process startup initializes the Hub library flag before shared
imports. That flag is not IP denial; the private worker's native/rootless sandbox
and credential masks supply separate enforcement. Shared domain calls never
change environment to emulate isolation. No durable schema or domain algorithm
is added by context propagation.

## Relationships and technical evidence

- [decision 64](decision-064.md)
- [offline verification](offline-verification.md)
- [decision 110](decision-110.md)
- [AD-19](ad-19.md)
- [Scheduling authority](systemd-scheduling.md)
- [context, logger, secret and verification isolation tests](../../tests/unit/test_execution_isolation.py)
- [delayed formatting and existing CLI logging tests](../../tests/unit/test_logging.py)
- [sync producer propagation tests](../../tests/unit/test_synchronize.py)
- [startup-only child-process tests](../../tests/unit/test_offline_process.py)
- [identity/result tests](../../tests/unit/test_queries.py)
- [execution context](../../src/hfcache/services/context.py)
- [event capture and thread submission](../../src/hfcache/logging.py)
- [redaction](../../src/hfcache/redaction.py)
- [shared commands](../../src/hfcache/services/commands.py)
- [offline initialization](../../src/hfcache/offline.py)
- [Decision 127](decision-127.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
