/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { execFileSync, spawn, spawnSync } from 'node:child_process';
import {
    chmodSync, existsSync, linkSync, lstatSync, mkdtempSync, mkdirSync, readFileSync,
    readdirSync, rmSync, statSync, symlinkSync, writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { delimiter, join } from 'node:path';
import { setTimeout as pause } from 'node:timers/promises';
import { test } from 'node:test';

import {
    candidateMutationInvocation, CONFIGURATION_PATHS, guardCandidateInvocation, guardInstalledInvocation,
    inspectCandidateInvocation, MAX_CANDIDATE_BYTES, readInstalledInvocation, validateCandidateText,
} from '../src/lib/candidate-guard.ts';
import type {
    CandidateGuard, CandidateInspection, ConfigurationFixture, GuardedInvocation,
} from '../src/lib/candidate-guard.ts';
import { HFCACHE_CLI, hfcacheArgv } from '../src/lib/command.ts';

const BASE = 'schema_version=1\n# original π\n\n';
const CONTENT = 'schema_version=1\n# proposed λ\n\n\n';
const GUARD = { candidateContent: CONTENT, installedContent: BASE };

function fixture() {
    const root = mkdtempSync(join(tmpdir(), 'hfcache-config-'));
    const paths = {
        installed: join(root, 'config.toml'),
        candidate: join(root, '.candidate.toml'),
        backup: join(root, 'config.toml.bak'),
        lock: join(root, '.configuration.lock'),
    };
    const ownerUid = process.getuid?.();
    assert.notEqual(ownerUid, undefined);
    const identity: ConfigurationFixture = {
        paths, ownerUid: ownerUid as number, group: execFileSync('id', ['-gn'], { encoding: 'utf8' }).trim(),
    };
    writeFileSync(paths.installed, BASE, { mode: 0o640 });
    chmodSync(paths.installed, 0o640);
    const bin = join(root, 'bin');
    mkdirSync(bin, { mode: 0o700 });
    const called = join(root, 'called');
    const argumentsPath = join(root, 'arguments');
    const response = join(root, 'response');
    writeFileSync(response, '{"fixture":"API response"}\n');
    writeFileSync(join(bin, 'systemd-run'), '#!/usr/bin/env bash\n' +
        'if [[ "$HFCACHE_TEST_REQUIRE_STDOUT_PIPE" == 1 && ! -p /proc/self/fd/1 ]]; then exit 91; fi\n' +
        'printf called > "$HFCACHE_TEST_CALLED"\n' +
        'printf \'%s\\0\' "$@" > "$HFCACHE_TEST_ARGUMENTS"\n' +
        'if [[ -n "$HFCACHE_TEST_ENTERED" ]]; then\n' +
        '  : > "$HFCACHE_TEST_ENTERED"\n' +
        '  for ((i=0; i<250; i++)); do [[ -f "$HFCACHE_TEST_RELEASE" ]] && break; sleep .02; done\n' +
        '  [[ -f "$HFCACHE_TEST_RELEASE" ]] || exit 99\n' +
        'fi\n' +
        'cat "$HFCACHE_TEST_RESPONSE"\nexit "$HFCACHE_TEST_STATUS"\n', { mode: 0o700 });
    const env = {
        ...process.env,
        PATH: bin + delimiter + process.env.PATH,
        HFCACHE_TEST_CALLED: called,
        HFCACHE_TEST_ARGUMENTS: argumentsPath,
        HFCACHE_TEST_RESPONSE: response,
        HFCACHE_TEST_CHANGED_PATH: '',
        HFCACHE_TEST_REQUIRE_STDOUT_PIPE: '',
        HFCACHE_TEST_STATUS: '0',
    };
    const run = (invocation: GuardedInvocation) => spawnSync(invocation.argv[0], invocation.argv.slice(1), {
        input: invocation.input, encoding: 'utf8', env, timeout: 10000, maxBuffer: 4 * 1024 * 1024,
    });
    const write = (guard: CandidateGuard = GUARD) => run(candidateMutationInvocation('write', guard, identity));
    const cli = (guard: CandidateGuard = GUARD) => guardCandidateInvocation(
        hfcacheArgv(['config', 'validate'], { config: paths.candidate }), guard, identity,
    );
    return {
        root,
        paths,
        identity,
        bin,
        env,
        called,
        argumentsPath,
        run,
        write,
        cli,
        close: () => rmSync(root, { recursive: true, force: true })
    };
}

test('fixed production helper keeps content in stdin and imports no arbitrary command/path option', () => {
    const invocation = guardCandidateInvocation(['systemd-run', '--', 'fixed-cli'], GUARD);
    assert.equal(invocation.input, Buffer.from(CONTENT).toString('base64') + '\n' +
        Buffer.from(BASE).toString('base64') + '\n');
    assert.ok(!invocation.argv.some(argument => argument.includes(CONTENT) || argument.includes(BASE)));
    for (const path of Object.values(CONFIGURATION_PATHS))
        assert.ok(invocation.argv.includes(path));
    assert.throws(() => guardCandidateInvocation(['sh', '-c', 'untrusted'], GUARD));
});

test('every guarded action transports exact bounded bytes through a NUL-free Cockpit text channel', () => {
    const guard = { candidateContent: '# λ😀\n\n\n', installedContent: '# π\r\n\n' };
    const expected = Buffer.from(guard.candidateContent).toString('base64') + '\n' +
        Buffer.from(guard.installedContent).toString('base64') + '\n';
    for (const invocation of [
        ...(['write', 'install', 'remove'] as const).map(action => candidateMutationInvocation(action, guard)),
        guardCandidateInvocation(['systemd-run', '--', 'fixed-cli'], guard),
        inspectCandidateInvocation(guard),
        guardInstalledInvocation(hfcacheArgv(['config', 'validate']), guard.candidateContent),
    ]) {
        assert.equal(invocation.input.includes('\0'), false);
        assert.match(invocation.input, /^[A-Za-z0-9+/=\n]*$/);
        assert.equal(invocation.input, invocation.argv.includes('confirm')
            ? Buffer.from(guard.candidateContent).toString('base64') + '\n' +
                Buffer.from(guard.candidateContent).toString('base64') + '\n'
            : expected);
    }
});

test('malformed transport frames refuse before lock creation, filesystem changes or CLI execution', () => {
    const encode = (value: string) => Buffer.from(value).toString('base64');
    const valid = encode(CONTENT) + '\n' + encode(BASE) + '\n';
    const frames = [
        '', CONTENT + '\0' + BASE + '\0', valid.slice(0, -1), valid + '\n', valid + 'extra',
        '\n' + encode(BASE) + '\n', '!\n' + encode(BASE) + '\n',
        'YR==\n' + encode(BASE) + '\n', // noncanonical pad bits
        Buffer.from([0xff]).toString('base64') + '\n' + encode(BASE) + '\n',
        encode('x\0y') + '\n' + encode(BASE) + '\n',
        encode('x'.repeat(MAX_CANDIDATE_BYTES + 1)) + '\n' + encode(BASE) + '\n',
        'x'.repeat(1398105) + '\n' + encode(BASE) + '\n',
    ];
    for (const action of ['write', 'install', 'remove', 'guard', 'confirm', 'inspect'] as const) {
        const files = fixture();
        try {
            const invocation = action === 'guard'
                ? files.cli()
                : action === 'confirm'
                    ? guardInstalledInvocation(hfcacheArgv(['config', 'validate']), CONTENT, files.identity)
                    : action === 'inspect'
                        ? inspectCandidateInvocation(GUARD, files.identity)
                        : candidateMutationInvocation(action, GUARD, files.identity);
            const original = readdirSync(files.root).sort();
            for (const input of frames) {
                const result = files.run({ ...invocation, input });
                if (action === 'inspect') {
                    assert.equal(result.status, 0, result.stderr);
                    assert.deepEqual(JSON.parse(result.stdout), {
                        candidate: 'unknown',
                        installedBase: 'unknown',
                        installedCandidate: 'unknown',
                        backupBase: 'unknown',
                    });
                } else {
                    assert.notEqual(result.status, 0);
                }
                assert.deepEqual(readdirSync(files.root).sort(), original, action);
                assert.equal(readFileSync(files.paths.installed, 'utf8'), BASE);
                assert.equal(existsSync(files.called), false);
            }
        } finally {
            files.close();
        }
    }
});

test('failed wire reader, decoder or canonical encoder cannot authorize filesystem effects', () => {
    for (const phase of ['read', 'read-sentinel', 'decode', 'decode-sentinel', 'encode']) {
        const files = fixture();
        try {
            const executable = phase.startsWith('read') ? 'head' : 'base64';
            const arguments_ = phase.startsWith('decode') ? '--decode' : '--wrap=0';
            writeFileSync(join(files.bin, executable), '#!/usr/bin/env bash\n' +
                '/usr/bin/' + executable + ' "$@"\n' +
                (phase.endsWith('sentinel') ? 'printf \'\\0\'\n' : '') +
                (phase.startsWith('read') ? 'exit 31\n' : '[[ "$1" != "' + arguments_ + '" ]] || exit 31\n'),
                          { mode: 0o700 });
            const before = readdirSync(files.root).sort();
            const result = files.write();
            assert.notEqual(result.status, 0);
            assert.deepEqual(readdirSync(files.root).sort(), before);
            assert.equal(readFileSync(files.paths.installed, 'utf8'), BASE);
            assert.equal(existsSync(files.called), false);
        } finally {
            files.close();
        }
    }
});

test('two maximum-size UTF-8 documents preserve exact bytes at the complete wire bound', () => {
    const files = fixture();
    try {
        const guard = {
            candidateContent: 'λ'.repeat(MAX_CANDIDATE_BYTES / 2),
            installedContent: 'x'.repeat(MAX_CANDIDATE_BYTES),
        };
        writeFileSync(files.paths.installed, guard.installedContent, { mode: 0o640 });
        const invocation = candidateMutationInvocation('write', guard, files.identity);
        assert.equal(invocation.input.length, 2796210);
        const result = files.run(invocation);
        assert.equal(result.status, 0, result.stderr);
        assert.equal(readFileSync(files.paths.candidate, 'utf8'), guard.candidateContent);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), guard.installedContent);
        assert.equal(existsSync(files.called), false);
        const before = readdirSync(files.root).sort();
        const inode = statSync(files.paths.lock).ino;
        for (const tail of ['x', 'x'.repeat(4096)]) {
            const overflow = files.run({ ...invocation, input: invocation.input + tail });
            assert.equal(overflow.error, undefined);
            assert.notEqual(overflow.status, 0);
            assert.deepEqual(readdirSync(files.root).sort(), before);
            assert.equal(statSync(files.paths.lock).ino, inode);
            assert.equal(readFileSync(files.paths.candidate, 'utf8'), guard.candidateContent);
            assert.equal(readFileSync(files.paths.installed, 'utf8'), guard.installedContent);
            assert.equal(existsSync(files.called), false);
        }
    } finally {
        files.close();
    }
});

