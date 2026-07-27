# Consuming the hfcache archive

| Field | Value |
| --- | --- |
| Status | Runbook, exercised from `hfcachewriter.lab.cross.solutions` against the live archive |
| Work package | `OPS-007` |
| Derived from | `docs/plan.md` §6.3, §33; `docs/schemas.md` §3, §4 |
| Helper | `examples/copy-revision.py`, shipped in the release at `/opt/hfcache/current/examples/` |

This is the **downstream** side of the archive: how a machine that is not the
writer takes a copy of a model or dataset revision and proves the bytes are the
ones the archive published.

Everything here needs only a read-only NFS mount and Python 3. It does not need
`hfcache` installed, does not need the Hub, and does not need network access at
all. That is deliberate — a consumer should not have to install this project to
read what it produced.

**Every command block below was run.** Output is real; where it is abbreviated it
is marked `…`, and nothing is invented. The one exception is marked explicitly in
§7, and says why.

---

## 1. What you mount

One export, read-only, containing the archive's `published/` directory and
nothing else:

```bash
sudo mkdir -p /mnt/hfcache
sudo mount -t nfs4 -o ro,hard,nosuid,nodev,noexec \
  nas.lab.cross.solutions:/mnt/tank/huggingface-archive/published /mnt/hfcache
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

## 3. Copying a revision

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
