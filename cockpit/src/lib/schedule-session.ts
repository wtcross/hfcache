/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Bounded application memory survives schedule tab unmount; nothing is serialized.
 */
import { normalizeFailure } from './failure.ts';
import type { BoundaryError } from './failure.ts';
import { AcknowledgedHostChangeError, HostProfileError } from './host-profile.ts';
import { ScheduleInputError } from './schedule.ts';

export const MAX_SCHEDULE_ATTEMPTS = 8;
export const MAX_SCHEDULE_EXPECTED_BYTES = 8192;
const MAX_SCHEDULE_MEMORY_BYTES = 64 * 1024;
export interface ScheduleAttempt {
    id: number;
    host: string;
    expected: string | null;
    state: 'pending' | 'uncertain';
    error: BoundaryError | null;
    restrictionReason: string | null;
}
export class ScheduleSessionError extends Error {
    constructor() {
        super('An unresolved schedule change or full recovery memory blocks another change. Preserve and inspect existing attempts.');
        this.name = 'ScheduleSessionError';
    }
}

export function createScheduleSession() {
    let sequence = 0;
    let snapshot: readonly Readonly<ScheduleAttempt>[] = Object.freeze([]);
    const listeners = new Set<() => void>();
    const publish = (records: readonly Readonly<ScheduleAttempt>[]) => {
        snapshot = Object.freeze([...records]);
        for (const listener of listeners) {
            try { listener() } catch { /* A detached component cannot alter a retained attempt. */ }
        }
    };
    const current = (attempt: Readonly<ScheduleAttempt>) => snapshot.find(record => record.id === attempt.id &&
        record.host === attempt.host && record.expected === attempt.expected);
    return {
        snapshot: () => snapshot,
        subscribe: (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener) } },
        begin: (host: string, expected: string | null): Readonly<ScheduleAttempt> => {
            if (typeof host !== 'string' || (expected !== null && typeof expected !== 'string'))
                throw new ScheduleSessionError();
            const bytes = expected === null ? 0 : new TextEncoder().encode(expected).length;
            if (!/^[A-Za-z0-9][A-Za-z0-9._:@+-]{0,254}$/.test(host) ||
                (expected !== null && (expected.includes('\0') || expected.includes('\r') ||
                    new TextDecoder().decode(new TextEncoder().encode(expected)) !== expected || bytes > MAX_SCHEDULE_EXPECTED_BYTES)) ||
                snapshot.some(record => record.host === host) || snapshot.length >= MAX_SCHEDULE_ATTEMPTS ||
                snapshot.reduce((total, record) => total + new TextEncoder().encode(record.expected ?? '').length + record.host.length + 2048, 0) +
                    bytes + host.length + 2048 > MAX_SCHEDULE_MEMORY_BYTES)
                throw new ScheduleSessionError();
            const attempt = Object.freeze({
                id: ++sequence,
                host,
                expected,
                state: 'pending' as const,
                error: null,
                restrictionReason: null
            });
            publish([...snapshot, attempt]);
            return attempt;
        },
        complete: (attempt: Readonly<ScheduleAttempt>): void => {
            if (current(attempt)?.state === 'pending')
                publish(snapshot.filter(record => record.id !== attempt.id));
        },
        fail: (attempt: Readonly<ScheduleAttempt>, failure: unknown): void => {
            if (current(attempt)?.state !== 'pending')
                return;
            const error = failure instanceof HostProfileError || failure instanceof ScheduleInputError
                ? normalizeFailure(failure instanceof HostProfileError ? { problem: 'access-denied' } : null,
                                   { stage: 'schedule-write', hostMutationUncertain: false })
                : normalizeFailure(failure, { stage: 'schedule-write' });
            if (!error.hostMutationUncertain) {
                publish(snapshot.filter(record => record.id !== attempt.id));
                return;
            }
            const restrictionReason = failure instanceof AcknowledgedHostChangeError ? failure.restrictionReason : null;
            delete error.stack;
            const retained = Object.freeze({
                ...attempt,
                state: 'uncertain' as const,
                error: Object.freeze(error),
                restrictionReason
            });
            publish(snapshot.map(record => record.id === attempt.id ? retained : record));
        },
        acknowledge: (attempt: Readonly<ScheduleAttempt>): void => {
            if (current(attempt)?.state !== 'uncertain')
                throw new ScheduleSessionError();
            publish(snapshot.filter(record => record.id !== attempt.id));
        },
    };
}

export const scheduleSession = createScheduleSession();
