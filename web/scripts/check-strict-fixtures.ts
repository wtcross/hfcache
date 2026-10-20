import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { mkdirSync, writeFileSync } from "node:fs";

const root = fileURLToPath(new URL("../", import.meta.url));
const compiler = fileURLToPath(
    new URL("../node_modules/typescript/bin/tsc", import.meta.url),
);
mkdirSync(new URL("../.artifacts/", import.meta.url), { recursive: true });
writeFileSync(
    new URL("../.artifacts/rejected-types.tsconfig.json", import.meta.url),
    JSON.stringify({
        extends: "../tsconfig.json",
        include: ["../test/strict-fixtures/rejected-types.ts"],
    }),
);
const badTypes = spawnSync(
    process.execPath,
    [compiler, "--project", ".artifacts/rejected-types.tsconfig.json"],
    { cwd: root, encoding: "utf8", timeout: 30000 },
);
if (
    badTypes.error !== undefined ||
    badTypes.signal !== null ||
    badTypes.status !== 2 ||
    !badTypes.stdout.includes("TS2322") ||
    !badTypes.stdout.includes("TS2375")
) {
    console.error(
        "Strict TypeScript rejection fixture did not establish both required failures.",
    );
    process.exitCode = 1;
}
const linter = fileURLToPath(
    new URL("../node_modules/eslint/bin/eslint.js", import.meta.url),
);
const unsafe = spawnSync(
    process.execPath,
    [
        linter,
        "--config",
        "test/strict-fixtures/eslint.config.mjs",
        "--no-ignore",
        "test/strict-fixtures/rejected-assertion.ts",
    ],
    { cwd: root, encoding: "utf8", timeout: 30000 },
);
if (
    unsafe.error !== undefined ||
    unsafe.signal !== null ||
    unsafe.status !== 1 ||
    !unsafe.stdout.includes("@typescript-eslint/no-unsafe-type-assertion")
) {
    console.error(
        "Unsafe assertion rejection fixture did not establish the required failure.",
    );
    process.exitCode = 1;
}
if (process.exitCode === undefined)
    console.log(
        "Strict fixtures: unchecked index, optional value and blind unknown assertion rejected.",
    );
