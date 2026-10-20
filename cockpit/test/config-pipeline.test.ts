/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    candidateAssessment, confirmedFingerprint, confirmConfiguration, ConfigurationPipelineError,
    installConfiguration, PreparationSuperseded, prepareConfiguration,
} from '../src/lib/config-pipeline.ts';
import type { ConfigurationEvidence, ConfigurationPorts } from '../src/lib/config-pipeline.ts';
import type { Envelope } from '../src/lib/envelope.ts';
import { extractFieldPath, parseConfig, selectorsNeedingPreview } from '../src/lib/config.ts';
import { BoundaryError } from '../src/lib/failure.ts';
import { HostProfileError } from '../src/lib/host-profile.ts';

const FINGERPRINT = 'a'.repeat(64);
const BASE = 'schema_version=1\n[[repositories]]\nid="org/model"\ntype="model"\nrevision="main"\nenabled=false\n';
const CONTENT = BASE.replace('enabled=false', 'enabled=true');

function envelope(command: string, data: unknown, exitCode = 0): Envelope {
    return {
        schema_version: 1,
        command,
        run_id: 'b'.repeat(32),
        started_at: '2026-10-18T12:00:00.000000Z',
        completed_at: '2026-10-18T12:00:00.000000Z',
        exit_code: exitCode,
        outcome: exitCode === 0 ? 'success' : 'failed',
        data,
        warnings: [],
        errors: exitCode === 0
            ? []
            : [
                { code: 'HFCFG001', message: 'safe domain refusal', repository: null, context: {} },
            ],
    };
}

function validation(changes: Record<string, unknown> = {}, exitCode = 0): Envelope {
    return envelope('config validate', {
        valid: true,
        syntax_valid: true,
        authority_compatible: true,
        authority_mismatches: [],
        installed_policy_valid: true,
        config_fingerprint: FINGERPRINT,
        ...changes,
    }, exitCode);
}

function plannedRow(changes: Record<string, unknown> = {}): Record<string, unknown> {
    return {
        enabled: true,
        repository_type: 'model',
        repository_id: 'org/model',
        requested_revision: 'main',
        resolved_commit_sha: 'b'.repeat(40),
        upstream_state: 'available',
        file_count: 1,
        logical_bytes: 16,
        estimated_new_bytes: 16,
        projected_publication_bytes: 0,
        publication_mode: 'hardlink',
        ...changes,
    };
}

function planned(changes: Record<string, unknown> = {}): Envelope {
    return envelope('plan', { repositories: [plannedRow(changes)] });
}

function ports() {
    const calls: string[] = [];
    const guard = { candidateContent: CONTENT, installedContent: BASE };
    const adapter: ConfigurationPorts = {
        write: async expected => { assert.deepEqual(expected, guard); calls.push('write') },
        validate: async expected => { assert.deepEqual(expected, guard); calls.push('validate'); return validation() },
        preview: async (selectors, expected) => {
            assert.deepEqual(expected, guard);
            assert.deepEqual(selectors, ['model:org/model']);
            calls.push('preview');
            return planned();
        },
        install: async expected => { assert.deepEqual(expected, guard); calls.push('install') },
        confirm: async expected => { assert.equal(expected, guard.candidateContent); calls.push('confirm'); return envelope('config validate', { config_fingerprint: FINGERPRINT }) },
    };
    return { calls, guard, adapter };
}

test('host permission refusal before candidate write/install is classified without inventing host uncertainty', async () => {
    const { adapter, guard, calls } = ports();
    const deny = async () => { throw new HostProfileError('Trusted host profile refuses this effect.') };
    for (const stage of ['candidate-write', 'install'] as const) {
        const action = stage === 'candidate-write'
            ? prepareConfiguration(guard, { ...adapter, write: deny })
            : installConfiguration({ guard, fingerprint: FINGERPRINT }, { ...adapter, install: deny });
        await assert.rejects(action, failure => {
            assert.ok(failure instanceof ConfigurationPipelineError);
            assert.equal(failure.stage, stage);
            assert.equal(failure.cause?.category, 'access');
            assert.equal(failure.cause?.hostMutationUncertain, false);
            assert.deepEqual(failure.acknowledgedStages, []);
            return true;
        });
    }
    assert.deepEqual(calls, []);
});

