/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Strict read-only host facts; browser input never provisions permissions.
 */
import { SYNC_SERVICE, SYNC_TIMER, VERIFY_SERVICE, VERIFY_TIMER } from './systemd.ts';
import { BoundaryError } from './failure.ts';

export const HOST_ACTIONS = ['archive', 'hub', 'control', 'schedule', 'configuration', 'observer'] as const;
export type HostAction = typeof HOST_ACTIONS[number];
export const HOST_UNITS = [SYNC_SERVICE, VERIFY_SERVICE, SYNC_TIMER, VERIFY_TIMER] as const;
export type HostUnit = typeof HOST_UNITS[number];
export const MAX_HOST_PROFILE_BYTES = 16 * 1024;
export const DENIED_HOST_PERMISSIONS: Readonly<Record<HostAction, boolean>> = Object.freeze({
    archive: false, hub: false, control: false, schedule: false, configuration: false, observer: false,
});

const UNKNOWN_REASONS = ['policy-missing', 'policy-invalid', 'deployment-unverified', 'facts-unavailable', 'privilege-required'] as const;
export type HostProfileUnknownReason = typeof UNKNOWN_REASONS[number];
export interface HostUnitFacts {
    load: 'loaded' | 'masked' | 'not-found';
    active: 'active' | 'inactive' | 'failed';
    unit_file: 'enabled' | 'enabled-runtime' | 'disabled' | 'static' | 'masked' |
        'masked-runtime' | 'not-found' | 'linked' | 'linked-runtime';
}
export interface KnownHostProfile {
    schema_version: 1;
    state: 'guarded' | 'permitted';
    deployment: 'rootless';
    source_commit: string;
    index_sha256: string;
    image: string;
    policy_sha256: string;
    permissions: Readonly<Record<HostAction, boolean>>;
    facts: {
        guard: 'held' | 'inactive' | 'absent';
        archive_mount: 'nfs-ro' | 'local-ro' | 'local-rw' | 'absent';
        units: Readonly<Record<HostUnit, Readonly<HostUnitFacts>>>;
    };
}
export interface UnknownHostProfile {
    schema_version: 1;
    state: 'unknown';
    reason: HostProfileUnknownReason;
}
export type HostProfile = Readonly<KnownHostProfile> | Readonly<UnknownHostProfile>;

const REASONS: Record<HostProfileUnknownReason, string> = {
    'policy-missing': 'Explicit administrator host permissions are not provisioned. Host effects are unavailable.',
    'policy-invalid': 'Administrator host permissions are unsafe, changed or incompatible. Host effects are unavailable.',
    'deployment-unverified': 'The selected deployment or fixed launcher binding is unverified. Host effects are unavailable.',
    'facts-unavailable': 'Current host restrictions or unit facts are unavailable. Host effects are unavailable.',
    'privilege-required': 'Administrative access is required to inspect host restrictions.',
};
const ACTION_NAMES: Record<HostAction, string> = {
    archive: 'Archive jobs',
    hub: 'Sizing and diagnostic jobs',
    control: 'Control jobs',
    schedule: 'Sync scheduling',
    configuration: 'Configuration changes',
    observer: 'Stopping the scheduled sync observer',
};
export const HOST_PROFILE_UNAVAILABLE = 'Obtain fresh trusted host restrictions before changing the host or submitting a job.';

export class HostProfileError extends Error {
    constructor(message = HOST_PROFILE_UNAVAILABLE) {
        super(message);
        this.name = 'HostProfileError';
    }
}

/* A later preflight refusal cannot undo an already acknowledged host effect.
 * Retain safe classified facts, never the raw exception or host diagnostics. */
export class AcknowledgedHostChangeError extends BoundaryError {
    readonly restrictionReason: string | null;
    constructor(failure: unknown, stage: 'schedule-write' | 'unit-mutation') {
        super(failure instanceof HostProfileError ? { problem: 'access-denied' } : failure,
              { stage, hostMutationUncertain: true });
        this.name = 'AcknowledgedHostChangeError';
        this.restrictionReason = failure instanceof HostProfileError ? failure.message : null;
    }
}

