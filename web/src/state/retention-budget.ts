/** WEB011: shared encoded-data limits and bounded read concurrency, not JS-heap accounting. */
import type { ReadResult } from "../api/types";
export const MAX_RETAINED_BYTES = 32 * 1024 * 1024;
export const SESSION_RESPONSE_BYTES = 8 * 1024 * 1024;
export const READ_RESERVATION_BYTES = SESSION_RESPONSE_BYTES + 4096;

export class StateCapacityError extends Error {
    constructor() {
        super("Browser observation capacity is unavailable.");
        this.name = "StateCapacityError";
    }
}

export function encodedBytes(value: unknown): number {
    if (
        value === undefined ||
        typeof value === "function" ||
        typeof value === "symbol"
    )
        throw new StateCapacityError();
    const encoded = JSON.stringify(value);
    return new TextEncoder().encode(encoded).length;
}

export function logicalReadEvidence<S, F>(result: ReadResult<S, F>): unknown {
    return result.kind === "success" || result.kind === "domain_failure"
        ? { kind: result.kind, response: result.response }
        : result;
}

export interface RetentionBudget {
    readonly maximumBytes: number;
    readonly usedBytes: number;
    claim(owner: string, bytes: number): boolean;
    release(owner: string): void;
}

export function createRetentionBudget(
    maximumBytes = MAX_RETAINED_BYTES,
): RetentionBudget {
    if (
        !Number.isSafeInteger(maximumBytes) ||
        maximumBytes < 1 ||
        maximumBytes > MAX_RETAINED_BYTES
    )
        throw new StateCapacityError();
    const retained = new Map<string, number>();
    let used = 0;
    return Object.freeze({
        maximumBytes,
        get usedBytes() {
            return used;
        },
        claim(owner: string, bytes: number) {
            if (!Number.isSafeInteger(bytes) || bytes < 0)
                throw new StateCapacityError();
            const next = used - (retained.get(owner) ?? 0) + bytes;
            if (next > maximumBytes) return false;
            retained.set(owner, bytes);
            used = next;
            return true;
        },
        release(owner: string) {
            used -= retained.get(owner) ?? 0;
            retained.delete(owner);
        },
    });
}

export interface ReadCoordinator {
    readonly active: number;
    readonly waiting: number;
    run<T>(
        owner: string,
        signal: AbortSignal,
        read: () => Promise<T>,
    ): Promise<T>;
}

function aborted(): DOMException {
    return new DOMException("Observation stopped.", "AbortError");
}
function isAborted(signal: AbortSignal): boolean {
    return signal.aborted;
}

/** One cancelled predecessor may drain while its replacement waits; never overlap its owner. */
export function createReadCoordinator(): ReadCoordinator {
    interface Waiter {
        owner: string;
        signal: AbortSignal;
        grant: () => void;
        reject: (error: Error) => void;
        onAbort: () => void;
    }
    const active = new Map<string, AbortSignal>();
    const queue: Waiter[] = [];
    function drain() {
        while (active.size < 2) {
            const index = queue.findIndex((item) => !active.has(item.owner));
            if (index < 0) return;
            const waiter = queue.splice(index, 1)[0];
            if (waiter === undefined) return;
            waiter.signal.removeEventListener("abort", waiter.onAbort);
            if (waiter.signal.aborted) {
                waiter.reject(aborted());
                continue;
            }
            active.set(waiter.owner, waiter.signal);
            waiter.grant();
        }
    }
    return Object.freeze({
        get active() {
            return active.size;
        },
        get waiting() {
            return queue.length;
        },
        async run<T>(
            owner: string,
            signal: AbortSignal,
            read: () => Promise<T>,
        ): Promise<T> {
            if (signal.aborted) throw aborted();
            const predecessor = active.get(owner);
            if (
                (predecessor !== undefined && !predecessor.aborted) ||
                queue.some((item) => item.owner === owner) ||
                queue.length >= 64
            )
                throw new StateCapacityError();
            await new Promise<void>((resolve, reject) => {
                const waiter: Waiter = {
                    owner,
                    signal,
                    grant: resolve,
                    reject,
                    onAbort: () => {
                        const index = queue.indexOf(waiter);
                        if (index >= 0) queue.splice(index, 1);
                        reject(aborted());
                        drain();
                    },
                };
                signal.addEventListener("abort", waiter.onAbort, {
                    once: true,
                });
                queue.push(waiter);
                drain();
            });
            try {
                if (isAborted(signal)) throw aborted();
                return await read();
            } finally {
                active.delete(owner);
                drain();
            }
        },
    });
}
