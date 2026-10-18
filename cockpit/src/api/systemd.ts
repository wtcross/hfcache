/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * systemd over D-Bus, as root via the superuser bridge (docs/cockpit.md §2).
 * The guardrails live here structurally: hfcache.target is never operated
 * on (CP-05) and hfcache-verify.timer is display-only (CP-06) — refused in
 * this module rather than trusted to every call site.
 */

import cockpit from 'cockpit';

import { assertOperable } from '../lib/systemd';

export {
    ForbiddenUnitError, HFCACHE_TARGET, SYNC_SERVICE, SYNC_TIMER, VERIFY_SERVICE, VERIFY_TIMER,
} from '../lib/systemd';

const BUS = 'org.freedesktop.systemd1';
const MANAGER_PATH = '/org/freedesktop/systemd1';
const MANAGER = 'org.freedesktop.systemd1.Manager';
const PROPERTIES = 'org.freedesktop.DBus.Properties';
const UNIT = 'org.freedesktop.systemd1.Unit';
const TIMER = 'org.freedesktop.systemd1.Timer';
const SERVICE = 'org.freedesktop.systemd1.Service';

let cachedClient: cockpit.DBusClient | null = null;

function client(): cockpit.DBusClient {
    cachedClient ??= cockpit.dbus(BUS, { bus: 'system', superuser: 'try' });
    return cachedClient;
}

export function startUnit(name: string): Promise<unknown[]> {
    assertOperable(name, 'start');
    return client().call(MANAGER_PATH, MANAGER, 'StartUnit', [name, 'replace']);
}

export function stopUnit(name: string): Promise<unknown[]> {
    assertOperable(name, 'stop');
    return client().call(MANAGER_PATH, MANAGER, 'StopUnit', [name, 'replace']);
}

export function restartUnit(name: string): Promise<unknown[]> {
    assertOperable(name, 'restart');
    return client().call(MANAGER_PATH, MANAGER, 'RestartUnit', [name, 'replace']);
}

export function daemonReload(): Promise<unknown[]> {
    return client().call(MANAGER_PATH, MANAGER, 'Reload', []);
}

export async function enableUnit(name: string): Promise<void> {
    assertOperable(name, 'enable');
    await client().call(MANAGER_PATH, MANAGER, 'EnableUnitFiles', [[name], false, true]);
    await daemonReload();
}

export async function disableUnit(name: string): Promise<void> {
    assertOperable(name, 'disable');
    await client().call(MANAGER_PATH, MANAGER, 'DisableUnitFiles', [[name], false]);
    await daemonReload();
}

async function unitPath(name: string): Promise<string> {
    const [path] = await client().call(MANAGER_PATH, MANAGER, 'LoadUnit', [name]);
    return path as string;
}

type VariantMap = Record<string, { v: unknown } | undefined>;

async function properties(name: string, iface: string): Promise<VariantMap> {
    const path = await unitPath(name);
    const [props] = await client().call(path, PROPERTIES, 'GetAll', [iface]);
    return props as VariantMap;
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
