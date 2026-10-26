import { describe, expect, test } from "vitest";
import {
    DEFAULT_LIBRARY_FILTERS,
    LibraryFilterError,
    libraryFragment,
    normalizeLibraryFilters,
    parseLibraryFragment,
    setLibraryType,
    updateLibraryFilters,
} from "../src/library/filters";

describe("bounded Library filter bookmarks", () => {
    test("empty input explicitly selects both types/all repositories/current and a finite page", () => {
        expect(parseLibraryFragment("")).toEqual({
            scope: "all",
            revision_scope: "current",
            tag_source: "current_or_last_observed",
            limit: 25,
        });
        expect(parseLibraryFragment("#")).toEqual(DEFAULT_LIBRARY_FILTERS);
        expect(Object.isFrozen(DEFAULT_LIBRARY_FILTERS)).toBe(true);
    });
    test("roundtrips only existing API filters and preserves literal Unicode spelling", () => {
        const input = normalizeLibraryFilters({
            type: "model",
            q: "  STRAẞE e\u0301 😀  ",
            tag_all: [" GPU ", "gpu", "format:gguf"],
            tag_any: ["reviewed", "GPU"],
            tag_source: "current_only",
            scope: "configured",
            revision_scope: "retained",
            format: "GGUF",
            quantization: "q4_k_m",
            quantization_method: "GGUF",
            bits: 4,
            max_variant_bytes: 0,
            limit: 50,
        });
        expect(input.q).toBe("  STRAẞE e\u0301 😀  ");
        expect(input.tag_all).toEqual(["format:gguf", "gpu"]);
        expect(input.tag_any).toEqual(["gpu", "reviewed"]);
        expect(input).toMatchObject({
            format: "gguf",
            quantization: "Q4_K_M",
            quantization_method: "gguf",
            max_variant_bytes: 0,
        });
        expect(parseLibraryFragment(libraryFragment(input))).toEqual(input);
        expect(libraryFragment(input)).not.toContain("?");
        expect(Object.isFrozen(input.tag_all)).toBe(true);
    });
    test("q bound is Unicode scalar values, without casefold or NFC expansion", () => {
        const q = "😀".repeat(255) + "ß";
        expect(normalizeLibraryFilters({ q }).q).toBe(q);
        expect(() => normalizeLibraryFilters({ q: q + "x" })).toThrow(
            LibraryFilterError,
        );
    });
    test("tag all and any remain separate conjunctive predicates", () => {
        expect(
            parseLibraryFragment("#tag_all=b&tag_all=a&tag_any=c&tag_any=b"),
        ).toMatchObject({ tag_all: ["a", "b"], tag_any: ["b", "c"] });
    });
    test.each([
        "#q=x&q=y",
        "#type=model&type=dataset",
        "#limit=25&limit=50",
        "#facet=tag",
        "#selector=model:owner/repo",
        "#cursor=opaque",
        "#toString=x",
        "#__proto__=x",
        "#q",
        "#=x",
        "#q=x&",
        "#q=%",
        "#q=%F0%9F",
        "#q=%ED%A0%80",
    ])("rejects unknown, ambiguous or malformed fragment %s", (value) => {
        expect(() => parseLibraryFragment(value)).toThrow(LibraryFilterError);
    });
    test.each([
        "\ud800",
        "\udfff",
        "\u0000",
        "\n",
        "\u0085",
        "\u202e",
        "\u2066",
    ])("refuses unsafe text before URL replacement", (text) => {
        expect(() => normalizeLibraryFilters({ q: text })).toThrow(
            LibraryFilterError,
        );
        expect(() => parseLibraryFragment("#q=" + text)).toThrow(
            LibraryFilterError,
        );
    });
    test.each([
        "#bits=01",
        "#bits=+1",
        "#bits=-1",
        "#bits=1.0",
        "#bits=1e1",
        "#bits=0",
        "#bits=65",
        "#bits=Infinity",
        "#max_variant_bytes=9007199254740992",
        "#limit=0",
        "#limit=101",
        "#limit=",
    ])("refuses noncanonical or out-of-range numeric field %s", (fragment) => {
        expect(() => parseLibraryFragment(fragment)).toThrow(
            LibraryFilterError,
        );
    });
    test.each([{}, [], null, 1.5, "25", false])(
        "does not coerce a limit",
        (limit) => {
            expect(() => normalizeLibraryFilters({ limit })).toThrow(
                LibraryFilterError,
            );
        },
    );
    test("accepts exact safe integer bounds and zero logical bytes", () => {
        expect(
            parseLibraryFragment(
                "#bits=64&max_variant_bytes=9007199254740991&limit=100",
            ),
        ).toMatchObject({
            type: "model",
            bits: 64,
            max_variant_bytes: Number.MAX_SAFE_INTEGER,
            limit: 100,
        });
    });
    test.each([
        { tag_all: Array<string>(65).fill("gpu") },
        { tag_any: [" ".repeat(129)] },
        { tag_any: ["café"] },
        { format: "not a format" },
        { quantization: "x".repeat(65) },
        { tag_source: "historical_only" },
        { scope: "unmanaged" },
        { revision_scope: "all" },
        { unknown: "private-value" },
        { q: null },
    ])("refuses unsupported values without echo", (input) => {
        expect(() => normalizeLibraryFilters(input)).toThrow(
            "Library filters are invalid or exceed the supported bounds.",
        );
    });
    test("bounds raw and encoded work, even where repeated tags normalize smaller", () => {
        expect(() => parseLibraryFragment("#q=" + "x".repeat(8192))).toThrow(
            LibraryFilterError,
        );
        const tags = Array.from(
            { length: 64 },
            (_, i) => String(i).padStart(2, "0") + ":".repeat(62),
        );
        expect(() =>
            normalizeLibraryFilters({ tag_all: tags, tag_any: tags }),
        ).toThrow(LibraryFilterError);
    });
    test("omits empty controls without introducing null API filters", () => {
        expect(
            normalizeLibraryFilters({
                q: "",
                format: "",
                quantization: "",
                quantization_method: "",
                tag_all: [],
                tag_any: [],
                cursor: "",
            }),
        ).toEqual(DEFAULT_LIBRARY_FILTERS);
    });
    test("direct dataset/model predicates refuse; deliberate dataset switch clears and announces", () => {
        expect(() =>
            normalizeLibraryFilters({ type: "dataset", bits: 4 }),
        ).toThrow(LibraryFilterError);
        const model = normalizeLibraryFilters({
            bits: 4,
            quantization: "Q4_K_M",
            quantization_method: "gguf",
            max_variant_bytes: 123,
            format: "gguf",
            cursor: "opaque",
        });
        expect(model.type).toBe("model");
        const changed = setLibraryType(model, "dataset");
        expect(changed.announcement).toBe(
            "Model-only variant filters were cleared for datasets.",
        );
        expect(changed.filters).toEqual({
            ...DEFAULT_LIBRARY_FILTERS,
            type: "dataset",
            format: "gguf",
        });
        expect(setLibraryType(changed.filters, undefined).filters).toEqual({
            ...DEFAULT_LIBRARY_FILTERS,
            format: "gguf",
        });
        expect(() =>
            updateLibraryFilters(changed.filters, { bits: 4 }),
        ).toThrow(LibraryFilterError);
    });
    test("semantic filter/page size changes reset continuation, equivalent tags do not", () => {
        const current = normalizeLibraryFilters({
            tag_all: ["gpu"],
            cursor: "old",
        });
        expect(
            updateLibraryFilters(current, { tag_all: [" GPU ", "gpu"] }).filters
                .cursor,
        ).toBe("old");
        expect(
            updateLibraryFilters(current, { q: "new", cursor: "unrelated" })
                .filters.cursor,
        ).toBeUndefined();
        expect(
            updateLibraryFilters(current, { limit: 50 }).filters.cursor,
        ).toBeUndefined();
        expect(
            updateLibraryFilters(current, { cursor: "next" }).filters.cursor,
        ).toBe("next");
        expect(libraryFragment(current)).not.toContain("cursor");
        expect(
            parseLibraryFragment(libraryFragment(current)).cursor,
        ).toBeUndefined();
    });
    test("clearing controls is explicit; fragment never grants a transport path", () => {
        const input = normalizeLibraryFilters({
            q: "owner/repo",
            format: "gguf",
        });
        expect(
            updateLibraryFilters(input, { q: undefined, format: undefined })
                .filters,
        ).toEqual(DEFAULT_LIBRARY_FILTERS);
        expect(() =>
            normalizeLibraryFilters({ origin: "https://foreign.example" }),
        ).toThrow(LibraryFilterError);
        expect(() => parseLibraryFragment("#https://foreign.example")).toThrow(
            LibraryFilterError,
        );
    });
    test("accessors and nonplain objects cannot supply filter values", () => {
        let reads = 0;
        expect(() =>
            normalizeLibraryFilters({
                get q() {
                    reads++;
                    return "private";
                },
            }),
        ).toThrow(LibraryFilterError);
        expect(reads).toBe(0);
        expect(() => normalizeLibraryFilters(new Date())).toThrow(
            LibraryFilterError,
        );
        expect(() =>
            updateLibraryFilters(
                {},
                {
                    get q() {
                        reads++;
                        return "private";
                    },
                },
            ),
        ).toThrow(LibraryFilterError);
        expect(reads).toBe(0);
    });
});
