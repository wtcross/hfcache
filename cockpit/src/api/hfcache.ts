/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Running the hfcache CLI from the page (docs/cockpit.md §2): superuser
 * bridge, then a transient systemd unit as the service identity, JSON
 * envelope in, JSON envelope out — even on failure. This is the only module
 * that spawns the CLI; everything above it consumes envelopes.
 */

import cockpit from 'cockpit';

import { hfcacheArgv } from '../lib/command';
import { guardCandidateInvocation, CandidateGuard } from '../lib/candidate-guard';
import { Envelope } from '../lib/envelope';
import { HfcacheSpawnError, ObservationOptions, runSpawned } from '../lib/runner';

export { HfcacheSpawnError };

export interface RunOptions extends ObservationOptions {
    /* Validate or plan against a candidate file instead of the installed
     * configuration (docs/cockpit.md §6). */
    config?: string;
    candidateGuard?: CandidateGuard;
}

export async function runHfcache(command: string[], options: RunOptions = {}): Promise<Envelope> {
    const argv = hfcacheArgv(command, options);
    const guarded = options.candidateGuard === undefined
        ? undefined
        : guardCandidateInvocation(argv, options.candidateGuard);
    return runSpawned(guarded?.argv ?? argv, arguments_ => {
        // Merge bounded CLI progress/handle notices with terminal stdout; the
        // independent collector never mistakes them for result authority.
        const proc = cockpit.spawn(arguments_, { superuser: 'require', err: 'out' });
        if (guarded !== undefined)
            proc.input(guarded.input);
        return proc;
    }, options);
}

export type StreamRunOptions = RunOptions;

/* API operation notices/progress accompany the exact terminal Envelope. A
 * closed page detaches its display; neither the client nor this adapter can
 * cancel accepted execution (decision 122, docs/cockpit.md §5). */
export async function runHfcacheStreaming(
    command: string[],
    options: StreamRunOptions = {}
): Promise<Envelope> {
    return runHfcache(command, options);
}
