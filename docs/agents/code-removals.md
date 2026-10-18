# Code disposition ledger

## API-018 — CLI rendering and observation remnants

Branch-wide source, tests, examples, scripts, packaging and Cockpit searches at
`db55170` found these dispositions. No external compatibility API was documented
for these renderer/migration seams. Current public CLI/transport behavior is the
replacement coverage; domain services and bootstrap output remain.

| Symbol | Callers and decision | Replacement evidence |
| --- | --- | --- |
| `cli._emit` | Definition only; removed. | Public local version/bootstrap and remote result tests. |
| `cli_client.run_job` | Definition only; removed. Current CLI uses explicit `submit_job`/`observe_operation`. | Public single-POST, retained-key/ID, timeout, uncertainty, detach and reconnect tests. |
| `_show_result(ServiceResult)` | Every real caller passes an Envelope. Remove the union/reconstruction branch and obsolete `started_at`/`human_errors` inputs. | Exact server result identity/data/exit and quiet/JSON diagnostics tests. |
| `cli.UNPROVABLE_READ_ONLY` | One test-only consumer; removed CLI re-export and import from defining `services.requests` there. | Keep real preflight/service consumers and preflight's supported re-export. |
| `GlobalOptions.color` | Assigned but never read; removed. Three test constructions updated. | Supported per-invocation Typer plain-help and Click context controls; forced-color help/output tests and later-invocation isolation. |

Keep `emit_envelope`, `ServiceResult` in bootstrap/domain code, `cli_client.problem`,
actual service functions and the real preflight allowlist. No operational fallback,
receipt schema, public command, job replay or MCP tool change.

CLI interface chronology removed from the human introduction is preserved in
[historical amendments](history/cli-interface-amendments.md). Current help explains
dispatch and four effects: HTTP, local control state, archive mutation and Hub use.
