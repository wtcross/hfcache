"""Real foreground signals clean owned sockets without changing signal semantics."""

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

from hfcache import server as bootstrap
from hfcache.server_config import InstalledPolicy
from hfcache.unix_http import UnixHTTPTransport
from tests.intent_fixtures import OperationStore
from tests.socket_activation import activated_process
from tests.unit.test_server_bootstrap import TOKEN
from tests.unit.test_server_bootstrap import policy as original_policy  # noqa: F401 - fixture

DRIVER = r"""
import json,os,signal,sys,time
from pathlib import Path
import hfcache
from hfcache.server import build_server,listeners
from hfcache.api.app import create_app
from hfcache.api.operations import OperationStore
from hfcache.server_config import validate_server_config_mapping

root=Path(sys.argv[1]);mode=sys.argv[2]
policy=validate_server_config_mapping(json.loads((root/'policy.json').read_text()))
custom_calls=[]
def custom(signum,frame):
    custom_calls.append(signum)
if mode=='custom':signal.signal(signal.SIGTERM,custom)
elif mode=='ignore':signal.signal(signal.SIGTERM,signal.SIG_IGN)
else:assert signal.getsignal(signal.SIGTERM)==signal.SIG_DFL
before=signal.getsignal(signal.SIGTERM)
original_unlink=os.unlink
def delayed_unlink(path,*args,**kwargs):
    if path=='api.sock' and kwargs.get('dir_fd') is not None:
        (root/'cleanup-entered.json').write_text(json.dumps({'pid':os.getpid()}))
        end=time.monotonic()+8
        counter=0
        while not (root/'cleanup-release').exists():
            if time.monotonic()>=end:raise TimeoutError('owned cleanup barrier expired')
            counter+=1
            (root/'cleanup-progress').write_text(str(counter))
            time.sleep(.01)
        # A second TERM during this barrier must not prevent this actual unlink.
        result=original_unlink(path,*args,**kwargs)
        (root/'cleanup-finished').write_text('actual unlink returned')
        return result
    return original_unlink(path,*args,**kwargs)
if mode=='repeat':os.unlink=delayed_unlink
store=OperationStore(policy.state_directory)
store.intent_lock_path=root/'intent.lock'
application=create_app(policy,instance_lock_path=root/'daemon.lock',operation_store=store)
server=build_server(application,policy)
with listeners(policy.listener) as channels:
    info=policy.listener.unix_socket.lstat()
    (root/'bound.json').write_text(json.dumps({
        'pid':os.getpid(),
        'start_ticks':Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19],
        'device':info.st_dev,'inode':info.st_ino,'mode':info.st_mode,
        'package':str(Path(hfcache.__file__).resolve()),'original_signal':str(before),
    }))
    server.run(sockets=channels)
    (root/'after-run').write_text('original server.run returned')
(root/'after-context.json').write_text(json.dumps({
    'restored':signal.getsignal(signal.SIGTERM)==before,'custom_calls':custom_calls,
    'started':server.started,'socket_absent':not policy.listener.unix_socket.exists(),
}))
"""


@pytest.fixture
def tmp_path(tmp_path_factory):
    # A short pathname also lets the manager fixture bind its literal ABI path.
    return tmp_path_factory.mktemp("server-signals")


@pytest.fixture
def policy(request):
    return request.getfixturevalue("original_policy")


def prepare(policy, tmp_path):
    with OperationStore(policy.state_directory, archive_id=InstalledPolicy.open(policy).archive_id):
        pass  # Explicit owned offline activation precedes the isolated real server.
    (tmp_path / "policy.json").write_text(policy.model_dump_json())


