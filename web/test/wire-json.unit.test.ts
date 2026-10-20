import { expect, test } from "vitest";
import {
    codePointLength,
    hasNativeSourceContext,
    NORMAL_JSON_LIMITS,
    numberSource,
    parseWireJson,
    readBoundedJson,
    abortable,
} from "../src/wire/json";
import {
    isRecord,
    wireArray,
    wireBoolean,
    wireInteger,
    wireJsonValue,
    wireLiteral,
    wireNull,
    wireNumber,
    wireObject,
    wireString,
    wireUnion,
} from "../src/wire/runtime";

function value(text: string): unknown {
    const parsed = parseWireJson(`{"value":${text}}`);
    if (!isRecord(parsed)) throw new Error("Expected fixture object.");
    return parsed.value;
}

test("native primitive source support is required, with no rounded fallback", () => {
    expect(hasNativeSourceContext()).toBe(true);
    expect(
        hasNativeSourceContext((_text, reviver) => reviver("integer", 1)),
    ).toBe(false);
    expect(hasNativeSourceContext(() => null)).toBe(false);
});

test.each([
    "9007199254740991.4",
    "9007199254740993",
    "1e309",
    "1.0",
    "1.0000000000000001",
    "1e0",
])("raw token %s survives before strict integer refusal", (source) => {
    const token = value(source);
    expect(numberSource(token)).toBe(source);
    expect(() => wireInteger(token, null, null)).toThrow();
});

test("integer ranges are exact before conversion and float rules stay separate", () => {
    expect(
        wireInteger(value("9007199254740991"), "0", "9223372036854775807"),
    ).toBe(Number.MAX_SAFE_INTEGER);
    expect(wireInteger(value("-0"), "0", null)).toBe(0);
    expect(() => wireInteger(value("-1"), "0", null)).toThrow();
    expect(() => wireInteger(value("2"), null, "1")).toThrow();
    expect(() =>
        wireInteger(value("12345678901234567890"), null, null),
    ).toThrow();
    expect(() => wireInteger(true, null, null)).toThrow();
    expect(wireNumber(value("1.0"), "0", null)).toBe(1);
    expect(wireNumber(value("1e1"), null, "10")).toBe(10);
    expect(() => wireNumber(value("1e309"), null, null)).toThrow();
    expect(() => wireNumber(value("-1.0"), "0", null)).toThrow();
    expect(() => wireNumber(value("2.0"), null, "1")).toThrow();
    expect(() => wireNumber(1, null, null)).toThrow();
});

test.each([
    '{"a":1,"a":1}',
    '{"é":1,"\\u00e9":1}',
    '{"𝄞":1,"\\ud834\\udd1e":2}',
    '{"nested":{"a":1,"a":2}}',
])("every duplicate decoded key refuses: %s", (text) => {
    expect(() => parseWireJson(text)).toThrow();
});

test("Unicode scalar length, lexical strings and inert keys survive without pollution", () => {
    expect(codePointLength("𝄞雪")).toBe(2);
    expect(wireString("𝄞".repeat(64), 64, 64, null)).toHaveLength(128);
    expect(() => wireString("𝄞".repeat(65), null, 64, null)).toThrow();
    expect(() => codePointLength("\ud800")).toThrow();
    expect(() => codePointLength("\udc00")).toThrow();
    const context = wireJsonValue(
        parseWireJson('{"__proto__":{"polluted":true},"constructor":"inert"}'),
        4,
        20,
    );
    if (!isRecord(context)) throw new Error("Expected context object.");
    expect(Object.hasOwn(context, "__proto__")).toBe(true);
    expect(Object.getPrototypeOf({})).toBe(Object.prototype);
    expect(Object.hasOwn(Object.prototype, "polluted")).toBe(false);
    expect(
        wireJsonValue(parseWireJson('[null,true,"snow",1,1.0]'), 4, 20),
    ).toEqual([null, true, "snow", 1, 1]);
});

test.each([
    '{"s":"\\ud800"}',
    '"\ud800"',
    '{"\\ud800":1}',
    "\ufeff{}",
    "[",
    "}",
    '"unterminated',
    '"\\x"',
    '{"a" 1}',
    "[1,]",
    "[true false]",
])("malformed input refuses: %s", (text) => {
    expect(() => parseWireJson(text)).toThrow();
});

test("aggregate work and byte budgets refuse before unbounded native parsing", () => {
    expect(() =>
        parseWireJson("[[[]]]", { ...NORMAL_JSON_LIMITS, maxDepth: 2 }),
    ).toThrow();
    expect(() =>
        parseWireJson('{"a":1,"b":2}', { ...NORMAL_JSON_LIMITS, maxKeys: 1 }),
    ).toThrow();
    expect(() =>
        parseWireJson("[1,2]", { ...NORMAL_JSON_LIMITS, maxTokens: 2 }),
    ).toThrow();
    expect(() =>
        parseWireJson('"雪"', { ...NORMAL_JSON_LIMITS, maxBytes: 4 }),
    ).toThrow();
    expect(() =>
        parseWireJson("123", { ...NORMAL_JSON_LIMITS, maxNumberCharacters: 2 }),
    ).toThrow();
    expect(() =>
        parseWireJson("{}", { ...NORMAL_JSON_LIMITS, maxBytes: Infinity }),
    ).toThrow();
    expect(() => wireJsonValue(parseWireJson("[[1]]"), 1, 20)).toThrow();
    expect(() => wireJsonValue(parseWireJson("[1,2]"), 4, 2)).toThrow();
});

