/** Explicit registry audit provisioning; ordinary verification remains offline. */
import { createHash } from "node:crypto";
import {
    readFileSync,
    writeFileSync,
    mkdirSync,
    existsSync,
    realpathSync,
} from "node:fs";
import { fileURLToPath } from "node:url";
import { join, sep } from "node:path";
import { createRequire } from "node:module";

const root = fileURLToPath(new URL("../", import.meta.url));
const lock = readFileSync(join(root, "pnpm-lock.yaml"), "utf8");
const digest = createHash("sha256").update(lock).digest("hex");
const inventory = join(root, "dependencies/licenses.json");
function record(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
const arguments_ = process.argv.slice(2);
const section = lock.split("\npackages:\n")[1]?.split("\nsnapshots:\n")[0];
if (section === undefined)
    throw new Error("Unknown lockfile package structure.");
const names: string[] = [];
for (const line of section.split("\n")) {
    const match = /^  (?:'([^']+)'|([^\s:]+)):\s*$/u.exec(line);
    const key = match?.[1] ?? match?.[2];
    if (key !== undefined) names.push(key);
}
if (
    names.length === 0 ||
    names.length > 1000 ||
    new Set(names).size !== names.length
)
    throw new Error("Invalid bounded lockfile inventory.");
const browser = new Set<string>();
const runtimePaths = new Map<string, string>();
const installedRoot = realpathSync(join(root, "node_modules"));
function packageMetadata(parent: string, name: string): string {
    if (!/^(?:@[a-z0-9][a-z0-9._-]*\/)?[a-z0-9][a-z0-9._-]*$/u.test(name))
        throw new Error("Invalid production package name.");
    // ESM packages may deliberately omit package.json from their exports.
    // Node's own resolution search roots still identify the installed package
    // without importing or executing its entrypoint, including type-only deps.
    const roots = createRequire(parent).resolve.paths(name);
    if (roots === null || roots.length > 64)
        throw new Error("Unbounded production package resolution.");
    for (const directory of roots) {
        const candidate = join(directory, name, "package.json");
        if (existsSync(candidate)) {
            const installed = realpathSync(candidate);
            if (!installed.startsWith(installedRoot + sep))
                throw new Error("Ambient production package is forbidden.");
            return installed;
        }
    }
    throw new Error(`Production package metadata missing: ${name}.`);
}
function runtimeClosure(parent: string, name: string) {
    const path = packageMetadata(parent, name);
    const metadata: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (
        !record(metadata) ||
        metadata.name !== name ||
        typeof metadata.version !== "string"
    )
        throw new Error("Invalid runtime package identity.");
    const key = metadata.name + "@" + metadata.version;
    if (browser.has(key)) return;
    browser.add(key);
    runtimePaths.set(key, path);
    if (metadata.dependencies !== undefined) {
        if (!record(metadata.dependencies))
            throw new Error("Invalid runtime dependency declaration.");
        for (const dependency of Object.keys(metadata.dependencies))
            runtimeClosure(path, dependency);
    }
}
const directData: unknown = JSON.parse(
    readFileSync(join(root, "package.json"), "utf8"),
);
if (
    !record(directData) ||
    !record(directData.dependencies) ||
    !record(directData.devDependencies)
)
    throw new Error("Invalid package declaration.");
for (const name of Object.keys(directData.dependencies))
    runtimeClosure(join(root, "package.json"), name);
if ([...browser].some((name) => !names.includes(name)))
    throw new Error("Production closure is absent from the frozen lock.");
