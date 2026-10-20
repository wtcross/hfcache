/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { OperationAuthorityError, operationAuthority } from '../src/lib/operation-authority.ts';
import { createOperationRegistry, OperationRegistryError } from '../src/lib/operation-registry.ts';
import type { Envelope } from '../src/lib/envelope.ts';

const HOST = 'fixture-host.example.test';
const ARCHIVE = '12345678-1234-1234-1234-123456789abc';
const METADATA = {
    metadata_schema_version: 1,
    profile_fingerprint: 'a'.repeat(64),
    authority_fingerprint: 'b'.repeat(64),
    endpoint: 'unix:/run/hfcache/api/api.sock',
    credential_class: 'rest-writer',
    archive_id: ARCHIVE,
    instance_id: 'c'.repeat(32),
};

function envelope(data: unknown = { ...METADATA }): Envelope {
    return {
        schema_version: 1,
        command: 'client describe',
        run_id: 'd'.repeat(32),
        started_at: '2026-10-19T12:00:00.000000Z',
        completed_at: '2026-10-19T12:00:01.000000Z',
        exit_code: 0,
        outcome: 'success',
        data,
        warnings: [],
        errors: []
    };
}

function refuses(value: Envelope, host = HOST): void {
    assert.throws(() => operationAuthority(value, host), error => {
        assert.ok(error instanceof OperationAuthorityError);
        assert.equal(error.name, 'OperationAuthorityError');
        assert.equal(error.envelope, value);
        assert.ok(!error.message.includes('SYNTHETIC_SECRET'));
        return true;
    });
}

test('V25/V51 client describe maps only current metadata into an immutable recovery scope', () => {
    const data = { ...METADATA };
    const scope = operationAuthority(envelope(data), HOST);
    assert.deepEqual(scope, {
        host: HOST,
        profile: METADATA.profile_fingerprint,
        authorityFingerprint: METADATA.authority_fingerprint,
        endpoint: METADATA.endpoint,
        credentialClass: 'rest-writer',
        archiveId: ARCHIVE,
        instanceId: METADATA.instance_id,
    });
    assert.ok(Object.isFrozen(scope));
    data.endpoint = 'unix:/changed.sock';
    data.archive_id = 'ffffffff-ffff-ffff-ffff-ffffffffffff';
    assert.equal(scope.endpoint, METADATA.endpoint);
    assert.equal(scope.archiveId, ARCHIVE);
});

test('V25 an unconfirmed archive remains null and cannot prepare any keyed operation', () => {
    const scope = operationAuthority(envelope({ ...METADATA, archive_id: null }), HOST);
    assert.equal(scope.archiveId, null);
    const registry = createOperationRegistry({
        storage: { getItem: () => null, setItem: () => assert.fail('Unknown archive must never persist a submission') },
        keyFactory: () => assert.fail('Unknown archive must never create an original key')
    });
    assert.throws(() => registry.prepare('prune-apply', scope), error => {
        assert.ok(error instanceof OperationRegistryError);
        assert.equal(error.reason, 'scope');
        return true;
    });
    assert.equal(registry.snapshot().records.length, 0);
});

test('V25 metadata retains reader and writer credential classes without inventing privileges', () => {
    for (const credential_class of ['rest-writer', 'rest-reader']) {
        assert.equal(operationAuthority(envelope({ ...METADATA, credential_class }), HOST).credentialClass,
                     credential_class);
    }
});

test('V25 authority failures preserve the exact classified Envelope before metadata interpretation', () => {
    const failed = envelope({ token: 'SYNTHETIC_SECRET' });
    failed.command = 'capabilities';
    failed.exit_code = 10;
    failed.outcome = 'failed';
    failed.errors = [{
        code: 'HFAPI002',
        message: 'original authentication refusal',
        repository: null,
        context: { location: 'writer profile' }
    }];
    const before = JSON.stringify(failed);
    assert.throws(() => operationAuthority(failed, HOST), error => {
        assert.ok(error instanceof OperationAuthorityError);
        assert.equal(error.envelope, failed);
        assert.equal(error.envelope.command, 'capabilities');
        assert.equal(error.envelope.errors[0].code, 'HFAPI002');
        assert.equal(error.envelope.run_id, failed.run_id);
        assert.ok(error.message.includes('No operation was submitted'));
        assert.ok(!error.message.includes('SYNTHETIC_SECRET'));
        return true;
    });
    assert.equal(JSON.stringify(failed), before);
});

