/** Deterministic strict decoders from the source-audited Python transport IR. */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { format, resolveConfig } from "prettier";
import ts from "typescript";
import { semanticSourceHashes } from "../src/wire/semantic-audit.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
// Read the explicit implementation lists without executing application modules or
// requiring generated.ts to exist before its own generation.
const implementedSemanticIds: string[] = [];
for (const [relative, exportName] of [
    ["semantics.ts", "ownSemanticIds"],
    ["catalog-semantics.ts", "catalogSemanticIds"],
    ["manifest-semantics.ts", "manifestSemanticIds"],
    ["../api/bindings.ts", "contextSemanticIds"],
    ["ui-semantics.ts", "uiSemanticIds"],
    ["ui-semantics.ts", "uiContextSemanticIds"],
]) {
    if (relative === undefined || exportName === undefined)
        throw new Error("Missing semantic registry.");
    const path = fileURLToPath(
        new URL(`../src/wire/${relative}`, import.meta.url),
    );
    const ast = ts.createSourceFile(
        path,
        readFileSync(path, "utf8"),
        ts.ScriptTarget.Latest,
        true,
    );
    let found = false;
    for (const statement of ast.statements) {
        if (!ts.isVariableStatement(statement)) continue;
        for (const declaration of statement.declarationList.declarations) {
            if (
                !ts.isIdentifier(declaration.name) ||
                declaration.name.text !== exportName ||
                declaration.initializer === undefined
            )
                continue;
            let initializer = declaration.initializer;
            if (
                ts.isCallExpression(initializer) &&
                initializer.expression.getText(ast) === "Object.freeze" &&
                initializer.arguments.length === 1
            ) {
                const argument = initializer.arguments[0];
                if (argument === undefined)
                    throw new Error("Missing semantic registry value.");
                initializer = argument;
            }
            if (!ts.isArrayLiteralExpression(initializer))
                throw new Error("Semantic registry must be a literal list.");
            for (const element of initializer.elements) {
                if (!ts.isStringLiteral(element))
                    throw new Error("Semantic IDs must be literal strings.");
                implementedSemanticIds.push(element.text);
            }
            found = true;
        }
    }
    if (!found)
        throw new Error(
            `Missing semantic implementation registry: ${exportName}.`,
        );
}

const input = fileURLToPath(
    new URL("../src/wire/contracts.json", import.meta.url),
);
const output = fileURLToPath(
    new URL("../src/wire/generated.ts", import.meta.url),
);
const raw = readFileSync(input);
if (raw.length > 8 * 1024 * 1024) throw new Error("Oversized transport IR.");
const parsed: unknown = JSON.parse(raw.toString("utf8"));
function object(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new Error("Invalid transport IR object.");
    return value;
}
function string(value: unknown): string {
    if (typeof value !== "string")
        throw new Error("Invalid transport IR string.");
    return value;
}
function array(value: unknown): unknown[] {
    if (!Array.isArray(value)) throw new Error("Invalid transport IR array.");
    const result: unknown[] = value;
    return result;
}
function boolean(value: unknown): boolean {
    if (typeof value !== "boolean")
        throw new Error("Invalid transport IR boolean.");
    return value;
}
function bounded(value: unknown): number | null {
    if (value === null) return null;
    if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0)
        throw new Error("Invalid IR collection bound.");
    return value;
}
function decimal(value: unknown): string | null {
    if (value === null) return null;
    const text = string(value);
    if (
        !/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$/u.test(text) ||
        text.length > 128
    )
        throw new Error("Invalid exact IR numeric bound.");
    return text;
}
function keys(value: Record<string, unknown>, expected: readonly string[]) {
    if (
        Object.keys(value).sort().join("\0") !== [...expected].sort().join("\0")
    )
        throw new Error("Unknown or missing transport IR field.");
}
function name(value: unknown): string {
    const text = string(value);
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/u.test(text))
        throw new Error("Invalid generated identifier.");
    return text;
}
const ir = object(parsed);
keys(ir, [
    "schema_version",
    "source_digest",
    "definitions",
    "semantics",
    "routes",
    "operation_results",
]);
if (
    ir.schema_version !== 1 ||
    !/^[0-9a-f]{64}$/u.test(string(ir.source_digest))
)
    throw new Error("Unknown transport IR version.");
