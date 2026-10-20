import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, expect, test } from "vitest";
import {
    pythonCollisionKey,
    pythonCasefold,
    pythonNfc,
    pythonIsPrintable,
    PYTHON_UNICODE_VERSION,
    UnicodeWork,
} from "../src/wire/unicode";

function fixture(name: string): string {
    return gunzipSync(
        readFileSync(
            new URL(
                `../../tests/fixtures/unicode16/${name}.txt.gz`,
                import.meta.url,
            ),
        ),
    ).toString("utf8");
}
function sequence(points: string): string {
    return points
        .trim()
        .split(/\s+/u)
        .map((value) => String.fromCodePoint(Number.parseInt(value, 16)))
        .join("");
}

describe("pinned Unicode16 authority independent of the engine's Unicode release", () => {
    test("all official normalization vectors satisfy the five NFC invariants", () => {
        expect(PYTHON_UNICODE_VERSION).toBe("16.0.0");
        let rows = 0;
        for (const line of fixture("NormalizationTest").split("\n")) {
            const row = line.split("#")[0]?.trim();
            if (row === undefined || row === "" || row.startsWith("@"))
                continue;
            const [a, b, c, d, e] = row.split(";").slice(0, 5).map(sequence);
            if (
                a === undefined ||
                b === undefined ||
                c === undefined ||
                d === undefined ||
                e === undefined
            )
                throw new Error("Truncated official normalization vector");
            for (const input of [a, b, c]) expect(pythonNfc(input)).toBe(b);
            for (const input of [d, e]) expect(pythonNfc(input)).toBe(d);
            rows++;
        }
        expect(rows).toBe(19965);
    });
    test("all official common/full casefold mappings agree with collision keys", () => {
        let rows = 0;
        for (const line of fixture("CaseFolding").split("\n")) {
            const row = line.split("#")[0]?.trim();
            if (row === undefined || row === "") continue;
            const [source, status, mapped] = row
                .split(";")
                .map((value) => value.trim());
            if (status !== "C" && status !== "F") continue;
            if (source === undefined || mapped === undefined)
                throw new Error("Truncated official casefold vector");
            expect(pythonCasefold(sequence(source))).toBe(sequence(mapped));
            rows++;
        }
        expect(rows).toBe(1557);
    });
    test.each([
        ["e\u0301", "é"],
        ["\u1100\u1161", "가"],
        ["\u1100\u1161\u11a8", "각"],
        ["\u212b", "Å"],
        ["\u0344", "\u0308\u0301"],
        ["\u{1e030}", "\u{1e030}"],
        ["\u0307\u0323", "\u0323\u0307"],
        ["", ""],
    ])("canonical normalization %s", (source, expected) => {
        expect(pythonNfc(source)).toBe(expected);
    });
    test("collision folding preserves compatibility distinctions and full expansion", () => {
        expect(pythonCollisionKey("Straße/ﬁle")).toBe("strasse/file");
        expect(pythonCollisionKey("Σςσ")).toBe("σσσ");
        expect(pythonCollisionKey("①/Ａ/²")).toBe("①/ａ/²");
        expect(pythonCollisionKey("İ")).toBe("i\u0307");
        expect(pythonCollisionKey("\u0390")).toBe("\u03b9\u0308\u0301");
        expect(pythonCasefold("\u1fbb")).toBe("\u1f71");
        expect(pythonCollisionKey("\u1fbb")).toBe("\u03ac");
    });
    test("work is bounded across separate strings and rejects invalid Unicode", () => {
        for (const invalid of [0, -1, Number.NaN, 8_000_001])
            expect(() => new UnicodeWork(invalid)).toThrow("bounds");
        const work = new UnicodeWork(3);
        expect(pythonCollisionKey("a", work)).toBe("a");
        expect(() => pythonCollisionKey("b", work)).toThrow("bounds");
        expect(() => pythonNfc("\ud800")).toThrow("unicode");
        expect(() => pythonNfc("a".repeat(500), new UnicodeWork(5))).toThrow(
            "bounds",
        );
    });
    test("printability follows Python16 assignment and separator rules", () => {
        for (const value of ["", " ", "é", "\u{1cc00}", "🦄", "\u0301"])
            expect(pythonIsPrintable(value)).toBe(true);
        for (const value of [
            "\n",
            "\u00a0",
            "\u2028",
            "\u200b",
            "\ud800",
            "\u{1e6c0}",
            "\u{10ffff}",
        ])
            expect(pythonIsPrintable(value)).toBe(false);
    });
});
