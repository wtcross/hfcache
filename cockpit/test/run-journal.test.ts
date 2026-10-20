/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    collectRunJournal, JournalReadError, runJournalArgv,
    RUN_JOURNAL_BYTES, RUN_JOURNAL_DEADLINE_MS, RUN_JOURNAL_LINES,
    RUN_JOURNAL_LINE_BYTES, RUN_JOURNAL_RAW_BYTES,
} from '../src/lib/run-journal.ts';
import type { JournalDeadline, JournalProcess, RunJournal } from '../src/lib/run-journal.ts';
import { utf8Bytes } from '../src/lib/stream.ts';

const ID = 'a'.repeat(32);
const OTHER = 'b'.repeat(32);
const LINE = `event=run.started level=info run_id=${ID}`;

function controlled() {
    let receive: (chunk: string) => void = () => undefined;
    let complete!: () => void;
    let fail!: (failure: unknown) => void;
    const promise = new Promise<void>((resolve, reject) => { complete = resolve; fail = reject });
    let closes = 0;
    const process: JournalProcess = Object.assign(promise, {
        stream: (callback: (chunk: string) => void) => { receive = callback },
        close: (problem?: string) => {
            assert.equal(problem, 'cancelled');
            closes += 1;
            fail({ problem: 'cancelled' });
        },
    });
    return { process, emit: (chunk: string) => receive(chunk), resolve: complete, reject: fail, closes: () => closes };
}

function clock() {
    let tick: () => void = () => undefined;
    let stopped = 0;
    const start: JournalDeadline = (callback, milliseconds) => {
        assert.equal(milliseconds, RUN_JOURNAL_DEADLINE_MS);
        tick = callback;
        return () => { stopped += 1 };
    };
    return { start, tick: () => tick(), stopped: () => stopped };
}

function bounds(result: RunJournal) {
    assert.ok(result.lines.length <= RUN_JOURNAL_LINES);
    assert.ok(utf8Bytes(result.lines.join('\n')) <= RUN_JOURNAL_BYTES);
    assert.ok(result.lines.every(line => utf8Bytes(line) <= RUN_JOURNAL_LINE_BYTES));
    assert.ok(Object.isFrozen(result));
    assert.ok(Object.isFrozen(result.lines));
    assert.ok(Object.isFrozen(result.truncationReasons));
}

test('V44/V45 exact fixed journal argv has no archive path, shell, user manager or dynamic selectors', () => {
    assert.deepEqual(runJournalArgv(ID), [
        'timeout', '--signal=TERM', '--kill-after=1s', '5s',
        'journalctl', '--quiet', '--no-pager', '--output=cat', '--reverse',
        '--since=-7days', '--lines=201', '--case-sensitive=yes',
        `--grep=(^|[[:space:]])run_id=${ID}([[:space:]]|$)`,
        '_SYSTEMD_UNIT=hfcache-sync.service', '_SYSTEMD_UNIT=hfcache-verify.service',
        '+', '_SYSTEMD_USER_UNIT=hfcache-api.service', '_SYSTEMD_USER_UNIT=hfcache-verification.service',
    ]);
    for (const invalid of ['', '../etc/shadow', '--help', ID.toUpperCase(), ID + 'a', 'https://example.invalid/', '$(' + ID + ')']) {
        let spawned = 0;
        assert.throws(() => collectRunJournal(invalid, () => { spawned += 1; return controlled().process }), JournalReadError);
        assert.equal(spawned, 0);
    }
});

