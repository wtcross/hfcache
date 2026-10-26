/** ADR142: closed card projection; native digest verification precedes client exposure. */
import { codePointLength, WireError } from "./json";
import { isRecord } from "./runtime";

const PRESENTATION_BYTES = 1024 * 1024;
const RECORD_BYTES = 2 * 1024 * 1024;
const states = [
    "present",
    "absent",
    "unsupported",
    "oversize",
    "unsafe",
    "failed",
    "not_captured",
];

function check(condition: boolean): void {
    if (!condition) throw new WireError("semantic");
}

function field(value: unknown, name: string): unknown {
    if (!isRecord(value)) throw new WireError("semantic");
    const descriptor = Object.getOwnPropertyDescriptor(value, name);
    if (
        descriptor === undefined ||
        descriptor.get !== undefined ||
        descriptor.set !== undefined
    )
        throw new WireError("semantic");
    return descriptor.value;
}

function text(value: unknown): string {
    if (typeof value !== "string") throw new WireError("semantic");
    return value;
}

function utf8Size(value: string): number {
    codePointLength(value); // refuse lone surrogates, never silently replace with U+FFFD
    let result = 0;
    for (const char of value) {
        const point = char.codePointAt(0);
        if (point === undefined) throw new WireError("semantic");
        result +=
            point < 0x80 ? 1 : point < 0x800 ? 2 : point < 0x10000 ? 3 : 4;
    }
    return result;
}

function jsonStringSize(value: string): number {
    let result = 2;
    for (const char of value) {
        if ('\\"\b\f\n\r\t'.includes(char)) result += 2;
        else if ((char.codePointAt(0) ?? 0) < 32) result += 6;
        else result += utf8Size(char);
        if (result > PRESENTATION_BYTES) return result;
    }
    return result;
}

function coherence(value: unknown): void {
    const state = text(field(value, "state"));
    check(states.includes(state));
    const source = field(value, "source_path");
    const expected = field(value, "expected_source_sha256");
    check((source === null) === (expected === null));
    if (state !== "not_captured")
        check((state === "absent") === (source === null));
    const markdown = field(value, "markdown");
    const digest = field(value, "presentation_sha256");
    if (state === "present") {
        const body = text(markdown);
        check(typeof digest === "string");
        check(utf8Size(body) <= PRESENTATION_BYTES);
        check(jsonStringSize(body) <= PRESENTATION_BYTES);
    } else check(markdown === null && digest === null);
    const captured = field(value, "captured_at");
    const version = field(value, "presentation_version");
    if (state === "not_captured") {
        check(captured === null && version === null);
        const diagnostics = field(value, "diagnostics");
        check(Array.isArray(diagnostics) && diagnostics.length === 0);
    } else check(captured !== null && version === "markdown-1");
    const diagnostics = field(value, "diagnostics");
    if (!Array.isArray(diagnostics)) throw new WireError("semantic");
    let previous: string | undefined;
    for (const item of diagnostics) {
        const code = text(item);
        check(previous === undefined || previous < code);
        previous = code;
    }
    // Python dump() uses two-space indentation and a trailing newline. Sorting
    // changes field order, not this flat record's encoded byte count.
    check(utf8Size(JSON.stringify(value, null, 2) + "\n") <= RECORD_BYTES);
}

export const cardSemanticIds: readonly string[] = Object.freeze([
    "hfcache.card_models.RepositoryCardRead.strict_version",
    "hfcache.card_models.RepositoryCardRead.coherent",
]);

export function applyCardSemantic(id: string, value: unknown): unknown {
    switch (id) {
        case "hfcache.card_models.RepositoryCardRead.strict_version":
            check(value === 1);
            break;
        case "hfcache.card_models.RepositoryCardRead.coherent":
            coherence(value);
            break;
        default:
            throw new WireError("semantic");
    }
    return value;
}

function digestEngine(engine: Crypto | undefined): SubtleCrypto | undefined {
    return engine?.subtle;
}

/** Synchronous reconstruction cannot call WebCrypto. Every typed card read awaits this. */
export async function validateCardDigest(value: unknown): Promise<void> {
    const state = text(field(value, "state"));
    check(states.includes(state));
    if (state !== "present") return;
    const body = text(field(value, "markdown"));
    const expected = text(field(value, "presentation_sha256"));
    check(utf8Size(body) <= PRESENTATION_BYTES);
    let digest: ArrayBuffer;
    try {
        const subtle = digestEngine(globalThis.crypto);
        if (subtle === undefined) throw new WireError("unsupported_engine");
        digest = await subtle.digest("SHA-256", new TextEncoder().encode(body));
    } catch {
        throw new WireError("unsupported_engine");
    }
    const observed = Array.from(new Uint8Array(digest), (byte) =>
        byte.toString(16).padStart(2, "0"),
    ).join("");
    check(observed === expected);
}
