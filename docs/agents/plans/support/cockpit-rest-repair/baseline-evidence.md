# Revalidated baseline (2026-10-19)

HEAD and reviewed source both equal `dcc2c562b52304541d0cb85d20fc046072038e79`.
`rtk git diff dcc2c562b52304541d0cb85d20fc046072038e79 --stat` was empty.
Only the user-imported plan/support/tasks were untracked at startup. No other
active plan was selected. A full tracked/untracked text scan excluding that bundle
found no CPR ID collisions. The dedicated branch was created without discarding
files. Decision 134 was allocated after inspecting the actual indexes (last 133).

## Reproductions

Command: `rtk node --experimental-strip-types docs/agents/plans/support/cockpit-rest-repair/baseline-reproduce.ts`
(exit 0, Node v24.18.1). Actual runner and candidate pipeline imports, synthetic
inputs, no host commands or archive access:

- F01: Error("reconnected") plus problem/status/signal loses all structured fields;
  plain rejection also loses its message and becomes no-terminal-envelope.
- F02: failed `config validate`, HFAPI003, data={} becomes generic incompatible
  validation; write/validate ran, preview did not. Original API error is lost.
- F05: exact baseline predicate, old successful dry run, applied=null and caught
  error with original key/ID yields uncertain=false and canApply=true. This is
  predicate-only investigation, not mounted component acceptance.
- F04: source checks confirm mountOnEnter/unmountOnExit with hook-local handles.
  This is source lifetime evidence, not a rendered lifecycle pass.

The fixture is intentionally outside the default test suite: later regression
assertions belong to each owning repair, rather than committing a red gate.

## Current surface and discrepancy map

The imported audit and surface map describe this exact source with no drift.
Rechecked runner.ts structured failure loss; config-pipeline.ts unconditional
assessment parsing and generic install catch; hooks.ts local handles and swallowed
poll failures; api/systemd.ts immortal cached D-Bus; maintenance.tsx Apply predicate;
app.tsx tab unmount; sync.tsx/verify.tsx full system-service starts;
api/archive.ts host report reads; dashboard.tsx/verify.tsx missing read alerts.
F07/F08 are explicit existing contract choices requiring amendments, not accidental
violations. Reports already have REST/SDK routes but no runs CLI adapter.

Validate pipeline: guarded candidate write -> guarded synchronous REST validate ->
optional guarded keyed REST plan -> guarded host install/backup -> exact guarded
installed confirmation. The initial write is a host effect; plan is an admitted
Hub-contacting job; validation alone has no operation receipt.

The launcher remains fixed to hfcache-client/client.toml/rootless UDS. The container
helper binds the whole config directory and overlays protected client settings.
No missing candidate mount or incorrect native socket was established. Existing
strict streams, nonzero Envelopes, no-cancel observation and exact tag-only byte
confirmation remain required. See decisions 122/127/133/134 and CP-01–14,
INV-006 and workflow INV-011. No archive/durable format/runtime dependency change.

## Diagnostic identity and unavailable evidence

Application/CLI source is the reviewed SHA; Node v24.18.1, pnpm 11.18.0 are present.
Physical installed launcher/profile, runtime images, API/client runtime versions,
Cockpit/PAM/session and actual installed browser bundle were NOT INSPECTED: the
user prohibits production inspection. Recorded deployment docs describe guarded
rootless 0.2.1 from 4088994, not current runtime proof. Package version alone
cannot show artifact parity. No production credentials or live archive were used.

No separately provisioned disposable Cockpit/PAM/systemd/rootless environment was
provided. Required V54 runtime evidence remains blocked until an isolated target
with immutable fixture artifacts, synthetic credentials and no live/NAS archive
is explicitly provisioned. No original installed failure stage/root cause is
established. Do not treat source fixes as installed symptom resolution.

## Later local-host authority

The user subsequently authorized local-host development, service outage and
necessary backed-up/restored installation changes, provided NAS data is unaffected.
No host mutation has yet occurred. Prefer independent disposable fixtures and
preserve the existing guard-held operation. The original no-inspection limit
above describes baseline evidence collection, not a denial of the newer authority.
Provisioning feasibility remains under investigation; it is not a runtime pass.

Read-only local fixture feasibility: CentOS Stream 10, Cockpit 364, Podman 6.0.2,
Firefox 140.13.0esr, SELinux Enforcing. /dev/kvm and nested KVM are available;
QEMU/qemu-img/libvirt/virt-install/systemd-nspawn/machinectl are absent. A full
isolated guest with its own filesystem/PID1/system bus can preserve the fixed
launcher paths without touching installed host state. Additional host accounts
alone cannot isolate those fixed global paths. Provisioning tools plus a reviewed
guest image/local fixture release is the next runtime prerequisite. No tools were
installed, no guest created, no service/credential/guard/mount state changed.


### Mounted baseline investigation

`rtk node docs/agents/plans/support/cockpit-rest-repair/baseline-browser.mjs`
exited 0 in Firefox 140.13.0esr, using actual Maintenance/QueryError/hooks/API
adapter/runner with only the Cockpit process boundary controlled. Bounded artifact:
[baseline-browser-evidence.json](baseline-browser-evidence.json).
Actual DOM clicks dry-run -> Apply -> confirmation produced exactly one synthetic
Apply; after its key/ID and `reconnected` failure, Apply was enabled again.
The mounted validation QueryError lost problem/stage and showed generic guidance.
Unmount/remount lost local handles and issued zero new calls. This is a real
component root lifecycle reproduction, not the Application tab acceptance test,
real API/PAM/launcher proof, or satisfaction of repaired V01/V24/V27 expectations.
The owned loopback server/browser exited; no application command, production
credential, host configuration, NAS or live archive was accessed. No sandbox was
weakened. The private temporary browser profile is retained as fixture evidence.