test('bounded UTF-8 framing rejects NUL, lone surrogates and byte overflow before spawn', () => {
    for (const value of ['', '\0', 'a\0b', '\ud800', '\udfff', 'é'.repeat(MAX_CANDIDATE_BYTES)])
        assert.throws(() => validateCandidateText(value));
    validateCandidateText('λ\n'.repeat(100));
    validateCandidateText('a'.repeat(MAX_CANDIDATE_BYTES));
});

test('installed confirmation passes a pipe to the manager and preserves every classified CLI exit', () => {
    const files = fixture();
    try {
        assert.equal(files.write().status, 0);
        assert.equal(files.run(candidateMutationInvocation('install', GUARD, files.identity)).status, 0);
        const lock = statSync(files.paths.lock).ino;
        files.env.HFCACHE_TEST_REQUIRE_STDOUT_PIPE = '1';
        const invocation = guardInstalledInvocation(hfcacheArgv(['config', 'validate']), CONTENT, files.identity);
        for (const status of [0, 10, 20, 30, 40, 50]) {
            files.env.HFCACHE_TEST_STATUS = String(status);
            const result = files.run(invocation);
            assert.equal(result.status, status, result.stderr);
            assert.equal(result.stdout, readFileSync(files.root + '/response', 'utf8'));
            assert.equal(statSync(files.paths.lock).ino, lock);
            assert.equal(readFileSync(files.paths.installed, 'utf8'), CONTENT);
            assert.equal(readFileSync(files.paths.backup, 'utf8'), BASE);
            assert.ok(!readdirSync(files.root).some(name => /^\.(candidate-input|installed-input|confirmation)\./.test(name)));
        }
        for (const status of [1, 2, 126, 127, 137]) {
            files.env.HFCACHE_TEST_STATUS = String(status);
            const result = files.run(invocation);
            assert.equal(result.status, status);
            assert.equal(result.stdout, '');
        }
        files.env.HFCACHE_TEST_STATUS = '0';
        // Even a collector that emits a complete plausible result then fails
        // with a domain-like exit must not release its spool.
        writeFileSync(join(files.bin, 'cat'), '#!/usr/bin/env bash\n/usr/bin/cat "$@"\nexit 30\n', { mode: 0o700 });
        const collectorFailure = files.run(invocation);
        assert.equal(collectorFailure.status, 30);
        assert.equal(collectorFailure.stdout, '');
        assert.equal(statSync(files.paths.lock).ino, lock);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), CONTENT);
        assert.equal(readFileSync(files.paths.backup, 'utf8'), BASE);
    } finally {
        files.close();
    }
});

