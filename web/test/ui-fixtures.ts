/** Hand-authored protocol fixtures; no fixture bootstrap is shipped in the app. */
import type { UiBootstrap } from "../src/wire/generated";
import { WIRE_SOURCE_DIGEST } from "../src/wire/generated";
export function uiBootstrapFixture(): UiBootstrap {
    return {
        schema_version: 1,
        kind: "hfcache_ui_bootstrap",
        ui_contract_version: 1,
        rest_api_schema_version: 1,
        wire_source_digest: WIRE_SOURCE_DIGEST,
        instance_id: "1".repeat(32),
        authority_epoch: "1".repeat(32),
        configured_archive_id: "12345678-1234-1234-1234-123456789abc",
        archive_identity_source: "installed_policy",
        config_fingerprint: null,
        configured_origin: "https://archive.invalid",
        paths: {
            public_prefix: "",
            effective_prefix: "",
            ui_base: "/ui/",
            bootstrap: "/ui/bootstrap.json",
            api_base: "/api/v1",
            mcp_base: "/mcp/",
        },
        user: {
            subject: "administrator",
            display_name: "administrator",
            authentication_method: "basic",
            credential_class: "rest-writer",
            rest_capabilities: ["read", "write"],
            admin_permissions: [
                "config-read",
                "config-write",
                "host-read",
                "observer-stop",
                "schedule-write",
            ].map((capability) => {
                switch (capability) {
                    case "config-read":
                    case "config-write":
                    case "host-read":
                    case "observer-stop":
                    case "schedule-write":
                        return {
                            capability,
                            granted: true,
                            effective: false,
                            reason: "feature_unavailable",
                        };
                    default:
                        throw new Error("Unknown fixture permission.");
                }
            }),
        },
        build: {
            asset_manifest_sha256: "2".repeat(64),
            metadata: {
                application_version: "0.2.2",
                source_commit: "3".repeat(40),
                source_snapshot_sha256: "4".repeat(64),
                source_dirty: true,
                ui_contract_version: 1,
                rest_api_schema_version: 1,
                wire_source_digest: WIRE_SOURCE_DIGEST,
                pnpm_lock_sha256: "5".repeat(64),
                toolchain: {
                    node: "24.18.1",
                    pnpm: "11.18.0",
                    typescript: "6.0.3",
                    vite: "8.3.4",
                },
                toolchain_sha256:
                    "3e32946e5658f85022f956da102a251778d6c5e942d05ba98bedbea5de8b3f45",
                licenses_sha256: "6".repeat(64),
                notices_sha256: "7".repeat(64),
            },
        },
    };
}
export function inertUiDocument(document: Document): void {
    document.head.innerHTML =
        '<base href="/ui/"><meta name="hfcache-ui-base" content="/ui/"><meta name="hfcache-ui-bootstrap" content="/ui/bootstrap.json"><meta name="hfcache-ui-fingerprint" content="' +
        "2".repeat(64) +
        '"><meta name="hfcache-ui-contract" content="1">';
    document.body.innerHTML =
        '<div id="root"><main aria-label="Interface startup"><h1>Starting hfcache</h1><p>The interface has not started.</p><a href="./">Reload interface</a></main></div>';
}
