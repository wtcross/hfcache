"""Startup capability repair; kernel transitions here are explicitly simulated.

Real owned subprocesses exercise proc descriptors, thread refusal and inert help.
Managed root capability proof remains the separate disposable-guest acceptance.
"""

import ast
import ctypes
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts/host-helper.py"
SPEC = importlib.util.spec_from_file_location("protected_host_startup", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
daemon = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(daemon)


def facts(*, root=True, inheritable=0, ambient=0):
    return {
        "CapEff": 0xC0 if root else 0,
        "CapPrm": 0xC0 if root else 0,
        "CapBnd": 0xC0,
        "CapInh": inheritable,
        "CapAmb": ambient,
        "NoNewPrivs": 1,
        "Seccomp": 2,
        "Seccomp_filters": 24,
    }


class SimulatedKernel:
    def __init__(self, before, events):
        self.before = before
        self.events = events
        self.written = None
        self.error_at = None
        self.mismatch = False

    def capget(self, header, data):
        self.events.append("capget")
        assert list(ctypes.cast(header, ctypes.POINTER(ctypes.c_uint32 * 2)).contents) == [
            0x20080522,
            0,
        ]
        words = ctypes.cast(data, ctypes.POINTER(ctypes.c_uint32 * 6)).contents
        for offset in range(2):
            for index, name in enumerate(("CapEff", "CapPrm", "CapInh")):
                words[offset * 3 + index] = (self.before[name] >> (32 * offset)) & 0xFFFFFFFF
        if self.mismatch:
            words[0] |= 1 << 8
        return -1 if self.error_at == "capget" else 0

    def prctl(self, *arguments):
        self.events.append("clear-ambient")
        assert arguments == (47, 4, 0, 0, 0)
        return -1 if self.error_at == "clear-ambient" else 0

    def capset(self, header, data):
        self.events.append("clear-inheritable")
        self.written = list(ctypes.cast(data, ctypes.POINTER(ctypes.c_uint32 * 6)).contents)
        return -1 if self.error_at == "clear-inheritable" else 0


def simulated_startup(monkeypatch, *, root=True, inheritable=0, ambient=0):
    before = facts(root=root, inheritable=inheritable, ambient=ambient)
    after = facts(root=root)
    events = []
    kernel = SimulatedKernel(before, events)
    samples = iter(((before, 101), (after, 103)))
    monkeypatch.setattr(daemon, "startup_principal", lambda: root)
    monkeypatch.setattr(daemon, "startup_task", lambda: 5)
    monkeypatch.setattr(daemon, "startup_status", lambda: next(samples))

    def library(name, *, use_errno):
        assert name is None
        assert use_errno is True
        events.append("library")
        return kernel

    monkeypatch.setattr(daemon.ctypes, "CDLL", library)
    return before, after, events, kernel


@pytest.mark.parametrize(
    ("root", "inheritable", "ambient"),
    [(True, 0x80, 0x80), (True, 0, 0), (True, 1 << 40, 0), (False, 0, 0), (False, 0x80, 0)],
)
def test_simulated_root_and_delegated_startup_clear_all_ia_without_increasing_pe(
    monkeypatch, root, inheritable, ambient
):
    _before, _after, events, kernel = simulated_startup(
        monkeypatch, root=root, inheritable=inheritable, ambient=ambient
    )
    assert daemon.clear_startup_capabilities() == {"files": 4, "bytes": 214}
    expected = 0xC0 if root else 0
    assert kernel.written == [expected, expected, 0, 0, 0, 0]
    assert events == ["library", "capget", "clear-ambient", "clear-inheritable"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("CapEff", 0x40),
        ("CapPrm", 0x1C0),
        ("CapBnd", 0x1C0),
        ("NoNewPrivs", 0),
        ("Seccomp", 0),
        ("Seccomp", 1),
        ("Seccomp_filters", 0),
    ],
)
def test_unexpected_startup_security_refuses_before_any_capability_call(monkeypatch, field, value):
    before, _after, events, _kernel = simulated_startup(monkeypatch)
    before[field] = value
    with pytest.raises(ValueError, match="refused"):
        daemon.clear_startup_capabilities()
    assert events == []


