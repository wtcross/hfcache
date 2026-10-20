/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Original operation identities survive tab lifetime. Session storage holds only
 * bounded recovery metadata, never request/result bodies or execution authority.
 */

import { operationEvidence } from './envelope.ts';
import type { Envelope, EnvelopeOutcome } from './envelope.ts';
import type { OperationNotice } from './events.ts';

export const ACTION_ROUTES = Object.freeze({
    'candidate-plan': '/api/v1/plans',
    plan: '/api/v1/plans',
    doctor: '/api/v1/diagnostics',
    'prune-dry-run': '/api/v1/prune-plans',
    'prune-apply': '/api/v1/prunes',
    'recover-dry-run': '/api/v1/recovery-plans',
    'recover-apply': '/api/v1/recoveries',
    repair: '/api/v1/repairs',
    'sync-selected': '/api/v1/syncs',
    'sync-full': '/api/v1/syncs',
    'verify-selected': '/api/v1/verifications',
    'verify-full': '/api/v1/verifications',
} as const);

export type OperationAction = keyof typeof ACTION_ROUTES;
export const OPERATION_ACTIONS = Object.freeze(Object.keys(ACTION_ROUTES) as OperationAction[]);
export type OperationIdentity = Extract<OperationNotice, { kind: 'key' | 'operation' }>;
export const OPERATION_STORAGE_KEY = 'hfcache.operations.v1';
export const MAX_OPERATION_RECORDS = 32;
export const MAX_OPERATION_STORAGE_BYTES = 64 * 1024;

export interface OperationScope {
    host: string;
    profile: string;
    endpoint: string;
    credentialClass: 'rest-writer' | 'rest-reader';
    archiveId: string | null;
    instanceId: string;
    authorityFingerprint: string;
}

export type OperationState = 'prepared' | 'uncertain' | 'accepted' | 'observing' |
    'missing' | 'unavailable' | 'conflict' | 'unverified' | 'terminal';

export interface SafeTerminalSummary {
    command: string;
    exitCode: number;
    outcome: EnvelopeOutcome;
    runId: string;
    code: string | null;
}

export interface OperationRecord {
    schemaVersion: 1;
    action: OperationAction;
    route: typeof ACTION_ROUTES[OperationAction];
    key: string;
    operationId: string | null;
    scope: Readonly<OperationScope>;
    createdAt: number;
    updatedAt: number;
    state: OperationState;
    terminal: Readonly<SafeTerminalSummary> | null;
}

export interface OperationStorage {
    getItem: (key: string) => string | null;
    setItem: (key: string, value: string) => void;
}

export interface OperationRegistryOptions {
    storage: OperationStorage | null;
    keyFactory?: () => string;
    clock?: () => number;
}

export interface OperationSnapshot {
    records: readonly Readonly<OperationRecord>[];
    storage: 'ready' | 'unavailable' | 'corrupt' | 'full';
    error: string | null;
}

type RegistryProblem = 'storage' | 'capacity' | 'blocked' | 'scope' | 'invalid' | 'missing';
const MESSAGES: Record<RegistryProblem, string> = {
    storage: 'Operation recovery storage is unavailable. Preserve existing handles before another submission.',
    capacity: 'Operation recovery storage is full. Unresolved operations are preserved; observe them before another submission.',
    blocked: 'An unresolved operation already exists for this action on this host. Observe its original handles before another submission.',
    scope: 'The original operation authority is unconfirmed or changed. Preserve its handles; observation against this authority is unavailable.',
    invalid: 'Operation recovery metadata is invalid. Preserve the stored evidence for operator review.',
    missing: 'The original operation recovery record is unavailable. No replacement submission was created.',
};

export class OperationRegistryError extends Error {
    readonly reason: RegistryProblem;
    constructor(reason: RegistryProblem) {
        super(MESSAGES[reason]);
        this.name = 'OperationRegistryError';
        this.reason = reason;
    }
}

