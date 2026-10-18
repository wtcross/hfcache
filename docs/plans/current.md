# Current plan

| Field | Value |
| --- | --- |
| State | Active |
| Active plan | [Local rootless rollout](2026-10-18-plan-local-rootless-rollout.md) |
| Next task | [OPS-015](tasks/ops-015-rootless-container-runtime.md) |
| Blockers | None; later tasks wait for committed predecessors |
| Updated | 2026-10-18 |

OPS-014 is completed in its implementation commit; OPS-015 is next pending and
must be activated only after that commit exists. The read-only NAS mount and
blocked writers remain guarded. User-authorized local changes must preserve NAS
content/metadata and leave other hosts unchanged. No remote push or unrelated
backlog is selected; completed REST/MCP feature records remain history.