def test_nonroot_effective_capability_refuses_instead_of_preserving_it(monkeypatch):
    before, _after, events, _kernel = simulated_startup(monkeypatch, root=False)
    before["CapEff"] = 0x80
    with pytest.raises(ValueError, match="refused"):
        daemon.clear_startup_capabilities()
    assert events == []


@pytest.mark.parametrize("operation", ["capget", "clear-ambient", "clear-inheritable"])
def test_kernel_refusal_never_continues_or_loads_protected_code(monkeypatch, operation):
    _before, _after, events, kernel = simulated_startup(monkeypatch)
    kernel.error_at = operation
    with pytest.raises(ValueError, match="refused"):
        daemon.clear_startup_capabilities()
    assert events[-1] == operation


def test_kernel_proc_disagreement_refuses_before_ambient_or_inheritable_changes(monkeypatch):
    _before, _after, events, kernel = simulated_startup(monkeypatch)
    kernel.mismatch = True
    with pytest.raises(ValueError, match="refused"):
        daemon.clear_startup_capabilities()
    assert events == ["library", "capget"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("CapInh", 1 << 40),
        ("CapAmb", 0x80),
        ("CapEff", 0x40),
        ("CapBnd", 0),
        ("Seccomp_filters", 23),
    ],
)
def test_steady_state_must_actually_match_after_successful_syscalls(monkeypatch, field, value):
    _before, after, _events, _kernel = simulated_startup(monkeypatch)
    after[field] = value
    with pytest.raises(ValueError, match="refused"):
        daemon.clear_startup_capabilities()


@pytest.mark.parametrize(
    ("uids", "gids", "groups", "valid"),
    [
        ((0, 0, 0), (0, 0, 0), [], True),
        ((0, 0, 0), (0, 0, 0), [0], True),
        ((983, 983, 983), (983, 983, 983), [], True),
        ((983, 0, 983), (983, 983, 983), [], False),
        ((0, 0, 0), (983, 983, 983), [], False),
        ((983, 983, 983), (0, 0, 0), [], False),
        ((983, 983, 983), (983, 983, 983), [983], False),
        ((0, 0, 0), (0, 0, 0), [983], True),
        ((0, 0, 0), (0, 0, 0), [0, 983], True),
        ((0, 0, 0), (0, 0, 0), [984], False),
    ],
)
def test_startup_ids_reject_mixed_or_extra_principals(monkeypatch, uids, gids, groups, valid):
    monkeypatch.setattr(daemon.grp, "getgrnam", lambda _name: SimpleNamespace(gr_gid=983))
    monkeypatch.setattr(
        daemon,
        "os",
        SimpleNamespace(getresuid=lambda: uids, getresgid=lambda: gids, getgroups=lambda: groups),
    )
    if valid:
        assert daemon.startup_principal() is (uids[0] == 0)
    else:
        with pytest.raises(ValueError, match="refused"):
            daemon.startup_principal()


def status_body():
    values = facts(inheritable=0x80, ambient=0x80)
    return b"Name:\towned-source-test\n" + b"".join(
        f"{key}:\t{value:016x}\n".encode()
        if key.startswith("Cap")
        else f"{key}:\t{value}\n".encode()
        for key, value in values.items()
    )


