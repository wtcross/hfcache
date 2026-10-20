/* SPDX-License-Identifier: LGPL-2.1-or-later
 * One original-key registry outside tab lifetimes; no replay or cancellation.
 */
import cockpit from 'cockpit';

import { assertSession, captureSession } from './connection';
import { HFCACHE_API_SOCKET } from '../lib/command';
import type { ClientCommandOptions } from '../lib/command';
import { Envelope } from '../lib/envelope';
import { normalizeFailure } from '../lib/failure';
import { OperationAuthorityError, operationAuthority } from '../lib/operation-authority';
import {
    createOperationRegistry, OperationRegistryError, sameOperationScope,
} from '../lib/operation-registry';
import type { OperationAction, OperationRecord, OperationScope, OperationStorage } from '../lib/operation-registry';
import { HfcacheSpawnError } from '../lib/runner';
import type { ObservationOptions } from '../lib/runner';

function storage(): OperationStorage | null {
    try { return window.sessionStorage } catch { return null }
}

export const operationRegistry = createOperationRegistry({ storage: storage() });
export type ClientObserver = (command: string[], options?: ObservationOptions & ClientCommandOptions) => Promise<Envelope>;
export interface OperationRunOptions extends ObservationOptions, ClientCommandOptions {
    requiredScope?: Readonly<OperationScope>;
}

export interface OperationView {
    busy: boolean;
    envelope: Envelope | null;
    error: Error | null;
}

export interface AuthorityView {
    scope: Readonly<OperationScope> | null;
    error: Error | null;
    loading: boolean;
    generation: number;
}

interface OperationViews {
    authority: AuthorityView;
    records: ReadonlyMap<string, OperationView>;
    preparingHosts: ReadonlySet<string>;
}

let views: OperationViews = {
    authority: { scope: null, error: null, loading: false, generation: -1 },
    records: new Map(),
    preparingHosts: new Set(),
};
const listeners = new Set<() => void>();
let authorityRequest = 0;
const publish = (patch: Partial<OperationViews>) => {
    views = { ...views, ...patch };
    for (const listener of listeners)
        listener();
};
function view(key: string, patch: Partial<OperationView>): void {
    const records = new Map(views.records);
    records.set(key, { busy: false, envelope: null, error: null, ...records.get(key), ...patch });
    const retained = new Set(operationRegistry.snapshot().records.map(record => record.key));
    for (const existing of records.keys()) {
        if (!retained.has(existing))
            records.delete(existing);
    }
    publish({ records });
}

export const operationViews = () => views;
export const subscribeOperationViews = (listener: () => void) => {
    listeners.add(listener);
    return () => { listeners.delete(listener) };
};
export const currentOperationHost = (): string => cockpit.transport.host;

export function submissionBlocked(): boolean {
    const host = currentOperationHost();
    return views.preparingHosts.has(host) || operationRegistry.snapshot().storage !== 'ready' ||
        operationRegistry.snapshot().records.some(record => record.scope.host === host && record.state !== 'terminal');
}

/* Always refresh immediately before an effect/handle lookup. The same-process
 * CLI pin then closes the gap between this inspection and that invocation. */
export async function readOperationAuthority(observe: ClientObserver): Promise<Readonly<OperationScope>> {
    const request = ++authorityRequest;
    const generation = captureSession('api-read');
    const host = currentOperationHost();
    publish({ authority: { scope: null, error: null, loading: true, generation } });
    try {
        const envelope = await observe(['client', 'describe'], { stage: 'api-read' });
        assertSession(generation, 'api-read');
        if (currentOperationHost() !== host)
            throw new OperationAuthorityError('changed');
        const scope = operationAuthority(envelope, host);
        if (scope.endpoint !== 'unix:' + HFCACHE_API_SOCKET)
            throw new OperationAuthorityError('changed');
        if (request === authorityRequest)
            publish({ authority: { scope, error: null, loading: false, generation } });
        return scope;
    } catch (error) {
        if (request === authorityRequest)
            publish({ authority: { scope: null, error: error as Error, loading: false, generation } });
        throw error;
    }
}

export function keyedAction(command: string[], candidate: boolean): OperationAction | null {
    switch (command[0]) {
    case 'plan': return candidate ? 'candidate-plan' : 'plan';
    case 'doctor': return 'doctor';
    case 'prune': return command.includes('--apply') ? 'prune-apply' : 'prune-dry-run';
    case 'recover': return command.includes('--apply') ? 'recover-apply' : 'recover-dry-run';
    case 'repair': return 'repair';
    case 'sync': return command.length === 1 ? 'sync-full' : 'sync-selected';
    case 'verify':
        return command.includes('--estimate') ? null : command.includes('--full') ? 'verify-full' : 'verify-selected';
    default: return null;
    }
}

