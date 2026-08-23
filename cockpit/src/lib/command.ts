/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Building hfcache invocations (docs/cockpit.md §2) and the selector grammar
 * (docs/cli.md §1.1). Pure logic: no cockpit import.
 */

export const HFCACHE_CLI = '/opt/hfcache/current/.venv/bin/hfcache';
export const HFCACHE_CONFIG = '/etc/hfcache/config.toml';
export const SERVICE_IDENTITY = 'hfcache';
/* The deployment's documented default credential name
 * (docs/configuration.md §7). A deployment that renames
 * `hub.credential_name` resolves no page token: `optional` is anonymous and
 * `required` fails closed. Doctor reports the result (docs/cockpit.md §2). */
export const CREDENTIAL_NAME = 'hf-token';

/* The one invocation shape (CP-03): a transient unit that drops to the
 * service identity and speaks JSON. systemd-run rather than runuser
 * (decision 92) so that PID 1 imports the deployment's encrypted Hub
 * credential — `ImportCredential=` is silently skipped when none is installed.
 * That is anonymous fallback under `optional` and `HFARG008` under `required`;
 * the page never touches token bytes (CP-08) — and so the run carries the sync
 * unit's environment, umask, and `MemoryHigh=` (decision 86).
 * `--wait --pipe` propagates the CLI's exit code, which the envelope
 * mapping depends on. `--config` is stated even though it is the
 * default, matching the systemd units and the runbook's `$H`. */
export function hfcacheArgv(command: string[], options?: { config?: string }): string[] {
    return [
        'systemd-run', '--quiet', '--wait', '--pipe', '--collect',
        `--property=User=${SERVICE_IDENTITY}`,
        `--property=Group=${SERVICE_IDENTITY}`,
        `--property=ImportCredential=${CREDENTIAL_NAME}`,
        '--property=UMask=0027',
        '--property=MemoryHigh=4G',
        '--property=Environment=HF_HOME=/var/lib/hfcache/hf-home',
        '--property=Environment=HF_XET_CACHE=/var/cache/hfcache/xet',
        '--',
        HFCACHE_CLI, '--config', options?.config ?? HFCACHE_CONFIG, '--json',
        ...command,
    ];
}

export type RepositoryType = 'model' | 'dataset';

export interface Selector {
    type: RepositoryType;
    id: string;
    sha?: string;
}

const ID_SEGMENT = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const FULL_COMMIT_SHA = /^[0-9a-f]{40}$/;

export function isFullCommitSha(text: string): boolean {
    return FULL_COMMIT_SHA.test(text);
}

export class SelectorError extends Error {}

/* Repository id grammar from docs/configuration.md §6: exactly two segments,
 * each starting alphanumeric, none `.` or `..`, at most 96 characters. */
export function validateRepositoryId(id: string): void {
    if (id.length > 96)
        throw new SelectorError(`repository id is longer than 96 characters: ${id}`);
    const segments = id.split('/');
    if (segments.length !== 2)
        throw new SelectorError(`repository id must be exactly two segments <org>/<repo>: ${id}`);
    for (const segment of segments) {
        if (segment === '.' || segment === '..' || !ID_SEGMENT.test(segment))
            throw new SelectorError(`invalid repository id segment: ${segment || '(empty)'}`);
    }
}

export function formatSelector(selector: Selector): string {
    const base = `${selector.type}:${selector.id}`;
    return selector.sha === undefined ? base : `${base}@${selector.sha}`;
}

/* TYPE:ID or TYPE:ID@SHA. An abbreviated SHA is rejected here for the same
 * reason the CLI rejects it as HFARG001: it is a guess. */
export function parseSelector(text: string): Selector {
    const colon = text.indexOf(':');
    if (colon < 0)
        throw new SelectorError(`selector has no TYPE: prefix: ${text}`);
    const type = text.slice(0, colon);
    if (type !== 'model' && type !== 'dataset')
        throw new SelectorError(`selector type must be model or dataset: ${type}`);
    const rest = text.slice(colon + 1);
    const at = rest.indexOf('@');
    const id = at < 0 ? rest : rest.slice(0, at);
    validateRepositoryId(id);
    if (at < 0)
        return { type, id };
    const sha = rest.slice(at + 1);
    if (!isFullCommitSha(sha))
        throw new SelectorError('revision must be the full 40-character lowercase commit SHA; ' +
                                `an abbreviated SHA is ambiguous: ${sha}`);
    return { type, id, sha };
}
