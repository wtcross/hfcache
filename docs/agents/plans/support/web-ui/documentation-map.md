# Human documentation requirements

The primary audience is **people who use and operate hfcache**. Agent plans, progress logs and ADRs are required audit material, but do not substitute for human guides. Documentation is created and updated in the same work package as behavior. WEB-024 is a final walkthrough/polish gate, not the first documentation task.

## 1. Information architecture to create

Create a human-facing `docs/web-ui/` section, indexed from `docs/README.md` and the root README. Proposed guides:

| Guide | Reader's question and required content | First owning tasks |
| --- | --- | --- |
| `README.md` | What is the UI, where do I open it, and which workspace should I use? Include the shared Caddy entrypoint, supported scope, Basic login, read-only versus permitted states and clear navigation. | WEB-001, WEB-005 |
| `library.md` | How do I find a model/dataset? Explain configured/archived/current/retained scopes, exact ID/tag search, all/any filters, technical coverage and zero-known-matches. | WEB-012 |
| `repository-details.md` | What do publication, variant, integrity and metadata labels mean? Explain SHA versus publication ID, repair, files/manifest locators, dataset declarations, and unknown fields. | WEB-013 |
| `readme-cards.md` | Where does the displayed README come from? Explain pinned offline capture, missing/oversize/redacted/unsupported states, explicit refresh and blocked external media. | WEB-009, WEB-010, WEB-014 |
| `configuration-and-tags.md` | How do I add/disable/remove repositories, edit tags, preview and apply safely? Explain normalization, current versus historical tags, dirty drafts, protected fields, stale conflicts, exact confirmation and no implicit deletion. | WEB-007, WEB-008, WEB-015 |
| `operations.md` | How do I sync/verify/diagnose, observe results and resume after disconnect? Explain original handles, admission versus completion, warnings/partial/integrity failures, no cancellation, and lost-history uncertainty. | WEB-011, WEB-016 |
| `maintenance.md` | When and how do I preview/apply prune, purge, recover, quarantine or repair? Explain prerequisites, scope, confirmations and stop conditions. | WEB-017 |
| `administration.md` | Which host controls are available and why might they be disabled? Explain supported profiles, policy provisioning, fixed systemd schedule/observer semantics and journals as diagnostics. | WEB-006, WEB-018, WEB-019 |
| `deployment.md` | How do I provision one Basic user and serve the static UI behind the existing Caddy? Include protected hash input, compatible versions, asset identity, native/rootless differences, same origin/prefix, no extra port/server, TLS/CSRF and validation. | WEB-004, WEB-005, WEB-021 |
| `troubleshooting.md` | What should I do for a login failure, HTTP/Envelope error, stale draft/cursor, missing card, unavailable helper, blocked profile or uncertain operation? Give safe checks, exact labels/codes, and escalation without replay/cleanup. | WEB-004 onward |
| `migration-from-cockpit.md` | How do I move to the independent web UI without losing operational capability or evidence? Include parity, handles/candidates, rollback constraints, preserved deprecated legacy material/live installation and production acceptance checklist. | WEB-021, WEB-023, WEB-025 |

These are target paths, not files already supplied as completed user documentation. Create each with functioning content when its behavior first exists; no placeholder guide presented as finished.

## 2. Existing documents that must remain aligned

Update `README.md` and `docs/README.md` for entrypoints and human navigation. Update `docs/api.md` for exact new routes, request alternatives, modes, permissions, effects, budgets, status codes and version transitions; keep independent route completeness tests. Update `docs/server.md` and packaging server examples for optional web/Basic configuration, protected credential delivery, startup behavior and CLI compatibility. Update `docs/configuration.md` only for actual application configuration behavior—server transport/auth remains a separate schema.

Update `docs/discovery.md` and `docs/schemas.md` for card adjunct formats, capture/refresh semantics, extraction versus integrity and compatibility. Update `docs/security.md` for Basic authentication, browser CSRF/XSS, content capture, new privileged-helper trust boundary, least privilege and residual whole-archive authorization. Review `docs/invariants.md`, related `docs/architecture.md` sections and ADRs in the same commit; preserve historical identifiers/reasons and append explicit supersession/amendment links.

