/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The configuration document as the form editor holds it
 * (docs/configuration.md; docs/cockpit.md §6). Client-side constraints are
 * convenience only — `config validate` in the pipeline is the authority,
 * and the CLI re-validates everything. Pure logic: no cockpit import.
 */

import { parse, stringify } from 'smol-toml';

export interface RepositoryEntry {
    id: string;
    type: 'model' | 'dataset';
    revision: string;
    enabled: boolean;
    declared_dependencies: string[];
    tags?: string[];
}

export type ConfigDocument = Record<string, unknown> & { repositories?: RepositoryEntry[] };

export function parseConfig(text: string): ConfigDocument {
    const document = parse(text) as ConfigDocument;
    if (!Array.isArray(document.repositories))
        document.repositories = [];
    for (const entry of document.repositories) {
        if (entry.tags !== undefined)
            entry.tags = normalizeTags(entry.tags);
    }
    return document;
}

/* Form mode serializes canonically and does not preserve operator comments;
 * the generated header says so, names the writer, and dates the write
 * (docs/cockpit.md §6). */
export function serializeConfig(document: ConfigDocument, writtenAt: Date): string {
    const header =
        '# /etc/hfcache/config.toml — written by the hfcache Cockpit plugin\n' +
        `# ${writtenAt.toISOString()}\n` +
        '# Form mode serializes canonically; operator comments are not preserved\n' +
        '# (docs/cockpit.md §6). Text mode edits the document verbatim.\n\n';
    const canonical = {
        ...document,
        repositories: (document.repositories ?? []).map(entry =>
            entry.tags === undefined ? { ...entry } : { ...entry, tags: normalizeTags(entry.tags) })
    };
    return header + stringify(canonical) + '\n';
}

/* Shared grammar: tests/fixtures/tags.json also drives backend tests (INV-018). */
export function normalizeTags(value: unknown): string[] {
    if (!Array.isArray(value) || value.length > 64)
        throw new Error('Tags must be a list of at most 64 strings');
    const canonical = value.map(raw => {
        if (typeof raw !== 'string' || raw.length > 128)
            throw new Error('Each tag must be a string of at most 128 raw characters');
        const tag = raw.replace(/^ +| +$/g, '').replace(/[A-Z]/g, letter => letter.toLowerCase());
        if (!/^[a-z0-9][a-z0-9._:/-]{0,63}(?![\s\S])/.test(tag))
            throw new Error('Each canonical tag must match [a-z0-9][a-z0-9._:/-]{0,63}');
        return tag;
    });
    return [...new Set(canonical)].sort();
}

export function tagInput(text: string): string[] {
    return text === '' ? [] : text.split(',');
}

export function configuredTagSuggestions(document: ConfigDocument): string[] {
    const tags = new Set<string>();
    for (const entry of document.repositories ?? []) {
        try {
            for (const tag of normalizeTags(entry.tags ?? []))
                tags.add(tag);
        } catch { /* An invalid draft is still editable; the backend rejects it. */ }
    }
    return [...tags].sort().slice(0, 64);
}

export function repositorySelectors(document: ConfigDocument): string[] {
    return (document.repositories ?? []).map(entry => `${entry.type}:${entry.id}`);
}

/* Which repositories a candidate adds or retargets against the installed
 * document — the set the contract's §6 step 3 sizing preview covers. */
export function selectorsNeedingPreview(installed: ConfigDocument, candidate: ConfigDocument): string[] {
    const before = new Map((installed.repositories ?? [])
            .map(entry => [`${entry.type}:${entry.id}`, entry]));
    const need: string[] = [];
    for (const entry of candidate.repositories ?? []) {
        const selector = `${entry.type}:${entry.id}`;
        const previous = before.get(selector);
        // Text-mode TOML preserves omitted fields. Match RepositoryConfig's
        // defaults when deciding whether sizing is required, without editing it.
        if ((entry.enabled ?? true) && (previous === undefined || !(previous.enabled ?? true) ||
            (previous.revision ?? 'main') !== (entry.revision ?? 'main')))
            need.push(selector);
    }
    return need;
}

/* Reference-name grammar from docs/configuration.md §6. */
export function validateRevisionReference(text: string): string | null {
    if (text === '')
        return 'a revision is required (branch, tag, or full 40-character lowercase commit SHA)';
    if (text.length > 255)
        return 'a reference name is at most 255 characters';
    if (!/^[A-Za-z0-9._/-]+$/.test(text))
        return 'a reference name uses only [A-Za-z0-9._/-]';
    if (text.startsWith('/') || text.endsWith('/') || text.includes('//'))
        return 'no leading or trailing "/" and no "//"';
    if (text.includes('..'))
        return 'no ".."';
    if (text.startsWith('-'))
        return 'no leading "-"';
    if (text.endsWith('.lock'))
        return 'no trailing ".lock"';
    if (/^[0-9a-fA-F]{4,39}$/.test(text))
        return 'an abbreviated commit SHA is ambiguous; use the full 40 characters or a reference name';
    return null;
}

