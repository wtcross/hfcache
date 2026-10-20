/* SPDX-License-Identifier: LGPL-2.1-or-later */
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

test('V43 production plugin source has no direct host run-report archive path', () => {
    const source = fileURLToPath(new URL('../src/', import.meta.url));
    const violations = readdirSync(source, { recursive: true, encoding: 'utf8' })
            .filter(file => /\.[jt]sx?$/.test(file))
            .filter(file => readFileSync(join(source, file), 'utf8').includes('/srv/hfcache/runs'));
    assert.deepEqual(violations, [], 'Run reports must cross the authenticated fixed REST client, including when the client has no archive access');
});

test('V43 the optional host diagnostic adapter exposes no legacy report-file read API', () => {
    const adapter = readFileSync(new URL('../src/api/archive.ts', import.meta.url), 'utf8');
    assert.equal(/export\s+(?:async\s+)?function\s+(?:listRunReports|readRunReport)\b/.test(adapter), false,
                 'The host diagnostic adapter must not retain a privileged report-file fallback');
});
