/* SPDX-License-Identifier: LGPL-2.1-or-later
 * The plugin's fixed unit/action authority (CP-04–06, ADR122).
 */

export const SYNC_SERVICE = 'hfcache-sync.service';
export const VERIFY_SERVICE = 'hfcache-verify.service';
export const SYNC_TIMER = 'hfcache-sync.timer';
export const VERIFY_TIMER = 'hfcache-verify.timer';
export const HFCACHE_TARGET = 'hfcache.target';

export type UnitAction = 'start' | 'stop' | 'restart' | 'enable' | 'disable';

export class ForbiddenUnitError extends Error {}

const ACTIONS = new Map<string, ReadonlySet<UnitAction>>([
    [SYNC_SERVICE, new Set(['start', 'stop'])],
    [VERIFY_SERVICE, new Set(['start'])],
    [SYNC_TIMER, new Set(['start', 'stop', 'restart', 'enable', 'disable'])],
]);

export function assertOperable(unit: string, action: UnitAction): void {
    if (unit === HFCACHE_TARGET)
        throw new ForbiddenUnitError('hfcache.target is never operated from the plugin (CP-05): ' +
            'stopping it unmounts /srv/hfcache; pause only hfcache-sync.timer');
    if (unit === VERIFY_TIMER)
        throw new ForbiddenUnitError('hfcache-verify.timer is display-only (CP-06): ' +
            'operator handoff item 8 owns its calendar');
    if (!ACTIONS.get(unit)?.has(action))
        throw new ForbiddenUnitError('This unit/action is outside the plugin controls: ' +
            'only installed sync/verification clients and the sync schedule are operated');
}
