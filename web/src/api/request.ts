/** Explicit canonical request builders; response decoders never insert defaults. */
import { canonicalHex, repositorySegments } from "./identity";
import { codePointLength, parseWireJson, WireError } from "../wire/json";
import { isRecord } from "../wire/runtime";
import { compareCodePoints } from "../wire/semantics";
import { normalizeManagedTags } from "../wire/config-semantics";

/** Validate ordinary caller values before JSON.stringify can normalize them. */
export function serializeRequestJson(value: unknown): string {
    let nodes = 0,
        keys = 0,
        bytes = 0;
    function chargeCount(count: number): void {
        bytes += count;
        if (bytes > 16 * 1024 * 1024) throw new WireError("bounds");
    }
    function charge(value: string): void {
        chargeCount(value.length);
    }
    function chargeString(value: string): void {
        codePointLength(value);
        chargeCount(2);
        for (const character of value) {
            const point = character.codePointAt(0);
            if (point === undefined) throw new WireError("unicode");
            chargeCount(
                point < 32
                    ? [8, 9, 10, 12, 13].includes(point)
                        ? 2
                        : 6
                    : point === 34 || point === 92
                      ? 2
                      : point < 128
                        ? 1
                        : point < 2048
                          ? 2
                          : point < 65536
                            ? 3
                            : 4,
            );
        }
    }
    function validate(member: unknown, depth: number): void {
        if (++nodes > 1000000 || depth > 32) throw new WireError("bounds");
        if (member === null || typeof member === "boolean") {
            charge(String(member));
            return;
        }
        if (typeof member === "string") {
            if (member.length > 16 * 1024 * 1024) throw new WireError("bounds");
            chargeString(member);
            return;
        }
        if (typeof member === "number") {
            if (
                !Number.isFinite(member) ||
                (Number.isInteger(member) && !Number.isSafeInteger(member))
            )
                throw new WireError("unsafe_number");
            charge(String(member));
            return;
        }
        if (Array.isArray(member)) {
            const entries: unknown[] = member;
            chargeCount(entries.length + 2);
            if (Reflect.ownKeys(member).length !== member.length + 1)
                throw new WireError("schema");
            for (let index = 0; index < entries.length; index++) {
                const descriptor = Object.getOwnPropertyDescriptor(
                    member,
                    String(index),
                );
                if (
                    descriptor === undefined ||
                    descriptor.get !== undefined ||
                    descriptor.set !== undefined ||
                    descriptor.enumerable !== true
                )
                    throw new WireError("schema");
                validate(entries[index], depth + 1);
            }
            return;
        }
        if (!isRecord(member)) throw new WireError("schema");
        const names = Object.keys(member);
        chargeCount(names.length + 2);
        keys += names.length;
        if (keys > 100000) throw new WireError("bounds");
        if (Reflect.ownKeys(member).length !== names.length)
            throw new WireError("schema");
        for (const name of names) {
            chargeString(name);
            charge(":");
            const descriptor = Object.getOwnPropertyDescriptor(member, name);
            if (
                descriptor === undefined ||
                descriptor.get !== undefined ||
                descriptor.set !== undefined ||
                name === "toJSON"
            )
                throw new WireError("schema");
            validate(member[name], depth + 1);
        }
    }
    validate(value, 0);
    const result: unknown = JSON.stringify(value);
    if (
        typeof result !== "string" ||
        new TextEncoder().encode(result).length > 16 * 1024 * 1024
    )
        throw new WireError("bounds");
    return result;
}

function selected(value: unknown, stripRevision: boolean): string {
    if (typeof value !== "string") throw new WireError("schema");
    const colon = value.indexOf(":"),
        at = value.indexOf("@"),
        type = value.slice(0, colon);
    const repository = value.slice(colon + 1, at < 0 ? undefined : at);
    if (colon < 1) throw new WireError("schema");
    repositorySegments(type, repository);
    if (at >= 0 && (!stripRevision || !canonicalHex(value.slice(at + 1), 40)))
        throw new WireError("schema");
    return type + ":" + repository;
}
export function buildRequestInput(route: string, value: unknown): unknown {
    const text = serializeRequestJson(value);
    const raw = parseWireJson(text);
    if (!isRecord(raw)) throw new WireError("schema");
    if (
        [
            "/api/v1/plans",
            "/api/v1/config/validate",
            "/api/v1/config/applications",
        ].includes(route) &&
        isRecord(raw.managed) &&
        Array.isArray(raw.managed.edits)
    ) {
        const edits: readonly unknown[] = raw.managed.edits;
        return {
            ...raw,
            managed: {
                ...raw.managed,
                edits: edits.map((edit) => {
                    if (
                        !isRecord(edit) ||
                        edit.kind !== "repository-upsert" ||
                        !isRecord(edit.repository) ||
                        !Object.hasOwn(edit.repository, "tags")
                    )
                        return edit;
                    return {
                        ...edit,
                        repository: {
                            ...edit.repository,
                            tags: normalizeManagedTags(edit.repository.tags),
                        },
                    };
                }),
            },
        };
    }
    if (Object.hasOwn(raw, "selectors") && Array.isArray(raw.selectors)) {
        const strip = ["/api/v1/syncs", "/api/v1/plans"].includes(route);
        const selectors: readonly unknown[] = raw.selectors;
        const normalized = [
            ...new Set(selectors.map((entry) => selected(entry, strip))),
        ].sort(compareCodePoints);
        return { ...raw, selectors: normalized };
    }
    if (
        route.startsWith("/api/v1/quarantine-") &&
        Array.isArray(raw.transaction_ids)
    ) {
        const entries: readonly unknown[] = raw.transaction_ids;
        const ids = entries.map((entry) => {
            if (typeof entry !== "string" || !canonicalHex(entry, 32))
                throw new WireError("schema");
            return entry;
        });
        return {
            ...raw,
            transaction_ids: [...new Set(ids)].sort(compareCodePoints),
        };
    }
    return raw;
}