test('V45/V51 actual streamed process projects only the exact authoritative closed prefix', async () => {
    const proc = controlled();
    const timer = clock();
    const pending = collectRunJournal(ID, () => proc.process, timer.start);
    const secret = 'SYNTHETIC_JOURNAL_CREDENTIAL';
    proc.emit(`${LINE} message="${secret}" token=${secret}\n`);
    proc.emit(`event=repository.failed level=error run_id=${ID} repository=${secret}\n`);
    proc.emit(`event=run.completed level=info run_id=${ID}x\n`);
    proc.emit(`event=run.completed level=info run_id=${OTHER}\n`);
    proc.emit(`message="run_id=${ID}" event=run.started level=info\n`);
    proc.emit(`event=unknown.event level=info run_id=${ID}\n`);
    proc.emit(`event=run.started level=info run_id=${ID} message=unsafe\u001b\n`);
    proc.resolve();
    const result = await pending;
    assert.deepEqual(result.lines, [LINE, `event=repository.failed level=error run_id=${ID}`]);
    assert.equal(result.truncated, true);
    assert.deepEqual(result.truncationReasons, ['filtered-lines']);
    assert.ok(!JSON.stringify(result).includes(secret));
    assert.equal(proc.closes(), 0);
    assert.equal(timer.stopped(), 1);
    bounds(result);
});

test('V45 empty journal is a bounded observed empty diagnostic, including final chunk framing', async () => {
    for (const body of ['', LINE]) {
        const proc = controlled();
        const pending = collectRunJournal(ID, () => proc.process, clock().start);
        if (body !== '') proc.emit(body);
        proc.resolve();
        const result = await pending;
        assert.deepEqual(result.lines, body === '' ? [] : [LINE]);
        assert.equal(result.truncated, false);
        bounds(result);
    }
});

test('V45 one oversized line is discarded through newline before later correlated events', async () => {
    const proc = controlled();
    const pending = collectRunJournal(ID, () => proc.process, clock().start);
    proc.emit(LINE + ' x'.repeat(RUN_JOURNAL_LINE_BYTES));
    proc.emit('\n' + LINE.slice(0, 10));
    proc.emit(LINE.slice(10) + '\n');
    proc.resolve();
    const result = await pending;
    assert.deepEqual(result.lines, [LINE]);
    assert.ok(result.truncationReasons.includes('oversized-line'));
    bounds(result);
});

test('V45 newest-first 201st entry closes only the owned diagnostic and explicitly truncates', async () => {
    const proc = controlled();
    const pending = collectRunJournal(ID, () => proc.process, clock().start);
    const newest = `event=run.completed level=info run_id=${ID}`;
    const oldest = `event=preflight.failed level=error run_id=${ID}`;
    proc.emit(newest + '\n' + (LINE + '\n').repeat(RUN_JOURNAL_LINES - 1) + oldest + '\n');
    const result = await pending;
    assert.equal(result.lines.length, RUN_JOURNAL_LINES);
    assert.equal(result.lines[0], newest);
    assert.equal(result.lines[result.lines.length - 1], LINE);
    assert.ok(!result.lines.includes(oldest));
    assert.deepEqual(result.truncationReasons, ['line-limit']);
    assert.equal(proc.closes(), 1);
    proc.emit(LINE + '\n');
    assert.equal(result.lines.length, RUN_JOURNAL_LINES);
    bounds(result);
});

test('V45 raw transport cap refuses an oversized callback without retaining arbitrary bytes', async () => {
    for (const chunk of ['x'.repeat(RUN_JOURNAL_RAW_BYTES + 1), 'é'.repeat(RUN_JOURNAL_RAW_BYTES / 2 + 1)]) {
        const proc = controlled();
        const pending = collectRunJournal(ID, () => proc.process, clock().start);
        proc.emit(LINE + '\n');
        proc.emit(chunk);
        const result = await pending;
        assert.deepEqual(result.lines, [LINE]);
        assert.deepEqual(result.truncationReasons, ['raw-byte-limit']);
        assert.equal(proc.closes(), 1);
        bounds(result);
    }
});

test('V45 client deadline closes only the journal and exposes bounded partial timeout evidence', async () => {
    const proc = controlled();
    const timer = clock();
    const pending = collectRunJournal(ID, () => proc.process, timer.start);
    proc.emit(LINE + '\n');
    timer.tick();
    await assert.rejects(pending, error => {
        assert.ok(error instanceof JournalReadError);
        assert.equal(error.stage, 'journal-read');
        assert.equal(error.category, 'bridge');
        assert.equal(error.problem, 'timeout');
        assert.equal(error.hostMutationUncertain, false);
        assert.deepEqual(error.partial.lines, [LINE]);
        assert.deepEqual(error.partial.truncationReasons, ['deadline']);
        bounds(error.partial);
        return true;
    });
    assert.equal(proc.closes(), 1);
    assert.equal(timer.stopped(), 1);
});

