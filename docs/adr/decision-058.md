# The archive mount is defined by explicit units and the fstab line is retired

- Decision identity: 058.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Decision, context, and consequences

The host deployment contract permits either mechanism, and
the initial deployment used fstab. Keeping both is not a
third option: a unit in `/etc/systemd/system` shadows the one
`systemd-fstab-generator` produces from that line, so the file an operator
would edit first would have had no effect at all. The native packaging ships the two explicit units, so the units win and the fstab line is commented in place
with a pointer to them; `/etc/fstab.pre-hfcache-units` holds the original.

The handover was the risk — the working session depended on the archive mount — so it
was done with `daemon-reload` and nothing else. A reload re-reads unit files
and does not stop active units, and a mount unit's active state comes from
`/proc/self/mountinfo` rather than from its configuration. Confirmed after:
the same autofs file descriptor, the same NFS mount with the same options,
both units `active` and now sourced from `/etc/systemd/system`, and `status`
still reporting the archive reachable. The unit's `Options=` apply from the
next mount, not to the one already established, which is why `systemctl show`
still lists the fstab-era `x-systemd.*` options.

Two findings worth keeping. **`systemd-analyze verify` exits `0` while
reporting ordering cycles**, so its *output* is the gate and its exit status
is not — the same lesson as piping a gate into `grep`. And the first
automount unit had one: `After=network-online.target` on the *automount*
produced `local-fs.target → srv-hfcache.automount → network-online.target →
NetworkManager.service → sysinit.target → local-fs.target`, because systemd
gives every automount unit an implicit `Before=local-fs.target`. Network
ordering belongs on the mount, which is the unit that contacts the NAS; an
automount is a kernel trigger on a directory and needs nothing. The
fstab generator had it right, and comparing against what it produced —
`systemctl show` on the generated units, before the reload replaced them —
is what found it.

`hfcache.target` does **not** list the timers in `Wants=`. The original target proposal wanted
the automount and both timers, but a `Wants=` starts a unit
whether or not it is enabled, and the deployment contract requires the quarterly verification
timer to stay off until an operator confirms its calendar against the NAS
schedules. The timers attach through their own `[Install]
WantedBy=hfcache.target` instead, so what the target wants is exactly what
has been enabled and "installed but disabled" is a state the design can
actually express.

## Provenance and governing evidence

The source entry first appears in
[2fd432a](https://github.com/wtcross/hfcache/commit/2fd432aaba6a8df2561f66b3c00264e1675f1427)
(2026-07-26, `host integration: install and validate the systemd target, services, and
timers`). The decision retains its rationale, alternatives and consequences.

Current governing documents:
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md)

Implementation or shipped-artifact evidence:
[packaging/systemd/srv-hfcache.mount](../../packaging/systemd/srv-hfcache.mount),
[packaging/systemd/srv-hfcache.automount](../../packaging/systemd/srv-hfcache.automount),
[packaging/systemd/hfcache.target](../../packaging/systemd/hfcache.target).

Relevant verification:
[scripts/check-hardening.sh](../../scripts/check-hardening.sh).