test('installed read is exact and bounded under the persistent lock', () => {
    const files = fixture();
    try {
        const read = () => files.run(readInstalledInvocation(files.identity));
        const result = read();
        assert.equal(result.status, 0, result.stderr);
        assert.equal(result.stdout, BASE);
        assert.equal(existsSync(files.called), false);
        const inode = statSync(files.paths.lock).ino;
        writeFileSync(files.paths.installed, 'x'.repeat(MAX_CANDIDATE_BYTES + 1));
        const oversized = read();
        assert.notEqual(oversized.status, 0);
        assert.equal(oversized.stdout, '');
        assert.equal(statSync(files.paths.lock).ino, inode);
    } finally {
        files.close();
    }
});

for (const unsafe of ['symlink', 'hardlink', 'mode', 'directory', 'fifo'] as const) {
    test(`installed read preserves unsafe ${unsafe} evidence without following or blocking`, () => {
        const files = fixture();
        try {
            const evidence = join(files.root, 'evidence');
            if (unsafe === 'symlink') {
                writeFileSync(evidence, 'private evidence', { mode: 0o640 });
                rmSync(files.paths.installed);
                symlinkSync(evidence, files.paths.installed);
            } else if (unsafe === 'hardlink') {
                linkSync(files.paths.installed, evidence);
            } else if (unsafe === 'mode') {
                chmodSync(files.paths.installed, 0o666);
            } else {
                rmSync(files.paths.installed);
                if (unsafe === 'directory')
                    mkdirSync(files.paths.installed);
                else
                    execFileSync('mkfifo', [files.paths.installed]);
            }
            const before = lstatSync(files.paths.installed);
            const result = files.run(readInstalledInvocation(files.identity));
            assert.notEqual(result.status, 0);
            assert.equal(result.error, undefined);
            assert.equal(result.stdout, '');
            assert.equal(lstatSync(files.paths.installed).ino, before.ino);
            assert.equal(existsSync(files.called), false);
        } finally {
            files.close();
        }
    });
}