test('V45 a deadline or failed process never promotes an incomplete frame to a complete event', async () => {
    for (const timeout of [false, true]) {
        const proc = controlled();
        const timer = clock();
        const pending = collectRunJournal(ID, () => proc.process, timer.start);
        proc.emit(LINE);
        if (timeout)
            timer.tick();
        else
            proc.reject({ problem: 'reconnected' });
        await assert.rejects(pending, error => {
            assert.ok(error instanceof JournalReadError);
            assert.deepEqual(error.partial.lines, []);
            return true;
        });
    }
});

test('V45/V51 journal rejection preserves original safe process or bridge facts independently of partial lines', async () => {
    for (const [failure, category] of [
        [{ problem: 'reconnected', exit_status: 17, message: 'SYNTHETIC_JOURNAL_CREDENTIAL' }, 'bridge'],
        [{ problem: 'access-denied', message: 'SYNTHETIC_JOURNAL_CREDENTIAL' }, 'access'],
        [{ exit_status: 124, message: 'SYNTHETIC_JOURNAL_CREDENTIAL' }, 'process'],
        [{ problem: 'not-found', message: 'SYNTHETIC_JOURNAL_CREDENTIAL' }, 'launcher'],
    ] as const) {
        const proc = controlled();
        const pending = collectRunJournal(ID, () => proc.process, clock().start);
        proc.emit(LINE + '\n');
        proc.reject(failure);
        await assert.rejects(pending, error => {
            assert.ok(error instanceof JournalReadError);
            assert.equal(error.category, category);
            assert.equal(error.problem, 'problem' in failure ? failure.problem : undefined);
            assert.equal(error.exitStatus, 'exit_status' in failure ? failure.exit_status : undefined);
            assert.equal(error.hostMutationUncertain, false);
            assert.deepEqual(error.partial.lines, [LINE]);
            assert.equal(error.partial.truncationReasons.includes('deadline'), error.exitStatus === 124);
            assert.ok(!JSON.stringify(error).includes('SYNTHETIC_JOURNAL_CREDENTIAL'));
            assert.ok(!error.message.includes('SYNTHETIC_JOURNAL_CREDENTIAL'));
            bounds(error.partial);
            return true;
        });
        assert.equal(proc.closes(), 0);
    }
});

test('V45 synchronous launcher or streaming failure is classified and never retries', async () => {
    let spawned = 0;
    await assert.rejects(collectRunJournal(ID, () => {
        spawned += 1;
        throw Object.assign(new Error('SYNTHETIC_JOURNAL_CREDENTIAL'), { problem: 'not-found' });
    }, clock().start), error => error instanceof JournalReadError && error.category === 'launcher');
    assert.equal(spawned, 1);
    const proc = controlled();
    proc.process.stream = () => { throw Object.assign(new Error('SYNTHETIC_JOURNAL_CREDENTIAL'), { problem: 'reconnected' }) };
    await assert.rejects(collectRunJournal(ID, () => proc.process, clock().start), error =>
        error instanceof JournalReadError && error.problem === 'reconnected');
    assert.equal(proc.closes(), 1);
});

test('V51 hostile rejection properties are never invoked or echoed', async () => {
    let reads = 0;
    const failure = Object.create(null);
    Object.defineProperty(failure, 'exit_status', { get: () => { reads += 1; throw new Error('SYNTHETIC_JOURNAL_CREDENTIAL') } });
    Object.defineProperty(failure, 'message', { get: () => { reads += 1; throw new Error('SYNTHETIC_JOURNAL_CREDENTIAL') } });
    const proc = controlled();
    const pending = collectRunJournal(ID, () => proc.process, clock().start);
    proc.reject(failure);
    await assert.rejects(pending, error => {
        assert.ok(error instanceof JournalReadError);
        assert.equal(error.exitStatus, undefined);
        assert.ok(!JSON.stringify(error).includes('SYNTHETIC_JOURNAL_CREDENTIAL'));
        return true;
    });
    assert.equal(reads, 0);
});
