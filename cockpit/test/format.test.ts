/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { formatBytes, formatDuration, formatHours, formatTimestamp, shortSha } from '../src/lib/format.ts';

test('bytes format in binary units', () => {
    assert.equal(formatBytes(0), '0 B');
    assert.equal(formatBytes(1023), '1023 B');
    assert.equal(formatBytes(12890456), '12.3 MiB');
    assert.equal(formatBytes(34287235629056), '31.2 TiB');
    assert.equal(formatBytes(null), '—');
    assert.equal(formatBytes(-1), '—');
});

test('timestamps and hours degrade to a dash, never to NaN', () => {
    assert.equal(formatTimestamp(null), '—');
    assert.equal(formatTimestamp('not a date'), '—');
    assert.notEqual(formatTimestamp('2026-07-27T22:08:47.413051Z'), '—');
    assert.equal(formatHours(32.077), '32.1 h');
    assert.equal(formatHours(undefined), '—');
});

test('durations format for the maintenance-window question', () => {
    assert.equal(formatDuration(12), '12 s');
    assert.equal(formatDuration(300), '5 min');
    assert.equal(formatDuration(12000), '3 h 20 min');
    assert.equal(formatDuration(null), '—');
    assert.equal(formatDuration(-1), '—');
});

test('shortSha truncates for display only', () => {
    assert.equal(shortSha('71034c5d8bde858ff824298bdedc65515b97d2b9'), '71034c5d8bde');
    assert.equal(shortSha(null), '—');
});
