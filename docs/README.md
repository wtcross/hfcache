# hfcache documentation

Choose a guide by the work you need to do. API metadata access and NFS payload
copying are separate paths.

| Audience | Start here | Reference |
| --- | --- | --- |
| API reader | [Quickstart](quickstart.md) | [Client settings and reconnect](api-client.md), [CLI](cli.md), [REST API](api.md) |
| Writer administrator | [Deployment profiles](deployment-centos-stream-10.md), [operations](operations.md) | [Server](server.md), [archive policy](configuration.md), [recovery](recovery.md) |
| MCP client or administrator | [Connect and use nine metadata tools](mcp.md) | [Security](security.md), [consumer identity](consumers.md) |
| Model/dataset consumer | [Copy, verify and promote](consumers.md) | [Storage/export requirements](storage-requirements.md), [schemas](schemas.md) |
| Browser operator | [Cockpit guides](cockpit-plugin/README.md) | [Cockpit contract](cockpit.md) |
| Developer | [Setup and validation](development.md) | [Script catalog](scripts.md), [architecture](architecture.md), [invariants](invariants.md), [ADRs](adr/README.md) |

The [container contract](containers.md) covers pinned images, fixed roles,
listener readiness, credentials and executor drain. The
[recorded deployment scope](deployment-status.md) distinguishes demonstrated
local behavior from remaining acceptance. [Release notes](../CHANGELOG.md)
preserve breaking changes and rollback constraints.
