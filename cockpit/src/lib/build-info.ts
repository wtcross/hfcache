/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Advisory loaded-browser identity (decision 137), separate from host authority.
 */

export interface BuildInfo {
    readonly schema_version: 1;
    readonly source_commit: string | null;
    readonly source_dirty: boolean | null;
    readonly inputs_sha256: string | null;
}
export const UNKNOWN_BUILD_INFO: Readonly<BuildInfo> = Object.freeze({
    schema_version: 1, source_commit: null, source_dirty: null, inputs_sha256: null,
});

export class BuildInfoError extends Error {
    constructor() {
        super('Browser build provenance is unavailable or incompatible. Obtain a fresh production build and verify the deployed bundle separately.');
        this.name = 'BuildInfoError';
    }
}

export function parseBuildInfo(value: unknown): Readonly<BuildInfo> {
    if (typeof value !== 'object' || value === null)
        throw new BuildInfoError();
    const fields = ['schema_version', 'source_commit', 'source_dirty', 'inputs_sha256'];
    const data: Record<string, unknown> = Object.create(null);
    try {
        if (Array.isArray(value) || Reflect.ownKeys(value).length !== fields.length)
            throw new BuildInfoError();
        for (const name of fields) {
            const descriptor = Object.getOwnPropertyDescriptor(value, name);
            if (!descriptor || !Object.prototype.hasOwnProperty.call(descriptor, 'value'))
                throw new BuildInfoError();
            data[name] = descriptor.value;
        }
    } catch {
        throw new BuildInfoError();
    }
    if (data.schema_version !== 1 ||
        (data.source_commit !== null && (typeof data.source_commit !== 'string' || !/^[0-9a-f]{40}$/.test(data.source_commit))) ||
        (data.source_dirty !== null && typeof data.source_dirty !== 'boolean') ||
        (data.source_commit === null && data.source_dirty !== null) ||
        (data.inputs_sha256 !== null && (typeof data.inputs_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(data.inputs_sha256))))
        throw new BuildInfoError();
    return Object.freeze(data) as unknown as Readonly<BuildInfo>;
}

declare const __HFCACHE_BUILD_INFO__: unknown;
export const embeddedBuildInfo: unknown = typeof __HFCACHE_BUILD_INFO__ === 'undefined'
    ? UNKNOWN_BUILD_INFO
    : __HFCACHE_BUILD_INFO__;

export type BuildComparison = 'unavailable' | 'dirty' | 'mismatch' | 'same-source';
export function compareBuildSource(build: Readonly<BuildInfo>, selectedCommit: string | null): BuildComparison {
    if (build.source_dirty === true)
        return 'dirty';
    if (build.source_commit === null || build.source_dirty === null || build.inputs_sha256 === null ||
        selectedCommit === null || !/^[0-9a-f]{40}$/.test(selectedCommit))
        return 'unavailable';
    return build.source_commit === selectedCommit ? 'same-source' : 'mismatch';
}
