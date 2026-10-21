/** Capture explicit build inputs, bundle once, and emit canonical schema1 evidence. */
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import {
    readdirSync,
    readFileSync,
    lstatSync,
    writeFileSync,
    mkdirSync,
    openSync,
    closeSync,
    fstatSync,
    constants,
    readSync,
} from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { build, version as viteVersion } from "vite";
import ts from "typescript";
import { verifyBuild } from "./check-build.ts";

const root = fileURLToPath(new URL("../", import.meta.url));
const repository = dirname(root.replace(/\/$/u, ""));
export function canonicalJson(value: unknown): string {
    function sorted(value: unknown): unknown {
        if (Array.isArray(value)) {
            const array: unknown[] = value;
            return array.map(sorted);
        }
        if (value !== null && typeof value === "object") {
            const result: Record<string, unknown> = {};
            for (const key of Object.keys(value).sort()) {
                const descriptor = Object.getOwnPropertyDescriptor(value, key);
                if (
                    descriptor === undefined ||
                    !Object.hasOwn(descriptor, "value")
                )
                    throw new Error("Non-data canonical input.");
                const child: unknown = descriptor.value;
                Object.defineProperty(result, key, {
                    value: sorted(child),
                    enumerable: true,
                });
            }
            return result;
        }
        if (typeof value === "number" && !Number.isFinite(value))
            throw new Error("Nonfinite canonical input.");
        if (value === undefined) throw new Error("Missing canonical input.");
        return value;
    }
    return JSON.stringify(sorted(value), null, 2) + "\n";
}
export function sha256(value: string | Uint8Array): string {
    return createHash("sha256").update(value).digest("hex");
}
function command(binary: string, args: readonly string[]): string {
    const result = spawnSync(binary, args, {
        cwd: repository,
        encoding: "utf8",
        timeout: 30000,
        maxBuffer: 2 * 1024 * 1024,
    });
    if (
        result.error !== undefined ||
        result.signal !== null ||
        result.status !== 0
    )
        throw new Error("Build authority command failed.");
    return result.stdout.trim();
}
interface InputInventory {
    readonly hashes: Readonly<Record<string, string>>;
    readonly identities: Readonly<Record<string, string>>;
}
function inventory(): InputInventory {
    const paths = [
        "web/.npmrc",
        "web/package.json",
        "web/pnpm-lock.yaml",
        "web/index.html",
        "web/vite.config.ts",
        "web/tsconfig.json",
        "web/tsconfig.node.json",
        "web/dependencies/licenses.json",
        "web/THIRD_PARTY_NOTICES.txt",
    ];
    function walk(path: string) {
        for (const entry of readdirSync(join(repository, path), {
            withFileTypes: true,
        })) {
            const child = path + "/" + entry.name;
            if (entry.isDirectory()) walk(child);
            else if (entry.isFile()) paths.push(child);
            else throw new Error("Build input must be a regular file.");
        }
    }
    walk("web/src");
    walk("web/scripts");
    const result: Record<string, string> = {},
        identities: Record<string, string> = {};
    let bytes = 0;
    for (const path of paths.sort()) {
        const full = join(repository, path),
            fd = openSync(full, constants.O_RDONLY | constants.O_NOFOLLOW);
        try {
            const before = fstatSync(fd, { bigint: true }),
                linked = lstatSync(full, { bigint: true });
            if (
                !before.isFile() ||
                before.size > 8388608n ||
                linked.dev !== before.dev ||
                linked.ino !== before.ino ||
                linked.isSymbolicLink()
            )
                throw new Error("Unsafe build input.");
            const storage = Buffer.alloc(Number(before.size) + 1);
            let length = 0;
            while (length < storage.length) {
                const amount = readSync(
                    fd,
                    storage,
                    length,
                    storage.length - length,
                    null,
                );
                if (amount === 0) break;
                length += amount;
            }
            const body = storage.subarray(0, length),
                after = fstatSync(fd, { bigint: true });
            bytes += body.length;
            const identity = (stat: typeof before) =>
                [
                    stat.dev,
                    stat.ino,
                    stat.mode,
                    stat.size,
                    stat.mtimeNs,
                    stat.ctimeNs,
                ]
                    .map(String)
                    .join(":");
            if (
                identity(before) !== identity(after) ||
                BigInt(body.length) !== before.size ||
                bytes > 67108864
            )
                throw new Error("Build input changed or exceeded bounds.");
            result[path] = sha256(body);
            identities[path] = identity(before);
        } finally {
            closeSync(fd);
        }
    }
    return { hashes: result, identities };
}
export async function buildArtifact(): Promise<void> {
    command(process.execPath, [join(root, "scripts/licenses.ts")]);
    const before = inventory(),
        snapshot = canonicalJson(before.hashes);
    const commit = command("git", ["rev-parse", "HEAD"]);
    if (!/^[0-9a-f]{40}$/u.test(commit))
        throw new Error("Invalid build base commit.");
    const dirty =
        command("git", [
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            ...Object.keys(before.hashes),
        ]).length > 0;
    const application = command(join(repository, ".venv/bin/python"), [
        "-c",
        "from hfcache.reporting import RuntimeVersions; print(RuntimeVersions.measured().application)",
    ]);
    const pnpm = command("pnpm", ["--version"]);
    const toolchain = {
        node: process.versions.node,
        pnpm,
        typescript: ts.version,
        vite: viteVersion,
    };
    const pkg: unknown = JSON.parse(
        readFileSync(join(root, "package.json"), "utf8"),
    );
    if (
        typeof pkg !== "object" ||
        pkg === null ||
        !("engines" in pkg) ||
        !("devDependencies" in pkg)
    )
        throw new Error("Missing pinned toolchain.");
    const engines = pkg.engines,
        dev = pkg.devDependencies;
    if (
        typeof engines !== "object" ||
        engines === null ||
        !("node" in engines) ||
        !("pnpm" in engines) ||
        engines.node !== toolchain.node ||
        engines.pnpm !== pnpm ||
        typeof dev !== "object" ||
        dev === null ||
        !("typescript" in dev) ||
        !("vite" in dev) ||
        dev.typescript !== ts.version ||
        dev.vite !== viteVersion
    )
        throw new Error("Installed build tools differ from pins.");
    const ir: unknown = JSON.parse(
        readFileSync(join(root, "src/wire/contracts.json"), "utf8"),
    );
    if (
        typeof ir !== "object" ||
        ir === null ||
        !("source_digest" in ir) ||
        typeof ir.source_digest !== "string" ||
        !/^[0-9a-f]{64}$/u.test(ir.source_digest)
    )
        throw new Error("Missing audited wire identity.");
    const sourceDigest = sha256(snapshot);
    await build({
        root,
        define: {
            __HFCACHE_BUILD_SOURCE__: JSON.stringify(sourceDigest),
            __HFCACHE_APPLICATION_VERSION__: JSON.stringify(application),
        },
    });
    const dist = join(root, "dist");
    writeFileSync(
        join(dist, "licenses.json"),
        readFileSync(join(root, "dependencies/licenses.json")),
    );
    writeFileSync(
        join(dist, "THIRD_PARTY_NOTICES.txt"),
        readFileSync(join(root, "THIRD_PARTY_NOTICES.txt")),
    );
    const members: {
        path: string;
        bytes: number;
        sha256: string;
        mime: string;
    }[] = [];
    const mime: Readonly<Record<string, string>> = {
        html: "text/html",
        js: "text/javascript",
        css: "text/css",
        json: "application/json",
        png: "image/png",
        webp: "image/webp",
        woff2: "font/woff2",
    };
    function capture(directory: string) {
        for (const entry of readdirSync(directory, { withFileTypes: true })) {
            const path = join(directory, entry.name);
            if (entry.isDirectory()) capture(path);
            else {
                if (!entry.isFile())
                    throw new Error("Nonregular build output.");
                const name = relative(dist, path),
                    body = readFileSync(path);
                const type =
                    name === "THIRD_PARTY_NOTICES.txt"
                        ? "text/plain"
                        : mime[name.split(".").at(-1) ?? ""];
                if (type === undefined)
                    throw new Error("Unsupported build member.");
                members.push({
                    path: name,
                    bytes: body.length,
                    sha256: sha256(body),
                    mime: type,
                });
            }
        }
    }
    capture(dist);
    members.sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
    const manifest = {
        schema_version: 1,
        kind: "hfcache_web_assets",
        entrypoint: "index.html",
        meta_identity: {
            ui_base: "__HFCACHE_UI_BASE_V1__",
            bootstrap_path: "__HFCACHE_UI_BOOTSTRAP_V1__",
            asset_fingerprint: "__HFCACHE_UI_FINGERPRINT_V1__",
            ui_contract: "__HFCACHE_UI_CONTRACT_V1__",
        },
        build: {
            application_version: application,
            source_commit: commit,
            source_snapshot_sha256: sourceDigest,
            source_dirty: dirty,
            ui_contract_version: 1,
            rest_api_schema_version: 1,
            wire_source_digest: ir.source_digest,
            pnpm_lock_sha256: sha256(
                readFileSync(join(root, "pnpm-lock.yaml")),
            ),
            toolchain,
            toolchain_sha256: sha256(canonicalJson(toolchain)),
            licenses_sha256: sha256(readFileSync(join(dist, "licenses.json"))),
            notices_sha256: sha256(
                readFileSync(join(dist, "THIRD_PARTY_NOTICES.txt")),
            ),
        },
        members,
    };
    const bytes = canonicalJson(manifest);
    const validation = spawnSync(
        join(repository, ".venv/bin/python"),
        [
            "-c",
            "import sys; from hfcache.ui_models import UiAssetManifest; from hfcache.models import dump; raw=sys.stdin.buffer.read(); m=UiAssetManifest.model_validate_json(raw); assert dump(m)==raw",
        ],
        {
            cwd: repository,
            encoding: "utf8",
            input: bytes,
            timeout: 30000,
            maxBuffer: 1024 * 1024,
        },
    );
    if (
        validation.error !== undefined ||
        validation.signal !== null ||
        validation.status !== 0
    )
        throw new Error("Original Python UI authority refused manifest.");
    if (
        Buffer.byteLength(bytes) > 2097152 ||
        canonicalJson(inventory()) !== canonicalJson(before)
    )
        throw new Error("Build inputs changed or manifest exceeded bound.");
    writeFileSync(join(dist, "manifest.json"), bytes);
    const evidence = join(
        root,
        ".artifacts",
        `build-${Date.now().toString()}-${process.pid.toString()}`,
    );
    mkdirSync(evidence, { recursive: true });
    writeFileSync(join(evidence, "source-inputs.json"), snapshot);
    writeFileSync(
        join(evidence, "identity.json"),
        canonicalJson({
            manifest_sha256: sha256(bytes),
            source_snapshot_sha256: sourceDigest,
            source_commit: commit,
            source_dirty: dirty,
            toolchain,
        }),
    );
    verifyBuild(dist);
    console.log(
        `UI artifact manifest SHA256 ${sha256(bytes)}; source ${sourceDigest}; dirty ${String(dirty)}.`,
    );
}
if (process.argv[1] === fileURLToPath(import.meta.url)) await buildArtifact();
