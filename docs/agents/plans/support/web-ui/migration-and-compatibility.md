# Migration, compatibility and retirement requirements

## Source work versus deployment

This plan authorizes source implementation and disposable test execution only after the kickoff prompt is issued. It does not authorize another production rollout. The reviewed repository records guarded rootless 0.2.2 from application source `1c68501`; original configuration/candidate/backup/locks/stores/handles/secrets, NAS read-only, writer masks and disabled calendars remain. Do not revive any historical broad host permissions from prior progress entries.

Implement packaging and human deployment procedures, and prove them on disposable local/native/rootless test targets. Real deployment, Caddy reload, credential rotation, service changes, remote publication/tagging, NAS access and clearing holds require a later explicit operator instruction. Completing this plan can establish implementation readiness and fixture acceptance without claiming production migration has happened.

## Release unit and provenance

A coherent release comprises the Python wheel/locked optional closures, static UI artifact, UI/backend schema contract identity, native/rootless role templates, Caddy template, privileged-helper protocol/build, release installer and per-file artifact index. Update the existing build/stage/install/verification flows, not an untracked 'copy dist beside the server' script. Native assets reside in the immutable release directory; rootless API image contains the verified assets. Base and server-only installations retain their supported dependency boundaries. Enabling UI with missing/mismatched assets fails clearly.

Keep current TLS termination and API/MCP addresses unchanged. No additional Caddy container, application port, development server, CDN, or global Basic layer is introduced. Caddy sees the existing Unix API upstream only. Its secret/network/mount boundaries stay unchanged. The API receives only the new protected Basic hash and narrowly scoped helper socket where enabled; the verifier receives neither. Review/re-pin artifact hashes and all affected strict role schemas rather than bypass their validation. Reuse old Caddy image where unchanged; don't rebuild it solely to house frontend files.

## Compatibility checks before feature completion

Run actual installed old base CLI, REST writer/reader and MCP clients against the new server on owned fixtures. Preserve old route response schemas, capability fields, operation class grammar, candidate APIs, JSON Envelopes, no-Origin bearer behavior and separate MCP allowlist. Capture additions must not silently break old refresh/sync results. Do not substitute newly compiled source under an old version string for a compatibility test. Record exact source, wheel and dependency closure.

Run old supported binaries against fixture copies containing new card adjunct/private helper/config-application state, tags and observation state. Document the true result: supported read, safe refusal, or incompatible observation. An additive directory or operation kind can still make a strict old parser refuse. Preserve all unknown state; never delete it to force old startup. Use the repository's required durable-format drill and compatible target backups. UI artifact omission must not break backend-only startup when UI is disabled.

Password/provider changes do not change the stable human subject or silently rebind operation ownership. Existing credential-class receipts remain class-scoped historical evidence; no retroactive human attribution. Future account/repository authorization is out of scope. Keep browser-operation registry schemas independently versioned and reject malformed/cross-authority restored entries.

## Existing Cockpit evidence and handoff

Before a real migration, the operator inventories unfinished operations, candidate/base/predecessor configuration, fixed client profile, effective host permissions, actual executor state and original locks. The future UI must offer lookup/observation by an operator-supplied original safe key/ID against the same verified authority. It cannot directly read Cockpit's browser session storage from another origin. Do not promise automatic migration of that browser state, invent handles, treat missing history as nonexecution, or replay work to recreate a result.

Keep configuration candidate/backup lock paths and ownership semantics stable, or design an explicitly tested, non-destructive adapter. A new helper must refuse conflicting/incompatible candidate state, not adopt/delete it silently. Its ownership of mutations and journals cannot overlap with still-active Cockpit writes without the original common lock and exact-byte guards. Test concurrent legacy/new config clients before retiring the plugin.

## Cockpit source/package retirement

WEB-025 happens only after all parity rows have executable coverage, real platform functional tests pass, new human documentation is usable, and compatibility/rollback has been exercised. It removes Cockpit as a shipped/supported UI and removes production dependencies on its bridge, while preserving generic API clients, runtime helpers, licensed reused code, relevant tests, historical plans/ADRs and rollback artifacts.

Create an inventory for each file/test/install hook before removal: retained generic behavior, moved reusable component/test, replaced and covered integration, legacy historical document, or retired plugin-only artifact. Update artifact allowlists/indexers/installers so new releases no longer require a Cockpit build. Port safety tests before deleting the old harness. Preserve uninstall/migration instructions and historical evidence. Do not uninstall the actual host's Cockpit package or remove global Cockpit services as part of source work. Other host applications may depend on them.

The new UI remains complete on supported profiles without opening Cockpit, running a browser shell, or forwarding to old plugin pages. A guarded profile's denied schedule/observer state is valid, but unsupported implementation is not a permanent excuse to drop positive native controls.

## Rollback runbook requirements

The human runbook must distinguish frontend-only selection rollback, complete application/host-helper rollback, and legacy binary/schema compatibility. It must preserve candidates/backups, both operation stores, helper outcome records, original key/ID handles, new card adjuncts, and old immutable release artifacts. Never rebuild old artifacts in place or reassign an existing release tag.

Before any authorized switch: prove actual executor drain and shared-lock ownership using the existing safe procedures; don't equate observer exit or free wrapper PID with completion. Preserve NAS read-only/guard and disabled timers unless separately authorized otherwise. Switch only compatible reviewed artifacts and config; confirm TLS/UI/REST/MCP, asset identity, server contract, helper policy and permission denials afterwards. If old binaries cannot observe new unresolved operations, rollback stays blocked or uses compatible observation; deleting history is forbidden. A failed/unknown change requires evidence-preserving operator reconciliation, not automatic replay/cleanup/forced kill.

A real deployment checklist is a handoff artifact. No box representing production acceptance is checked by this source plan or a disposable VM test.
