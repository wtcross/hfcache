/* SPDX-License-Identifier: LGPL-2.1-or-later */

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { huggingFaceRepositoryUrl } from '../src/lib/repository.ts';

test('repository links use the type-aware Hugging Face route', () => {
    assert.equal(
        huggingFaceRepositoryUrl('model', 'organization/model-name'),
        'https://huggingface.co/organization/model-name',
    );
    assert.equal(
        huggingFaceRepositoryUrl('dataset', 'organization/dataset-name'),
        'https://huggingface.co/datasets/organization/dataset-name',
    );
});

test('repository links encode identifier path segments', () => {
    assert.equal(
        huggingFaceRepositoryUrl('model', 'organization/model name#card'),
        'https://huggingface.co/organization/model%20name%23card',
    );
});
