/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { isReportName, isRunId, parseReportName } from '../src/lib/reports.ts';

test('observed report names parse to a start time and run id', () => {
    const parsed = parseReportName('20260727T104452Z-cccb23522c9a4d4d9520f9cc782670a6.json');
    assert.equal(parsed.runId, 'cccb23522c9a4d4d9520f9cc782670a6');
    assert.equal(parsed.startedAt?.toISOString(), '2026-07-27T10:44:52.000Z');
});

test('anything that is not a report name is rejected, not guessed at', () => {
    for (const name of [
        '../../../etc/shadow',
        'current.json',
        '20260727T104452Z-cccb23522c9a4d4d9520f9cc782670a6.json.bak',
        '20260727T104452Z-SHOUTING.json',
    ]) {
        assert.ok(!isReportName(name), name);
        assert.equal(parseReportName(name).runId, null, name);
    }
});

test('run ids are 32 lowercase hex characters', () => {
    assert.ok(isRunId('cccb23522c9a4d4d9520f9cc782670a6'));
    assert.ok(!isRunId('cccb2352'));
    assert.ok(!isRunId('CCCB23522C9A4D4D9520F9CC782670A6'));
});
