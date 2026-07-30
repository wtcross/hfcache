/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The journal's structured event lines (docs/plan.md §24;
 * hfcache.logging.EVENTS). The vocabulary is closed: the UI keys only on
 * these names and ignores lines it does not know rather than failing on
 * them (docs/cockpit.md §5). Pure logic: no cockpit import.
 */

/* hfcache.logging.EVENTS, verbatim. A name added there is added here in the
 * same change or the UI simply does not react to it — never an error. */
export const EVENTS = [
    'run.started',
    'preflight.failed',
    'repository.resolved',
    'repository.skipped',
    'download.started',
    'download.completed',
    'verification.completed',
    'dependency.undeclared',
    'publication.completed',
    'retention.pruned',
    'retention.deferred',
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
