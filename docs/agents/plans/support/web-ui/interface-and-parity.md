# Interface behavior and Cockpit replacement checklist

## Navigation and repository detail

Use the approved prototype's persistent sidebar and dense information layout. Library is the default workspace; retain global connection health, deployment restriction notices, and unresolved-operation recovery across route changes. The four workspaces share the same shell and keyboard/focus conventions.

Library: All/Models/Datasets; configured/archived/all scope; current/retained evidence scope; ID/tag text; all/any tags and configured-versus-historical tag source; formats; model-only method/scheme/bits/maximum weight bytes. Reflect filters in the URL and use exact backend filter grammar. Search is not full-text README search. An unmanaged repository remains visible and its upstream link stays type-aware. Use server-qualified counts/coverage, not global numbers invented from a page. A filtered operation acts on explicit reviewed canonical identities, not a hidden changing search result or a not-yet-loaded page.

Repository detail: stable type/ID route, full SHA and publication ID in URL/state for exact selection, current pointer resolution as a separate read, visible selection and provenance. Tabs: Overview, Variants or Dataset details, Files & manifest, Revisions, Integrity, Activity. Changing revisions invalidates old in-flight responses and swaps all publication-derived panels together. Do not mix latest tags, an old README, and newer verification into an apparently single publication snapshot. Current configured tags are explicitly current even when viewing older retained publications.

Overview: sanitized archived README beside archive/publication facts and attributed upstream task/language/license/base-model declarations. Integrity and metadata coverage are separate panels. For models show supported variant roles, member count, bytes, format, encoding, quantization, bits/group size, completeness, evidence and diagnostics. Unknown bits remain unknown (not zero or a guessed value); format and method remain separate. Datasets show only static format/config/split/feature declarations, not model fields, inferred row counts or executed samples. README-authored performance/specification statements are visibly upstream-authored, not verified hfcache metadata.

Files are manifest metadata, not a raw-file browser. Copyable consumer locators stay labelled relative to their documented base. No browser weight download, automatic shell execution, archive mount, or arbitrary file endpoint. Preserve budget failures explicitly; virtualized UI does not remove server limits.

## Operations and maintenance

Manual full/selected sync, sizing preview, diagnostics, metadata refresh and verification use existing keyed REST jobs. Show action scope, possible Hub contact, archive/control effects, original operation identity, event gaps and exact terminal outcomes. Poll only while useful, with finite backoff and independent observation state. Stop observing is not Cancel. A disconnect banner links the original observation; navigation cannot erase a failed or unknown state.

Maintenance exposes existing preview/apply flows for prune, unmanaged purge, recovery, quarantine cleanup, and exact-SHA repair from findings. Each destructive apply requires fresh server checks and a separate explicit confirmation; previews are not irrevocable authority. No automatic recovery/prune/repair from an error. Retention shows the current policy and one-round behavior, not a fabricated 'delete everything old' button. Lowering retention or removing/disabling config does not immediately remove data. Quarantine accepts only explicit validated known transaction identifiers; no arbitrary path input or directory scanner is added.

All classified errors remain visible with operator-oriented next steps. Preserve 0/10/20/30/40/50 domain classifications, HFMNT010 busy, operation-history uncertainty and per-repository partial results. HTTP 200 does not override a failed Envelope. Verification confidence is exact-publication evidence, never 'API healthy', source hashing, card capture, or variant completeness.

## Administration and tags

Provide structured repository/global configuration editing and a safe advanced view for supported nonsecret fields. Read server-supported field constraints rather than duplicate validation logic. Use an explicit dirty draft, reviewed diff, validation, required sizing preview, guarded apply, and exact installed confirmation. Editing after validation invalidates readiness. Browser navigation prompts before discarding a dirty draft. Store no drafts in recovery storage or browser persistent storage by default.

Tag chips have add/remove and normalized suggestions from existing facets. Enforce documented normalization and 64-tag limit both client-side for feedback and server-side for authority. Current configuration tags are editable; last-observed/unknown unmanaged labels are read-only. Bulk label edits, if implemented for selected configured rows, are one reviewed configuration transaction using the same endpoint; there is no independent tag database. Tags never silently modify selection, retention, schedule, permissions, or operational fingerprint.

Host panel reports effective permissions, profile/release identity, read-only/unknown guards, actual fixed timer/observer status and bounded diagnostic journals. Missing helper or incompatible profile produces a clear unavailable/denied state. Unknown is not inactive/healthy. Sync schedule editing preserves calendar validation, exact managed drop-in, randomized delay, reset-to-shipped behavior and pause/resume semantics. Verification timer is read-only. Never control hfcache.target or redirect system actions to identically named user units. On the guarded rootless baseline, schedule/observer actions remain disabled with reasons until a separately authorized compatible binding exists.

## Parity register to complete before retirement

The implementation creates executable coverage references for every row below. No 'replaced by a link to Cockpit' counts as replacement. A denied control with its real reason is correct parity on a restricted profile; a universally missing supported control is not.

| Existing capability | Replacement source/workspace | Owner |
| --- | --- | --- |
| Archive health six fields, free capacity/reserve, repository states and warnings | Existing status/health; Library summary and Administration | WEB-012, WEB-019 |
| Managed/unmanaged repositories, retained publications, type-aware Hub links | Existing inventory/catalog/reference/manifest; Library/details | WEB-012, WEB-013 |
| Full and selected sizing/sync and operation observation | Existing keyed routes; Operations and contextual actions | WEB-011, WEB-016 |
| Original key/ID recovery across bridge loss, tabs and unknown outcomes | Persistent route-independent registry and authenticated observation | WEB-011, WEB-016 |
| Verification estimate/full/new/exact revision, findings/repair | Existing estimate/verifications/repairs; detail and Maintenance | WEB-016, WEB-017 |
| Doctor checks and classified partial failures | Existing diagnostics results; Administration | WEB-016, WEB-019 |
| Installed config, guarded candidates, backup/apply/confirmation | New narrow config management; Administration/tag editor | WEB-007, WEB-008, WEB-015 |
| Sync timer display/pause/resume/calendar/delay/reset | Fixed host bridge, proven system-manager binding | WEB-018, WEB-019 |
| Verification timer status and disabled reason | Read-only host status; Administration | WEB-006, WEB-019 |
| Stop a proven scheduled sync observer without cancelling accepted work | Fixed host action with exact observer proof | WEB-018, WEB-019 |
| Bounded journal diagnostics, separate from job outcome | Fixed source allowlist and paged diagnostics | WEB-018, WEB-019 |
| Run reports list/exact read | Existing REST runs; Operations/details | WEB-016 |
| Prune/recovery/repair and existing additional REST maintenance | Existing previews/applies; Maintenance | WEB-017 |
| Safe version/build/profile presentation | Existing version plus independent UI build/bootstrap and host status | WEB-005, WEB-019, WEB-021 |
| Administrative locks and forbidden actions explained | Internal permission policy plus guarded adapter | WEB-004, WEB-006, WEB-019 |
| No credential editor or browser API/Hub bearer | Native Basic authentication and separate server-provisioned sources | WEB-004, WEB-005 |

Explicitly out of UI scope: archive initialization/reinitialization, arbitrary host administration, terminal execution, live model inference, enabling verification scheduling, and general payload serving. Keep CLI/MCP and native/base installation support. Do not remove generic client/runtime helpers because Cockpit uses them; classify all call sites before retirement.
