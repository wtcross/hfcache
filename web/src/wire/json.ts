/** Bounded native JSON transport. Rounded callback numbers never leave this module. */
export type WireFailure =
    | "bounds"
    | "utf8"
    | "json"
    | "duplicate_key"
    | "unicode"
    | "unsupported_engine"
    | "media_type"
    | "length"
    | "schema"
    | "semantic"
    | "unsafe_number";

export class WireError extends Error {
    readonly reason: WireFailure;
    constructor(reason: WireFailure) {
        super(`The response was refused (${reason}).`);
        this.name = "WireError";
        this.reason = reason;
    }
}

export interface JsonLimits {
    readonly maxBytes: number;
    readonly maxDepth: number;
    readonly maxTokens: number;
    readonly maxKeys: number;
    readonly maxNumberCharacters: number;
}

export const NORMAL_JSON_LIMITS: JsonLimits = Object.freeze({
    maxBytes: 16 * 1024 * 1024,
    maxDepth: 32,
    maxTokens: 1_000_000,
    maxKeys: 100_000,
    maxNumberCharacters: 128,
});
export const ARTIFACT_JSON_LIMITS: JsonLimits = Object.freeze({
    ...NORMAL_JSON_LIMITS,
    maxBytes: 64 * 1024 * 1024,
});
export const CARD_JSON_LIMITS: JsonLimits = Object.freeze({
    ...NORMAL_JSON_LIMITS,
    maxBytes: 2 * 1024 * 1024,
});

class RawNumber {
    readonly source: string;
    constructor(source: string) {
        this.source = source;
        Object.freeze(this);
    }
}

export function numberSource(value: unknown): string | undefined {
    return value instanceof RawNumber ? value.source : undefined;
}

type SourceContext = { source?: string };
type SourceParser = (
    text: string,
    reviver: (key: string, value: unknown, context?: SourceContext) => unknown,
) => unknown;

export function hasNativeSourceContext(
    parser: SourceParser = JSON.parse,
): boolean {
    const expected = new Map([
        ["integer", "9007199254740993"],
        ["fraction", "9007199254740991.4"],
        ["float", "1.0"],
        ["overflow", "1e309"],
    ]);
    try {
        parser(
            '{"integer":9007199254740993,"fraction":9007199254740991.4,"float":1.0,"overflow":1e309}',
            (key: string, value: unknown, context?: SourceContext): unknown => {
                if (typeof value === "number") {
                    if (context?.source !== expected.get(key))
                        throw new WireError("unsupported_engine");
                    expected.delete(key);
                }
                return value;
            },
        );
        return expected.size === 0;
    } catch {
        return false;
    }
}

/** Counts Unicode scalar values; rejects unpaired UTF-16 surrogates. */
export function codePointLength(value: string): number {
    let count = 0;
    for (let index = 0; index < value.length; index++) {
        const unit = value.charCodeAt(index);
        if (unit >= 0xd800 && unit <= 0xdbff) {
            const next = value.charCodeAt(++index);
            if (!(next >= 0xdc00 && next <= 0xdfff))
                throw new WireError("unicode");
        } else if (unit >= 0xdc00 && unit <= 0xdfff)
            throw new WireError("unicode");
        count++;
    }
    return count;
}

function utf8Length(text: string): number {
    let length = 0;
    for (const character of text) {
        const point = character.codePointAt(0);
        if (point === undefined || (point >= 0xd800 && point <= 0xdfff))
            throw new WireError("unicode");
        length +=
            point < 0x80 ? 1 : point < 0x800 ? 2 : point < 0x10000 ? 3 : 4;
    }
    return length;
}

function validateLimits(limits: JsonLimits): void {
    const ceilings = ARTIFACT_JSON_LIMITS;
    for (const key of [
        "maxBytes",
        "maxDepth",
        "maxTokens",
        "maxKeys",
        "maxNumberCharacters",
    ] as const) {
        if (
            !Number.isSafeInteger(limits[key]) ||
            limits[key] < 1 ||
            limits[key] > ceilings[key]
        )
            throw new WireError("bounds");
    }
}

function whitespace(character: string | undefined): boolean {
    return (
        character === " " ||
        character === "\t" ||
        character === "\n" ||
        character === "\r"
    );
}

/** Only bounds, string/key identity and nesting are scanned; native parsing owns JSON grammar. */
function preScan(text: string, limits: JsonLimits): void {
    const stack: ({ kind: "object"; keys: Set<string> } | { kind: "array" })[] =
        [];
    let keys = 0;
    let tokens = 0;
    const delimiters = new Set([",", "]", "}", "[", "{", '"', ":"]);
    function token() {
        if (++tokens > limits.maxTokens) throw new WireError("bounds");
    }
    for (let index = 0; index < text.length; index++) {
        const character = text[index];
        if (whitespace(character) || character === ":" || character === ",")
            continue;
        if (character === "{" || character === "[") {
            token();
            if (stack.length >= limits.maxDepth) throw new WireError("bounds");
            stack.push(
                character === "{"
                    ? { kind: "object", keys: new Set() }
                    : { kind: "array" },
            );
        } else if (character === "}" || character === "]") {
            const frame = stack.pop();
            if (frame?.kind !== (character === "}" ? "object" : "array"))
                throw new WireError("json");
        } else if (character === '"') {
            token();
            const start = index;
            let ended = false;
            while (++index < text.length) {
                if (text[index] === "\\") index++;
                else if (text[index] === '"') {
                    ended = true;
                    break;
                }
            }
            if (!ended) throw new WireError("json");
            const value: unknown = JSON.parse(text.slice(start, index + 1));
            if (typeof value !== "string") throw new WireError("json");
            codePointLength(value);
            let next = index + 1;
            while (whitespace(text[next])) next++;
            if (text[next] === ":") {
                const frame = stack.at(-1);
                if (frame?.kind !== "object") throw new WireError("json");
                if (frame.keys.has(value)) throw new WireError("duplicate_key");
                if (++keys > limits.maxKeys) throw new WireError("bounds");
                frame.keys.add(value);
            }
        } else {
            token();
            while (
                index + 1 < text.length &&
                !whitespace(text[index + 1]) &&
                !delimiters.has(text[index + 1] ?? "")
            )
                index++;
        }
    }
    if (stack.length !== 0) throw new WireError("json");
}

