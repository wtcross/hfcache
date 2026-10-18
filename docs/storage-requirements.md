# Storage requirements

What the storage server must provide for `hfcache` to operate, stated for
**any** NFSv4.2 server. The [TrueNAS settings](#truenas-settings) give a worked example, and `hfcache doctor` proves most of what this page requires
from the writer, against the real mount, before anything relies on it
(`docs/deployment-centos-stream-10.md` §11).

The shape in one paragraph: one filesystem holds the whole archive; the writer
reaches it over a read/write NFS export that only the writer can use, with
every client identity mapped to one writer-side identity; consumers reach only
`published/` over a second, server-enforced read-only export mapped to a read
identity. Read-only for consumers is a property of the **server**, never of
file modes or client goodwill (`docs/architecture.md` §2.1).

## 1. One filesystem

- The entire archive — download cache, staging, publications, manifests,
  references, audit records — lives on **one filesystem**, so `link(2)` and
  `rename(2)` work across all of it (`FS-04`). Publication is hardlinks plus
  atomic rename (`AD-11`, `AD-14`); a server that cannot hardlink within the
  export cannot run the default publication mode, and `doctor` will say so
  before anything is downloaded.
- Case-sensitive, with no name normalization (`docs/architecture.md` §5.3):
  the archive preserves upstream file names exactly.
- NFSv4.2 is the deployed standard (the writer mounts `rw,hard`, `nconnect=4`
  — `packaging/systemd/srv-hfcache.mount`). Preflight accepts an `nfs`/`nfs4`
  mount and then proves the semantics it needs directly — hardlink, atomic
  rename over an existing file, reference replacement — rather than trusting
  a version number.
- Snapshots, replication, and scrubs are the server's job, and worth having:
  the archive is designed to be restored from a snapshot
  (`docs/recovery.md` §7). See [data protection](#data-protection).

## 2. The writer export

Exactly one host mutates the archive (`AD-17`), and the export is what
enforces it:

| Property | Requirement |
| --- | --- |
| Scope | The full archive dataset |
| Access | Read/write, allowed **only** from the writer's address |
| Identity | Every client identity mapped to one writer-side `user:group` pair |

The identity mapping is TrueNAS's "Mapall"; on a Linux server it is
`all_squash,anonuid=<writer-uid>,anongid=<archive-gid>`. The numeric ids are
the **server's choice**: nothing on the writer depends on their values, and
they need no account on the writer at all — files on the mount appear there
as `UNKNOWN:UNKNOWN`, which is why preflight proves writability with a real
create/fsync/rename/delete probe rather than by comparing uids
(`docs/deployment-centos-stream-10.md` §2).

## 3. The consumer export

| Property | Requirement |
| --- | --- |
| Scope | The `published/` subtree only |
| Access | **Read-only, enforced server-side**; allowed from consumer hosts, excluding the writer |
| Identity | Every client identity mapped to a read user whose **group is the archive group** |

The read identity's group is what grants access: `published/` is `2750` with
setgid and published files are `0640`, so membership in the archive group is
the entire read path (`docs/architecture.md` §5.2). On a Linux server:
`ro,all_squash,anonuid=<read-uid>,anongid=<archive-gid>`.

A consumer must be able to read, and must fail to create, modify, rename, and
delete — at the server. Prove both from a real consumer host
Writer-side fixtures cannot establish consumer export enforcement.

## 4. Pre-creation and ownership

- The archive root should exist before `hfcache archive init` runs against
  it, owned by the writer identity, mode `0750`.
- If the server requires an export's target directory to exist before the
  export can be defined — TrueNAS does, for `published/` — pre-create it
  **empty**, with the same owner and group as the archive root, mode `2750`.
  Initialization adopts exactly that shape and refuses anything else
  (`FS-22`).

## 5. Capacity

Size for the configured repositories times `storage.maximum_revisions` retained
revisions each (three by default, or five explicitly), plus the private download
cache — hardlink publication makes a revision
nearly free when its blobs are already cached (`AD-11`). `hfcache plan`
reports dry-run sizes without downloading anything, and
`storage.minimum_free_space_gib` / `minimum_free_space_percent` set the
reserve preflight enforces on every run (`docs/configuration.md` §4). Quotas
and capacity alerts on the server are the operator's backstop
(see [data protection](#data-protection)).

## TrueNAS settings

Use a dedicated child dataset, such as `<pool>/huggingface-archive`; do not
export the pool root or create one dataset per repository. For TrueNAS
25.10.5 the initial settings are:

| Setting | Value |
| --- | --- |
| Preset and ACL | Generic, POSIX |
| Case sensitivity | Sensitive |
| Record size | `1M` |
| Compression | `lz4` |
| Atime | Off |
| Sync | Standard |
| Deduplication | Off |
| Quota | From repository dry-run sizing, with warning headroom |

Create server identities `hfcache-sync` and `hfcache-read`, both in
`hfcache-archive`. Use owner/group `hfcache-sync:hfcache-archive`, root
`0750`, private `.store`, `audit` and `runs` directories `0700`, and
`published` `2750`. Published files use `0640` with service umask `0027`.
Only published content is accessible to the read identity.

Export the dataset read/write to the exact writer address (`/32`), mapping
all identities to `hfcache-sync:hfcache-archive`. Export only `published/`
read-only to explicit consumer hosts or an isolated consumer VLAN, mapping
all identities to `hfcache-read:hfcache-archive`. Selectors must be disjoint;
never include the writer in a consumer CIDR. Prove the parent/subdirectory
export topology on the actual server before relying on hardlink publication.

If middleware rejects that topology, stop provisioning. The alternative is
separate private-cache and published datasets with explicit copy publication,
fresh capacity/throughput sizing and operator approval. This needs a separately
reviewed layout: current staging and publication destinations must still share
one filesystem (`FS-04`). Never weaken server-enforced read-only isolation to
retain hardlink deduplication.

On a trusted isolated storage VLAN, `AUTH_SYS` with exact host restrictions
and Mapall is acceptable. Use a separately designed `KRB5I` or `KRB5P`
deployment when cryptographic client identity is required.

## Data protection

Start with daily snapshots retained 14 days, weekly snapshots 8 weeks and
monthly snapshots 12 months; tune after measuring snapshot-held space.
Schedule the daily snapshot before the 02:00 sync and replicate to another
pool or system. Keep the existing scrub schedule, or approximately monthly
scrubs if no site policy exists. Keep SMART tests away from sync, verification,
scrub and replication. Protect exported TrueNAS configuration, encryption keys
and the secret seed when encryption is enabled. Restore at least once into a
separate dataset and complete full application verification before declaring
the restored archive usable.

Measure Hub download, NFS write/read, unique-object SHA-256, hardlink and copy
publication, large-repository metadata performance, retained-revision and
snapshot-held space, and peak local Xet cache use. Require dry-run logical and
new-download sizes before activating large repositories. Establish server
capacity alerts before enabling unattended sync.
