/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Bounded read identity is separate from terminal Envelopes and job receipts.
 */
import { utf8Bytes } from './stream.ts';

export const READ_METADATA_PREFIX = 'Run read metadata: ';
export const READ_METADATA_LINE_BYTES = 2048;
export interface RunReadMetadata {
    schema_version: 1;
    command: 'runs' | 'runs read';
    run_id: string;
    request_id: string;
    archive_id: string;
    config_fingerprint: string;
    next_cursor: string | null;
}
export class ReadMetadataError extends Error {
    constructor() { super('Run read identity metadata is missing, incompatible or inconsistent.'); this.name = 'ReadMetadataError' }
}
export const isArchiveId = (value: unknown): value is string => typeof value === 'string' &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value);
export const isReadCursor = (value: unknown): value is string => typeof value === 'string' &&
    /^[\x21-\x7e]{1,256}$/.test(value);

export function parseReadMetadataLine(line: string): Readonly<RunReadMetadata> | null {
    if (!line.startsWith(READ_METADATA_PREFIX))
        return null;
    try {
        if (utf8Bytes(line) > READ_METADATA_LINE_BYTES)
            throw new ReadMetadataError();
        const body = line.slice(READ_METADATA_PREFIX.length);
        const value: unknown = JSON.parse(body);
        if (typeof value !== 'object' || value === null || Array.isArray(value) || JSON.stringify(value) !== body)
            throw new ReadMetadataError();
        const data = value as Record<string, unknown>;
        const fields = ['schema_version', 'command', 'run_id', 'request_id', 'archive_id', 'config_fingerprint', 'next_cursor'];
        if (Object.keys(data).length !== fields.length || !fields.every(field => Object.prototype.hasOwnProperty.call(data, field)) ||
            data.schema_version !== 1 || !['runs', 'runs read'].includes(data.command as string) ||
            typeof data.run_id !== 'string' || !/^[0-9a-f]{32}$/.test(data.run_id) ||
            typeof data.request_id !== 'string' || !/^[0-9a-f]{32}$/.test(data.request_id) ||
            !isArchiveId(data.archive_id) || typeof data.config_fingerprint !== 'string' ||
            !/^[0-9a-f]{64}$/.test(data.config_fingerprint) ||
            (data.next_cursor !== null && !isReadCursor(data.next_cursor)) ||
            (data.command === 'runs read' && data.next_cursor !== null))
            throw new ReadMetadataError();
        return Object.freeze(data as unknown as RunReadMetadata);
    } catch {
        throw new ReadMetadataError();
    }
}

/* Inspect every candidate metadata line independently of display eviction and
 * terminal size. Ignore other lines without retaining their arbitrary content. */
export class ReadMetadataCollector {
    private pending = '';
    private interested = true;
    private seen = 0;
    private invalid = false;
    private value: Readonly<RunReadMetadata> | null = null;

    private readonly receive: ((metadata: Readonly<RunReadMetadata>) => void) | undefined;
    constructor(receive?: (metadata: Readonly<RunReadMetadata>) => void) { this.receive = receive }

    private append(fragment: string): void {
        if (!this.interested)
            return;
        const probe = this.pending + fragment.slice(0, Math.max(0, READ_METADATA_PREFIX.length - this.pending.length));
        if (!READ_METADATA_PREFIX.startsWith(probe) && !probe.startsWith(READ_METADATA_PREFIX)) {
            this.interested = false;
            this.pending = '';
            return;
        }
        if (utf8Bytes(this.pending) + utf8Bytes(fragment) > READ_METADATA_LINE_BYTES) {
            this.invalid = true;
            this.interested = false;
            this.pending = '';
            return;
        }
        this.pending += fragment;
    }

    private line(): void {
        if (this.interested && this.pending.startsWith(READ_METADATA_PREFIX)) {
            this.seen += 1;
            try {
                const metadata = parseReadMetadataLine(this.pending);
                if (metadata === null || this.seen !== 1)
                    throw new ReadMetadataError();
                this.value = metadata;
                this.receive?.(metadata);
            } catch {
                this.invalid = true;
            }
        }
        this.pending = '';
        this.interested = true;
    }

    push(chunk: string): void {
        let offset = 0;
        while (offset < chunk.length) {
            const newline = chunk.indexOf('\n', offset);
            this.append(chunk.slice(offset, newline === -1 ? chunk.length : newline));
            if (newline === -1)
                return;
            this.line();
            offset = newline + 1;
        }
    }

    finish(): void { if (this.pending !== '') this.line(); }

    result(): Readonly<RunReadMetadata> {
        if (this.invalid || this.seen !== 1 || this.value === null)
            throw new ReadMetadataError();
        return this.value;
    }
}
