/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Running the hfcache CLI from the page (docs/cockpit.md §2): superuser
 * bridge, then runuser to the service identity, JSON envelope in, JSON
 * envelope out — even on failure. This is the only module that spawns the
 * CLI; everything above it consumes envelopes.
 */

import cockpit from 'cockpit';

import { hfcacheArgv } from '../lib/command';
import { Envelope, parseEnvelope } from '../lib/envelope';

export interface RunOptions {
    /* Validate or plan against a candidate file instead of the installed
     * configuration (docs/cockpit.md §6). */
    config?: string;
    /* Incremental stderr, for a collapsed log pane. Never interpreted
     * (CP-02): display only. */
    onStderr?: (data: string) => void;
}

/* A spawn-level failure: the process could not run or produced no envelope.
 * An hfcache failure is NOT this — the CLI emits its envelope even on
 * failure, and that envelope is returned normally. */
export class HfcacheSpawnError extends Error {
    readonly stderr: string;

    constructor(message: string, stderr: string) {
        super(message);
        this.stderr = stderr;
    }
}

export async function runHfcache(command: string[], options: RunOptions = {}): Promise<Envelope> {
    const argv = options.config !== undefined
        ? hfcacheArgv(command, { config: options.config })
        : hfcacheArgv(command);
    const proc = cockpit.spawn(argv, { superuser: 'require', err: 'message' });
    let stdout = '';
    proc.stream(data => {
        stdout += data;
    });
    let failure: Error | null = null;
    try {
        await proc;
    } catch (error) {
        // A non-zero exit still carries the envelope on stdout
        // (docs/cli.md §4); only an empty stdout is a spawn-level failure.
        failure = error as Error;
    }
    if (stdout.trim() === '') {
        const message = failure === null ? 'hfcache produced no output' : failure.message;
        throw new HfcacheSpawnError(message, failure?.message ?? '');
    }
    return parseEnvelope(stdout);
}
