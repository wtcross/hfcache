# WEB-014: Render archived README cards as inert, bounded React content

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-013](web-013-publication-detail-pages.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-014: <completed outcome>` |

## Read before implementation

Card endpoint/decoder; architecture card/XSS policy; react-markdown primary docs at pinned version; details Overview layout.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Integrate react-markdown/GFM with an explicit reviewed sanitizer allowlist and custom link/image/heading components. Disable raw HTML and MDX, unsafe protocols, embedded script/style/SVG/iframe/form/object and dynamic content. Do not use dangerouslySetInnerHTML or load plugins, fonts/images/scripts from card references. Represent external media as labelled placeholders and rewrite safe relative navigation against exact upstream commit/type identity with no opener/referrer.

Render capture/source/provenance/limited-content status prominently. Provide rendered and sanitized-source views, clearly identifying redaction and derivative content. Hide front matter from the rendered prose only through a safe bounded parser; supported metadata already comes from attributed extraction. Unsupported Markdown constructs degrade to inert text or a clear state, never looser execution.

Enforce finite input/parse/render work, table/code block/heading limits and accessible overflow. A malicious card cannot freeze the page, clobber navigation identifiers, mutate page state, read credentials or call same-origin management endpoints. Rendering errors stay local to the card and do not break operations recovery.

## Unit and component validation

Test hostile Markdown/HTML/MDX, mixed-case/control-encoded javascript/data/blob URLs, attribute injection, SVG/forms, DOM clobbering, deeply nested/tables/code limits, invalid encodings, relative URLs and redacted source view.

## Integration validation

Run real captured cards through API decoders and renderer with normal/partial/missing/oversized/mismatched fixtures. Verify CSP and no-store headers, no unsanitized alternative route, and no GET-triggered payload read.

## Functional validation

In all three engines through Caddy, inspect actual DOM, CSP violations and network requests while displaying hostile cards. Assert zero executable/script/frame/form/external-resource effects and no mutation request. Verify keyboard/link behavior and graceful bounded failure.

## Human documentation deliverables

Complete readme-cards.md: offline provenance, supported formatting, blocked media/links, source toggle, missing capture and explicit refresh, upstream claims versus verified archive evidence. Update security dependencies and examples.

## Acceptance

Useful README content displays safely for model/dataset publications, including hostile inputs, without external requests or execution; source view cannot reveal unsuppressed credentials.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-014, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
