/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { EVENTS, interpretEvent, interpretOperationLine, parseLogfmt } from '../src/lib/events.ts';

/* Real lines from docs/operations.md §4, observed on the deployment. */
const RESOLVED = 'event=repository.resolved level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 ' +
    'commit_sha=71034c5d8bde858ff824298bdedc65515b97d2b9 ' +
    'repository=model:hf-internal-testing/tiny-random-gpt2 requested_revision=main';
const COMPLETED = 'event=run.completed level=info run_id=cccb23522c9a4d4d9520f9cc782670a6 ' +
    'command=sync downloaded_bytes=0 exit_code=0 hashed_bytes=0 outcome=success ' +
    'report=runs/20260727T104452Z-cccb23522c9a4d4d9520f9cc782670a6.json repositories=2 reused_bytes=0';

test('observed journal lines interpret with run id and repository', () => {
    const resolved = interpretEvent(RESOLVED);
    assert.ok(resolved);
    assert.equal(resolved.event, 'repository.resolved');
    assert.equal(resolved.runId, 'cccb23522c9a4d4d9520f9cc782670a6');
    assert.equal(resolved.repository, 'model:hf-internal-testing/tiny-random-gpt2');

    const completed = interpretEvent(COMPLETED);
    assert.ok(completed);
    assert.equal(completed.event, 'run.completed');
    assert.equal(completed.fields.report, 'runs/20260727T104452Z-cccb23522c9a4d4d9520f9cc782670a6.json');
});

test('quoted values with spaces unquote', () => {
    const fields = parseLogfmt('event=verification.completed command="verify --full" findings=0');
    assert.ok(fields);
    assert.equal(fields.command, 'verify --full');
});

test('a name outside the closed vocabulary is ignored, not an error', () => {
    assert.equal(interpretEvent('event=totally.new_event run_id=abc'), null);
});

test('non-logfmt journal lines are ignored', () => {
    assert.equal(interpretEvent('Starting hfcache-sync.service - Synchronize configured repositories...'), null);
    assert.equal(interpretEvent(''), null);
});

test('the vocabulary is the closed §24 set', () => {
    assert.equal(EVENTS.length, 17);
    for (const name of [
        'run.started',
        'preflight.failed',
        'repository.queued',
        'hash.started',
        'hash.completed',
        'publication.completed',
        'quarantine.cleaned',
        'run.completed',
    ]) {
        assert.ok((EVENTS as readonly string[]).includes(name), name);
    }
});

test('API client progress and safety handles are distinct from journal events', () => {
    assert.deepEqual(interpretOperationLine('Idempotency key: cli.key-1'), { kind: 'key', key: 'cli.key-1' });
    assert.deepEqual(interpretOperationLine('Operation: ' + 'a'.repeat(32)), { kind: 'operation', operationId: 'a'.repeat(32) });
    assert.deepEqual(interpretOperationLine('[42] running: Verifying files'), {
        kind: 'progress', sequence: 42, phase: 'running', message: 'Verifying files',
    });
    assert.deepEqual(interpretOperationLine('Event history gap; retained events start at 12'), {
        kind: 'gap', oldestSequence: 12,
    });
    assert.deepEqual(interpretOperationLine('Accepted work may continue; reconnect using the retained handles'), { kind: 'continuing' });
    assert.equal(interpretEvent('[42] running: Verifying files'), null);
    assert.equal(interpretOperationLine(RESOLVED), null);
});

test('malformed, oversized, control-bearing and unsafe numeric notices are ignored', () => {
    for (const line of [
        'Operation: ../other', 'Operation: ' + 'A'.repeat(32),
        'Idempotency key: space key', 'Idempotency key: ' + 'x'.repeat(129),
        '[9007199254740992] running: Too large', '[0] running: Zero',
        '[1] running: bad\u001b[31m', '[1] running: ' + 'x'.repeat(8192),
        'Event history gap; retained events start at 9007199254740992',
    ])
        assert.equal(interpretOperationLine(line), null, line.slice(0, 100));
});
