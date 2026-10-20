# Start here — Cockpit REST repair plan bundle

This archive contains only new files under `docs/agents/plans/`. It has no outer
wrapper directory, no application patch, no credentials or installed configuration,
and no replacement `current.md` or progress log. Extraction proposes work; it does
not activate a plan or authorize implementation/production operations.

## Extract into the repository

From outside or inside the repository, choose the actual paths:

```sh
# Refuse overwriting an existing file. No current.md is in this archive.
tar --keep-old-files -xzf /path/to/hfcache-cockpit-rest-repair-plan.tar.gz \
    -C /path/to/hfcache
```

The equivalent ZIP extraction preserves existing files:

```sh
unzip -n /path/to/hfcache-cockpit-rest-repair-plan.zip -d /path/to/hfcache
```

Inspect any collision before proceeding: ZIP's no-overwrite mode may skip it.
Never extract with an overwrite option merely to replace an earlier plan. Check
the supplied bundle-manifest.json against the extracted contents; it lists every
payload file and its SHA-256, excluding the manifest itself to avoid self-hashing.

## Review and execution

Read the [dated plan](../../2026-10-19-plan-cockpit-rest-repair.md) and
[audit](audit.md), then the [design](design.md) and [surface map](surface-map.md).
The main plan links all nine work packages in order. Tasks start `pending`, and
the plan remains `draft`. The reviewed baseline is `dcc2c562b52304541d0cb85d20fc046072038e79`; compare actual HEAD
before relying on any path or finding.

The current source already uses a REST-backed CLI. Do not replace it with browser
tokens, native-local fallback, MCP writes, arbitrary HTTP forwarding or a new
service. Preserve the guarded host configuration installer and current workload
holds. In particular, the reported `reconnected` message does not establish that
the daemon crashed or that no operation was admitted.

To implement, issue the separate instruction in [implementation-prompt.md](implementation-prompt.md).
That instruction selects the dedicated branch and project workflow. Merely reading
or extracting this file is not implementation authorization. No old plan/current
tracker/handoff should be silently overwritten.

## Contents

The bundle contains a draft main plan, nine work-package task files, the audit,
design, surface map, 60-case validation matrix, diagnosis runbook, pinned source
review, start/resume prompt, empty acceptance record and a content manifest.
The accompanying SHA-256 file outside the archive verifies the downloadable
archives; their contents are the same project-relative payload.

## Review limitations

The review used pinned GitHub source and official Cockpit documentation. It did
not access the installed writer, capture its browser logs, run the product gate,
execute a full repository checkout, test Podman/PAM/systemd, or fix application
code. Archive creation and manifest/path/link checks are packaging validation,
not product acceptance. Use the acceptance record to keep those claims separate.