test('real guarded shell preserves exact Unicode/trailing-newline bytes, predecessor and persistent lock', () => {
    const files = fixture();
    try {
        const first = files.write();
        assert.equal(first.status, 0, first.stderr);
        assert.equal(readFileSync(files.paths.candidate, 'utf8'), CONTENT);
        assert.equal(statSync(files.paths.candidate).mode & 0o777, 0o640);
        const inode = statSync(files.paths.lock).ino;
        const checked = files.run(files.cli());
        assert.equal(checked.status, 0, checked.stderr);
        assert.equal(checked.stdout, '{"fixture":"API response"}\n');
        assert.equal(readFileSync(files.called, 'utf8'), 'called');
        const argv = readFileSync(files.argumentsPath, 'utf8').split('\0')
                .slice(0, -1);
        assert.deepEqual(argv.slice(argv.indexOf('--') + 1), [
            HFCACHE_CLI, '--client-config', '/etc/hfcache/client.toml',
            '--api-socket', '/run/hfcache/api/api.sock', '--json',
            '--config', files.paths.candidate, 'config', 'validate',
        ]);
        assert.ok(!argv.some(argument => argument.includes('ImportCredential')));
        writeFileSync(files.paths.backup, 'previous predecessor', { mode: 0o640 });
        const installed = files.run(candidateMutationInvocation('install', GUARD, files.identity));
        assert.equal(installed.status, 0, installed.stderr);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), CONTENT);
        assert.equal(readFileSync(files.paths.backup, 'utf8'), BASE);
        assert.equal(statSync(files.paths.installed).mode & 0o777, 0o640);
        assert.equal(statSync(files.paths.backup).mode & 0o777, 0o640);
        assert.equal(statSync(files.paths.lock).ino, inode);
        assert.equal(statSync(files.paths.lock).mode & 0o777, 0o600);
        assert.equal(existsSync(files.paths.candidate), false);
        assert.equal(readdirSync(files.root).some(name => name.endsWith('.tmp')), false);
    } finally {
        files.close();
    }
});

for (const target of ['candidate', 'installed'] as const) {
    test(`changed ${target} bytes refuse CLI and install without overwriting evidence`, () => {
        const files = fixture();
        try {
            assert.equal(files.write().status, 0);
            writeFileSync(files.paths[target], 'changed by another editor\n');
            const before = readFileSync(files.paths[target]);
            assert.notEqual(files.run(files.cli()).status, 0);
            assert.equal(existsSync(files.called), false);
            assert.notEqual(files.run(candidateMutationInvocation('install', GUARD, files.identity)).status, 0);
            assert.deepEqual(readFileSync(files.paths[target]), before);
            assert.equal(existsSync(files.paths.backup), false);
        } finally {
            files.close();
        }
    });
}

for (const target of ['candidate', 'installed', 'backup', 'lock'] as const) {
    test(`unexpected ${target} symlink is preserved and never followed`, () => {
        const files = fixture();
        try {
            assert.equal(files.write().status, 0);
            const evidence = join(files.root, 'evidence');
            writeFileSync(evidence, 'preserve external evidence', { mode: 0o640 });
            rmSync(files.paths[target], { force: true });
            symlinkSync(evidence, files.paths[target]);
            assert.notEqual(files.run(candidateMutationInvocation('install', GUARD, files.identity)).status, 0);
            assert.equal(lstatSync(files.paths[target]).isSymbolicLink(), true);
            assert.equal(readFileSync(evidence, 'utf8'), 'preserve external evidence');
        } finally {
            files.close();
        }
    });
}

test('shell metacharacters remain candidate data rather than shell code', () => {
    const files = fixture();
    try {
        const marker = join(files.root, 'must-not-exist');
        const guard = { ...GUARD, candidateContent: `schema_version=1\n# $(touch ${marker}) \`touch ${marker}\` '$HOME'\n` };
        assert.equal(files.write(guard).status, 0);
        assert.equal(files.run(files.cli(guard)).status, 0);
        assert.equal(existsSync(marker), false);
        assert.equal(readFileSync(files.paths.candidate, 'utf8'), guard.candidateContent);
    } finally {
        files.close();
    }
});

test('removal requires owned exact candidate/base and keeps the lock inode', () => {
    const files = fixture();
    try {
        assert.equal(files.write().status, 0);
        const inode = statSync(files.paths.lock).ino;
        assert.notEqual(files.run(candidateMutationInvocation('remove', {
            ...GUARD, candidateContent: 'different proposal',
        }, files.identity)).status, 0);
        assert.equal(readFileSync(files.paths.candidate, 'utf8'), CONTENT);
        assert.equal(files.run(candidateMutationInvocation('remove', GUARD, files.identity)).status, 0);
        assert.equal(existsSync(files.paths.candidate), false);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), BASE);
        assert.equal(statSync(files.paths.lock).ino, inode);
    } finally {
        files.close();
    }
});

test('failed predecessor persistence preserves current policy, candidate and previous backup', () => {
    const files = fixture();
    try {
        assert.equal(files.write().status, 0);
        writeFileSync(files.paths.backup, 'old backup', { mode: 0o640 });
        writeFileSync(join(files.bin, 'sync'), '#!/usr/bin/env bash\nexit 1\n', { mode: 0o700 });
        assert.notEqual(files.run(candidateMutationInvocation('install', GUARD, files.identity)).status, 0);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), BASE);
        assert.equal(readFileSync(files.paths.candidate, 'utf8'), CONTENT);
        assert.equal(readFileSync(files.paths.backup, 'utf8'), 'old backup');
        assert.equal(readdirSync(files.root).some(name => name.startsWith('.predecessor.')), false);
    } finally {
        files.close();
    }
});

