import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";
import { canonicalJson, sha256 } from "../scripts/build-artifact";
import { verifyIndex } from "../scripts/check-build";

test("artifact canonical JSON uses Python serializer spelling and sorted own keys", () => {
    expect(canonicalJson({ z: [{ b: 1, a: "管理" }], a: true })).toBe(
        '{\n  "a": true,\n  "z": [\n    {\n      "a": "管理",\n      "b": 1\n    }\n  ]\n}\n',
    );
    expect(sha256("abc")).toBe(
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    );
    const accessor = {
        get secret() {
            throw new Error("Accessor executed.");
        },
    };
    expect(() => canonicalJson(accessor)).toThrow("Non-data");
    expect(() => canonicalJson({ missing: undefined })).toThrow("Missing");
    expect(() => canonicalJson({ bad: Infinity })).toThrow("Nonfinite");
    const inert: unknown = JSON.parse('{"__proto__":{"polluted":true}}');
    expect(canonicalJson(inert)).toContain('"__proto__"');
    expect(Object.hasOwn({}, "polluted")).toBe(false);
});
test("Node independently verifies actual source HTML marker placement after bundling", () => {
    const source = readFileSync(
        fileURLToPath(new URL("../index.html", import.meta.url)),
        "utf8",
    );
    const built = source.replace(
        '<script type="module" src="/src/main.tsx"></script>',
        '<script type="module" crossorigin src="./assets/index-12345678.js"></script>',
    );
    expect(() => {
        verifyIndex(built);
    }).not.toThrow();
    for (const changed of [
        built.replace("__HFCACHE_UI_CONTRACT_V1__", "2"),
        built + "<!-- __HFCACHE_UI_BASE_V1__ -->",
        built.replace(
            '<base href="__HFCACHE_UI_BASE_V1__" />',
            '<base href="/ui/" />',
        ),
        built.replace("Reload interface", "Reload"),
        built.replace(
            'type="module" crossorigin',
            'type="module" onclick="run()" crossorigin',
        ),
        built.replace("</script>", "run()</script>"),
        built.replace(
            "./assets/index-12345678.js",
            "https://foreign.invalid/app.js",
        ),
        built.replace(
            '<script type="module" crossorigin src="./assets/index-12345678.js"></script>',
            "",
        ),
    ])
        expect(() => {
            verifyIndex(changed);
        }).toThrow();
});