const definitions = object(ir.definitions);
const manifest = object(ir.semantics);
if (
    Object.keys(definitions).length === 0 ||
    Object.keys(definitions).length > 1000
)
    throw new Error("Invalid definition registry.");
for (const [id, rawSemantic] of Object.entries(manifest)) {
    const semantic = object(rawSemantic);
    keys(semantic, ["phase", "source_hash"]);
    if (
        !["field", "model", "context"].includes(string(semantic.phase)) ||
        !implementedSemanticIds.includes(id) ||
        semanticSourceHashes[id] !== semantic.source_hash
    )
        throw new Error(`Unaudited semantic implementation: ${id}.`);
}

function semanticIds(node: Record<string, unknown>): string[] {
    return array(node.semantic_ids).map((id) => {
        const text = string(id);
        if (!Object.hasOwn(manifest, text))
            throw new Error("Unknown semantic reference.");
        if (object(manifest[text]).phase === "context")
            throw new Error("Context binding cannot run as a field semantic.");
        return text;
    });
}
function fields(node: Record<string, unknown>) {
    return array(node.fields).map((rawField) => {
        const field = object(rawField);
        keys(field, ["name", "node", "required"]);
        return {
            name: string(field.name),
            node: field.node,
            required: boolean(field.required),
        };
    });
}
const nodeFields: Readonly<Record<string, readonly string[]>> = {
    object: ["fields", "extra"],
    array: ["items", "min_items", "max_items"],
    string: ["min_codepoints", "max_codepoints", "pattern"],
    integer: ["minimum", "maximum"],
    number: ["minimum", "maximum"],
    boolean: [],
    null: [],
    literal: ["value"],
    union: ["choices"],
    ref: ["name"],
    json_value: ["max_depth", "max_nodes", "object_only"],
};
// These four audited ASCII patterns have identical Rust/Python/ECMAScript
// character semantics; runtime.ts supplies true end-of-input behavior.
const auditedPatterns = new Set([
    "^HF[A-Z]{2,6}[0-9]{3}$",
    "^[A-Za-z0-9][A-Za-z0-9._-]*$",
    "^[a-f0-9]{64}$",
    "^[a-z][a-z0-9_.-]{0,63}$",
]);
function nodeInfo(rawNode: unknown, depth: number): Record<string, unknown> {
    if (depth > 64) throw new Error("IR nesting exceeds generator budget.");
    const node = object(rawNode),
        kind = string(node.kind),
        extra = nodeFields[kind];
    if (extra === undefined)
        throw new Error(`Unsupported schema node: ${kind}.`);
    keys(node, ["kind", "semantic_ids", ...extra]);
    semanticIds(node);
    if (
        kind === "string" &&
        node.pattern !== null &&
        !auditedPatterns.has(string(node.pattern))
    )
        throw new Error("Unaudited cross-language schema pattern.");
    return node;
}
function literal(value: unknown): string {
    if (
        value !== null &&
        typeof value !== "string" &&
        typeof value !== "boolean" &&
        !(typeof value === "number" && Number.isSafeInteger(value))
    )
        throw new Error("Unsafe schema literal.");
    return JSON.stringify(value);
}
function typeOf(rawNode: unknown, depth = 0): string {
    const node = nodeInfo(rawNode, depth);
    switch (node.kind) {
        case "object":
            if (node.extra !== "forbid")
                throw new Error("Unbounded schema object.");
            if (fields(node).length === 0)
                return "Readonly<Record<string,never>>";
            return `{ ${fields(node)
                .map(
                    (field) =>
                        `readonly [${JSON.stringify(field.name)}]${field.required ? "" : "?"}: ${typeOf(field.node, depth + 1)};`,
                )
                .join(" ")} }`;
        case "array":
            return `readonly (${typeOf(node.items, depth + 1)})[]`;
        case "string":
            return "string";
        case "integer":
        case "number":
            return "number";
        case "boolean":
            return "boolean";
        case "null":
            return "null";
        case "literal":
            return literal(node.value);
        case "union": {
            const choices = array(node.choices),
                types = choices.map((choice) => typeOf(choice, depth + 1));
            const useful = choices
                .filter((choice) => {
                    const member = object(choice);
                    return (
                        member.kind !== "literal" ||
                        !types.includes(typeof member.value)
                    );
                })
                .map((choice) => typeOf(choice, depth + 1));
            return `(${[...new Set(useful)].join(" | ")})`;
        }
        case "ref": {
            const reference = name(node.name);
            if (!Object.hasOwn(definitions, reference))
                throw new Error("Missing schema reference.");
            return reference;
        }
        case "json_value":
            if (node.object_only !== true)
                throw new Error("Generic transport context must be an object.");
            return "JsonObject";
        default:
            throw new Error("Unsupported schema node.");
    }
}
function expression(rawNode: unknown, input: string, depth = 0): string {
    const node = nodeInfo(rawNode, depth);
    let result: string;
    switch (node.kind) {
        case "object": {
            const members = fields(node);
            const required = members
                .filter((field) => field.required)
                .map((field) => field.name);
            const optional = members
                .filter((field) => !field.required)
                .map((field) => field.name);
            const constructor =
                optional.length === 0
                    ? `wireObject(input, ${JSON.stringify(required)})`
                    : `wireRequestObject(input, ${JSON.stringify(required)}, ${JSON.stringify(optional)})`;
            if (members.length === 0) {
                result = `((input:unknown) => {${constructor};return Object.freeze({});})(${input})`;
                break;
            }
            result = `((input: unknown) => { const object = ${constructor}; return Object.freeze({${members
                .map((field) => {
                    const property = `[${JSON.stringify(field.name)}]: ${expression(field.node, `object[${JSON.stringify(field.name)}]`, depth + 1)}`;
                    return field.required
                        ? property
                        : `...(Object.hasOwn(object, ${JSON.stringify(field.name)}) ? {${property}} : {})`;
                })
                .join(",")}}); })(${input})`;
            break;
        }
        case "array":
            result = `wireArray(${input}, (member: unknown) => ${expression(node.items, "member", depth + 1)}, ${String(bounded(node.min_items))}, ${String(bounded(node.max_items))})`;
            break;
        case "string":
            result = `wireString(${input}, ${String(bounded(node.min_codepoints))}, ${String(bounded(node.max_codepoints))}, ${node.pattern === null ? "null" : JSON.stringify(string(node.pattern))})`;
            break;
        case "integer":
        case "number":
            result = `${node.kind === "integer" ? "wireInteger" : "wireNumber"}(${input}, ${JSON.stringify(decimal(node.minimum))}, ${JSON.stringify(decimal(node.maximum))})`;
            break;
        case "boolean":
            result = `wireBoolean(${input})`;
            break;
        case "null":
            result = `wireNull(${input})`;
            break;
        case "literal":
            result = `wireLiteral(${input}, ${literal(node.value)})`;
            break;
        case "union": {
            const choices = array(node.choices);
            if (choices.length < 1 || choices.length > 32)
                throw new Error("Invalid bounded union.");
            result = `wireUnion<${typeOf(node)}>(${input}, [${choices.map((choice) => `(member: unknown) => ${expression(choice, "member", depth + 1)}`).join(",")}])`;
            break;
        }
        case "ref":
            result = `decode${name(node.name)}(${input})`;
            break;
        case "json_value": {
            const maxDepth = bounded(node.max_depth),
                maxNodes = bounded(node.max_nodes);
            if (maxDepth === null || maxNodes === null)
                throw new Error("Unbounded JSON context.");
            if (node.object_only !== true)
                throw new Error("Generic transport context must be an object.");
            result = `wireJsonValue(${input}, ${String(maxDepth)}, ${String(maxNodes)}, true)`;
            break;
        }
        default:
            throw new Error("Unsupported schema node.");
    }
    const ids = semanticIds(node);
    return ids.length === 0
        ? result
        : `checked(${result}, ${JSON.stringify(ids)})`;
}

