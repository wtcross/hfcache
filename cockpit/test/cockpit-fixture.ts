/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Controlled Cockpit boundaries used by the real mounted browser tests.
 * These objects never execute a host command or open a D-Bus connection.
 */

import {
    CONFIGURATION_PATHS, MAX_CANDIDATE_BYTES, readInstalledInvocation,
    validateCandidateText
} from '../src/lib/candidate-guard';
import { hfcacheArgv } from '../src/lib/command';
import type { Envelope } from '../src/lib/envelope';

export const DEFAULT_CLIENT_METADATA = Object.freeze({
    metadata_schema_version: 1,
    profile_fingerprint: 'a'.repeat(64),
    authority_fingerprint: 'c'.repeat(64),
    endpoint: 'unix:/run/hfcache/api/api.sock',
    credential_class: 'rest-writer',
    archive_id: '12345678-1234-1234-1234-123456789abc',
    instance_id: 'b'.repeat(32),
});

export function metadataEnvelope(changes: Record<string, unknown> = {}): Envelope {
    const result = JSON.parse(envelope('client describe', 'metadata')) as Envelope;
    result.data = { ...DEFAULT_CLIENT_METADATA, ...changes };
    return result;
}

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
    private static sequence = 0;
    readonly argv: string[];
    readonly action: 'cli' | 'read' | 'inspect' | 'write' | 'install' | 'remove' | 'guard' | 'confirm';
    readonly clientArgv: string[] | null;
    readonly command: readonly string[];
    readonly key: string | null;
    readonly clientScope: string | null;
    readonly operationId: string;
    readonly handle: Promise<string> & {
        stream: (callback: (chunk: string) => void) => unknown;
        input: (value: string) => unknown;
        close: () => never;
    };

    private receive: (chunk: string) => void = () => undefined;
    private resolve!: (value: string) => void;
    private reject!: (error: Error) => void;
    private capturedInput: string | null = null;

    get input(): string | null { return this.capturedInput }

    constructor(argv: string[], options: Record<string, unknown>) {
        this.argv = [...argv];
        if (argv[0] === 'bash') {
            // Compare the actual imported helper, every fixed path and root
            // identity. This boundary records data and never runs that script.
            const expected = readInstalledInvocation().argv;
            const action = argv[4];
            invariant(action === 'read' || action === 'inspect' || action === 'write' ||
                      action === 'install' || action === 'remove' || action === 'guard' || action === 'confirm',
                      'Only fixed configuration guard actions are permitted');
            expected[4] = action;
            invariant(expected.every((argument, index) => argument === argv[index]),
                      'Actual guarded adapter must retain the exact trusted script, paths and identity');
            this.action = action;
            const client = action === 'guard' || action === 'confirm';
            invariant(client || argv.length === expected.length, 'Host-only guard must contain no command tail');
            this.clientArgv = client ? argv.slice(expected.length) : null;
            if (this.clientArgv !== null) {
                const parsed = validateClientArgv(this.clientArgv);
                if (action === 'confirm') {
                    invariant(parsed.command.join(' ') === 'config validate' && parsed.config === null &&
                              parsed.key === null,
                              'Installed confirmation must retain its fixed installed validation command');
                } else {
                    invariant(parsed.config === CONFIGURATION_PATHS.candidate,
                              'Candidate CLI must select only the fixed candidate path');
                    invariant(parsed.command[0] === 'plan' ||
                              (parsed.command.join(' ') === 'config validate' && parsed.key === null),
                              'Only candidate validation and sizing may use the guard');
                }
            }
            invariant(options.superuser === 'require' && options.err === (client ? 'out' : 'message'),
                      'Actual guarded adapter must retain privileged process observation');
        } else {
            this.action = 'cli';
            this.clientArgv = [...argv];
            validateClientArgv(argv);
            invariant(options.superuser === 'require' && options.err === 'out',
                      'Actual adapter must retain privileged merged-stream observation');
        }
        const parsed = this.clientArgv === null ? null : validateClientArgv(this.clientArgv);
        this.command = Object.freeze(parsed?.command ?? []);
        this.key = parsed?.key ?? null;
        this.clientScope = parsed?.clientScope ?? null;
        this.operationId = (++ProcessBoundary.sequence).toString(16).padStart(32, '0');
        const completion = new Promise<string>((resolve, reject) => {
            this.resolve = resolve;
            this.reject = reject;
        });
        this.handle = Object.assign(completion, {
            stream: (callback: (chunk: string) => void) => {
                this.receive = callback;
                return this.handle;
            },
            input: (value: string) => {
                invariant(this.action !== 'cli', 'Direct CLI processes accept no host-write input');
                invariant(this.capturedInput === null && typeof value === 'string',
                          'Guarded stdin must be captured exactly once');
                // Two separately bounded documents plus their NUL framing. No
                // candidate bytes become argv, commands, storage or host I/O.
                invariant(new TextEncoder().encode(value).length <= 2 * MAX_CANDIDATE_BYTES + 2,
                          'Guarded stdin exceeds the two-document bound');
                const documents = value.split('\0');
                invariant(documents.length === 3 && documents[2] === '',
                          'Guarded stdin must contain exactly two NUL-terminated documents');
                validateCandidateText(documents[0]);
                validateCandidateText(documents[1], true);
                this.capturedInput = value;
                return this.handle;
            },
            close: (): never => { throw new Error('Observation must never close an admitted process') },
        });
    }

    succeed(command: string, marker: string): void {
        this.receipts();
        this.emit(envelope(this.resultCommand(command), marker));
        this.resolve('');
    }

    rawSuccess(output = ''): void { this.resolve(output) }

    emit(chunk: string): void { this.receive(chunk) }

    succeedEnvelope(result: Envelope): void {
        invariant(result.exit_code === 0, 'Successful result helper requires a successful Envelope');
        this.receipts();
        this.emit(JSON.stringify(result) + '\n');
        this.resolve('');
    }

    failEnvelope(result: Envelope, error = Object.assign(new Error('Classified CLI result'), {
        exit_status: result.exit_code,
    })): void {
        invariant(result.exit_code !== 0, 'Failed result helper requires an authentic nonzero Envelope');
        this.emit(JSON.stringify(result) + '\n');
        this.reject(error);
    }

    fail(error = bridgeFailure()): void {
        this.reject(error);
    }

    private receipts(): void {
        if (this.key !== null)
            this.emit(`Idempotency key: ${this.key}\nOperation: ${this.operationId}\n`);
    }

    private resultCommand(command: string): string {
        if ((command === 'prune' || command === 'recover') && this.command[0] === command)
            return command + (this.command.includes('--apply') ? ' --apply' : ' --dry-run');
        if (command === 'verify' && this.command[0] === 'verify') {
            const mode = ['--full', '--revision', '--new', '--estimate'].find(option => this.command.includes(option));
            return command + (mode ? ' ' + mode : '');
        }
        return command;
    }
}

