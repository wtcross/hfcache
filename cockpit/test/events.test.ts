/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { EVENTS, interpretEvent, parseLogfmt } from '../src/lib/events.ts';

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
    assert.equal(EVENTS.length, 13);
    for (const name of ['run.started', 'preflight.failed', 'publication.completed', 'run.completed']) {
        assert.ok((EVENTS as readonly string[]).includes(name), name);
    }
});