test("closed reconstruction preserves false/zero/null and refuses missing or extra fields", () => {
    expect(
        wireObject(parseWireJson('{"a":false,"b":0,"c":null}'), [
            "a",
            "b",
            "c",
        ]),
    ).toBeDefined();
    expect(() => wireObject({}, ["a"])).toThrow();
    expect(() => wireObject({ a: 1 }, [])).toThrow();
    expect(() => wireObject(new Date(), [])).toThrow();
    expect(() =>
        wireObject(
            Object.defineProperty({}, "a", { get: () => 1, enumerable: true }),
            ["a"],
        ),
    ).toThrow();
    expect(wireBoolean(false)).toBe(false);
    expect(() => wireBoolean(0)).toThrow();
    expect(wireNull(null)).toBe(null);
    expect(() => wireNull(undefined)).toThrow();
    expect(wireLiteral(value("1"), 1)).toBe(1);
    expect(() => wireLiteral("a", "b")).toThrow();
    expect(
        wireArray(
            parseWireJson('["x"]'),
            (item) => wireString(item, 1, 1, "x"),
            1,
            1,
        ),
    ).toEqual(["x"]);
    expect(() => wireArray([], wireBoolean, 1, null)).toThrow();
    expect(() => wireArray([true, false], wireBoolean, null, 1)).toThrow();
    expect(() => wireArray(null, wireBoolean, null, null)).toThrow();
    expect(() => wireString(1, null, null, null)).toThrow();
    expect(() => wireString("", 1, null, null)).toThrow();
    expect(() => wireString("x", null, null, "y")).toThrow();
    expect(wireUnion(null, [wireNull])).toBe(null);
    expect(() => wireUnion(1, [wireNull])).toThrow();
    expect(() =>
        wireUnion(1, [
            () => {
                throw new Error("bug");
            },
        ]),
    ).toThrow("bug");
});

function response(
    body: BodyInit | null,
    headers: HeadersInit = { "content-type": "application/json" },
): Response {
    return new Response(body, { headers });
}

test("bounded streams decode UTF-8 and compare only identity Content-Length", async () => {
    expect(isRecord(await readBoundedJson(response('{"雪":false}')))).toBe(
        true,
    );
    await expect(
        readBoundedJson(
            response("{}", {
                "content-type": "application/json",
                "content-length": "2",
            }),
        ),
    ).resolves.toEqual({});
    await expect(
        readBoundedJson(
            response("{}", {
                "content-type": "application/json",
                "content-length": "100",
                "content-encoding": "gzip",
            }),
        ),
    ).resolves.toEqual({});
    for (const bytes of [
        [0xc3, 0x28],
        [0xe2, 0x82],
        [0xed, 0xa0, 0x80],
        [0xef, 0xbb, 0xbf, 0x7b, 0x7d],
    ])
        await expect(
            readBoundedJson(response(new Uint8Array(bytes))),
        ).rejects.toThrow();
    await expect(readBoundedJson(response(null))).rejects.toThrow();
    await expect(readBoundedJson(response("{}", {}))).rejects.toThrow();
    await expect(
        readBoundedJson(response("{}", { "content-type": "text/html" })),
    ).rejects.toThrow();
    await expect(
        readBoundedJson(
            response("{}", {
                "content-type": "application/json",
                "content-length": "1,1",
            }),
        ),
    ).rejects.toThrow();
    await expect(
        readBoundedJson(
            response("{}", {
                "content-type": "application/json",
                "content-length": "1",
            }),
        ),
    ).rejects.toThrow();
    await expect(
        readBoundedJson(
            response("{}", {
                "content-type": "application/json",
                "content-length": "100",
            }),
            { limits: { ...NORMAL_JSON_LIMITS, maxBytes: 10 } },
        ),
    ).rejects.toThrow();
    await expect(
        readBoundedJson(response("[true]"), {
            limits: { ...NORMAL_JSON_LIMITS, maxBytes: 2 },
        }),
    ).rejects.toThrow();
});

test("aborted or stalled reads cancel their reader without creating another request", async () => {
    expect(await abortable(Promise.resolve(1))).toBe(1);
    const controller = new AbortController();
    let canceled = false;
    const stream = new ReadableStream<Uint8Array>({
        cancel() {
            canceled = true;
        },
    });
    const read = readBoundedJson(response(stream), {
        signal: controller.signal,
    });
    controller.abort();
    await expect(read).rejects.toThrow();
    expect(canceled).toBe(true);
    await expect(
        abortable(Promise.resolve(1), controller.signal),
    ).rejects.toThrow();
});
