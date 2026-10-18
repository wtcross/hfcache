/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Bounded display framing, independent of terminal JSON (decision 122).
 */

export const PROGRESS_LINE_BYTES = 8 * 1024;
export const DIAGNOSTIC_BYTES = 64 * 1024;
export const TERMINAL_BYTES = 16 * 1024 * 1024;

/* Avoid allocating an encoded copy of an untrusted oversized chunk. */
export function utf8Bytes(value: string): number {
    let bytes = 0;
    for (let index = 0; index < value.length; index += 1) {
        const character = value.charCodeAt(index);
        if (character < 0x80)
            bytes += 1;
        else if (character < 0x800)
            bytes += 2;
        else if (character >= 0xd800 && character <= 0xdbff &&
                 index + 1 < value.length && value.charCodeAt(index + 1) >= 0xdc00 &&
                 value.charCodeAt(index + 1) <= 0xdfff) {
            bytes += 4;
            index += 1;
        } else {
            bytes += 3;
        }
    }
    return bytes;
}

/* UI arrays retain a whole-line suffix, independently of durable handles. The
 * byte ceiling includes separators, so 200 maximum-size lines cannot silently
 * grow the displayed log beyond the 64 KiB diagnostic contract. */
export function appendDisplayLine(previous: readonly string[], line: string, maxLines = 200): string[] {
    if (!Number.isSafeInteger(maxLines) || maxLines < 1)
        throw new RangeError('display line bound must be a positive integer');
    const retained: string[] = [];
    let bytes = 0;
    for (let index = previous.length; index >= 0 && retained.length < maxLines; index -= 1) {
        const candidate = index === previous.length ? line : previous[index];
        const size = utf8Bytes(candidate);
        if (size > PROGRESS_LINE_BYTES)
            continue;
        const extra = size + (retained.length === 0 ? 0 : 1);
        if (bytes + extra > DIAGNOSTIC_BYTES)
            break;
        retained.push(candidate);
        bytes += extra;
    }
    return retained.reverse();
}

function appendedBytes(previous: string, fragment: string): number {
    const last = previous.charCodeAt(previous.length - 1);
    const first = fragment.charCodeAt(0);
    // Native chunks can split a UTF-16 surrogate pair. Its two previously
    // independent replacement counts (3+3) become one four-byte codepoint.
    const size = utf8Bytes(fragment);
    if (last >= 0xd800 && last <= 0xdbff && first >= 0xdc00 && first <= 0xdfff)
        return size - 2;
    return size;
}

/* An oversized line is discarded through its newline, never emitted as a
 * plausible truncated handle/event. Returned arrays are bounded too. inspect
 * sees every complete bounded line before display suppression; the runner uses
 * it only to retain key/operation handles, not for unbounded display callbacks. */
export class BoundedLineDecoder {
    readonly maxLineBytes: number;
    readonly maxLinesPerPush: number;
    private pending = '';
    private bytes = 0;
    private discarding = false;
    private dropped = 0;

    constructor(
        maxLineBytes = PROGRESS_LINE_BYTES,
        maxLinesPerPush = 256
    ) {
        if (!Number.isSafeInteger(maxLineBytes) || maxLineBytes < 1 ||
            !Number.isSafeInteger(maxLinesPerPush) || maxLinesPerPush < 1)
            throw new RangeError('line framing bounds must be positive integers');
        this.maxLineBytes = maxLineBytes;
        this.maxLinesPerPush = maxLinesPerPush;
    }

    get droppedLines(): number { return this.dropped }

    private drop(): void { this.dropped = Math.min(Number.MAX_SAFE_INTEGER, this.dropped + 1) }

