from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "consumer-serve-hfcache-model.sh"


def run_script(
    *arguments: str,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *arguments],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_consumer_serve_script_is_executable_bash() -> None:
    assert SCRIPT.stat().st_mode & stat.S_IXUSR
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True, timeout=10)


def test_consumer_serve_script_help_is_safe_from_any_directory(tmp_path: Path) -> None:
    result = run_script("--help", cwd=tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "VLLM_IMAGE MODEL_DIRECTORY VLLM_CONFIG_YAML" in result.stdout
    assert "read-only" in result.stdout


def test_consumer_serve_script_rejects_unknown_options(tmp_path: Path) -> None:
    result = run_script("--not-an-option", cwd=tmp_path)

    assert result.returncode == 64
    assert "unknown option: --not-an-option" in result.stderr
    assert result.stdout == ""


def test_consumer_serve_script_requires_all_three_inputs(tmp_path: Path) -> None:
    result = run_script("example.invalid/vllm:latest", cwd=tmp_path)

    assert result.returncode == 64
    assert "expected VLLM_IMAGE, MODEL_DIRECTORY, and VLLM_CONFIG_YAML" in result.stderr
    assert result.stdout == ""


def test_consumer_serve_script_rejects_unsupported_runtime(tmp_path: Path) -> None:
    result = run_script(
        "--runtime",
        "containerd",
        "example.invalid/vllm:latest",
        "/missing-model",
        "/missing-config",
        cwd=tmp_path,
    )

    assert result.returncode == 64
    assert "unsupported runtime: containerd" in result.stderr
    assert result.stdout == ""


def test_consumer_serve_script_builds_podman_command_and_propagates_exit(
    tmp_path: Path,
) -> None:
    model = tmp_path / "model"
    model.mkdir()
    config = tmp_path / "serve.yaml"
    config.write_text("gpu-memory-utilization: 0.9\n", encoding="utf-8")
    fake_runtime = tmp_path / "podman"
    fake_runtime.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\0\' "$@"\nexit "${FAKE_RUNTIME_EXIT:-0}"\n',
        encoding="utf-8",
    )
    fake_runtime.chmod(0o755)
    environment = os.environ | {
        "FAKE_RUNTIME_EXIT": "23",
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
    }

    result = run_script(
        "--runtime",
        "podman",
        "example.invalid/vllm:test",
        str(model),
        str(config),
        cwd=tmp_path,
        env=environment,
    )

    assert result.returncode == 23
    assert result.stderr == ""
    assert result.stdout.split("\0")[:-1] == [
        "run",
        "--rm",
        "--device",
        "nvidia.com/gpu=all",
        "--ipc=host",
        "--publish",
        "8000:8000",
        "--volume",
        f"{model}:/opt/hfcache/model:ro,Z",
        "--volume",
        f"{config}:/etc/vllm/config.yaml:ro,Z",
        "--entrypoint",
        "vllm",
        "example.invalid/vllm:test",
        "serve",
        "/opt/hfcache/model",
        "--config",
        "/etc/vllm/config.yaml",
    ]


def test_consumer_serve_script_uses_docker_gpu_flag(tmp_path: Path) -> None:
    model = tmp_path / "model"
    model.mkdir()
    config = tmp_path / "serve.yaml"
    config.write_text("dtype: auto\n", encoding="utf-8")
    fake_runtime = tmp_path / "docker"
    fake_runtime.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\0' \"$@\"\n",
        encoding="utf-8",
    )
    fake_runtime.chmod(0o755)
    environment = os.environ | {"PATH": f"{tmp_path}:{os.environ['PATH']}"}

    result = run_script(
        "--runtime",
        "docker",
        "example.invalid/vllm:test",
        str(model),
        str(config),
        cwd=tmp_path,
        env=environment,
    )

    assert result.returncode == 0
    arguments = result.stdout.split("\0")[:-1]
    assert arguments[0:4] == ["run", "--rm", "--gpus", "all"]
