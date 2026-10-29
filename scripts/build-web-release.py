#!/usr/bin/env python3
"""Construct an indexed backend/UI/helper release from clean committed source.

Decision143: run only as the login builder in a clean detached source worktree.
Outputs and failed evidence stay outside that worktree. No service, credentials,
archive initialization, container engine or deployment selection is accessed.
"""

import argparse
import importlib.util
import io
import os
import shutil
import subprocess
import tarfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def authority():
    spec = importlib.util.spec_from_file_location("web_release", ROOT / "scripts/web-release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(argv, *, environment=None):
    return subprocess.run(  # noqa: S603 - fixed tools/argv; no shell or user commands
        argv,
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
    ).stdout


def build(output):  # noqa: PLR0915 - one clean construction transaction; preserve failed outputs
    web = authority()
    web.require(os.geteuid() != 0, "build as the login user")
    web.require(
        run(["uv", "--version"]).decode().split()[:2] == ["uv", "0.11.32"],
        "pinned uv required",
    )
    web.require(
        not run(["git", "status", "--porcelain=v1", "--untracked-files=all"]),
        "clean committed source required",
    )
    commit = run(["git", "rev-parse", "HEAD"]).decode().strip()
    epoch = run(["git", "show", "-s", "--format=%ct", "HEAD"]).decode().strip()
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    output = Path(os.path.abspath(output))  # noqa: PTH100 - lexical path before local proof
    web.local(output.parent)
    web.require(not output.is_relative_to(ROOT), "release output must be outside source")
    output.mkdir(mode=0o755)
    output.chmod(0o755)
    environment = dict(os.environ, SOURCE_DATE_EPOCH=epoch, PYTHONDONTWRITEBYTECODE="1")
    commands = (
        ["uv", "sync", "--locked", "--extra", "server", "--extra", "mcp"],
        ["pnpm", "--dir", "web", "install", "--frozen-lockfile"],
        ["uv", "build", "--wheel", "--sdist", "--out-dir", str(output / "backend-build")],
        ["pnpm", "--dir", "web", "run", "build"],
    )
    for number, argv in enumerate(commands):
        log = output / f"build-{number}.log"
        with log.open("xb") as stream:
            subprocess.run(  # noqa: S603 - fixed build commands; output retained on failure
                argv,
                cwd=ROOT,
                env=environment,
                check=True,
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
    manifest_path = ROOT / "web/dist/manifest.json"
    expected = web.digest(manifest_path.read_bytes())
    wire = web.decode((ROOT / "web/src/wire/contracts.json").read_bytes())["source_digest"]
    manifest, files = web.load_assets(
        ROOT / "web/dist",
        expected,
        application_version=version,
        source_commit=commit,
        require_clean=True,
        wire_source_digest=wire,
        pnpm_lock_sha256=web.digest((ROOT / "web/pnpm-lock.yaml").read_bytes()),
    )
    # Construction additionally uses the application's original schema authority.
    run(
        [
            str(ROOT / ".venv/bin/python"),
            "-c",
            (
                "from hfcache.ui_models import UiAssetManifest; from hfcache.models import dump; "
                "from pathlib import Path; p=Path('web/dist/manifest.json'); "
                "m=UiAssetManifest.model_validate_json(p.read_bytes()); "
                "assert dump(m)==p.read_bytes()"
            ),
        ],
        environment=environment,
    )
    # Repeat bundling on identical source/tools and compare every artifact byte.
    with (output / "reproduce-ui.log").open("xb") as stream:
        subprocess.run(  # noqa: S603 - fixed reproducibility command
            commands[-1],
            cwd=ROOT,
            env=environment,
            check=True,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    second, repeated = web.load_assets(
        ROOT / "web/dist",
        expected,
        application_version=version,
        source_commit=commit,
        require_clean=True,
    )
    web.require(second == manifest and repeated == files, "UI build is not reproducible")
    repeated_backend = output / "reproduce-backend"
    with (output / "reproduce-backend.log").open("xb") as stream:
        subprocess.run(  # noqa: S603 - fixed same-source backend reproduction
            [shutil.which("uv"), "build", "--wheel", "--sdist", "--out-dir", str(repeated_backend)],
            cwd=ROOT,
            env=environment,
            check=True,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    backend_names = {f"hfcache-{version}-py3-none-any.whl", f"hfcache-{version}.tar.gz"}
    originals = {
        name: web.digest((output / "backend-build" / name).read_bytes()) for name in backend_names
    }
    repeats = {name: web.digest((repeated_backend / name).read_bytes()) for name in backend_names}
    web.require(originals == repeats, "backend build is not reproducible")
    (output / "wheels").mkdir(mode=0o755)
    for name in sorted(backend_names):
        shutil.copyfile(output / "backend-build" / name, output / "wheels" / name)
    web.require(
        run(["git", "rev-parse", "HEAD"]).decode().strip() == commit, "source commit changed"
    )
    web.require(
        not run(["git", "status", "--porcelain=v1", "--untracked-files=all"]),
        "build changed committed source",
    )
    source = output / "source"
    source.mkdir(mode=0o755)
    archive = run(["git", "archive", "--format=tar", commit])
    with tarfile.open(fileobj=io.BytesIO(archive)) as captured:
        captured.extractall(source, filter="data")
    source_files = {}
    for raw_name in run(["git", "ls-files", "-z"]).split(b"\0"):
        if not raw_name:
            continue
        name = raw_name.decode()
        path = source / name
        if path.is_symlink():
            web.require(name == "CLAUDE.md" and path.readlink() == Path("AGENTS.md"))
            continue
        web.relative(name)
        source_files[name] = web.digest(web.read_file(path, web.MAX_TOTAL))
    for name, body in files.items():
        destination = output / "ui" / name
        destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        destination.write_bytes(body)
        destination.chmod(0o644)
    (output / "host-helper").mkdir(mode=0o755)
    for name, original in web.HELPER.items():
        shutil.copyfile(source / original, output / "host-helper" / name)
        (output / "host-helper" / name).chmod(0o644)
    artifacts = {}
    for folder in ("ui", "wheels", "host-helper"):
        (output / folder).chmod(0o755)
        for path in sorted((output / folder).rglob("*")):
            path.chmod(0o755 if path.is_dir() else 0o644)
            if path.is_file():
                artifacts[path.relative_to(output).as_posix()] = web.digest(
                    web.read_file(path, web.MAX_TOTAL)
                )
    index = {
        "schema_version": 1,
        "kind": "hfcache_web_release",
        "version": version,
        "source_commit": commit,
        "source_files": source_files,
        "files": artifacts,
        "ui_manifest_sha256": expected,
    }
    raw = web.encoded(index)
    (output / "web-release.json").write_bytes(raw)
    (output / "web-release.json").chmod(0o644)
    web.verify_native(output, web.digest(raw), source)
    (output / "build-evidence.json").write_bytes(
        web.encoded(
            {
                "schema_version": 1,
                "source_commit": commit,
                "source_clean": True,
                "source_snapshot_sha256": web.digest(web.encoded(source_files)),
                "source_date_epoch": int(epoch),
                "uv": run(["uv", "--version"]).decode().strip(),
                "backend": originals,
                "backend_reproducible": True,
                "ui_reproducible": True,
                "ui_manifest_sha256": expected,
                "release_index_sha256": web.digest(raw),
            }
        )
    )
    print("release index SHA256 " + web.digest(raw))
    print("source " + commit + "; UI manifest SHA256 " + expected)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="new local directory outside source; retained"
    )
    options = parser.parse_args()
    try:
        build(options.output)
    except OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, tarfile.TarError:
        print("web release build refused or failed; retain source and output for inspection")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
