/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import fs, { mkdtempSync, mkdirSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

import {
    assertStableBuildSnapshot, browserBuildInfo, BuildInputError, captureBuildProvenance, captureBuildSnapshot,
    hashPublicBuildInputs, MAX_BUILD_INPUT_BYTES, MAX_BUILD_INPUT_FILES, publicBuildInputs,
} from '../build-info.js';
import { BuildInfoError, compareBuildSource, embeddedBuildInfo, parseBuildInfo, UNKNOWN_BUILD_INFO } from '../src/lib/build-info.ts';

const COMMIT = 'a'.repeat(40);
const HASH = 'b'.repeat(64);
const BUILD = { schema_version: 1, source_commit: COMMIT, source_dirty: false, inputs_sha256: HASH };
const bytes = (value: string) => new TextEncoder().encode(value);

test('V50 only fresh Linux production builds request protected provenance capture', () => {
    assert.equal(captureBuildProvenance(true, false, 'linux'), true);
    for (const [production, watch, platform] of [[false, false, 'linux'], [true, true, 'linux'],
        [true, false, 'darwin'], [true, false, 'win32']] as const)
        assert.equal(captureBuildProvenance(production, watch, platform), false);
});

function fixture() {
    const directory = mkdtempSync(join(tmpdir(), 'hfcache-cpr-build-inputs-'));
    for (const name of ['src', 'pkg/lib', '.local-fixtures', 'src/.private', 'src/fixtures'])
        mkdirSync(join(directory, name), { recursive: true, mode: 0o700 });
    for (const name of ['Makefile', 'build.js', 'build-info.js', 'package.json', 'pnpm-lock.yaml'])
        writeFileSync(join(directory, name), 'public-' + name);
    writeFileSync(join(directory, 'src/index.tsx'), 'export const publicValue = 1;');
    writeFileSync(join(directory, 'pkg/lib/cockpit.js'), 'export const pinned = true;');
    for (const name of ['.local-fixtures/credentials.json', 'src/.private/credential.json', 'src/fixtures/token.json'])
        writeFileSync(join(directory, name), 'SYNTHETIC_BUILD_CREDENTIAL', { mode: 0o600 });
    return { directory, cleanup: () => rmSync(directory, { recursive: true, force: true }) };
}

test('V50 loaded browser metadata is an exact immutable public schema', () => {
    const info = parseBuildInfo(BUILD);
    assert.deepEqual({ ...info }, BUILD);
    assert.ok(Object.isFrozen(info));
    assert.deepEqual({ ...parseBuildInfo(UNKNOWN_BUILD_INFO) }, UNKNOWN_BUILD_INFO);
    assert.deepEqual({ ...parseBuildInfo({ ...UNKNOWN_BUILD_INFO, inputs_sha256: HASH }) },
                     { ...UNKNOWN_BUILD_INFO, inputs_sha256: HASH });
    assert.deepEqual(embeddedBuildInfo, UNKNOWN_BUILD_INFO);
});

test('V50/V51 invalid, extra or secret-bearing build fields are safely unavailable', () => {
    for (const value of [null, [], 'SYNTHETIC_BUILD_CREDENTIAL', {},
        { ...BUILD, schema_version: 2 }, { ...BUILD, source_commit: COMMIT.toUpperCase() },
        { ...BUILD, source_dirty: 'false' }, { ...BUILD, inputs_sha256: 'SYNTHETIC_BUILD_CREDENTIAL' },
        { ...BUILD, source_commit: null }, { ...BUILD, token: 'SYNTHETIC_BUILD_CREDENTIAL' }]) {
        assert.throws(() => parseBuildInfo(value), error => error instanceof BuildInfoError &&
            !error.message.includes('SYNTHETIC_BUILD_CREDENTIAL'));
    }
});

test('V51 build metadata accessors and hostile proxies are never presentation authority', () => {
    let calls = 0;
    const accessor = { ...BUILD };
    Object.defineProperty(accessor, 'source_commit', { get: () => { calls += 1; return 'SYNTHETIC_BUILD_CREDENTIAL' } });
    assert.throws(() => parseBuildInfo(accessor), BuildInfoError);
    assert.equal(calls, 0);
    assert.throws(() => parseBuildInfo(new Proxy({}, { ownKeys: () => { throw new Error('SYNTHETIC_BUILD_CREDENTIAL') } })),
                  error => error instanceof BuildInfoError && !error.message.includes('SYNTHETIC_BUILD_CREDENTIAL'));
    assert.throws(() => parseBuildInfo({ ...BUILD, [Symbol('SYNTHETIC_BUILD_CREDENTIAL')]: true }), BuildInfoError);
    const revoked = Proxy.revocable({}, {});
    revoked.revoke();
    assert.throws(() => parseBuildInfo(revoked.proxy), BuildInfoError);
});

test('V50 same-source, different-source, dirty and unavailable browser evidence are distinct', () => {
    const info = parseBuildInfo(BUILD);
    assert.equal(compareBuildSource(info, COMMIT), 'same-source');
    assert.equal(compareBuildSource(info, 'c'.repeat(40)), 'mismatch');
    assert.equal(compareBuildSource(parseBuildInfo({ ...BUILD, source_dirty: true }), COMMIT), 'dirty');
    assert.equal(compareBuildSource(info, null), 'unavailable');
    assert.equal(compareBuildSource(UNKNOWN_BUILD_INFO, COMMIT), 'unavailable');
});

test('V50 declared input hashing is sorted, deterministic and framed without path/byte ambiguity', () => {
    const inputs = [{ name: 'src/b.ts', bytes: bytes('second') }, { name: 'src/a.ts', bytes: bytes('first') }];
    const hash = hashPublicBuildInputs(inputs);
    assert.match(hash, /^[0-9a-f]{64}$/);
    assert.equal(hashPublicBuildInputs([...inputs].reverse()), hash);
    assert.notEqual(hashPublicBuildInputs([{ name: 'src/a.ts', bytes: bytes('first!') }, inputs[0]]), hash);
    assert.notEqual(hashPublicBuildInputs([{ name: 'src/a.ts', bytes: bytes('b1:') }]),
                    hashPublicBuildInputs([{ name: 'src/a.tsb', bytes: bytes('1:') }]));
});

test('V50/V51 hashing rejects duplicate, unsafe, oversized or excessive inputs without echoing values', () => {
    for (const inputs of [[], [{ name: '../SYNTHETIC_BUILD_CREDENTIAL', bytes: bytes('public') }],
        [{ name: '/SYNTHETIC_BUILD_CREDENTIAL', bytes: bytes('public') }],
        [{ name: 'src/a.ts', bytes: bytes('first') }, { name: 'src/a.ts', bytes: bytes('second') }],
        [{ name: 'src/a.ts', bytes: new Uint8Array(MAX_BUILD_INPUT_BYTES + 1) }],
        Array.from({ length: MAX_BUILD_INPUT_FILES + 1 }, (_value, index) => ({ name: `src/a${index}.ts`, bytes: bytes('public') }))]) {
        assert.throws(() => hashPublicBuildInputs(inputs), error => error instanceof BuildInputError &&
            !error.message.includes('SYNTHETIC_BUILD_CREDENTIAL'));
    }
});

test('V50 source exports hash only declared public inputs and report unknown Git provenance', () => {
    const files = fixture();
    try {
        const inputs = publicBuildInputs(files.directory);
        assert.equal(inputs.length, 7);
        assert.ok(!inputs.some(input => new TextDecoder().decode(input.bytes)
                .includes('SYNTHETIC_BUILD_CREDENTIAL')));
        const snapshot = captureBuildSnapshot(files.directory);
        assert.equal(snapshot.source_commit, null);
        assert.equal(snapshot.source_dirty, null);
        assert.equal(snapshot.git_state, null);
        const info = browserBuildInfo(snapshot);
        assert.deepEqual(Object.keys(info).sort(), ['inputs_sha256', 'schema_version', 'source_commit', 'source_dirty']);
        assert.match(info.inputs_sha256!, /^[0-9a-f]{64}$/);
        assert.ok(!JSON.stringify(info).includes(files.directory));
        assert.ok(!JSON.stringify(info).includes('SYNTHETIC_BUILD_CREDENTIAL'));
        writeFileSync(join(files.directory, '.local-fixtures/credentials.json'), 'DIFFERENT_PRIVATE_VALUE');
        assert.equal(captureBuildSnapshot(files.directory).inputs_sha256, snapshot.inputs_sha256);
        writeFileSync(join(files.directory, 'src/index.tsx'), 'export const publicValue = 2;');
        assert.notEqual(captureBuildSnapshot(files.directory).inputs_sha256, snapshot.inputs_sha256);
    } finally { files.cleanup() }
});

test('V50 public input scan refuses a symlink instead of reading outside declared source', () => {
    const files = fixture();
    try {
        symlinkSync(join(files.directory, '.local-fixtures/credentials.json'), join(files.directory, 'src/escape.json'));
        assert.throws(() => publicBuildInputs(files.directory), error => error instanceof BuildInputError &&
            !error.message.includes(files.directory));
    } finally { files.cleanup() }
});

test('V50 a symlinked ancestor cannot open or hash an external private fixture leaf', () => {
    const files = fixture();
    const external = mkdtempSync(join(tmpdir(), 'hfcache-cpr-private-input-'));
    const originalOpen = fs.openSync;
    let privateLeafOpens = 0;
    try {
        mkdirSync(join(external, 'lib'));
        writeFileSync(join(external, 'lib/private.js'), 'SYNTHETIC_BUILD_CREDENTIAL');
        rmSync(join(files.directory, 'pkg'), { recursive: true });
        symlinkSync(external, join(files.directory, 'pkg'));
        // Observe real opens without replacing their filesystem behavior.
        fs.openSync = (...args: Parameters<typeof fs.openSync>) => {
            if (typeof args[0] === 'string' && args[0].endsWith('/private.js')) privateLeafOpens += 1;
            return originalOpen(...args);
        };
        let failure: unknown = null;
        try { publicBuildInputs(files.directory) } catch (error) { failure = error }
        assert.equal(privateLeafOpens, 0, 'Declared ancestor refusal must happen before any external private leaf is opened');
        assert.ok(failure instanceof BuildInputError);
    } finally {
        fs.openSync = originalOpen;
        files.cleanup();
        rmSync(external, { recursive: true, force: true });
    }
});

test('V50 declared source scanning refuses oversized files and unbounded directory depth', () => {
    for (const oversized of [false, true]) {
        const files = fixture();
        try {
            if (oversized)
                writeFileSync(join(files.directory, 'src/large.ts'), new Uint8Array(MAX_BUILD_INPUT_BYTES + 1));
            else
                mkdirSync(join(files.directory, 'src', ...Array.from({ length: 33 }, () => 'nested')), { recursive: true });
            assert.throws(() => publicBuildInputs(files.directory), BuildInputError);
        } finally { files.cleanup() }
    }
});

test('V50 a nonregular fixed build input refuses without blocking on a named pipe', () => {
    const files = fixture();
    try {
        const pipe = join(files.directory, 'build.js');
        rmSync(pipe);
        execFileSync('mkfifo', ['-m', '600', pipe]);
        const helper = pathToFileURL(fileURLToPath(new URL('../build-info.js', import.meta.url))).href;
        const script = `import {publicBuildInputs,BuildInputError} from ${JSON.stringify(helper)};` +
            'try { publicBuildInputs(process.argv[1]); process.exit(2) }' +
            'catch (error) { process.exit(error instanceof BuildInputError ? 0 : 3) }';
        const child = spawnSync(process.execPath, ['--input-type=module', '-e', script, files.directory], {
            timeout: 1000, encoding: 'utf8', maxBuffer: 1024,
        });
        assert.equal(child.status, 0, 'A fixed build input must refuse nonregular files before a blocking read');
    } finally { files.cleanup() }
});

test('V50 ambient Git directory selection cannot give a source export another repository identity', () => {
    const files = fixture();
    const previous = process.env.GIT_DIR;
    try {
        process.env.GIT_DIR = fileURLToPath(new URL('../../.git', import.meta.url));
        const snapshot = captureBuildSnapshot(files.directory);
        assert.equal(snapshot.source_commit, null);
        assert.equal(snapshot.source_dirty, null);
        assert.ok(!JSON.stringify(browserBuildInfo(snapshot)).includes('GIT_DIR'));
    } finally {
        if (previous === undefined) delete process.env.GIT_DIR;
        else process.env.GIT_DIR = previous;
        files.cleanup();
    }
});

test('V50 changing inputs, commit or working-copy evidence refuses production provenance', () => {
    const snapshot = { source_commit: COMMIT, source_dirty: false, inputs_sha256: HASH, git_state: '' };
    assert.doesNotThrow(() => assertStableBuildSnapshot(snapshot, { ...snapshot }));
    for (const changed of [{ source_commit: 'c'.repeat(40) }, { source_dirty: true },
        { inputs_sha256: 'd'.repeat(64) }, { git_state: 'SYNTHETIC_BUILD_CREDENTIAL' }]) {
        assert.throws(() => assertStableBuildSnapshot(snapshot, { ...snapshot, ...changed }), error =>
            error instanceof BuildInputError && !error.message.includes('SYNTHETIC_BUILD_CREDENTIAL'));
    }
});
