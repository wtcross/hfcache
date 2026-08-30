/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Browser navigation for repository rows (docs/cockpit.md §3). Pure logic:
 * no cockpit import and no credential-bearing API surface (CP-08).
 */

import type { RepositoryType } from './command';

const HUGGING_FACE_WEB_ORIGIN = 'https://huggingface.co';

export function huggingFaceRepositoryUrl(type: RepositoryType, id: string): string {
    const encodedId = id.split('/')
            .map(segment => encodeURIComponent(segment))
            .join('/');
    const path = type === 'dataset' ? `datasets/${encodedId}` : encodedId;
    return `${HUGGING_FACE_WEB_ORIGIN}/${path}`;
}
