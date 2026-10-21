# Finish owned foreground socket cleanup before replaying default SIGTERM

- Decision identity: 149.
- Status: Accepted.
- Date: 2026-10-20.

## Context

The foreground API bootstrap creates a Unix socket through a pinned parent and
owns that exact filesystem inode until its listener context exits. Uvicorn's
main-thread signal scope performs graceful application shutdown, restores its
previous handlers and then replays captured signals before returning to the
outer listener context. With the default SIGTERM action, the process can end
after lifespan shutdown but before its owned socket pathname is removed.
An owned installed control reproduces this ordering: the kernel listener and
process end while the unchanged socket node remains. A refused connection or
finished lifespan therefore does not establish owned pathname cleanup.

Activated listeners have another owner and lifetime. Their filesystem nodes
must remain under manager control. PID1, custom signal handlers and ignored
signals also have existing semantics that this correction must preserve.

## Decision and rationale

Use a private, main-thread signal scope around the complete foreground listener
resource scope. It is eligible only when the process is not PID1 and the saved
SIGTERM handler is the default action. Arm it only after a foreground Unix
socket's exact device/inode ownership and configured mode have been recorded.
TCP-only and activated paths do not arm this behavior.

The first deferred SIGTERM records that it is pending and raises a private
`BaseException` to unwind the outer listener context. Further SIGTERM deliveries
while that cleanup runs do not interrupt it. Catch that private exception only
when this same signal scope has a pending delivery; an exception from another
scope must propagate. Keep the signal scope outside the existing listener
`try`/`finally`, so socket close, exact owned-node removal and pinned-parent close
all precede restoring the original handler and delivering the original SIGTERM.

Keep Uvicorn's normal graceful-lifecycle handler while it serves. This scope
handles the later restored-handler/replay boundary; it does not replace joins,
shorten shutdown budgets or convert signal termination into success or a typed
startup error. Existing custom handlers, `SIG_IGN`, non-main threads, PID1 and
manager-owned activation are unchanged. Unknown, pre-existing or replaced nodes
remain preserved under the original exact device/inode test.

A broad signal handler, unconditional pathname unlink, altered activation
lifetime or successful-exit substitution would change unrelated ownership or
termination contracts. Keeping the scope private and arming only after owned
Unix bookkeeping addresses the reproduced boundary without those changes.

## Consequences and validation

Normal return and startup failure retain their existing classifications. Default
SIGTERM still terminates the eligible process by the original signal, after the
owned foreground listener context has unwound. This does not provide cleanup
under SIGKILL, interpreter failure or other forced process death. A leftover node
from such a termination remains evidence; startup must continue to refuse it.
No operator should delete or replace an unexplained socket to manufacture drain.

Regression evidence must include an actual owned foreground server subprocess:
real SIGTERM, completed application shutdown, original signal exit and removal
of only the original owned socket. Tests also cover repeated TERM during cleanup,
replaced-node preservation, normal return/startup failure, handler restoration,
custom/ignored handlers and the PID1/main-thread/activation exclusions. Passing
source tests and an owned control do not establish a production rollout or
complete installed application acceptance.

- [Foreground server contract](../server.md#foreground-listener-bootstrap)
- [Listener ownership and bootstrap](../../src/hfcache/server.py)
- [Foreground signal ownership tests](../../tests/unit/test_server_signals.py)
- [Foreground bootstrap tests](../../tests/unit/test_server_bootstrap.py)
- [Activated listener tests](../../tests/unit/test_server_activation.py)
- [Decision 113](decision-113.md) owns the shared application lifespan;
  this decision amends only foreground default-SIGTERM cleanup ordering.
- [Decision 121](decision-121.md) retains manager-owned listener lifetime and
  strict activation unchanged.
