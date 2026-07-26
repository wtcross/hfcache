"""Exercise everything plan §22.5 says the hardening must not break.

Run by `scripts/check-hardening.sh` inside a transient unit carrying the *exact*
`[Service]` properties of the installed `hfcache-sync.service`, so what is tested
is what is deployed rather than a copy of it that can drift.

Two halves, and both matter.

**The workload.** DNS, TLS, a real `huggingface_hub` API call, a real download
through `hf_xet`, native extension imports, and a create/fsync/rename/unlink on
the NFS archive. A hardening setting that quietly breaks one of these does not
announce itself: `snapshot_download` failing under `ProcSubset=pid` looks like a
network problem at 02:00 on a Tuesday.

**The sandbox.** Every setting is then confirmed to be *in effect*, because a
property systemd parsed and silently could not apply is worse than one that was
never set — it reads as protection in the unit file and is not there. `CapBnd`
and `NoNewPrivs` come from `/proc/self/status`; the rest are probed by trying the
thing the setting forbids.

Exit `0` only when every check passes. Output is one line per check so a failure
names itself.
"""

from __future__ import annotations

import json
import os
import socket
import ssl
import sys
import tempfile
from pathlib import Path

ARCHIVE = Path("/srv/hfcache")
PROBE_AREA = ARCHIVE / ".store" / "health"
PUBLISHED_DIRECTORY_MODE = 0o2750
"""Mirrors `publication.PUBLISHED_DIRECTORY_MODE`, restated rather than imported.

The probe runs under a sandbox that may not be able to import the application at
all, and what is being tested is the *syscall* the application makes, not the
application. If the constant changes there, this line has to change too — which
is why `docs/plan.md` §22.5 says to re-run this after an upgrade."""
HOST = "huggingface.co"
REPOSITORY = "hf-internal-testing/tiny-random-gpt2"

results: list[tuple[str, bool, str]] = []


def record(name: str, *, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))


def check(name: str, _unused: str = ""):
    """Run a check, turning any exception into a failure rather than a traceback.

    The unused second parameter makes this interchangeable with `denied`, so the
    network checks can be registered as one or the other from a single name.
    """

    def decorate(function):
        try:
            record(name, ok=True, detail=function())
        except Exception as error:  # noqa: BLE001 - a probe reports, it does not raise
            record(name, ok=False, detail=f"{type(error).__name__}: {error}")
        return function

    return decorate


def status_field(field: str) -> str:
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    message = f"{field} is not in /proc/self/status"
    raise AssertionError(message)


def denied(name: str, detail: str):
    """A check that passes when an operation is *refused*."""

    def decorate(function):
        try:
            function()
        except Exception as error:  # noqa: BLE001 - the refusal is the result
            record(name, ok=True, detail=f"refused: {type(error).__name__}")
            return function
        record(name, ok=False, detail=f"permitted, and {detail}")
        return function

    return decorate


# --------------------------------------------------------------------------- #
# The sandbox is actually in effect
# --------------------------------------------------------------------------- #


@check("NoNewPrivileges")
def _no_new_privileges() -> str:
    value = status_field("NoNewPrivs")
    assert value == "1", f"NoNewPrivs is {value}"
    return "NoNewPrivs=1"


@check("CapabilityBoundingSet")
def _capabilities() -> str:
    bounding = status_field("CapBnd")
    effective = status_field("CapEff")
    assert int(bounding, 16) == 0, f"CapBnd={bounding}"
    assert int(effective, 16) == 0, f"CapEff={effective}"
    return f"CapBnd={bounding} CapEff={effective}"


@check("SystemCallArchitectures")
def _seccomp() -> str:
    value = status_field("Seccomp")
    assert value != "0", "no seccomp filter is loaded"
    return f"Seccomp={value} (filter loaded)"


@check("ProtectSystem=strict")
def _read_only_system() -> str:
    for path in (Path("/usr"), Path("/etc"), Path("/opt")):
        try:
            (path / ".hfcache-hardening-probe").touch()
        except OSError:
            continue
        message = f"{path} is writable"
        raise AssertionError(message)
    return "/usr, /etc, and /opt are read-only"


