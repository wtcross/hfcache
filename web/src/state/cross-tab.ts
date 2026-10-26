/** Bounded advisory signals only; no recovery evidence or execution authority. */
import { canonicalHex } from "../api/identity";
import type { ApiScope } from "../api/identity";
import { parseWireJson, WireError } from "../wire/json";
import { wireInteger, wireObject } from "../wire/runtime";
import { stableAuthorityIdentity } from "./authority";
import type { RecordId } from "./authority";

export const CROSS_TAB_CHANNEL = "hfcache.web.operation-advice.v1";
export const MAX_ADVICE_BYTES = 4096;
export const MAX_ADVICE_SUBSCRIBERS = 32;

export interface AdviceChannel {
    postMessage(message: string): void;
    addEventListener(
        type: "message",
        listener: (event: MessageEvent<unknown>) => void,
    ): void;
    removeEventListener(
        type: "message",
        listener: (event: MessageEvent<unknown>) => void,
    ): void;
    close(): void;
}

export interface CrossTabAdvice {
    publish(recordId: RecordId): boolean;
    subscribe(listener: (recordId: RecordId) => void): () => void;
    dispose(): void;
}

export interface CrossTabAdviceOptions {
    readonly scope: ApiScope;
    readonly channelFactory?: (name: string) => AdviceChannel | null;
}

function defaultChannel(name: string): AdviceChannel | null {
    return typeof BroadcastChannel === "undefined"
        ? null
        : new BroadcastChannel(name);
}

function message(scope: string, recordId: RecordId): string {
    return JSON.stringify({
        schemaVersion: 1,
        kind: "registry-stale",
        scope,
        recordId,
    });
}

/** Same stable authority may advise across API restarts; it never rebinds a handle. */
export function createCrossTabAdvice(
    options: CrossTabAdviceOptions,
): CrossTabAdvice {
    const scope = stableAuthorityIdentity(options.scope);
    if (
        new TextEncoder().encode(message(scope, "0".repeat(32))).byteLength >
        MAX_ADVICE_BYTES
    )
        throw new WireError("bounds");
    const listeners = new Set<(recordId: RecordId) => void>();
    let disposed = false;
    let channel: AdviceChannel | null = null;

    function receive(event: MessageEvent<unknown>): void {
        if (disposed) return;
        let recordId: string;
        try {
            const raw = event.data;
            if (typeof raw !== "string" || raw.length > MAX_ADVICE_BYTES)
                return;
            const row = wireObject(
                parseWireJson(raw, {
                    maxBytes: MAX_ADVICE_BYTES,
                    maxDepth: 2,
                    maxTokens: 16,
                    maxKeys: 4,
                    maxNumberCharacters: 4,
                }),
                ["schemaVersion", "kind", "scope", "recordId"],
            );
            if (
                wireInteger(row.schemaVersion, "1", "1") !== 1 ||
                row.kind !== "registry-stale" ||
                row.scope !== scope ||
                typeof row.recordId !== "string" ||
                !canonicalHex(row.recordId, 32)
            )
                return;
            recordId = row.recordId;
        } catch {
            return;
        }
        for (const listener of listeners) {
            try {
                listener(recordId);
            } catch {
                /* A view cannot turn advice into trusted recovery evidence. */
            }
        }
    }

    try {
        channel = (options.channelFactory ?? defaultChannel)(CROSS_TAB_CHANNEL);
        channel?.addEventListener("message", receive);
    } catch {
        try {
            channel?.close();
        } catch {
            /* Advisory transport has no cleanup or execution authority. */
        }
        channel = null;
    }

    return Object.freeze({
        publish(recordId: RecordId): boolean {
            if (disposed || channel === null || !canonicalHex(recordId, 32))
                return false;
            try {
                channel.postMessage(message(scope, recordId));
                return true;
            } catch {
                return false;
            }
        },
        subscribe(listener: (recordId: RecordId) => void): () => void {
            if (disposed || listeners.size >= MAX_ADVICE_SUBSCRIBERS)
                return () => undefined;
            listeners.add(listener);
            return () => {
                listeners.delete(listener);
            };
        },
        dispose(): void {
            if (disposed) return;
            disposed = true;
            listeners.clear();
            try {
                channel?.removeEventListener("message", receive);
            } catch {
                /* Ignore unavailable advisory transport. */
            }
            try {
                channel?.close();
            } catch {
                /* No outcome or mutation block may be settled here. */
            }
            channel = null;
        },
    });
}