test('compatible candidate follows guarded validation, required preview, install and exact confirmation', async () => {
    const { calls, guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.equal(prepared.blocked, null);
    assert.ok(prepared.proposal);
    assert.deepEqual(calls, ['write', 'validate', 'preview']);
    const result = await installConfiguration(prepared.proposal, adapter);
    assert.equal(result.fingerprint, FINGERPRINT);
    assert.equal(result.envelope.command, 'config validate');
    assert.deepEqual(calls, ['write', 'validate', 'preview', 'install', 'confirm']);
});

test('enable transition needs sizing even when repository revision is unchanged', () => {
    assert.deepEqual(selectorsNeedingPreview(parseConfig(BASE), parseConfig(CONTENT)), ['model:org/model']);
    assert.deepEqual(selectorsNeedingPreview(parseConfig(CONTENT), parseConfig(BASE)), []);
});

test('unchanged enabled repository needs no new sizing preview', async () => {
    const { adapter } = ports();
    const guard = { candidateContent: CONTENT, installedContent: CONTENT };
    const prepared = await prepareConfiguration(guard, {
        ...adapter,
        write: async () => {},
        validate: async () => validation(),
        preview: async () => { assert.fail('unnecessary preview') },
    });
    assert.ok(prepared.proposal);
    assert.equal(prepared.plan, null);
});

for (const field of ['storage.archive_root', 'storage.archive_id', 'hub.endpoint',
    'hub.token_mode', 'hub.expected_account', 'hub.credential_name']) {
    test(`syntax-valid changed ${field} cannot grant preview/install even with equal fingerprint`, async () => {
        const { calls, guard, adapter } = ports();
        adapter.validate = async () => validation({ authority_compatible: false, authority_mismatches: [field] });
        const result = await prepareConfiguration(guard, adapter);
        assert.equal(result.assessment?.syntaxValid, true);
        assert.equal(result.assessment?.fingerprint, FINGERPRINT);
        assert.equal(result.blocked, 'authority');
        assert.equal(result.proposal, null);
        assert.equal(result.plan, null);
        assert.deepEqual(calls, ['write']);
    });
}

test('valid candidate against invalid installed policy stays reviewable without install authority', async () => {
    const { guard, adapter } = ports();
    adapter.validate = async () => validation({ installed_policy_valid: false, authority_compatible: null });
    const result = await prepareConfiguration(guard, adapter);
    assert.equal(result.assessment?.syntaxValid, true);
    assert.equal(result.blocked, 'authority');
    assert.equal(result.proposal, null);
});

test('malformed candidate retains ordered domain errors without invoking preview or install', async () => {
    const { calls, guard, adapter } = ports();
    const failed = validation({
        valid: false,
        syntax_valid: false,
        authority_compatible: null,
        authority_mismatches: [],
        config_fingerprint: undefined
    }, 10);
    failed.errors.push({
        code: 'HFCFG004',
        message: 'second safe problem',
        repository: null,
        context: { location: 'storage.archive_id' }
    });
    adapter.validate = async () => failed;
    const result = await prepareConfiguration(guard, adapter);
    assert.equal(result.blocked, 'invalid');
    assert.equal(result.validation, failed);
    assert.equal(result.proposal, null);
    assert.deepEqual(calls, ['write']);
    assert.equal(extractFieldPath(failed.errors[1]), 'storage.archive_id');
});

for (const changes of [
    { syntax_valid: undefined }, { valid: 1 }, { authority_compatible: 'true' },
    { installed_policy_valid: 1 }, { authority_mismatches: ['caller_secret'] },
    { authority_mismatches: ['hub.endpoint', 'hub.endpoint'] },
    { config_fingerprint: null }, { config_fingerprint: 'not-a-fingerprint' },
    { authority_compatible: false, authority_mismatches: [] },
    { installed_policy_valid: false, authority_compatible: true },
]) {
    test('malformed or contradictory validation evidence is refused', () => {
        assert.throws(() => candidateAssessment(validation(changes)));
    });
}

for (const exitCode of [10, 20, 30, 40, 50]) {
    test(`failed preview exit ${exitCode} never becomes ready`, async () => {
        const { guard, adapter } = ports();
        const failure = envelope('plan', { work_may_continue: true, operation_id: 'c'.repeat(32) }, exitCode);
        adapter.preview = async () => failure;
        const result = await prepareConfiguration(guard, adapter);
        assert.equal(result.blocked, 'preview');
        assert.equal(result.plan, failure);
        assert.equal(result.proposal, null);
    });
}

test('confirmation requires exact expected fingerprint and successful installed validation', () => {
    for (const result of [
        envelope('config validate', {}, 10), envelope('config validate', {}, 0),
        envelope('config validate', { config_fingerprint: 'b'.repeat(64) }),
        envelope('status', { config_fingerprint: FINGERPRINT }),
    ])
        assert.throws(() => confirmedFingerprint(result, FINGERPRINT), /did not confirm the expected configuration fingerprint/);
});

test('confirmation failure never returns an installed-success object or silently reinstalls', async () => {
    const { calls, guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    const failed = envelope('config validate', {}, 20);
    adapter.confirm = async () => failed;
    const failure = await pipelineFailure(installConfiguration(prepared.proposal, adapter));
    assert.equal(failure.stage, 'installed-confirm');
    assert.equal(failure.envelope, failed);
    assert.equal(failure.cause, null);
    assert.match(failure.message, /returned a failed result/);
    assert.deepEqual(calls, ['write', 'validate', 'preview', 'install']);
});

test('failed install acknowledgment or lost installed validation requires explicit reload rather than retry', async () => {
    for (const stage of ['install', 'confirm'] as const) {
        const { guard, adapter } = ports();
        const prepared = await prepareConfiguration(guard, adapter);
        assert.ok(prepared.proposal);
        const calls: string[] = [];
        adapter.install = async () => {
            calls.push('install');
            if (stage === 'install')
                throw new Error('lost privileged process acknowledgment');
        };
        adapter.confirm = async () => { calls.push('confirm'); throw new Error('API unavailable') };
        const failure = await pipelineFailure(installConfiguration(prepared.proposal, adapter));
        assert.equal(failure.stage, stage === 'install' ? 'install' : 'installed-confirm');
        assert.ok(failure.cause instanceof BoundaryError);
        assert.equal(failure.cause.stage, failure.stage);
        assert.equal(failure.cause.hostMutationUncertain, true);
        assert.deepEqual(calls, stage === 'install' ? ['install'] : ['install', 'confirm']);
    }
});

test('captured candidate/base is immutable across async validation', async () => {
    const { guard, adapter } = ports();
    const original = { ...guard };
    adapter.write = async captured => {
        guard.candidateContent = 'changed draft';
        guard.installedContent = 'changed base';
        assert.deepEqual(captured, original);
    };
    adapter.validate = async captured => { assert.deepEqual(captured, original); return validation() };
    adapter.preview = async (_selectors, captured) => { assert.deepEqual(captured, original); return planned() };
    const result = await prepareConfiguration(guard, adapter);
    assert.deepEqual(result.proposal?.guard, original);
    assert.equal(Object.isFrozen(result.proposal?.guard), true);
});

for (const stage of ['validate', 'preview'] as const) {
    test(`editing during ${stage} invalidates late readiness and never authorizes install`, async () => {
        const { guard, adapter } = ports();
        let current = true;
        let resume: (() => void) | undefined;
        let entered: (() => void) | undefined;
        const waiting = new Promise<void>(resolve => { resume = resolve });
        const ready = new Promise<void>(resolve => { entered = resolve });
        let previewed = false;
        adapter.validate = async () => {
            if (stage === 'validate') {
                entered?.();
                await waiting;
            }
            return validation();
        };
        adapter.preview = async () => {
            previewed = true;
            if (stage === 'preview') {
                entered?.();
                await waiting;
            }
            return planned();
        };
        adapter.install = async () => assert.fail('edited evidence must not install');
        const preparing = prepareConfiguration(guard, adapter, () => current);
        await ready;
        current = false;
        resume?.();
        await assert.rejects(preparing, /Candidate changed during validation/);
        assert.equal(previewed, stage === 'preview');
    });
}

test('tag-only candidate preserves labels through the pipeline without sizing', async () => {
    const { adapter } = ports();
    const content = BASE + 'tags=["Coding", " coding "]\n';
    const guard = { candidateContent: content, installedContent: BASE };
    const calls: string[] = [];
    const configured: ConfigurationPorts = {
        ...adapter,
        write: async actual => { assert.deepEqual(actual, guard); calls.push('write') },
        validate: async actual => { assert.deepEqual(actual, guard); return validation() },
        preview: async () => { assert.fail('tag-only edit must not contact sizing') },
        install: async actual => { assert.equal(actual.candidateContent, content); calls.push('install') },
        confirm: async expected => {
            assert.equal(expected, content);
            calls.push('confirm');
            return envelope('config validate', { config_fingerprint: FINGERPRINT });
        },
    };
    const prepared = await prepareConfiguration(guard, configured);
    assert.ok(prepared.proposal);
    assert.equal(prepared.plan, null);
    assert.equal((await installConfiguration(prepared.proposal, configured)).fingerprint, FINGERPRINT);
    assert.deepEqual(calls, ['write', 'install', 'confirm']);
});

test('equal policy hash never bypasses changed installed tag bytes during confirmation', async () => {
    const { adapter, guard } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    let confirmations = 0;
    adapter.confirm = async expected => {
        assert.equal(expected, CONTENT);
        confirmations += 1;
        throw new Error('installed bytes differ only in tags, reload');
    };
    const failure = await pipelineFailure(installConfiguration(prepared.proposal, adapter));
    assert.equal(failure.stage, 'installed-confirm');
    assert.equal(failure.guard.candidateContent, CONTENT);
    assert.equal(failure.envelope, null);
    assert.equal(confirmations, 1);
});

async function pipelineFailure(result: Promise<unknown>): Promise<ConfigurationPipelineError> {
    try {
        await result;
    } catch (error) {
        assert.ok(error instanceof ConfigurationPipelineError);
        return error;
    }
    assert.fail('A refused pipeline must not return installation success');
}

for (const code of ['HFAPI003', 'HFAPI017', 'HFAPI018', 'HFAPI019', 'HFARG001', 'HFCFG001']) {
    test(`V11/V12 ${code} request refusal retains its Envelope without invented assessment fields`, async () => {
        const { calls, guard, adapter } = ports();
        const failed = envelope('config validate', {}, 10);
        failed.errors = [{ code, message: 'classified API/client refusal', repository: null, context: {} }];
        adapter.validate = async () => failed;
        const results: ConfigurationEvidence[] = [];
        const preparation = await prepareConfiguration(guard, adapter, () => true,
                                                       { onEvidence: result => results.push(result) });
        assert.equal(preparation.validation, failed);
        assert.equal(preparation.assessment, null);
        assert.equal(preparation.blocked, 'request');
        assert.equal(preparation.proposal, null);
        assert.equal(preparation.plan, null);
        assert.deepEqual(calls, ['write']);
        assert.ok(results.some(result => result.status === 'result' && result.envelope === failed));
    });
}

test('V09 no-preview candidate publishes validation evidence before readiness', async () => {
    const { adapter } = ports();
    const guard = { candidateContent: CONTENT, installedContent: CONTENT };
    const results: ConfigurationEvidence[] = [];
    let returned = false;
    const prepared = await prepareConfiguration(guard, {
        ...adapter,
        write: async () => {},
        validate: async () => validation(),
        preview: async () => assert.fail('No changed selectors need sizing'),
    }, () => true, {
        onEvidence: result => {
            assert.equal(returned, false);
            results.push(result);
        }
    });
    returned = true;
    assert.ok(prepared.proposal);
    assert.deepEqual(results.map(result => [result.stage, result.status]), [
        ['candidate-write', 'started'], ['candidate-write', 'acknowledged'],
        ['candidate-validate', 'started'], ['candidate-validate', 'acknowledged'],
        ['candidate-validate', 'result'],
    ]);
});

test('V10 malformed negative assessment stays strict while preserving its original errors', async () => {
    const { guard, adapter } = ports();
    const failed = validation({ valid: false, syntax_valid: false, authority_compatible: true }, 10);
    const results: ConfigurationEvidence[] = [];
    adapter.validate = async () => failed;
    const failure = await pipelineFailure(prepareConfiguration(guard, adapter, () => true,
                                                               { onEvidence: result => results.push(result) }));
    assert.equal(failure.envelope, failed);
    assert.equal(failure.cause?.category, 'protocol');
    assert.equal(failure.stage, 'candidate-validate');
    assert.ok(results.some(result => result.status === 'result' && result.envelope === failed));
    assert.equal(failure.proposal, null);
});

test('V09 malformed successful validation is refused with retained terminal evidence', async () => {
    const { calls, guard, adapter } = ports();
    const malformed = envelope('config validate', {});
    adapter.validate = async () => malformed;
    const failure = await pipelineFailure(prepareConfiguration(guard, adapter));
    assert.equal(failure.envelope, malformed);
    assert.equal(failure.cause?.category, 'protocol');
    assert.deepEqual(calls, ['write']);
});

test('V01/V18 preview bridge failure retains earlier validation, original handles and preview stage', async () => {
    const { calls, guard, adapter } = ports();
    const validated = validation();
    const original = new BoundaryError({ problem: 'reconnected' }, {
        stage: 'candidate-preview', idempotencyKey: 'original-preview-key', operationId: 'd'.repeat(32),
    });
    const results: ConfigurationEvidence[] = [];
    adapter.validate = async () => validated;
    adapter.preview = async () => {
        assert.ok(results.some(result => result.status === 'result' && result.envelope === validated));
        throw original;
    };
    const failure = await pipelineFailure(prepareConfiguration(guard, adapter, () => true,
                                                               { onEvidence: result => results.push(result) }));
    assert.equal(failure.stage, 'candidate-preview');
    assert.equal(failure.cause?.problem, 'reconnected');
    assert.equal(failure.cause?.category, 'bridge');
    assert.equal(failure.cause?.idempotencyKey, 'original-preview-key');
    assert.equal(failure.cause?.operationId, 'd'.repeat(32));
    assert.deepEqual(failure.acknowledgedStages, ['candidate-write', 'candidate-validate']);
    assert.deepEqual(failure.guard, guard);
    assert.deepEqual(calls, ['write']);
    assert.equal(results[results.length - 1]?.status, 'failed');
});

test('V17 lost write acknowledgement retains frozen intent and never validates, rewrites or removes', async () => {
    const { calls, guard, adapter } = ports();
    const expected = { ...guard };
    adapter.write = async captured => {
        calls.push('write');
        assert.deepEqual(captured, expected);
        guard.candidateContent = 'edited after transmission';
        guard.installedContent = 'changed after transmission';
        throw Object.assign(new Error('SYNTHETIC_SECRET'), { problem: 'disconnected' });
    };
    const failure = await pipelineFailure(prepareConfiguration(guard, adapter));
    assert.deepEqual(calls, ['write']);
    assert.deepEqual(failure.guard, expected);
    assert.ok(Object.isFrozen(failure.guard));
    assert.deepEqual(failure.acknowledgedStages, []);
    assert.equal(failure.cause?.problem, 'disconnected');
    assert.equal(failure.cause?.hostMutationUncertain, true);
    assert.ok(!failure.message.includes('SYNTHETIC_SECRET'));
});

test('V17 explicit revalidation of an inspected matching candidate skips every host write', async () => {
    const { guard, adapter } = ports();
    const calls: string[] = [];
    const results: ConfigurationEvidence[] = [];
    const prepared = await prepareConfiguration(guard, {
        ...adapter,
        write: async () => assert.fail('Read-only reconciliation cannot replay write'),
        validate: async expected => { assert.deepEqual(expected, guard); calls.push('validate'); return validation() },
        preview: async () => { calls.push('preview'); return planned() },
    }, () => true, { skipWrite: true, onEvidence: result => results.push(result) });
    assert.ok(prepared.proposal);
    assert.deepEqual(calls, ['validate', 'preview']);
    assert.ok(!results.some(result => result.stage === 'candidate-write'));
});

for (const stage of ['write', 'validate', 'preview'] as const) {
    test(`V08/V17 supersession during ${stage} preserves its already-started classified failure`, async () => {
        const { guard, adapter } = ports();
        let current = true;
        let resume!: () => void;
        let entered!: () => void;
        const waiting = new Promise<void>(resolve => { resume = resolve });
        const ready = new Promise<void>(resolve => { entered = resolve });
        const results: ConfigurationEvidence[] = [];
        const fail = async () => { entered(); await waiting; throw Object.assign(new Error('withheld'), { problem: 'reconnected' }) };
        if (stage === 'write') adapter.write = fail;
        if (stage === 'validate') adapter.validate = fail;
        if (stage === 'preview') adapter.preview = fail;
        const preparing = prepareConfiguration(guard, adapter, () => current,
                                               { onEvidence: result => results.push(result) });
        await ready;
        current = false;
        resume();
        const failure = await pipelineFailure(preparing);
        assert.equal(failure.cause?.problem, 'reconnected');
        assert.equal(results[results.length - 1]?.status, 'failed');
        assert.equal(results[results.length - 1]?.stage, `candidate-${stage}`);
    });
}

for (const stage of ['validate', 'preview'] as const) {
    test(`V08/V10 supersession during ${stage} preserves its negative terminal Envelope without readiness`, async () => {
        const { guard, adapter } = ports();
        let current = true;
        const failed = stage === 'validate'
            ? validation({ valid: false, syntax_valid: false, authority_compatible: null }, 10)
            : envelope('plan', {}, 20);
        const results: ConfigurationEvidence[] = [];
        const refuse = async () => { current = false; return failed };
        if (stage === 'validate') adapter.validate = refuse;
        else adapter.preview = refuse;
        await assert.rejects(prepareConfiguration(guard, adapter, () => current,
                                                  { onEvidence: result => results.push(result) }), PreparationSuperseded);
        assert.ok(results.some(result => result.status === 'result' && result.envelope === failed));
        assert.ok(!results.some(result => result.stage === 'install'));
    });
}

test('V18 preview callback seam forwards original key and ID independently of preparation readiness', async () => {
    const { guard, adapter } = ports();
    const notices: unknown[] = [];
    adapter.preview = async (_selectors, _guard, onNotice) => {
        onNotice?.({ kind: 'key', key: 'original-preview' });
        onNotice?.({ kind: 'operation', operationId: 'e'.repeat(32) });
        return envelope('plan', {}, 20);
    };
    const prepared = await prepareConfiguration(guard, adapter, () => true,
                                                { onPreviewNotice: notice => notices.push(notice) });
    assert.equal(prepared.proposal, null);
    assert.deepEqual(notices, [
        { kind: 'key', key: 'original-preview' },
        { kind: 'operation', operationId: 'e'.repeat(32) },
    ]);
});

test('V18 callback failure never interrupts or repeats the admitted preview', async () => {
    const { guard, adapter } = ports();
    let previews = 0;
    adapter.preview = async (_selectors, _guard, onNotice) => {
        previews += 1;
        onNotice?.({ kind: 'key', key: 'one-preview' });
        return planned();
    };
    const prepared = await prepareConfiguration(guard, adapter, () => true, {
        onEvidence: () => { throw new Error('display detached') },
        onPreviewNotice: () => { throw new Error('display detached') },
    });
    assert.ok(prepared.proposal);
    assert.equal(previews, 1);
});

test('V18 receipt evidence stays bounded across progress floods and acknowledgement snapshots stay immutable', async () => {
    const { guard, adapter } = ports();
    const results: ConfigurationEvidence[] = [];
    adapter.preview = async (_selectors, _guard, onNotice) => {
        onNotice?.({ kind: 'key', key: 'x'.repeat(129) });
        onNotice?.({ kind: 'operation', operationId: 'not-an-operation' });
        for (let index = 0; index < 1000; index += 1) {
            onNotice?.({ kind: 'progress', sequence: index + 1, phase: 'preview', message: 'bounded display event' });
            onNotice?.({ kind: 'key', key: 'original-preview' });
            onNotice?.({ kind: 'operation', operationId: 'e'.repeat(32) });
        }
        return planned();
    };
    const prepared = await prepareConfiguration(guard, adapter, () => true,
                                                { onEvidence: result => results.push(result) });
    assert.ok(prepared.proposal);
    const receipts = results.filter(result => result.status === 'notice');
    assert.equal(receipts.length, 2);
    assert.deepEqual(receipts.map(result => result.notice), [
        { kind: 'key', key: 'original-preview' },
        { kind: 'operation', operationId: 'e'.repeat(32) },
    ]);
    assert.deepEqual(results[0].acknowledgedStages, []);
    assert.deepEqual(results[results.length - 1]?.acknowledgedStages, ['candidate-write', 'candidate-validate', 'candidate-preview']);
    for (const result of results) {
        assert.ok(Object.isFrozen(result.acknowledgedStages));
        assert.ok(result.acknowledgedStages.length <= 3);
    }
});

test('V19 install failure preserves proposal, exact bytes and classified cause without proceeding to confirm', async () => {
    const { guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    const original = { ...guard };
    const transmitted = { ...prepared.proposal, guard: { ...prepared.proposal.guard } };
    const calls: string[] = [];
    const failure = await pipelineFailure(installConfiguration(transmitted, {
        install: async () => {
            calls.push('install');
            transmitted.guard.candidateContent = 'new draft after lost acknowledgement';
            throw Object.assign(new Error('withheld'), { problem: 'reconnected' });
        },
        confirm: async () => { calls.push('confirm'); return validation() },
    }));
    assert.equal(failure.stage, 'install');
    assert.deepEqual(failure.guard, original);
    assert.deepEqual(failure.proposal?.guard, original);
    assert.equal(failure.cause?.category, 'bridge');
    assert.equal(failure.cause?.hostMutationUncertain, true);
    assert.deepEqual(calls, ['install']);
});

test('V19 explicit confirmation after exact reconciliation never repeats installation', async () => {
    const { guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    const results: ConfigurationEvidence[] = [];
    let confirmations = 0;
    const result = await confirmConfiguration(prepared.proposal, {
        confirm: async expected => {
            confirmations += 1;
            assert.equal(expected, CONTENT);
            return validation();
        },
    }, { onEvidence: evidence => results.push(evidence) });
    assert.equal(result.fingerprint, FINGERPRINT);
    assert.equal(confirmations, 1);
    assert.ok(results.every(result => result.stage === 'installed-confirm'));
});

test('V20 confirmation process/postcheck failure keeps classified cause and acknowledged install', async () => {
    const { guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    const original = new BoundaryError({ exit_status: 1 }, {
        stage: 'installed-confirm', reason: 'process-postcheck',
    });
    adapter.confirm = async () => { throw original };
    const results: ConfigurationEvidence[] = [];
    const failure = await pipelineFailure(installConfiguration(prepared.proposal, adapter,
                                                               { onEvidence: result => results.push(result) }));
    assert.equal(failure.stage, 'installed-confirm');
    assert.equal(failure.cause?.category, 'process');
    assert.equal(failure.cause?.reason, 'process-postcheck');
    assert.equal(failure.cause?.exitStatus, 1);
    assert.deepEqual(failure.acknowledgedStages, ['install']);
    assert.equal(failure.envelope, null);
    assert.equal(results[results.length - 1]?.status, 'failed');
});

test('V20 confirmation failure Envelope is published before rejection without a fabricated boundary error', async () => {
    const { guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    const refused = envelope('config validate', {}, 10);
    refused.errors = [{ code: 'HFAPI003', message: 'writer capability required', repository: null, context: {} }];
    adapter.confirm = async () => refused;
    const results: ConfigurationEvidence[] = [];
    const failure = await pipelineFailure(installConfiguration(prepared.proposal, adapter,
                                                               { onEvidence: result => results.push(result) }));
    assert.equal(failure.envelope, refused);
    assert.equal(failure.cause, null);
    assert.deepEqual(failure.acknowledgedStages, ['install', 'installed-confirm']);
    assert.ok(results.some(result => result.status === 'result' && result.envelope === refused));
    assert.ok(!failure.message.includes('No valid terminal Envelope'));
});

test('V08/V20 changed session after apparent successful confirmation cannot return installation success', async () => {
    const { guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    let current = true;
    const confirmed = validation();
    adapter.confirm = async () => { current = false; return confirmed };
    const results: ConfigurationEvidence[] = [];
    const failure = await pipelineFailure(installConfiguration(prepared.proposal, adapter, {
        isCurrent: () => current, onEvidence: result => results.push(result),
    }));
    assert.equal(failure.stage, 'installed-confirm');
    assert.equal(failure.cause?.problem, 'reconnected');
    assert.equal(failure.envelope, confirmed);
    assert.ok(results.some(result => result.status === 'result' && result.envelope === confirmed));
});

for (const data of [null, {}, { repositories: null }, { repositories: {} }, { repositories: [] },
    { repositories: [null] }, { repositories: [{ repository_id: 'org/model' }] },
    { repositories: [plannedRow(), plannedRow()] }]) {
    test('V09/V18 malformed or incomplete successful sizing cannot authorize installation', async () => {
        const { guard, adapter } = ports();
        const malformed = envelope('plan', data);
        adapter.preview = async () => malformed;
        const failure = await pipelineFailure(prepareConfiguration(guard, adapter));
        assert.equal(failure.stage, 'candidate-preview');
        assert.equal(failure.envelope, malformed);
        assert.equal(failure.cause?.category, 'protocol');
        assert.equal(failure.proposal, null);
    });
}

for (const changes of [
    { enabled: false }, { repository_type: 'dataset' }, { repository_id: 'other/model' },
    { requested_revision: 'other-branch' }, { resolved_commit_sha: null }, { resolved_commit_sha: 'b'.repeat(39) },
    { upstream_state: 'unknown' }, { publication_mode: 'copy' }, { projected_publication_bytes: 16 },
    ...['file_count', 'logical_bytes', 'estimated_new_bytes', 'projected_publication_bytes']
            .flatMap(field => [null, -1, 0.5, Number.MAX_SAFE_INTEGER + 1, '16'].map(value => ({ [field]: value }))),
]) {
    test('V09/V18 inconsistent successful sizing retains its evidence and refuses readiness', async () => {
        const { guard, adapter } = ports();
        const malformed = planned(changes);
        adapter.preview = async () => malformed;
        const failure = await pipelineFailure(prepareConfiguration(guard, adapter));
        assert.equal(failure.envelope, malformed);
        assert.equal(failure.stage, 'candidate-preview');
        assert.equal(failure.cause?.category, 'protocol');
    });
}

test('V18 partial failed sizing preserves legitimate null fields without successful-shape parsing', async () => {
    const { guard, adapter } = ports();
    const partial = envelope('plan', {
        repositories: [plannedRow({
            resolved_commit_sha: null,
            upstream_state: 'missing',
            file_count: null,
            logical_bytes: null,
            estimated_new_bytes: null,
            projected_publication_bytes: null,
        })]
    }, 30);
    adapter.preview = async () => partial;
    const prepared = await prepareConfiguration(guard, adapter);
    assert.equal(prepared.blocked, 'preview');
    assert.equal(prepared.plan, partial);
    assert.equal(prepared.proposal, null);
});

test('V09 copy-mode sizing uses the captured mode and permits exact zero-sized results', async () => {
    const { adapter } = ports();
    const guard = { installedContent: BASE, candidateContent: CONTENT + '\n[storage]\npublication_mode="copy"\n' };
    const copyPorts: ConfigurationPorts = {
        ...adapter,
        write: async () => {},
        validate: async () => validation(),
        preview: async () => planned({ publication_mode: 'copy', projected_publication_bytes: 16 }),
    };
    assert.ok((await prepareConfiguration(guard, copyPorts)).proposal);
    copyPorts.preview = async () => planned({
        publication_mode: 'copy',
        file_count: 0,
        logical_bytes: 0,
        estimated_new_bytes: 0,
        projected_publication_bytes: 0
    });
    assert.ok((await prepareConfiguration(guard, copyPorts)).proposal);
    copyPorts.preview = async () => planned({ publication_mode: 'copy', projected_publication_bytes: 0 });
    assert.equal((await pipelineFailure(prepareConfiguration(guard, copyPorts))).stage, 'candidate-preview');
});

test('V09 default-enabled new repository requires complete sizing for its default main revision', async () => {
    const { adapter } = ports();
    const guard = {
        installedContent: 'schema_version=1\n',
        candidateContent: 'schema_version=1\n[[repositories]]\nid="org/model"\ntype="model"\n'
    };
    let previews = 0;
    const prepared = await prepareConfiguration(guard, {
        ...adapter,
        write: async () => {},
        validate: async () => validation(),
        preview: async selectors => { previews += 1; assert.deepEqual(selectors, ['model:org/model']); return planned() },
    });
    assert.equal(previews, 1);
    assert.ok(prepared.proposal);
});

test('V09 required sizing matches every exact selector and revision without requiring response order', async () => {
    const { adapter } = ports();
    const second = '\n[[repositories]]\nid="org/dataset"\ntype="dataset"\nrevision="release"\nenabled=true\n';
    const guard = { installedContent: BASE, candidateContent: CONTENT + second };
    const secondRow = plannedRow({ repository_id: 'org/dataset', repository_type: 'dataset', requested_revision: 'release' });
    const selected: ConfigurationPorts = {
        ...adapter,
        write: async () => {},
        validate: async () => validation(),
        preview: async () => envelope('plan', { repositories: [secondRow, plannedRow()] }),
    };
    assert.ok((await prepareConfiguration(guard, selected)).proposal);
    for (const rows of [[plannedRow()], [plannedRow(), plannedRow()], [secondRow, plannedRow({ repository_id: 'org/other' })]]) {
        selected.preview = async () => envelope('plan', { repositories: rows });
        assert.equal((await pipelineFailure(prepareConfiguration(guard, selected))).stage, 'candidate-preview');
    }
});

test('V09 sizing for an immutable requested commit must resolve that same commit', async () => {
    const { adapter } = ports();
    const requested = 'a'.repeat(40);
    const guard = { installedContent: BASE, candidateContent: CONTENT.replace('revision="main"', `revision="${requested}"`) };
    const configured: ConfigurationPorts = {
        ...adapter,
        write: async () => {},
        validate: async () => validation(),
        preview: async () => planned({ requested_revision: requested }),
    };
    const failure = await pipelineFailure(prepareConfiguration(guard, configured));
    assert.equal(failure.stage, 'candidate-preview');
    assert.equal(failure.cause?.category, 'protocol');
    configured.preview = async () => planned({ requested_revision: requested, resolved_commit_sha: requested });
    assert.ok((await prepareConfiguration(guard, configured)).proposal);
});