const names = Object.keys(definitions).sort();
function definition(value: unknown): string {
    const result = name(value);
    if (!Object.hasOwn(definitions, result))
        throw new Error("Missing route payload definition.");
    return result;
}
function bindings(value: unknown): string[] {
    return array(value).map((entry) => {
        const id = string(entry);
        if (object(manifest[id]).phase !== "context")
            throw new Error("Unknown context binding.");
        return id;
    });
}
function commandList(value: unknown): string[] {
    return array(value).map(string);
}
const routes = array(ir.routes).map((entry) => {
    const route = object(entry);
    keys(route, [
        "id",
        "method",
        "path",
        "mode",
        "response_kind",
        "commands",
        "success",
        "failure",
        "cursor",
        "binding_ids",
        "path_parameters",
        "query_parameters",
        "request_body",
    ]);
    name(route.id);
    name(route.mode);
    if (
        !["GET", "POST"].includes(string(route.method)) ||
        !(
            /^\/api\/v1\/[A-Za-z0-9_{}\/-]+$/u.test(string(route.path)) ||
            (route.path === "/ui/bootstrap.json" &&
                route.response_kind === "ui_bootstrap" &&
                route.method === "GET")
        ) ||
        !["read", "acceptance", "operation_result", "ui_bootstrap"].includes(
            string(route.response_kind),
        ) ||
        !["none", "opaque"].includes(string(route.cursor))
    )
        throw new Error("Unknown route authority.");
    commandList(route.commands);
    bindings(route.binding_ids);
    if (route.success !== null) definition(route.success);
    array(route.failure).forEach(definition);
    if (route.request_body !== null) definition(route.request_body);
    const pathNames = array(route.path_parameters).map((parameter) => {
        const record = object(parameter);
        keys(record, ["name", "node"]);
        name(record.name);
        typeOf(record.node);
        return string(record.name);
    });
    const placeholders = [
        ...string(route.path).matchAll(/\{([A-Za-z_][A-Za-z0-9_]*)\}/gu),
    ].map((match) => match[1]);
    if (JSON.stringify(pathNames) !== JSON.stringify(placeholders))
        throw new Error("Unbound path parameters.");
    array(route.query_parameters).forEach((parameter) => {
        const record = object(parameter);
        keys(record, ["name", "node", "repeated"]);
        name(record.name);
        typeOf(record.node);
        if (boolean(record.repeated) && object(record.node).kind !== "array")
            throw new Error("Repeated query requires bounded array.");
    });
    return route;
});
const resultRoutes = array(ir.operation_results).map((entry) => {
    const result = object(entry);
    keys(result, [
        "origin_path",
        "commands",
        "success",
        "failure",
        "binding_ids",
    ]);
    if (
        !routes.some(
            (route) =>
                route.method === "POST" && route.path === result.origin_path,
        )
    )
        throw new Error("Unknown original operation route.");
    commandList(result.commands);
    definition(result.success);
    array(result.failure).forEach(definition);
    bindings(result.binding_ids);
    return result;
});
let source = `/** Generated from source digest ${string(ir.source_digest)}. Run generate:wire; do not edit. */\n`;
source += `export const WIRE_SOURCE_DIGEST = ${JSON.stringify(ir.source_digest)};\n`;
source +=
    'import {wireObject,wireRequestObject,wireArray,wireString,wireInteger,wireNumber,wireBoolean,wireNull,wireLiteral,wireUnion,wireJsonValue} from "./runtime";\n';