@pytest.mark.parametrize("kind", ["valid", "duplicate", "missing", "negative", "wide", "large"])
def test_actual_owned_file_parser_is_bounded_strict_and_closes_descriptor(
    tmp_path, monkeypatch, kind
):
    body = status_body()
    if kind == "duplicate":
        body += b"CapEff:\t00000000000000c0\n"
    elif kind == "missing":
        body = body.replace(b"Seccomp:\t2\n", b"")
    elif kind == "negative":
        body = body.replace(b"NoNewPrivs:\t1", b"NoNewPrivs:\t-1")
    elif kind == "wide":
        body = body.replace(b"00000000000000c0", b"100000000000000c0")
    elif kind == "large":
        body += b"x" * daemon.MAX_STARTUP_STATUS_BYTES
    leaf = tmp_path / "self-status"
    leaf.write_bytes(body)
    original = os.open
    opened = []

    def owned(path, flags):
        assert path == "/proc/self/status"
        assert flags & (os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        descriptor = original(leaf, flags)
        opened.append(descriptor)
        return descriptor

    monkeypatch.setattr(
        daemon, "os", SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})
    )
    monkeypatch.setattr(daemon.os, "open", owned)
    if kind == "valid":
        assert daemon.startup_status() == (facts(inheritable=0x80, ambient=0x80), len(body))
    else:
        with pytest.raises(ValueError, match="refused"):
            daemon.startup_status()
    assert len(opened) == 1
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(opened[0])


def test_real_proc_task_checks_close_fds_and_reject_an_actual_second_thread():
    program = """import importlib.util,os,sys,threading
spec=importlib.util.spec_from_file_location('owned_startup',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def fds():return len(os.listdir('/proc/self/fd'))
original=fds()
assert module.startup_task()==len(str(os.getpid()))
first,size=module.startup_status();assert size>0 and first['CapBnd']>=0
assert fds()==original
ready=threading.Event();release=threading.Event()
def held():ready.set();release.wait(3)
thread=threading.Thread(target=held);thread.start();assert ready.wait(1)
try:
 try:module.startup_task()
 except ValueError:pass
 else:raise AssertionError('two tasks accepted')
 assert fds()==original
finally:release.set();thread.join(2);assert not thread.is_alive()
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program, str(SCRIPT)],
        capture_output=True,
        timeout=8,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()


def test_real_help_has_no_capability_authority_socket_or_subprocess_effects():
    program = """import runpy,sys
protected=('/proc/','/sys/fs/selinux/','/etc/hfcache/','/run/hfcache-host-helper',
 '/usr/local/lib/hfcache-host-helper')
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and args[0].startswith(protected):
  raise AssertionError('help read host authority')
 if event in {'subprocess.Popen','socket.__new__'}:
  raise AssertionError('help created host resource')
 if event=='ctypes.dlsym' and args[1] in {'capget','capset','prctl'}:
  raise AssertionError('help touched capabilities')
sys.addaudithook(audit)
path=sys.argv[1];sys.argv=[path,'--help']
try:runpy.run_path(path,run_name='__main__')
except SystemExit as error:assert error.code==0
else:raise AssertionError('help did not exit')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program, str(SCRIPT)],
        capture_output=True,
        timeout=8,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
    assert b"usage:" in result.stdout


