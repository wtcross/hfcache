# Quickstart

Run `hfcache` end to end on one machine, with nothing but a Linux host,
`sudo`, and [uv](https://docs.astral.sh/uv/): a directory exported over NFS to
`localhost` stands in for the NAS. This is `docs/recovery.md` §6's rehearsal
archive, promoted to a first run.

Two things this page is not. It is not production guidance — that is
`docs/deployment-centos-stream-10.md`, with `docs/storage-requirements.md`
for the server side. And it is not a way around the NFS requirement: the
archive root **must** be an `nfs`/`nfs4` mount; preflight checks
`/proc/self/mountinfo` and there is no override (`FS-02`). The loopback
export exists so that requirement can be met honestly on a laptop.

> **On a host that already runs a deployed `hfcache`, do not follow this
> page.** `/run/hfcache` belongs to the service identity there. Use
> `docs/recovery.md` §6 instead, which runs the deployed binary as the
> service identity against a separate throwaway export.

## 1. The checkout

```bash
git clone https://github.com/wtcross/hfcache.git && cd hfcache
uv sync                # brings CPython 3.14 itself; no system Python is used
uv run hfcache --help
uv run pytest          # the offline default suite
```

## 2. A loopback NFS archive

```bash
# the NFS server; package name varies by distribution
sudo dnf install -y nfs-utils          # Debian/Ubuntu: apt install nfs-kernel-server

# a directory you own, exported to this host only
sudo install -d -m 0750 -o "$(id -un)" -g "$(id -gn)" /srv/hfcache-quickstart-src
echo '/srv/hfcache-quickstart-src 127.0.0.1(rw,sync,no_subtree_check,fsid=77)' \
  | sudo tee /etc/exports.d/hfcache-quickstart.exports
sudo systemctl enable --now nfs-server && sudo exportfs -ra

# mount the export path itself (the NFSv4 pseudo-root is read-only)
sudo install -d -m 0755 /mnt/hfcache-quickstart
sudo mount -t nfs4 -o rw,hard,proto=tcp \
  127.0.0.1:/srv/hfcache-quickstart-src /mnt/hfcache-quickstart
```

There is no identity squashing here: over a loopback NFSv4 mount you are the
same uid on both sides, so the directory you own server-side is a directory
you can write through the mount. A real deployment maps every client identity
at the server instead (`docs/storage-requirements.md` §2–§3).

Mutating commands take one exclusive lock under `/run/hfcache` (`AD-17`).
`/run` is a tmpfs — the deployment provisions the directory with
`packaging/tmpfiles.d/hfcache.conf`; for a first run, create it by hand, and
again after any reboot:

```bash
sudo install -d -m 0700 -o "$(id -un)" -g "$(id -gn)" /run/hfcache
```

## 3. Configure, initialize, sync

```bash
cp examples/config.toml quickstart.toml
uuidgen        # this becomes storage.archive_id
```

Edit `quickstart.toml`:

- `storage.archive_root = "/mnt/hfcache-quickstart"`
- `storage.archive_id` — the UUID you just generated
- `storage.minimum_free_space_gib` — turn the reserve down to fit the
  machine (the example's `100` is a production value; preflight refuses to
  run into it)

The `[[repositories]]` entries already name two tiny public test repositories
— about 15 MiB together — so nothing else needs choosing yet.

```bash
Q="uv run hfcache --config quickstart.toml"
$Q config validate
$Q archive init --archive-root /mnt/hfcache-quickstart \
    --archive-id <the-uuid> --confirm
$Q doctor         # proves hardlink, atomic rename, and ref replacement live
$Q sync           # downloads from huggingface.co, hashes, publishes
$Q list
$Q verify --full
$Q status
```

A second `$Q sync` is an idempotent skip: the resolved commit SHAs are
unchanged, so nothing is downloaded and nothing is republished (`AD-01`).

Everything a consumer would see is under
`/mnt/hfcache-quickstart/published/`. Take a verified copy with the helper —
it needs only the Python standard library, exactly as it would on a real
downstream host (`docs/consumers.md`):

```bash
python3 examples/copy-revision.py --mount /mnt/hfcache-quickstart/published \
    --type model --repository hf-internal-testing/tiny-random-gpt2 \
    --destination ./tiny-random-gpt2
```

## 4. Tear down

```bash
sudo umount /mnt/hfcache-quickstart
sudo rm /etc/exports.d/hfcache-quickstart.exports && sudo exportfs -ra
sudo rm -rf /srv/hfcache-quickstart-src /mnt/hfcache-quickstart /run/hfcache
rm -rf quickstart.toml ./tiny-random-gpt2
```

Stop `nfs-server` too if nothing else on the machine uses it.

## 5. Where next

- Production writer host: `docs/deployment-centos-stream-10.md`
- What the real storage server must provide: `docs/storage-requirements.md`
- Operating it: `docs/operations.md` · consumer side: `docs/consumers.md`
