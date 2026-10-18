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
    candidateMutationInvocation, CONFIGURATION_PATHS, guardCandidateInvocation,
    MAX_CANDIDATE_BYTES, readInstalledInvocation, validateCandidateText,
} from '../src/lib/candidate-guard.ts';
import type { CandidateGuard, ConfigurationFixture, GuardedInvocation } from '../src/lib/candidate-guard.ts';

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
    const response = join(root, 'response');
    writeFileSync(response, '{"fixture":"API response"}\n');
    writeFileSync(join(bin, 'systemd-run'), '#!/usr/bin/env bash\n' +
        'printf called > "$HFCACHE_TEST_CALLED"\n' +
        'if [[ -n "$HFCACHE_TEST_ENTERED" ]]; then\n' +
        '  : > "$HFCACHE_TEST_ENTERED"\n' +
        '  for ((i=0; i<250; i++)); do [[ -f "$HFCACHE_TEST_RELEASE" ]] && break; sleep .02; done\n' +
        '  [[ -f "$HFCACHE_TEST_RELEASE" ]] || exit 99\n' +
        'fi\n' +
        'cat "$HFCACHE_TEST_RESPONSE"\n', { mode: 0o700 });
    const env = {
        ...process.env,
        PATH: bin + delimiter + process.env.PATH,
        HFCACHE_TEST_CALLED: called,
        HFCACHE_TEST_RESPONSE: response,
    };
    const run = (invocation: GuardedInvocation) => spawnSync(invocation.argv[0], invocation.argv.slice(1), {
        input: invocation.input, encoding: 'utf8', env, timeout: 10000, maxBuffer: 4 * 1024 * 1024,
    });
    const write = (guard: CandidateGuard = GUARD) => run(candidateMutationInvocation('write', guard, identity));
    const cli = (guard: CandidateGuard = GUARD) => guardCandidateInvocation(
        ['systemd-run', '--', '/opt/hfcache/current/.venv/bin/hfcache', '--config', paths.candidate,
            '--json', 'config', 'validate'], guard, identity,
    );
    return {
        root,
        paths,
        identity,
        bin,
        env,
        called,
        run,
        write,
        cli,
        close: () => rmSync(root, { recursive: true, force: true })
    };
}

test('fixed production helper keeps content in stdin and imports no arbitrary command/path option', () => {
    const invocation = guardCandidateInvocation(['systemd-run', '--', 'fixed-cli'], GUARD);
    assert.equal(invocation.input, CONTENT + '\0' + BASE + '\0');
    assert.ok(!invocation.argv.some(argument => argument.includes(CONTENT) || argument.includes(BASE)));
    for (const path of Object.values(CONFIGURATION_PATHS))
        assert.ok(invocation.argv.includes(path));
    assert.throws(() => guardCandidateInvocation(['sh', '-c', 'untrusted'], GUARD));
});

test('bounded UTF-8 framing rejects NUL, lone surrogates and byte overflow before spawn', () => {
    for (const value of ['', '\0', 'a\0b', '\ud800', '\udfff', 'é'.repeat(MAX_CANDIDATE_BYTES)])
        assert.throws(() => validateCandidateText(value));
    validateCandidateText('λ\n'.repeat(100));
    validateCandidateText('a'.repeat(MAX_CANDIDATE_BYTES));
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
