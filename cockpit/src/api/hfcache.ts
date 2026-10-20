/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Running the hfcache CLI from the page (docs/cockpit.md §2): superuser
 * bridge, then a transient systemd unit as the service identity, JSON
 * envelope in, JSON envelope out — even on failure. This is the only module
 * that spawns the CLI; everything above it consumes envelopes.
 */

import cockpit from 'cockpit';

import { assertSession, captureSession } from './connection';
import type { FailureStage } from '../lib/failure';

import { hfcacheArgv } from '../lib/command';
import { guardCandidateInvocation, guardInstalledInvocation, CandidateGuard } from '../lib/candidate-guard';
import { Envelope } from '../lib/envelope';
import { HfcacheSpawnError, ObservationOptions, runSpawned } from '../lib/runner';

export { HfcacheSpawnError };

export interface RunOptions extends ObservationOptions {
    /* Validate or plan against a candidate file instead of the installed
     * configuration (docs/cockpit.md §6). */
    config?: string;
    candidateGuard?: CandidateGuard;
    confirmInstalledContent?: string;
}

export async function runHfcache(command: string[], options: RunOptions = {}): Promise<Envelope> {
    const stage: FailureStage = options.stage ?? (
        options.confirmInstalledContent !== undefined
            ? 'installed-confirm'
            : options.config !== undefined
                ? (command[0] === 'plan' ? 'candidate-preview' : 'candidate-validate')
                : command[0] === 'config'
                    ? 'installed-validate'
                    : command[0] === 'operations'
                        ? (command[1] === 'lookup' ? 'operation-lookup' : 'operation-wait')
                        : ['plan', 'sync', 'doctor', 'prune', 'recover', 'repair'].includes(command[0]) ||
        (command[0] === 'verify' && !command.includes('--estimate'))
                            ? 'operation-observe'
                            : 'api-read'
    );
    const generation = captureSession(stage);
    const argv = hfcacheArgv(command, options);
    if (options.confirmInstalledContent !== undefined &&
        (options.config !== undefined || options.candidateGuard !== undefined))
        throw new Error('Installed confirmation cannot select a candidate');
    const guarded = options.confirmInstalledContent !== undefined
        ? guardInstalledInvocation(argv, options.confirmInstalledContent)
        : options.candidateGuard === undefined
            ? undefined
            : guardCandidateInvocation(argv, options.candidateGuard);
    const envelope = await runSpawned(guarded?.argv ?? argv, arguments_ => {
        // Merge bounded CLI progress/handle notices with terminal stdout; the
        // independent collector never mistakes them for result authority.
        const proc = cockpit.spawn(arguments_, { superuser: 'require', err: 'out' });
        if (guarded !== undefined)
            proc.input(guarded.input);
        return proc;
    }, { ...options, stage }, options.confirmInstalledContent !== undefined);
    // A classified failed Envelope stays authoritative. Successful installed
    // confirmation additionally requires the same administrative session.
    if (options.confirmInstalledContent !== undefined && envelope.exit_code === 0)
        assertSession(generation, stage, true);
    return envelope;
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
