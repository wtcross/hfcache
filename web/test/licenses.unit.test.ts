import { afterEach, expect, test } from "vitest";
import {
    mkdtempSync,
    mkdirSync,
    readFileSync,
    rmSync,
    symlinkSync,
    writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = fileURLToPath(new URL("../", import.meta.url));
const temporary: string[] = [];
afterEach(() => {
    for (const path of temporary.splice(0)) rmSync(path, { recursive: true });
});

test("the frozen browser dependency closure has complete installed license notices", () => {
    const result = spawnSync(
        process.execPath,
        [join(root, "scripts/licenses.ts")],
        {
            cwd: root,
            encoding: "utf8",
            timeout: 15000,
        },
    );
    expect(result.status, result.stderr).toBe(0);
    expect(result.stdout).toContain(
        "License inventory and production notices match frozen lock",
    );
    const notices = readFileSync(join(root, "THIRD_PARTY_NOTICES.txt"), "utf8");
    for (const name of [
        "react-markdown@10.1.0",
        "remark-gfm@4.0.1",
        "rehype-sanitize@6.0.0",
        "@ungap/structured-clone@1.4.0",
    ])
        expect(notices).toContain("--- " + name + " (");
    expect(notices).toContain("ISC License");
    expect(notices).toContain("LGPL-2.1-or-later");
});

test("a parser dependency cannot be relabelled as build-only to omit its shipped notice", () => {
    const work = mkdtempSync(join(tmpdir(), "hfcache-license-classification-"));
    temporary.push(work);
    for (const name of [
        "package.json",
        "pnpm-lock.yaml",
        "scripts/licenses.ts",
        "dependencies/licenses.json",
    ]) {
        const target = join(work, name);
        mkdirSync(dirname(target), { recursive: true });
        writeFileSync(target, readFileSync(join(root, name)));
    }
    symlinkSync(join(root, "node_modules"), join(work, "node_modules"), "dir");
    const inventory = join(work, "dependencies/licenses.json");
    // This is an independently corrupted external input to the real checker.
    const original = readFileSync(inventory, "utf8");
    const marker =
        /("name": "react-markdown",[\s\S]*?"use": ")production-dependency-closure(")/u;
    expect(marker.test(original)).toBe(true);
    writeFileSync(inventory, original.replace(marker, "$1build-test-only$2"));
    const result = spawnSync(
        process.execPath,
        [join(work, "scripts/licenses.ts")],
        {
            cwd: work,
            encoding: "utf8",
            timeout: 15000,
        },
    );
    expect(result.status).toBe(1);
    expect(result.stderr).toContain(
        "Unreviewed or inconsistent package license record: react-markdown@10.1.0",
    );
});