def start(policy, tmp_path, mode="default"):
    prepare(policy, tmp_path)
    environment = {"PATH": os.environ["PATH"], "LANG": "C.UTF-8"}
    return subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", DRIVER, str(tmp_path), mode],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def ready(process, policy, tmp_path):
    deadline = time.monotonic() + 10
    with httpx.Client(
        transport=UnixHTTPTransport(
            policy.listener.unix_socket,
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
        ),
        base_url="http://localhost",
        timeout=0.2,
        trust_env=False,
    ) as client:
        while True:
            try:
                response = client.get(
                    "/api/v1/capabilities", headers={"Authorization": "Bearer " + TOKEN}
                )
                assert response.status_code == 200
                assert response.json()["envelope"]["data"]["instance_id"]
                bound = json.loads((tmp_path / "bound.json").read_text())
                assert bound["pid"] == process.pid
                assert Path(bound["package"]).parent == Path(bootstrap.__file__).resolve().parent
            except httpx.HTTPError, FileNotFoundError:
                if process.poll() is not None or time.monotonic() >= deadline:
                    pytest.fail("actual owned API did not become ready")
                time.sleep(0.02)
            else:
                return bound


def joined(process, tmp_path):
    stdout, stderr = process.communicate(timeout=12)
    assert TOKEN.encode() not in stdout + stderr
    (tmp_path / "child-output.json").write_text(
        json.dumps(
            {
                "pid": process.pid,
                "returncode": process.returncode,
                "stdout": stdout.decode(errors="replace"),
                "stderr": stderr.decode(errors="replace"),
            }
        )
    )
    return process.returncode


def finish_owned(process, tmp_path):
    # Test failures release the deterministic I/O barrier and signal only the
    # exact Popen child; no process-group, UID or manager operations exist.
    (tmp_path / "cleanup-release").touch(exist_ok=True)
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            process.communicate(timeout=12)
        except subprocess.TimeoutExpired:
            # This unreaped Popen child cannot have its PID reused. A last
            # resort is permitted only for failed local source-test teardown;
            # it is always a test failure, never normal-drain evidence.
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
                pytest.fail("owned source-test child required forced cleanup; no drain proof")
            pytest.fail("owned source-test child exited without closing its output pipes")
    assert process.poll() is not None
    process.communicate(timeout=5)  # Close exact stopped child pipes after startup failure too.


def assert_no_archive(policy):
    assert not (policy.archive_config.parent / "archive").exists()


def test_real_default_sigterm_removes_only_owned_foreground_node(policy, tmp_path):
    process = start(policy, tmp_path)
    try:
        bound = ready(process, policy, tmp_path)
        process.send_signal(signal.SIGTERM)
        assert joined(process, tmp_path) == -signal.SIGTERM
        assert not policy.listener.unix_socket.exists(), (
            "default SIGTERM bypassed original listeners finally; owned inode "
            f"{bound['device']}:{bound['inode']} remains in {tmp_path}"
        )
        assert_no_archive(policy)
    finally:
        finish_owned(process, tmp_path)


def test_real_default_sigterm_preserves_a_replacement_socket_inode(policy, tmp_path):
    process = start(policy, tmp_path)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as replacement:
        try:
            original = ready(process, policy, tmp_path)
            policy.listener.unix_socket.unlink()
            replacement.bind(str(policy.listener.unix_socket))
            replacement.listen(1)
            before = policy.listener.unix_socket.lstat()
            assert before.st_ino != original["inode"]
            process.send_signal(signal.SIGTERM)
            assert joined(process, tmp_path) == -signal.SIGTERM
            after = policy.listener.unix_socket.lstat()
            assert (before.st_dev, before.st_ino, before.st_mode) == (
                after.st_dev,
                after.st_ino,
                after.st_mode,
            )
            assert replacement.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN)
            assert_no_archive(policy)
        finally:
            finish_owned(process, tmp_path)


@pytest.mark.parametrize("mode", ["custom", "ignore"])
def test_real_sigterm_preserves_original_custom_or_ignored_handler(policy, tmp_path, mode):
    process = start(policy, tmp_path, mode)
    try:
        ready(process, policy, tmp_path)
        process.send_signal(signal.SIGTERM)
        assert joined(process, tmp_path) == 0
        after = json.loads((tmp_path / "after-context.json").read_text())
        assert after == {
            "restored": True,
            "custom_calls": [signal.SIGTERM] if mode == "custom" else [],
            "started": True,
            "socket_absent": True,
        }
        assert_no_archive(policy)
    finally:
        finish_owned(process, tmp_path)