@check("ProtectHome")
def _protect_home() -> str:
    # `true` replaces /home with an empty *inaccessible* directory, so listing it
    # raises rather than returning nothing. Both answers mean the same thing and
    # the first draft of this probe accepted only one of them — which failed the
    # check while the setting was working, exactly the confusion the sandbox half
    # of this file exists to prevent.
    try:
        entries = sorted(path.name for path in Path("/home").iterdir())
    except PermissionError:
        return "/home is not traversable"
    assert entries == [], f"/home shows {entries}"
    return "/home is empty"


@check("ProcSubset=pid")
def _proc_subset() -> str:
    visible = [
        name for name in ("meminfo", "cpuinfo", "stat", "kallsyms") if Path("/proc", name).exists()
    ]
    assert visible == [], f"/proc still shows {visible}"
    return "/proc holds only pid entries"


@check("ProtectProc=invisible")
def _protect_proc() -> str:
    mine = str(os.getpid())
    others = [
        entry.name
        for entry in Path("/proc").iterdir()
        if entry.name.isdigit() and entry.name != mine
    ]
    assert others == [], f"other processes are visible: {others[:5]}"
    return "no other process is visible"


@check("PrivateTmp")
def _private_tmp() -> str:
    entries = sorted(path.name for path in Path("/tmp").iterdir())
    assert entries == [], f"/tmp shows {entries}"
    return "/tmp is private and empty"


@check("PrivateDevices")
def _private_devices() -> str:
    assert Path("/dev/urandom").exists(), "/dev/urandom is missing"
    assert not Path("/dev/sda").exists(), "a block device is present"
    assert not Path("/dev/kmsg").exists(), "/dev/kmsg is present"
    return "/dev holds the api pseudo-devices only"


# The next two are denied by more than one setting at once — `ProcSubset=pid`
# hides all of /proc/sys and `PrivateDevices=true` removes /dev/kmsg — so the
# refusal does not prove which one did it. That is defence in depth rather than a
# weakness, and the check is still worth having: what it asserts is that the
# operation is refused, not which line of the unit refused it. Removing any one of
# the contributing settings would not be caught here, which is why the unit file
# is also the input to this probe rather than a copy of it.
@denied("ProtectKernelTunables", "a kernel tunable could be written")
def _kernel_tunables() -> None:
    Path("/proc/sys/vm/swappiness").write_text("60", encoding="utf-8")


@denied("ProtectKernelLogs", "the kernel ring buffer is readable")
def _kernel_logs() -> None:
    Path("/dev/kmsg").read_bytes()


@denied("RestrictNamespaces", "a new namespace could be created")
def _namespaces() -> None:
    os.unshare(os.CLONE_NEWUSER)


@denied("RestrictAddressFamilies", "AF_PACKET is reachable")
def _address_families() -> None:
    socket.socket(socket.AF_PACKET, socket.SOCK_RAW).close()


@check("writable paths")
def _writable_paths() -> str:
    allowed = []
    for path in (
        ARCHIVE,
        Path("/var/lib/hfcache"),
        Path("/var/cache/hfcache"),
        Path("/run/hfcache"),
    ):
        probe = path / ".hfcache-hardening-probe"
        probe.touch()
        probe.unlink()
        allowed.append(str(path))
    return ", ".join(allowed)


# --------------------------------------------------------------------------- #
# The workload still runs
# --------------------------------------------------------------------------- #

OFFLINE = os.environ.get("HF_HUB_OFFLINE") == "1"
"""Whether this unit is one that must *not* reach the Hub (§22.3).

The verification unit sets `HF_HUB_OFFLINE=1` and `IPAddressDeny=any`, so for it
the four network checks below invert: reaching the Hub would be the failure. A
probe that asserted "DNS works" against every unit would have to be run only
against the sync unit, and then nothing would ever check that the offline unit is
actually offline — which is the more valuable of the two assertions, because it
is the one a dependency upgrade can quietly undo.
"""

network = denied if OFFLINE else check
_expected = "refused" if OFFLINE else "permitted"


@network(f"DNS ({_expected})", "the Hub is resolvable from an offline unit")
def _dns() -> str:
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(HOST, 443)})
    assert addresses, "no address returned"
    return f"{HOST} -> {len(addresses)} addresses"


@network(f"TLS ({_expected})", "the Hub is reachable from an offline unit")
def _tls() -> str:
    context = ssl.create_default_context()
    with socket.create_connection((HOST, 443), timeout=30) as raw:
        with context.wrap_socket(raw, server_hostname=HOST) as wrapped:
            return f"{wrapped.version()} to {HOST}"


