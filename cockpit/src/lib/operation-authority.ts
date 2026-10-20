/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Safe presentation of validated client authority; never browser routing input.
 */
import type { Envelope } from './envelope.ts';
import type { OperationScope } from './operation-registry.ts';
import { validOperationScope } from './operation-registry.ts';

type AuthorityProblem = 'unavailable' | 'invalid' | 'changed' | 'unknown-archive';
const MESSAGES: Record<AuthorityProblem, string> = {
    unavailable: 'Authenticated client authority is unavailable. No operation was submitted.',
    invalid: 'Client authority metadata is incompatible. Verify the selected client and plugin artifacts.',
    changed: 'The selected client authority changed. Preserve original handles before another action.',
    'unknown-archive': 'The client has not confirmed an archive UUID. Operation submission and saved observation are unavailable.',
};

export class OperationAuthorityError extends Error {
    readonly envelope: Envelope | null;
    constructor(reason: AuthorityProblem, envelope: Envelope | null = null) {
        super(MESSAGES[reason]);
        this.name = 'OperationAuthorityError';
        this.envelope = envelope;
    }
}

export function operationAuthority(envelope: Envelope, host: string): Readonly<OperationScope> {
    if (envelope.exit_code !== 0)
        throw new OperationAuthorityError('unavailable', envelope);
    const data = envelope.data;
    if (envelope.command !== 'client describe' || typeof data !== 'object' || data === null || Array.isArray(data))
        throw new OperationAuthorityError('invalid', envelope);
    const row = data as Record<string, unknown>;
    const fields = ['metadata_schema_version', 'profile_fingerprint', 'authority_fingerprint', 'endpoint',
        'credential_class', 'archive_id', 'instance_id'];
    if (Object.keys(row).length !== fields.length || !fields.every(field => Object.prototype.hasOwnProperty.call(row, field)) ||
        row.metadata_schema_version !== 1)
        throw new OperationAuthorityError('invalid', envelope);
    const scope = {
        host,
        profile: row.profile_fingerprint,
        authorityFingerprint: row.authority_fingerprint,
        endpoint: row.endpoint,
        credentialClass: row.credential_class,
        archiveId: row.archive_id,
        instanceId: row.instance_id,
    };
    if (!validOperationScope(scope))
        throw new OperationAuthorityError('invalid', envelope);
    return Object.freeze(scope);
}
