import { expect, test } from "vitest";
import goldens from "../../tests/fixtures/web_wire/goldens.json";
import { decodeNamed } from "../src/wire/generated";
import {
    codePointLength,
    hasNativeSourceContext,
    NORMAL_JSON_LIMITS,
    parseWireJson,
    readBoundedJson,
    WireError,
} from "../src/wire/json";
import {
    wireInteger,
    wireJsonValue,
    wireNumber,
    wireObject,
    wireString,
} from "../src/wire/runtime";

for (const fixture of goldens) {
    test(`independent original-authority golden reconstructs ${fixture.case_id}`, () => {
        const value = decodeNamed(
            fixture.definition,
            parseWireJson(JSON.stringify(fixture.value)),
        );
        expect(value).toEqual(fixture.value);
        expect(value).not.toBe(fixture.value);
    });
}

test.each([undefined, null, false, true, "1", 0, 2])(
    "generated exact schema refuses %s rather than filling a default",
    (schema_version) => {
        const original = goldens.find((row) => row.definition === "ClientRead");
        if (original === undefined)
            throw new Error("Independent ClientRead golden is missing.");
        expect(() =>
            decodeNamed(
                "ClientRead",
                parseWireJson(
                    JSON.stringify({ ...original.value, schema_version }),
                ),
            ),
        ).toThrow(WireError);
    },
);

test.each([
    { definition: "Capabilities", patch: { maintenance_enabled: 0 } },
    { definition: "Capabilities", patch: { reads: null } },
    { definition: "Capabilities", patch: { capabilities: ["read", "write"] } },
    { definition: "Capabilities", patch: { capabilities: ["read", "read"] } },
    { definition: "Capabilities", patch: { max_page_size: 0 } },
    { definition: "ModelVariant", patch: { total_bytes: 1 } },
    { definition: "ModelVariant", patch: { total_bytes: null } },
    { definition: "CatalogEntry", patch: { enabled: null } },
    { definition: "Reference", patch: { publication_generation: 0 } },
    {
        definition: "Reference",
        patch: { publication_id: "0".repeat(32) + "\n" },
    },
    { definition: "Reference", patch: { commit_sha: "A".repeat(40) } },
])(
    "independent $definition semantic or strict primitive mutation refuses: $patch",
    ({ definition, patch }) => {
        const original = goldens.find((row) => row.definition === definition);
        if (original === undefined)
            throw new Error("Independent source golden is missing.");
        expect(() =>
            decodeNamed(
                definition,
                parseWireJson(JSON.stringify({ ...original.value, ...patch })),
            ),
        ).toThrow(WireError);
    },
);

test.each([
    {
        definition: "CatalogEntry",
        field: "tags",
        values: Array.from(
            { length: 65 },
            (_, index) => `tag-${String(index)}`,
        ),
    },
    {
        definition: "ModelVariant",
        field: "members",
        values: Array.from({ length: 4097 }, (_, index) => ({
            path: `part-${String(index)}.gguf`,
            size_bytes: 0,
        })),
    },
    {
        definition: "ModelVariant",
        field: "source_paths",
        values: Array.from(
            { length: 65 },
            (_, index) => `part-${String(index)}.gguf`,
        ),
    },
])(
    "normalized source array bound is enforced for $definition.$field",
    ({ definition, field, values }) => {
        const original = goldens.find((row) => row.definition === definition);
        if (original === undefined)
            throw new Error("Independent source golden is missing.");
        expect(() =>
            decodeNamed(
                definition,
                parseWireJson(
                    JSON.stringify({ ...original.value, [field]: values }),
                ),
            ),
        ).toThrow(WireError);
    },
);

test("native numeric source support is required rather than silently rounding", () => {
    expect(hasNativeSourceContext()).toBe(true);
    expect(
        hasNativeSourceContext((text, reviver) => {
            const parsed: unknown = JSON.parse(
                text,
                (key: string, value: unknown): unknown => reviver(key, value),
            );
            return parsed;
        }),
    ).toBe(false);
});

