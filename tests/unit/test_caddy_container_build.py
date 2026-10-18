"""Decision 129: UBI-only stages, byte provenance and confined finite Caddy proof."""

import importlib.util
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "sha256:" + "a" * 64
CONTAINER_ID = "d" * 64


@pytest.fixture
def builder(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "caddy_container_build", ROOT / "scripts/build-caddy-container.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repository = tmp_path / "source"
    packaging = repository / "packaging/containers"
    packaging.mkdir(parents=True)
    for name in ("images.json", "Containerfile.caddy"):
        shutil.copyfile(ROOT / "packaging/containers" / name, packaging / name)
    monkeypatch.setattr(module, "REPOSITORY", repository)
    monkeypatch.setattr(module.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(module, "executable", lambda name: f"/usr/bin/{name}")
    return module


def pins_path(builder):
    return builder.REPOSITORY / "packaging/containers/images.json"


def pins(builder):
    return builder.foundation(pins_path(builder))


def proof_output(inputs, *, version="v2.11.7 h1:known-public-build"):
    return (
        f"{inputs['caddy_binary_sha256']}  /usr/bin/caddy\n"
        f"{inputs['ca_bundle_sha256']}  /etc/ssl/cert.pem\n{version}\n"
    )


def tools(builder, monkeypatch, context, *, failure=None, output=None, dirty=False):  # noqa: PLR0913 - independent injected build/proof/source outcomes
    calls = []
    probe_marker = ""

    def run(arguments, **kwargs):
        nonlocal probe_marker
        calls.append((arguments, kwargs))
        if arguments[0].endswith("/git"):
            stdout = "c" * 40 if "rev-parse" in arguments else (" M source\n" if dirty else "")
            return subprocess.CompletedProcess(arguments, 0, stdout=stdout)
        assert arguments[:2] == ["/usr/bin/podman", "--remote=false"]
        if arguments[2] == "container":
            assert arguments[3:] == ["inspect", CONTAINER_ID]
            record = {
                "Id": CONTAINER_ID,
                "Image": IMAGE,
                "Config": {"Labels": {"io.hfcache.proof": probe_marker}},
                "State": {"Running": False, "Pid": 0, "ExitCode": 0},
            }
            return subprocess.CompletedProcess(arguments, 0, stdout=json.dumps([record]))
        assert "--pull=never" in arguments
        assert "--http-proxy=false" in arguments
        assert "--network=none" in arguments
        if arguments[2] == "run":
            (context / "probe-container.id").write_text(CONTAINER_ID)
            probe_marker = next(
                argument.removeprefix("--label=io.hfcache.proof=")
                for argument in arguments
                if argument.startswith("--label=io.hfcache.proof=")
            )
        if failure == arguments[2]:
            raise subprocess.CalledProcessError(125, arguments, stderr="private-engine-diagnostic")
        if arguments[2] == "build":
            (context / "image.id").write_text(IMAGE)
            return subprocess.CompletedProcess(arguments, 0)
        assert arguments[2] == "run"
        return subprocess.CompletedProcess(
            arguments, 0, stdout=proof_output(pins(builder)) if output is None else output
        )

    monkeypatch.setattr(builder.subprocess, "run", run)
    return calls


@pytest.mark.parametrize("dirty", [False, True])
def test_caddy_build_records_foundation_and_accepts_only_proven_final_bytes(
    builder, monkeypatch, tmp_path, dirty
):
    context = tmp_path / "new-build"
    calls = tools(builder, monkeypatch, context, dirty=dirty)
    result = builder.build(context, "localhost/hfcache:caddy-proof")
    inputs = pins(builder)
    assert result["image_id"] == IMAGE
    assert result["source_commit"] == "c" * 40
    assert result["source_dirty"] is dirty
    assert result["caddy_base"] == inputs["caddy"]
    assert result["build_base"] == inputs["build"]
    for field in (
        "caddy_binary_image",
        "ca_bundle_image",
        "caddy_binary_sha256",
        "ca_bundle_sha256",
    ):
        assert result[field] == inputs[field]
    assert result["containerfile_sha256"] == builder.digest(
        (context / "Containerfile").read_bytes()
    )
    assert result["caddy_version"] == "v2.11.7 h1:known-public-build"
    assert result["file_capabilities"] == ""
    assert json.loads((context / "build.json").read_text()) == result
    assert set(json.loads((context / "inputs.json").read_text())) == set(result) - {
        "image_id",
        "caddy_version",
        "file_capabilities",
        "probe_container_id",
        "probe_container_name",
        "probe_exit_code",
    }
    assert stat.S_IMODE(context.stat().st_mode) == 0o700
    assert [argv[2] for argv, _ in calls if argv[0].endswith("podman")] == [
        "build",
        "run",
        "container",
    ]
    final_probe, options = calls[-2]
    assert final_probe[-3:] == [IMAGE, "-ec", builder._PROBE]
    assert {
        "--network=none",
        "--read-only",
        "--read-only-tmpfs=false",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--userns=keep-id:uid=981,gid=981",
        "--user=981:981",
    } <= set(final_probe)
    assert options["timeout"] == 30
    assert "--rm" not in final_probe
    assert "--name" in final_probe
    assert result["probe_container_id"] == CONTAINER_ID
    assert result["probe_exit_code"] == 0
    assert (context / "probe-container.id").read_text() == CONTAINER_ID
    assert not any(
        argument.startswith(("--volume", "--secret", "--publish")) for argument in final_probe
    )
    assert "/usr/bin/caddy version" in builder._PROBE
    assert "/usr/bin/caddy run" not in builder._PROBE


@pytest.mark.parametrize("failure", ["build", "run"])
def test_failed_caddy_build_or_final_probe_preserves_inputs_without_success(
    builder, monkeypatch, tmp_path, failure
):
    context = tmp_path / "failed-build"
    tools(builder, monkeypatch, context, failure=failure)
    with pytest.raises(subprocess.CalledProcessError):
        builder.build(context, "localhost/hfcache:caddy-proof")
    assert (context / "inputs.json").exists()
    assert (context / "Containerfile").exists()
    assert not (context / "build.json").exists()
    if failure == "run":
        assert (context / "probe-container.id").read_text() == CONTAINER_ID


@pytest.mark.parametrize(
    "change",
    [
        {"Id": "e" * 64},
        {"Image": "sha256:" + "e" * 64},
        {"Config": {"Labels": {"io.hfcache.proof": "unexplained"}}},
        {"State": {"Running": True, "Pid": 123, "ExitCode": 0}},
        {"State": {"Running": False, "Pid": 0, "ExitCode": 1}},
        {"State": {"Running": False, "Pid": 0, "ExitCode": False}},
    ],
)
def test_unknown_or_unfinished_probe_is_retained_without_success(
    builder, monkeypatch, tmp_path, change
):
    context = tmp_path / "unknown-probe"
    calls = tools(builder, monkeypatch, context)
    original = builder.subprocess.run

    def run(arguments, **kwargs):
        result = original(arguments, **kwargs)
        if arguments[2] == "container":
            record = json.loads(result.stdout)[0] | change
            return subprocess.CompletedProcess(arguments, 0, stdout=json.dumps([record]))
        return result

    monkeypatch.setattr(builder.subprocess, "run", run)
    with pytest.raises(ValueError, match="preserve"):
        builder.build(context, "localhost/hfcache:caddy-proof")
    assert (context / "probe-container.id").read_text() == CONTAINER_ID
    assert not (context / "build.json").exists()
    assert not any("stop" in argv or "rm" in argv or "kill" in argv for argv, _ in calls)


def test_probe_timeout_preserves_container_handle_and_never_attempts_force_cleanup(
    builder, monkeypatch, tmp_path
):
    context = tmp_path / "timed-out-probe"
    calls = tools(builder, monkeypatch, context)
    original = builder.subprocess.run

    def run(arguments, **kwargs):
        result = original(arguments, **kwargs)
        if arguments[2] == "run":
            raise subprocess.TimeoutExpired(arguments, kwargs["timeout"])
        return result

    monkeypatch.setattr(builder.subprocess, "run", run)
    with pytest.raises(subprocess.TimeoutExpired):
        builder.build(context, "localhost/hfcache:caddy-proof")
    assert (context / "probe-container.id").read_text() == CONTAINER_ID
    assert (context / "inputs.json").exists()
    assert not (context / "build.json").exists()
    assert not any("stop" in argv or "rm" in argv or "kill" in argv for argv, _ in calls)


@pytest.mark.parametrize(
    "output",
    [
        "",
        "a" * 4097,
        "unexpected\nextra\nlines\nmore\n",
        "a  /usr/bin/caddy\nb  /etc/ssl/cert.pem\nv2.11.7\n",
    ],
)
def test_malformed_or_unverified_final_image_output_never_emits_success(
    builder, monkeypatch, tmp_path, output
):
    context = tmp_path / "bad-proof"
    tools(builder, monkeypatch, context, output=output)
    with pytest.raises(ValueError, match="proof"):
        builder.build(context, "localhost/hfcache:caddy-proof")
    assert not (context / "build.json").exists()


@pytest.mark.parametrize("version", ["v2.11.6", "v2.11.70", "", " "])
def test_final_version_must_match_the_approved_binary(builder, monkeypatch, version):
    context = builder.REPOSITORY / "proof"
    context.mkdir()
    tools(builder, monkeypatch, context, output=proof_output(pins(builder), version=version))
    with pytest.raises(ValueError, match="proof"):
        builder.probe_image(IMAGE, pins(builder), context)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("platform", "linux/arm64"),
        ("caddy", "registry.access.redhat.com/ubi10/ubi-minimal@sha256:" + "a" * 64),
        ("build", "docker.io/library/alpine@sha256:" + "a" * 64),
        ("caddy", "registry.access.redhat.com/ubi10/ubi-micro:latest"),
        ("ca_bundle_image", "docker.io/library/alpine@sha256:" + "a" * 64),
        ("caddy_binary_image", "docker.io/library/caddy:latest"),
        ("caddy_binary_sha256", "A" * 64),
        ("ca_bundle_sha256", True),
    ],
)
def test_foreign_or_unpinned_foundation_is_refused_before_engine(
    builder, monkeypatch, tmp_path, field, value
):
    path = pins_path(builder)
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    calls = tools(builder, monkeypatch, tmp_path / "not-created")
    with pytest.raises(ValueError, match=r"platform|micro|donor|identity|hash|SHA256"):
        builder.build(tmp_path / "not-created", "localhost/hfcache:caddy-proof")
    assert calls == []
    assert not (tmp_path / "not-created").exists()


