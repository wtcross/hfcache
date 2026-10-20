/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The configuration pipeline (docs/cockpit.md §6, CP-11): candidate beside
 * the target, validate as the service identity, predecessor kept, fsync and
 * rename. Ownership stays 0640 root:hfcache at every step, which is why the
 * writes go through a root shell rather than cockpit.file.
 */

import cockpit from 'cockpit';

import { Envelope } from '../lib/envelope';
import {
    CandidateGuard, CandidateInspection, candidateMutationInvocation, CONFIGURATION_PATHS,
    inspectCandidateInvocation, readInstalledInvocation,
} from '../lib/candidate-guard';
import { OperationNotice } from '../lib/events';
import { normalizeFailure } from '../lib/failure';
import { runHfcache } from './hfcache';
import { hostCall } from './connection';

export const CONFIG_PATH = CONFIGURATION_PATHS.installed;
export const CANDIDATE_PATH = CONFIGURATION_PATHS.candidate;
export const BACKUP_PATH = CONFIGURATION_PATHS.backup;

async function mutate(action: 'write' | 'install' | 'remove', guard: CandidateGuard): Promise<void> {
    const invocation = candidateMutationInvocation(action, guard);
    await hostCall(action === 'install' ? 'install' : 'candidate-write', true, async () => {
        const proc = cockpit.spawn(invocation.argv, { superuser: 'require', err: 'message' });
        proc.input(invocation.input);
        await proc;
    });
}

export async function readInstalledConfig(): Promise<string> {
    const invocation = readInstalledInvocation();
    return hostCall('installed-read', false, () =>
        cockpit.spawn(invocation.argv, { superuser: 'require', err: 'message' }));
}

/* §6 step 1: the candidate lands beside the target — same directory, so the
 * final rename is atomic and the service identity can read it. */
export function writeCandidate(guard: CandidateGuard): Promise<void> {
    return mutate('write', guard);
}

/* §6 step 2: exactly the validation every mutating command performs. */
export function validateCandidate(guard: CandidateGuard): Promise<Envelope> {
    return runHfcache(['config', 'validate'], { config: CANDIDATE_PATH, candidateGuard: guard });
}

/* §6 step 3: the API sizing job holds the config flock and binds exact bytes.
 * It creates an operation receipt while remaining archive-lock-free. */
export function planCandidate(selectors: string[], guard: CandidateGuard,
    onNotice?: (notice: OperationNotice) => void): Promise<Envelope> {
    return runHfcache(['plan', ...selectors], {
        config: CANDIDATE_PATH,
        candidateGuard: guard,
        ...(onNotice === undefined ? {} : { onNotice })
    });
}

/* No writes, lock creation, temporary files or candidate adoption. */
export async function inspectCandidate(guard: CandidateGuard): Promise<CandidateInspection> {
    const invocation = inspectCandidateInvocation(guard);
    const output = await hostCall('installed-read', false, async () => {
        const proc = cockpit.spawn(invocation.argv, { superuser: 'require', err: 'message' });
        proc.input(invocation.input);
        return await proc;
    });
    try {
        if (output.length > 512)
            throw new Error();
        const value: unknown = JSON.parse(output);
        const fields = ['candidate', 'installedBase', 'installedCandidate', 'backupBase'];
        if (typeof value !== 'object' || value === null || Array.isArray(value) ||
            Object.keys(value).length !== fields.length ||
            !fields.every(field => Object.prototype.hasOwnProperty.call(value, field) &&
                ['matching', 'absent', 'changed', 'unknown'].includes((value as Record<string, string>)[field])))
            throw new Error();
        return value as CandidateInspection;
    } catch {
        throw normalizeFailure(null, { stage: 'installed-read', reason: 'invalid-envelope' });
    }
}

/* §6 step 4: one predecessor kept, then fsync and rename over the target. */
export function installCandidate(guard: CandidateGuard): Promise<void> {
    return mutate('install', guard);
}

/* §6 step 5: confirm what is now installed, and report the fingerprint run
 * reports will carry. */
export function validateInstalled(): Promise<Envelope> {
    return runHfcache(['config', 'validate']);
}

export function removeCandidate(guard: CandidateGuard): Promise<void> {
    return mutate('remove', guard);
}

export function confirmInstalledCandidate(expected: string): Promise<Envelope> {
    return runHfcache(['config', 'validate'], { confirmInstalledContent: expected });
}