    push(chunk: string, inspect?: (line: string) => void): string[] {
        const lines: string[] = [];
        let offset = 0;
        while (offset < chunk.length) {
            const newline = chunk.indexOf('\n', offset);
            const end = newline === -1 ? chunk.length : newline;
            const fragment = chunk.slice(offset, end);
            if (!this.discarding) {
                const size = appendedBytes(this.pending, fragment);
                if (this.bytes + size > this.maxLineBytes) {
                    this.pending = '';
                    this.bytes = 0;
                    this.discarding = true;
                } else {
                    this.pending += fragment;
                    this.bytes += size;
                }
            }
            if (newline === -1)
                break;
            if (this.discarding) {
                this.drop();
            } else {
                const line = this.pending.endsWith('\r') ? this.pending.slice(0, -1) : this.pending;
                inspect?.(line);
                if (lines.length === this.maxLinesPerPush) {
                    lines.shift();
                    this.drop();
                }
                lines.push(line);
            }
            this.pending = '';
            this.bytes = 0;
            this.discarding = false;
            offset = newline + 1;
        }
        return lines;
    }

    finish(inspect?: (line: string) => void): string[] {
        if (this.discarding) {
            this.drop();
            this.discarding = false;
            return [];
        }
        const line = this.pending;
        this.pending = '';
        this.bytes = 0;
        if (line === '')
            return [];
        inspect?.(line);
        return [line];
    }
}

/* Keep bounded diagnostics without retaining all progress. UTF-16 slicing is
 * followed by a UTF-8 bound; a broken leading surrogate is never interpreted. */
export class DiagnosticTail {
    readonly maxBytes: number;
    private value = '';

    constructor(maxBytes = DIAGNOSTIC_BYTES) {
        if (!Number.isSafeInteger(maxBytes) || maxBytes < 1)
            throw new RangeError('diagnostic bound must be a positive integer');
        this.maxBytes = maxBytes;
    }

    push(chunk: string): void {
        this.value = (this.value + chunk.slice(-this.maxBytes)).slice(-this.maxBytes);
        while (utf8Bytes(this.value) > this.maxBytes)
            this.value = this.value.slice(Math.max(1, Math.floor(this.value.length / 8)));
    }

    text(): string { return this.value }
}

/* CLI stdout contains a single terminal object. Its collector does not depend
 * on progress framing, so a large JSON line/pretty document survives display
 * truncation and arbitrarily many preceding progress lines. */
export class TerminalCollector {
    readonly maxBytes: number;
    private parts: string[] = [];
    private pendingParts: string[] = [];
    private pendingBytes = 0;
    private bytes = 0;
    private atLineStart = true;
    private capturing = false;
    private lastCharacter = '';
    overflow = false;

    constructor(maxBytes = TERMINAL_BYTES) {
        if (!Number.isSafeInteger(maxBytes) || maxBytes < 1)
            throw new RangeError('terminal bound must be a positive integer');
        this.maxBytes = maxBytes;
    }

    push(chunk: string): void {
        let offset = 0;
        while (offset < chunk.length) {
            const newline = chunk.indexOf('\n', offset);
            const end = newline === -1 ? chunk.length : newline + 1;
            const fragment = chunk.slice(offset, end);
            if (this.atLineStart && fragment.startsWith('{'))
                this.capturing = true;
            if (this.capturing && !this.overflow) {
                const size = appendedBytes(this.lastCharacter, fragment);
                if (this.bytes + size > this.maxBytes) {
                    this.parts = [];
                    this.pendingParts = [];
                    this.overflow = true;
                } else {
                    this.pendingParts.push(fragment);
                    this.pendingBytes += size;
                    // Flatten each small block once. Repeatedly joining the
                    // whole result on tiny chunks would be quadratic.
                    if (this.pendingBytes >= PROGRESS_LINE_BYTES) {
                        this.parts.push(this.pendingParts.join(''));
                        this.pendingParts = [];
                        this.pendingBytes = 0;
                    }
                    this.bytes += size;
                    this.lastCharacter = fragment.slice(-1);
                }
            }
            this.atLineStart = newline !== -1;
            offset = end;
        }
    }

    text(): string { return this.parts.join('') + this.pendingParts.join('') }
}
