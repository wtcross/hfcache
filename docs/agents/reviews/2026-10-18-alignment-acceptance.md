# Final REST/MCP documentation and script disposition

Plan: [alignment](../plans/2026-10-18-plan-rest-mcp-docs-scripts-alignment.md).
Baseline: `65b65714b29e835498138ec3122b5669571850cf`.
Branch: `feat/rest-api-and-mcp`. This is source/offline acceptance, not a new
release or installed-host/NAS acceptance. Later user steering authorizes normal
feature-branch pushes to github and forgejo after the final commit; merge, tag,
deploy and production archive operations remain outside scope.

## Findings

| Finding | Final disposition and evidence |
| --- | --- |
| F01 | Human tracking removed across all guides and technical ADRs. Raw/rendered audience checks include encoded paths, references, HTML, literals, mixed-case/formatted IDs and stage introductions. `test_docs_alignment.py` includes failing fixtures; no leakage baseline remains. |
| F02 | README and human index route audiences; concise release notes retain version/date/rollback, while deployment-status owns dated restricted acceptance. Original transcripts and technical rationale are preserved under agent history. |
| F03 | Native installer requires positive native classification before staging/managers/candidate execution. Static help/list/dry-run are distinct. Rootless/reader/consumer paths have separate guides and role fixtures. |
| F04 | Current pinned UBI inputs, nested sockets, worker-created listener/notify readiness and dormant socket binding are explicit. Numeric runtime facts are compared with pins/templates/units; wrong base/socket/readiness fixtures fail. |
| F05 | Hardening import/default/help/dry-run perform no workload. Explicit disposable identity/root/UUID/lock/mount/sentinel/inode ownership precedes workload writes. No real kernel-setting denial writes remain. `test_hardening_probe.py` tests early refusal and cleanup. |
| F06 | Denial results distinguish pass/fail/not_proven; only relevant real errno establishes enforcement. Missing prerequisites/import/network/generic errors never pass isolation. Existing adversarial probe fixtures remain. |
| F07 | CLI help explains HTTP/control/Hub/archive effects. All command help is exercised without API construction; actual route/mode/capability/lock/effect fixtures retain independent expected inventories. |
| F08 | Five proven CLI migration seams removed/simplified in API-018 with public-contract replacements. Domain `ServiceResult`, bootstrap rendering and actual preflight/service allowlists retained. See the code ledger. |
| F09 | Quiet warnings/errors and retained handles remain; no-color controls real per-invocation rendering, and sanitized progress respects verbosity/TTY. `test_cli_diagnostics.py` and adversarial result/uncertainty tests pass. |
| F10 | REST, MCP and Hub sources are separate, with native named credentials versus fixed rootless files. Reader quickstart needs no Hub/archive settings. Legacy native reset example renamed/described as migration-only; no installed drop-in is changed. |
| F11 | Complete bounded collection or explicit failure replaces the false unbounded-local claim. CLI/API errors never fall back to local execution or replay. Existing pagination, budget, timeout and command-option rejection tests remain. |
| F12 | Cockpit fixed client/rendered settings, blocked legacy controls, exact candidate installation guards and host-local report-read exception are documented/tested. Independent NFS copying retains exact identity, full verification, retry and fresh destinations. |
| F13 | Every original script retained with supported purpose and test ownership; two new helpers included. Catalog and explicit inspection classifications require every helper once, including non-executable Python files. No unexplained candidate remains. |
| F14 | Gate executes parser-backed human links/anchors/audience/catalog checks; actual REST/MCP/role and model/default/bounds comparisons remain independent. Original migration and reference hashes are tested; old normative requirements have living homes. |

## Code and inactive artifact disposition

[Code ledger](../code-removals.md) retains the complete API-018 caller/replacement
evidence. Fresh source/tests/scripts/packaging/Cockpit searches confirm no `_emit`
or `run_job` definition/caller, no CLI preflight allowlist re-export, and no inert
color field. Those names survive only in historical evidence. Actual domain and
bootstrap uses remain and are covered by their public behavior.

