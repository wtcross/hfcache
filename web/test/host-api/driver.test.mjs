/** Metadata and owned HTTP checks; no browser or installed fixture is launched. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import test from "node:test";
import {
    assertHostStatus,
    assertObservedHostStatus,
    assertProblem,
    readBrowserJSON,
} from "./driver.mjs";

const original = JSON.parse(
    await readFile(
        new URL(
            "../../../tests/fixtures/schemas/host-status.json",
            import.meta.url,
        ),
        "utf8",
    ),
);

function fixture(profile = "rootless") {
    const status = JSON.parse(JSON.stringify(original));
    status.profile = profile;
    if (profile === "native")
        for (const name of ["schedule", "observer"])
            status.permission_reasons[name] = "policy-denied";
    return {
        status,
        runtime: { profile },
        manifest: {
            profiles: {
                [profile]: {
                    deployment: { sha256: status.binding.deployment_sha256 },
                    policy: { sha256: status.binding.policy_sha256 },
                },
            },
        },
    };
}

for (const profile of ["native", "rootless"])
    test(`exact ${profile} config-only status preserves observed absent guard`, () => {
        const { status, runtime, manifest } = fixture(profile);
        assert.equal(
            assertHostStatus(status, runtime, manifest, "baseline"),
            status,
        );
    });

for (const [label, alter] of [
    [
        "unknown grant",
        (status) => {
            status.permissions.archive = true;
        },
    ],
    [
        "false policy",
        (status) => {
            status.binding.policy_sha256 = "0".repeat(64);
        },
    ],
    [
        "wrong profile",
        (status) => {
            status.profile = "native";
        },
    ],
    [
        "held guard substitution",
        (status) => {
            status.facts.guard = "held";
        },
    ],
    [
        "extra key",
        (status) => {
            status.unaccounted = true;
        },
    ],
])
    test(`observed status refuses ${label}`, () => {
        const { status, runtime, manifest } = fixture();
        alter(status);
        assert.throws(() =>
            assertHostStatus(status, runtime, manifest, "baseline"),
        );
    });

function unavailable(reason) {
    return {
        schema_version: 1,
        state: "unavailable",
        reason,
        profile: null,
        binding: null,
        facts: null,
        permissions: Object.fromEntries(
            Object.keys(original.permissions).map((key) => [key, false]),
        ),
        permission_reasons: Object.fromEntries(
            Object.keys(original.permissions).map((key) => [
                key,
                "helper-unavailable",
            ]),
        ),
    };
}

test("real timeout requires timeout classification, never generic unavailability", () => {
    assertHostStatus(unavailable("helper-timeout"), {}, {}, "timeout");
    assert.throws(() =>
        assertHostStatus(unavailable("helper-refused"), {}, {}, "timeout"),
    );
});

test("unavailable status never grants a partial permission", () => {
    const status = unavailable("helper-unavailable");
    status.permissions.configuration = true;
    assert.throws(() => assertHostStatus(status, {}, {}, "helper-down"));
});

test("actual flat API problem schemas distinguish denied from unavailable", () => {
    for (const [status, code, exit_code] of [
        [403, "HFAPI002", 10],
        [503, "HFAPI022", 20],
    ]) {
        const problem = {
            request_id: "a".repeat(32),
            code,
            message: "fixed public diagnostic",
            exit_code,
        };
        assert.deepEqual(assertProblem(problem, status, code), {
            request_id: problem.request_id,
            status,
            error_code: code,
        });
        assert.throws(() =>
            assertProblem(problem, status === 403 ? 503 : 403, code),
        );
        assert.throws(() =>
            assertProblem(
                { ...problem, raw_exception: "unknown" },
                status,
                code,
            ),
        );
        if (code === "HFAPI002")
            assert.throws(() =>
                assertProblem({ ...problem, exit_code: 2 }, status, code),
            );
    }
});

async function withServer(handler, operation) {
    const server = createServer(handler);
    await new Promise((resolve, reject) => {
        server.once("error", reject);
        server.listen(0, "127.0.0.1", resolve);
    });
    try {
        return await operation(
            `http://127.0.0.1:${server.address().port}/api/v1/host/status`,
        );
    } finally {
        server.closeAllConnections();
        await new Promise((resolve, reject) =>
            server.close((error) => (error ? reject(error) : resolve())),
        );
    }
}

// Run the page callback against owned real HTTP bytes. Installed browser/Caddy
// acceptance separately proves the actual page realm, TLS and native auth.
const pageCallback = { evaluate: (operation, argument) => operation(argument) };

for (const status of [200, 403])
    test(`page JSON read preserves one HTTP${status} reply and request identity`, async () => {
        let requests = 0;
        const body = { schema_version: 1, observed: status };
        await withServer(
            (request, reply) => {
                requests += 1;
                assert.equal(request.method, "GET");
                assert.equal(request.url, "/api/v1/host/status");
                reply.writeHead(status, {
                    "Content-Type": "application/json",
                    "X-Request-ID": "a".repeat(32),
                });
                reply.end(JSON.stringify(body));
            },
            async (url) => {
                assert.deepEqual(await readBrowserJSON(pageCallback, url), {
                    status,
                    request_id: "a".repeat(32),
                    body,
                });
            },
        );
        assert.equal(requests, 1);
    });

test("invalid page JSON fails without another request", async () => {
    let requests = 0;
    await withServer(
        (_request, reply) => {
            requests += 1;
            reply.writeHead(200, { "Content-Type": "application/json" });
            reply.end("invalid JSON");
        },
        async (url) => {
            await assert.rejects(
                readBrowserJSON(pageCallback, url),
                SyntaxError,
            );
        },
    );
    assert.equal(requests, 1);
});

test("failed page execution has no Node-side request fallback", async () => {
    const failure = new Error("modeled page execution closed");
    let requests = 0;
    await withServer(
        (_request, reply) => {
            requests += 1;
            reply.end("{}");
        },
        async (url) => {
            await assert.rejects(
                readBrowserJSON(
                    {
                        evaluate: async () => {
                            throw failure;
                        },
                    },
                    url,
                ),
                (error) => error === failure,
            );
        },
    );
    assert.equal(requests, 0);
});

for (const profile of ["native", "rootless"])
    test(`supported ${profile} status keeps original acceptance and bounded observation`, () => {
        const { status, runtime, manifest } = fixture(profile);
        const evidence = {};
        assert.equal(
            assertObservedHostStatus(
                evidence,
                status,
                runtime,
                manifest,
                "baseline",
            ),
            status,
        );
        assert.equal(evidence.host_status, status);
        assert.deepEqual(evidence.host_status_observation, {
            state: "supported",
            reason: null,
            profile,
        });
    });

for (const reason of ["helper-refused", "helper-timeout", "facts-unavailable"])
    test(`failed baseline retains typed ${reason} without accepting the status`, () => {
        const evidence = {};
        const status = unavailable(reason);
        assert.throws(() =>
            assertObservedHostStatus(evidence, status, {}, {}, "baseline"),
        );
        assert.deepEqual(evidence.host_status_observation, {
            state: "unavailable",
            reason,
            profile: null,
        });
        assert.equal(Object.hasOwn(evidence, "host_status"), false);
    });

test("pre-assert evidence excludes all unselected response fields", () => {
    const evidence = {};
    const status = {
        ...unavailable("helper-refused"),
        private_detail: "UNSELECTED_PRIVATE_VALUE",
    };
    assert.throws(() =>
        assertObservedHostStatus(evidence, status, {}, {}, "baseline"),
    );
    assert.equal(
        JSON.stringify(evidence).includes("UNSELECTED_PRIVATE_VALUE"),
        false,
    );
    assert.deepEqual(Object.keys(evidence.host_status_observation).sort(), [
        "profile",
        "reason",
        "state",
    ]);
});

for (const field of ["state", "reason", "profile"])
    test(`unknown ${field} is refused without copying free text into evidence`, () => {
        const evidence = {};
        const status = {
            ...unavailable("helper-refused"),
            [field]: "UNRECOGNIZED_PRIVATE_VALUE",
        };
        assert.throws(() =>
            assertObservedHostStatus(evidence, status, {}, {}, "baseline"),
        );
        assert.deepEqual(evidence, {});
    });

test("guarded status is retained before baseline acceptance fails", () => {
    const { status, runtime, manifest } = fixture();
    status.state = "guarded";
    status.facts.guard = "held";
    const evidence = {};
    assert.throws(() =>
        assertObservedHostStatus(
            evidence,
            status,
            runtime,
            manifest,
            "baseline",
        ),
    );
    assert.deepEqual(evidence.host_status_observation, {
        state: "guarded",
        reason: null,
        profile: "rootless",
    });
    assert.equal(Object.hasOwn(evidence, "host_status"), false);
});

test("unknown authority is retained without accepting the baseline", () => {
    const status = {
        ...unavailable("deployment-unverified"),
        state: "unknown",
    };
    const evidence = {};
    assert.throws(() =>
        assertObservedHostStatus(evidence, status, {}, {}, "baseline"),
    );
    assert.deepEqual(evidence.host_status_observation, {
        state: "unknown",
        reason: "deployment-unverified",
        profile: null,
    });
    assert.equal(Object.hasOwn(evidence, "host_status"), false);
});