function object(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function fields(value: Record<string, unknown>, names: readonly string[]): boolean {
    return Object.keys(value).length === names.length && names.every(name =>
        Object.prototype.hasOwnProperty.call(value, name));
}
function knownUnit(value: unknown): value is HostUnitFacts {
    return object(value) && fields(value, ['load', 'active', 'unit_file']) &&
        ['loaded', 'masked', 'not-found'].includes(value.load as string) &&
        ['active', 'inactive', 'failed'].includes(value.active as string) &&
        ['enabled', 'enabled-runtime', 'disabled', 'static', 'masked', 'masked-runtime',
            'not-found', 'linked', 'linked-runtime'].includes(value.unit_file as string);
}
function usableUnit(value: HostUnitFacts): boolean {
    return value.load === 'loaded' && !['masked', 'masked-runtime', 'not-found'].includes(value.unit_file);
}

/* JSON.parse checks grammar; this bounded lexical pass separately rejects
 * duplicate decoded keys, including escaped aliases, without echoing input. */
function uniqueKeys(output: string): void {
    const stack: Array<Set<string> | null> = [];
    for (const match of output.matchAll(/"(?:[^"\\]|\\[\s\S])*"|[{}[\]]/g)) {
        const token = match[0];
        if (token === '{' || token === '[') {
            stack.push(token === '{' ? new Set() : null);
            if (stack.length > 8)
                throw new HostProfileError();
        } else if (token === '}' || token === ']') {
            stack.pop();
        } else if (/^\s*:/.test(output.slice(match.index! + token.length))) {
            const keys = stack[stack.length - 1];
            const key = JSON.parse(token) as string;
            if (!keys || keys.has(key))
                throw new HostProfileError();
            keys.add(key);
        }
    }
}

export function parseHostProfile(output: string): HostProfile {
    try {
        if (typeof output !== 'string' || new TextEncoder().encode(output).length > MAX_HOST_PROFILE_BYTES)
            throw new HostProfileError();
        const parsed: unknown = JSON.parse(output);
        uniqueKeys(output);
        if (!object(parsed) || parsed.schema_version !== 1)
            throw new HostProfileError();
        if (parsed.state === 'unknown') {
            if (!fields(parsed, ['schema_version', 'state', 'reason']) ||
                !UNKNOWN_REASONS.includes(parsed.reason as HostProfileUnknownReason))
                throw new HostProfileError();
            return Object.freeze(parsed) as unknown as Readonly<UnknownHostProfile>;
        }
        const permissions = parsed.permissions;
        const facts = parsed.facts;
        const units = object(facts) ? facts.units : null;
        if (!fields(parsed, ['schema_version', 'state', 'deployment', 'source_commit', 'index_sha256',
            'image', 'policy_sha256', 'permissions', 'facts']) ||
            !['guarded', 'permitted'].includes(parsed.state as string) || parsed.deployment !== 'rootless' ||
            typeof parsed.source_commit !== 'string' || !/^[0-9a-f]{40}$/.test(parsed.source_commit) ||
            typeof parsed.index_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(parsed.index_sha256) ||
            typeof parsed.image !== 'string' || !/^sha256:[0-9a-f]{64}$/.test(parsed.image) ||
            typeof parsed.policy_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(parsed.policy_sha256) ||
            !object(permissions) || !fields(permissions, HOST_ACTIONS) ||
            !HOST_ACTIONS.every(action => typeof permissions[action] === 'boolean') ||
            !object(facts) || !fields(facts, ['guard', 'archive_mount', 'units']) ||
            !['held', 'inactive', 'absent'].includes(facts.guard as string) ||
            !['nfs-ro', 'local-ro', 'local-rw', 'absent'].includes(facts.archive_mount as string) ||
            !object(units) || !fields(units, HOST_UNITS) ||
            !HOST_UNITS.every(unit => knownUnit(units[unit])))
            throw new HostProfileError();
        const profile = parsed as unknown as KnownHostProfile;
        if ((profile.state === 'guarded') !== (profile.facts.guard === 'held') ||
            (profile.facts.guard === 'held' && profile.permissions.archive) ||
            (profile.permissions.schedule && (!usableUnit(profile.facts.units[SYNC_TIMER]) ||
                !usableUnit(profile.facts.units[SYNC_SERVICE]))) ||
            (profile.permissions.observer && !usableUnit(profile.facts.units[SYNC_SERVICE])))
            throw new HostProfileError();
        Object.freeze(profile.permissions);
        for (const unit of HOST_UNITS)
            Object.freeze(profile.facts.units[unit]);
        Object.freeze(profile.facts.units);
        Object.freeze(profile.facts);
        return Object.freeze(profile);
    } catch {
        throw new HostProfileError('Host restriction metadata is incompatible. Preserve the selected artifacts and administrator policy for review.');
    }
}

export function profileActionAllowed(profile: HostProfile | null, action: HostAction): boolean {
    return HOST_ACTIONS.includes(action) && profile !== null && profile.state !== 'unknown' &&
        profile.permissions[action] === true;
}
export function profileActionReason(profile: HostProfile | null, action?: HostAction): string {
    if (profile === null)
        return HOST_PROFILE_UNAVAILABLE;
    if (profile.state === 'unknown')
        return REASONS[profile.reason];
    if (action !== undefined && !profileActionAllowed(profile, action)) {
        if (action === 'archive' && profile.facts.guard === 'held')
            return 'Archive jobs are blocked by the retained read-only guard. Preserve the original lock and workload holds.';
        return `${ACTION_NAMES[action]} are not approved by the trusted host profile or required unit bindings.`;
    }
    return profile.state === 'guarded'
        ? 'The read-only archive guard remains held. Other effects require their own explicit host permission.'
        : 'Verified host profile; each effect still requires explicit permission and final API/storage checks.';
}
