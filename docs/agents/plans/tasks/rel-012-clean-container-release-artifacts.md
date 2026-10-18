# REL-012: Build immutable artifacts from clean committed source

| Field | Value |
| --- | --- |
| Work package | `REL-012` |
| Status | completed |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [REL-010](rel-010-rootless-release-artifacts.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Start from REL-010's actual clean committed 0.2.0 source. Record commit,
   clean-state check, tools, lock and exact package/build inputs. Any necessary
   source correction receives its own completed package before a new clean build;
   do not relabel a dirty preview as the final artifact.
   Use an isolated clean detached worktree outside the repository and ignored
   parents: /var/tmp/hfcache-rel-012-source at the actual committed REL-010 source.
   Run the wheel/image builder and full gate there; final production wheel/sdist,
   image contexts, provenance and retained logs stay outside that checkout.
   Ordinary ignored .venv, cockpit/node_modules and dist outputs may exist inside
   without changing tracked Git cleanliness. Main-workspace evidence edits must not contaminate
   the clean source's source_dirty provenance.
2. Build exact wheel/sdist and locked hashed server+MCP runtime images, including
   the pinned Caddy derivative. Record hashes, platform/base/build/runtime image
   identities and provenance. No runtime resolution, automatic pulls or remote
   publication; source versions/tags alone are not artifact identity.
3. Run actual installed/image compatibility against retained targets for archive,
   service, scheduled and new deployment records. Preserve bytes and distinguish
   unavailable old readers from schema-aware refusal. Complete meaningful actual
   local container/TLS/credential/peer/activation/drain proofs without a NAS bind.
4. Stage immutable identified local artifacts with retained rollback trees/state;
   do not select or activate production. Run the required full --with-build gate
   in the NAS-masked test environment. Commit only execution records/evidence,
   leaving package/build inputs identical to the clean source identified above.

## Contracts, invariants, and ADRs

[Release policy](../../release.md), [rootless contract](../../../containers.md),
[deployment](../../../deployment-centos-stream-10.md), [schemas 15/16](../../../schemas.md#15-rootless-runtime-deployment-profile),
INV-005/010/011/014/015, decisions 65/75/79/121/126/127. Preserve workflow's one
work package per commit, exact source/artifact identity and all retained state.

## Validation

Required validation: `scripts/check.sh --with-build`, actual three
locked installation profiles, exact artifact/index/rendered binding checks,
compatibility and owned local container proofs, plus record/link/whitespace audit.
Use the empty read-only NAS shadow for repository collection. Forbidden real NAS
write/full-domain/hardening checks remain NOT RUN. Only root performs privileged
host actions and no secret values are printed.

## Execution notes and handoff

Activated 2026-10-18 after REL-010 committed as
481fcc4e8f9b3c1975d33d6683290076b455087f. REL-012 was the sole task in progress
under the authorized rollout; OPS-016 remains pending. Source/version preparation
and artifact evidence are deliberately separate commits. Root owns actual builds,
compatibility/staging and required gate; Markdown records the evidence. No
production selection, service activation, tag or remote publication is performed.
The artifact's source identity is the REL-010 commit; the later REL-012 evidence
commit is distinct and does not retroactively become the build's source.

### Clean checkout correction and preserved stopped gate

The first detached checkout was under ignored .scratch. Its initial gate missed
intended Pyrefly test coverage because the ignored parent made tests skip. Root
stopped it after 19.907 seconds/SIGTERM 15 and retained
.scratch/rel-012-gate-ignored-source-stopped.log. A wrapper exit 0 is not a gate
pass; no completed test total or full acceptance is claimed for this run.

The corrected detached checkout is /var/tmp/hfcache-rel-012-source, at the same
REL-010 commit with actual Git-clean proof. Main-workspace activation/evidence
edits do not enter it. Standard ignored gate outputs inside it are distinct from
the final production artifacts/provenance/contexts/logs retained outside. An
initial actual clean wheel/sdist rebuild matched the REL-010 preview byte hashes;
root will rebuild from this corrected path for final provenance, rather than
promote preview artifacts or treat the stopped gate as passing evidence.

### Clean artifact and local worker evidence

The corrected-path wheel/sdist rebuild exits 0 with Git-clean source
481fcc4e8f9b3c1975d33d6683290076b455087f. The byte hashes equal the previews,
but these are separately executed clean builds, not promoted dirty artifacts.
Application/Caddy provenance records source_dirty=false and version 0.2.0:
.scratch/rel-012-image-build/build.json and .scratch/rel-012-caddy-build.json.

| Artifact | SHA-256 identity |
| --- | --- |
| Wheel | 4cd663dbdedc6edb10f989a18e5035c28de21d7e5db2da68efddc24582400e2b |
| Sdist | 23ea664da8101d51b947fc3f2ca1e99080ec091b975bf5ff52e4f144ef114733 |
| Application image | sha256:869da6ef2fe68756472e8a476ee45c8d8fbccd2ac91ae3d45190359996962fd3 |
| Caddy derivative | sha256:b6112cfbb3ea8dbbb41a9a7910301ecf548ccc9fde9455f5b386d76005459bc6 |

The actual image build exits 0. Its locked dependency closure SHA-256 is
f1c9ff7f25d91bf27ceb52e1bf3dcc1db6d6005981c44ff8e3b66126af7781db;
uv.lock SHA-256 is d66c41ffa08961eace429cfa0f731c79111361934798eb05a576469a0b1a3bb6.
The records retain exact requirements/Containerfile hashes and pinned Python
3.14.6, build-only uv 0.11.32 and Caddy 2.11.7 platform inputs. Neither displayed
version nor equal bytes substitute for the recorded clean source/build operation.

Actual /var/tmp/hfcache-rel012-worker/proof.json passes with the new exact image:
real FD3/PID1/peer, mapped container UID 981, offline/private PID+network, IPv4/
IPv6 refusal errno 38, masked sources/separate protected-file reader, shared lock
inode/contention, empty operation state and clean stop with retained socket.
There is no NAS bind or verification submission; production account/manager and
full storage acceptance are not inferred from this disposable rootless proof.

### Compatibility and required gate progress

The actual installed native 0.1.10 reader completes 42 observations across 21
record families in .scratch/rel-012-native-readers.json: 15 schema-1 reads,
15 future-2 refusals and 12 reader-unavailable observations, all expected with
bytes preserved and no archive operations, credentials or listeners. Unavailable
service/config readers are not schema-aware success/refusal or nonexecution
proof. Its installed distribution RECORD SHA-256 is
cea3b715498a55134675af0cce2333ce1d245037a6c14ed9df5fcaf0c3d95baf;
the captured result-file SHA-256 is
d27bb9201c89c2ad004c3a4936b6d42803b4d75cb998e99ba02fa6da99293579.
The exact new image completes another 42 observations, accepting all 21 schema-1
families and refusing all 21 future-2 variants with bytes preserved. The staged
host tools separately accept schema 1/refuse future 2 for runtime profile,
release manifest and artifact index (six observations). Native/image plus host
controls total 90 observations; missing old host tools remain unavailable, not
schema-aware refusals. An actual image boundary probe exits 0 and confirms both
host orchestration tools are absent from the app image, as intended. Its record
is .scratch/rel-012-image-tool-boundary.json, SHA-256
fb6de29b67b503a84455d4d21126bd585bc1554f960e5408c528968e291c40e6.

The corrected NAS-masked full --with-build gate ran from the clean
/var/tmp checkout as hfcache-rel012-final-gate, invocation
c730ddcfdc464b8c98cd3ea162d1072e, session 89643, in .scratch/rel-012-gate.log.
Its actual exit is 0: 405-file format/Ruff and whole Pyrefly 0 errors
(11 suppressed, 59 warnings), without the earlier ignored-test warning;
3,792 Python passed/40 deselected in 507.85 seconds; 0.2.0 wheel/sdist and all
three locked installation profiles; Cockpit lint/style/types, 135 tests in
2.276 seconds/build 1,200 ms; four extra wheel smokes in 5.31 seconds. Unit runtime
is 9 minutes 21.707 seconds. Log SHA-256:
e94fe63dc82cf183d0fd5e7e034512cca9a56ce545a78a78218f46139cde0ea5.
The clean worktree's actual Git status stays empty and main-workspace runtime/
package inputs byte-match committed 481fcc4. No fixture containers remain running.

### Source assembly before protected staging

The artifact owner completes source assembly with actual exit 0 at
.scratch/rel-012-stage-source. Its ten-field container-release.json is 5,088
bytes, service UID/GID 981, SHA-256
e55adc61d88bc97c8b562074a4fa0498218ea85dbd429fb5f838cf6d27ef9bca.
The 43 authenticated source files total 1,526,182 bytes (44 files including the
manifest), all nonempty regular/bounded files with hashes re-read and verified.
They include wheel/sdist/Cockpit bundle and seven reviewed proof JSON records,
without image archives. This assembly is user-owned/unprotected, not an installed
stage or selector. Root owns protected copying/staging; clean source remains
Git-clean and no production selection or service start has occurred.

Root protects the manifest at
/opt/hfcache/deployment/20261018-rootless-0.2.0/container-release.json and stages
/opt/hfcache/releases/0.2.0. The first stage returns 0 but a real UID-981 control
fails PermissionError: root's wrapper inherited umask 077, making directories
0700 despite readable 0644 files. This is an operator readability failure, not
format refusal or an activated deployment. The failed fixture remains at
/var/tmp/hfcache-rel012-control.

After exact verification, root preserves that known unactivated tree, with its
original metadata/bytes, at the protected backup's private-stage-umask077. Root
restages the same clean inputs with subprocess umask 022, actual exit 0; root,
scripts and rendered directories are root-owned 0755. All file/index bytes remain
identical. artifact-index.json SHA-256:
2a6b8218051fb2909862953017524ecbb01a5c081b507b5c0b7e865a26ba355e.
The protected stage-permission-correction.json records this transition.

The new /var/tmp/hfcache-rel012-control-2 probe exits 0 using actual staged host
helpers on Python 3.12.13, with no mocks/application imports. Runtime-profile
reading uses actual UID/GID 981; the three schema-1/future-2 pairs pass, preserve
bytes and are recorded in the protected control-readers.json. Positive exhaustive
index verification is repeated after the probe. The current selector remains
releases/0.1.10, the guard remains active and no API/service/account/secret or NAS
change occurs. Control record SHA-256:
68fe575982f2587154b453d9ca5dabd02e5f7e8889d04a36a2f764b9d8058c2c;
permission-correction ledger SHA-256:
7131d6078f946550d50bb759d5fc8341a1d99bae10960d376822b2ffc059cc78.

### Protected local image archives

Both actual OCI exports exit 0 (sessions 8732/73621). Root creates new exclusive
root-owned 0600 copies under
/opt/hfcache/deployment/20261018-rootless-0.2.0 and verifies their hashes:

| Archive | Bytes | SHA-256 |
| --- | --- | --- |
| rel-012-app.oci.tar | 70,001,152 | 015f75e56223f80976f022132a4064c6a1ced79db23df1df315b6054ecc5abff |
| rel-012-caddy.oci.tar | 44,745,216 | 58b5004a8a5208816fd880d66112aa98dbde0daa18c461b38243bea3111f23e8 |

The protected image-archives.json records them. They have not been loaded into
the service engine; exporting/staging neither selects nor starts production.

## Completion evidence

Completed 2026-10-18 in this evidence commit. Actual clean-source artifacts,
runtime/Caddy provenance, new-image worker proof, 90 compatibility observations,
protected indexed staging/readability controls, local OCI exports and corrected
full --with-build gate pass as recorded. The ignored-parent stopped run and
operator umask failure remain preserved and are not passing evidence.

Runtime/package inputs stay identical to source commit 481fcc4, whose clean
worktree remains Git-clean; this later evidence commit is not the artifact's
source. Reviewed INV-005/010/011/014/015 and 65/75/79/121/126/127; no runtime,
dependency, format or architecture change/new decision. Release guidance records
the proven checkout/readability procedure. The [progress audit](../../progress.md),
plan/current, local links/dependencies and whitespace agree. OPS-016 remains next
pending until this commit. Production still selects native 0.1.10, guard active,
writers masked, NAS read-only and fixtures stopped. No service-engine image load,
account/secret/service activation, NAS file I/O or writes, other-host change,
remote publication, ACME or tag. Installed-manager/full-storage acceptance stays
explicitly held for the guarded deployment and separately forbidden checks.