test.each(["0", "1", "9007199254740991", "-9007199254740991"])(
    "integer lexeme %s stays exact",
    (raw) => {
        expect(wireInteger(parseWireJson(raw), null, null)).toBe(Number(raw));
    },
);

test.each([
    "9007199254740993",
    "9223372036854775807",
    "-9007199254740992",
    "9007199254740991.1",
    "1.0000000000000001",
    "1.0",
    "1e0",
    "1e309",
    "true",
    "null",
    '"1"',
])(
    "integer field refuses raw token %s before rounded meaning can escape",
    (raw) => {
        expect(() =>
            wireInteger(parseWireJson(raw), "0", "9223372036854775807"),
        ).toThrow(WireError);
    },
);

test("legitimate float fields retain their separate number semantics", () => {
    expect(wireNumber(parseWireJson("1.0"), "0", null)).toBe(1);
    expect(wireNumber(parseWireJson("1.25e2"), "0", null)).toBe(125);
    expect(() => wireNumber(parseWireJson("1e309"), null, null)).toThrow(
        WireError,
    );
    expect(() => wireNumber(parseWireJson("-1.0"), "0", null)).toThrow(
        WireError,
    );
});

test.each([
    '{"same":1,"same":2}',
    '{"a":0,"\\u0061":1}',
    '{"outer":{"x":0,"x":1}}',
])("duplicate member identity is refused: %s", (raw) => {
    expect(() => parseWireJson(raw)).toThrow(/duplicate_key/u);
});

test.each([
    '{"unclosed":',
    "[[}",
    "[1,]",
    '{"x":NaN}',
    '{"x":Infinity}',
    "\ufeff{}",
    '"\\ud800"',
    '"\\udfff"',
])("malformed or non-scalar text is refused: %s", (raw) => {
    expect(() => parseWireJson(raw)).toThrow(WireError);
});

test("code-point bounds accept valid non-BMP strings and reject lone surrogates", () => {
    const text = "𐀀".repeat(64);
    expect(codePointLength(text)).toBe(64);
    expect(
        wireString(parseWireJson(JSON.stringify(text)), null, 64, null),
    ).toBe(text);
    expect(() => wireString(text + "a", null, 64, null)).toThrow(WireError);
    expect(() => codePointLength("\ud800")).toThrow(WireError);
});

test("generic diagnostic context preserves inert prototype-like keys", () => {
    const context = wireObject(
        wireJsonValue(
            parseWireJson(
                '{"__proto__":{"polluted":true},"constructor":"inert","value":0}',
            ),
            32,
            100,
        ),
        ["__proto__", "constructor", "value"],
    );
    expect(Object.hasOwn(context, "__proto__")).toBe(true);
    expect("polluted" in {}).toBe(false);
    expect(JSON.stringify(context)).toBe(
        '{"__proto__":{"polluted":true},"constructor":"inert","value":0}',
    );
});

test("forbidden object extras, inherited values and accessors never establish a typed record", () => {
    expect(() =>
        wireObject({ allowed: true, extra: false }, ["allowed"]),
    ).toThrow(WireError);
    expect(() =>
        wireObject(Object.create({ allowed: true }), ["allowed"]),
    ).toThrow(WireError);
    const getter = Object.defineProperty({}, "allowed", {
        get() {
            throw new Error("must not execute");
        },
        enumerable: true,
    });
    expect(() => wireObject(getter, ["allowed"])).toThrow(WireError);
});

