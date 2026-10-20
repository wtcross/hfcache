/* SPDX-License-Identifier: LGPL-2.1-or-later
 * CP-02/03: own one close-aware connection; retry bounded reads, never writes.
 */

export interface ManagedClient {
    addEventListener(name: 'close', listener: () => void): void;
    removeEventListener(name: 'close', listener: () => void): void;
    close(): void;
}

function interrupted(): Error {
    return Object.assign(new Error('The host connection changed'), { problem: 'reconnected' });
}

function reconnectable(error: unknown): boolean {
    const problem = typeof error === 'object' && error !== null
        ? (error as { problem?: unknown }).problem
        : undefined;
    return ['reconnected', 'disconnected', 'terminated', 'timeout', 'no-cockpit'].includes(String(problem));
}

export class OwnedConnection<C extends ManagedClient> {
    private factory: () => C;
    private pause: (milliseconds: number) => Promise<void>;
    private current: { client: C; closed: () => void } | null = null;
    private epoch = 0;
    private listeners = new Set<() => void>();
    private ownerKey: () => string;
    private observedOwner: string;

    constructor(factory: () => C, pause = (milliseconds: number) =>
        new Promise<void>(resolve => setTimeout(resolve, milliseconds)), ownerKey = () => '') {
        this.factory = factory;
        this.pause = pause;
        this.ownerKey = ownerKey;
        this.observedOwner = ownerKey();
    }

    private synchronizeOwner(): void {
        if (this.observedOwner !== this.ownerKey())
            this.invalidate();
    }

    get generation(): number { this.synchronizeOwner(); return this.epoch }

    subscribe(listener: () => void): () => void {
        this.listeners.add(listener);
        return () => { this.listeners.delete(listener) };
    }

    invalidate(): void {
        this.observedOwner = this.ownerKey();
        const previous = this.current;
        this.current = null;
        this.epoch += 1;
        if (previous !== null) {
            // Disposal cannot hide the original failure or prevent invalidation.
            try { previous.client.removeEventListener('close', previous.closed) } catch { /* detached */ }
            try { previous.client.close() } catch { /* already unavailable */ }
        }
        for (const listener of this.listeners) {
            try { listener() } catch { /* one view cannot suppress other subscribers */ }
        }
    }

    private client(): C {
        this.synchronizeOwner();
        if (this.current === null) {
            const client = this.factory();
            const closed = () => {
                if (this.current?.client === client)
                    this.invalidate();
            };
            this.current = { client, closed };
            client.addEventListener('close', closed);
        }
        return this.current.client;
    }

    async read<T>(action: (client: C) => Promise<T>): Promise<T> {
        for (let attempt = 0; ; attempt += 1) {
            const client = this.client();
            const generation = this.generation;
            try {
                const result = await action(client);
                if (generation !== this.generation)
                    throw interrupted();
                return result;
            } catch (error) {
                const changed = generation !== this.generation;
                if (!changed && !reconnectable(error))
                    throw error;
                if (!changed)
                    this.invalidate();
                if (attempt >= 1)
                    throw error;
                await this.pause(100);
            }
        }
    }

    async mutate<T>(action: (client: C) => Promise<T>): Promise<T> {
        const client = this.client();
        const generation = this.generation;
        try {
            const result = await action(client);
            if (generation !== this.generation)
                throw interrupted();
            return result;
        } catch (error) {
            if (generation === this.generation && reconnectable(error))
                this.invalidate();
            throw error;
        }
    }
}
