/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Pure observation of one spawned API client (CP-02/08, decision 122).
 * The injected process deliberately has no cancellation/close capability.
 */

import { EnvelopeSchemaError, parseEnvelope } from './envelope.ts';
import type { Envelope } from './envelope.ts';
import { interpretOperationLine } from './events.ts';
import type { OperationNotice } from './events.ts';
import type { OperationIdentity } from './operation-registry.ts';
import { BoundaryError } from './failure.ts';
import type { FailureContext, FailureReason, FailureStage } from './failure.ts';
import { BoundedLineDecoder, TerminalCollector } from './stream.ts';

export type { OperationIdentity } from './operation-registry.ts';

export interface StreamProcess extends PromiseLike<unknown> {
    stream(callback: (chunk: string) => void): unknown;
}

export type Spawn = (argv: string[]) => StreamProcess;

export interface ObservationOptions {
    stage?: FailureStage;
    signal?: AbortSignal;
    onLine?: (line: string) => void;
    onNotice?: (notice: OperationNotice) => void;
    expectedKey?: string;
    onIdentity?: (notice: OperationIdentity) => void;
}

/* Missing/malformed/oversized result is an observation failure. Handles remain
 * useful even if every earlier progress line has fallen out of the tail. */
export class HfcacheSpawnError extends BoundaryError {
    readonly stderr: string;
    readonly identityConflict: boolean;
    readonly envelope: Envelope | null;

    /* Keep the old constructor shape for consumers, but never retain arbitrary
     * supplied messages/stderr. New callers provide fixed context and cause. */
    constructor(_message: string, _stderr: string, key?: string, operationId?: string,
        context: FailureContext = {}, failure?: unknown,
        evidence: { identityConflict?: boolean; envelope?: Envelope | null } = {}) {
        super(failure ?? (_message === 'reconnected' ? { problem: 'reconnected' } : failure), {
            ...context,
            ...(key === undefined ? {} : { idempotencyKey: key }),
            ...(operationId === undefined ? {} : { operationId }),
        });
        this.name = 'HfcacheSpawnError';
        this.stderr = this.safeDiagnostics.join('\n');
        this.identityConflict = evidence.identityConflict === true;
        this.envelope = evidence.envelope ?? null;
    }
}

/* Callback exceptions and page closure detach display, never domain execution.
 * Internal framing/handle capture continues until the existing process ends. */
export async function runSpawned(
    argv: string[], spawn: Spawn, options: ObservationOptions = {}, requireSuccessfulProcess = false,
): Promise<Envelope> {
    const lines = new BoundedLineDecoder();
    const terminal = new TerminalCollector();
    let key: string | undefined = options.expectedKey;
    let operationId: string | undefined;
    let keyObserved = false;
    let identityConflict = false;
    let identityObserverFailed = false;
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
        if (notice?.kind === 'key' || notice?.kind === 'operation') {
            if (notice.kind === 'key') {
                if (key !== undefined && key !== notice.key)
                    identityConflict = true;
                if (key === undefined)
                    key = notice.key;
                if (!keyObserved)
                    display(() => options.onNotice?.(notice));
                keyObserved = true;
            } else {
                if (operationId !== undefined && operationId !== notice.operationId)
                    identityConflict = true;
                if (operationId === undefined && !identityConflict) {
                    operationId = notice.operationId;
                    display(() => options.onNotice?.(notice));
                }
            }
            // Persistence/identity observation is independent of display and
            // receives duplicates/conflicts even after AbortSignal or UI errors.
            try { options.onIdentity?.(notice) } catch { identityObserverFailed = true }
        }
    };
    const emit = (complete: string[]): void => {
        for (const line of complete) {
            const notice = interpretOperationLine(line);
            // Only validated protocol records enter browser logs. Arbitrary
            // stderr and terminal bodies remain outside presentation callbacks.
            if (notice !== null)
                display(() => options.onLine?.(line));
            if (notice !== null && notice.kind !== 'key' && notice.kind !== 'operation')
                display(() => options.onNotice?.(notice));
        }
    };
    let failure: unknown = null;
    let failed = false;
    if (options.expectedKey !== undefined && !/^[A-Za-z0-9._~+-]{1,128}$/.test(options.expectedKey))
        throw new HfcacheSpawnError('', '', undefined, undefined,
                                    { stage: options.stage ?? 'operation-observe', reason: 'invalid-envelope' });
    try {
        const proc = spawn(argv);
        proc.stream(chunk => {
            terminal.push(chunk);
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
            failed = true;
        }
    } catch (error) {
        failure = error;
        failed = true;
    }
    emit(lines.finish(inspect));
    const observationError = (reason: FailureReason, envelope: Envelope | null = null): HfcacheSpawnError =>
        new HfcacheSpawnError('', '', key, operationId, {
            stage: options.stage ?? (requireSuccessfulProcess ? 'installed-confirm' : 'api-read'),
            reason,
        }, failure, { identityConflict: identityConflict || identityObserverFailed, envelope });
    let parsed: Envelope | null = null;
    if (!terminal.overflow && terminal.text().trim() !== '') {
        try { parsed = parseEnvelope(terminal.text()) } catch { /* Existing strict framing below classifies it. */ }
    }
    if (options.expectedKey !== undefined && parsed?.exit_code === 0 && (!keyObserved || operationId === undefined))
        identityConflict = true;
    if (identityConflict || identityObserverFailed)
        throw observationError('invalid-envelope', parsed);
    // A negative result cannot confirm installation, but its original API/domain
    // classification remains useful. Successful confirmation still requires every
    // guarded byte postcheck and successful process completion (CP-11).
    if (requireSuccessfulProcess && failed) {
        if (!terminal.overflow) {
            try {
                const refused = parseEnvelope(terminal.text());
                if (refused.exit_code !== 0)
                    return refused;
            } catch { /* Missing or invalid terminal output proves no result. */ }
        }
        throw observationError('process-postcheck');
    }
    if (terminal.overflow)
        throw observationError('terminal-overflow');
    if (terminal.text().trim() === '')
        throw observationError('no-envelope');
    try {
        return parseEnvelope(terminal.text());
    } catch (error) {
        if (error instanceof EnvelopeSchemaError)
            throw observationError('unsupported-schema');
        throw observationError('invalid-envelope');
    }
}