@pytest.mark.parametrize("body", ["{}", "[]", '{"caddy":"x","caddy":"y"}', " " * 16385])
def test_bad_public_pin_shape_or_duplicate_fields_refuse(builder, body):
    path = pins_path(builder)
    path.write_text(body)
    with pytest.raises(ValueError, match=r"fields|empty|duplicate|oversized"):
        builder.foundation(path)


@pytest.mark.parametrize("change", ["stage", "donor", "hash"])
def test_containerfile_drift_from_public_pins_refuses_before_engine(
    builder, monkeypatch, tmp_path, change
):
    path = builder.REPOSITORY / "packaging/containers/Containerfile.caddy"
    body = path.read_text()
    inputs = pins(builder)
    if change == "stage":
        body = body.replace("FROM " + inputs["build"], "FROM scratch", 1)
    elif change == "donor":
        body = body.replace(inputs["caddy_binary_image"], "docker.io/library/caddy:latest")
    else:
        body = body.replace(inputs["ca_bundle_sha256"], "0" * 64)
    path.write_text(body)
    calls = tools(builder, monkeypatch, tmp_path / "not-created")
    with pytest.raises(ValueError, match="Containerfile"):
        builder.build(tmp_path / "not-created", "localhost/hfcache:caddy-proof")
    assert calls == []


