# CPR-004 disposable launcher diagnostics

Continues the exact isolated guest handoff in [runtime-003.md](runtime-003.md).
This is diagnostic preparation during the sole active CPR-004 package, not
CPR-008/V54 completion. Production installation, services, credentials, original
locks/guards/masks and NAS are untouched. All administrative mutations below occur
inside the owned guest. Local changes are confined to this record and ignored
`.local-fixtures/cpr-runtime/cpr004/` files.

The selected release, artifact index and application image are unchanged from
CPR-003: source `92f19b5a5991b1de3425d9ee3f92400253279cdb`, application image
`sha256:21cd4a2027cde144133d302d5abb803ddb1670b56a47b90c127e981be402258c`.
**Current CPR-004 Python changes are not installed in this fixture.** A future
current-source test needs a new immutable artifact identity; do not overwrite or
reinterpret the retained CPR-003 release/index.

Read-only installer review confirms the fixed `/opt/hfcache` prefix has no
override and an existing release cannot be overwritten. Selecting another
same-guest release would require the original domain lock exclusively, conflicting
with the retained guard. Prefer a second independently isolated guest and fresh
manifest/image/wheel/source identity for current-source acceptance; preserve this
guest's candidate, original lock inodes, guards and evidence without a switch.
No second fixture or runtime mutation was performed by that review.

## Exact prerequisite correction and deliberate activation

Re-ran the previous read-only handoff before changing anything: old verifier
container `7b07b8c0e2fe779d3e4978dc0eefdc0c283cb0ac2a3366c6c7aff2b8314612e4`
remained created, Running=false, PID 0, with terminal unit exit 126; both operation
directories remained empty. Preserved its full inspect record privately before
the fixed helper's next explicit start.

Independently rechecked `/etc/hfcache/credentials`: not a symlink, root UID/GID
0, device 64515/inode 25174935, mode 0700, zero children. Opened that exact
directory without following a symlink, checked its descriptor identity and
emptiness again, then used descriptor-pinned `fchmod(0755)`. Reverified the same
inode and empty contents afterward. This corrects only the historical empty
placeholder prerequisite from OPS-016; no nonempty credential directory was
chmodded. The root configuration and original domain lock were not replaced.

After confirming the known failed worker and live independent guard, made one
deliberate worker start, observed READY, proved its effective masks, then made one
deliberate API start:

```text
runuser -u hfcache -- env -u DBUS_SESSION_BUS_ADDRESS XDG_RUNTIME_DIR=/run/user/981 systemctl --user start --no-block hfcache-verification.service
runuser -u hfcache -- env -u DBUS_SESSION_BUS_ADDRESS XDG_RUNTIME_DIR=/run/user/981 systemctl --user start --no-block hfcache-api.service
```

Both commands exited 0; bounded subsequent observations reached active/running.
The unchanged helper applied its own stopped-container ownership/state checks.
No manual container removal, socket cleanup, POST replay or rollback was used.
The old failed container record remains evidence rather than being reported as
successful execution.

Actual worker PID 1 had all four credential masks mounted read-only, mode 000:
`/etc/hfcache/credentials`, `/run/credentials`, `/etc/credstore` and
`/etc/credstore.encrypted`. Its effective capability set was zero,
`NoNewPrivs=1`, `Seccomp=2`; known credential environment names were absent.
SELinux remained enforcing. The placeholder correction did not relax these
in-container barriers.

## Real fixed-client boundary

Ran the exact transient identity and fixed rootless client, with its selected
client profile, separate mounted REST credential and authenticated Unix API:

```text
/usr/bin/systemd-run --quiet --wait --pipe --collect --property=User=hfcache --property=Group=hfcache --property=UMask=0027 --property=MemoryHigh=4G -- /usr/local/libexec/hfcache-client --client-config /etc/hfcache/client.toml --api-socket /run/hfcache/api/api.sock --json version --server
```

Process exit 0; one strict schema-1 successful `version` Envelope, application
0.2.1/Python 3.14.6/Hub library 1.24.0, run ID
`ec526286ece448538d06e214e9544598`. This crosses real systemd, rootless Podman,
CLI authentication and UDS boundaries; it does not exercise Cockpit's bridge.

