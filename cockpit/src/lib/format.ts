/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Display formatting. Pure logic: no cockpit import.
 */

const UNITS = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'];

export function formatBytes(bytes: number | null | undefined): string {
    if (bytes === null || bytes === undefined || !Number.isFinite(bytes) || bytes < 0)
        return '—';
    let value = bytes;
    let unit = 0;
    while (value >= 1024 && unit < UNITS.length - 1) {
        value /= 1024;
        unit += 1;
    }
    return `${unit === 0 ? String(value) : value.toFixed(1)} ${UNITS[unit]}`;
}

export function formatTimestamp(iso: string | null | undefined): string {
    if (iso === null || iso === undefined || iso === '')
        return '—';
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString();
}

/* Display truncation only. Anything that goes back into a command uses the
 * full SHA (docs/cli.md §1.1); callers pair this with the full value in a
 * tooltip or copy affordance. */
export function shortSha(sha: string | null | undefined): string {
    return sha === null || sha === undefined ? '—' : sha.slice(0, 12);
}

export function formatHours(hours: number | null | undefined): string {
    if (hours === null || hours === undefined || !Number.isFinite(hours))
        return '—';
    return `${hours.toFixed(1)} h`;
}

export function formatDuration(seconds: number | null | undefined): string {
    if (seconds === null || seconds === undefined || !Number.isFinite(seconds) || seconds < 0)
        return '—';
    if (seconds < 60)
        return `${Math.round(seconds)} s`;
    const minutes = seconds / 60;
    if (minutes < 60)
        return `${Math.round(minutes)} min`;
    const hours = Math.floor(minutes / 60);
    return `${hours} h ${Math.round(minutes - hours * 60)} min`;
}
