/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Optional host-local diagnostic only (CP-09, decision 136). No journal field
 * grants authority or establishes a durable run result.
 */

import { EVENTS } from './events.ts';
import { BoundaryError, normalizeFailure } from './failure.ts';
import { isRunId } from './reports.ts';
import { BoundedLineDecoder, utf8Bytes } from './stream.ts';

export const RUN_JOURNAL_LINES = 200;
export const RUN_JOURNAL_BYTES = 64 * 1024;
export const RUN_JOURNAL_LINE_BYTES = 8 * 1024;
export const RUN_JOURNAL_RAW_BYTES = 256 * 1024;
export const RUN_JOURNAL_DEADLINE_MS = 6000;
export const RUN_JOURNAL_WINDOW_DAYS = 7;

export type JournalTruncationReason = 'line-limit' | 'display-byte-limit' |
    'oversized-line' | 'raw-byte-limit' | 'filtered-lines' | 'deadline';

export interface RunJournal {
    readonly lines: readonly string[];
    readonly truncated: boolean;
    readonly truncationReasons: readonly JournalTruncationReason[];
}

function result(lines: readonly string[], reasons: ReadonlySet<JournalTruncationReason>): RunJournal {
    return Object.freeze({
        lines: Object.freeze([...lines]),
        truncated: reasons.size !== 0,
        truncationReasons: Object.freeze([...reasons]),
    });
}

export class JournalReadError extends BoundaryError {
    readonly partial: RunJournal;

    constructor(failure: unknown, partial: RunJournal = result([], new Set())) {
        super(failure, { stage: 'journal-read', hostMutationUncertain: false });
        this.name = 'JournalReadError';
        this.partial = partial;
    }
}

/* These OR matches include the fixed rootless user-unit journal fields without
 * selecting a user manager or accidentally filtering to root's own UID. */
export function runJournalArgv(runId: string): string[] {
    if (typeof runId !== 'string' || !isRunId(runId))
        throw new JournalReadError({ problem: 'protocol-error' });
    return [
        'timeout', '--signal=TERM', '--kill-after=1s', '5s',
        'journalctl', '--quiet', '--no-pager', '--output=cat', '--reverse',
        '--since=-7days', '--lines=201', '--case-sensitive=yes',
        `--grep=(^|[[:space:]])run_id=${runId}([[:space:]]|$)`,
        '_SYSTEMD_UNIT=hfcache-sync.service', '_SYSTEMD_UNIT=hfcache-verify.service',
        '+', '_SYSTEMD_USER_UNIT=hfcache-api.service', '_SYSTEMD_USER_UNIT=hfcache-verification.service',
    ];
}

const EVENT_NAMES: ReadonlySet<string> = new Set(EVENTS);

/* The authoritative logger prefix has exactly these first three fields. A
 * substring in quoted prose, a longer ID or an unknown event is not correlation.
 * Never retain arbitrary MESSAGE prose, trailing fields or control characters. */
function projectLine(line: string, runId: string): string | null {
    for (let index = 0; index < line.length; index += 1) {
        const code = line.charCodeAt(index);
        if (code < 32 || (code >= 127 && code <= 159))
            return null;
    }
    const prefix = /^event=([a-z][a-z0-9_.-]{0,63}) level=(debug|info|warning|error|critical) run_id=([0-9a-f]{32})(?: |$)/.exec(line);
    if (prefix === null || prefix[3] !== runId || !EVENT_NAMES.has(prefix[1]))
        return null;
    return `event=${prefix[1]} level=${prefix[2]} run_id=${runId}`;
}

export interface JournalProcess extends PromiseLike<unknown> {
    stream(callback: (chunk: string) => void): unknown;
    close(problem?: string): void;
}
export type JournalSpawn = (argv: string[]) => JournalProcess;
export type JournalDeadline = (callback: () => void, milliseconds: number) => () => void;

const deadline: JournalDeadline = (callback, milliseconds) => {
    const timer = globalThis.setTimeout(callback, milliseconds);
    return () => globalThis.clearTimeout(timer);
};