export async function submitOperation(command: string[], options: OperationRunOptions,
    action: OperationAction, observe: ClientObserver): Promise<Envelope> {
    const host = currentOperationHost();
    if (submissionBlocked())
        throw new OperationRegistryError('blocked');
    const preparing = new Set(views.preparingHosts);
    preparing.add(host);
    publish({ preparingHosts: preparing });
    let record: Readonly<OperationRecord> | null = null;
    try {
        const generation = captureSession('operation-observe');
        const scope = await readOperationAuthority(observe);
        if (scope.archiveId === null)
            throw new OperationAuthorityError('unknown-archive');
        if (options.requiredScope && !sameOperationScope(options.requiredScope, scope))
            throw new OperationAuthorityError('changed');
        assertSession(generation, 'operation-observe');
        if (host !== currentOperationHost() || operationRegistry.snapshot().records.some(item =>
            item.scope.host === host && item.state !== 'terminal'))
            throw new OperationRegistryError('blocked');
        record = operationRegistry.prepare(action, scope);
        const original = record;
        view(original.key, { busy: true });
        if (!options.signal?.aborted) {
            try { options.onNotice?.({ kind: 'key', key: original.key }) } catch { /* Retain the persisted original. */ }
        }
        const result = await observe(command, {
            ...options,
            idempotencyKey: original.key,
            expectedClientScope: scope.authorityFingerprint,
            expectedKey: original.key,
            onIdentity: notice => { operationRegistry.identity(original.key, notice) },
        });
        const completed = operationRegistry.complete(original.key, result, scope);
        view(original.key, { envelope: result });
        if (completed.state === 'conflict' || (result.exit_code === 0 && completed.state !== 'terminal'))
            throw new HfcacheSpawnError('', '', original.key, completed.operationId ?? undefined,
                                        { stage: 'operation-observe', reason: 'invalid-envelope', workMayContinue: true },
                                        undefined, { identityConflict: completed.state === 'conflict', envelope: result });
        return result;
    } catch (error) {
        if (record !== null) {
            operationRegistry.uncertain(record.key);
            view(record.key, { error: error as Error });
        }
        if (record === null && error instanceof OperationAuthorityError && error.envelope?.exit_code !== 0 && error.envelope)
            return error.envelope;
        throw error;
    } finally {
        if (record !== null)
            view(record.key, { busy: false });
        const remaining = new Set(views.preparingHosts);
        remaining.delete(host);
        publish({ preparingHosts: remaining });
    }
}

export async function observeOriginal(key: string, mode: 'lookup' | 'wait', observe: ClientObserver): Promise<Envelope> {
    const original = operationRegistry.snapshot().records.find(record => record.key === key);
    if (!original || views.records.get(key)?.busy)
        throw new OperationRegistryError('missing');
    view(key, { busy: true, error: null });
    try {
        const scope = await readOperationAuthority(observe);
        operationRegistry.observing(key, scope);
        if (mode === 'wait' && original.operationId === null)
            throw new OperationRegistryError('missing');
        const result = await observe(['operations', mode, '--', mode === 'lookup' ? original.key : original.operationId!], {
            stage: mode === 'lookup' ? 'operation-lookup' : 'operation-wait',
            expectedClientScope: original.scope.authorityFingerprint,
            onIdentity: notice => { operationRegistry.identity(key, notice) },
        });
        if (mode === 'wait') {
            const completed = operationRegistry.complete(key, result, scope);
            view(key, { envelope: result });
            if (completed.state === 'conflict' || (result.exit_code === 0 && completed.state !== 'terminal'))
                throw new HfcacheSpawnError('', '', key, completed.operationId ?? undefined,
                                            { stage: 'operation-wait', reason: 'invalid-envelope', workMayContinue: true },
                                            undefined, { identityConflict: completed.state === 'conflict', envelope: result });
        } else if (result.exit_code !== 0) {
            operationRegistry.lookupState(key, result.errors.some(issue => issue.code === 'HFAPI013') ? 'missing' : 'unavailable');
        } else {
            const operation = (result.data as { operation?: Record<string, unknown> }).operation;
            if (result.command !== 'operations lookup' || !operation || operation.route !== original.route ||
                operation.archive_id !== original.scope.archiveId || operation.principal !== original.scope.credentialClass ||
                typeof operation.operation_id !== 'string' || !/^[0-9a-f]{32}$/.test(operation.operation_id))
                throw normalizeFailure(null, {
                    stage: 'operation-lookup',
                    reason: 'invalid-envelope',
                    idempotencyKey: key,
                    workMayContinue: true
                });
            const retained = operationRegistry.identity(key, { kind: 'operation', operationId: operation.operation_id });
            if (retained.state === 'conflict')
                throw new OperationRegistryError('scope');
        }
        view(key, { envelope: result });
        return result;
    } catch (error) {
        operationRegistry.lookupState(key, 'unavailable');
        view(key, { error: error as Error });
        throw error;
    } finally {
        view(key, { busy: false });
    }
}
