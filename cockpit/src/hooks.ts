/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * React glue over the invocation layer.
 */

import { useCallback, useEffect, useState } from 'react';

import { runHfcache } from './api/hfcache';
import { Envelope } from './lib/envelope';

export interface EnvelopeQuery {
    envelope: Envelope | null;
    error: Error | null;
    loading: boolean;
    refresh: () => void;
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
