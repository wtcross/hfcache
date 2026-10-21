# Troubleshoot browser access and web reads

## Administrator login

The optional administrator provider and authenticated asset routes are implemented
in unreleased source; installed systems retain their recorded release. See
[protected provisioning](deployment.md) and [interface availability](README.md)
first. `/ui/` requires explicit enablement with matching immutable assets.

| Problem | Meaning and safe next step |
| --- | --- |
| Repeated native sign-in dialog / HFAPI001 / HTTP 401 | The browser's cached pair or configured identity did not authenticate. Verify the intended HTTPS authority, username and reviewed credential delivery with the operator. Wrong username and wrong password deliberately have the same response. Do not share Authorization headers or substitute a bearer in the page. |
| HFAPI021 / HTTP 429 | The two verification workers/eight waiting slots or the global failed-attempt budget are occupied. Wait for accepted verification work and the 60-second failure window; repeated retries increase load. Bearer observation of an original operation remains separate. |
| HFAPI010 / HTTP 403 on a browser mutation | Verify the exact configured HTTPS Origin, JSON Content-Type and application request header. Foreign/missing/null Origins and simple forms are refused. Use the supported UI action; do not disable CSRF or widen allowlists. |
| HFAPI002 / HTTP 403 | The authenticated principal lacks the required permission. Administrator login grants no protected host policy; inspect effective grants and the intended action without changing a guard. |
| HFAPI003 during startup | The selected hash record is missing, unsafe, malformed or uses unsupported hash parameters. Inspect source path/owner/mode/record version without printing its contents. Restore the reviewed source or provision a new protected record; there is no credential-source fallback. |
| HFAPI009 / unavailable during authentication | The authentication service is unavailable or draining. Keep original operation handles and investigate service readiness/drain; do not replay a mutation. |
| Certificate warning | Stop and correct trust, certificate chain/SAN or endpoint selection. Do not bypass TLS. |
| Old credentials remain after closing a tab | Basic authentication is browser-managed and has no reliable application logout. Close the dedicated profile/session; password rotation needs a new protected record and authorized drained restart. |

An administrator record's stable subject owns its original operation keys.
Keeping the subject during password rotation preserves that namespace. Changing
it separates the new identity; it never proves an old operation did not execute.
Do not delete receipts or resend a lost action to regain visibility.

## Private verification service

`HFAPI016` / HTTP 503 / exit 20 means the separate verification executor is
unavailable or untrusted. This can prevent startup reconciliation or refuse a
verification request even when administrator authentication and metadata reads
work. Preserve original operation handles; an unavailable worker is not evidence
that an earlier operation stopped.

