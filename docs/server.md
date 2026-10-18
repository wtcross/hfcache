# Writer server contract

Status: planned implementation. API-001 establishes the target boundary;
API-005/006/008/014 provide configuration, HTTP, executor, and packaging.
See [the API contract](api.md) and [active plan](plans/2026-10-17-plan-rest-api-and-mcp.md).
No service is installed or listening as a result of this document.

Run one unprivileged process, one admission registry, one heavyweight worker,
a bounded metadata pool, and both local Unix and optional TCP listeners sharing
that application. A daemon-instance lock prevents competing registries. Actual
archive work retains the existing local flock; metadata reads do not create
archive layout or rebuild catalogs. Systemd remains scheduling authority.

Archive policy reloads per admission; server listener and credentials require
restart. Root/UUID changes require restart and cannot hot-switch authority.
Configuration is operator-owned; REST cannot write `/etc/hfcache`. New config
cannot redirect an existing credential to a candidate-selected Hub endpoint.

Verification is delegated only to a narrow socket-activated executor with
`HF_HUB_OFFLINE=1`, `IPAddressDeny=any`, no credentials, peer identity checks,
bounded framed requests, and operation-correlated durable outcomes. It owns
the archive lock through hashing, report write, and catalog merge. No production
fallback runs it in the network-enabled HTTP process. Hermetic tests inject
an executor; host hardening remains an operator acceptance prerequisite.

Drain stops admission and joins work; disconnecting a scheduled CLI or Cockpit
client leaves accepted work running. Recovery evidence must identify the real
executor and operation, not a vanished CLI process. Preserve FS-18's narrow
supervised-cancellation rule. Never unlink a potentially held lock file.

Packaging will preserve sync/verify service names as authenticated Unix HTTP
clients. The actual verifier and its client both retain deny-all IP policy.
Deployment requires locked server extras, protected API credentials, socket
ownership, startup ordering, TLS/Host/Origin/proxy configuration, graceful drain,
rollback barriers, NFS and hardening acceptance, and the disabled verify timer.
No host policy changes or production listener starts are authorized here.
