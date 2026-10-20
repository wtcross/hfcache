/** Independent literal wires for transport/view adversaries, never generated IR. */
export const REQUEST_ID = "1".repeat(32);
export const ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90";
export const versionPayload = {
    application: "independent-version",
    python: "fixture-python",
    huggingface_hub: "fixture-hub",
    transfer_backend: "http",
};
export function readWire(command: string, data: unknown, failed = false) {
    return {
        schema_version: 1,
        request_id: REQUEST_ID,
        archive_id:
            command === "status" || command === "archive init"
                ? ARCHIVE_ID
                : null,
        config_fingerprint:
            command === "status" || command === "archive init"
                ? "2".repeat(64)
                : null,
        envelope: {
            schema_version: 1,
            command,
            run_id: "3".repeat(32),
            started_at: "2026-10-20T12:00:00.000001Z",
            completed_at: "2026-10-20T12:00:00.000002Z",
            outcome: failed ? "failed" : "success",
            exit_code: failed ? 20 : 0,
            data,
            warnings: [],
            errors: failed
                ? [
                      {
                          code: "HFMNT001",
                          message:
                              "Private original detail must not become HTML",
                          context: {},
                          repository: null,
                      },
                  ]
                : [],
        },
        next_cursor: null,
    };
}
export function jsonResponse(value: unknown, status = 200) {
    return new Response(JSON.stringify(value), {
        status,
        headers: { "Content-Type": "application/json" },
    });
}
export const capabilitiesPayload = {
    api_version: 1,
    credential_class: "rest-reader",
    capabilities: ["read"],
    instance_id: "4".repeat(32),
    reads: true,
    operations: true,
    operation_history: true,
    mcp: false,
    maintenance_enabled: false,
    max_page_size: 1000,
};
export function statusPayload(reachable: boolean) {
    const archive = {
        archive_id: ARCHIVE_ID,
        root: "/independent-fixture/archive",
        reachable,
        verification: {
            degraded: false,
            last_full_verification: null,
            outstanding_failures: 0,
        },
    };
    return {
        archive: reachable
            ? {
                  ...archive,
                  available_bytes: 0,
                  available_gib: 0,
                  headroom_bytes: 0,
                  reserve_bytes: 0,
                  total_bytes: 0,
                  deferred_cleanup: 0,
                  findings: [],
                  unfinished_transactions: 0,
                  unknown_entries: [],
                  quarantined_bytes: 0,
              }
            : archive,
        repositories: [],
    };
}
export const inspectionPayload = {
    adopted_published: false,
    archive_id: null,
    archive_root: "/independent-fixture/archive",
    existing_directories: [],
    initializable: false,
    leftover_temporaries: [],
    missing_directories: [],
    mount: {
        exists: false,
        filesystem_type: null,
        is_mount_point: false,
        read_only: null,
        source: null,
    },
    state: "unusable",
    unknown_entries: [],
    unknown_entry_count: 0,
};
export function problemWire(code = "HFAPI001", exit_code = 10) {
    return {
        request_id: REQUEST_ID,
        code,
        message: "Private service detail <script>never render</script>",
        exit_code,
    };
}
