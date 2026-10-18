# Keep a narrow release around a durable compatibility change

- Decision identity: 079.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Context, decision and consequences

The historical 0.1.3 patch release isolated nullable corrupt-current findings
from unrelated nondurable changes. Cross-version readers then differed for one
known cause: older derived-catalog readers lost the degraded signal. That
compatibility limit belongs beside the prune-in-flight rollback rule, rather than
being hidden by a broader release claim.

The version matched the tested/staged/deployed artifact and deliberately did not
claim outstanding consumer, reboot, data-protection or calendar acceptance.
Original release provenance remains below; current scope is recorded separately
in the changelog and deployment status.

## Provenance and governing evidence

The source entry first appears in
[4dd886e](https://github.com/wtcross/hfcache/commit/4dd886ed8982688bbad05cf71c85079e460b695d)
(2026-07-27, `release preparation: build, check, deploy, and tag 0.1.3`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[CHANGELOG.md](../../CHANGELOG.md).

Implementation or shipped-artifact evidence:
[pyproject.toml](../../pyproject.toml),
[scripts/install-release.sh](../../scripts/install-release.sh).

Verification or recorded operational evidence:
[recorded deployment scope](../deployment-status.md).


## 2026-10-18 data-preserving local rollout amendment

[Decision 126](decision-126.md) records new local-host release/rollout authority
with an absolute NAS content/metadata-write ban and no other-host changes. Retain
artifact identity, actual-executor quiescence and state/lock preservation; live
sync/full verification/archive-write acceptance is forbidden and remains NOT RUN.
Any local deployed tag records this partial acceptance explicitly. No remote push
or ACME issuance is authorized. Rootless runtime design/proof belongs to rootless runtime.