test.each([
    { raw: "[[[]]]", limits: { ...NORMAL_JSON_LIMITS, maxDepth: 2 } },
    { raw: '{"a":0,"b":0}', limits: { ...NORMAL_JSON_LIMITS, maxKeys: 1 } },
    { raw: "[0,0,0]", limits: { ...NORMAL_JSON_LIMITS, maxTokens: 3 } },
    {
        raw: "123456789",
        limits: { ...NORMAL_JSON_LIMITS, maxNumberCharacters: 8 },
    },
    { raw: '"éé"', limits: { ...NORMAL_JSON_LIMITS, maxBytes: 5 } },
    { raw: "null", limits: { ...NORMAL_JSON_LIMITS, maxBytes: 0 } },
])(
    "finite parser bounds are enforced before returning data",
    ({ raw, limits }) => {
        expect(() => parseWireJson(raw, limits)).toThrow(/bounds/u);
    },
);

test.each([
    { bytes: [0xc0, 0xaf] },
    { bytes: [0xed, 0xa0, 0x80] },
    { bytes: [0xe2, 0x82] },
    { bytes: [0xff] },
])("fatal UTF8 decoding refuses malformed bytes %#", async ({ bytes }) => {
    const response = new Response(Uint8Array.from(bytes), {
        headers: { "Content-Type": "application/json" },
    });
    await expect(readBoundedJson(response)).rejects.toThrow(/utf8/u);
});

test("valid split UTF8 and declared byte length are read exactly", async () => {
    const raw = new TextEncoder().encode('"𐀀"');
    const response = new Response(
        new ReadableStream<Uint8Array>({
            start(controller) {
                for (const byte of raw) controller.enqueue(Uint8Array.of(byte));
                controller.close();
            },
        }),
        {
            headers: {
                "Content-Type": "application/json; charset=utf-8",
                "Content-Length": String(raw.byteLength),
            },
        },
    );
    expect(await readBoundedJson(response)).toBe("𐀀");
});

test.each([
    { "Content-Type": "text/html" },
    { "Content-Type": "application/json; charset=latin-1" },
    { "Content-Type": "application/json", "Content-Length": "2, 2" },
    { "Content-Type": "application/json", "Content-Length": "3" },
    {
        "Content-Type": "application/json",
        "Content-Length": "99999999999999999999",
    },
])(
    "response headers cannot substitute guessed or unbounded JSON",
    async (headers) => {
        await expect(
            readBoundedJson(new Response("{}", { headers })),
        ).rejects.toThrow(WireError);
    },
);

test("stream byte overflow cancels the original source", async () => {
    let cancelled = false;
    const response = new Response(
        new ReadableStream<Uint8Array>({
            start(controller) {
                controller.enqueue(new Uint8Array(12));
            },
            cancel() {
                cancelled = true;
            },
        }),
        { headers: { "Content-Type": "application/json" } },
    );
    await expect(
        readBoundedJson(response, {
            limits: { ...NORMAL_JSON_LIMITS, maxBytes: 10 },
        }),
    ).rejects.toThrow(/bounds/u);
    expect(cancelled).toBe(true);
});

test("aborting a stalled body cancels the original read without producing facts", async () => {
    let cancelled = false;
    const response = new Response(
        new ReadableStream<Uint8Array>({
            cancel() {
                cancelled = true;
            },
        }),
        { headers: { "Content-Type": "application/json" } },
    );
    const controller = new AbortController();
    const read = readBoundedJson(response, { signal: controller.signal });
    controller.abort();
    await expect(read).rejects.toThrow(/aborted/iu);
    expect(cancelled).toBe(true);
});

test("empty chunks spend a finite work budget instead of growing retained metadata forever", async () => {
    let reads = 0;
    let cancelled = false;
    const response = new Response(
        new ReadableStream<Uint8Array>({
            pull(controller) {
                reads += 1;
                if (reads > 70000)
                    throw new Error(
                        "collector exceeded the independently bounded fixture",
                    );
                controller.enqueue(new Uint8Array(0));
            },
            cancel() {
                cancelled = true;
            },
        }),
        { headers: { "Content-Type": "application/json" } },
    );
    await expect(readBoundedJson(response)).rejects.toThrow(/bounds/u);
    expect(reads).toBeLessThan(70000);
    expect(cancelled).toBe(true);
});