Update `docs/containers.md`, `docs/deployment-centos-stream-10.md`, and packaging/build/install script contracts for asset artifacts, host-helper socket separation, role/secret matrices, native/rootless differences, same Caddy and immutable rollback. `docs/deployment-status.md` records only **actually observed** installed facts; feature tests do not change the recorded production version/acceptance. Do not put future implementation assertions into its current-status table.

Update `docs/development.md` with exact strict/unit/integration/functional commands, test infrastructure setup, safe fixture boundaries, no-skip rules and evidence interpretation. Update `docs/scripts.md` for every new executable helper/runner, including dependency/effect/inspection classification and safe help. Human guides may link to technical references, but must explain operator consequences in their own words.

Per the user's2026-11-01 instruction to ignore and deprecate the plugin once the
new web UI is complete, mark `docs/cockpit.md` and `docs/cockpit-plugin/` as
deprecated legacy with replacement guidance. Preserve source, history, licenses,
generic clients/runtime helpers and the live installation. Do not require more
plugin validation, inventory, harness ports, dependency cleanup or uninstall.
Human navigation leads to the independent web UI without claiming production
migration. Reference screenshots use only synthetic data, identify UI version,
have useful alt text, and match actual built screens—not this design prototype.

## 3. Style and safety standard

Write task-oriented procedures with prerequisites, the expected visible outcome, and safe failure/stop conditions. Distinguish read-only inspection, control-state creation, archive mutation, Hub contact, service changes and actual deployment. Use full labels users see in the UI. Explain 'publication', 'coverage', 'configured', 'last observed', 'busy' and 'execution unknown' before relying on them. Do not make readers understand work-package IDs or an agent's internal workflow to operate hfcache.

Avoid credential literals, passwords in argv, copied production endpoints/tokens, broad sudo snippets and unqualified 'run this' commands that start/stop the live archive. Password-hash examples use protected input and fake placeholders labelled nonfunctional. Do not suggest disabling TLS, SELinux, CSRF, no-follow checks or systemd hardening. A browser Basic user has no reliable application logout; state that limitation honestly. A guarded deployment does not become writable by signing in.

Examples explain account/profile context and do not assume UID 981 is the host user's identity. Port 8443 is the current Caddy endpoint, not a request to open an additional firewall port. Prefix examples must work for both empty and nonempty configured roots. Links to Hugging Face contain no credentials and distinguish dataset paths. Source/code examples in model cards are inert upstream text, not endorsed execution instructions.

## 4. Verification in every package

For WEB-024 use medium effort and the [bounded-testing policy](testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Reuse valid fixture evidence; update changed/missing guide steps without a new
documentation-test framework. Required examples, safety, accessibility and human
workflow outcomes remain; source availability is separate from deployment.

Run the repository's `scripts/check-docs.py` through `scripts/check.sh`. Test new human links/anchors, image paths/alt text, exact CLI commands without invoking effectful callbacks, server examples against strict models, endpoint matrix against actual routes and authorization, helper inventory coverage, and defaults/bounds against code. Do not execute every code fence—installation, service and NAS examples have effects. Keep independent golden expectations so generating both code and docs from a wrong schema cannot make the test vacuous.

For each feature's functional test, include at least one scenario that follows its human guide: a fresh user finds the correct view/action, understands the scope, completes or is safely refused, and sees the documented result. WEB-024 walks through login, Library filtering, exact publication/README, tags with conflict, sync/verification observation, reconnect, maintenance preview, and host restriction explanations. Record gaps and fix them before the task completes.

Each task's documentation section names created/updated guides and relevant reference contracts, or explains a genuinely documentation-neutral change. 'Will document later', an ADR alone, or an agent progress entry is not acceptable for a user-visible change.