source +=
    'import type {JsonObject} from "./runtime";\nimport {WireError} from "./json";\nimport {applySemantic} from "./semantics";\n';
source +=
    "function checked<T>(value:T,ids:readonly string[]):T { for(const id of ids) applySemantic(id,value); return value; }\n";
for (const key of names)
    source += `export type ${name(key)} = ${typeOf(definitions[key])};\n`;
for (const key of names)
    source += `export function decode${key}(value:unknown):${key} { return ${expression(definitions[key], "value")}; }\n`;
source +=
    "export function decodeNamed(name:string,value:unknown):unknown { switch(name) {";
for (const key of names)
    source += `case ${JSON.stringify(key)}: return decode${key}(value);`;
source += 'default: throw new WireError("schema");}}\n';
function parameters(value: unknown, query: boolean): unknown {
    return {
        kind: "object",
        extra: "forbid",
        semantic_ids: [],
        fields: array(value).map((entry) => {
            const parameter = object(entry);
            return {
                name: string(parameter.name),
                node: parameter.node,
                required: !query,
            };
        }),
    };
}
function unionDecoder(value: unknown): string {
    const choices = array(value).map(definition);
    return choices.length === 0
        ? '(_value:unknown):never => {void _value;throw new WireError("schema");}'
        : `(value:unknown):${choices.join("|")} => wireUnion<${choices.join("|")}>(value,[${choices.map((key) => `decode${key}`).join(",")}])`;
}
source += "export const routeContracts = {\n";
for (const route of routes) {
    const key = `${string(route.id)}_${string(route.mode)}`;
    source += `${JSON.stringify(key)}:{method:${JSON.stringify(route.method)},path:${JSON.stringify(route.path)},commands:${JSON.stringify(route.commands)},bindingIds:${JSON.stringify(route.binding_ids)},responseKind:${JSON.stringify(route.response_kind)},cursor:${JSON.stringify(route.cursor)},`;
    source += `decodePath:(value:unknown):${typeOf(parameters(route.path_parameters, false))} => ${expression(parameters(route.path_parameters, false), "value")},`;
    source += `decodeQuery:(value:unknown):${typeOf(parameters(route.query_parameters, true))} => ${expression(parameters(route.query_parameters, true), "value")},`;
    source += `repeated:${JSON.stringify(
        array(route.query_parameters)
            .filter((entry) => object(entry).repeated === true)
            .map((entry) => object(entry).name),
    )},`;
    source += `decodeSuccess:${route.success === null ? '(_value:unknown):never => {void _value;throw new WireError("schema");}' : `decode${definition(route.success)}`},decodeFailure:${unionDecoder(route.failure)},decodeBody:${route.request_body === null ? "wireNull" : `decode${definition(route.request_body)}`}},\n`;
}
source += "} as const;\n";
const operationSuccess = [
    ...new Set(resultRoutes.map((route) => definition(route.success))),
];
const operationFailure = [
    ...new Set(
        resultRoutes.flatMap((route) => array(route.failure).map(definition)),
    ),
];
source += `export type OperationSuccess = ${operationSuccess.join("|")};\nexport type OperationFailure = ${operationFailure.join("|")};\n`;
source +=
    "export function decodeOriginalOperationPayload(origin:string,command:string,failed:false,value:unknown):OperationSuccess;\nexport function decodeOriginalOperationPayload(origin:string,command:string,failed:true,value:unknown):OperationFailure;\nexport function decodeOriginalOperationPayload(origin:string,command:string,failed:boolean,value:unknown):OperationSuccess|OperationFailure {\n";