The same fixed prefix with `config validate` returned process exit 10 and the
original schema-1 failed domain Envelope, run ID
`6d3c7554d2614917bdddb19bd44c823c`, error `HFARG002` at `--token-file`:
the deliberately disabled fixture Hub mode conflicts with the API role's
explicit Hub token-file source. This is the documented refusal in
[configuration §7.2](../../../../configuration.md#72-when-each-source-fails), not a
bridge interruption, OCI/process failure or incompatible candidate result. The
fixture source policy was not silently rewritten, and the fixed role's credential
source was not removed. No Hub request occurs in this validation refusal.

The first two-command diagnostic asserted success before persisting its batch
and therefore retained no batch record when installed validation failed. A
separate deliberate bounded validation preserved the terminal failure before
asserting anything. A later read-only version request preserved its own complete
record. No uncertain operation was resubmitted.

## Actual guarded candidate validation

Compiled the repository's actual pure `candidate-guard.ts` and `hfcacheArgv`
exports using existing esbuild. Used their fixed production paths and root/group
settings, without a fixture path override. Guard helper source SHA256:
`d96e8585c6f8963c9172a4615c2881321e89100603b6dd5042c89c990e0ada01`.

Executed the generated guarded read, guarded candidate write, guarded candidate
validation and read-only inspect invocations as guest root. The candidate adds
only a synthetic comment to the exact captured installed bytes: no authority,
repository or job intent changes. Payload bytes travel on stdin to the existing
NUL-delimited helper protocol, never as shell code or command arguments.

| Observed stage | Result |
| --- | --- |
| Guarded installed read | Exit 0; exact installed SHA256 `c020563c6b1812b40377c5ab3a6107442b88fb92c851263346a8f22fb3d38639` |
| Guarded candidate write | Exit 0; candidate SHA256 `8dbe7f4c8b0a646b2f18811b1f2a2ffd3e2fc696d6817fd6bfcf12a552451224` |
| Guarded fixed-client candidate validate | Process/Envelope exit 0, success; `valid`, `syntax_valid`, `authority_compatible`, `installed_policy_valid` true; no authority mismatches; zero repositories; token source `not-resolved` |
| Read-only candidate inspect | Candidate matching, installed base matching, installed candidate changed, backup absent |
| Installed bytes afterward | Exact same installed SHA256; no installation or cleanup attempted |
| Configuration lock | Root-owned 0600, inode 8395118; actual helper flock used |

Candidate validation run ID `8c6c5de22b4744e4a1b86e653eeaad0f` and fingerprint
`03cbfb28846856d8ce119c785fbb18fb7242752dc86d975a0f2fdee67a7c698d`
remain in the private terminal Envelope. The candidate intentionally remains at
the fixed path. No sizing/plan/job submission, archive initialization or Hub
access was performed.

## Stable handoff and remaining acceptance

Final bounded read-only observation exited 0 and retained these identities:

| Role | Container ID / payload PID / service PID |
| --- | --- |
| Worker | `2681e5f94040ec97305ab877b1d7f4996694317637159b2a03a8f67eae2e4901` / 8596 / 8593 |
| API | `05228ca1fd99e6bdbe23b99346d0a4f336cc4b3786c2d9a9341824656560a24e` / 8786 / 8752 |
| Caddy | `f350d526c19a26c40f43144aaa5f2bd94e5e7b03ed8e4e5377835a37fa06ce6d` / 7396 / 7357 |

All three user services are active/running. Independent guard PID 6300 still
holds original domain lock device 27/inode 2113, UID 981. A separate noncreating
exclusive-lock attempt refused as expected. Guest PID 1 still sees the same
read-only NFS4 mount of `127.0.0.1:/`; guest IPv4 routing contains only its
connected `10.0.2.0/24` route, with no default route. API/private worker listeners
exist. Each operation-state directory contains only its regular empty `.lock`
file, with no admitted operation records. An initial observation expecting
literally empty directories was corrected after inspecting these startup-created
locks; it was a diagnostic assertion error, not evidence of an admitted job.

Private guest evidence lives under `/root/cpr-fixture/004/`, including
`placeholder-correction.json`, `worker-start-proof.json`,
`worker-mask-api-start-proof.json`, `installed-validation-classification.json`,
`guarded-candidate-validation.json` and `stable-handoff.json`. Copies of these six
nonsecret records are in the ignored host `cpr004/evidence/` directory. Reproduce
each prepared diagnostic with:

```text
rtk proxy python3 .local-fixtures/cpr-runtime/guest-exec.py --sudo .local-fixtures/cpr-runtime/cpr004/<recorded-script>.py
```

This command uses only the pinned synthetic guest key and protected password on
stdin. Never print their values or use a production profile. Retain failed
attempt evidence and inspect current identities before a deliberate next action;
the template is not permission to replay mutation scripts.

The isolated guest may remain running while paused: no admitted jobs, external
route, production credentials or host/NAS sharing exist. Retain the guard,
NFS-ro mount, masks, secrets and candidate. Teardown retains the identity/drain
precautions in [runtime-setup.md](runtime-setup.md); no automatic teardown follows
an observer ending.

Next required work is actual Cockpit/PAM administrative bridge acceptance and a
new immutable current-source artifact for CPR-004 metadata/recovery tests.
Installed validation's fixture-policy refusal remains explicit. This result
does not diagnose or fix the original installed `reconnected` symptom, exercise
bridge disconnect/reconnect or complete V54. No production inspection or
deployment was performed.
