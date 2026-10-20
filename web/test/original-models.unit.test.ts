/** Independent original Python serializers are the valid-wire oracle. */
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";
import {
    decodeNamed,
    routeContracts,
    routeDefinitions,
    operationResultDefinitions,
    decodeOriginalOperationPayload,
} from "../src/wire/generated";
import { parseWireJson, WireError } from "../src/wire/json";
import { wireArray, wireObject, wireString } from "../src/wire/runtime";

const generated = spawnSync(
    "uv",
    [
        "run",
        "--locked",
        "--extra",
        "server",
        "--extra",
        "mcp",
        "python",
        "-c",
        "import json; from tests.web_wire_corpus import serialized_corpus, malformed_serialized_corpus; print(json.dumps({'originals':serialized_corpus(),'incorrect':malformed_serialized_corpus()}, ensure_ascii=False))",
    ],
    {
        cwd: fileURLToPath(new URL("../../", import.meta.url)),
        encoding: "utf8",
        timeout: 60000,
        maxBuffer: 8 * 1024 * 1024,
    },
);
if (
    generated.error !== undefined ||
    generated.signal !== null ||
    generated.status !== 0
)
    throw new Error("Original Python serializer corpus failed.");
const sourceCorpus = wireObject(parseWireJson(generated.stdout), [
    "originals",
    "incorrect",
]);
function corpusEntry(entry: unknown) {
    const item = wireObject(entry, ["case_id", "definition", "value"]);
    return {
        id: wireString(item.case_id, 1, 256, null),
        definition: wireString(item.definition, 1, 128, null),
        value: item.value,
    };
}
const corpus = wireArray(sourceCorpus.originals, corpusEntry, 1, 512);
const incorrect = wireArray(sourceCorpus.incorrect, corpusEntry, 1, 2048);
test.each(corpus)(
    "original source serializer $id validates without inventing API values",
    ({ definition, value }) => {
        expect(() => decodeNamed(definition, value)).not.toThrow();
    },
);
test.each(incorrect)(
    "original Python authority rejects malformed $id and browser agrees",
    ({ definition, value }) => {
        expect(() => decodeNamed(definition, value)).toThrow(WireError);
    },
);
test("every generated definition has an independently serialized source original", () => {
    // Exporter's separately audited coverage assertion owns the exact authority set.
    expect(new Set(corpus.map((item) => item.definition)).size).toBe(118);
});
test("route path/query schemas reconstruct explicit optional inputs and forbid extras", () => {
    for (const contract of Object.values(routeContracts)) {
        expect(() => contract.decodeQuery(parseWireJson("{}"))).not.toThrow();
        expect(() =>
            contract.decodeQuery(parseWireJson('{"unlisted":1}')),
        ).toThrow(WireError);
        if (!contract.path.includes("{"))
            expect(() =>
                contract.decodePath(parseWireJson("{}")),
            ).not.toThrow();
    }
});
test("every registered route decodes its independently chosen path/query inputs and source-serialized body/failure", () => {
    const pathValues: Readonly<Record<string, string>> = {
        repository_type: "model",
        namespace: "org",
        name: "name",
        revision: "current",
        commit_sha: "a".repeat(40),
        publication_id: "b".repeat(32),
        run_id: "c".repeat(32),
        operation_id: "d".repeat(32),
    };
    const queryValues: Readonly<Record<string, unknown>> = {
        type: "model",
        selector: ["model:org/name"],
        q: "literal search",
        tag_all: ["task:text-generation"],
        tag_any: ["library:pytorch"],
        tag_source: "current_or_last_observed",
        scope: "all",
        revision_scope: "retained",
        format: "gguf",
        quantization: "q4",
        quantization_method: "gguf",
        bits: 4,
        max_variant_bytes: 4096,
        limit: 10,
        cursor: "opaque-fixture-cursor",
        facet: "tag",
        commit_sha: "a".repeat(40),
        publication_id: "b".repeat(32),
        after: 0,
    };
    const input = (value: unknown) => parseWireJson(JSON.stringify(value));
    for (const [key, contract] of Object.entries(routeContracts)) {
        const route = routeDefinitions.find(
            (entry) => `${entry.id}_${entry.mode}` === key,
        );
        if (route === undefined)
            throw new Error("Missing independently exercised route.");
        const path = Object.fromEntries(
            route.path_parameters.map((parameter) => {
                const value = pathValues[parameter.name];
                if (value === undefined)
                    throw new Error("No hand-chosen path input.");
                return [parameter.name, value];
            }),
        );
        const query = Object.fromEntries(
            route.query_parameters.map((parameter) => {
                const value = queryValues[parameter.name];
                if (value === undefined)
                    throw new Error("No hand-chosen query input.");
                return [parameter.name, value];
            }),
        );
        expect(() => contract.decodePath(input(path))).not.toThrow();
        expect(() => contract.decodeQuery(input(query))).not.toThrow();
        if (route.request_body === null)
            expect(contract.decodeBody(null)).toBeNull();
        else {
            const sample = corpus.find(
                (entry) => entry.definition === route.request_body,
            );
            if (sample === undefined)
                throw new Error("Missing original request body.");
            expect(() => contract.decodeBody(sample.value)).not.toThrow();
        }
        if (route.failure.length === 0)
            expect(() => contract.decodeFailure({})).toThrow(WireError);
        for (const definition of route.failure) {
            const sample = corpus.find(
                (entry) => entry.definition === definition,
            );
            if (sample === undefined)
                throw new Error("Missing original failure body.");
            expect(() => contract.decodeFailure(sample.value)).not.toThrow();
        }
        if (route.success === null)
            expect(() => contract.decodeSuccess({})).toThrow(WireError);
        else {
            const sample = corpus.find(
                (entry) => entry.definition === route.success,
            );
            if (sample === undefined)
                throw new Error("Missing original success body.");
            expect(() => contract.decodeSuccess(sample.value)).not.toThrow();
        }
    }
});
test("original-result dispatch selects the stored route and original command", () => {
    for (const route of operationResultDefinitions) {
        const sample = corpus.find(
            (entry) => entry.definition === route.success,
        );
        if (sample === undefined)
            throw new Error("Missing original result fixture.");
        const command = route.commands[0];
        expect(() =>
            decodeOriginalOperationPayload(
                route.origin_path,
                command,
                false,
                sample.value,
            ),
        ).not.toThrow();
        for (const definition of route.failure) {
            const sample = corpus.find(
                (entry) => entry.definition === definition,
            );
            if (sample === undefined)
                throw new Error("Missing original failure variant.");
            expect(() =>
                decodeOriginalOperationPayload(
                    route.origin_path,
                    command,
                    true,
                    sample.value,
                ),
            ).not.toThrow();
        }
        const empty = corpus.find(
            (entry) => entry.definition === "EmptyPayload",
        );
        if (empty === undefined)
            throw new Error("Missing empty result fixture.");
        expect(() =>
            decodeOriginalOperationPayload(
                route.origin_path,
                command,
                true,
                empty.value,
            ),
        ).not.toThrow();
    }
});
