/** WEB015/ADR153: bounded editable intent, never protected TOML or installed authority. */
import { repositorySegments } from "../api/identity";
import { serializeRequestJson } from "../api/request";
import { normalizeManagedTags } from "../wire/config-semantics";
import {
    decodeConfigRead,
    decodeEditableConfig,
    decodeEditableRepair,
    decodeEditableStorage,
    decodeEditableSync,
    decodeEditableVerification,
    decodeRepositoryConfig,
    decodeRequestManagedEditRequest,
} from "../wire/generated";
import type {
    ConfigRead,
    EditableConfig,
    RepositoryConfig,
    RequestManagedEditRequest,
} from "../wire/generated";
import {
    codePointLength,
    numberSource,
    parseWireJson,
    WireError,
} from "../wire/json";
import { isRecord, wireInteger, wireObject } from "../wire/runtime";

export const MAX_DRAFT_BYTES = 2 * 1024 * 1024;
export const MAX_DRAFT_EDITS = 256;
const MAX_WORK = 100000;
const JSON_LIMITS = {
    maxBytes: MAX_DRAFT_BYTES,
    maxDepth: 8,
    maxTokens: MAX_WORK * 4,
    maxKeys: MAX_WORK,
    maxNumberCharacters: 128,
};
const REPOSITORY_FIELDS = [
    "id",
    "type",
    "revision",
    "enabled",
    "tags",
    "declared_dependencies",
] as const;
const SETTINGS = [
    {
        table: "storage",
        key: "publication_mode",
        field: "storage.publication_mode",
    },
    {
        table: "storage",
        key: "minimum_free_space_gib",
        field: "storage.minimum_free_space_gib",
    },
    {
        table: "storage",
        key: "minimum_free_space_percent",
        field: "storage.minimum_free_space_percent",
    },
    {
        table: "storage",
        key: "maximum_revisions",
        field: "storage.maximum_revisions",
    },
    { table: "sync", key: "max_workers", field: "sync.max_workers" },
    {
        table: "sync",
        key: "lock_wait_seconds",
        field: "sync.lock_wait_seconds",
    },
    {
        table: "sync",
        key: "continue_on_repository_error",
        field: "sync.continue_on_repository_error",
    },
    {
        table: "sync",
        key: "dependency_policy",
        field: "sync.dependency_policy",
    },
    {
        table: "sync",
        key: "stale_staging_age_hours",
        field: "sync.stale_staging_age_hours",
    },
    {
        table: "verification",
        key: "lock_wait_seconds",
        field: "verification.lock_wait_seconds",
    },
    {
        table: "repair",
        key: "retired_instance_grace_hours",
        field: "repair.retired_instance_grace_hours",
    },
] as const;
export type EditableSettingField = (typeof SETTINGS)[number]["field"];
type Scalar = string | number | boolean;
export type DraftDiffRow =
    | {
          readonly kind: "setting";
          readonly field: EditableSettingField;
          readonly before: Scalar;
          readonly after: Scalar;
      }
    | {
          readonly kind: "repository";
          readonly field: "repositories";
          readonly repositoryType: "model" | "dataset";
          readonly repositoryId: string;
          readonly before: RepositoryConfig | null;
          readonly after: RepositoryConfig | null;
      };
