import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import "./licenses.ts";

const root = fileURLToPath(new URL("../dist/", import.meta.url));
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
