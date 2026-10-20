/* SPDX-License-Identifier: LGPL-2.1-or-later
 * A fresh fixed read-only helper proof precedes each effect; cached UI facts do not authorize it.
 */
import cockpit from 'cockpit';

import { assertSession, captureSession, connectionSnapshot, hostCall } from './connection';
import {
    DENIED_HOST_PERMISSIONS, HOST_PROFILE_UNAVAILABLE, HostProfileError, MAX_HOST_PROFILE_BYTES, parseHostProfile,
    profileActionAllowed, profileActionReason,
} from '../lib/host-profile';
import type { HostAction, HostProfile } from '../lib/host-profile';
import { normalizeFailure } from '../lib/failure';

export const HOST_PROFILE_ARGV = Object.freeze(['/usr/local/libexec/hfcache-container-service', 'inspect-cockpit']);
export interface HostProfileSnapshot {
    profile: HostProfile | null;
    permissions: Readonly<Record<HostAction, boolean>>;
    reason: string;
    loading: boolean;
    error: Error | null;
    generation: number;
    host: string;
}
let snapshot: HostProfileSnapshot = Object.freeze({
    profile: null,
    permissions: DENIED_HOST_PERMISSIONS,
    reason: HOST_PROFILE_UNAVAILABLE,
    loading: false,
    error: null,
    generation: -1,
    host: '',
});
let requestSequence = 0;
const listeners = new Set<() => void>();
const publish = (patch: Partial<HostProfileSnapshot>) => {
    snapshot = Object.freeze({ ...snapshot, ...patch });
    for (const listener of listeners) {
        try { listener() } catch { /* A detached UI cannot change a host inspection. */ }
    }
};
export const profileSnapshot = () => snapshot;
export const subscribeProfile = (listener: () => void) => {
    listeners.add(listener);
    return () => { listeners.delete(listener) };
};
function fresh(): boolean {
    const connection = connectionSnapshot();
    return connection.administrative && snapshot.generation === connection.generation &&
        snapshot.host === cockpit.transport.host && !snapshot.loading && snapshot.error === null;
}
export function hostActionAllowed(action: HostAction): boolean {
    return fresh() && profileActionAllowed(snapshot.profile, action);
}
export function hostActionReason(action: HostAction): string {
    return fresh() ? profileActionReason(snapshot.profile, action) : HOST_PROFILE_UNAVAILABLE;
}

export async function readHostProfile(): Promise<HostProfile> {
    const request = ++requestSequence;
    const host = cockpit.transport.host;
    let generation = -1;
    publish({
        loading: true,
        error: null,
        profile: null,
        permissions: DENIED_HOST_PERMISSIONS,
        reason: HOST_PROFILE_UNAVAILABLE,
        host,
        generation
    });
    try {
        generation = captureSession('profile-read');
        const output = await hostCall('profile-read', false, async () => {
            const process = cockpit.spawn([...HOST_PROFILE_ARGV], { superuser: 'require', err: 'message' });
            let content = '';
            let size = 0;
            let overflow = false;
            process.stream(chunk => {
                size += new TextEncoder().encode(chunk).length;
                if (size > MAX_HOST_PROFILE_BYTES)
                    overflow = true;
                if (!overflow)
                    content += chunk;
            });
            await process;
            if (overflow)
                throw new HostProfileError();
            return content;
        });
        assertSession(generation, 'profile-read');
        if (host !== cockpit.transport.host)
            throw new HostProfileError();
        const profile = parseHostProfile(output);
        if (request === requestSequence)
            publish({
                profile,
                permissions: profile.state === 'unknown' ? DENIED_HOST_PERMISSIONS : profile.permissions,
                reason: profileActionReason(profile),
                loading: false,
                error: null,
                host,
                generation
            });
        return profile;
    } catch (failure) {
        const error = failure instanceof HostProfileError ? failure : normalizeFailure(failure, { stage: 'profile-read' });
        if (request === requestSequence)
            publish({
                profile: null,
                permissions: DENIED_HOST_PERMISSIONS,
                reason: HOST_PROFILE_UNAVAILABLE,
                loading: false,
                error,
                host,
                generation
            });
        throw error;
    }
}

export async function requireHostAction(action: HostAction): Promise<HostProfile> {
    const generation = captureSession('profile-read');
    const host = cockpit.transport.host;
    const profile = await readHostProfile();
    assertSession(generation, 'profile-read');
    if (host !== cockpit.transport.host || snapshot.profile !== profile || !fresh() ||
        !profileActionAllowed(profile, action))
        throw new HostProfileError(profileActionReason(profile, action));
    return profile;
}
