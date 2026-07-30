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
import { runHfcache } from './hfcache';

export const CONFIG_PATH = '/etc/hfcache/config.toml';
export const CANDIDATE_PATH = '/etc/hfcache/.candidate.toml';
export const BACKUP_PATH = '/etc/hfcache/config.toml.bak';

function shell(script: string): cockpit.Spawn<string> {
    return cockpit.spawn(['bash', '-ec', script], { superuser: 'require', err: 'message' });
}

export function readInstalledConfig(): Promise<string> {
    return cockpit.spawn(['cat', CONFIG_PATH], { superuser: 'require', err: 'message' });
}

/* §6 step 1: the candidate lands beside the target — same directory, so the
 * final rename is atomic and the service identity can read it. */
export async function writeCandidate(content: string): Promise<void> {
    const script =
        'umask 077\n' +
        'tmp=$(mktemp /etc/hfcache/.candidate.XXXXXX)\n' +
        'cat > "$tmp"\n' +
        'chown root:hfcache "$tmp"\n' +
        'chmod 0640 "$tmp"\n' +
        `mv -f "$tmp" ${CANDIDATE_PATH}\n`;
    const proc = shell(script);
    proc.input(content);
    await proc;
}

/* §6 step 2: exactly the validation every mutating command performs. */
export function validateCandidate(): Promise<Envelope> {
    return runHfcache(['config', 'validate'], { config: CANDIDATE_PATH });
}

/* §6 step 3: the sizing preview, against the candidate — plan takes no lock
 * and mutates nothing, so a candidate is a legitimate target. */
export function planCandidate(selectors: string[]): Promise<Envelope> {
    return runHfcache(['plan', ...selectors], { config: CANDIDATE_PATH });
}

/* §6 step 4: one predecessor kept, then fsync and rename over the target. */
export async function installCandidate(): Promise<void> {
    const script =
        `sync ${CANDIDATE_PATH}\n` +
        `cp -p ${CONFIG_PATH} ${BACKUP_PATH}\n` +
        `mv -f ${CANDIDATE_PATH} ${CONFIG_PATH}\n` +
        'sync /etc/hfcache\n';
    await shell(script);
}

/* §6 step 5: confirm what is now installed, and report the fingerprint run
 * reports will carry. */
export function validateInstalled(): Promise<Envelope> {
    return runHfcache(['config', 'validate']);
}

export function removeCandidate(): Promise<string> {
    return shell(`rm -f ${CANDIDATE_PATH}`);
}
