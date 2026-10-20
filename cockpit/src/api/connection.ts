/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Application-owned privileged channels (CP-03/13, decision 134).
 */
import cockpit from 'cockpit';
import { superuser } from 'superuser';

import { OwnedConnection } from '../lib/connection';
import { normalizeFailure } from '../lib/failure';
import type { FailureStage } from '../lib/failure';

export const systemConnection = new OwnedConnection(() =>
    cockpit.dbus('org.freedesktop.systemd1', { bus: 'system', superuser: 'try' }), undefined, () => cockpit.transport.host);

export interface ConnectionSnapshot {
    generation: number;
    administrative: boolean;
}

let snapshot: ConnectionSnapshot = {
    generation: systemConnection.generation, administrative: superuser.allowed === true,
};
const listeners = new Set<() => void>();
let detach: (() => void) | null = null;

function publish(): void {
    // Reading generation may itself retire an old host owner and publish once.
    // Compare after that reconciliation, avoiding a second same-state snapshot.
    const generation = systemConnection.generation;
    const administrative = superuser.allowed === true;
    if (snapshot.generation === generation && snapshot.administrative === administrative)
        return;
    snapshot = { generation, administrative };
    for (const listener of listeners)
        listener();
}

export function subscribeConnection(listener: () => void): () => void {
    listeners.add(listener);
    if (detach === null) {
        const invalidate = () => systemConnection.invalidate();
        const unsubscribe = systemConnection.subscribe(publish);
        superuser.addEventListener('changed', invalidate);
        superuser.addEventListener('reconnect', invalidate);
        detach = () => {
            superuser.removeEventListener('changed', invalidate);
            superuser.removeEventListener('reconnect', invalidate);
            unsubscribe();
            systemConnection.invalidate();
            publish();
        };
        publish();
    }
    return () => {
        listeners.delete(listener);
        if (listeners.size === 0 && detach !== null) {
            const dispose = detach;
            detach = null;
            dispose();
        }
    };
}

export function connectionSnapshot(): ConnectionSnapshot { return snapshot }

/* Reconcile a trusted host change before beginning an asynchronous read. Keep
 * this outside React snapshot/render access: invalidation can notify subscribers. */
export function synchronizeConnection(): ConnectionSnapshot {
    publish();
    return snapshot;
}

export function captureSession(stage: FailureStage): number {
    const connection = synchronizeConnection();
    if (!connection.administrative)
        throw normalizeFailure({ problem: 'access-denied' }, { stage, hostMutationUncertain: false });
    return connection.generation;
}

export function assertSession(generation: number, stage: FailureStage, mutation = false): void {
    const connection = synchronizeConnection();
    if (!connection.administrative || generation !== connection.generation)
        throw normalizeFailure({ problem: 'reconnected' }, { stage, hostMutationUncertain: mutation });
}

export async function hostCall<T>(
    stage: FailureStage, mutation: boolean, action: () => PromiseLike<T>,
): Promise<T> {
    const generation = captureSession(stage);
    try {
        const result = await action();
        assertSession(generation, stage, mutation);
        return result;
    } catch (error) {
        throw normalizeFailure(error, { stage, hostMutationUncertain: mutation });
    }
}