/* Only the owned journal diagnostic can be closed. The operation runner has no
 * close capability and is deliberately not reused here. The clock seam permits
 * deterministic deadline tests without a real host process or a long sleep. */
export function collectRunJournal(
    runId: string, spawn: JournalSpawn, startDeadline: JournalDeadline = deadline,
): Promise<RunJournal> {
    const argv = runJournalArgv(runId); // Refuse unsafe selectors before spawning.
    return new Promise((resolve, reject) => {
        const decoder = new BoundedLineDecoder(RUN_JOURNAL_LINE_BYTES, RUN_JOURNAL_LINES + 1);
        const lines: string[] = [];
        const reasons = new Set<JournalTruncationReason>();
        let rawBytes = 0;
        let displayBytes = 0;
        let seenLines = 0;
        let bounded = false;
        let settled = false;
        let proc: JournalProcess | null = null;
        let cancelDeadline: () => void = () => undefined;

        const accept = (line: string): void => {
            if (bounded || settled)
                return;
            seenLines += 1;
            if (seenLines > RUN_JOURNAL_LINES) {
                reasons.add('line-limit');
                bounded = true;
                return;
            }
            const projected = projectLine(line, runId);
            if (projected === null) {
                if (line !== '')
                    reasons.add('filtered-lines');
                return;
            }
            const bytes = utf8Bytes(projected) + (lines.length === 0 ? 0 : 1);
            if (displayBytes + bytes > RUN_JOURNAL_BYTES) {
                reasons.add('display-byte-limit');
                bounded = true;
                return;
            }
            lines.push(projected);
            displayBytes += bytes;
        };
        const noteDropped = () => {
            if (decoder.droppedLines !== 0)
                reasons.add('oversized-line');
        };
        const closeDiagnostic = () => {
            try { proc?.close('cancelled') } catch { /* Already bounded; never replay a diagnostic. */ }
        };
        const finish = (failed: boolean, failure?: unknown) => {
            if (settled)
                return;
            // A deadline/cap/failure cannot turn an incomplete frame into a
            // complete-looking event. Only normal EOF admits a final line.
            decoder.finish(failed || bounded ? undefined : accept);
            noteDropped();
            settled = true;
            cancelDeadline();
            const partial = result(lines, reasons);
            if (failed)
                reject(new JournalReadError(failure, partial));
            else
                resolve(partial);
        };
        try {
            proc = spawn(argv);
            // Observe rejection before installing the stream callback, which
            // itself may throw or immediately reach a display cap.
            Promise.resolve(proc).then(() => finish(false), failure => {
                const normalized = normalizeFailure(failure, { stage: 'journal-read', hostMutationUncertain: false });
                if (normalized.exitStatus === 124)
                    reasons.add('deadline');
                finish(true, normalized);
            });
            proc.stream(chunk => {
                if (settled)
                    return;
                // UTF-16 length is a lower bound on UTF-8 size. Inspect at most
                // the remaining bounded chunk, never encode/copy arbitrary input.
                const remaining = RUN_JOURNAL_RAW_BYTES - rawBytes;
                if (typeof chunk !== 'string' || chunk.length > remaining || utf8Bytes(chunk) > remaining) {
                    reasons.add('raw-byte-limit');
                    bounded = true;
                    finish(false);
                    closeDiagnostic();
                    return;
                }
                rawBytes += utf8Bytes(chunk);
                decoder.push(chunk, accept);
                noteDropped();
                if (bounded) {
                    finish(false);
                    closeDiagnostic();
                }
            });
            if (!settled) {
                cancelDeadline = startDeadline(() => {
                    if (settled)
                        return;
                    reasons.add('deadline');
                    finish(true, { problem: 'timeout' });
                    closeDiagnostic();
                }, RUN_JOURNAL_DEADLINE_MS);
            }
        } catch (failure) {
            finish(true, failure);
            closeDiagnostic();
        }
    });
}
