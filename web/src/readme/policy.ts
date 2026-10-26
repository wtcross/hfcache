/** ADR155: finite pre-parser work and navigation without upstream DOM authority. */
import { publicationIdentity, repositorySegments } from "../api/identity";
import type { ExactPublication } from "../api/identity";
import { codePointLength, WireError } from "../wire/json";
import { wireObject } from "../wire/runtime";

type Admission =
    | { readonly allowed: true }
    | {
          readonly allowed: false;
          readonly reason: string;
      };
const MAX_BYTES = 64 * 1024;
const delimiters = new Set("\\`~*_[](){}<>!|#+-=.");
const closers: Readonly<Record<string, string>> = {
    "]": "[",
    ")": "(",
    "}": "{",
};
const utf8 = new TextEncoder();

function refuse(reason: string): Admission {
    return { allowed: false, reason };
}

function quotePrefix(line: string): { depth: number; content: string } {
    let cursor = 0,
        end = 0,
        depth = 0;
    while (cursor < line.length) {
        let spaces = 0;
        while (line[cursor] === " " && spaces < 3) {
            cursor++;
            spaces++;
        }
        if (line[cursor] !== ">") break;
        cursor++;
        depth++;
        if (line[cursor] === " ") cursor++;
        end = cursor;
    }
    return { depth, content: line.slice(end) };
}

/** Count potential GFM cells conservatively, including a single-column row. */
function rowCells(line: string): { count: number; separator: boolean } {
    const cells: string[] = [];
    let start = 0,
        escaped = false;
    for (let index = 0; index < line.length; index++) {
        const char = line[index];
        if (char === "|" && !escaped) {
            cells.push(line.slice(start, index));
            start = index + 1;
        }
        escaped = char === "\\" && !escaped;
    }
    cells.push(line.slice(start));
    if (cells.length > 1 && cells[0]?.trim() === "") cells.shift();
    if (cells.length > 1 && cells.at(-1)?.trim() === "") cells.pop();
    return {
        count: line.trim() === "" ? 0 : cells.length,
        separator:
            cells.length > 0 &&
            cells.every((cell) => /^\s*:?-+:?\s*$/u.test(cell)),
    };
}

