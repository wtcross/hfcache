/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Browser authority helpers accompanying the Cockpit recovery-registry port.
 * Epochs describe observation sessions; they never replace original authority.
 */

import { createApiScope } from "../api/identity";
import type { ApiScope } from "../api/identity";
import type { ClientOperation } from "../wire/generated";
import { WireError } from "../wire/json";
import { wireObject } from "../wire/runtime";

export type RecordId = string;

export interface AuthSession {
    readonly scope: ApiScope;
    readonly authGeneration: number;
}

export type SafeReceiptIdentity = Readonly<
    Pick<
        ClientOperation,
        | "operation_id"
        | "principal"
        | "route"
        | "archive_id"
        | "config_fingerprint"
        | "created_at"
    >
>;

export interface AuthorizedObservation {
    readonly recordId: RecordId;
    readonly target: ApiScope;
    readonly authGeneration: number;
    readonly locator:
        | { readonly kind: "key"; readonly key: string }
        | { readonly kind: "id"; readonly operationId: string };
    readonly expectedSafeReceiptIdentity: SafeReceiptIdentity | null;
}

export function decodeApiScope(value: unknown): ApiScope {
    const row = wireObject(value, [
        "origin",
        "publicPrefix",
        "authorityEpoch",
        "subject",
        "credentialClass",
        "instanceId",
        "archiveId",
        "configFingerprint",
    ]);
    if (
        typeof row.origin !== "string" ||
        typeof row.publicPrefix !== "string" ||
        typeof row.authorityEpoch !== "string" ||
        typeof row.subject !== "string" ||
        (row.credentialClass !== "rest-reader" &&
            row.credentialClass !== "rest-writer") ||
        (row.instanceId !== null && typeof row.instanceId !== "string") ||
        (row.archiveId !== null && typeof row.archiveId !== "string") ||
        (row.configFingerprint !== null &&
            typeof row.configFingerprint !== "string")
    )
        throw new WireError("schema");
    try {
        return createApiScope({
            origin: row.origin,
            publicPrefix: row.publicPrefix,
            authorityEpoch: row.authorityEpoch,
            subject: row.subject,
            credentialClass: row.credentialClass,
            instanceId: row.instanceId,
            archiveId: row.archiveId,
            configFingerprint: row.configFingerprint,
        });
    } catch {
        throw new WireError("schema");
    }
}

export function createAuthSession(session: AuthSession): AuthSession {
    if (
        !Number.isSafeInteger(session.authGeneration) ||
        session.authGeneration < 0
    )
        throw new WireError("schema");
    return Object.freeze({
        scope: decodeApiScope(session.scope),
        authGeneration: session.authGeneration,
    });
}

/** Stable namespace only: a changed epoch/fingerprint still requires reconnect. */
export function stableAuthorityIdentity(scope: ApiScope): string {
    const checked = decodeApiScope(scope);
    return JSON.stringify([
        checked.origin,
        checked.publicPrefix,
        checked.subject,
        checked.credentialClass,
        checked.archiveId,
    ]);
}

export function sameStableAuthority(left: ApiScope, right: ApiScope): boolean {
    return (
        left.archiveId !== null &&
        right.archiveId !== null &&
        stableAuthorityIdentity(left) === stableAuthorityIdentity(right)
    );
}

export function sameApiScope(left: ApiScope, right: ApiScope): boolean {
    return (
        JSON.stringify(decodeApiScope(left)) ===
        JSON.stringify(decodeApiScope(right))
    );
}

export function sameAuthSession(
    left: AuthSession,
    right: AuthSession,
): boolean {
    return (
        left.authGeneration === right.authGeneration &&
        sameApiScope(left.scope, right.scope)
    );
}

export function receiptIdentity(receipt: ClientOperation): SafeReceiptIdentity {
    return Object.freeze({
        operation_id: receipt.operation_id,
        principal: receipt.principal,
        route: receipt.route,
        archive_id: receipt.archive_id,
        config_fingerprint: receipt.config_fingerprint,
        created_at: receipt.created_at,
    });
}

export function sameReceiptIdentity(
    left: SafeReceiptIdentity,
    right: SafeReceiptIdentity,
): boolean {
    return (
        left.operation_id === right.operation_id &&
        left.principal === right.principal &&
        left.route === right.route &&
        left.archive_id === right.archive_id &&
        left.config_fingerprint === right.config_fingerprint &&
        left.created_at === right.created_at
    );
}
