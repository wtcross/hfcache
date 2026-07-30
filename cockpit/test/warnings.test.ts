/* SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * The repository's pattern applied to the plugin: the test parses the
 * runbook, so the guidance the UI shows cannot drift from
 * docs/operations.md §8 without failing here.
 */

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { WARNING_GUIDANCE } from '../src/lib/warnings.ts';

test('the warning guidance covers exactly the ops §8 table', () => {
    const operations = readFileSync(new URL('../../docs/operations.md', import.meta.url), 'utf8');
    const documented = new Set<string>();
    for (const match of operations.matchAll(/^\| `(HF(?:WRN|DEP)\d{3})` \|/gm))
        documented.add(match[1]);

    assert.ok(documented.size >= 11, `parsed only ${documented.size} codes from ops §8`);
    for (const code of documented) {
        assert.ok(WARNING_GUIDANCE[code], `ops §8 documents ${code} but the UI has no guidance`);
        assert.ok(WARNING_GUIDANCE[code].meaning.length > 0, code);
        assert.ok(WARNING_GUIDANCE[code].response.length > 0, code);
    }
    for (const code of Object.keys(WARNING_GUIDANCE))
        assert.ok(documented.has(code), `UI carries ${code} but ops §8 does not document it`);
});
