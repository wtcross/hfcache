/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Build-only public input identity (decision 137); never imported by the browser.
 */
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

export const MAX_BUILD_INPUT_FILES = 1024;
export const MAX_BUILD_INPUT_BYTES = 2 * 1024 * 1024;
export const MAX_BUILD_TOTAL_BYTES = 16 * 1024 * 1024;
const MAX_BUILD_TREE_ENTRIES = 4096;
export const UNKNOWN_BUILD_INFO = Object.freeze({ schema_version: 1, source_commit: null, source_dirty: null, inputs_sha256: null });
const FILES = ['Makefile', 'build.js', 'build-info.js', 'package.json', 'pnpm-lock.yaml'];
const ROOTS = ['src', 'pkg/lib'];
const EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.scss', '.css', '.html', '.json', '.svg', '.png', '.jpg', '.jpeg', '.woff', '.woff2']);
const PRIVATE_DIRECTORIES = new Set(['fixtures', '__fixtures__', 'test', 'tests', 'node_modules']);

/** @typedef {{name:string, bytes:Uint8Array}} PublicBuildInput */
/** @typedef {{schema_version:1,source_commit:string|null,source_dirty:boolean|null,inputs_sha256:string|null}} BrowserBuildInfo */
/** @typedef {{source_commit:string|null,source_dirty:boolean|null,inputs_sha256:string,git_state:string|null}} BuildSnapshot */

export class BuildInputError extends Error {
    constructor() {
        super('Public browser build inputs are unavailable, unsafe or changed during the build. Rebuild from a stable source tree.');
        this.name = 'BuildInputError';
    }
}

/** Advisory provenance has no unsafe traversal fallback on other builders.
 * @param {boolean} production @param {boolean} watch @param {string} platform
 */
export function captureBuildProvenance(production, watch, platform) {
    return production && !watch && platform === 'linux';
}

/** @param {ReadonlyArray<PublicBuildInput>} inputs */
export function hashPublicBuildInputs(inputs) {
    if (inputs.length === 0 || inputs.length > MAX_BUILD_INPUT_FILES)
        throw new BuildInputError();
    const sorted = [...inputs].sort((left, right) => left.name < right.name ? -1 : left.name > right.name ? 1 : 0);
    const hash = createHash('sha256').update('hfcache-cockpit-public-inputs-v1\0');
    let total = 0;
    let previous = '';
    for (const input of sorted) {
        if (typeof input.name !== 'string' || !/^[A-Za-z0-9_@+./-]{1,512}$/.test(input.name) ||
            input.name.startsWith('/') || input.name.split('/').some(part => part === '.' || part === '..' || part === '') ||
            input.name === previous || !(input.bytes instanceof Uint8Array) || input.bytes.byteLength > MAX_BUILD_INPUT_BYTES)
            throw new BuildInputError();
        total += input.bytes.byteLength;
        if (total > MAX_BUILD_TOTAL_BYTES)
            throw new BuildInputError();
        const name = Buffer.from(input.name, 'utf8');
        hash.update(String(name.byteLength) + ':').update(name)
                .update(String(input.bytes.byteLength) + ':')
                .update(input.bytes);
        previous = input.name;
    }
    return hash.digest('hex');
}

/** Read only declared public repository inputs, never hidden/private trees.
 * @param {string} directory
 * @returns {PublicBuildInput[]}
 */