test('config flock remains held through the CLI and serializes a competing install', async () => {
    const files = fixture();
    const entered = join(files.root, 'entered');
    const release = join(files.root, 'release');
    let validating: ReturnType<typeof spawn> | null = null;
    let installing: ReturnType<typeof spawn> | null = null;
    try {
        assert.equal(files.write().status, 0);
        const invocation = files.cli();
        validating = spawn(invocation.argv[0], invocation.argv.slice(1), {
            env: {
                ...files.env, HFCACHE_TEST_ENTERED: entered, HFCACHE_TEST_RELEASE: release,
            },
            stdio: ['pipe', 'ignore', 'ignore']
        });
        const validated = new Promise<number | null>(resolve => validating?.once('exit', resolve));
        validating.stdin?.end(invocation.input);
        for (let attempt = 0; attempt < 250 && !existsSync(entered); attempt += 1)
            await pause(20);
        assert.ok(existsSync(entered));
        const mutation = candidateMutationInvocation('install', GUARD, files.identity);
        installing = spawn(mutation.argv[0], mutation.argv.slice(1), {
            env: files.env,
            stdio: ['pipe', 'ignore', 'ignore']
        });
        const installed = new Promise<number | null>(resolve => installing?.once('exit', resolve));
        installing.stdin?.end(mutation.input);
        await pause(100);
        assert.equal(installing.exitCode, null);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), BASE);
        writeFileSync(release, 'release');
        assert.equal(await validated, 0);
        assert.equal(await installed, 0);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), CONTENT);
        assert.equal(readFileSync(files.paths.backup, 'utf8'), BASE);
    } finally {
        if (validating?.exitCode === null)
            validating.kill('SIGKILL');
        if (installing?.exitCode === null)
            installing.kill('SIGKILL');
        files.close();
    }
});

for (const target of ['installed', 'candidate'] as const) {
    test(`concurrent tag-only ${target} edit refuses without overwriting labels`, () => {
        const files = fixture();
        try {
            const base = 'schema_version=1\n[[repositories]]\nid="org/model"\ntype="model"\ntags=["coding"]\n';
            const proposed = base.replace('coding', 'local-inference');
            const guard = { installedContent: base, candidateContent: proposed };
            writeFileSync(files.paths.installed, base);
            assert.equal(files.write(guard).status, 0);
            const changed = (target === 'installed' ? base : proposed).replace(/coding|local-inference/, 'changed');
            writeFileSync(files.paths[target], changed);
            assert.notEqual(files.run(files.cli(guard)).status, 0);
            assert.notEqual(files.run(candidateMutationInvocation('install', guard, files.identity)).status, 0);
            assert.equal(readFileSync(files.paths[target], 'utf8'), changed);
            assert.equal(existsSync(files.paths.backup), false);
            assert.equal(existsSync(files.called), false);
        } finally { files.close() }
    });
}

test('installed confirmation compares exact tags under lock after candidate rename', () => {
    const files = fixture();
    try {
        const guard = { ...GUARD, candidateContent: CONTENT + '# tags=["coding"]\n' };
        assert.equal(files.write(guard).status, 0);
        assert.equal(files.run(candidateMutationInvocation('install', guard, files.identity)).status, 0);
        assert.equal(existsSync(files.paths.candidate), false);
        const lock = statSync(files.paths.lock).ino;
        const argv = hfcacheArgv(['config', 'validate']);
        const confirm = guardInstalledInvocation(argv, guard.candidateContent, files.identity);
        assert.ok(!argv.includes('--config'));
        assert.equal(files.run(confirm).status, 0);
        assert.equal(readFileSync(files.paths.backup, 'utf8'), BASE);
        rmSync(files.called);
        const concurrent = guard.candidateContent.replace('coding', 'vision');
        writeFileSync(files.paths.installed, concurrent);
        const refused = files.run(confirm);
        assert.notEqual(refused.status, 0);
        assert.equal(refused.stdout, '');
        assert.equal(existsSync(files.called), false);
        assert.equal(readFileSync(files.paths.installed, 'utf8'), concurrent);
        assert.equal(readFileSync(files.paths.backup, 'utf8'), BASE);
        assert.equal(statSync(files.paths.lock).ino, lock);
        assert.throws(() => guardInstalledInvocation(
            hfcacheArgv(['config', 'validate'], { config: files.paths.candidate }), CONTENT, files.identity));
    } finally { files.close() }
});

test('installed confirmation forwards the original authority pin without admitting a fake job key', () => {
    const files = fixture();
    try {
        const pin = 'a'.repeat(64);
        const argv = hfcacheArgv(['config', 'validate'], { expectedClientScope: pin });
        const result = files.run(guardInstalledInvocation(argv, BASE, files.identity));
        assert.equal(result.status, 0, result.stderr);
        const forwarded = readFileSync(files.argumentsPath, 'utf8').split('\0');
        assert.equal(forwarded[forwarded.indexOf('--expected-client-scope') + 1], pin);
        rmSync(files.called);
        assert.throws(() => guardInstalledInvocation(
            hfcacheArgv(['config', 'validate'], { expectedClientScope: pin, idempotencyKey: 'not-a-job' }), BASE, files.identity));
        assert.equal(existsSync(files.called), false);
    } finally { files.close() }
});

test('changed installed tags during confirmation withhold a plausible terminal response', async () => {
    const files = fixture();
    let child: ReturnType<typeof spawn> | null = null;
    const entered = join(files.root, 'confirm-entered');
    const release = join(files.root, 'confirm-release');
    try {
        const expected = BASE + '# tags=["coding"]\n';
        writeFileSync(files.paths.installed, expected);
        const invocation = guardInstalledInvocation(hfcacheArgv(['config', 'validate']), expected, files.identity);
        child = spawn(invocation.argv[0], invocation.argv.slice(1), {
            env: { ...files.env, HFCACHE_TEST_ENTERED: entered, HFCACHE_TEST_RELEASE: release },
            stdio: ['pipe', 'pipe', 'ignore']
        });
        const finished = new Promise<number | null>(resolve => child?.once('exit', resolve));
        let output = '';
        child.stdout?.on('data', bytes => { output += String(bytes) });
        child.stdin?.end(invocation.input);
        for (let attempt = 0; attempt < 250 && !existsSync(entered); attempt += 1)
            await pause(20);
        assert.ok(existsSync(entered));
        const changed = expected.replace('coding', 'vision');
        writeFileSync(files.paths.installed, changed);
        writeFileSync(release, 'release');
        assert.notEqual(await finished, 0);
        assert.equal(output, '');
        assert.equal(readFileSync(files.paths.installed, 'utf8'), changed);
    } finally {
        if (child?.exitCode === null)
            child.kill('SIGKILL');
        files.close();
    }
});