@check("native extensions")
def _native() -> str:
    import hf_xet
    import pydantic_core
    import yaml

    loader = "C" if getattr(yaml, "__with_libyaml__", False) else "python"
    return (
        f"pydantic_core {pydantic_core.__version__}, "
        f"hf_xet {getattr(hf_xet, '__version__', 'present')}, yaml {loader} loader"
    )


@network(f"huggingface_hub API ({_expected})", "an API call succeeded from an offline unit")
def _hub_api() -> str:
    from huggingface_hub import HfApi

    info = HfApi().repo_info(REPOSITORY, repo_type="model", revision="main", token=False)
    assert info.sha, "no commit sha returned"
    return f"{REPOSITORY}@{info.sha[:12]}"


@network(f"hf_xet download ({_expected})", "a download succeeded from an offline unit")
def _download() -> str:
    from huggingface_hub import hf_hub_download

    with tempfile.TemporaryDirectory(dir=os.environ.get("CACHE_DIRECTORY", "/tmp")) as scratch:
        path = Path(
            hf_hub_download(
                REPOSITORY,
                filename="config.json",
                repo_type="model",
                revision="main",
                cache_dir=scratch,
                token=False,
            )
        )
        payload = path.read_bytes()
    assert payload, "the downloaded file is empty"
    return f"config.json, {len(payload)} bytes"


@check("NFS create, fsync, rename, unlink")
def _nfs() -> str:
    source = PROBE_AREA / f"hardening-{os.getpid()}"
    destination = PROBE_AREA / f"hardening-{os.getpid()}.renamed"
    try:
        with source.open("wb") as handle:
            handle.write(b"hardening probe")
            handle.flush()
            os.fsync(handle.fileno())
        source.replace(destination)
        directory = os.open(PROBE_AREA, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return f"{destination.name} written, renamed, removed"
    finally:
        for path in (source, destination):
            path.unlink(missing_ok=True)


@check("setgid directory on the archive")
def _setgid_directory() -> str:
    # `publication.create_staging` makes the staging tree at
    # PUBLISHED_DIRECTORY_MODE = 0o2750, because publication is a rename and a
    # rename does not change a mode. `RestrictSUIDSGID=true` makes that exact call
    # EPERM, and the first version of this probe missed it: it wrote *files* to the
    # archive and never created a directory with the setgid bit. The failure
    # therefore surfaced as a failed sync rather than as a failed check, which is
    # the whole thing this file exists to prevent (decision 61).
    target = PROBE_AREA / f"setgid-{os.getpid()}"
    target.mkdir(mode=PUBLISHED_DIRECTORY_MODE)
    try:
        return (
            f"mkdir(mode={oct(PUBLISHED_DIRECTORY_MODE)}) -> {oct(target.stat().st_mode & 0o7777)}"
        )
    finally:
        target.rmdir()


@check("hardlink on the archive")
def _hardlink() -> str:
    # The other publication primitive, and the one plan §14.2 says NFS is exactly
    # where an assumption about it would be wrong.
    source = PROBE_AREA / f"link-source-{os.getpid()}"
    link = PROBE_AREA / f"link-{os.getpid()}"
    try:
        source.write_bytes(b"hardening probe")
        os.link(source, link)
        assert source.samefile(link), "the link is not the same inode"
        return f"link count {source.stat().st_nlink}"
    finally:
        for path in (link, source):
            path.unlink(missing_ok=True)


@check("archive is the live NFS mount")
def _nfs_identity() -> str:
    # `ProtectSystem=strict` bind-mounts the world read-only and `ReadWritePaths=`
    # re-mounts the archive. On an autofs path that could capture the *trigger*
    # rather than the NFS mount, leaving the service writing to an empty
    # directory inside its own namespace. The sentinel proves otherwise.
    sentinel = json.loads((ARCHIVE / ".hfcache-root").read_bytes())
    entries = sorted(path.name for path in ARCHIVE.iterdir())
    assert "published" in entries, f"the archive root shows {entries}"
    return f"archive {sentinel['archive_id']}, {len(entries)} entries"


for name, ok, detail in results:
    print(f"{'pass' if ok else 'FAIL':4}  {name:34}  {detail}")

failed = [name for name, ok, _ in results if not ok]
if failed:
    print(f"\n{len(failed)} of {len(results)} checks failed: {', '.join(failed)}")
    sys.exit(1)
print(f"\nall {len(results)} hardening checks passed")
