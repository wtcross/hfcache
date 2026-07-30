/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Warning codes and their operator responses, carried inline so the UI
 * teaches the runbook (docs/cockpit.md §3). The source of truth is
 * docs/operations.md §8; test/warnings.test.ts parses that table and fails
 * this file when it drifts. Pure logic: no cockpit import.
 */

export interface WarningGuidance {
    meaning: string;
    response: string;
}

export const WARNING_GUIDANCE: Record<string, WarningGuidance> = {
    HFDEP001: {
        meaning: 'Undeclared dependency detected in repository metadata',
        response: 'Add it to declared_dependencies, or configure the dependency as its own ' +
            'repository. Never downloaded implicitly.',
    },
    HFWRN001: {
        meaning: 'Temporary over-retention: a deferred prune left six revisions',
        response: 'Run recover --dry-run, then prune --apply.',
    },
    HFWRN002: {
        meaning: 'Logical prune committed, trash removal outstanding',
        response: 'Physical only; the revision is gone logically. recover --apply retries the cleanup.',
    },
    HFWRN003: {
        meaning: 'Unknown files in an application-owned area',
        response: 'Preserved, never deleted. Identify them before removing anything by hand.',
    },
    HFWRN004: {
        meaning: 'Stale staging directory',
        response: 'A run stopped part way and aged past sync.stale_staging_age_hours. ' +
            'Run recover --dry-run.',
    },
    HFWRN005: {
        meaning: 'Free space approaching the configured reserve',
        response: 'Capacity work. Note ZFS snapshots hold blocks after an application prune.',
    },
    HFWRN006: {
        meaning: 'Upstream repository unreachable',
        response: 'Nothing to do. Every local revision is preserved; this never triggers a prune.',
    },
    HFWRN007: {
        meaning: 'Archived repository is not in configuration',
        response: 'Expected after removing one. Its revisions are kept.',
    },
    HFWRN008: {
        meaning: 'Retired repair instance past its grace period',
        response: 'recover --apply quarantines it.',
    },
    HFWRN009: {
        meaning: 'Local Xet transfer cache exceeded its advisory ceiling',
        response: 'Writer-local disk, not the archive. Check /var/cache/hfcache/xet.',
    },
    HFWRN010: {
        meaning: 'Verification may overlap storage maintenance',
        response: 'Reschedule one of them.',
    },
};
