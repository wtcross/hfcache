# Troubleshoot web reads

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
