# Migration, compatibility and retirement requirements

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `cef766abdfd7ff51defe28cca67c8204505811518a08432f4b35afce8b7d3a48`,
original content SHA-256 `a583a5122af767e4d0493d8b7f68de6cd214ad5557b3c76a5d0fedd723a0904a`.
Historical proof hashes identify the original artifacts, not this edited record.

## Source work versus deployment

This plan authorizes source implementation and disposable test execution only after the kickoff prompt is issued. It does not authorize another production rollout. The reviewed repository records guarded rootless 0.2.2 from application source `1c68501`; original configuration/candidate/backup/locks/stores/handles/secrets, NAS read-only, writer masks and disabled calendars remain. Do not revive any historical broad host permissions from prior progress entries.

Implement packaging and human deployment procedures, and prove them on disposable local/native/rootless test targets. Real deployment, Caddy reload, credential rotation, service changes, remote publication/tagging, NAS access and clearing holds require a later explicit operator instruction. Completing this plan can establish implementation readiness and fixture acceptance without claiming production migration has happened.

## Release unit and provenance

A coherent release comprises the Python wheel/locked optional closures, static UI artifact, UI/backend schema contract identity, native/rootless role templates, Caddy template, privileged-helper protocol/build, release installer and per-file artifact index. Update the existing build/stage/install/verification flows, not an untracked 'copy dist beside the server' script. Native assets reside in the immutable release directory; rootless API image contains the verified assets. Base and server-only installations retain their supported dependency boundaries. Enabling UI with missing/mismatched assets fails clearly.

Keep current TLS termination and API/MCP addresses unchanged. No additional Caddy container, application port, development server, CDN, or global Basic layer is introduced. Caddy sees the existing Unix API upstream only. Its secret/network/mount boundaries stay unchanged. The API receives only the new protected Basic hash and narrowly scoped helper socket where enabled; the verifier receives neither. Review/re-pin artifact hashes and all affected strict role schemas rather than bypass their validation. Reuse old Caddy image where unchanged; don't rebuild it solely to house frontend files.

## WEB-023 and WEB-025 execution

Use the [bounded-testing policy](testing-strategy.md#web-023026-bounded-product-testing-and-effort)
and task-specific high effort. Reuse retained targets and owned fixture copies;
investigate actual compatibility/rollback gaps. Required real-client, drain,
preservation and independent new-web operation remain mandatory. The2026-11-01
user direction excludes further legacy plugin maintenance or validation.

## Compatibility checks before feature completion

Run actual installed old base CLI, REST writer/reader and MCP clients against the new server on owned fixtures. Preserve old route response schemas, capability fields, operation class grammar, candidate APIs, JSON Envelopes, no-Origin bearer behavior and separate MCP allowlist. Capture additions must not silently break old refresh/sync results. Do not substitute newly compiled source under an old version string for a compatibility test. Record exact source, wheel and dependency closure.

Run old supported binaries against fixture copies containing new card adjunct/private helper/config-application state, tags and observation state. Document the true result: supported read, safe refusal, or incompatible observation. An additive directory or operation kind can still make a strict old parser refuse. Preserve all unknown state; never delete it to force old startup. Use the repository's required durable-format drill and compatible target backups. UI artifact omission must not break backend-only startup when UI is disabled.

Password/provider changes do not change the stable human subject or silently rebind operation ownership. Existing credential-class receipts remain class-scoped historical evidence; no retroactive human attribution. Future account/repository authorization is out of scope. Keep browser-operation registry schemas independently versioned and reject malformed/cross-authority restored entries.

## Legacy deprecation and independent web operation

After compatibility, new-web workflows and usable documentation pass, WEB-025
records proportional deprecation and handoff. The new UI works independently
without opening historical frontend or forwarding to old plugin pages. New-web safety
coverage and supported native controls/rootless denials remain required.

## Rollback runbook requirements

The human runbook must distinguish frontend-only selection rollback, complete application/host-helper rollback, and legacy binary/schema compatibility. It must preserve candidates/backups, both operation stores, helper outcome records, original key/ID handles, new card adjuncts, and old immutable release artifacts. Never rebuild old artifacts in place or reassign an existing release tag.

Before any authorized switch: prove actual executor drain and shared-lock ownership using the existing safe procedures; don't equate observer exit or free wrapper PID with completion. Preserve NAS read-only/guard and disabled timers unless separately authorized otherwise. Switch only compatible reviewed artifacts and config; confirm TLS/UI/REST/MCP, asset identity, server contract, helper policy and permission denials afterwards. If old binaries cannot observe new unresolved operations, rollback stays blocked or uses compatible observation; deleting history is forbidden. A failed/unknown change requires evidence-preserving operator reconciliation, not automatic replay/cleanup/forced kill.

A real deployment checklist is a handoff artifact. No box representing production acceptance is checked by this source plan or a disposable VM test.