export interface FieldSpec {
    table: 'hub' | 'storage' | 'sync' | 'verification' | 'repair';
    key: string;
    kind: 'str' | 'int' | 'bool' | 'enum';
    min?: number;
    max?: number;
    options?: (string | number)[];
    defaultValue?: number;
    hint: string;
}

/* The global tables of docs/configuration.md §3–§5, one row per key. */
export const GLOBAL_FIELDS: FieldSpec[] = [
    { table: 'hub', key: 'endpoint', kind: 'str', hint: 'absolute https:// URL, no path, no trailing /' },
    { table: 'hub', key: 'expected_account', kind: 'str', hint: 'empty = anonymous, no identity check' },
    { table: 'hub', key: 'token_mode', kind: 'enum', options: ['disabled', 'optional', 'required'], hint: 'required = credential mandatory and private/gated scope enabled' },
    { table: 'hub', key: 'credential_name', kind: 'str', hint: 'systemd credential name, [A-Za-z0-9._-]{1,64}' },
    { table: 'storage', key: 'archive_root', kind: 'str', hint: 'absolute path; must be the NFS mount (FS-02)' },
    { table: 'storage', key: 'archive_id', kind: 'str', hint: 'must match .hfcache-root; a mismatch is fatal (FS-03)' },
    { table: 'storage', key: 'publication_mode', kind: 'enum', options: ['hardlink', 'copy'], hint: 'copy doubles stored bytes (AD-11)' },
    { table: 'storage', key: 'minimum_free_space_gib', kind: 'int', min: 0, max: 1048576, hint: 'reserve floor in GiB' },
    { table: 'storage', key: 'minimum_free_space_percent', kind: 'int', min: 0, max: 100, hint: 'reserve floor as percent; the greater wins' },
    { table: 'storage', key: 'maximum_revisions', kind: 'int', options: [3, 5], defaultValue: 3, hint: '3 by default; 5 preserves the original policy (HFCFG011)' },
    { table: 'sync', key: 'max_workers', kind: 'int', min: 1, max: 32, hint: 'download workers' },
    { table: 'sync', key: 'lock_wait_seconds', kind: 'int', min: 0, max: 86400, hint: 'a scheduled sync waits this long for the lock' },
    { table: 'sync', key: 'continue_on_repository_error', kind: 'bool', hint: 'one failure does not abandon the run; exit stays non-zero' },
    { table: 'sync', key: 'dependency_policy', kind: 'enum', options: ['warn'], hint: 'only "warn" in schema version 1' },
    { table: 'sync', key: 'stale_staging_age_hours', kind: 'int', min: 1, max: 8760, hint: 'minimum age before reconciliation acts on staging' },
    { table: 'verification', key: 'algorithm', kind: 'enum', options: ['sha256'], hint: 'only sha256 in schema version 1' },
    { table: 'verification', key: 'hash_new_content', kind: 'bool', hint: 'must remain true (AD-18)' },
    { table: 'verification', key: 'lock_wait_seconds', kind: 'int', min: 0, max: 604800, hint: 'verification waits out a long sync rather than racing it' },
    { table: 'repair', key: 'retired_instance_grace_hours', kind: 'int', min: 168, max: 8760, hint: 'seven-day floor (HFCFG016)' },
];

export function getField(document: ConfigDocument, spec: FieldSpec): unknown {
    const table = document[spec.table];
    if (typeof table !== 'object' || table === null)
        return spec.defaultValue;
    const value = (table as Record<string, unknown>)[spec.key];
    return value === undefined ? spec.defaultValue : value;
}

export function setField(document: ConfigDocument, spec: FieldSpec, value: unknown): ConfigDocument {
    const table = { ...(document[spec.table] as Record<string, unknown> | undefined ?? {}) };
    table[spec.key] = value;
    return { ...document, [spec.table]: table };
}

/* Best-effort mapping of a validation issue to the form field it names:
 * structured context first, then the "[path]" convention in messages.
 * Verbatim messages are always shown as well — this only adds a pointer. */
export function extractFieldPath(issue: { message: string; context?: unknown }): string | null {
    if (typeof issue.context === 'object' && issue.context !== null) {
        const context = issue.context as Record<string, unknown>;
        for (const candidate of [context.location, context.key, context.path, context.field]) {
            if (typeof candidate === 'string' && candidate !== '')
                return candidate;
        }
    }
    const match = /\[([A-Za-z0-9_.[\]-]+)\]/.exec(issue.message);
    return match === null ? null : match[1];
}
