# Decision 132 — Positively classify native releases before effects

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-10-18 |
| Amends | [Native lifecycle](decision-121.md), [diagnostics](decision-131.md) |

## Context and decision

Native and rootless releases share an install prefix and service names but use
different executables, managers and credential delivery. An acknowledgement or
the absence of one recognized container marker cannot establish native authority.

Use one standard-library, read-only layout classifier before native staging,
switching, manager calls or probe interpreter execution. Require ordinary native
project/version, Python pin, locked project and application sources; installed
releases also require a built environment. Permit managed venv Python symlinks
without executing them for classification. Require an exact internal current
selector; refuse dangling/external/unknown selectors, container markers, mixed
layouts, unknown JSON release metadata and incomplete installed releases.
Validate existing ancestors even for a fresh prefix. Use the classifier's parsed
project version for staging so a second parser cannot select another destination.
Validate source, current and an existing destination before mutation; repeat
current/target validation inside the atomic-switch library path. Fresh native
installation remains supported with positive source or built-target evidence.

## Rationale and alternatives

Executing the candidate interpreter to ask its profile runs code before the
boundary is established. Inferring native from missing container metadata turns
partial or unfamiliar releases into authority. A new durable marker is unnecessary
because existing source/lock/environment evidence provides a positive layout
contract. Layout classification does not authenticate artifacts or prove quiescence;
existing immutable-input, actual-executor and original-lock guards still apply.

## Consequences and evidence

Help/list/dry-run remain non-mutating inspection and can run without source,
root, archive, manager or secrets. Dry-run is intent only. Rootless tooling keeps
fixed roles, user-manager selection, file-mounted secrets, worker readiness and
the dormant socket binding; native named-FD3 activation remains supported.
No schedule, observer handle, operation store or lock lifetime changes.

See [script profiles](../scripts.md), [classifier](../../scripts/release-profile.py),
[installer tests](../../tests/unit/test_release_installer.py),
[diagnostic tests](../../tests/unit/test_hardening_probe.py) and
[safe help tests](../../tests/unit/test_script_help.py).
