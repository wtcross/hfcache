/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Controlled Cockpit boundaries used by the real mounted browser tests.
 * These objects never execute a host command or open a D-Bus connection.
 */

export function invariant(condition: unknown, description: string): asserts condition {
    if (!condition)
        throw new Error(description);
}

export function bridgeFailure(problem = 'reconnected'): Error {
    return Object.assign(new Error('SYNTHETIC_SECRET_DO_NOT_RENDER'), {
        problem, exit_status: null, exit_signal: null,
    });
}

export function envelope(command: string, marker: string): string {
    return JSON.stringify({
        schema_version: 1,
        command,
        run_id: 'a'.repeat(32),
        started_at: '2026-10-19T12:00:00.000000Z',
        completed_at: '2026-10-19T12:00:01.000000Z',
        exit_code: 0,
        outcome: 'success',
        data: { marker },
        warnings: [],
        errors: [],
    }) + '\n';
}

export class ProcessBoundary {
    readonly argv: string[];
    readonly handle: Promise<string> & {
        stream: (callback: (chunk: string) => void) => unknown;
        input: (value: string) => unknown;
        close: () => never;
    };

    private receive: (chunk: string) => void = () => undefined;
    private resolve!: (value: string) => void;
    private reject!: (error: Error) => void;

    constructor(argv: string[], options: Record<string, unknown>) {
        this.argv = [...argv];
        invariant(argv[0] === 'systemd-run', 'Actual adapter must retain transient systemd launcher');
        const separator = argv.indexOf('--');
        invariant(separator > 0 && argv[separator + 1] === '/usr/local/libexec/hfcache-client',
                  'Actual adapter must retain the fixed client helper');
        invariant(argv.includes('--property=User=hfcache') && argv.includes('--property=Group=hfcache'),
                  'Actual adapter must retain the service identity');
        invariant(options.superuser === 'require' && options.err === 'out',
                  'Actual adapter must retain privileged merged-stream observation');
        const completion = new Promise<string>((resolve, reject) => {
            this.resolve = resolve;
            this.reject = reject;
        });
        this.handle = Object.assign(completion, {
            stream: (callback: (chunk: string) => void) => {
                this.receive = callback;
                return this.handle;
            },
            input: () => { throw new Error('This fixture accepts no host-write input') },
            close: (): never => { throw new Error('Observation must never close an admitted process') },
        });
    }

    succeed(command: string, marker: string): void {
        this.receive(envelope(command, marker));
        this.resolve('');
    }

    fail(error = bridgeFailure()): void {
        this.reject(error);
    }
}

export class BusRequest {
    readonly method: string;
    readonly arguments: unknown[];
    readonly promise: Promise<unknown[]>;
    private resolve!: (result: unknown[]) => void;
    private reject!: (error: Error) => void;

    constructor(method: string, arguments_: unknown[]) {
        this.method = method;
        this.arguments = arguments_;
        this.promise = new Promise((resolve, reject) => {
            this.resolve = resolve;
            this.reject = reject;
        });
    }

    succeed(properties: Record<string, { v: unknown }> = {}): void {
        this.resolve([properties]);
    }

    fail(error = bridgeFailure('not-authorized')): void {
        this.reject(error);
    }
}

export class BusBoundary extends EventTarget {
    readonly requests: BusRequest[] = [];
    closed = false;
    closeListeners = 0;

    override addEventListener(type: string, callback: EventListenerOrEventListenerObject | null,
        options?: boolean | AddEventListenerOptions): void {
        if (type === 'close')
            this.closeListeners++;
        super.addEventListener(type, callback, options);
    }

    override removeEventListener(type: string, callback: EventListenerOrEventListenerObject | null,
        options?: boolean | EventListenerOptions): void {
        if (type === 'close')
            this.closeListeners--;
        super.removeEventListener(type, callback, options);
    }

    call(_path: string, _iface: string, method: string, arguments_: unknown[]): Promise<unknown[]> {
        if (this.closed)
            return Promise.reject(bridgeFailure('disconnected'));
        if (method === 'LoadUnit')
            return Promise.resolve(['/org/freedesktop/systemd1/unit/owned_2eservice']);
        const request = new BusRequest(method, arguments_);
        this.requests.push(request);
        return request.promise;
    }

    close(): void {
        if (!this.closed) {
            this.closed = true;
            this.dispatchEvent(new Event('close'));
            for (const request of this.requests)
                request.fail(bridgeFailure('disconnected'));
        }
    }
}

export class SuperuserBoundary extends EventTarget {
    allowed = true;

    change(allowed: boolean): void {
        this.allowed = allowed;
        this.dispatchEvent(new Event('changed'));
    }

    reconnect(): void {
        this.dispatchEvent(new Event('reconnect'));
    }
}

export class FileBoundary {
    readonly path: string;
    readonly handle: { read: () => Promise<string | null>; close: () => void };
    closeCalls = 0;
    private resolve!: (value: string | null) => void;
    private reject!: (error: Error) => void;

    constructor(path: string, options: Record<string, unknown>) {
        this.path = path;
        invariant(path === '/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf' &&
                  options.superuser === 'try', 'Only the fixed read-only schedule file is permitted');
        const completion = new Promise<string | null>((resolve, reject) => {
            this.resolve = resolve;
            this.reject = reject;
        });
        this.handle = {
            read: () => completion,
            close: () => { this.closeCalls += 1 },
        };
    }

    succeed(value: string | null): void { this.resolve(value) }
    fail(error = bridgeFailure('access-denied')): void { this.reject(error) }
}

export class CockpitBoundary {
    readonly processes: ProcessBoundary[] = [];
    readonly buses: BusBoundary[] = [];
    readonly files: FileBoundary[] = [];
    readonly superuser = new SuperuserBoundary();

    spawn(argv: string[], options: Record<string, unknown>): ProcessBoundary['handle'] {
        const process = new ProcessBoundary(argv, options);
        this.processes.push(process);
        if (!this.superuser.allowed)
            queueMicrotask(() => process.fail(bridgeFailure('access-denied')));
        return process.handle;
    }

    dbus(name: string, options: Record<string, unknown>): BusBoundary {
        invariant(name === 'org.freedesktop.systemd1' && options.bus === 'system' &&
                  options.superuser === 'try', 'Only the fixed system-manager bus is permitted');
        const bus = new BusBoundary();
        this.buses.push(bus);
        return bus;
    }

    file(path: string, options: Record<string, unknown>): FileBoundary['handle'] {
        const file = new FileBoundary(path, options);
        this.files.push(file);
        return file.handle;
    }
}

export const controlledCockpit = new CockpitBoundary();

declare global {
    interface Window {
        cprFixture: CockpitBoundary;
    }
}
