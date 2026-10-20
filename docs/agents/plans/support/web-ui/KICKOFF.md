# Execution kickoff prompt

Copy the following prompt into the coding agent running in the repository after extraction. Issuing it authorizes implementation within the stated limits.

```text
Implement the hfcache web UI replacement plan in:

docs/agents/plans/2026-10-20-plan-web-ui.md

This instruction authorizes activating the plan, implementing the scoped source changes, and running its owned local/disposable test environments. Work on a feature branch named feat/web-ui. Do not merge, push, tag, deploy, reload production Caddy, modify production services/timers/credentials/guards, access live NAS contents, or uninstall the live Cockpit plugin. Prior rollout permissions do not carry forward.

Start with AGENTS.md, git log/status, docs/agents/plans/current.md, relevant progress/Operator handoff, and the planning/workflow/environment contracts. Reconcile HEAD with the bundle's reviewed baseline 6b8fae2e0997403ae5c716a2e92148af0a972af9; do not reset to it. Preserve unrelated work and existing plan/task history. Check WEB work-package ID collisions, activate this draft without silently abandoning another active plan, then select WEB-001. Treat the extracted bundle as intended new plan files, not disposable scratch.

Execute the task records in dependency order. Follow the bundled architecture, API contract, interface/parity, testing, acceptance-matrix, documentation and migration specifications. The approved prototype is a design reference with fictional data, not production implementation or authoritative API behavior. Resolve necessary implementation details conservatively within scope and record contract/invariant/ADR decisions before or with the affected behavior. Split oversized tasks into new work packages with explicit dependencies rather than skip required work.

The React SPA must use strict TypeScript and runtime-validated typed API payloads. Serve its authenticated static assets from the hfcache API application behind the SAME EXISTING Caddy instance, TLS endpoint and Unix upstream used by REST and MCP. Do not add a second Caddy/frontend server/public listener or runtime Node process. Preserve existing REST bearer and read-only MCP authentication; do not apply a global Basic gate at Caddy. Add one protected Basic-authenticated human administrator through a replaceable principal/authorization boundary, enforce browser CSRF and server-side permissions, and retain deployment restrictions.

Preserve hfcache's complete snapshots, exact SHA/publication identity, configuration-backed tag provenance, archive/verification safety, original operation handles, no-replay uncertainty, fixed-manager host controls and guarded atomic configuration application. README rendering must use bounded publication-pinned captured metadata with no executable HTML/MDX, arbitrary payload serving, remote asset fetching or GET-triggered refresh. Implement only demonstrated missing capabilities; do not import unrelated downloader features.

Unit/component, integration and FUNCTIONAL testing are mandatory throughout, not deferred. Functional acceptance must exercise production-built UI -> real Caddy with trusted test TLS -> real installed API/services, plus actual isolated native/rootless host-helper/worker behavior. Preserve existing CLI/MCP/backend regressions. Mocks alone, skipped browsers/guests, weakened security and synthetic storage presented as live NAS proof are unacceptable. A missing required prerequisite blocks the task; record its unblock condition and continue only genuinely ready work. Do not retire Cockpit source/packaging until full parity, compatibility and real functional acceptance pass.

Create and update HUMAN USER AND OPERATOR documentation with each feature, including safe procedures, explanations, exact labels, examples and troubleshooting. Agent plans/progress/ADRs do not substitute for user guides. Keep the API/server/security/config/discovery/schema/deployment/container/script references and human navigation aligned; run documentation checks throughout.

For every work package, run the existing scripts/check.sh gate and all required strict frontend/integration/functional/docs checks, record actual test IDs/results/artifact identities and invariant/ADR review, update the task/current plan/progress/handoff, then commit WEB-NNN: <outcome>. Keep one work package per commit. Never claim a test, installation or production acceptance that was not performed. Resume interrupted work by reconciling git and original evidence, not by replaying operations.

Finish only when the final strict gate scripts/check.sh --require-web --with-build --with-web-functional passes with all required acceptance scenarios covered and no required skips, human guides are complete, and Cockpit is no longer a shipped UI dependency. Close the plan/current selector consistently and provide an implementation summary, exact validation evidence, remaining production-only acceptance steps and safe deployment/rollback handoff. Do not perform that production rollout or publish the branch.
```