def test_existing_context_and_unexplained_files_are_never_merged_or_deleted(
    builder, monkeypatch, tmp_path
):
    context = tmp_path / "existing"
    context.mkdir()
    (context / "unknown").write_bytes(b"preserved evidence")
    calls = tools(builder, monkeypatch, context)
    with pytest.raises(FileExistsError):
        builder.build(context, "localhost/hfcache:caddy-proof")
    assert calls == []
    assert (context / "unknown").read_bytes() == b"preserved evidence"


def test_root_build_and_remote_tag_are_refused_before_path_io(builder, monkeypatch, tmp_path):
    monkeypatch.setattr(builder.os, "geteuid", lambda: 0)
    with pytest.raises(ValueError, match="never root"):
        builder.build(tmp_path / "new", "localhost/hfcache:caddy-proof")
    monkeypatch.setattr(builder.os, "geteuid", lambda: 1000)
    with pytest.raises(ValueError, match="local"):
        builder.build(tmp_path / "new", "registry.example/caddy:published")
    assert not (tmp_path / "new").exists()


def test_nas_context_refuses_before_any_foundation_or_engine(builder, monkeypatch):
    def forbidden(*_):
        pytest.fail("NAS refusal must precede source/foundation work")

    monkeypatch.setattr(builder, "foundation", forbidden)
    with pytest.raises(ValueError, match="local"):
        builder.build(Path("/srv/hfcache/forbidden"), "localhost/hfcache:caddy-proof")