test('oversized confirmation output refuses without releasing a partial response', () => {
    const files = fixture();
    try {
        writeFileSync(files.env.HFCACHE_TEST_RESPONSE, 'x'.repeat(4 * 1024 * 1024 + 1));
        const invocation = guardInstalledInvocation(hfcacheArgv(['config', 'validate']), BASE, files.identity);
        const result = files.run(invocation);
        assert.notEqual(result.status, 0);
        assert.equal(result.stdout, '');
        assert.equal(readFileSync(files.paths.installed, 'utf8'), BASE);
        assert.equal(readdirSync(files.root).some(name => name.startsWith('.confirmation.')), false);
    } finally { files.close() }
});

const UNKNOWN_INSPECTION: CandidateInspection = {
    candidate: 'unknown', installedBase: 'unknown', installedCandidate: 'unknown', backupBase: 'unknown',
};

function inspection(files: ReturnType<typeof fixture>, guard: CandidateGuard = GUARD): CandidateInspection {
    const result = files.run(inspectCandidateInvocation(guard, files.identity));
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    assert.ok(Buffer.byteLength(result.stdout) <= 160);
    const parsed = JSON.parse(result.stdout) as CandidateInspection;
    assert.deepEqual(Object.keys(parsed).sort(), ['backupBase', 'candidate', 'installedBase', 'installedCandidate']);
    assert.ok(Object.values(parsed).every(value => ['matching', 'absent', 'changed', 'unknown'].includes(value)));
    assert.ok(!result.stdout.includes(BASE) && !result.stdout.includes(CONTENT));
    return parsed;
}

function inspectionLock(files: ReturnType<typeof fixture>): void {
    writeFileSync(files.paths.lock, '', { mode: 0o600 });
    chmodSync(files.paths.lock, 0o600);
}

test('read-only inspection never creates a missing lock or any comparison artifact', () => {
    const files = fixture();
    try {
        const names = readdirSync(files.root).sort();
        assert.deepEqual(inspection(files), UNKNOWN_INSPECTION);
        assert.deepEqual(readdirSync(files.root).sort(), names);
        assert.equal(existsSync(files.paths.lock), false);
        assert.equal(existsSync(files.called), false);
    } finally { files.close() }
});

test('read-only inspection gives exact status for absent, matching and changed fixed files', () => {
    const files = fixture();
    try {
        inspectionLock(files);
        const inode = statSync(files.paths.lock).ino;
        const names = readdirSync(files.root).sort();
        assert.deepEqual(inspection(files), {
            candidate: 'absent', installedBase: 'matching', installedCandidate: 'changed', backupBase: 'absent',
        });
        assert.deepEqual(readdirSync(files.root).sort(), names);
        writeFileSync(files.paths.candidate, CONTENT, { mode: 0o640 });
        writeFileSync(files.paths.backup, BASE, { mode: 0o640 });
        const presentNames = readdirSync(files.root).sort();
        assert.deepEqual(inspection(files), {
            candidate: 'matching', installedBase: 'matching', installedCandidate: 'changed', backupBase: 'matching',
        });
        writeFileSync(files.paths.installed, 'changed installed bytes\n');
        writeFileSync(files.paths.candidate, 'changed proposed bytes\n');
        writeFileSync(files.paths.backup, 'changed predecessor bytes\n');
        assert.deepEqual(inspection(files), {
            candidate: 'changed', installedBase: 'changed', installedCandidate: 'changed', backupBase: 'changed',
        });
        assert.deepEqual(readdirSync(files.root).sort(), presentNames);
        assert.equal(statSync(files.paths.lock).ino, inode);
        assert.equal(statSync(files.paths.lock).size, 0);
        assert.equal(existsSync(files.called), false);
    } finally { files.close() }
});

test('matching candidate write reuses its inode; a different preexisting candidate is preserved', () => {
    const files = fixture();
    try {
        assert.equal(files.write().status, 0);
        const candidate = statSync(files.paths.candidate).ino;
        const lock = statSync(files.paths.lock).ino;
        const names = readdirSync(files.root).sort();
        assert.equal(files.write().status, 0);
        assert.equal(statSync(files.paths.candidate).ino, candidate);
        const changed = { ...GUARD, candidateContent: CONTENT + '# edited draft\n' };
        assert.notEqual(files.write(changed).status, 0);
        assert.equal(readFileSync(files.paths.candidate, 'utf8'), CONTENT);
        assert.equal(statSync(files.paths.candidate).ino, candidate);
        assert.equal(statSync(files.paths.lock).ino, lock);
        assert.deepEqual(readdirSync(files.root).sort(), names);
    } finally { files.close() }
});

