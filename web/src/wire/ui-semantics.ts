/** Explicit ports of the independent UI artifact/bootstrap authorities. */
import { WireError } from "./json";
import { isRecord } from "./runtime";
import { canonicalHex } from "../api/identity";
import { pythonIsPrintable } from "./unicode";
import { uriPath } from "../api/url-paths";

function check(value: boolean): void {
    if (!value) throw new WireError("semantic");
}
function text(value: unknown): string {
    if (typeof value !== "string") throw new WireError("semantic");
    return value;
}
function record(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("semantic");
    return value;
}
function list(value: unknown): unknown[] {
    if (!Array.isArray(value)) throw new WireError("semantic");
    const items: unknown[] = value;
    return items;
}
function integer(value: unknown): number {
    if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0)
        throw new WireError("semantic");
    return value;
}
const permissions = [
    "config-read",
    "config-write",
    "host-read",
    "observer-stop",
    "schedule-write",
];
export function canonicalUiPrefix(value: unknown): string {
    const source = text(value);
    check(new TextEncoder().encode(source).length <= 1024);
    check(
        source === "" ||
            (source.startsWith("/") &&
                !source.startsWith("//") &&
                !source.endsWith("/") &&
                pythonIsPrintable(source) &&
                !/[?#\\%\s]/u.test(source) &&
                source
                    .slice(1)
                    .split("/")
                    .every(
                        (part) => part !== "" && part !== "." && part !== "..",
                    )),
    );
    return source;
}
export function canonicalToolchain(value: unknown): string {
    const data = record(value);
    return (
        JSON.stringify(
            {
                node: data.node,
                pnpm: data.pnpm,
                typescript: data.typescript,
                vite: data.vite,
            },
            null,
            2,
        ) + "\n"
    );
}
export const uiSemanticIds: readonly string[] = [
    "hfcache.ui_models._ascii",
    "hfcache.ui_models._one",
    "hfcache.ui_models._prefix",
    "hfcache.ui_models._origin",
    "hfcache.ui_models._subject",
    "hfcache.ui_models._instance",
    "hfcache.ui_models._asset_path",
    "hfcache.ui_models.UiAssetMember._member",
    "hfcache.ui_models.UiAssetManifest._members",
    "hfcache.ui_models.UiPaths._paths",
    "hfcache.ui_models.UiAdminPermission._permission",
    "hfcache.ui_models.UiUser._user",
    "hfcache.ui_models.UiBootstrap._bootstrap",
];
/** Separate context owners: async bootstrap WebCrypto/bindings and server/build
 * complete HTML byte checks. Browser readInertMetadata checks only visible slots.
 * These IDs are never attached to DTO nodes or accepted by applyUiSemantic. */
export const uiContextSemanticIds: readonly string[] = [
    "ui.bootstrap",
    "ui.html",
];
export function applyUiSemantic(id: string, value: unknown): void {
    switch (id) {
        case "hfcache.ui_models._ascii":
            check(/^[\x20-\x7e]+$/u.exec(text(value))?.[0] === value);
            return;
        case "hfcache.ui_models._one":
            check(value === 1);
            return;
        case "hfcache.ui_models._prefix":
            canonicalUiPrefix(value);
            return;
        case "hfcache.ui_models._origin": {
            const source = text(value);
            let origin: URL;
            try {
                origin = new URL(source);
            } catch {
                throw new WireError("semantic");
            }
            check(
                source.length <= 4096 &&
                    /^[\x21-\x7e]+$/u.exec(source)?.[0] === source &&
                    origin.protocol === "https:" &&
                    origin.origin === source,
            );
            return;
        }
        case "hfcache.ui_models._subject":
            check(
                /[A-Za-z0-9][A-Za-z0-9._:-]{0,127}/u.exec(text(value))?.[0] ===
                    value,
            );
            return;
        case "hfcache.ui_models._instance":
            check(canonicalHex(text(value), 32));
            return;
        case "hfcache.ui_models._asset_path": {
            const source = text(value),
                parts = source.split("/");
            check(
                source.length <= 1024 &&
                    parts.length <= 8 &&
                    parts.every(
                        (part) =>
                            part.length <= 255 &&
                            /[A-Za-z0-9][A-Za-z0-9._-]*/u.exec(part)?.[0] ===
                                part,
                    ),
            );
            return;
        }
        case "hfcache.ui_models.UiAssetMember._member": {
            const data = record(value),
                path = text(data.path),
                mime = text(data.mime);
            const types: Readonly<Record<string, string>> = {
                html: "text/html",
                css: "text/css",
                js: "text/javascript",
                json: "application/json",
                png: "image/png",
                webp: "image/webp",
                woff2: "font/woff2",
            };
            check(
                path === "THIRD_PARTY_NOTICES.txt"
                    ? mime === "text/plain"
                    : types[path.split(".").at(-1) ?? ""] === mime,
            );
            check(
                (mime !== "text/html" || path === "index.html") &&
                    ([
                        "index.html",
                        "licenses.json",
                        "THIRD_PARTY_NOTICES.txt",
                    ].includes(path) ||
                        path.startsWith("assets/")) &&
                    (path !== "index.html" || data.bytes !== 0),
            );
            return;
        }
        case "hfcache.ui_models.UiAssetManifest._members": {
            const data = record(value),
                members = list(data.members).map(record),
                paths = members.map((member) => text(member.path)),
                build = record(data.build);
            check(
                paths.every(
                    (path, index) =>
                        index === 0 || path > (paths[index - 1] ?? path),
                ) &&
                    [
                        "index.html",
                        "licenses.json",
                        "THIRD_PARTY_NOTICES.txt",
                    ].every((path) => paths.includes(path)),
            );
            check(
                members.reduce(
                    (sum, item) => sum + BigInt(integer(item.bytes)),
                    0n,
                ) <= 67108864n,
            );
            check(
                members.find((item) => item.path === "licenses.json")
                    ?.sha256 === build.licenses_sha256 &&
                    members.find(
                        (item) => item.path === "THIRD_PARTY_NOTICES.txt",
                    )?.sha256 === build.notices_sha256,
            );
            return;
        }
        case "hfcache.ui_models.UiPaths._paths": {
            const data = record(value),
                prefix = text(data.effective_prefix);
            check(
                (prefix === "" || prefix === data.public_prefix) &&
                    data.ui_base === uriPath(prefix + "/ui/") &&
                    data.bootstrap === uriPath(prefix + "/ui/bootstrap.json") &&
                    data.api_base === uriPath(prefix + "/api/v1") &&
                    (data.mcp_base === null ||
                        data.mcp_base === uriPath(prefix + "/mcp/")),
            );
            return;
        }
        case "hfcache.ui_models.UiAdminPermission._permission": {
            const data = record(value);
            check(
                !(data.effective === true && data.granted !== true) &&
                    data.reason ===
                        (data.effective === true
                            ? "allowed"
                            : data.granted === true
                              ? "feature_unavailable"
                              : "not_granted"),
            );
            return;
        }
        case "hfcache.ui_models.UiUser._user": {
            const data = record(value);
            check(
                data.subject === data.display_name &&
                    JSON.stringify(data.rest_capabilities) ===
                        '["read","write"]' &&
                    JSON.stringify(
                        list(data.admin_permissions).map(
                            (item) => record(item).capability,
                        ),
                    ) === JSON.stringify(permissions),
            );
            return;
        }
        case "hfcache.ui_models.UiBootstrap._bootstrap": {
            const data = record(value),
                metadata = record(record(data.build).metadata);
            check(
                data.instance_id === data.authority_epoch &&
                    data.wire_source_digest === metadata.wire_source_digest &&
                    data.ui_contract_version === metadata.ui_contract_version &&
                    data.rest_api_schema_version ===
                        metadata.rest_api_schema_version,
            );
            return;
        }
        default:
            throw new WireError("semantic");
    }
}