def test_real_repeated_sigterm_cannot_interrupt_owned_unlink(policy, tmp_path):
    process = start(policy, tmp_path, "repeat")
    try:
        ready(process, policy, tmp_path)
        process.send_signal(signal.SIGTERM)
        deadline = time.monotonic() + 5
        while not (tmp_path / "cleanup-entered.json").exists():
            assert process.poll() is None, "first TERM prevented cleanup from starting"
            assert time.monotonic() < deadline
            time.sleep(0.01)
        assert json.loads((tmp_path / "cleanup-entered.json").read_text())["pid"] == process.pid
        progress = tmp_path / "cleanup-progress"
        while True:
            try:
                previous = int(progress.read_text())
                break
            except FileNotFoundError, ValueError:
                assert process.poll() is None
                assert time.monotonic() < deadline
                time.sleep(0.01)
        process.send_signal(signal.SIGTERM)
        # Advancing Python work after the second delivery proves the child is
        # still inside the delayed real unlink, rather than already exiting.
        while True:
            assert process.poll() is None, "second TERM interrupted owned cleanup"
            try:
                if int(progress.read_text()) >= previous + 2:
                    break
            except ValueError:
                pass
            assert time.monotonic() < deadline
            time.sleep(0.01)
        (tmp_path / "cleanup-release").touch()
        assert joined(process, tmp_path) == -signal.SIGTERM
        assert (tmp_path / "cleanup-finished").is_file()
        assert not policy.listener.unix_socket.exists()
        assert_no_archive(policy)
    finally:
        finish_owned(process, tmp_path)


def test_real_activated_sigterm_preserves_manager_socket(policy, tmp_path):
    prepare(policy, tmp_path)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as manager:
        manager.bind(str(policy.listener.unix_socket))
        policy.listener.unix_socket.chmod(policy.listener.socket_mode)
        manager.listen(8)
        before = policy.listener.unix_socket.lstat()
        with activated_process(
            ["-I", "-B", "-c", DRIVER, str(tmp_path), "default"],
            [manager.fileno()],
            environment={"LISTEN_FDS": "1", "LISTEN_FDNAMES": "hfcache-api"},
        ) as process:
            ready(process, policy, tmp_path)
            process.send_signal(signal.SIGTERM)
            assert joined(process, tmp_path) == -signal.SIGTERM
        after = policy.listener.unix_socket.lstat()
        assert (before.st_dev, before.st_ino, before.st_mode) == (
            after.st_dev,
            after.st_ino,
            after.st_mode,
        )
        assert manager.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN)
        assert_no_archive(policy)


def test_non_main_thread_leaves_process_signal_handler_unchanged(policy):
    before = signal.getsignal(signal.SIGTERM)
    failures = []

    def observe():
        try:
            with bootstrap.listeners(policy.listener):
                assert signal.getsignal(signal.SIGTERM) == before
        except BaseException as error:  # noqa: BLE001 - retain any private signal escape from the thread
            failures.append(error)

    thread = threading.Thread(target=observe, name="owned-listener-non-main")
    thread.start()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert not failures
    assert signal.getsignal(signal.SIGTERM) == before
    assert not policy.listener.unix_socket.exists()


def test_source_pid1_eligibility_leaves_default_handler_unchanged(policy, monkeypatch):
    # A pure source eligibility seam, deliberately not Linux PID1 acceptance.
    before = signal.getsignal(signal.SIGTERM)
    assert before == signal.SIG_DFL
    with monkeypatch.context() as scoped:
        scoped.setattr(bootstrap.os, "getpid", lambda: 1)
        with bootstrap.listeners(policy.listener):
            assert signal.getsignal(signal.SIGTERM) == before
    assert signal.getsignal(signal.SIGTERM) == before
    assert not policy.listener.unix_socket.exists()


@pytest.mark.parametrize("error", [RuntimeError("owned ordinary failure"), KeyboardInterrupt()])
def test_unrelated_body_exception_survives_owned_listener_cleanup(policy, error):
    with pytest.raises(type(error)) as caught, bootstrap.listeners(policy.listener):
        raise error
    assert caught.value is error
    assert not policy.listener.unix_socket.exists()
    assert_no_archive(policy)
