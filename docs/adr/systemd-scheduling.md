# Keep host scheduling in systemd timers and drop-ins

- Status: accepted; an existing locked plan decision without an AD number.
- Original record: 2026-07-24, `87323c2` (initial plan, §4 and §22).
- ADR backfill: 2026-10-17.
- Authority: [plan §22](../plan.md#22-systemd-design),
  [operations §9](../operations.md), and
  [Cockpit schedule contract](../cockpit.md#7-sync-schedule) remain
  normative. Maintain this record under [the ADR policy](README.md).

## Context

Unattended sync and full verification require host lifecycle management,
mount ordering, credentials, hardening, and visible command exit status.
The application TOML describes archive and sync policy; a second scheduler
inside the process would duplicate host-level authority.

## Decision

Use distinct systemd oneshot services and calendar timers for sync and full
verification. Keep scheduling in timer units and local drop-ins, outside
application TOML. Use `hfcache.target` to group the scheduled lifecycle and
archive automount. Attach timers through their own `[Install] WantedBy=` so
an installed-but-disabled verification timer stays disabled when the target
starts.

The shipped initial calendars are daily sync at 02:00 local time and full
verification on the first Wednesday of January, April, July, and October
at 04:00. Use `Persistent=true`, documented random delays, and calendar
validation with `systemd-analyze calendar`. Operator schedule changes use
drop-ins rather than editing shipped units. Cockpit pauses or resumes only
the sync timer, because stopping the target also affects the archive mount.

## Rationale and alternatives

The original locked table explicitly selects systemd timers and drop-ins
and distinguishes scheduling from TOML policy; it does not enumerate
competing scheduler products. Systemd supplies the host lifecycle and
status boundary already required by the deployment.

Decision 58 rejects putting timers directly in the target's `Wants=`,
which would start disabled timers, and retaining an fstab entry shadowed
by explicit units. It also records that network ordering belongs on the
mount, since the automount's implicit local-filesystem ordering otherwise
creates a boot cycle. CP-12 rejects editing packaged timer units for local
schedule changes.

## Consequences

An elapsed timer while the same oneshot service is running merges into
that active run; it does not create parallel syncs or queue every missed
observation. Persistent catch-up covers elapsed events while the host was
down. Manual invocations and different services remain serialized by the
shared application lock (AD-17). The verification timer still requires
operator coordination before activation. Judge `systemd-analyze verify`
by its output, since an ordering diagnostic can accompany exit zero.

## History and evidence

`87323c2` (2026-07-24) records scheduling authority and initial calendars.
`2fd432a` (`SYS-001`, 2026-07-26),
[decision 58](decision-058.md), installs and validates all seven units
and records disabled-timer and mount-ordering corrections. `ea8c02c`
(`DOC-008`, 2026-07-28) documents long-running timer semantics.
`1a0be5d` (`CPT-009`, 2026-07-30) implements the Cockpit drop-in editor.

- [Shipped sync timer](../../packaging/systemd/hfcache-sync.timer).
- [Shipped verification timer](../../packaging/systemd/hfcache-verify.timer).
- [Lifecycle target and enabled-timer boundary](../../packaging/systemd/hfcache.target).
- [Host install and calendar validation runbook](../deployment-centos-stream-10.md).
- [Cockpit drop-in validation and writes](../../cockpit/src/api/schedule.ts).
- [Drop-in rendering, round-trip, and calendar-output tests](../../cockpit/test/schedule.test.ts).
- [Shared local lock tests](../../tests/unit/test_locking.py).