/** A conservative lexical admission pass, not a second Markdown interpreter. */
export function readmeAdmission(source: string): Admission {
    if (typeof source !== "string") return refuse("invalid_source");
    // UTF-16 length is a cheap lower bound before allocating encoded bytes.
    if (source.length > MAX_BYTES) return refuse("input_bytes");
    try {
        codePointLength(source);
    } catch {
        return refuse("invalid_source");
    }
    if (utf8.encode(source).length > MAX_BYTES) return refuse("input_bytes");
    const chunks = source.split(/(\r\n|[\r\n])/u);
    if ((chunks.length + 1) / 2 > 2048) return refuse("lines");
    let structural = 0,
        blocks = 0,
        cells = 0,
        previousCells = 0,
        tableColumns = 0;
    let table = false,
        previousText = false,
        indentedBytes = 0;
    let fence: { marker: string; length: number; bytes: number } | null = null;
    const brackets: string[] = [];
    for (let lineIndex = 0; lineIndex < chunks.length; lineIndex += 2) {
        const line = chunks[lineIndex] ?? "";
        const endingBytes = chunks[lineIndex + 1]?.length ?? 0;
        if (codePointLength(line) > 4096) return refuse("line_length");
        for (const char of line) {
            if (delimiters.has(char) && ++structural > 4096)
                return refuse("delimiters");
        }
        const { depth, content } = quotePrefix(line);
        if (fence !== null) {
            const close = /^ {0,3}(`{3,}|~{3,})[ \t]*$/u.exec(content)?.[1];
            if (close?.[0] === fence.marker && close.length >= fence.length)
                fence = null;
            else {
                fence.bytes += utf8.encode(line).length + endingBytes;
                if (fence.bytes > 16 * 1024) return refuse("code_block");
            }
            previousCells = 0;
            table = false;
            previousText = false;
            continue;
        }
        let indentation = 0;
        for (const char of content) {
            if (char === " ") indentation++;
            else if (char === "\t") indentation += 4 - (indentation % 4);
            else break;
        }
        const list = /^\s*(?:[-+*]|[0-9]{1,9}[.)])[ \t]+/u.test(content);
        if (depth + Math.floor(indentation / 2) + (list ? 1 : 0) > 8)
            return refuse("nesting");
        const opening =
            /^ {0,3}(?:(?:[-+*]|[0-9]{1,9}[.)])[ \t]{1,4})?(`{3,}|~{3,})([^\r\n]*)$/u.exec(
                content,
            );
        const marker = opening?.[1];
        if (
            marker !== undefined &&
            !(marker[0] === "`" && opening?.[2]?.includes("`"))
        ) {
            if (++blocks > 128) return refuse("blocks");
            fence = {
                marker: marker[0] ?? "",
                length: marker.length,
                bytes: 0,
            };
            indentedBytes = 0;
            previousCells = 0;
            table = false;
            previousText = false;
            continue;
        }
        if (indentation >= 4 || (line.trim() === "" && indentedBytes > 0)) {
            indentedBytes += utf8.encode(line).length + endingBytes;
            if (indentedBytes > 16 * 1024) return refuse("code_block");
        } else indentedBytes = 0;
        let escaped = false;
        for (const char of content) {
            if (!escaped) {
                if ("[({".includes(char)) brackets.push(char);
                else if (closers[char] === brackets.at(-1)) brackets.pop();
                if (depth + Math.floor(indentation / 2) + brackets.length > 8)
                    return refuse("nesting");
            }
            escaped = char === "\\" && !escaped;
        }
        const row = rowCells(content);
        if (!table && row.separator && previousCells > 0) {
            table = true;
            tableColumns = Math.max(previousCells, row.count);
            cells += tableColumns;
        } else if (table && row.count > 0)
            cells += Math.max(tableColumns, row.count);
        else table = false;
        if (cells > 256) return refuse("table_cells");
        if (
            /^ {0,3}#{1,6}(?:[ \t]|$)/u.test(content) ||
            (previousText && /^ {0,3}(?:=+|-+)[ \t]*$/u.test(content) && !table)
        ) {
            if (++blocks > 128) return refuse("blocks");
        }
        previousCells = row.count;
        previousText = content.trim() !== "";
    }
    return { allowed: true };
}

function identityValue(input: ExactPublication): ExactPublication {
    const value = wireObject(input, [
        "repositoryType",
        "repositoryId",
        "commitSha",
        "publicationId",
    ]);
    if (
        (value.repositoryType !== "model" &&
            value.repositoryType !== "dataset") ||
        typeof value.repositoryId !== "string" ||
        typeof value.commitSha !== "string" ||
        typeof value.publicationId !== "string"
    ) {
        throw new WireError("schema");
    }
    const identity: ExactPublication = {
        repositoryType: value.repositoryType,
        repositoryId: value.repositoryId,
        commitSha: value.commitSha,
        publicationId: value.publicationId,
    };
    publicationIdentity(identity);
    return identity;
}

/** The renderer appends an ordinal; no upstream heading text or ID enters this prefix. */
export function readmeIdPrefix(identity: ExactPublication): string {
    const checked = identityValue(identity);
    const [namespace, name] = repositorySegments(
        checked.repositoryType,
        checked.repositoryId,
    );
    return `readme-${checked.repositoryType}-${String(namespace.length)}-${namespace}-${String(name.length)}-${name}-${checked.commitSha}-${checked.publicationId}-`;
}

function unsafeTarget(value: string): boolean {
    return (
        /[\p{Cc}\p{Cf}\p{Zl}\p{Zp}\\<>"`]/u.test(value) ||
        value.trim() !== value ||
        /&(?:#[xX][0-9a-fA-F]+;?|#[0-9]+;?|[A-Za-z][A-Za-z0-9]+;)/u.test(value)
    );
}

/** All relative navigation leaves the management origin for the exact upstream commit. */
export function readmeLink(
    destination: string,
    identity: ExactPublication,
    managementOrigin?: string,
): string | null {
    try {
        const checked = identityValue(identity);
        let blockedOrigin: string | null = null;
        if (managementOrigin !== undefined) {
            const context = new URL(managementOrigin);
            if (
                !["http:", "https:"].includes(context.protocol) ||
                context.hostname === "" ||
                context.username !== "" ||
                context.password !== "" ||
                context.pathname !== "/" ||
                context.search !== "" ||
                context.hash !== ""
            )
                return null;
            blockedOrigin = context.origin;
        }
        if (typeof destination !== "string" || destination.length > 4096)
            return null;
        codePointLength(destination);
        if (utf8.encode(destination).length > 4096 || unsafeTarget(destination))
            return null;
        // Decode once only for validation/normalization. Encoded separators,
        // controls, schemes and further percent layers are deliberately refused.
        for (const match of destination.matchAll(/%([0-9a-fA-F]{2})/gu)) {
            const byte = Number.parseInt(match[1] ?? "", 16);
            if (
                byte < 32 ||
                byte === 127 ||
                "%:/\\?#@".includes(String.fromCharCode(byte))
            )
                return null;
        }
        const decoded = decodeURIComponent(destination);
        if (unsafeTarget(decoded) || decoded.startsWith("//")) return null;
        const scheme = /^[A-Za-z][A-Za-z0-9+.-]*:/u.exec(decoded)?.[0];
        if (scheme !== undefined) {
            if (!/^https?:\/\/[^/]/iu.test(decoded)) return null;
            const url = new URL(destination);
            if (
                !["http:", "https:"].includes(url.protocol) ||
                url.hostname === "" ||
                url.username !== "" ||
                url.password !== "" ||
                url.origin === blockedOrigin
            )
                return null;
            return url.href;
        }
        if (/^[^/?#]*:/u.test(decoded)) return null;
        const suffixAt = decoded.search(/[?#]/u);
        const path = suffixAt < 0 ? decoded : decoded.slice(0, suffixAt);
        const originalSuffixAt = destination.search(/[?#]/u);
        const suffix =
            originalSuffixAt < 0 ? "" : destination.slice(originalSuffixAt);
        if (path.includes("//")) return null;
        const segments: string[] = [];
        for (const segment of path.split("/")) {
            if (segment === "" || segment === ".") continue;
            if (segment === "..") {
                if (segments.length === 0) return null;
                segments.pop();
            } else segments.push(segment);
        }
        const [namespace, name] = repositorySegments(
            checked.repositoryType,
            checked.repositoryId,
        );
        const upstream =
            "https://huggingface.co/" +
            (checked.repositoryType === "dataset" ? "datasets/" : "") +
            namespace +
            "/" +
            name +
            "/blob/" +
            checked.commitSha +
            "/";
        let relative =
            path === ""
                ? "README.md"
                : segments.map(encodeURIComponent).join("/");
        if (
            relative !== "" &&
            (path.endsWith("/") || /(?:^|\/)\.{1,2}$/u.test(path))
        )
            relative += "/";
        const url = new URL(upstream + relative + suffix);
        return url.origin === blockedOrigin ? null : url.href;
    } catch {
        return null;
    }
}
