/** Exact browser port of urllib.quote(raw, safe="/:@[]!$&'()*+,;="). */
import { codePointLength, WireError } from "../wire/json";
import { pythonIsPrintable } from "../wire/unicode";

const safe = /^[A-Za-z0-9_.~/:@\[\]!$&'()*+,;=-]$/u;
export function uriPath(raw: string): string {
    codePointLength(raw);
    const parts =
        raw === "/" ? [] : raw.slice(1).replace(/\/$/u, "").split("/");
    if (
        !raw.startsWith("/") ||
        raw.startsWith("//") ||
        !pythonIsPrintable(raw) ||
        /[ ?#\\%]/u.test(raw) ||
        parts.some((part) => part === "" || part === "." || part === "..")
    )
        throw new WireError("schema");
    let result = "";
    for (const character of raw) {
        if (safe.test(character)) result += character;
        else
            for (const byte of new TextEncoder().encode(character))
                result +=
                    "%" + byte.toString(16).toUpperCase().padStart(2, "0");
    }
    return result;
}
