> Historical reference preserved before the human rewrite. Current authority is the living guide.

# Consuming the hfcache archive

| Field | Value |
| --- | --- |
| Status | Runbook, exercised from `hfcachewriter.lab.example.com` against the live archive |
| Work package | `OPS-007` |
| Derived from | `docs/agents/history/plan.md` §6.3, §33; `docs/schemas.md` §3, §4 |
| Helper | `examples/copy-revision.py`, shipped in the release at `/opt/hfcache/current/examples/` |
| Host setup | `scripts/setup-hfcache-consumer-model-store.sh` (`OPS-009`) |
| Serving | `scripts/consumer-serve-hfcache-model.sh` (`OPS-010`) |

This is the **downstream** side of the archive: how a machine that is not the
writer takes a copy of a model or dataset revision and proves the bytes are the
ones the archive published.

Copying needs only a read-only NFS mount and Python 3. It does not need
`hfcache` installed, does not need the Hub, and does not need network access at
all. The optional host-setup script in §3 additionally assumes a Linux host's
standard account-management tools and runs as root. A consumer still does not
install the Python project merely to read what the archive produced.

Archive-copy command blocks below were run. Output is real; where it is
abbreviated it is marked `…`, and nothing is invented. The §3 host-provisioning
command is an operator action and is marked separately; §7 describes the other
deliberately unexecuted alternative.

---

## 1. What you mount

One export, read-only, containing the archive's `published/` directory and
nothing else:

```bash
sudo mkdir -p /mnt/hfcache
sudo mount -t nfs4 -o ro,hard,nosuid,nodev,noexec \
  nas.lab.example.com:/mnt/tank/huggingface-archive/published /mnt/hfcache
```

Read-only is enforced **by the server**, not by this mount option and not by file
modes (`docs/architecture.md` §5.2). Mounting read-write will not give you write
access; it will give you errors from the server. That is the intended behaviour
and is what handoff item 1's acceptance check proves.

What you will find under it:

```text
/mnt/hfcache/
├── repos/
│   ├── models/<org>/<repo>/
│   │   ├── refs/
│   │   │   ├── current.json            <-- the one file you read
│   │   │   └── revisions/<sha>.json
│   │   └── revisions/<sha>/<publication-id>/     <-- immutable content
│   └── datasets/<org>/<repo>/
├── manifests/<type>/<org>/<repo>/<sha>/<publication-id>.json
└── catalog/
    ├── repositories.json
    └── verification.json
```

`.store/`, `audit/`, and `runs/` are **not** in this export. They are writer-private
and hold the cache, transaction journals, and provenance.

---

## 2. The contract, in one paragraph

Read `refs/current.json` **once**. It names a `tree` and a `manifest`, both
relative to the directory you mounted. Copy the tree. Verify every file in the
copy against the manifest — the complete path set, each size, each SHA-256. If
anything fails, throw the partial copy away, read `current.json` again, and start
over from whatever it now names.

Reading the ref once is the part people get wrong. The archive can publish a new
revision, or a repair can replace an instance, while your copy is running. A
consumer that re-read the ref mid-copy would splice two revisions together and
verify against neither.

---

Identity-based metadata services (API-002) return the exact reference and
manifest instance requested. Reference locators keep their `published/` base;
they are not relative to an HTTP endpoint or the private archive root. Validation
checks identity and containment and never substitutes a newer current instance
when a requested instance has vanished. These services add no artifact transfer
channel; the read-only export and independent copy verification remain the
consumer data path. API-006 now adds authenticated REST metadata discovery;
API-012 now supplies API-backed CLI metadata discovery and independent reader
settings. MCP-002 adds exactly named metadata discovery tools under separate
MCP-reader authentication; full MCP/host acceptance remains gated. No production
listener installation is asserted by
the implementation tests.

### Optional authenticated discovery

