# hfcache documentation

Choose a guide by the work you need to do. API metadata access and NFS payload
copying are separate paths.

| Audience | Start here | Reference |
| --- | --- | --- |
| Discovery reader/curator | [Tags and local discovery](discovery.md), [browser Library](web-ui/library.md), [exact repository details](web-ui/repository-details.md) | [Configuration](configuration.md), [CLI](cli.md), [REST](api.md), [MCP](mcp.md) |
| API reader | [Quickstart](quickstart.md) | [Client settings and reconnect](api-client.md), [CLI](cli.md), [REST API](api.md) |
| Writer administrator | [Deployment profiles](deployment-centos-stream-10.md), [operations](operations.md) | [Server](server.md), [archive policy](configuration.md), [recovery](recovery.md) |
| MCP client or administrator | [Connect and use fourteen metadata tools](mcp.md) | [Security](security.md), [consumer identity](consumers.md) |
| Model/dataset consumer | [Copy, verify and promote](consumers.md) | [Repository evidence and locator bases](web-ui/repository-details.md), [storage/export requirements](storage-requirements.md), [schemas](schemas.md) |
| Browser operator | [Cockpit guides](cockpit-plugin/README.md), [replacement web interface status](web-ui/README.md) | [Library search](web-ui/library.md), [administrator provisioning](web-ui/deployment.md), [host permissions](web-ui/administration.md), [configuration and tags](web-ui/configuration-and-tags.md), [original-operation recovery](web-ui/operations.md), [access/read troubleshooting](web-ui/troubleshooting.md), [Cockpit contract](cockpit.md) |
| Developer | [Setup and validation](development.md) | [Script catalog](scripts.md), [architecture](architecture.md), [invariants](invariants.md), [ADRs](adr/README.md) |

The [container contract](containers.md) covers pinned images, fixed roles,
listener readiness, credentials and executor drain. The
[recorded deployment scope](deployment-status.md) distinguishes demonstrated
local behavior from remaining acceptance. [Release notes](../CHANGELOG.md)
preserve breaking changes and rollback constraints.