The former `packaging/systemd/hfcache-sync.service.d/credential.conf.example` is
retained as `legacy-hub-credential-reset.conf.example`. It only resets obsolete
native scheduled-client Hub imports. Caller inventory found a unit-parser test,
the failure-example comment, technical ADR evidence and historical references;
no active installer, runtime entrypoint or rollback command installs it. The test,
comment, human native-upgrade instructions and current/historical link targets
are repaired; original history and source hashes remain. Installed files and old
release trees are untouched. Its explicit reset preserves migration utility
without describing credential provisioning it cannot perform.

## Supported helpers retained

The human [script catalog](../../scripts.md) owns exact invocation, effects,
dependencies and linked tests. This ledger records the final decision, not a
second operational reference.

| Helper | Outcome |
| --- | --- |
| build-caddy-container.py | Retain; pinned derivative/foundation evidence. |
| build-container.py | Retain; authenticated wheel/interpreter/locked closure build. |
| check-container-foundation.py | Retain; explicit disposable image proof, never routine inspection. |
| check-container-worker.py | Retain; explicit owned worker/peer/isolation fixture proof. |
| check-hardening.sh | Retain; static inspection and explicit profile/identity-guarded workload. |
| check-installations.py | Retain; three independently locked wheel profiles in the gate. |
| check.sh | Retain; provider-neutral quality/build/Cockpit/optional smoke gate. |
| consumer-serve-hfcache-model.sh | Retain; independent verified-model serving with explicit engine effects. |
| container-service.py | Retain; fixed rootless roles and non-killing drain. |
| fetch-container-python.py | Retain; explicit authenticated build-input fetch. |
| hardening-probe.py | Retain; safe import and scoped disposable evidence classification. |
| hfcache-client | Retain; fixed supported rootless host entrypoint. |
| hold-readonly-guard.py | Retain; independent original-flock/host-mount safety policy. |
| install-container-release.py | Retain; protected immutable stage/select binding and guard checks. |
| install-release.sh | Retain; supported native-only stage/list/switch path. |
| release-functions.sh | Retain; sourced native quiescence/rollback library. |
| setup-hfcache-consumer-model-store.sh | Retain; independent store ownership/capacity provisioning. |
| release-profile.py | Added in OPS-021; positive native layout classifier. |
| check-docs.py | Added in DOC-018; offline documentation/interface alignment. |

No helper was deleted. Keep native named-FD3 activation, scheduled client handles,
receipt stores, actual domain services, MCP auth/lifespan helpers, independent
consumer copy/store/serving tools and Cockpit's direct report browser. The dormant
rootless socket remains indexed and protected; a disabled artifact is not dead.

## Authority and preservation

- One selector: `docs/agents/plans/current.md`; task records own execution status.
  Forty-seven relocated records retain original identity/hash and collision-free
  destination. Process ADRs/invariant preserve their identifiers in the agent area.
- All 227 baseline Markdown documents have accounted current homes. All 177
  pre-rewrite references have original Git hashes and current snapshot hashes.
  One historical link target changed for the inactive example rename; its hash
  was deliberately updated without changing original-source provenance.
- [Historical contract coverage](../historical-contract-map.md) maps every old
  plan section to current authority. Bulk manifest migration retains the backup
  and explicit-command safeguard. Checkpoint table shapes/names/order remain.
- AD-05/FS-20 retain the lifetime-generation requirement and disclose the existing
  allocator conformance gap. No retention backlog or other historical task is
  activated. Archive JSON, transport wrappers, MCP projection, receipts, handles
  and deployment configuration remain separate compatibility domains.

Historical progress references describe the contracts at the time of each entry.
Current contracts govern behavior; preserved references/Git establish historical
acceptance rather than making current headings an implementation archive.

## Final validation ownership

DOC-019's task and completed progress entry record the final full gate results.
This audit does not count static review or an interrupted check as a pass.
Live Hub/NFS, installed PID1/cgroup/SELinux, other-host, browser and calendar
acceptance were not run. Existing guard, NAS-ro state, original locks, masks,
credentials, both operation stores and scheduled handles remain unchanged.