export function parseWireJson(
    text: string,
    limits: JsonLimits = NORMAL_JSON_LIMITS,
): unknown {
    validateLimits(limits);
    if (!hasNativeSourceContext()) throw new WireError("unsupported_engine");
    if (text.length > limits.maxBytes || utf8Length(text) > limits.maxBytes)
        throw new WireError("bounds");
    if (text.startsWith("\ufeff")) throw new WireError("json");
    try {
        preScan(text, limits);
        const parsed: unknown = JSON.parse(
            text,
            (
                _key: string,
                value: unknown,
                context?: SourceContext,
            ): unknown => {
                if (typeof value !== "number") return value;
                if (typeof context?.source !== "string")
                    throw new WireError("unsupported_engine");
                if (context.source.length > limits.maxNumberCharacters)
                    throw new WireError("bounds");
                return new RawNumber(context.source);
            },
        );
        return parsed;
    } catch (error) {
        if (error instanceof WireError) throw error;
        throw new WireError("json");
    }
}

export async function abortable<T>(
    operation: Promise<T>,
    signal?: AbortSignal,
): Promise<T> {
    if (signal === undefined) return operation;
    if (signal.aborted) {
        // INV-021: observe the already-started read without waiting past abort.
        void operation.catch(() => undefined);
        throw new DOMException("Read aborted.", "AbortError");
    }
    let onAbort: (() => void) | undefined;
    try {
        return await Promise.race([
            operation,
            new Promise<never>((_resolve, reject) => {
                onAbort = () => {
                    reject(new DOMException("Read aborted.", "AbortError"));
                };
                signal.addEventListener("abort", onAbort, { once: true });
            }),
        ]);
    } finally {
        if (onAbort !== undefined) signal.removeEventListener("abort", onAbort);
    }
}

async function collectResponseJson(
    response: Response,
    options: {
        readonly signal?: AbortSignal;
        readonly limits?: JsonLimits;
    } = {},
): Promise<unknown> {
    const limits = options.limits ?? NORMAL_JSON_LIMITS;
    validateLimits(limits);
    const media = response.headers.get("content-type");
    if (
        media === null ||
        !/^application\/json(?:\s*;\s*charset=(?:utf-8|"utf-8"))?$/iu.test(
            media,
        )
    )
        throw new WireError("media_type");
    const declared = response.headers.get("content-length");
    if (declared !== null && !/^(?:0|[1-9][0-9]{0,19})$/u.test(declared))
        throw new WireError("length");
    const identity = [null, "identity"].includes(
        response.headers.get("content-encoding"),
    );
    if (
        identity &&
        declared !== null &&
        BigInt(declared) > BigInt(limits.maxBytes)
    )
        throw new WireError("bounds");
    if (response.body === null) throw new WireError("json");
    const reader = response.body.getReader();
    let storage = new Uint8Array(Math.min(65536, limits.maxBytes));
    let size = 0;
    let reads = 0;
    let complete = false;
    try {
        for (;;) {
            if (++reads > 65536) throw new WireError("bounds");
            if (reads % 1024 === 0)
                await new Promise<void>((resolve) => {
                    setTimeout(resolve, 0);
                });
            const part = await abortable(reader.read(), options.signal);
            if (part.done) break;
            if (part.value.byteLength > limits.maxBytes - size)
                throw new WireError("bounds");
            if (storage.byteLength < size + part.value.byteLength) {
                const replacement = new Uint8Array(
                    Math.min(
                        limits.maxBytes,
                        Math.max(
                            storage.byteLength * 2,
                            size + part.value.byteLength,
                        ),
                    ),
                );
                replacement.set(storage.subarray(0, size));
                storage = replacement;
            }
            storage.set(part.value, size);
            size += part.value.byteLength;
        }
        complete = true;
    } finally {
        if (!complete) void reader.cancel().catch(() => undefined);
        reader.releaseLock();
    }
    if (identity && declared !== null && BigInt(size) !== BigInt(declared))
        throw new WireError("length");
    const bytes = storage.subarray(0, size);
    if (bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf)
        throw new WireError("json");
    let text: string;
    try {
        text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    } catch {
        throw new WireError("utf8");
    }
    return parseWireJson(text, limits);
}

export async function readBoundedJson(
    response: Response,
    options: {
        readonly signal?: AbortSignal;
        readonly limits?: JsonLimits;
    } = {},
): Promise<unknown> {
    try {
        return await collectResponseJson(response, options);
    } catch (error) {
        void response.body?.cancel().catch(() => undefined);
        throw error;
    }
}
