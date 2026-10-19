/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Pure observation of one spawned API client (CP-02/08, decision 122).
 * The injected process deliberately has no cancellation/close capability.
 */

import { EnvelopeSchemaError, parseEnvelope } from './envelope.ts';
import type { Envelope } from './envelope.ts';
import { interpretOperationLine } from './events.ts';
import type { OperationNotice } from './events.ts';
import { BoundedLineDecoder, DiagnosticTail, TerminalCollector } from './stream.ts';

export interface StreamProcess extends PromiseLike<unknown> {
    stream(callback: (chunk: string) => void): unknown;
}

export type Spawn = (argv: string[]) => StreamProcess;

export interface ObservationOptions {
    signal?: AbortSignal;
    onLine?: (line: string) => void;
    onNotice?: (notice: OperationNotice) => void;
}

/* Missing/malformed/oversized result is an observation failure. Handles remain
 * useful even if every earlier progress line has fallen out of the tail. */
export class HfcacheSpawnError extends Error {
    readonly stderr: string;
    readonly idempotencyKey: string | undefined;
    readonly operationId: string | undefined;
    readonly workMayContinue: boolean;

    constructor(message: string, stderr: string, key?: string, operationId?: string) {
        super(message);
        this.stderr = stderr;
        this.idempotencyKey = key;
        this.operationId = operationId;
        this.workMayContinue = key !== undefined || operationId !== undefined;
    }
}

/* Callback exceptions and page closure detach display, never domain execution.
 * Internal framing/handle capture continues until the existing process ends. */
export async function runSpawned(
    argv: string[], spawn: Spawn, options: ObservationOptions = {}, requireSuccessfulProcess = false,
): Promise<Envelope> {
    const lines = new BoundedLineDecoder();
    const diagnostics = new DiagnosticTail();
    const terminal = new TerminalCollector();
    let key: string | undefined;
    let operationId: string | undefined;
    let displayFailed = false;
    const display = (callback: (() => void) | undefined): void => {
        if (callback === undefined || displayFailed || options.signal?.aborted)
            return;
        try {
            callback();
        } catch {
            displayFailed = true;
        }
    };
    const inspect = (line: string): void => {
        // Every bounded line is inspected before per-chunk display suppression.
        const notice = interpretOperationLine(line);
        if (notice?.kind === 'key' && key === undefined) {
            key = notice.key;
            display(() => options.onNotice?.(notice));
        } else if (notice?.kind === 'operation' && operationId === undefined) {
            operationId = notice.operationId;
            display(() => options.onNotice?.(notice));
        }
    };
    const emit = (complete: string[]): void => {
        for (const line of complete) {
            display(() => options.onLine?.(line));
            const notice = interpretOperationLine(line);
            if (notice !== null && notice.kind !== 'key' && notice.kind !== 'operation')
                display(() => options.onNotice?.(notice));
        }
    };
    let failure: unknown = null;
    try {
        const proc = spawn(argv);
        proc.stream(chunk => {
            terminal.push(chunk);
            diagnostics.push(chunk);
            const dropped = lines.droppedLines;
            emit(lines.push(chunk, inspect));
            if (lines.droppedLines > dropped)
                display(() => options.onLine?.('Progress display truncated; earlier lines were dropped'));
        });
        try {
            await proc;
        } catch (error) {
            // Domain nonzero exit is carried by the exact terminal Envelope.
            failure = error;
        }
    } catch (error) {
        failure = error;
    }
    emit(lines.finish(inspect));
    const stderr = diagnostics.text();
    // Installed confirmation also owns byte postchecks after the CLI completes (CP-11).
    if (requireSuccessfulProcess && failure !== null)
        throw new HfcacheSpawnError('Installed confirmation did not complete successfully; reload and validate again', stderr, key, operationId);
    if (terminal.overflow)
        throw new HfcacheSpawnError('Terminal result exceeds the observation limit; accepted work may continue', stderr, key, operationId);
    if (terminal.text().trim() === '') {
        const reason = failure instanceof Error ? failure.message : 'hfcache produced no terminal envelope';
        // Spawn diagnostics are bounded too, and never interpreted as outcomes.
        const bounded = new DiagnosticTail();
        bounded.push(reason);
        throw new HfcacheSpawnError(bounded.text(), stderr, key, operationId);
    }
    try {
        return parseEnvelope(terminal.text());
    } catch (error) {
        if (error instanceof EnvelopeSchemaError)
            throw new HfcacheSpawnError('This terminal Envelope schema is unsupported; update the plugin to match the deployed hfcache. Accepted work may continue', stderr, key, operationId);
        throw new HfcacheSpawnError('No valid terminal Envelope was observed; accepted work may continue', stderr, key, operationId);
    }
}