@pytest.mark.parametrize(
    "operation", ["serve", "observe-peer", "observe-guard", "--observer-stop-child"]
)
def test_main_repairs_before_module_loading_and_preserves_original_budget_clock(
    monkeypatch, operation
):
    events = []
    output = io.BytesIO()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), operation])
    monkeypatch.setattr(
        daemon, "time", SimpleNamespace(monotonic=lambda: events.append("clock") or 12.0)
    )
    monkeypatch.setattr(daemon, "os", SimpleNamespace(getuid=lambda: 0, geteuid=lambda: 0))
    monkeypatch.setattr(
        daemon, "sys", SimpleNamespace(stdout=SimpleNamespace(buffer=output), stderr=io.StringIO())
    )

    monkeypatch.setattr(daemon, "require_startup_domain", lambda: {"files": 2, "bytes": 30})

    def cleared():
        assert events == ["clock"]
        events.append("cleared")
        return {"files": 4, "bytes": 214}

    labels = SimpleNamespace()
    hashes = {
        name: name
        for name in (
            "helper_daemon",
            "host_protocol",
            "host_selinux",
            "host_policy",
            "host_peer",
            "host_configuration",
            "host_actions",
        )
    }

    def observed(
        policy=None, *, bootstrap_work, started_at, host_labels=None, bootstrap_hashes=None
    ):
        assert events == ["clock", "cleared", "loaded"]
        assert bootstrap_work == {"files": 13, "bytes": 344}
        assert started_at == 12.0
        if operation == "--observer-stop-child":
            assert policy is protected_policy
            assert host_labels is labels
            assert bootstrap_hashes is hashes
        else:
            assert policy is None
            assert host_labels is None
            assert bootstrap_hashes is None
        events.append("observed")
        return {"observed": True}

    protected_policy = SimpleNamespace(observe_guard=observed)

    def loaded():
        assert events == ["clock", "cleared"]
        events.append("loaded")
        modules = {
            "host_peer": SimpleNamespace(observe_peer=observed),
            "host_policy": protected_policy,
            "host_protocol": SimpleNamespace(
                encode_object=lambda value: json.dumps(value).encode()
            ),
            "host_selinux": labels,
            "host_actions": SimpleNamespace(observer_signal_child=observed),
        }
        return modules, hashes, {"files": 7, "bytes": 100}

    monkeypatch.setattr(daemon, "clear_startup_capabilities", cleared)
    monkeypatch.setattr(daemon, "load_modules", loaded)
    monkeypatch.setattr(daemon.signal, "signal", lambda *_arguments: None)
    monkeypatch.setattr(
        daemon,
        "HostDaemon",
        lambda *_arguments: SimpleNamespace(serve=lambda: events.append("served")),
    )
    assert daemon.main() == 0
    assert events == [
        "clock",
        "cleared",
        "loaded",
        "served" if operation == "serve" else "observed",
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["--observer-stop-child", "serve"],
        ["--observer-stop-child", "observe-peer"],
        ["--observer-stop-child", "--pid", "123"],
        ["observer-stop-child"],
        ["serve", "--unit", "hfcache-api.service"],
    ],
)
def test_observer_child_flag_has_no_selector_or_ambiguous_operation_fallback(
    monkeypatch, arguments
):
    def forbidden():
        pytest.fail("invalid child arguments reached privileged startup")

    monkeypatch.setattr(sys, "argv", [str(SCRIPT), *arguments])
    monkeypatch.setattr(daemon, "require_startup_domain", forbidden)
    monkeypatch.setattr(daemon, "load_modules", forbidden)
    with pytest.raises(SystemExit) as result:
        daemon.main()
    assert result.value.code == 2


def test_failed_capability_repair_does_not_load_modules_or_delegated_code(monkeypatch):
    events = []
    error = io.StringIO()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "serve"])
    monkeypatch.setattr(daemon, "os", SimpleNamespace(getuid=lambda: 0, geteuid=lambda: 0))
    monkeypatch.setattr(daemon, "sys", SimpleNamespace(stderr=error))

    def refused():
        message = "must never publish these private facts"
        raise ValueError(message)

    monkeypatch.setattr(daemon, "require_startup_domain", lambda: {"files": 2, "bytes": 30})
    monkeypatch.setattr(daemon, "clear_startup_capabilities", refused)
    monkeypatch.setattr(daemon, "load_modules", lambda: events.append("loaded"))
    assert daemon.main() == 20
    assert events == []
    assert "private facts" not in error.getvalue()


