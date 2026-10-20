/** Small reconstruction primitives used by mechanically generated decoders. */
import { codePointLength, numberSource, WireError } from "./json";

export type JsonValue =
    | null
    | boolean
    | string
    | number
    | readonly JsonValue[]
    | { readonly [key: string]: JsonValue };
export type JsonObject = { readonly [key: string]: JsonValue };

export function isRecord(value: unknown): value is Record<string, unknown> {
    if (
        typeof value !== "object" ||
        value === null ||
        Array.isArray(value) ||
        numberSource(value) !== undefined
    )
        return false;
    const prototype: unknown = Object.getPrototypeOf(value);
    return prototype === Object.prototype || prototype === null;
}

function isArray(value: unknown): value is unknown[] {
    return Array.isArray(value);
}

export function wireObject(
    value: unknown,
    fields: readonly string[],
): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("schema");
    const keys = Reflect.ownKeys(value);
    if (
        keys.length !== fields.length ||
        fields.some((key) => !Object.hasOwn(value, key))
    )
        throw new WireError("schema");
    for (const key of fields) {
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (
            descriptor === undefined ||
            descriptor.get !== undefined ||
            descriptor.set !== undefined ||
            descriptor.enumerable !== true
        )
            throw new WireError("schema");
    }
    return value;
}

export function wireRequestObject(
    value: unknown,
    required: readonly string[],
    optional: readonly string[],
): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("schema");
    const keys = Object.keys(value);
    if (
        Reflect.ownKeys(value).length !== keys.length ||
        required.some((key) => !Object.hasOwn(value, key)) ||
        keys.some((key) => !required.includes(key) && !optional.includes(key))
    )
        throw new WireError("schema");
    for (const key of keys) {
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (
            descriptor === undefined ||
            descriptor.get !== undefined ||
            descriptor.set !== undefined
        )
            throw new WireError("schema");
    }
    return value;
}

export function wireArray<T>(
    value: unknown,
    item: (value: unknown) => T,
    minimum: number | null,
    maximum: number | null,
): readonly T[] {
    if (
        !isArray(value) ||
        (minimum !== null && value.length < minimum) ||
        (maximum !== null && value.length > maximum)
    )
        throw new WireError("schema");
    const result: T[] = [];
    for (const member of value) result.push(item(member));
    return Object.freeze(result);
}

export function wireString(
    value: unknown,
    minimum: number | null,
    maximum: number | null,
    pattern: string | null,
): string {
    if (typeof value !== "string") throw new WireError("schema");
    const length = codePointLength(value);
    if (
        (minimum !== null && length < minimum) ||
        (maximum !== null && length > maximum) ||
        (pattern !== null &&
            !new RegExp(
                pattern.endsWith("$") ? `${pattern}(?![\\s\\S])` : pattern,
                "u",
            ).test(value))
    )
        throw new WireError("schema");
    return value;
}

export function wireInteger(
    value: unknown,
    minimum: string | null,
    maximum: string | null,
): number {
    const source = numberSource(value);
    if (source === undefined || !/^-?(?:0|[1-9][0-9]*)$/u.test(source))
        throw new WireError("schema");
    if (source.length > 17) throw new WireError("unsafe_number");
    const exact = BigInt(source);
    if (exact < -9007199254740991n || exact > 9007199254740991n)
        throw new WireError("unsafe_number");
    if (
        (minimum !== null && exact < BigInt(minimum)) ||
        (maximum !== null && exact > BigInt(maximum))
    )
        throw new WireError("schema");
    return Number(exact);
}

export function wireNumber(
    value: unknown,
    minimum: string | null,
    maximum: string | null,
): number {
    const source = numberSource(value);
    if (source === undefined) throw new WireError("schema");
    const number = Number(source);
    if (!Number.isFinite(number)) throw new WireError("unsafe_number");
    if (
        (minimum !== null && number < Number(minimum)) ||
        (maximum !== null && number > Number(maximum))
    )
        throw new WireError("schema");
    return number;
}

export function wireBoolean(value: unknown): boolean {
    if (typeof value !== "boolean") throw new WireError("schema");
    return value;
}

export function wireNull(value: unknown): null {
    if (value !== null) throw new WireError("schema");
    return null;
}

export function wireLiteral<T extends string | number | boolean | null>(
    value: unknown,
    literal: T,
): T {
    const observed =
        typeof literal === "number" ? wireInteger(value, null, null) : value;
    if (observed !== literal) throw new WireError("schema");
    return literal;
}

export function wireUnion<T>(
    value: unknown,
    choices: readonly ((value: unknown) => T)[],
): T {
    for (const decode of choices) {
        try {
            return decode(value);
        } catch (error) {
            if (!(error instanceof WireError)) throw error;
        }
    }
    throw new WireError("schema");
}

export function wireJsonValue(
    value: unknown,
    maxDepth: number,
    maxNodes: number,
    objectOnly: true,
): JsonObject;
export function wireJsonValue(
    value: unknown,
    maxDepth: number,
    maxNodes: number,
    objectOnly?: false,
): JsonValue;
export function wireJsonValue(
    value: unknown,
    maxDepth: number,
    maxNodes: number,
    objectOnly = false,
): JsonValue {
    if (objectOnly && !isRecord(value)) throw new WireError("schema");
    let nodes = 0;
    function decode(member: unknown, depth: number): JsonValue {
        if (++nodes > maxNodes || depth > maxDepth)
            throw new WireError("bounds");
        if (member === null || typeof member === "boolean") return member;
        if (typeof member === "string") {
            codePointLength(member);
            return member;
        }
        const source = numberSource(member);
        if (source !== undefined)
            return /^[^.eE]+$/u.test(source)
                ? wireInteger(member, null, null)
                : wireNumber(member, null, null);
        if (isArray(member))
            return Object.freeze(member.map((item) => decode(item, depth + 1)));
        if (!isRecord(member)) throw new WireError("schema");
        const result: { [key: string]: JsonValue } = {};
        if (Reflect.ownKeys(member).length !== Object.keys(member).length)
            throw new WireError("schema");
        for (const key of Object.keys(member)) {
            codePointLength(key);
            const descriptor = Object.getOwnPropertyDescriptor(member, key);
            if (
                descriptor === undefined ||
                descriptor.get !== undefined ||
                descriptor.set !== undefined
            )
                throw new WireError("schema");
            Object.defineProperty(result, key, {
                value: decode(member[key], depth + 1),
                enumerable: true,
            });
        }
        return Object.freeze(result);
    }
    return decode(value, 0);
}