def test_fresh_install_preserves_bytes_but_drops_source_xattrs(tmp_path):
    """Exercise the real GNU install primitive used for the capability donor."""
    source = tmp_path / "donor"
    target = tmp_path / "prepared/caddy"
    source.write_bytes(b"exact verified executable bytes")
    os.setxattr(source, "user.hfcache-test", b"must not propagate")
    subprocess.run(["/usr/bin/install", "-D", "-m", "0755", source, target], check=True)
    assert target.read_bytes() == source.read_bytes()
    assert target.stat().st_ino != source.stat().st_ino
    assert "user.hfcache-test" not in os.listxattr(target)
    assert stat.S_IMODE(target.stat().st_mode) == 0o755


def test_containerfile_retains_only_approved_runtime_and_mount_placeholders(builder):
    text = (builder.REPOSITORY / "packaging/containers/Containerfile.caddy").read_text()
    builder.validate_containerfile(text.encode(), pins(builder))
    assert "install -D -m 0755 /build/caddy /prepared/usr/bin/caddy" in text
    assert "capabilities=$(/usr/sbin/getcap /prepared/usr/bin/caddy)" in text
    assert 'test -z "$capabilities"' in text
    assert "XDG_CONFIG_HOME=/config XDG_DATA_HOME=/data" in text
    assert "SSL_CERT_FILE=/etc/ssl/cert.pem" in text
    assert "USER 981:981" in text
    assert "/prepared/run/hfcache/api" in text
    assert "/prepared/etc/caddy/Caddyfile" in text
    assert "microdnf" not in text
    assert "FROM docker.io/" not in text
    assert "setcap cap_net_bind_service" not in text


def test_main_failure_emits_only_fixed_refusal_and_preserves_context_notice(
    builder, monkeypatch, capsys
):
    def fail(*_):
        raise subprocess.CalledProcessError(125, ["engine"], stderr="private-engine-diagnostic")

    monkeypatch.setattr(builder, "build", fail)
    monkeypatch.setattr(
        builder.argparse.ArgumentParser,
        "parse_args",
        lambda _: type("Options", (), {"context": Path("/unused"), "tag": "unused"})(),
    )
    assert builder.main() == 1
    output = capsys.readouterr()
    assert "retained context" in output.out
    assert "private-engine-diagnostic" not in output.out + output.err
