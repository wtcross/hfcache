# Troubleshoot browser access and web reads

## Administrator login

The optional administrator provider is implemented in unreleased source; the
installed interface remains unchanged. See [protected provisioning](deployment.md)
and [interface availability](README.md) first. `/ui/` is not served yet.

| Problem | Meaning and safe next step |
| --- | --- |
| Repeated native sign-in dialog / HFAPI001 / HTTP 401 | The browser's cached pair or configured identity did not authenticate. Verify the intended HTTPS authority, username and reviewed credential delivery with the operator. Wrong username and wrong password deliberately have the same response. Do not share Authorization headers or substitute a bearer in the page. |
| HFAPI021 / HTTP 429 | The two verification workers/eight waiting slots or the global failed-attempt budget are occupied. Wait for accepted verification work and the 60-second failure window; repeated retries increase load. Bearer observation of an original operation remains separate. |
| HFAPI010 / HTTP 403 on a browser mutation | Verify the exact configured HTTPS Origin, JSON Content-Type and application request header. Foreign/missing/null Origins and simple forms are refused. Use the supported UI action; do not disable CSRF or widen allowlists. |
| HFAPI002 / HTTP 403 | The authenticated principal lacks the required permission. Administrator login grants no protected host policy; inspect effective grants and the intended action without changing a guard. |
| HFAPI003 during startup | The selected hash record is missing, unsafe, malformed or uses unsupported hash parameters. Inspect source path/owner/mode/record version without printing its contents. Restore the reviewed source or provision a new protected record; there is no credential-source fallback. |
| HFAPI009 / unavailable | The verifier is unavailable or draining. Keep original operation handles and investigate service readiness/drain; do not replay a mutation. |
| Certificate warning | Stop and correct trust, certificate chain/SAN or endpoint selection. Do not bypass TLS. |
| Old credentials remain after closing a tab | Basic authentication is browser-managed and has no reliable application logout. Close the dedicated profile/session; password rotation needs a new protected record and authorized drained restart. |

An administrator record's stable subject owns its original operation keys.
Keeping the subject during password rotation preserves that namespace. Changing
it separates the new identity; it never proves an old operation did not execute.
Do not delete receipts or resend a lost action to regain visibility.

## Read results

Check [interface availability](README.md) before using this guide. The replacement
interface is a development preview; the installed interface and production
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
