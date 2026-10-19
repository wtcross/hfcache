/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
    candidateAssessment, confirmedFingerprint, installConfiguration,
    prepareConfiguration,
} from '../src/lib/config-pipeline.ts';
import type { ConfigurationPorts } from '../src/lib/config-pipeline.ts';
import type { Envelope } from '../src/lib/envelope.ts';
import { extractFieldPath, parseConfig, selectorsNeedingPreview } from '../src/lib/config.ts';

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
            return envelope('plan', { repositories: [{ repository_id: 'org/model' }] });
        },
        install: async expected => { assert.deepEqual(expected, guard); calls.push('install') },
        confirm: async expected => { assert.equal(expected, guard.candidateContent); calls.push('confirm'); return envelope('config validate', { config_fingerprint: FINGERPRINT }) },
    };
    return { calls, guard, adapter };
}

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
        assert.equal(result.assessment.syntaxValid, true);
        assert.equal(result.assessment.fingerprint, FINGERPRINT);
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
    assert.equal(result.assessment.syntaxValid, true);
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
        assert.throws(() => confirmedFingerprint(result, FINGERPRINT), /Installation may have completed/);
});

test('confirmation failure never returns an installed-success object or silently reinstalls', async () => {
    const { calls, guard, adapter } = ports();
    const prepared = await prepareConfiguration(guard, adapter);
    assert.ok(prepared.proposal);
    adapter.confirm = async () => envelope('config validate', {}, 20);
    await assert.rejects(installConfiguration(prepared.proposal, adapter), /Installation may have completed/);
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
        await assert.rejects(installConfiguration(prepared.proposal, adapter), /Reload and validate the installed configuration/);
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
    adapter.preview = async (_selectors, captured) => { assert.deepEqual(captured, original); return envelope('plan', {}) };
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
            return envelope('plan', {});
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
    await assert.rejects(installConfiguration(prepared.proposal, adapter), /Installation may have completed/);
    assert.equal(confirmations, 1);
});