A reader may install the base package and provision only the independent
[client settings/API reader credential](../../../api-client.md); no archive TOML, service
UID, Hub credential or archive mount is needed for metadata commands. API-012's
`status`, `list --revisions`, server version, inspection and estimate report the
writer, never silently read a local archive after connection failure. Complete
pagination/joined inventory is bounded and inconsistent evidence fails visibly.
The independent copy helper below still needs its read-only mount and Python,
with no project installation; API discovery does not replace its one-reference
copy attempt or complete local path/size/SHA-256 verification.

An authorized REST reader or writer can discover repositories through
`GET /api/v1/repositories`, walking `next_cursor` until null. Revision pages are
`GET /api/v1/repositories/revisions`; their flat rows carry repository type/ID
plus the exact retained revision fields. Stale continuation returns 409 and
requires restarting the walk. Pages do not create an archive-wide snapshot.

For `model:organization/model-name`, read
`GET /api/v1/repositories/model/organization/model-name/references/current`
once, then read the exact manifest at
`GET /api/v1/repositories/model/organization/model-name/manifests/{commit_sha}/{publication_id}`
using that reference's IDs. A full-SHA reference route is also available. Every
request authenticates, including Unix sockets; off-host access verifies TLS.
The client loads its distinct protected API credential into the Authorization
header without placing secrets in URLs, process arguments or browser storage.
Every reader must be authorized for all archived repositories under AD-21.

HTTP results wrap the schema-1 Envelope in `ReadResponse`; reference data is at
`envelope.data.reference`, with `locator_base="published/"`. Join reference
`tree`/`manifest` onto the read-only mount. Manifest data is at
`envelope.data.manifest`, and `tree_base="archive-root/"` describes its original
durable tree field: it is not relative to the manifest's parent or HTTP URL and
must not replace the reference's published-relative copy locator. Exact missing,
inconsistent or vanished evidence fails visibly, with no newer-instance fallback.

