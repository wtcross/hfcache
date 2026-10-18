/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * React glue over the invocation layer.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { runHfcache } from './api/hfcache';
import {
    ServiceResult, serviceResult, TimerState, timerState, UnitState, unitState,
} from './api/systemd';
import { Envelope, OperationEvidence } from './lib/envelope';
import { OperationNotice } from './lib/events';

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

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        runHfcache(JSON.parse(key) as string[])
                .then(result => {
                    if (!cancelled) {
                        setEnvelope(result);
                        setError(null);
                    }
                })
                .catch(failure => {
                    if (!cancelled)
                        setError(failure as Error);
                })
                .finally(() => {
                    if (!cancelled)
                        setLoading(false);
                });
        return () => {
            cancelled = true;
        };
    }, [key, generation]);

    const refresh = useCallback(() => setGeneration(value => value + 1), []);
    return { envelope, error, loading, refresh };
}

export interface UnitQuery {
    state: UnitState | null;
    timer: TimerState | null;
    result: ServiceResult | null;
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

    useEffect(() => {
        let cancelled = false;
        const poll = () => {
            unitState(name).then(value => {
                if (!cancelled)
                    setState(value);
            }, () => undefined);
            if (name.endsWith('.timer')) {
                timerState(name).then(value => {
                    if (!cancelled)
                        setTimer(value);
                }, () => undefined);
            }
            if (name.endsWith('.service')) {
                serviceResult(name).then(value => {
                    if (!cancelled)
                        setResult(value);
                }, () => undefined);
            }
        };
        poll();
        const handle = window.setInterval(poll, intervalMs);
        return () => {
            cancelled = true;
            window.clearInterval(handle);
        };
    }, [name, intervalMs, generation]);

    const refresh = useCallback(() => setGeneration(value => value + 1), []);
    return { state, timer, result, refresh };
}