const direct = new Set<string>();
for (const declaration of [
    directData.dependencies,
    directData.devDependencies,
]) {
    for (const [name, version] of Object.entries(declaration)) {
        if (typeof version !== "string")
            throw new Error("Invalid direct dependency pin.");
        direct.add(name + "@" + version);
    }
}
const approvedLicenses = new Set([
    "MIT",
    "Apache-2.0",
    "MPL-2.0",
    "ISC",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "MIT-0",
    "BlueOak-1.0.0",
    "CC-BY-4.0",
    "CC0-1.0",
]);
type PackageLicense = {
    name: string;
    version: string;
    license: string;
    relation: string;
    use: string;
    source: string;
};
function noticesFor(packages: PackageLicense[]): string {
    let notices =
        "hfcache web assets: third-party notices\n\nThe production dependency closure contains the following packages under MIT or ISC licenses; some modules may be optimized out of the static bundle.\nBuild/test dependencies and all optional-platform packages are inventoried separately in dependencies/licenses.json.\nA local operation-recovery module is adapted from the hfcache Cockpit implementation under LGPL-2.1-or-later; its notice and full license follow. No Cockpit runtime or bridge is used.\n";
    for (const dependency of packages.filter(
        (item) => item.use === "production-dependency-closure",
    )) {
        if (
            dependency.license !== "MIT" &&
            !(
                dependency.name === "@ungap/structured-clone" &&
                dependency.version === "1.4.0" &&
                dependency.license === "ISC"
            )
        )
            throw new Error(
                "Production license requires explicit notice review.",
            );
        const base = runtimePaths.get(
            dependency.name + "@" + dependency.version,
        );
        if (base === undefined)
            throw new Error("Production dependency license is missing.");
        const directory = join(base, "..");
        const filename = [
            "LICENSE",
            "LICENSE.md",
            "LICENSE.txt",
            "license",
            "license.md",
            "license.txt",
        ].find((name) => existsSync(join(directory, name)));
        if (filename === undefined)
            throw new Error(
                `Production license text missing: ${dependency.name}.`,
            );
        notices += `\n--- ${dependency.name}@${dependency.version} (${dependency.license}) ---\nSource: ${dependency.source}\n\n${readFileSync(join(directory, filename), "utf8")}\n`;
    }
    const unicode: unknown = JSON.parse(
        readFileSync(join(root, "dependencies/unicode.json"), "utf8"),
    );
    const unicodeLicense = readFileSync(
        join(root, "dependencies/UNICODE-LICENSE.txt"),
    );
    const unicodeTables = readFileSync(
        join(root, "src/wire/unicode-data.json"),
    );
    if (
        !record(unicode) ||
        unicode.schema_version !== 1 ||
        unicode.name !== "Unicode Character Database" ||
        unicode.version !== "16.0.0" ||
        unicode.license !== "Unicode-3.0" ||
        unicode.use !== "production-data" ||
        unicode.source !== "https://www.unicode.org/Public/16.0.0/ucd/" ||
        unicode.license_sha256 !==
            createHash("sha256").update(unicodeLicense).digest("hex") ||
        unicode.tables_sha256 !==
            createHash("sha256").update(unicodeTables).digest("hex")
    )
        throw new Error("Unreviewed Unicode data or license identity.");
    notices += `\n--- Unicode Character Database 16.0.0 (Unicode-3.0) ---\nSource: https://www.unicode.org/Public/16.0.0/ucd/\nDerived from the pinned Python Unicode authority for exact path collision checks.\n\n${unicodeLicense.toString("utf8")}\n`;
    const local: unknown = JSON.parse(
        readFileSync(join(root, "dependencies/local-sources.json"), "utf8"),
    );
    if (
        !record(local) ||
        Object.keys(local).sort().join(",") !== "schema_version,sources" ||
        local.schema_version !== 1 ||
        !Array.isArray(local.sources) ||
        local.sources.length !== 1
    )
        throw new Error("Unreviewed local source notice inventory.");
    const port: unknown = local.sources[0];
    const localPaths = [
        "src/state/authority.ts",
        "src/state/operation-registry.ts",
    ] as const;
    if (
        !record(port) ||
        Object.keys(port).sort().join(",") !==
            "license,license_file,license_sha256,original_commit,original_path,original_sha256,paths" ||
        JSON.stringify(port.paths) !== JSON.stringify(localPaths) ||
        port.license !== "LGPL-2.1-or-later" ||
        port.original_path !== "cockpit/src/lib/operation-registry.ts" ||
        typeof port.original_commit !== "string" ||
        !/^[0-9a-f]{40}$/u.test(port.original_commit) ||
        typeof port.original_sha256 !== "string" ||
        !/^[0-9a-f]{64}$/u.test(port.original_sha256) ||
        port.license_file !== "dependencies/LGPL-2.1.txt" ||
        port.license_sha256 !==
            "dc626520dcd53a22f727af3ee42c770e56c97a64fe3adb063799d8ab032fe551"
    )
        throw new Error("Unreviewed local operation recovery source.");
    const originalPath = port.original_path;
    const localLicense = readFileSync(join(root, port.license_file));
    const localSources = localPaths.map((path) =>
        readFileSync(join(root, path), "utf8"),
    );
    if (
        createHash("sha256").update(localLicense).digest("hex") !==
            port.license_sha256 ||
        !localSources.every((source) =>
            source.includes("SPDX-License-Identifier: LGPL-2.1-or-later"),
        ) ||
        !localSources.some((source) => source.includes(originalPath))
    )
        throw new Error(
            "Local operation recovery license/provenance is missing.",
        );
    notices += `\n--- hfcache operation recovery port (LGPL-2.1-or-later) ---\nOriginal source: ${port.original_path} at ${port.original_commit}\nOriginal source SHA256: ${port.original_sha256}\nAdapted sources: ${localPaths.map((path) => "web/" + path).join(", ")} in the hfcache source distribution.\nRebuild instructions: docs/development.md.\n\n${localLicense.toString("utf8")}\n`;
    // Remove our final separator when the upstream license already ends in LF.
    return notices.endsWith("\n\n") ? notices.slice(0, -1) : notices;
}
function validateInventory(parsed: unknown): PackageLicense[] {
    if (
        !record(parsed) ||
        parsed.schema_version !== 1 ||
        parsed.lock_sha256 !== digest ||
        typeof parsed.scope !== "string" ||
        !Array.isArray(parsed.packages) ||
        parsed.packages.length !== names.length
    )
        throw new Error(
            "Dependency inventory does not match the complete frozen lock set.",
        );
    const remaining = new Set(names);
    const packages: PackageLicense[] = [];
    for (const item of parsed.packages) {
        if (
            !record(item) ||
            Object.keys(item).sort().join(",") !==
                "license,name,relation,source,use,version" ||
            typeof item.name !== "string" ||
            typeof item.version !== "string" ||
            typeof item.license !== "string" ||
            typeof item.relation !== "string" ||
            typeof item.use !== "string" ||
            typeof item.source !== "string"
        )
            throw new Error("Malformed package license record.");
        const key = item.name + "@" + item.version;
        if (
            !remaining.delete(key) ||
            !approvedLicenses.has(item.license) ||
            item.relation !== (direct.has(key) ? "direct" : "transitive") ||
            item.use !==
                (browser.has(key)
                    ? "production-dependency-closure"
                    : "build-test-only") ||
            item.source !==
                `https://registry.npmjs.org/${encodeURIComponent(item.name)}/${encodeURIComponent(item.version)}`
        )
            throw new Error(
                `Unreviewed or inconsistent package license record: ${key}.`,
            );
        packages.push({
            name: item.name,
            version: item.version,
            license: item.license,
            relation: item.relation,
            use: item.use,
            source: item.source,
        });
    }
    if (remaining.size !== 0)
        throw new Error("Incomplete package license inventory.");
    return packages;
}
if (arguments_.length === 0) {
    const raw = readFileSync(inventory);
    if (raw.length > 1024 * 1024)
        throw new Error("Oversized dependency inventory.");
    const parsed: unknown = JSON.parse(raw.toString("utf8"));
    const packages = validateInventory(parsed);
    if (
        readFileSync(join(root, "THIRD_PARTY_NOTICES.txt"), "utf8") !==
        noticesFor(packages)
    )
        throw new Error(
            "Production notices do not match the complete audited dependency closure.",
        );
    console.log(
        `License inventory and production notices match frozen lock: ${String(packages.length)} packages; pinned Unicode16 data/license verified.`,
    );
} else if (arguments_.length === 1 && arguments_[0] === "--refresh-notices") {
    const packages = validateInventory(
        JSON.parse(readFileSync(inventory, "utf8")),
    );
    writeFileSync(join(root, "THIRD_PARTY_NOTICES.txt"), noticesFor(packages));
    console.log("Regenerated production package and Unicode notices offline.");
} else if (arguments_.length === 1 && arguments_[0] === "--refresh") {
    const packages: {
        name: string;
        version: string;
        license: string;
        relation: string;
        use: string;
        source: string;
    }[] = [];
    let offset = 0;
    async function worker() {
        while (offset < names.length) {
            const key = names[offset++];
            if (key === undefined) throw new Error("Missing package identity.");
            const at = key.lastIndexOf("@");
            const name = key.slice(0, at),
                version = key.slice(at + 1);
            const source = `https://registry.npmjs.org/${encodeURIComponent(name)}/${encodeURIComponent(version)}`;
            const response = await fetch(source, {
                signal: AbortSignal.timeout(20000),
            });
            if (!response.ok)
                throw new Error(`License metadata is unavailable for ${key}.`);
            const raw = await response.text();
            if (Buffer.byteLength(raw) > 1024 * 1024)
                throw new Error("Oversized license metadata.");
            const metadata: unknown = JSON.parse(raw);
            if (
                !record(metadata) ||
                metadata.name !== name ||
                metadata.version !== version ||
                typeof metadata.license !== "string" ||
                metadata.license === ""
            )
                throw new Error(`Explicit license audit required for ${key}.`);
            packages.push({
                name,
                version,
                license: metadata.license,
                relation: direct.has(key) ? "direct" : "transitive",
                use: browser.has(key)
                    ? "production-dependency-closure"
                    : "build-test-only",
                source,
            });
        }
    }
    await Promise.all(Array.from({ length: 8 }, worker));
    packages.sort(
        (a, b) =>
            a.name.localeCompare(b.name, "en") ||
            a.version.localeCompare(b.version, "en"),
    );
    mkdirSync(join(root, "dependencies"), { recursive: true });
    writeFileSync(
        inventory,
        JSON.stringify(
            {
                schema_version: 1,
                lock_sha256: digest,
                scope: "Complete locked package set, including optional packages for other platforms; registry metadata at exact versions. Node tooling is build/test only.",
                packages,
            },
            null,
            2,
        ) + "\n",
    );
    validateInventory(JSON.parse(readFileSync(inventory, "utf8")));
    writeFileSync(join(root, "THIRD_PARTY_NOTICES.txt"), noticesFor(packages));
    console.log(
        `Audited ${String(packages.length)} exact locked packages, including optional platforms; retained bundled license texts.`,
    );
} else {
    console.error(
        "Usage: node scripts/licenses.ts [--refresh|--refresh-notices]",
    );
    process.exitCode = 2;
}
