/** Exact manifest consistency/path grammar; these checks grant no filesystem access. */
import { compareCatalogText } from "./catalog-semantics";
import { codePointLength, WireError } from "./json";
import { isRecord } from "./runtime";
import { pythonCollisionKey, UnicodeWork } from "./unicode";

function requireEvidence(condition: boolean): void {
    if (!condition) throw new WireError("semantic");
}
function field(value: unknown, key: string): unknown {
    if (!isRecord(value)) throw new WireError("semantic");
    const property = Object.getOwnPropertyDescriptor(value, key);
    if (
        property === undefined ||
        property.get !== undefined ||
        property.set !== undefined
    )
        throw new WireError("semantic");
    const member: unknown = property.value;
    return member;
}
function text(value: unknown): string {
    if (typeof value !== "string") throw new WireError("semantic");
    return value;
}
function isList(value: unknown): value is readonly unknown[] {
    return Array.isArray(value);
}
function list(value: unknown): readonly unknown[] {
    if (!isList(value)) throw new WireError("semantic");
    return value;
}
function count(value: unknown): bigint {
    if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0)
        throw new WireError("semantic");
    return BigInt(value);
}

export function validateRelativePath(value: unknown): string {
    const path = text(value);
    codePointLength(path);
    requireEvidence(
        path.length > 0 && !path.startsWith("/") && !path.endsWith("/"),
    );
    requireEvidence(!/[\x00-\x1f\x7f\\]/u.test(path));
    const encoder = new TextEncoder();
    requireEvidence(encoder.encode(path).byteLength <= 1024);
    for (const component of path.split("/"))
        requireEvidence(
            component !== "" &&
                component !== "." &&
                component !== ".." &&
                encoder.encode(component).byteLength <= 255,
        );
    return path;
}

function provenance(value: unknown): void {
    const hashed = field(value, "hashed");
    requireEvidence(typeof hashed === "boolean");
    requireEvidence(hashed === (field(value, "hash_reused_from") === null));
    if (field(value, "source") === "repair_download")
        requireEvidence(field(value, "cache_root") === "repair");
}

function arithmetic(value: unknown): void {
    const files = list(field(value, "files"));
    requireEvidence(count(field(value, "file_count")) === BigInt(files.length));
    let total = 0n;
    let reused = 0n;
    for (const entry of files) {
        total += count(field(entry, "size"));
        if (field(field(entry, "provenance"), "hashed") === false) reused++;
    }
    requireEvidence(count(field(value, "total_bytes")) === total);
    requireEvidence(
        count(field(field(value, "verification"), "reused_digests")) === reused,
    );
}

function paths(value: unknown): void {
    const work = new UnicodeWork();
    const seen = new Set<string>();
    let previous: string | undefined;
    for (const entry of list(field(value, "files"))) {
        const path = validateRelativePath(field(entry, "path"));
        if (previous !== undefined)
            requireEvidence(compareCatalogText(previous, path) <= 0);
        previous = path;
        const folded = pythonCollisionKey(path, work);
        requireEvidence(!seen.has(folded));
        seen.add(folded);
    }
}

function ordering(value: unknown): void {
    let previous: readonly string[] | undefined;
    for (const item of list(field(value, "dependencies"))) {
        const current = ["source_file", "source_field", "detected_id"].map(
            (name) => text(field(item, name)),
        );
        if (previous !== undefined) {
            for (let index = 0; index < current.length; index++) {
                const a = previous[index];
                const b = current[index];
                if (a === undefined || b === undefined)
                    throw new WireError("semantic");
                const compared = compareCatalogText(a, b);
                requireEvidence(compared <= 0);
                if (compared !== 0) break;
            }
        }
        previous = current;
    }
}

function timestamp(value: unknown): string {
    const result = text(value);
    // The generated timestamp scalar validates calendar fields before this hook.
    requireEvidence(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$/u.exec(result)?.[0] ===
            result,
    );
    return result;
}

function timeline(value: unknown): void {
    let previous = timestamp(field(value, "download_started_at"));
    requireEvidence(timestamp(field(value, "first_observed_at")) <= previous);
    for (const key of [
        "download_completed_at",
        "verified_at",
        "published_at",
    ]) {
        const current = timestamp(field(value, key));
        requireEvidence(previous <= current);
        previous = current;
    }
    requireEvidence(
        timestamp(field(field(value, "verification"), "verified_at")) ===
            field(value, "verified_at"),
    );
}

export const manifestSemanticIds: readonly string[] = Object.freeze([
    "hfcache.manifests.FileProvenance._check",
    "hfcache.manifests.RevisionManifest._check_timeline",
    "hfcache.manifests.RevisionManifest._check_ordering",
    "hfcache.manifests.RevisionManifest._check_paths",
    "hfcache.manifests.RevisionManifest._check_arithmetic",
    "hfcache.models._archive_path",
    "hfcache.models._repository_path",
]);

export function applyManifestSemantic(id: string, value: unknown): unknown {
    switch (id) {
        case "hfcache.manifests.FileProvenance._check":
            provenance(value);
            break;
        case "hfcache.manifests.RevisionManifest._check_timeline":
            timeline(value);
            break;
        case "hfcache.manifests.RevisionManifest._check_ordering":
            ordering(value);
            break;
        case "hfcache.manifests.RevisionManifest._check_paths":
            paths(value);
            break;
        case "hfcache.manifests.RevisionManifest._check_arithmetic":
            arithmetic(value);
            break;
        case "hfcache.models._archive_path":
        case "hfcache.models._repository_path":
            validateRelativePath(value);
            break;
        default:
            throw new WireError("semantic");
    }
    return value;
}