export function publicBuildInputs(directory) {
    /** @type {PublicBuildInput[]} */
    const inputs = [];
    let total = 0;
    let entries = 0;
    const directoryFlags = fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK;
    /** Own directory descriptors are Linux's bounded path anchor. No fallback
     * follows an unchecked ancestor if descriptor traversal is unavailable.
     * @param {number} descriptor
     * @param {string} [leaf]
     */
    const anchored = (descriptor, leaf = '') => '/proc/self/fd/' + descriptor + (leaf === '' ? '' : '/' + leaf);
    /** @param {number} parent @param {string} leaf */
    const openDirectory = (parent, leaf) => {
        const descriptor = fs.openSync(anchored(parent, leaf), directoryFlags);
        if (!fs.fstatSync(descriptor).isDirectory()) {
            fs.closeSync(descriptor);
            throw new BuildInputError();
        }
        return descriptor;
    };
    /** @param {string} name @param {number} parent @param {string} leaf */
    const read = (name, parent, leaf) => {
        if (inputs.length >= MAX_BUILD_INPUT_FILES || !/^[A-Za-z0-9_@+./-]{1,512}$/.test(name))
            throw new BuildInputError();
        let descriptor;
        try {
            descriptor = fs.openSync(anchored(parent, leaf), fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
            const before = fs.fstatSync(descriptor);
            if (!before.isFile() || before.size > MAX_BUILD_INPUT_BYTES || total + before.size > MAX_BUILD_TOTAL_BYTES)
                throw new BuildInputError();
            const bytes = Buffer.alloc(before.size);
            let offset = 0;
            while (offset < bytes.byteLength) {
                const count = fs.readSync(descriptor, bytes, offset, bytes.byteLength - offset, offset);
                if (count === 0)
                    throw new BuildInputError();
                offset += count;
            }
            if (fs.readSync(descriptor, Buffer.alloc(1), 0, 1, before.size) !== 0)
                throw new BuildInputError();
            const after = fs.fstatSync(descriptor);
            if (before.dev !== after.dev || before.ino !== after.ino || before.size !== after.size ||
                before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs || bytes.byteLength !== before.size)
                throw new BuildInputError();
            total += bytes.byteLength;
            inputs.push({ name, bytes });
        } catch {
            throw new BuildInputError();
        } finally {
            if (descriptor !== undefined)
                fs.closeSync(descriptor);
        }
    };
    /** @param {string} name @param {number} descriptor */
    const walk = (name, descriptor) => {
        if (name.split('/').length > 32)
            throw new BuildInputError();
        let cursor;
        try {
            const before = fs.fstatSync(descriptor);
            cursor = fs.opendirSync(anchored(descriptor));
            let entry;
            while ((entry = cursor.readSync()) !== null) {
                entries += 1;
                if (entries > MAX_BUILD_TREE_ENTRIES)
                    throw new BuildInputError();
                if (entry.name.startsWith('.') || PRIVATE_DIRECTORIES.has(entry.name))
                    continue;
                const relative = name + '/' + entry.name;
                if (entry.isSymbolicLink())
                    throw new BuildInputError();
                if (entry.isDirectory()) {
                    const child = openDirectory(descriptor, entry.name);
                    try { walk(relative, child) } finally { fs.closeSync(child) }
                } else if (entry.isFile() && EXTENSIONS.has(path.extname(entry.name)))
                    read(relative, descriptor, entry.name);
                else if (!entry.isFile())
                    throw new BuildInputError();
            }
            const after = fs.fstatSync(descriptor);
            if (before.dev !== after.dev || before.ino !== after.ino || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs)
                throw new BuildInputError();
        } catch {
            throw new BuildInputError();
        } finally {
            cursor?.closeSync();
        }
    };
    let anchor;
    try {
        anchor = fs.openSync(directory, directoryFlags);
        if (!fs.fstatSync(anchor).isDirectory())
            throw new BuildInputError();
        for (const file of FILES)
            read(file, anchor, file);
        for (const root of ROOTS) {
            /** @type {number[]} */
            const prefixes = [];
            try {
                let parent = anchor;
                for (const part of root.split('/')) {
                    parent = openDirectory(parent, part);
                    prefixes.push(parent);
                }
                walk(root, parent);
            } finally {
                for (const descriptor of prefixes.reverse())
                    fs.closeSync(descriptor);
            }
        }
    } catch {
        throw new BuildInputError();
    } finally {
        if (anchor !== undefined)
            fs.closeSync(anchor);
    }
    return inputs;
}

/** @param {string} directory
 * @returns {{source_commit:string|null,source_dirty:boolean|null,git_state:string|null}}
 */
function sourceIdentity(directory) {
    const options = {
        encoding: /** @type {const} */ ('utf8'),
        timeout: 2000,
        maxBuffer: 64 * 1024,
        env: { PATH: process.env.PATH ?? '/usr/bin:/bin', LC_ALL: 'C', GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null' },
        stdio: /** @type {['ignore','pipe','ignore']} */ (['ignore', 'pipe', 'ignore'])
    };
    const commit = spawnSync('git', ['-c', 'core.fsmonitor=false', '-C', directory, 'rev-parse', '--verify', 'HEAD'], options);
    const state = spawnSync('git', ['-c', 'core.fsmonitor=false', '-C', directory, 'status', '--porcelain=v1', '-z', '--untracked-files=normal'], options);
    if (commit.status !== 0 || state.status !== 0 || !/^[0-9a-f]{40}\n?$/.test(commit.stdout))
        return { source_commit: null, source_dirty: null, git_state: null };
    return { source_commit: commit.stdout.trim(), source_dirty: state.stdout !== '', git_state: state.stdout };
}

/** @param {string} directory
 * @returns {Readonly<BuildSnapshot>}
 */
export function captureBuildSnapshot(directory) {
    return Object.freeze({ ...sourceIdentity(directory), inputs_sha256: hashPublicBuildInputs(publicBuildInputs(directory)) });
}

/** @param {Readonly<BuildSnapshot>} snapshot
 * @returns {Readonly<BrowserBuildInfo>}
 */
export function browserBuildInfo(snapshot) {
    return Object.freeze({
        schema_version: 1,
        source_commit: snapshot.source_commit,
        source_dirty: snapshot.source_dirty,
        inputs_sha256: snapshot.inputs_sha256
    });
}

/** @param {Readonly<BuildSnapshot>} before
 * @param {Readonly<BuildSnapshot>} after
 */
export function assertStableBuildSnapshot(before, after) {
    if (before.source_commit !== after.source_commit || before.source_dirty !== after.source_dirty ||
        before.inputs_sha256 !== after.inputs_sha256 || before.git_state !== after.git_state)
        throw new BuildInputError();
}