The existing copy helper still reads its own NFS reference once per copy attempt;
it does not consume a REST discovery response. API discovery neither transfers
artifact bytes nor replaces independent complete-path/size/SHA-256 verification.
The [API contract](../../../api.md#metadata-reads) defines wire
fields, pagination, limits and authenticated report streams.

## 3. Copying a revision

### Preparing a revisioned model store

`scripts/setup-hfcache-consumer-model-store.sh` prepares the local store used by
a vLLM consumer. It defaults to `unsloth/Qwen3.8-27B-NVFP4`, installs this
document's helper root-owned at
`/usr/local/libexec/hfcache/copy-revision.py`, creates the locked `vllm:vllm`
service identity, and creates this boundary:

```text
/var/lib/hfcache-models/unsloth/Qwen3.8-27B-NVFP4/
└── revisions/  # the only directory writable by vllm
```

The model root stays `root:vllm` so a later `current` serving pointer is changed
separately, only after a copy verifies. The script checks for 100 GiB of
existing-model-plus-available capacity. A plain directory cannot reserve blocks;
use a dedicated filesystem or quota when that capacity must be isolated from
other workloads.

From a checkout or installed release, run:

```bash
sudo scripts/setup-hfcache-consumer-model-store.sh
```

If only the two consumer files were transferred, name the helper explicitly:

```bash
sudo ./setup-hfcache-consumer-model-store.sh ./copy-revision.py
```

These host-mutating commands are not run by the repository gate. On the
consumer, they are idempotent after the first successful run and print the
installed paths, service identity, available capacity, and a safe unique
destination template.

Every invocation of `copy-revision.py` must use a new, non-existent path below
`revisions/`. It must never target the model root, `current`, or another live
serving path: immediately before its verified rename the helper removes an
existing destination (`examples/copy-revision.py`, `attempt()`). Root ownership
of the model root makes that separation a filesystem boundary, not only an
operator convention.

### Copy and verify

```bash
python3 /path/to/copy-revision.py \
  --mount /mnt/hfcache \
  --type model --repository hf-internal-testing/tiny-random-gpt2 \
  --destination ./tiny-random-gpt2
```

Observed, against the live archive:

```text
copied model hf-internal-testing/tiny-random-gpt2 @ 71034c5d8bde858ff824298bdedc65515b97d2b9
  instance    e0b802874ceb4b1dbb48e0376923c766 (generation 1)
  files       10, 12512611 bytes
  verified    every path, size, and SHA-256 against the manifest
  destination /var/tmp/hfcache-consumer-test/tiny-random-gpt2
exit=0
```

`--json` gives one object on stdout instead, for a scheduler:

```text
$ python3 copy-revision.py --mount /srv/hfcache/published --type dataset \
    --repository hf-internal-testing/fixtures_ade20k --destination ./ade20k --json
{"attempts":1,"commit_sha":"850d349e5038f291284e7999fcacbedc0922534b",
 "destination":"./ade20k","file_count":7,"publication_generation":7,
 "publication_id":"ad1b9ba230954439b5d5ad9aeb4a66ab",
 "repository_id":"hf-internal-testing/fixtures_ade20k",
 "repository_type":"dataset","total_bytes":206179,"verified":true}
exit=0
```

The copy is assembled in a temporary directory beside `--destination` and renamed
into place only after it verifies, so an interrupted run never leaves something
that looks finished. `verified: true` means every byte was read and hashed on
this host — not that the archive says so.

### Serve a verified local model

`scripts/consumer-serve-hfcache-model.sh` starts the OpenAI-compatible vLLM
server in a foreground container. It accepts the vLLM image, an already
verified local model directory, and a vLLM YAML configuration file, in that
order:

```bash
scripts/consumer-serve-hfcache-model.sh \
  docker.io/vllm/vllm-openai:latest \
  ~/.cache/hfcache/unsloth/Qwen3.8-27B-NVFP4/ \
  ./qwen3.8-vllm.yaml
```

The launcher prefers Podman when both Podman and Docker are installed; use
`--runtime docker` or `--runtime podman` to select one explicitly. It gives an
NVIDIA GPU to the container, publishes container port 8000 on host port 8000,
and uses host IPC as vLLM recommends for PyTorch shared memory. The model is
mounted at `/opt/hfcache/model` and the configuration at
`/etc/vllm/config.yaml`, both read-only and with a private container SELinux
label. It then explicitly runs:

```text
vllm serve /opt/hfcache/model --config /etc/vllm/config.yaml
```

Do not put a different `model` value in the YAML: the launcher's positional
model path is the verified tree to serve. The container is removed when vLLM
stops, and the script returns vLLM's exit status. It deliberately does not
verify the model again; use only a destination for which `copy-revision.py`
reported `verified: true`.

---

## 4. What verification actually catches

These were demonstrated on a **throwaway** copy of the published tree, never on
the live archive: §36.5 forbids damaging published content, so the tree was
copied to `/var/tmp`, damaged there, and the helper pointed at the copy.

A file's bytes changed:

```text
attempt 1/1 failed: the copy does not match the manifest: digest: config.json is
a706ac18737f3fda8a02386b05e1fc3c04b4ab2caed64fbbc7b42f974d44d33c, manifest says
9ad49cd2ff58daa38243e4eeaac13b1259786d9418e45bfc01a1fd1fe1089e77
exit=1
```

A file the manifest lists and the tree does not have:

```text
error: giving up after 1 attempts: the copy does not match the manifest: missing: config.json
exit=1
```

A file the tree has and the manifest does not list:

```text
error: giving up after 1 attempts: the copy does not match the manifest: extra: EXTRA.txt
exit=1
```

The third one matters more than it looks. A copy that has everything the manifest
lists is not necessarily correct; extra content is how something that is not the
published revision gets into a directory you are about to trust.

---

## 5. Repairs, the grace period, and retrying

A `repair` replaces a damaged publication instance with a re-downloaded and
re-verified one, then switches `current.json` to it by atomic rename. The retired
instance **stays readable at its original path** for a grace period (seven days by
default), so a copy that resolved the old locator can finish.

If your copy outlives the grace, or the tree disappears for any other reason, the
helper treats it as retryable — discards the partial copy, re-reads the reference,
and restarts:

```text
attempt 1/2 failed: the published tree went away while it was being copied: …/revisions/71034c5d…/e0b802874ceb4b1dbb48e0376923c766
attempt 2/2 failed: the published tree went away while it was being copied: …/revisions/71034c5d…/e0b802874ceb4b1dbb48e0376923c766
error: giving up after 2 attempts: the published tree went away while it was being copied: …
exit=1
```

And resolution follows the reference. With `current.json` switched to a new
instance while the old one was still present — which is exactly the state a repair
leaves during the grace — the helper took the new one:

```text
current.json now names instance ffffffffffffffffffffffffffffffff; the old instance e0b802874ceb4b1dbb48e0376923c766 still exists (grace).
 resolved instance: ffffffffffffffffffffffffffffffff
 verified: True  files: 10
```

A verification failure is also retried, for the same reason: the likeliest cause
of a mismatch against a complete manifest is that the instance was replaced while
the copy was in flight. Persistent failure after `--attempts` is a real problem —
see §8.

---

## 6. Two failures that are *not* retried

Some states mean the archive is inconsistent, and trying again would fail
identically. The helper exits `2` immediately without consuming an attempt.

A reference whose `tree` would escape the mount:

```text
error: the reference's tree has a traversing or empty component: '../../../../../../etc'
```

A reference and manifest that name different publication instances:

```text
error: the manifest at …/71034c5d…/ffffffffffffffffffffffffffffffff.json describes a
different instance than the reference names; the archive is inconsistent and this is not a retry
```

Both were provoked on the throwaway tree with `--attempts 3`, and both exited
before the first attempt was spent. Report either to whoever operates the archive;
they are not consumer-side problems.

---

## 7. Doing it without the helper

The helper is a reference implementation, not a dependency. If you implement this
yourself, these are the parts that are load-bearing:

1. **Read `refs/current.json` exactly once**, and do not re-read it during the copy.
2. **`tree` and `manifest` in a reference are relative to `published/`** — the
   directory you mounted — not to the archive root. Join them onto your mount
   point directly.
3. **Do not use the manifest's own `tree` field.** It is *archive*-relative
   (`published/repos/…`) and names a path you cannot see. This is the one
   difference between the two schemas that will silently produce a wrong path.
   (`docs/schemas.md` §3.1 and §4.1.)
4. **Validate every joined path stays under your mount** before opening it, after
   resolving symlinks. Paths inside a repository come from upstream and are
   hostile input.
5. **Hash in bounded chunks.** Model files do not fit in memory.
6. **Check the path set both ways** — missing and extra — not just the files the
   manifest lists.
7. **Assemble somewhere temporary and rename into place**, so a partial copy is
   never mistaken for a complete one.

A minimal resolution, for orientation — this fragment is illustrative rather than
observed output, which is why it is the one unmarked block in this document:

```python
import json
from pathlib import Path

mount = Path("/mnt/hfcache")
ref = json.loads(
    (mount / "repos/models/hf-internal-testing/tiny-random-gpt2/refs/current.json").read_bytes()
)
tree = mount / ref["tree"]  # published-relative
manifest = json.loads((mount / ref["manifest"]).read_bytes())
for entry in manifest["files"]:
    # verify (tree / entry["path"]) against entry["size"] and entry["sha256"]
    ...
```

---

## 8. When verification keeps failing

If the helper exhausts its attempts with digest or path mismatches, stop and
report it. Do not work around it by copying again, and do not delete anything from
the mount — you cannot, and should not be able to.

What is useful to include:

- The `commit_sha` and `publication_id` from `current.json`.
- The exact failing lines (which paths, which digests).
- Whether `catalog/verification.json` shows the archive as degraded.

The operator's side of this is `docs/recovery.md`: a revision that fails
verification on the archive itself is repaired from upstream or restored from a
snapshot, and neither is something a consumer can or should attempt.

---

## 9. What a consumer must never do

- **Write to the mount.** The export refuses it server-side. Attempts to create,
  modify, rename, or delete are expected to fail, and that is the acceptance check
  for the export itself.
- **Treat the catalog as authoritative for content.** `catalog/repositories.json`
  is derived and rebuildable; `refs/current.json` and the manifests are the
  contract.
- **Resolve a revision by directory modification time**, or by picking the
  newest-looking `<sha>` directory. A pruned SHA can leave an empty container
  behind, and a repaired SHA has more than one instance. The reference is the only
  correct way to choose.
- **Trust `upstream` digests in the manifest.** `git_oid`, `lfs_sha256`, and
  `xet_hash` are recorded to help explain a discrepancy. `sha256` is the one that
  was computed by reading the bytes.

---

## 10. Quick reference

| Task | Command |
| --- | --- |
| Copy and verify a model | `copy-revision.py --mount /mnt/hfcache --type model --repository <org>/<name> --destination <dir>` |
| Copy and verify a dataset | `copy-revision.py --mount /mnt/hfcache --type dataset --repository <org>/<name> --destination <dir>` |
| Machine-readable result | add `--json` |
| More retries on a busy archive | add `--attempts 5` |
| Which revision is current | `cat /mnt/hfcache/repos/<type>/<org>/<repo>/refs/current.json` |
| What the archive holds | `cat /mnt/hfcache/catalog/repositories.json` |

Helper exit codes — these are the helper's own, not the application's §11.2 set:

| Code | Meaning |
| --- | --- |
| `0` | Copied, and every path, size, and digest matched |
| `1` | Failed after exhausting `--attempts`; retryable in kind |
| `2` | Bad invocation, or an archive state retrying will not fix |

## MCP metadata discovery (MCP-002)

This section describes repository behavior and interface examples, not a deployed
MCP session exercised on the installed archive. [MCP tools](../../../mcp.md#available-tools)
provide bounded metadata only, never a file-transfer channel, command or Hub
fetch. The same whole-archive authorization applies, including restricted data.

Call `get_current_reference` once for the intended repository, then retain its
exact SHA/publication ID and published-relative tree/manifest locators throughout
the attempt. `get_revision_manifest` requires that exact pair; disappearing or
mismatched evidence fails visibly rather than substituting a later current.
Reference locators resolve under the mounted published/ export. Manifest `tree`
remains archive-relative, so do not resolve it directly as an export-relative
path or MCP URL; use the validated reference locator and existing base checks.

MCP manifests and reports are explicitly marked projections. Walk both manifest
collections (`files`, `dependencies`) to completion and reconstruct/validate the
full artifact before copy verification; a page's header totals describe the whole
source, not that page. Report headers retain original run identity/fingerprint/
times while their repositories/remediations/findings collection is paged. Do not
confuse current query metadata with the report's historical policy. Immutable
artifact cursors bind all sanitized source headers/collections; inventory cursors
bind selected rows and status headline/warnings are fresh per page. Changes to
bound visible content/policy refuse; there is no archive-wide snapshot or partial-
success claim. A page limit counts entries, and even one large entry/header can exceed a
wire budget and refuse rather than silently lose fields.

Unknown/missing derived verification confidence remains unknown. Metadata reading
or verification cost estimation never establishes integrity; only complete local
path/size/hash verification permits promotion as above. Archive-sourced strings
and dependency observations are untrusted data, not instructions to execute or
fetch external content. Existing copy/serving ownership, read-only export and
operator acceptance requirements remain unchanged.


The [protected-file example](../../../../examples/mcp-client.py) and
[setup/rotation guide](../../../mcp.md#connect) demonstrate
inventory and one-current/exact-manifest discovery without a local archive mount
or writer credential. Output is a bounded count summary, not a reconstructed
manifest or permission to promote. Keep the exact publication fixed during a
copy; a failed/changed walk is restarted as a new attempt rather than combined
with old pages. The same whole-archive authorization covers restricted metadata;
MCP remains independent of bulk copy and serving ownership.
