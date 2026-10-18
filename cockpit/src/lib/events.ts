/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The journal's structured event lines (docs/cli.md output discipline;
 * hfcache.logging.EVENTS). The vocabulary is closed: the UI keys only on
 * these names and ignores lines it does not know rather than failing on
 * them (docs/cockpit.md §5). Pure logic: no cockpit import.
 */

import { PROGRESS_LINE_BYTES, utf8Bytes } from './stream.ts';

export type OperationNotice =
    { kind: 'key'; key: string } |
    { kind: 'operation'; operationId: string } |
    { kind: 'progress'; sequence: number; phase: string; message: string } |
    { kind: 'gap'; oldestSequence: number } |
    { kind: 'continuing' };

/* These are the API CLI's bounded display records, not the journal's closed
 * domain-event vocabulary. No human diagnostic is used to classify a result.
 * Only exact validated handle lines are retained as reconnect evidence. */
export function interpretOperationLine(line: string): OperationNotice | null {
    if (utf8Bytes(line) > PROGRESS_LINE_BYTES || Array.from(line).some(character => {
        const code = character.charCodeAt(0);
        return code < 32 || (code >= 127 && code <= 159);
    }))
        return null;
    const key = /^(?:Idempotency key|Original idempotency key): ([A-Za-z0-9._~+-]{1,128})$/.exec(line);
    if (key !== null)
        return { kind: 'key', key: key[1] };
    const operation = /^Operation: ([0-9a-f]{32})(?:; accepted work may continue)?$/.exec(line);
    if (operation !== null)
        return { kind: 'operation', operationId: operation[1] };
    if (line === 'Accepted work may continue; reconnect using the retained handles')
        return { kind: 'continuing' };
    const gap = /^Event history gap; retained events start at ([1-9][0-9]{0,15})$/.exec(line);
    if (gap !== null && Number.isSafeInteger(Number(gap[1])))
        return { kind: 'gap', oldestSequence: Number(gap[1]) };
    const progress = /^\[([1-9][0-9]{0,15})\] ([a-z][a-z0-9_.-]{0,63}): (.*)$/.exec(line);
    if (progress !== null && Number.isSafeInteger(Number(progress[1])))
        return { kind: 'progress', sequence: Number(progress[1]), phase: progress[2], message: progress[3] };
    return null;
}

/* hfcache.logging.EVENTS, verbatim. A name added there is added here in the
 * same change or the UI simply does not react to it — never an error. */
export const EVENTS = [
    'run.started',
    'preflight.failed',
    'repository.resolved',
    'repository.queued',
    'repository.skipped',
    'download.started',
    'download.completed',
    'hash.started',
    'hash.completed',
    'verification.completed',
    'dependency.undeclared',
    'publication.completed',
    'retention.pruned',
    'retention.deferred',
    'quarantine.cleaned',
    'repository.failed',
    'run.completed',
] as const;

export type EventName = typeof EVENTS[number];

const EVENT_NAMES: ReadonlySet<string> = new Set(EVENTS);

export interface JournalEvent {
    event: EventName;
    runId: string;
    repository?: string;
    fields: Record<string, string>;
}

/* logfmt as hfcache emits it (docs/cli.md §6): `key=value`, values quoted
 * only when they would otherwise be ambiguous, backslash escapes inside
 * quotes. Returns null for a line that is not logfmt at all. */
export function parseLogfmt(line: string): Record<string, string> | null {
    const fields: Record<string, string> = {};
    const pattern = /([A-Za-z0-9_.-]+)=("(?:[^"\\]|\\.)*"|[^\s]*)/g;
    let matched = false;
    for (const match of line.matchAll(pattern)) {
        matched = true;
        let value = match[2];
        if (value.startsWith('"') && value.endsWith('"') && value.length >= 2)
            value = value.slice(1, -1).replace(/\\(.)/g, '$1');
        fields[match[1]] = value;
    }
    return matched ? fields : null;
}

/* One journal line to one typed event, or null: not logfmt, no event= key,
 * or a name outside the closed vocabulary. */
export function interpretEvent(line: string): JournalEvent | null {
    const fields = parseLogfmt(line.trim());
    if (fields === null || fields.event === undefined)
        return null;
    if (!EVENT_NAMES.has(fields.event))
        return null;
    const event: JournalEvent = {
        event: fields.event as EventName,
        runId: fields.run_id ?? '',
        fields,
    };
    if (fields.repository !== undefined)
        event.repository = fields.repository;
    return event;
}
