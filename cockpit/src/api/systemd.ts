/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * systemd over D-Bus, as root via the superuser bridge (docs/cockpit.md §2).
 * The guardrails live here structurally: hfcache.target is never operated
 * on (CP-05) and hfcache-verify.timer is display-only (CP-06) — refused in
 * this module rather than trusted to every call site.
 */

import cockpit from 'cockpit';

import { assertOperable, SYNC_SERVICE } from '../lib/systemd';
import { normalizeFailure } from '../lib/failure';
import { assertSession, captureSession, hostCall, systemConnection } from './connection';
import { requireHostAction } from './profile';
import { AcknowledgedHostChangeError, HostProfileError } from '../lib/host-profile';
import type { HostAction } from '../lib/host-profile';

export {
    ForbiddenUnitError, HFCACHE_TARGET, SYNC_SERVICE, SYNC_TIMER, VERIFY_SERVICE, VERIFY_TIMER,
} from '../lib/systemd';

const MANAGER_PATH = '/org/freedesktop/systemd1';
const MANAGER = 'org.freedesktop.systemd1.Manager';
const PROPERTIES = 'org.freedesktop.DBus.Properties';
const UNIT = 'org.freedesktop.systemd1.Unit';
const TIMER = 'org.freedesktop.systemd1.Timer';
const SERVICE = 'org.freedesktop.systemd1.Service';

async function mutate(method: string, arguments_: unknown[], action: HostAction): Promise<unknown[]> {
    const generation = captureSession('unit-mutation');
    const host = cockpit.transport.host;
    await requireHostAction(action);
    assertSession(generation, 'unit-mutation');
    if (host !== cockpit.transport.host)
        throw new HostProfileError();
    return hostCall('unit-mutation', true, () => systemConnection.mutate(client =>
        client.call(MANAGER_PATH, MANAGER, method, arguments_, { timeout: 5000 })));
}

export function startUnit(name: string): Promise<unknown[]> {
    assertOperable(name, 'start');
    return mutate('StartUnit', [name, 'replace'], 'schedule');
}

export function stopUnit(name: string): Promise<unknown[]> {
    assertOperable(name, 'stop');
    return mutate('StopUnit', [name, 'replace'], name === SYNC_SERVICE ? 'observer' : 'schedule');
}

export function restartUnit(name: string): Promise<unknown[]> {
    assertOperable(name, 'restart');
    return mutate('RestartUnit', [name, 'replace'], 'schedule');
}

export function daemonReload(): Promise<unknown[]> {
    return mutate('Reload', [], 'schedule');
}

export async function enableUnit(name: string): Promise<void> {
    assertOperable(name, 'enable');
    const generation = captureSession('unit-mutation');
    await mutate('EnableUnitFiles', [[name], false, false], 'schedule');
    try {
        assertSession(generation, 'unit-mutation', true);
        await daemonReload();
    } catch (failure) {
        throw new AcknowledgedHostChangeError(failure, 'unit-mutation');
    }
}

export async function disableUnit(name: string): Promise<void> {
    assertOperable(name, 'disable');
    const generation = captureSession('unit-mutation');
    await mutate('DisableUnitFiles', [[name], false], 'schedule');
    try {
        assertSession(generation, 'unit-mutation', true);
        await daemonReload();
    } catch (failure) {
        throw new AcknowledgedHostChangeError(failure, 'unit-mutation');
    }
}

type VariantMap = Record<string, { v: unknown } | undefined>;

async function properties(name: string, iface: string): Promise<VariantMap> {
    try {
        return await systemConnection.read(async client => {
            const [path] = await client.call(MANAGER_PATH, MANAGER, 'LoadUnit', [name], { timeout: 5000 });
            if (typeof path !== 'string' || !path.startsWith('/org/freedesktop/systemd1/unit/'))
                throw new Error('Invalid unit path');
            const [props] = await client.call(path, PROPERTIES, 'GetAll', [iface], { timeout: 5000 });
            if (typeof props !== 'object' || props === null || Array.isArray(props))
                throw new Error('Invalid unit properties');
            return props as VariantMap;
        });
    } catch (error) {
        throw normalizeFailure(error, { stage: 'unit-read' });
    }
}

export interface UnitState {
    activeState: string;
    subState: string;
    unitFileState: string;
}

export async function unitState(name: string): Promise<UnitState> {
    const props = await properties(name, UNIT);
    return {
        activeState: String(props.ActiveState?.v ?? 'unknown'),
        subState: String(props.SubState?.v ?? ''),
        unitFileState: String(props.UnitFileState?.v ?? ''),
    };
}

export interface ServiceResult {
    result: string;
    execMainStatus: number;
}

export async function serviceResult(name: string): Promise<ServiceResult> {
    const props = await properties(name, SERVICE);
    return {
        result: String(props.Result?.v ?? 'unknown'),
        execMainStatus: Number(props.ExecMainStatus?.v ?? -1),
    };
}

export interface TimerState {
    nextElapse: Date | null;
    lastTrigger: Date | null;
}

function usecToDate(value: unknown): Date | null {
    const usec = typeof value === 'number' ? value : Number(value ?? 0);
    // 0 means "none scheduled"; huge values are systemd's USEC_INFINITY.
    if (!Number.isFinite(usec) || usec <= 0 || usec >= 2 ** 62)
        return null;
    return new Date(usec / 1000);
}

export async function timerState(name: string): Promise<TimerState> {
    const props = await properties(name, TIMER);
    return {
        nextElapse: usecToDate(props.NextElapseUSecRealtime?.v),
        lastTrigger: usecToDate(props.LastTriggerUSec?.v),
    };
}
