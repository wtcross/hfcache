"""Disposable process fixtures for the actual systemd descriptor ABI."""

import os
import subprocess
import sys
from contextlib import contextmanager

# Duplicate first: descriptor order may differ and a source can already be fd3/4.
_TRAMPOLINE = """
import os, sys
original = [int(value) for value in sys.argv[1].split(',')]
copies = [os.dup(descriptor) for descriptor in original]
targets = set(range(3, 3 + len(copies)))
for target, descriptor in enumerate(copies, 3):
    os.dup2(descriptor, target, inheritable=True)
    os.set_inheritable(target, True)
for descriptor in set(original + copies) - targets:
    os.close(descriptor)
pid = os.environ.pop('ACTIVATION_TEST_PID', 'current')
if pid != 'missing':
    os.environ['LISTEN_PID'] = str(os.getpid()) if pid == 'current' else pid
pidfd = os.environ.pop('ACTIVATION_TEST_PIDFD', None)
if pidfd:
    descriptor = os.pidfd_open(os.getpid())
    os.environ['LISTEN_PIDFDID'] = str(os.fstat(descriptor).st_ino) if pidfd == 'valid' else '0'
    os.close(descriptor)
os.execv(sys.executable, [sys.executable, *sys.argv[2:]])
"""


@contextmanager
def activated_process(arguments, descriptors, *, environment, extra_fds=()):
    """Hand only declared fixture descriptors to a new interpreter and always join."""
    process = subprocess.Popen(
        [sys.executable, "-c", _TRAMPOLINE, ",".join(map(str, descriptors)), *arguments],
        pass_fds=(*descriptors, *extra_fds),
        env={"PATH": os.environ["PATH"], "LANG": "C.UTF-8"} | environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)