test('V25/V51 unknown metadata fields and secret-bearing extras are refused', () => {
    for (const field of ['token', 'authorization', 'candidate', 'raw_config', 'selected_settings', 'future_metadata'])
        refuses(envelope({ ...METADATA, [field]: 'SYNTHETIC_SECRET' }));
    const missing = { ...METADATA } as Record<string, unknown>;
    delete missing.archive_id;
    refuses(envelope(missing));
    const inherited = Object.create({ instance_id: METADATA.instance_id }) as Record<string, unknown>;
    Object.assign(inherited, METADATA);
    delete inherited.instance_id;
    refuses(envelope(inherited));
    refuses(envelope(JSON.parse(JSON.stringify(METADATA).replace(/}$/, ',"__proto__":"SYNTHETIC_SECRET"}'))));
});

test('V25 malformed containers and a different successful command provide no authority', () => {
    for (const value of [null, [], '', 'SYNTHETIC_SECRET', 1, false])
        refuses(envelope(value));
    const wrongCommand = envelope();
    wrongCommand.command = 'version';
    refuses(wrongCommand);
});

test('V25 unknown schema, identity formats and credential classes provide no authority', () => {
    const invalid: Record<string, unknown[]> = {
        metadata_schema_version: [0, 2, '1', null],
        profile_fingerprint: ['', 'a'.repeat(63), 'A'.repeat(64), 'SYNTHETIC_SECRET', null],
        authority_fingerprint: ['', 'b'.repeat(65), 'B'.repeat(64), {}, null],
        credential_class: ['', 'writer', 'mcp-reader', 'root', 'rest-writer\n', null],
        archive_id: ['', 'unconfirmed', '1234', ARCHIVE.toUpperCase(), 123],
        instance_id: ['', 'c'.repeat(31), 'C'.repeat(32), 'c'.repeat(33), null],
    };
    for (const [field, values] of Object.entries(invalid)) {
        for (const value of values)
            refuses(envelope({ ...METADATA, [field]: value }));
    }
    for (const host of ['', '-option', '../host', 'host;SYNTHETIC_SECRET', 'host\nname', 'a'.repeat(256)])
        refuses(envelope(), host);
});

test('V25 safe endpoint formats are presentation metadata rather than browser-selected argv', () => {
    for (const endpoint of [
        'unix:/run/hfcache/api/api.sock',
        'unix:/run/user/981/hfcache.sock',
        'https://api.example.test',
        'https://api.example.test:9443/prefix',
        'http://localhost:8080',
        'http://127.0.0.1:8080',
        'http://[::1]:8080',
    ])
        assert.equal(operationAuthority(envelope({ ...METADATA, endpoint }), HOST).endpoint, endpoint);
});

test('V25/V51 credentials, remote cleartext and unsafe endpoint syntax are refused', () => {
    for (const endpoint of [
        '', 'unix:relative.sock', 'unix:/', 'unix:/run//api.sock', 'unix:/run/../api.sock',
        'unix:/run/./api.sock', 'unix:/run/api.sock/', 'unix:/run/api.sock\0',
        'unix:/run/api.sock\n', 'unix:/run/SYNTHETIC_SECRET sock',
        'https://user:SYNTHETIC_SECRET@api.example.test',
        'https://api.example.test?token=SYNTHETIC_SECRET',
        'https://api.example.test#SYNTHETIC_SECRET',
        'https://api.example.test\\SYNTHETIC_SECRET',
        'http://api.example.test', 'ftp://api.example.test', 'javascript:SYNTHETIC_SECRET',
        'https://' + 'a'.repeat(2048),
    ])
        refuses(envelope({ ...METADATA, endpoint }));
});

test('authority error guidance is fixed safe text and does not invent a domain result', () => {
    for (const reason of ['unavailable', 'invalid', 'changed', 'unknown-archive'] as const) {
        const error = new OperationAuthorityError(reason);
        assert.equal(error.name, 'OperationAuthorityError');
        assert.equal(error.envelope, null);
        assert.ok(error.message.length > 0);
    }
});
