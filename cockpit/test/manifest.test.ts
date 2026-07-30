/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Scaffold test proving the node:test runner (chosen at CPT-002,
 * docs/cockpit.md §9): node 24 runs TypeScript directly via type stripping,
 * so unit tests carry no runner dependency at all.
 */

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

test('manifest registers the hfcache package', () => {
    const manifest = JSON.parse(
        readFileSync(new URL('../src/manifest.json', import.meta.url), 'utf8'));
    assert.equal(manifest.tools.index.label, 'hfcache');
    assert.ok(manifest.requires.cockpit, 'a minimum cockpit version is declared');
});
