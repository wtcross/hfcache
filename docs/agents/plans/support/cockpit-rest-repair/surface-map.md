# Reviewed surface / target transport map

Paths below are relative to `/api/v1`. “Existing” means the route is present in the
reviewed API contract, not that the installed host was exercised. All application
calls remain behind the fixed API-only client launcher. No route accepts browser
credentials, server filesystem paths, arbitrary HTTP methods or MCP writes.

| Surface | Current implementation | Existing API | Required correction / retained boundary |
| --- | --- | --- | --- |
| Candidate write/read/install/backup/discard | Guarded privileged fixed-path host operations | Intentionally none | Keep atomic host boundary; structured stage errors and exact read-only reconciliation. |
| Candidate validation | `--config /etc/hfcache/.candidate.toml config validate` | POST `/config/validate`, candidate, writer, synchronous | Keep content upload; preserve general failed Envelopes; never invent an operation receipt. |
| Installed validation/confirmation | `config validate` plus exact host guard for confirmation | POST `/config/validate`, installed, reader/writer | Keep exact before/after content and operational fingerprint checks; retain cause on failure. |
| Candidate sizing | `--config ... plan SELECTORS` | POST `/plans`, candidate, writer, keyed | Capture key before process/send; durable recovery UI; stale base invalidates install readiness. |
| Installed plan | `plan` | POST `/plans`, installed, reader/writer, keyed | Use shared operation registry; not a freely replayable synchronous read. |
| Status | `status` | GET `/status` | Preserve existing paging/client behavior; explicit stale/unavailable state. |
| Repositories/revisions | `list --revisions` | GET `/repositories`, `/repositories/revisions` | Keep bounded identity-checked joins and domain errors. |
| Server version | `version --server` | GET `/version` | Already correct request; add missing failed-Envelope rendering; correct old docs table. |
| Verification estimate | `verify --estimate` | GET `/verification/estimate` | Add failed-Envelope rendering; no verification confidence from missing values. |
| Selected sync | `sync SELECTORS` | POST `/syncs`, keyed writer job | Keep REST; durable handles, explicit guard restriction, no repeat after uncertainty. |
| Manual full sync | Start legacy system `hfcache-sync.service` | POST `/syncs`, CLI `sync` | Amend CP-04; use shared REST operation UI only for permitted profile; never bypass current holds. |
| Manual full verification | Start legacy system `hfcache-verify.service` | POST `/verifications`, mode full, CLI `verify --full` | Same shared operation UI/gates; private offline worker remains executor. |
| Revision verification | `verify --revision TYPE:ID@SHA` | POST `/verifications`, mode revision | Keep REST; retain exact publication/operation evidence and handle state. |
| Doctor | `doctor` / `doctor --read-only` | POST `/diagnostics`, keyed | Registry for both modes; preserve reader/writer and Hub-contact differences. |
| Prune/recover dry run | `prune --dry-run`, `recover --dry-run` | POST `/prune-plans`, `/recovery-plans`, keyed | Capture notices and prevent uncertain repeat; preview is not apply authority. |
| Prune/recover apply | `prune --apply`, `recover --apply` | POST `/prunes`, `/recoveries`, keyed writer | Fix error-based uncertainty guard; retain confirmation and server policy/lock revalidation. |
| Repair | `repair TYPE:ID@SHA [--reason TEXT]` | POST `/repairs`, keyed writer | Shared persistent handles; no automatic replay; existing integrity and guard restrictions. |
| Run reports | Host `runuser` + `ls`/`cat` under `/srv/hfcache/runs` | GET `/runs`, `/runs/{run_id}` | Add narrow proposed CLI `runs list/show`, then migrate UI and amend CP-01/09. |
| Operation recovery | Copy native `hfcache` commands; local tab handles | GET `/operations/lookup`, `/{id}`, `/{id}/events`, `/{id}/result` | In-page lookup/wait using same protected profile; scoped persistent handles; no cancellation. |
| Unit/timer state | Cached system D-Bus + silent polling failures | Intentionally none | Close-aware lifecycle, bounded read retries, unknown/stale state; fixed system manager only. |
| Sync schedule | Fixed system timer and drop-in shell/file operations | Intentionally none | Profile-aware refusal before writes; validate calendar; never enable verify timer or operate target. |
| Unit/run journal | Host journal APIs | No REST log-stream endpoint | Retain labeled bounded host diagnostics; no invented REST SSE or domain inference. |
| Tags in configuration | Existing form/text candidate pipeline | Existing candidate validation plus catalog routes | Preserve exact bytes/tag-only confirmation; this plan adds no new discovery surface. |
| MCP | Not the Cockpit write transport | Separate read-only protocol | No change; credentials and trust boundary remain separate. |

## Interpreting permission and state

Cockpit administrative access permits particular host work; it is not the REST
writer credential, a daemon readiness signal or archive-write approval. A REST
writer credential does not clear the read-only guard. A scheduled service is an
observer, not the server operation itself. A 202 is admission, a result Envelope
is the outcome, and journal text is only diagnostic. Keep those facts separate
in every button predicate and status label.