def test_observer_failure_keeps_suppressed_context_without_private_text(monkeypatch):
    output = io.BytesIO()
    error = io.StringIO()
    namespace = {}
    source = (
        "def observe_peer(**kwargs):\n"
        "    try:\n"
        "        raise PermissionError(13, 'PRIVATE /credential/path argv=secret pid=123')\n"
        "    except PermissionError:\n"
        "        raise ValueError('PRIVATE payload') from None\n"
    )
    exec(compile(source, str(daemon.LIBRARY / "host_peer.py"), "exec"), namespace)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "observe-peer"])
    monkeypatch.setattr(
        daemon, "sys", SimpleNamespace(stdout=SimpleNamespace(buffer=output), stderr=error)
    )
    monkeypatch.setattr(daemon, "require_startup_domain", lambda: {"files": 0, "bytes": 0})
    monkeypatch.setattr(daemon, "clear_startup_capabilities", lambda: {"files": 0, "bytes": 0})
    monkeypatch.setattr(
        daemon,
        "load_modules",
        lambda: (
            {"host_peer": SimpleNamespace(observe_peer=namespace["observe_peer"])},
            {},
            {"files": 0, "bytes": 0},
        ),
    )
    assert daemon.main() == 20
    assert output.getvalue() == b""
    lines = error.getvalue().splitlines()
    assert lines[0] == (
        "protected host helper unavailable; preserve state and inspect fixed prerequisites"
    )
    metadata = json.loads(lines[1].removeprefix("protected host helper failure "))
    assert metadata["operation"] == "observe-peer"
    assert [row["error_class"] for row in metadata["errors"]] == ["ValueError", "PermissionError"]
    assert [row["errno"] for row in metadata["errors"]] == [None, 13]
    assert metadata["errors"][1]["frames"] == [
        {"module": "host_peer", "function": "observe_peer", "line": 3}
    ]
    for excluded in (
        "PRIVATE",
        "/credential",
        "argv",
        "pid",
        "payload",
        str(SCRIPT),
        str(daemon.LIBRARY),
    ):
        assert excluded not in error.getvalue()


def test_failure_metadata_bounds_chains_frames_and_rejects_unprotected_locations():
    namespace = {}
    source = (
        "def recurse(depth):\n"
        "    if depth:\n"
        "        return recurse(depth - 1)\n"
        "    raise RuntimeError('PRIVATE')\n"
    )
    exec(compile(source, str(daemon.LIBRARY / "host_policy.py"), "exec"), namespace)
    with pytest.raises(RuntimeError) as captured:
        namespace["recurse"](80)
    original = captured.value
    current = original
    for _ in range(10):
        linked = RuntimeError("PRIVATE").with_traceback(original.__traceback__)
        current.__cause__ = linked
        current = linked
    current.__context__ = original
    metadata = daemon.failure_metadata(original, "PRIVATE operation")
    assert metadata["operation"] == "unknown"
    assert len(metadata["errors"]) == daemon.MAX_FAILURE_ERRORS
    for row in metadata["errors"]:
        assert len(row["frames"]) == daemon.MAX_FAILURE_FRAMES
        assert all(frame["module"] == "host_policy" for frame in row["frames"])
        assert all(frame["function"] == "recurse" for frame in row["frames"])
    body = json.dumps(metadata)
    assert len(body) <= daemon.MAX_FAILURE_BYTES
    assert "PRIVATE" not in body
    assert str(SCRIPT) not in body


def test_failure_metadata_does_not_stringify_arbitrary_exception_classes_or_errnos():
    class PrivateError(OSError):
        def __str__(self):
            raise AssertionError

        def __repr__(self):
            raise AssertionError

    error = PrivateError(99999999999999999, "PRIVATE")
    error.__context__ = error
    assert daemon.failure_metadata(error, "observe-engine") == {
        "operation": "observe-engine",
        "errors": [{"error_class": "OSError", "errno": None, "frames": []}],
    }


def test_failed_diagnostic_write_keeps_original_refusal_status(monkeypatch):
    class ClosedErrorStream:
        def write(self, _body):
            message = "PRIVATE stderr failure"
            raise OSError(message)

    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "observe-peer"])
    monkeypatch.setattr(daemon, "sys", SimpleNamespace(stderr=ClosedErrorStream()))
    monkeypatch.setattr(daemon, "require_startup_domain", lambda: daemon.refuse(condition=False))
    assert daemon.main() == 20


def test_startup_implementation_keeps_host_python312_syntax():
    ast.parse(SCRIPT.read_bytes(), feature_version=(3, 12))


