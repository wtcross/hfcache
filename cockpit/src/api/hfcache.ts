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
import { Envelope, extractEnvelope, parseEnvelope } from '../lib/envelope';

export interface RunOptions {
    /* Validate or plan against a candidate file instead of the installed
     * configuration (docs/cockpit.md §6). */
    config?: string;
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

export interface StreamRunOptions {
    onLine?: (line: string) => void;
}

/* A streamed mutating run (selector sync — decisions 89, 92): stderr merges
 * into the stream so the §24 checkpoint events are visible live, and the
 * envelope is recovered from the stream's tail. The transient unit outlives
 * a closed page — only this view and its envelope die with the page; the
 * caller owns stating that consequence before starting one
 * (docs/cockpit.md §5). */
export async function runHfcacheStreaming(
    command: string[],
    options: StreamRunOptions = {}
): Promise<Envelope> {
    const proc = cockpit.spawn(hfcacheArgv(command), { superuser: 'require', err: 'out' });
    let output = '';
    let pending = '';
    proc.stream(data => {
        output += data;
        if (options.onLine === undefined)
            return;
        pending += data;
        const lines = pending.split('\n');
        pending = lines.pop() ?? '';
        for (const line of lines)
            options.onLine(line);
    });
    let failure: Error | null = null;
    try {
        await proc;
    } catch (error) {
        failure = error as Error;
    }
    if (output.trim() === '') {
        const message = failure === null ? 'hfcache produced no output' : failure.message;
        throw new HfcacheSpawnError(message, '');
    }
    return extractEnvelope(output);
}