For native system-manager activation, check two independent authorities:
`verification.expected_peer_uid = 0` identifies the listener's creator, and
`verification.expected_socket_owner_uid` must match the actual numeric service
account owning the socket. Measure that installation's account and effective
`SocketUser`; do not assume another host's UID. If the owner setting is omitted,
the expected owner remains the resolved expected peer UID. Setting peer `0`
alone therefore does not describe the ordinary service-owned native socket.
Follow [native verifier identity](../deployment-centos-stream-10.md#native-verifier-identity)
and the [server settings](../server.md#private-verifier-client-settings).

Rootless worker-created sockets retain their equal owner/peer configuration.
Keep the native named-FD3 and rootless notify/listener modes separate. Never
chown an existing node, relax permissions or SELinux, replace the acceptor, or
run a local verifier as a fallback. A corrected configuration takes effect only
through an authorized drained restart and actual API-to-worker validation.

## Interface startup and release changes

| Problem | Meaning and safe next step |
| --- | --- |
| `/ui/` returns an authenticated 404 | The selected installation may have web disabled, an older release or a different public prefix. Confirm the selected release and configured prefix. Building a local UI does not change an installed API. |
| Startup refuses with HFCFG005 and an enabled-asset diagnostic | The manifest, application/wire version, indexed bytes, protected ownership, local mount identity or disjointness proof failed. Compare the selected artifact and reviewed manifest hash. Preserve the failed release; restore a coherent artifact/configuration pair in a separately authorized rollout. Do not grant write permissions, follow symlinks or move assets into the archive. |
| **Starting hfcache** remains visible | The entry module, bootstrap read or build/context validation did not complete. The explanation and **Reload interface** link are inert HTML and remain usable if JavaScript never loads. Check the HTTPS authority, deployment prefix and matching release; share safe status/codes rather than raw bootstrap or credential data. |
| **Interface update required** | A loaded chunk failed or an explicit version check observed a changed artifact. Preserve original operation handles and unsaved work, then reload when ready. The interface never reloads or replays an action automatically. |
| **The interface version could not be checked** | The bounded bootstrap read did not produce a matching supported result. Keep the current operation handles. Investigate the selected release and connection; failure does not prove an operation stopped. |
| Missing `.js`/`.css` or an unknown workspace returns JSON 404 | Only indexed assets and exact supported workspace routes are served. The API deliberately does not substitute HTML for a missing module or unrelated route. Compare the selected artifact/prefix; do not add a global history fallback in Caddy. |
| HTTP 503 / HFAPI009 while loading an asset | Static admission is full or draining. At most 16 UI bodies are active with no queue; each send has a 30-second deadline. Wait for the current requests or investigate an authorized service drain. Metadata and authentication use separate capacity. |
| Administration shows disabled actions | A known grant does not make an unimplemented or host-denied feature effective. The displayed reason is authoritative for that scope; signing in does not clear a guard, enable schedules or permit archive writes. |

Reload uses the same trusted URL and browser-managed credentials. Never paste a
bearer into page storage or use a certificate-bypass flag to get past startup.
The application captures assets once; changing files below the running process
does not update its captured release. An artifact transition requires a reviewed,
drained restart, not repeated mutation requests or manual receipt deletion.

## Foreground service shutdown

A completed application lifespan, vanished PID or refused connection does not
alone prove removal of an API-owned Unix socket. The foreground bootstrap defers
main-thread default SIGTERM in a non-PID1 process until its exact owned listener
cleanup finishes, then retains the original signal exit. Activated manager-owned
nodes, PID1 and custom/ignored handlers have separate unchanged lifetimes; follow
[foreground listener ownership](../server.md#foreground-listener-bootstrap).

If a stopped process leaves a socket pathname, preserve it and investigate the
selected version, actual signal/exit, exact device/inode ownership and complete
service drain. Forced termination has no cleanup guarantee. Do not unlink an
unknown node, chmod it or start another writer to make a readiness check pass.
Use the authorized [upgrade and drain procedure](../deployment-centos-stream-10.md#upgrade-and-drain).

## Read results

Check [interface availability](README.md) before using this guide. The current
authenticated shell establishes configured identity and navigation; domain read
views remain under development. The following read-state guidance also applies
to the real API read fixture and the forthcoming views. Installed production
services are unchanged. A read result describes observed information, never
permission to modify an archive or proof that an accepted job has finished.

| Message | Meaning | Safe next step |
| --- | --- | --- |
| Loading server information | The current GET is pending. | Wait for this read or leave the view; aborting observation does not cancel a backend operation. |
| Server status / Server version / Server capabilities / Archive inspection | The expected response and its identity validated. | Interpret the displayed fields and warnings. Readiness alone does not prove writability or publication integrity. |
| Read failed | The server returned a valid failed domain Envelope, including its original error codes. HTTP 200 can carry this state. | Keep the codes and request/run identity. Follow the relevant operator procedure; any displayed partial information is informational. |
| Access refused | The API returned an access problem, such as 401 or 403. | Check the intended endpoint and provisioned access with the operator. Do not substitute another credential class or weaken transport controls. |
| API unavailable | The API returned a classified HTTP problem. | Keep its code and request identity. The service may be busy, draining or unable to load policy; this does not prove the archive is empty. |
| Unsupported response | A version, required field, identity, numeric value or response bound could not be validated. | Preserve the browser/backend versions and safe diagnostic code for the operator. Do not treat rejected content as data or edit it into an acceptable response. |
| Connection unavailable | The read did not yield a valid HTTP response. | Check the intended service connection. The last read is unavailable; its failure says nothing about an earlier job's execution. |
| Read unavailable | Observation was aborted before a validated result. | Start a new explicit GET when appropriate. Retain any original operation handle separately. |

**Refresh read** repeats only the selected GET. It does not retry a mutation,
initialize an archive, start a service or contact the Hub. A fresh response replaces
earlier read evidence; a failed refresh must not leave old capacity or health
values looking current. A malformed or incomplete inventory is unavailable, not
zero repositories. Large integers outside the browser's exact supported range
are unavailable rather than rounded.

For an uncertain operation, keep its original idempotency key and accepted ID.
Inspect that original operation using the established
[reconnect procedure](../api.md#reconnect-after-lost-acknowledgement). A missing
receipt or unavailable connection does not prove nonexecution and does not
authorize a replacement POST, rollback or cleanup. HTTP admission and domain
completion remain different facts.

Share only safe codes and validated identifiers when reporting a problem.
Passwords, bearer values, raw response bodies, configuration drafts and exception
text do not belong in screenshots or diagnostic reports. Operators should compare
the intended API authority, archive identity and supported source/artifact versions
before investigating [wire limits](../api.md#browser-wire-boundary). Changing a
browser limit is a reviewed software change, not an operator workaround.