function validateClientArgv(argv: string[]): {
    command: string[]; key: string | null; clientScope: string | null; config: string | null;
} {
    const fixed = hfcacheArgv([]);
    invariant(fixed.every((argument, index) => argument === argv[index]),
              'Actual adapter must retain the exact fixed launcher, profile, socket and service identity');
    invariant(argv.length > fixed.length, 'Actual client command must be explicit');
    let index = fixed.length;
    let key: string | null = null;
    let clientScope: string | null = null;
    let config: string | null = null;
    if (argv[index] === '--idempotency-key') {
        key = argv[index + 1];
        invariant(typeof key === 'string' && /^[A-Za-z0-9._~+-]{1,128}$/.test(key),
                  'Original keyed submission must contain only a bounded safe key');
        index += 2;
    }
    if (argv[index] === '--expected-client-scope') {
        clientScope = argv[index + 1];
        invariant(typeof clientScope === 'string' && /^[0-9a-f]{64}$/.test(clientScope),
                  'Original authority comparison must contain only a safe fingerprint');
        index += 2;
    }
    if (argv[index] === '--config') {
        config = argv[index + 1];
        invariant(config === CONFIGURATION_PATHS.candidate, 'Only the fixed guarded candidate path is permitted');
        index += 2;
    }
    const command = argv.slice(index);
    invariant(command.length > 0 && !command.some(argument =>
        ['--idempotency-key', '--expected-client-scope', '--config'].includes(argument)),
              'Client globals must occur exactly once before the explicit command');
    return { command, key, clientScope, config };
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
    readonly transport = { host: 'cpr-initial' };
    // Every actual process remains observable. The legacy nonmetadata index
    // supports existing stage assertions; descriptions have their own index.
    readonly invocations: ProcessBoundary[] = [];
    readonly processes: ProcessBoundary[] = [];
    readonly metadataProcesses: ProcessBoundary[] = [];
    metadataMode: 'automatic' | 'manual' | 'failure' = 'automatic';
    metadata: Record<string, unknown> = { ...DEFAULT_CLIENT_METADATA };
    readonly buses: BusBoundary[] = [];
    readonly files: FileBoundary[] = [];
    readonly superuser = new SuperuserBoundary();

    spawn(argv: string[], options: Record<string, unknown>): ProcessBoundary['handle'] {
        const process = new ProcessBoundary(argv, options);
        this.invocations.push(process);
        const metadata = process.command.join(' ') === 'client describe';
        (metadata ? this.metadataProcesses : this.processes).push(process);
        if (!this.superuser.allowed) {
            queueMicrotask(() => process.fail(bridgeFailure('access-denied')));
        } else if (metadata && this.metadataMode !== 'manual') {
            queueMicrotask(() => {
                if (this.metadataMode === 'failure')
                    process.fail();
                else {
                    const result = metadataEnvelope();
                    result.data = { ...this.metadata };
                    process.succeedEnvelope(result);
                }
            });
        }
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