export interface PreparedDraft {
    readonly editable: EditableConfig;
    readonly managed: RequestManagedEditRequest;
    readonly diff: readonly DraftDiffRow[];
    readonly dirty: boolean;
}
export class ConfigurationDraftError extends Error {
    constructor(
        readonly reason:
            "invalid" | "bounds" | "duplicate" | "order" | "missing",
        readonly field: string,
    ) {
        super(
            {
                invalid: "The draft contains an invalid or unsupported value.",
                bounds: "The draft exceeds the supported size or edit limits.",
                duplicate: "A repository identity may appear only once.",
                order: "Existing repositories must retain their order, with new entries appended.",
                missing: "The repository is not configured in this draft.",
            }[reason],
        );
        this.name = "ConfigurationDraftError";
    }
}
function fail(reason: ConfigurationDraftError["reason"], field: string): never {
    throw new ConfigurationDraftError(reason, field);
}
function guarded<T>(field: string, action: () => T): T {
    try {
        return action();
    } catch (error) {
        if (error instanceof ConfigurationDraftError) throw error;
        if (error instanceof WireError && error.reason === "bounds")
            return fail("bounds", field);
        return fail("invalid", field);
    }
}
function childField(parent: string, key: string): string {
    if (parent === "base") return parent;
    if (
        parent === "editable" &&
        ["storage", "sync", "verification", "repair", "repositories"].includes(
            key,
        )
    )
        return key;
    const setting = SETTINGS.find(
        (item) => item.table === parent && item.key === key,
    );
    if (setting !== undefined) return setting.field;
    if (
        /^repositories\.[0-9]+$/u.test(parent) &&
        REPOSITORY_FIELDS.some((field) => field === key)
    )
        return parent + "." + key;
    return parent;
}
/** Charge plain caller data before stringify/decoders can allocate or walk it. */
function bounded(value: unknown, field: string, wireNumbers = false): void {
    const stack = [{ value, field, depth: 0 }];
    let bytes = 0,
        work = 0;
    const charge = (count: number, at: string) => {
        bytes += count;
        if (bytes > MAX_DRAFT_BYTES) fail("bounds", at);
    };
    const text = (source: string, at: string) => {
        if (source.length > MAX_DRAFT_BYTES) fail("bounds", at);
        guarded(at, () => codePointLength(source));
        charge(2, at);
        for (const character of source) {
            const point = character.codePointAt(0) ?? 0;
            charge(
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
                at,
            );
        }
    };
    while (stack.length > 0) {
        const entry = stack.pop();
        if (entry === undefined) break;
        const { value: member, field: at, depth } = entry;
        if (++work > MAX_WORK || depth > 8) fail("bounds", at);
        const number = wireNumbers ? numberSource(member) : undefined;
        if (number !== undefined) {
            guarded(at, () => wireInteger(member, null, null));
            charge(number.length, at);
            continue;
        }
        if (member === null || typeof member === "boolean") {
            charge(String(member).length, at);
            continue;
        }
        if (typeof member === "string") {
            text(member, at);
            continue;
        }
        if (typeof member === "number") {
            if (!Number.isSafeInteger(member)) fail("invalid", at);
            charge(String(member).length, at);
            continue;
        }
        if (Array.isArray(member)) {
            const array: unknown[] = member;
            if (array.length + work + stack.length > MAX_WORK)
                fail("bounds", at);
            if (
                Object.getPrototypeOf(array) !== Array.prototype ||
                Reflect.ownKeys(array).length !== array.length + 1
            )
                fail("invalid", at);
            charge(2 + Math.max(0, array.length - 1), at);
            for (let index = array.length - 1; index >= 0; index--) {
                const descriptor = Object.getOwnPropertyDescriptor(
                    array,
                    String(index),
                );
                if (
                    descriptor === undefined ||
                    descriptor.get !== undefined ||
                    descriptor.set !== undefined ||
                    !descriptor.enumerable
                )
                    fail("invalid", at);
                stack.push({
                    value: array[index],
                    field:
                        at === "repositories" ? at + "." + String(index) : at,
                    depth: depth + 1,
                });
            }
            continue;
        }
        if (!isRecord(member)) fail("invalid", at);
        const keys = Object.keys(member);
        work += keys.length;
        if (work + stack.length > MAX_WORK) fail("bounds", at);
        if (Reflect.ownKeys(member).length !== keys.length) fail("invalid", at);
        charge(2 + Math.max(0, keys.length - 1), at);
        for (const key of keys) {
            const next = childField(at, key);
            const descriptor = Object.getOwnPropertyDescriptor(member, key);
            if (
                descriptor === undefined ||
                descriptor.get !== undefined ||
                descriptor.set !== undefined ||
                key === "toJSON"
            )
                fail("invalid", next);
            text(key, next);
            charge(1, next);
            stack.push({ value: member[key], field: next, depth: depth + 1 });
        }
    }
}
function input(value: unknown): unknown {
    return parseWireJson(serializeRequestJson(value), JSON_LIMITS);
}
const validSettings = {
    storage: {
        publication_mode: "hardlink",
        minimum_free_space_gib: 0,
        minimum_free_space_percent: 0,
        maximum_revisions: 3,
    },
    sync: {
        max_workers: 1,
        lock_wait_seconds: 0,
        continue_on_repository_error: false,
        dependency_policy: "warn",
        stale_staging_age_hours: 1,
    },
    verification: { lock_wait_seconds: 0 },
    repair: { retired_instance_grace_hours: 168 },
};
function repository(value: unknown, field: string): RepositoryConfig {
    const raw = guarded(field, () => wireObject(value, REPOSITORY_FIELDS));
    const tags = guarded(field + ".tags", () => normalizeManagedTags(raw.tags));
    const normalized: Record<string, unknown> = { ...raw, tags };
    const valid = {
        id: "owned/entry",
        type: "model",
        revision: "main",
        enabled: true,
        tags: [],
        declared_dependencies: [],
    };
    try {
        return decodeRepositoryConfig(input(normalized));
    } catch {
        for (const key of REPOSITORY_FIELDS)
            guarded(field + "." + key, () =>
                decodeRepositoryConfig(
                    input({ ...valid, [key]: normalized[key] }),
                ),
            );
        return fail("invalid", field);
    }
}
function editable(value: unknown, wireNumbers = false): EditableConfig {
    bounded(value, "editable", wireNumbers);
    const raw = guarded("editable", () =>
        wireObject(value, [
            "storage",
            "sync",
            "verification",
            "repair",
            "repositories",
        ]),
    );
    for (const table of [
        "storage",
        "sync",
        "verification",
        "repair",
    ] as const) {
        const fields = SETTINGS.filter((item) => item.table === table);
        const section = guarded(table, () =>
            wireObject(
                raw[table],
                fields.map((item) => item.key),
            ),
        );
        for (const spec of fields) {
            const defaults = wireObject(
                input(validSettings[table]),
                fields.map((item) => item.key),
            );
            const candidate = {
                ...defaults,
                [spec.key]: wireNumbers
                    ? section[spec.key]
                    : input(section[spec.key]),
            };
            guarded(spec.field, () => {
                switch (table) {
                    case "storage":
                        return decodeEditableStorage(candidate);
                    case "sync":
                        return decodeEditableSync(candidate);
                    case "verification":
                        return decodeEditableVerification(candidate);
                    case "repair":
                        return decodeEditableRepair(candidate);
                }
            });
        }
    }
    if (!Array.isArray(raw.repositories)) fail("invalid", "repositories");
    const rows: unknown[] = raw.repositories;
    const seen = new Set<string>();
    const repositories = rows.map((row, index) => {
        const at = "repositories." + String(index);
        const checked = repository(row, at);
        const key = repositoryKey(checked);
        if (seen.has(key)) fail("duplicate", at);
        seen.add(key);
        return checked;
    });
    return guarded("editable", () =>
        decodeEditableConfig(
            wireNumbers
                ? { ...raw, repositories }
                : input({ ...raw, repositories }),
        ),
    );
}
function repositoryKey(value: RepositoryConfig): string {
    return value.type + ":" + value.id;
}
function sameRepository(a: RepositoryConfig, b: RepositoryConfig): boolean {
    return (
        a.id === b.id &&
        a.type === b.type &&
        a.revision === b.revision &&
        a.enabled === b.enabled &&
        a.tags.length === b.tags.length &&
        a.tags.every((tag, index) => tag === b.tags[index]) &&
        a.declared_dependencies.length === b.declared_dependencies.length &&
        a.declared_dependencies.every(
            (dependency, index) =>
                dependency === b.declared_dependencies[index],
        )
    );
}
function settingValues(
    value: EditableConfig,
): Readonly<Record<EditableSettingField, Scalar>> {
    return {
        "storage.publication_mode": value.storage.publication_mode,
        "storage.minimum_free_space_gib": value.storage.minimum_free_space_gib,
        "storage.minimum_free_space_percent":
            value.storage.minimum_free_space_percent,
        "storage.maximum_revisions": value.storage.maximum_revisions,
        "sync.max_workers": value.sync.max_workers,
        "sync.lock_wait_seconds": value.sync.lock_wait_seconds,
        "sync.continue_on_repository_error":
            value.sync.continue_on_repository_error,
        "sync.dependency_policy": value.sync.dependency_policy,
        "sync.stale_staging_age_hours": value.sync.stale_staging_age_hours,
        "verification.lock_wait_seconds": value.verification.lock_wait_seconds,
        "repair.retired_instance_grace_hours":
            value.repair.retired_instance_grace_hours,
    };
}
/** Review editable intent only. Full-byte base/candidate authority remains server-side. */
export function prepareDraft(
    base: ConfigRead,
    desired: unknown,
): PreparedDraft {
    bounded(base, "base");
    const original = guarded("base", () => decodeConfigRead(input(base)));
    const next = editable(desired);
    const oldByKey = new Map(
        original.editable.repositories.map((row) => [repositoryKey(row), row]),
    );
    const newByKey = new Map(
        next.repositories.map((row) => [repositoryKey(row), row]),
    );
    const order = original.editable.repositories
        .filter((row) => newByKey.has(repositoryKey(row)))
        .concat(
            next.repositories.filter(
                (row) => !oldByKey.has(repositoryKey(row)),
            ),
        );
    if (
        order.some(
            (row, index) =>
                repositoryKey(row) !==
                repositoryKey(next.repositories[index] ?? row),
        )
    )
        fail("order", "repositories");
    const diff: DraftDiffRow[] = [],
        edits: unknown[] = [];
    const append = (edit: unknown) => {
        if (edits.length >= MAX_DRAFT_EDITS) fail("bounds", "repositories");
        edits.push(edit);
    };
    const before = settingValues(original.editable),
        after = settingValues(next);
    const settings: Record<string, Record<string, Scalar>> = {};
    for (const spec of SETTINGS) {
        if (before[spec.field] === after[spec.field]) continue;
        const section = settings[spec.table] ?? {};
        section[spec.key] = after[spec.field];
        settings[spec.table] = section;
        diff.push(
            Object.freeze({
                kind: "setting",
                field: spec.field,
                before: before[spec.field],
                after: after[spec.field],
            }),
        );
    }
    if (diff.length > 0) append({ kind: "settings-replace", settings });
    const addDiff = (
        previous: RepositoryConfig | null,
        current: RepositoryConfig | null,
    ) => {
        const row = current ?? previous;
        if (row === null) fail("invalid", "repositories");
        diff.push(
            Object.freeze({
                kind: "repository",
                field: "repositories",
                repositoryType: row.type,
                repositoryId: row.id,
                before: previous,
                after: current,
            }),
        );
    };
    for (const previous of original.editable.repositories) {
        const current = newByKey.get(repositoryKey(previous));
        if (current === undefined) {
            append({
                kind: "repository-remove",
                repository_type: previous.type,
                repository_id: previous.id,
            });
            addDiff(previous, null);
        } else if (!sameRepository(previous, current)) {
            append({ kind: "repository-upsert", repository: current });
            addDiff(previous, current);
        }
    }
    for (const current of next.repositories) {
        if (oldByKey.has(repositoryKey(current))) continue;
        append({ kind: "repository-upsert", repository: current });
        addDiff(null, current);
    }
    const body = { base_revision: original.base_revision, edits };
    bounded(body, "editable");
    const managed = guarded("editable", () =>
        decodeRequestManagedEditRequest(input(body)),
    );
    if (diff.length > 267) fail("bounds", "editable");
    return Object.freeze({
        editable: next,
        managed,
        diff: Object.freeze(diff),
        dirty: diff.length > 0,
    });
}
/** Advanced JSON preserves raw number lexemes; only documented tag normalization is applied. */
export function prepareDraftJson(
    base: ConfigRead,
    source: string,
): PreparedDraft {
    if (typeof source !== "string") fail("invalid", "editable");
    if (source.length > MAX_DRAFT_BYTES) fail("bounds", "editable");
    const parsed = guarded("editable", () =>
        parseWireJson(source, JSON_LIMITS),
    );
    return prepareDraft(base, editable(parsed, true));
}
export function defaultRepository(
    type: RepositoryConfig["type"],
    id: string,
): RepositoryConfig {
    const value = {
        id,
        type,
        revision: "main",
        enabled: true,
        tags: [],
        declared_dependencies: [],
    };
    bounded(value, "repositories");
    return repository(value, "repositories");
}
export function upsertRepository(
    value: EditableConfig,
    entry: unknown,
): EditableConfig {
    const current = editable(value);
    bounded(entry, "repositories");
    const checked = repository(entry, "repositories");
    const index = current.repositories.findIndex(
        (row) => repositoryKey(row) === repositoryKey(checked),
    );
    const repositories = [...current.repositories];
    if (index < 0) repositories.push(checked);
    else repositories[index] = checked;
    return editable({ ...current, repositories });
}
export function removeRepository(
    value: EditableConfig,
    type: RepositoryConfig["type"],
    id: string,
): EditableConfig {
    const current = editable(value);
    guarded("repositories", () => repositorySegments(type, id));
    const key = type + ":" + id;
    if (!current.repositories.some((row) => repositoryKey(row) === key))
        fail("missing", "repositories");
    return editable({
        ...current,
        repositories: current.repositories.filter(
            (row) => repositoryKey(row) !== key,
        ),
    });
}