test('inspection reconciles lost write/install acknowledgements without another mutation', () => {
    const files = fixture();
    try {
        // Real owned filesystem effects occur; deliberately retain no proposal
        // from either acknowledgement. Inspection is the subsequent read only.
        assert.equal(files.write().status, 0);
        const candidate = statSync(files.paths.candidate).ino;
        const lock = statSync(files.paths.lock).ino;
        const beforeWriteReconciliation = readdirSync(files.root).sort();
        assert.equal(inspection(files).candidate, 'matching');
        assert.equal(statSync(files.paths.candidate).ino, candidate);
        assert.deepEqual(readdirSync(files.root).sort(), beforeWriteReconciliation);
        assert.equal(files.run(candidateMutationInvocation('install', GUARD, files.identity)).status, 0);
        const installed = statSync(files.paths.installed).ino;
        const backup = statSync(files.paths.backup).ino;
        const beforeInstallReconciliation = readdirSync(files.root).sort();
        assert.deepEqual(inspection(files), {
            candidate: 'absent', installedBase: 'changed', installedCandidate: 'matching', backupBase: 'matching',
        });
        assert.equal(statSync(files.paths.installed).ino, installed);
        assert.equal(statSync(files.paths.backup).ino, backup);
        assert.equal(statSync(files.paths.lock).ino, lock);
        assert.deepEqual(readdirSync(files.root).sort(), beforeInstallReconciliation);
    } finally { files.close() }
});

test('inspection compares exact Unicode, tag-only edits and trailing newlines without a fingerprint shortcut', () => {
    const files = fixture();
    try {
        inspectionLock(files);
        const base = 'schema_version=1\n[[repositories]]\nid="org/model"\ntype="model"\ntags=["coding"]\n# π 😀\n\n';
        const proposed = base.replace('coding', 'vision') + '\n';
        const guard = { installedContent: base, candidateContent: proposed };
        writeFileSync(files.paths.installed, base);
        writeFileSync(files.paths.candidate, proposed, { mode: 0o640 });
        assert.deepEqual(inspection(files, guard), {
            candidate: 'matching', installedBase: 'matching', installedCandidate: 'changed', backupBase: 'absent',
        });
        writeFileSync(files.paths.candidate, proposed.slice(0, -1));
        assert.equal(inspection(files, guard).candidate, 'changed');
        writeFileSync(files.paths.candidate, proposed.replace('vision', 'other-label'));
        assert.equal(inspection(files, guard).candidate, 'changed');
        assert.equal(readFileSync(files.paths.installed, 'utf8'), base);
    } finally { files.close() }
});

for (const target of ['candidate', 'installed', 'backup'] as const) {
    for (const unsafe of ['symlink', 'hardlink', 'mode', 'directory', 'fifo', 'oversized', 'nul', 'unicode'] as const) {
        test(`inspection preserves unsafe ${target} ${unsafe} as unknown without blocking or file artifacts`, () => {
            const files = fixture();
            try {
                inspectionLock(files);
                writeFileSync(files.paths.candidate, CONTENT, { mode: 0o640 });
                writeFileSync(files.paths.backup, BASE, { mode: 0o640 });
                const evidence = join(files.root, 'unsafe-evidence');
                if (unsafe === 'symlink') {
                    writeFileSync(evidence, 'private fixture evidence', { mode: 0o640 });
                    rmSync(files.paths[target]);
                    symlinkSync(evidence, files.paths[target]);
                } else if (unsafe === 'hardlink') {
                    linkSync(files.paths[target], evidence);
                } else if (unsafe === 'mode') {
                    chmodSync(files.paths[target], 0o666);
                } else if (unsafe === 'directory' || unsafe === 'fifo') {
                    rmSync(files.paths[target]);
                    if (unsafe === 'directory')
                        mkdirSync(files.paths[target]);
                    else
                        execFileSync('mkfifo', [files.paths[target]]);
                } else if (unsafe === 'oversized') {
                    writeFileSync(files.paths[target], 'x'.repeat(MAX_CANDIDATE_BYTES + 1));
                } else {
                    writeFileSync(files.paths[target], Buffer.from(unsafe === 'nul' ? [97, 0, 98] : [0xc0, 0xaf]));
                }
                const inode = lstatSync(files.paths[target]).ino;
                const lock = statSync(files.paths.lock).ino;
                const names = readdirSync(files.root).sort();
                const result = inspection(files);
                if (target === 'installed') {
                    assert.equal(result.installedBase, 'unknown');
                    assert.equal(result.installedCandidate, 'unknown');
                } else {
                    assert.equal(result[target === 'candidate' ? 'candidate' : 'backupBase'], 'unknown');
                }
                assert.equal(lstatSync(files.paths[target]).ino, inode);
                assert.equal(statSync(files.paths.lock).ino, lock);
                assert.deepEqual(readdirSync(files.root).sort(), names);
                assert.equal(existsSync(files.called), false);
            } finally { files.close() }
        });
    }
}

for (const unsafe of ['symlink', 'hardlink', 'mode', 'directory', 'fifo'] as const) {
    test(`inspection refuses unsafe lock ${unsafe} without changing its identity or creating a replacement`, () => {
        const files = fixture();
        try {
            inspectionLock(files);
            if (unsafe === 'symlink') {
                const evidence = join(files.root, 'unsafe-lock-evidence');
                writeFileSync(evidence, '', { mode: 0o600 });
                rmSync(files.paths.lock);
                symlinkSync(evidence, files.paths.lock);
            } else if (unsafe === 'hardlink') {
                linkSync(files.paths.lock, join(files.root, 'unsafe-lock-evidence'));
            } else if (unsafe === 'mode') {
                chmodSync(files.paths.lock, 0o666);
            } else {
                rmSync(files.paths.lock);
                if (unsafe === 'directory')
                    mkdirSync(files.paths.lock);
                else
                    execFileSync('mkfifo', [files.paths.lock]);
            }
            const inode = lstatSync(files.paths.lock).ino;
            const names = readdirSync(files.root).sort();
            assert.deepEqual(inspection(files), UNKNOWN_INSPECTION);
            assert.equal(lstatSync(files.paths.lock).ino, inode);
            assert.deepEqual(readdirSync(files.root).sort(), names);
        } finally { files.close() }
    });
}

