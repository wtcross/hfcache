import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

export function verifyIndex(html: string): void {
    const slots = [
        ["hfcache-ui-base", "__HFCACHE_UI_BASE_V1__"],
        ["hfcache-ui-bootstrap", "__HFCACHE_UI_BOOTSTRAP_V1__"],
        ["hfcache-ui-fingerprint", "__HFCACHE_UI_FINGERPRINT_V1__"],
        ["hfcache-ui-contract", "__HFCACHE_UI_CONTRACT_V1__"],
    ] as const;
    if (
        (html.match(/<base\b/gu) ?? []).length !== 1 ||
        !/<base\s+href="__HFCACHE_UI_BASE_V1__"\s*\/?\s*>/u.test(html)
    )
        throw new Error("Invalid indexed base marker.");
    for (const [name, token] of slots) {
        if (
            html.split(token).length - 1 !==
                (name === "hfcache-ui-base" ? 2 : 1) ||
            (
                html.match(
                    new RegExp(
                        `<meta\\s+name="${name}"\\s+content="${token}"\\s*/?\\s*>`,
                        "gu",
                    ),
                ) ?? []
            ).length !== 1
        )
            throw new Error("Invalid indexed metadata marker.");
    }
    if (
        /<style\b|\son[A-Za-z]+\s*=|\sstyle\s*=|<meta[^>]+http-equiv/iu.test(
            html,
        ) ||
        !/<a href="\.\/">Reload interface<\/a>/u.test(html) ||
        !html.includes('id="root"')
    )
        throw new Error("Missing inert fallback or executable inline HTML.");
    for (const match of html.matchAll(
        /<script\b([^>]*)>([\s\S]*?)<\/script>/gu,
    )) {
        if (
            match[2]?.trim() !== "" ||
            !/^\s+type="module"(?:\s+crossorigin)?\s+src="\.\/assets\/[A-Za-z0-9_.-]+-[A-Za-z0-9_-]{8,64}\.js"\s*$/u.test(
                match[1] ?? "",
            )
        )
            throw new Error("Unindexed executable script.");
    }
    if ((html.match(/<script\b/gu) ?? []).length === 0)
        throw new Error("Missing indexed entry module.");
}

export function verifyBuild(root: string): void {
    let bytes = 0;
    let javascript = 0;
    function check(directory: string) {
        for (const item of readdirSync(directory, { withFileTypes: true })) {
            const path = join(directory, item.name);
            if (item.isDirectory()) check(path);
            else {
                if (
                    !item.isFile() ||
                    item.name.endsWith(".map") ||
                    statSync(path).size > 8 * 1024 * 1024
                )
                    throw new Error("Unsafe build member.");
                const content = readFileSync(path);
                if (item.name === "index.html")
                    verifyIndex(content.toString("utf8"));
                bytes += content.length;
                if (/\.(?:html|js|css)$/u.test(item.name)) {
                    const text = content.toString("utf8");
                    if (
                        /(?:https?:)?\/\/(?:fonts\.|cdn\.|unpkg\.|jsdelivr\.)|hf_[A-Za-z0-9]{16}|Bearer [A-Za-z0-9._~-]{16}|mockServiceWorker|example-lab\/|API ready · demo/u.test(
                            text,
                        )
                    )
                        throw new Error(
                            "Production output contains a prohibited external/mock/credential reference.",
                        );
                    if (item.name.endsWith(".js"))
                        javascript += gzipSync(content).length;
                }
            }
        }
    }
    check(root);
    if (bytes === 0 || bytes > 64 * 1024 * 1024 || javascript > 350 * 1024)
        throw new Error("Build output exceeds its declared budget.");
    console.log(
        `Built static shell: ${String(bytes)} bytes; ${String(javascript)} gzip JavaScript bytes; no prohibited references.`,
    );
}
if (process.argv[1] === fileURLToPath(import.meta.url))
    verifyBuild(fileURLToPath(new URL("../dist/", import.meta.url)));
