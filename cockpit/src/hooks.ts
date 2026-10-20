/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * React glue over the invocation layer.
 */

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';

import { runHfcache } from './api/hfcache';
import { connectionSnapshot, subscribeConnection } from './api/connection';
import { normalizeFailure } from './lib/failure';
import {
    ServiceResult, serviceResult, TimerState, timerState, UnitState, unitState,
} from './api/systemd';
import { Envelope, OperationEvidence } from './lib/envelope';
import { OperationNotice } from './lib/events';
import { currentOperationHost, operationRegistry, operationViews, subscribeOperationViews, submissionBlocked } from './api/operations';
import { hostActionAllowed, profileSnapshot, readHostProfile, subscribeProfile } from './api/profile';
import { HOST_ACTIONS } from './lib/host-profile';

export function useConnection() {
    return useSyncExternalStore(subscribeConnection, connectionSnapshot);
}

export function useHostProfile() {
    const connection = useConnection();
    const host = currentOperationHost();
    const profile = useSyncExternalStore(subscribeProfile, profileSnapshot);
    useEffect(() => {
        const current = profileSnapshot();
        if (connection.administrative && !current.loading &&
            (current.host !== host || current.generation !== connection.generation || (current.profile === null && current.error === null)))
            readHostProfile().catch(() => { /* Safe classified error is retained by the adapter. */ });
    }, [connection.administrative, connection.generation, host, profile.loading, profile.generation]);
    return {
        ...profile,
        permissions: Object.fromEntries(HOST_ACTIONS.map(action =>
            [action, hostActionAllowed(action)])) as typeof profile.permissions
    };
}

export function useOperations() {
    const registry = useSyncExternalStore(operationRegistry.subscribe, operationRegistry.snapshot);
    const views = useSyncExternalStore(subscribeOperationViews, operationViews);
    return { registry, views, blocked: submissionBlocked() };
}

export interface EnvelopeQuery {
    envelope: Envelope | null;
    error: Error | null;
    loading: boolean;
    refresh: () => void;
}

/* Abort detaches this page's display only. API admission/execution and the
 * existing CLI observer are never cancelled or resubmitted (ADR122). */
export function useObservationSignal(): () => AbortSignal {
    const controller = useRef<AbortController | null>(null);
    useEffect(() => () => controller.current?.abort(), []);
    return useCallback(() => {
        controller.current?.abort();
        controller.current = new AbortController();
        return controller.current.signal;
    }, []);
}

export function useOperationHandles() {
    const [handles, setHandles] = useState<OperationEvidence>({ workMayContinue: false });
    const reset = useCallback(() => setHandles({ workMayContinue: false }), []);
    const onNotice = useCallback((notice: OperationNotice) => {
        if (notice.kind === 'key')
            setHandles(previous => previous.idempotencyKey === notice.key
                ? previous
                : { idempotencyKey: notice.key, workMayContinue: false });
        if (notice.kind === 'operation')
            setHandles(previous => ({ ...previous, operationId: notice.operationId, workMayContinue: true }));
        if (notice.kind === 'continuing')
            setHandles(previous => ({ ...previous, workMayContinue: true }));
    }, []);
    return { handles, reset, onNotice };
}

/* Run one read-only hfcache command and hold its envelope. A non-zero exit
 * is a value here, not an error (docs/cockpit.md §4): `error` is only a
 * spawn- or envelope-level failure. */
export function useHfcache(command: string[]): EnvelopeQuery {
    const [envelope, setEnvelope] = useState<Envelope | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [loading, setLoading] = useState(true);
    const [generation, setGeneration] = useState(0);
    const key = JSON.stringify(command);
    const connection = useConnection();
    const origin = JSON.stringify([key, generation, connection]);
    const [observedOrigin, setObservedOrigin] = useState('');

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setEnvelope(null);
        setError(null);
        runHfcache(JSON.parse(key) as string[])
                .then(result => {
                    if (!cancelled) {
                        setObservedOrigin(origin);
                        setEnvelope(result);
                        setError(null);
                    }
                })
                .catch(failure => {
                    if (!cancelled) {
                        setObservedOrigin(origin);
                        setError(normalizeFailure(failure));
                    }
                })
                .finally(() => {
                    if (!cancelled)
                        setLoading(false);
                });
        return () => {
            cancelled = true;
        };
    }, [key, generation, connection, origin]);

    const refresh = useCallback(() => setGeneration(value => value + 1), []);
    const fresh = observedOrigin === origin;
    return {
        envelope: fresh ? envelope : null,
        error: fresh ? error : null,
        loading: loading || !fresh,
        refresh
    };
}

export interface UnitQuery {
    state: UnitState | null;
    timer: TimerState | null;
    result: ServiceResult | null;
    error: Error | null;
    loading: boolean;
    refresh: () => void;
}

/* Poll one unit's state. Timer units also read next/last elapse; services
 * also read Result/ExecMainStatus. Read-only D-Bus, safe for any unit —
 * operating on units goes through api/systemd's guarded entry points. */
export function useUnitPoll(name: string, intervalMs = 5000): UnitQuery {
    const [state, setState] = useState<UnitState | null>(null);
    const [timer, setTimer] = useState<TimerState | null>(null);
    const [result, setResult] = useState<ServiceResult | null>(null);
    const [generation, setGeneration] = useState(0);

    const [error, setError] = useState<Error | null>(null);
    const [loading, setLoading] = useState(true);
    const connection = useConnection();
    const origin = JSON.stringify([name, intervalMs, generation, connection]);
    const [observedOrigin, setObservedOrigin] = useState('');
    const latestOrigin = useRef(origin);
    latestOrigin.current = origin;

    useEffect(() => {
        let cancelled = false;
        let handle: ReturnType<typeof setTimeout> | undefined;
        const poll = async () => {
            // A close invalidates rendered evidence immediately. Its next read
            // uses this finite loop, avoiding a reconnect/render retry storm.
            const observedConnection = connectionSnapshot();
            setLoading(true);
            setState(null);
            setTimer(null);
            setResult(null);
            try {
                const value = await unitState(name);
                const timerValue = name.endsWith('.timer') ? await timerState(name) : null;
                const resultValue = name.endsWith('.service') ? await serviceResult(name) : null;
                if (!cancelled && observedConnection === connectionSnapshot()) {
                    setObservedOrigin(latestOrigin.current);
                    setState(value);
                    setTimer(timerValue);
                    setResult(resultValue);
                    setError(null);
                }
            } catch (failure) {
                if (!cancelled) {
                    setObservedOrigin(latestOrigin.current);
                    setError(normalizeFailure(failure, { stage: 'unit-read' }));
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                    handle = setTimeout(() => { poll() }, intervalMs);
                }
            }
        };
        poll();
        return () => {
            cancelled = true;
            clearTimeout(handle);
        };
    }, [name, intervalMs, generation, connection.administrative]);

    const refresh = useCallback(() => setGeneration(value => value + 1), []);
    const fresh = observedOrigin === origin;
    return {
        state: fresh ? state : null,
        timer: fresh ? timer : null,
        result: fresh ? result : null,
        error: fresh ? error : null,
        loading: loading || !fresh,
        refresh
    };
}
