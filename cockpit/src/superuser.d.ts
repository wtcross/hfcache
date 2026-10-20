/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Public API documented by the pinned pkg/lib/superuser.js.
 */
declare module 'superuser' {
    export const superuser: {
        readonly allowed: boolean | null;
        addEventListener(event: 'changed' | 'reconnect', listener: () => void): void;
        removeEventListener(event: 'changed' | 'reconnect', listener: () => void): void;
    };
}