const COMMANDS: Record<OperationAction, readonly string[]> = {
    'candidate-plan': ['plan'],
    plan: ['plan'],
    doctor: ['doctor'],
    'prune-dry-run': ['prune --dry-run'],
    'prune-apply': ['prune --apply'],
    'recover-dry-run': ['recover --dry-run'],
    'recover-apply': ['recover --apply'],
    repair: ['repair'],
    'sync-selected': ['sync'],
    'sync-full': ['sync'],
    'verify-selected': ['verify --new', 'verify --revision'],
    'verify-full': ['verify --full'],
};
const STATES: readonly OperationState[] = [
    'prepared', 'uncertain', 'accepted', 'observing', 'missing', 'unavailable', 'conflict', 'unverified', 'terminal',
];
const KEY = /^[A-Za-z0-9._~+-]{1,128}$/;
const ID = /^[0-9a-f]{32}$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const CODE = /^(?:HFAPI|HFARG|HFCFG|HFHUB|HFMNT|HFVER|HFSYNC|HFSTO)[0-9]{3}$/;
const EXITS = [0, 10, 20, 30, 40, 50];

function object(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function fields(value: Record<string, unknown>, names: readonly string[]): boolean {
    return Object.keys(value).length === names.length && names.every(name =>
        Object.prototype.hasOwnProperty.call(value, name));
}

function timestamp(value: unknown): value is number {
    return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}

function endpoint(value: unknown): value is string {
    if (typeof value !== 'string' || value.length > 2048 || /\s/.test(value) ||
        Array.from(value).some(character => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127))
        return false;
    if (value.startsWith('unix:')) {
        const path = value.slice(5);
        return /^\/[A-Za-z0-9._/-]+$/.test(path) && !path.includes('//') && !path.endsWith('/') &&
            !path.split('/').some(segment => segment === '.' || segment === '..');
    }
    if ((!value.startsWith('https://') && !value.startsWith('http://')) || /[?#\\]/.test(value))
        return false;
    try {
        const parsed = new URL(value);
        return parsed.username === '' && parsed.password === '' && parsed.search === '' && parsed.hash === '' &&
            (parsed.protocol === 'https:' || (parsed.protocol === 'http:' &&
                ['localhost', '127.0.0.1', '[::1]'].includes(parsed.hostname)));
    } catch { return false }
}

export function validOperationScope(value: unknown): value is OperationScope {
    if (!object(value) || !fields(value, ['host', 'profile', 'endpoint', 'credentialClass', 'archiveId', 'instanceId', 'authorityFingerprint']))
        return false;
    return typeof value.host === 'string' && /^[A-Za-z0-9][A-Za-z0-9._:@+-]{0,254}$/.test(value.host) &&
        typeof value.profile === 'string' && /^[0-9a-f]{64}$/.test(value.profile) && endpoint(value.endpoint) &&
        ['rest-writer', 'rest-reader'].includes(value.credentialClass as string) &&
        (value.archiveId === null || (typeof value.archiveId === 'string' && UUID.test(value.archiveId))) &&
        typeof value.instanceId === 'string' && ID.test(value.instanceId) &&
        typeof value.authorityFingerprint === 'string' && /^[0-9a-f]{64}$/.test(value.authorityFingerprint);
}

export function sameOperationScope(original: OperationScope, current: OperationScope): boolean {
    return validOperationScope(original) && validOperationScope(current) && original.archiveId !== null &&
        original.host === current.host && original.profile === current.profile && original.endpoint === current.endpoint &&
        original.credentialClass === current.credentialClass && original.archiveId === current.archiveId &&
        original.authorityFingerprint === current.authorityFingerprint;
}

function validTerminal(value: unknown, action: OperationAction): value is SafeTerminalSummary {
    if (!object(value) || !fields(value, ['command', 'exitCode', 'outcome', 'runId', 'code']))
        return false;
    return typeof value.command === 'string' && COMMANDS[action].includes(value.command) &&
        EXITS.includes(value.exitCode as number) &&
        (value.exitCode === 0 ? ['success', 'success_with_warnings'].includes(value.outcome as string) : value.outcome === 'failed') &&
        typeof value.runId === 'string' && ID.test(value.runId) &&
        (value.code === null || (typeof value.code === 'string' && CODE.test(value.code)));
}

function validRecord(value: unknown): value is OperationRecord {
    if (!object(value) || !fields(value, ['schemaVersion', 'action', 'route', 'key', 'operationId',
        'scope', 'createdAt', 'updatedAt', 'state', 'terminal']) || value.schemaVersion !== 1 ||
        !OPERATION_ACTIONS.includes(value.action as OperationAction))
        return false;
    const action = value.action as OperationAction;
    return value.route === ACTION_ROUTES[action] && typeof value.key === 'string' && KEY.test(value.key) &&
        (value.operationId === null || (typeof value.operationId === 'string' && ID.test(value.operationId))) &&
        validOperationScope(value.scope) && timestamp(value.createdAt) && timestamp(value.updatedAt) &&
        value.updatedAt >= value.createdAt && STATES.includes(value.state as OperationState) &&
        (value.state === 'terminal' || value.state === 'unverified'
            ? validTerminal(value.terminal, action)
            : value.terminal === null || (['uncertain', 'observing', 'missing', 'unavailable', 'conflict'].includes(value.state as string) &&
                validTerminal(value.terminal, action)));
}

function freezeRecord(record: OperationRecord): Readonly<OperationRecord> {
    return Object.freeze({
        ...record,
        scope: Object.freeze({ ...record.scope }),
        terminal: record.terminal === null ? null : Object.freeze({ ...record.terminal })
    });
}

function encode(records: readonly Readonly<OperationRecord>[]): string {
    return JSON.stringify({ schemaVersion: 1, records });
}

function bytes(value: string): number { return new TextEncoder().encode(value).length }

export function createOperationRegistry(options: OperationRegistryOptions) {
    const listeners = new Set<() => void>();
    const clock = options.clock ?? Date.now;
    const keyFactory = options.keyFactory ?? (() => crypto.randomUUID());
    let writable = false;
    let lastPersisted: string | null = null;
    let snapshot: OperationSnapshot = Object.freeze({ records: Object.freeze([]), storage: 'ready', error: null });
    const publish = (records: readonly Readonly<OperationRecord>[], storage: OperationSnapshot['storage'], error: string | null) => {
        snapshot = Object.freeze({ records: Object.freeze([...records]), storage, error });
        for (const listener of listeners) {
            try { listener() } catch { /* A detached view cannot alter operation observation. */ }
        }
    };
    try {
        if (options.storage === null)
            throw new Error();
        const saved = options.storage.getItem(OPERATION_STORAGE_KEY);
        lastPersisted = saved;
        if (saved !== null) {
            if (bytes(saved) > MAX_OPERATION_STORAGE_BYTES)
                throw new OperationRegistryError('invalid');
            const parsed: unknown = JSON.parse(saved);
            if (!object(parsed) || !fields(parsed, ['schemaVersion', 'records']) || parsed.schemaVersion !== 1 ||
                !Array.isArray(parsed.records) || parsed.records.length > MAX_OPERATION_RECORDS || !parsed.records.every(validRecord) ||
                new Set(parsed.records.map(record => record.key)).size !== parsed.records.length)
                throw new OperationRegistryError('invalid');
            publish(parsed.records.map(record => freezeRecord({
                ...record,
                // Storage is recovery metadata; only authenticated observation
                // in this module lifetime can authorize a resolved state.
                state: record.state === 'prepared' ? 'uncertain' : record.state === 'terminal' ? 'unverified' : record.state
            })), 'ready', null);
        }
        writable = true;
    } catch (error) {
        const invalid = error instanceof SyntaxError || error instanceof OperationRegistryError;
        publish([], invalid ? 'corrupt' : 'unavailable', MESSAGES[invalid ? 'invalid' : 'storage']);
    }
    const now = (): number => {
        const value = clock();
        if (!timestamp(value))
            throw new OperationRegistryError('invalid');
        return value;
    };
    const persist = (records: readonly Readonly<OperationRecord>[]): boolean => {
        if (!writable || options.storage === null) {
            publish(records, snapshot.storage, snapshot.error);
            return false;
        }
        const text = encode(records);
        if (bytes(text) > MAX_OPERATION_STORAGE_BYTES) {
            // A hostile but valid restored record may consume the old byte cap.
            // Keep newly learned identities in memory even if persistence fails.
            publish(records, 'full', MESSAGES.capacity);
            return false;
        }
        try {
            if (options.storage.getItem(OPERATION_STORAGE_KEY) !== lastPersisted) {
                writable = false;
                publish(records, 'corrupt', MESSAGES.invalid);
                return false;
            }
            options.storage.setItem(OPERATION_STORAGE_KEY, text);
            if (options.storage.getItem(OPERATION_STORAGE_KEY) !== text)
                throw new Error();
            lastPersisted = text;
            publish(records, 'ready', null);
            return true;
        } catch {
            publish(records, 'unavailable', MESSAGES.storage);
            return false;
        }
    };
    const find = (key: string): Readonly<OperationRecord> => {
        const record = snapshot.records.find(record => record.key === key);
        if (!record)
            throw new OperationRegistryError('missing');
        return record;
    };
    const update = (record: Readonly<OperationRecord>, patch: Partial<OperationRecord>): Readonly<OperationRecord> => {
        const changed = freezeRecord({ ...record, ...patch, updatedAt: Math.max(record.updatedAt, now()) });
        persist(snapshot.records.map(previous => previous.key === record.key ? changed : previous));
        return changed;
    };
    const canRecover = (record: Readonly<OperationRecord>, scope: OperationScope): boolean =>
        record.state !== 'conflict' && sameOperationScope(record.scope, scope);
    const hasUnresolved = (action: OperationAction, scope: OperationScope): boolean =>
        snapshot.records.some(record => record.action === action && record.scope.host === scope.host && record.state !== 'terminal');
    const identity = (key: string, notice: OperationIdentity): Readonly<OperationRecord> => {
        const record = find(key);
        if (record.state === 'conflict')
            return record;
        if ((notice.kind === 'key' && (!KEY.test(notice.key) || notice.key !== record.key)) ||
            (notice.kind === 'operation' && (!ID.test(notice.operationId) ||
                (record.operationId !== null && notice.operationId !== record.operationId))))
            return update(record, { state: 'conflict' });
        if (notice.kind === 'operation' && record.operationId === null) {
            if (record.terminal !== null)
                return update(record, { state: 'conflict' });
            return update(record, { operationId: notice.operationId, state: 'accepted', terminal: null });
        }
        return record;
    };
    return {
        snapshot: () => snapshot,
        subscribe: (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener) } },
        canRecover,
        hasUnresolved,
        prepare: (action: OperationAction, scope: OperationScope): Readonly<OperationRecord> => {
            if (!OPERATION_ACTIONS.includes(action) || !validOperationScope(scope))
                throw new OperationRegistryError('invalid');
            if (scope.archiveId === null)
                throw new OperationRegistryError('scope');
            if (snapshot.storage === 'corrupt' || snapshot.storage === 'unavailable')
                throw new OperationRegistryError('storage');
            if (hasUnresolved(action, scope))
                throw new OperationRegistryError('blocked');
            let key: unknown;
            try { key = keyFactory() } catch { throw new OperationRegistryError('invalid') }
            if (typeof key !== 'string' || !KEY.test(key) || snapshot.records.some(record => record.key === key))
                throw new OperationRegistryError('invalid');
            const timestamp = now();
            const record = freezeRecord({
                schemaVersion: 1,
                action,
                route: ACTION_ROUTES[action],
                key,
                operationId: null,
                scope,
                createdAt: timestamp,
                updatedAt: timestamp,
                state: 'prepared',
                terminal: null
            });
            let records = [...snapshot.records, record];
            // Only conclusive terminal summaries may leave storage, oldest first,
            // and only when the explicit count/byte capacity requires room.
            while (records.length > MAX_OPERATION_RECORDS || bytes(encode(records)) +
                records.filter(record => record.state !== 'terminal').length * 512 > MAX_OPERATION_STORAGE_BYTES) {
                const oldest = records.filter(record => record.state === 'terminal')
                        .sort((left, right) => left.updatedAt - right.updatedAt)[0];
                if (!oldest) {
                    publish(snapshot.records, 'full', MESSAGES.capacity);
                    throw new OperationRegistryError('capacity');
                }
                records = records.filter(record => record !== oldest);
            }
            if (!persist(records))
                throw new OperationRegistryError('storage');
            return record;
        },
        identity,
        uncertain: (key: string): Readonly<OperationRecord> => {
            const record = find(key);
            return record.state === 'terminal' || record.state === 'conflict' ? record : update(record, { state: 'uncertain' });
        },
        observing: (key: string, scope: OperationScope): Readonly<OperationRecord> => {
            const record = find(key);
            if (!canRecover(record, scope))
                throw new OperationRegistryError('scope');
            return record.state === 'terminal' ? record : update(record, { state: 'observing' });
        },
        lookupState: (key: string, state: 'missing' | 'unavailable'): Readonly<OperationRecord> => {
            const record = find(key);
            if (!['missing', 'unavailable'].includes(state))
                throw new OperationRegistryError('invalid');
            return record.state === 'terminal' || record.state === 'conflict' ? record : update(record, { state });
        },
        complete: (key: string, envelope: Envelope, scope: OperationScope): Readonly<OperationRecord> => {
            let record = find(key);
            if (!sameOperationScope(record.scope, scope))
                throw new OperationRegistryError('scope');
            if (record.state === 'conflict')
                return record;
            const evidence = operationEvidence(envelope);
            if (evidence.idempotencyKey !== undefined)
                record = identity(key, { kind: 'key', key: evidence.idempotencyKey });
            if (evidence.operationId !== undefined)
                record = identity(key, { kind: 'operation', operationId: evidence.operationId });
            if (record.state === 'conflict')
                return record;
            if (evidence.workMayContinue || envelope.errors.some(issue =>
                ['HFAPI013', 'HFAPI015', 'HFAPI018', 'HFAPI019', 'HFAPI020'].includes(issue.code)))
                return update(record, { state: envelope.errors.some(issue => issue.code === 'HFAPI013') ? 'missing' : 'uncertain' });
            const code = envelope.errors.find(issue => CODE.test(issue.code))?.code ?? null;
            const terminal: SafeTerminalSummary = {
                command: envelope.command,
                exitCode: envelope.exit_code,
                outcome: envelope.outcome,
                runId: envelope.run_id,
                code
            };
            if (envelope.schema_version !== 1 || !validTerminal(terminal, record.action) ||
                (envelope.exit_code === 0 && record.operationId === null))
                return update(record, { state: 'conflict' });
            if (record.terminal !== null) {
                const previous = record.terminal;
                if (previous.command !== terminal.command || previous.exitCode !== terminal.exitCode ||
                    previous.outcome !== terminal.outcome || previous.runId !== terminal.runId || previous.code !== terminal.code)
                    return update(record, { state: 'conflict' });
            }
            return record.state === 'terminal' ? record : update(record, { state: 'terminal', terminal });
        },
    };
}

export type OperationRegistry = ReturnType<typeof createOperationRegistry>;