for (const route of resultRoutes)
    source += `if(origin===${JSON.stringify(route.origin_path)}&&${JSON.stringify(route.commands)}.includes(command)) return failed?(${unionDecoder(route.failure)})(value):decode${definition(route.success)}(value);\n`;
source += 'throw new WireError("semantic");}\n';
// Metadata is non-executable and contains no unvalidated URLs or schema code.
for (const [key, records] of [
    ["routeDefinitions", routes],
    ["operationResultDefinitions", resultRoutes],
] as const) {
    source += `export const ${key} = ${JSON.stringify(records)} as const;\n`;
}
const formatting = {
    ...(await resolveConfig(output, { editorconfig: true })),
    filepath: output,
};
const formatted = await format(source, formatting);
const options = process.argv.slice(2);
if (options.length === 1 && options[0] === "--write") {
    writeFileSync(output, formatted);
    console.log(
        `Generated ${String(names.length)} precise transport types and reconstructing decoders.`,
    );
} else if (
    options.length === 0 ||
    (options.length === 1 && options[0] === "--check")
) {
    if (readFileSync(output, "utf8") !== formatted)
        throw new Error(
            "Generated transport contracts are stale. Run generate:wire after review.",
        );
    console.log(
        `Checked ${String(names.length)} generated transport definitions and audited semantics.`,
    );
} else throw new Error("Usage: node scripts/generate-wire.ts --check|--write");