def test_engine_branch_merges_original_startup_work_before_fixed_exec(monkeypatch):
    events = []
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "observe-engine"])
    monkeypatch.setattr(daemon.time, "monotonic", lambda: 20.0)
    monkeypatch.setattr(daemon, "require_startup_domain", lambda: {"files": 2, "bytes": 30})
    monkeypatch.setattr(daemon, "clear_startup_capabilities", lambda: {"files": 4, "bytes": 50})
    monkeypatch.setattr(daemon, "sys", SimpleNamespace(stderr=io.StringIO()))

    def engine(*, bootstrap_work, started_at):
        assert bootstrap_work == {"files": 10, "bytes": 180}
        assert started_at == 20.0
        events.append("engine-exec")
        raise SystemExit(0)  # A real fixed branch replaces its process by FD exec.

    monkeypatch.setattr(
        daemon,
        "load_modules",
        lambda: (
            {"host_peer": SimpleNamespace(observe_engine=engine)},
            {},
            {"files": 4, "bytes": 100},
        ),
    )
    with pytest.raises(SystemExit) as result:
        daemon.main()
    assert result.value.code == 0
    assert events == ["engine-exec"]


@pytest.mark.parametrize("terminal", [b"", b"\0", b"\n"])
@pytest.mark.parametrize("enforce", [b"1", b"1\n"])
def test_exact_enforcing_helper_domain_accepts_only_explicit_kernel_terminators(
    monkeypatch, terminal, enforce
):
    seen = []

    def read(path, *, owner):
        seen.append((path, owner))
        return enforce if path.name == "enforce" else daemon._STARTUP_SELINUX_CONTEXT + terminal

    monkeypatch.setattr(daemon, "startup_security_read", read)
    work = daemon.require_startup_domain()
    assert work == {
        "files": 2,
        "bytes": len(enforce) + len(daemon._STARTUP_SELINUX_CONTEXT) + len(terminal),
    }
    assert seen[0] == (Path("/sys/fs/selinux/enforce"), {0})
    assert seen[1][0] == Path(f"/proc/{os.getpid()}/attr/current")


@pytest.mark.parametrize(
    "context",
    [
        b"",
        b"system_u:system_r:unconfined_service_t:s0",
        b"x:hfcache_host_helper_t:s0",
        b"system_u:system_r:hfcache_host_helper_t:s0:c1",
        b"system_u:system_r:hfcache_host_helper_t:s0 ",
        b"system_u:system_r:hfcache_host_helper_t:s0\0\0",
        b"system_u:system_r:hfcache_host_helper_t:s0\0\n",
    ],
)
def test_other_context_or_extra_terminators_refuse(monkeypatch, context):
    monkeypatch.setattr(
        daemon,
        "startup_security_read",
        lambda path, **_: b"1" if path.name == "enforce" else context,
    )
    with pytest.raises(ValueError, match="refused"):
        daemon.require_startup_domain()


@pytest.mark.parametrize("value", [b"0", b"0\n", b" 1", b"1\0", b"1\n\n"])
def test_permissive_or_noncanonical_enforcement_refuses_before_domain_read(monkeypatch, value):
    seen = []

    def read(path, **_):
        seen.append(path)
        return value

    monkeypatch.setattr(daemon, "startup_security_read", read)
    with pytest.raises(ValueError, match="refused"):
        daemon.require_startup_domain()
    assert seen == [Path("/sys/fs/selinux/enforce")]


def test_domain_refusal_precedes_capability_repair_and_authority_loading(monkeypatch):
    events = []
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "observe-peer"])
    monkeypatch.setattr(daemon, "sys", SimpleNamespace(stderr=io.StringIO()))
    monkeypatch.setattr(daemon.time, "monotonic", lambda: events.append("clock") or 1.0)

    def refused():
        assert events == ["clock"]
        raise ValueError

    monkeypatch.setattr(daemon, "require_startup_domain", refused)
    monkeypatch.setattr(daemon, "clear_startup_capabilities", lambda: events.append("caps"))
    monkeypatch.setattr(daemon, "load_modules", lambda: events.append("modules"))
    assert daemon.main() == 20
    assert events == ["clock"]


def test_real_owned_kernel_reader_refuses_fifo_without_blocking_or_leaking(tmp_path):
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    before = len(list(Path("/proc/self/fd").iterdir()))
    with pytest.raises(ValueError, match="refused"):
        daemon.startup_security_read(fifo, owner={os.getuid()})
    assert len(list(Path("/proc/self/fd").iterdir())) == before
