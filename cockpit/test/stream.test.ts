/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { appendDisplayLine, BoundedLineDecoder, DIAGNOSTIC_BYTES, DiagnosticTail, TerminalCollector, utf8Bytes } from '../src/lib/stream.ts';

test('bounded framing handles chunk boundaries, CRLF and the final partial line', () => {
    const decoder = new BoundedLineDecoder(32);
    assert.deepEqual(decoder.push('fir'), []);
    assert.deepEqual(decoder.push('st\r\nsecond\nthi'), ['first', 'second']);
    assert.deepEqual(decoder.finish(), ['thi']);
    assert.deepEqual(decoder.finish(), []);
    assert.equal(decoder.droppedLines, 0);
});

test('oversized UTF-8 progress is dropped as a whole, never a forged suffix', () => {
    const decoder = new BoundedLineDecoder(8);
    assert.deepEqual(decoder.push('😀😀😀'), []);
    assert.deepEqual(decoder.push('Operation: ' + 'a'.repeat(32) + '\nok\n'), ['ok']);
    assert.equal(decoder.droppedLines, 1);
    assert.equal(utf8Bytes('aé😀'), Buffer.byteLength('aé😀'));
});

test('split surrogate pairs have their exact UTF-8 bound', () => {
    const decoder = new BoundedLineDecoder(4);
    assert.deepEqual(decoder.push('\ud83d'), []);
    assert.deepEqual(decoder.push('\ude00\n'), ['😀']);
    const collector = new TerminalCollector(5);
    collector.push('{\ud83d');
    collector.push('\ude00');
    assert.equal(collector.overflow, false);
    assert.equal(collector.text(), '{😀');
});

test('display arrays are bounded while the independent inspector sees early handles', () => {
    const decoder = new BoundedLineDecoder(64, 2);
    const inspected: string[] = [];
    assert.deepEqual(decoder.push('key\none\ntwo\nthree\n', line => inspected.push(line)), ['two', 'three']);
    assert.deepEqual(inspected, ['key', 'one', 'two', 'three']);
    assert.equal(decoder.droppedLines, 2);
});

test('diagnostic tail is bounded by UTF-8 bytes', () => {
    const tail = new DiagnosticTail(16);
    tail.push('x'.repeat(100));
    tail.push('😀'.repeat(100));
    assert.ok(utf8Bytes(tail.text()) <= 16);
});

test('terminal collector ignores arbitrary progress and preserves pretty JSON independently', () => {
    const collector = new TerminalCollector(128);
    collector.push('progress'.repeat(10000) + '\n');
    collector.push('{\n  "schema_version": ');
    collector.push('1\n}\n');
    assert.equal(collector.text(), '{\n  "schema_version": 1\n}\n');
    assert.equal(collector.overflow, false);
});

test('terminal overflow refuses rather than retaining a plausible suffix', () => {
    const collector = new TerminalCollector(16);
    collector.push('{"value":"' + 'x'.repeat(100));
    collector.push('"}\n');
    assert.equal(collector.overflow, true);
    assert.equal(collector.text(), '');
});

test('tiny native chunks retain one exact bounded terminal document', () => {
    const body = '{"value":"' + 'x'.repeat(40000) + '"}\n';
    const collector = new TerminalCollector(50000);
    for (const character of body)
        collector.push(character);
    assert.equal(collector.text(), body);
    assert.equal(collector.overflow, false);
});

test('UI tail evicts whole lines under both byte and row ceilings', () => {
    let rows: string[] = [];
    for (let index = 0; index < 200; index += 1)
        rows = appendDisplayLine(rows, String(index).padEnd(8192, 'x'));
    assert.ok(utf8Bytes(rows.join('\n')) <= DIAGNOSTIC_BYTES);
    assert.ok(rows.length < 200);
    assert.ok(rows[0].startsWith('193'));
    assert.ok(rows[rows.length - 1].startsWith('199'));
    assert.deepEqual(appendDisplayLine(['first', 'second'], 'third', 2), ['second', 'third']);
});

test('UI tail never turns an oversized line into a plausible handle suffix', () => {
    assert.deepEqual(appendDisplayLine(['previous'], 'x'.repeat(9000) + 'Operation: ' + 'a'.repeat(32)), ['previous']);
    let rows: string[] = [];
    for (let index = 0; index < 20; index += 1)
        rows = appendDisplayLine(rows, '😀'.repeat(2048));
    assert.ok(utf8Bytes(rows.join('\n')) <= DIAGNOSTIC_BYTES);
});