test('inspection rejects malformed inert frames and unsafe directory without artifacts or contents', () => {
    const files = fixture();
    try {
        inspectionLock(files);
        const names = readdirSync(files.root).sort();
        for (const input of ['', CONTENT + '\0' + BASE, CONTENT + '\0' + BASE + '\0extra', 'x'.repeat(MAX_CANDIDATE_BYTES + 1) + '\0\0']) {
            const invocation = inspectCandidateInvocation(GUARD, files.identity);
            invocation.input = input;
            const result = files.run(invocation);
            assert.equal(result.status, 0);
            assert.deepEqual(JSON.parse(result.stdout), UNKNOWN_INSPECTION);
            assert.equal(result.stderr, '');
            assert.deepEqual(readdirSync(files.root).sort(), names);
        }
        chmodSync(files.root, 0o777);
        assert.deepEqual(inspection(files), UNKNOWN_INSPECTION);
        assert.deepEqual(readdirSync(files.root).sort(), names);
    } finally { files.close() }
});

test('inspection detects a concurrent change during its bounded read and preserves the changed evidence', () => {
    const files = fixture();
    try {
        inspectionLock(files);
        writeFileSync(files.paths.candidate, CONTENT, { mode: 0o640 });
        files.env.HFCACHE_TEST_CHANGED_PATH = files.paths.installed;
        writeFileSync(join(files.bin, 'dd'), '#!/usr/bin/env bash\n' +
            '/usr/bin/dd "$@"\n' +
            'if [[ "$1" == "if=$HFCACHE_TEST_CHANGED_PATH" ]]; then\n' +
            '  printf "changed by a concurrent editor\\n" > "$HFCACHE_TEST_CHANGED_PATH"\n' +
            'fi\n', { mode: 0o700 });
        const names = readdirSync(files.root).sort();
        const result = inspection(files);
        assert.equal(result.installedBase, 'unknown');
        assert.equal(result.installedCandidate, 'unknown');
        assert.equal(readFileSync(files.paths.installed, 'utf8'), 'changed by a concurrent editor\n');
        assert.deepEqual(readdirSync(files.root).sort(), names);
    } finally { files.close() }
});

test('inspection accepts the full byte bound and rejects malformed UTF-8 rather than normalizing it', () => {
    const files = fixture();
    try {
        inspectionLock(files);
        const candidate = 'λ'.repeat(MAX_CANDIDATE_BYTES / 2);
        const guard = { installedContent: BASE, candidateContent: candidate };
        writeFileSync(files.paths.candidate, candidate, { mode: 0o640 });
        assert.equal(inspection(files, guard).candidate, 'matching');
        for (const invalid of [
            [0x80], [0xc2], [0xed, 0xa0, 0x80], [0xf0, 0x80, 0x80, 0x80], [0xf4, 0x90, 0x80, 0x80],
        ]) {
            writeFileSync(files.paths.candidate, Buffer.from(invalid));
            assert.equal(inspection(files).candidate, 'unknown');
        }
    } finally { files.close() }
});

test('inspection waits on the original configuration flock and observes a concurrent changed base', async () => {
    const files = fixture();
    const entered = join(files.root, 'inspection-lock-entered');
    const release = join(files.root, 'inspection-lock-release');
    let validating: ReturnType<typeof spawn> | null = null;
    let inspecting: ReturnType<typeof spawn> | null = null;
    try {
        assert.equal(files.write().status, 0);
        const lock = statSync(files.paths.lock).ino;
        const held = files.cli();
        validating = spawn(held.argv[0], held.argv.slice(1), {
            env: { ...files.env, HFCACHE_TEST_ENTERED: entered, HFCACHE_TEST_RELEASE: release },
            stdio: ['pipe', 'ignore', 'ignore'],
        });
        const validated = new Promise<number | null>(resolve => validating?.once('exit', resolve));
        validating.stdin?.end(held.input);
        for (let attempt = 0; attempt < 250 && !existsSync(entered); attempt += 1)
            await pause(20);
        assert.ok(existsSync(entered));
        const invocation = inspectCandidateInvocation(GUARD, files.identity);
        inspecting = spawn(invocation.argv[0], invocation.argv.slice(1), {
            env: files.env, stdio: ['pipe', 'pipe', 'ignore'],
        });
        const inspected = new Promise<number | null>(resolve => inspecting?.once('exit', resolve));
        let output = '';
        inspecting.stdout?.on('data', chunk => { output += String(chunk) });
        inspecting.stdin?.end(invocation.input);
        await pause(100);
        assert.equal(inspecting.exitCode, null);
        writeFileSync(files.paths.installed, 'changed while the original flock was held\n');
        writeFileSync(release, 'release');
        assert.equal(await validated, 0);
        assert.equal(await inspected, 0);
        const result = JSON.parse(output) as CandidateInspection;
        assert.equal(result.candidate, 'matching');
        assert.equal(result.installedBase, 'changed');
        assert.equal(result.installedCandidate, 'changed');
        assert.equal(statSync(files.paths.lock).ino, lock);
        assert.equal(readdirSync(files.root).some(name => /^\.(candidate-input|installed-input|predecessor|confirmation)\./.test(name)), false);
    } finally {
        if (validating?.exitCode === null)
            validating.kill('SIGKILL');
        if (inspecting?.exitCode === null)
            inspecting.kill('SIGKILL');
        files.close();
    }
});
