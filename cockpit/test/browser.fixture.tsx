/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Real React roots, hooks, adapters and runner; controlled external Cockpit ports.
 */

import React from 'react';
import { createRoot, Root } from 'react-dom/client';

import { runHfcache } from '../src/api/hfcache';
import { startUnit, unitState } from '../src/api/systemd';
import { QueryError } from '../src/components';
import { useHfcache, useUnitPoll } from '../src/hooks';
import { Maintenance } from '../src/maintenance';
import { ScheduleEditor } from '../src/schedule';
import {
    bridgeFailure, BusRequest, controlledCockpit, FileBoundary, invariant, ProcessBoundary,
} from './cockpit-fixture';

window.cprFixture = controlledCockpit;
const boundary = window.cprFixture;
const tests: { name: string; passed: boolean; message?: string }[] = [];
const container = document.getElementById('fixture');
invariant(container, 'Mounted fixture root is missing');
let mounted: Root | null = null;

declare global {
    interface Window {
        cprResultPath: string;
    }
}

const delay = (milliseconds = 25) => new Promise(resolve => setTimeout(resolve, milliseconds));

async function until<T>(read: () => T | null | false, description: string): Promise<T> {
    const deadline = performance.now() + 3000;
    while (performance.now() < deadline) {
        const value = read();
        if (value !== null && value !== false)
            return value;
        await delay();
    }
    throw new Error('Timed out: ' + description);
}

function mount(content: React.ReactNode): void {
    invariant(container, 'Mounted fixture root is missing');
    mounted ??= createRoot(container);
    mounted.render(content);
}

function text(): string {
    return container?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
}

function evidence(): Record<string, unknown> {
    const raw = container?.querySelector('pre')?.textContent;
    return raw ? JSON.parse(raw) as Record<string, unknown> : {};
}

function refresh(): void {
    const button = container?.querySelector('button');
    invariant(button, 'Actual hook refresh control is absent');
    button.click();
}

function button(label: string, within: ParentNode = document): HTMLButtonElement | null {
    return [...within.querySelectorAll('button')]
            .find(node => node.textContent?.replace(/\s+/g, ' ').trim() === label) ?? null;
}

function ReadProbe(): React.ReactElement {
    const query = useHfcache(['version', '--server']);
    const data = query.envelope?.data as Record<string, unknown> | undefined;
    const handleRefresh = query.refresh;
    return (
        <>
            <button onClick={handleRefresh}>Refresh read</button>
            <pre>{JSON.stringify({
                marker: data?.marker ?? null,
                error: query.error !== null,
                loading: query.loading,
            })}
            </pre>
            {query.error && <QueryError error={query.error} />}
        </>
    );
}

function UnitProbe({ name }: { name: string }): React.ReactElement {
    const query = useUnitPoll(name, 60000);
    const current = query as typeof query & { error?: Error | null; loading?: boolean };
    const handleRefresh = query.refresh;
    return (
        <>
            <button onClick={handleRefresh}>Refresh unit</button>
            <pre>{JSON.stringify({
                state: query.state?.activeState ?? null,
                result: query.result?.result ?? null,
                error: current.error !== undefined && current.error !== null,
                loading: current.loading,
            })}
            </pre>
        </>
    );
}

function allRequests(): BusRequest[] {
    return boundary.buses.flatMap(bus => bus.requests);
}

async function nextProcess(index: number): Promise<ProcessBoundary> {
    return until(() => boundary.processes[index] ?? null, 'actual CLI adapter invocation');
}

async function nextFile(index: number): Promise<FileBoundary> {
    return until(() => boundary.files[index] ?? null, 'actual schedule file read');
}

async function propertyRequests(start: number, count = 2): Promise<BusRequest[]> {
    return until(() => {
        const pending = allRequests().slice(start)
                .filter(request => request.method === 'GetAll');
        return pending.length >= count ? pending.slice(0, count) : null;
    }, 'actual D-Bus property requests');
}

function resolveProperties(requests: BusRequest[], marker: string): void {
    for (const request of requests) {
        const iface = request.arguments[0];
        request.succeed(iface === 'org.freedesktop.systemd1.Unit'
            ? { ActiveState: { v: marker }, SubState: { v: 'running' }, UnitFileState: { v: 'enabled' } }
            : { Result: { v: marker }, ExecMainStatus: { v: 0 } });
    }
}

async function resolvePoll(start: number, marker: string): Promise<void> {
    resolveProperties(await propertyRequests(start, 1), marker);
    const complete = await propertyRequests(start, 2);
    resolveProperties(complete.slice(1), marker);
}

async function test(name: string, body: () => Promise<void>): Promise<void> {
    try {
        await body();
        tests.push({ name, passed: true });
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown fixture assertion';
        tests.push({ name, passed: false, message: message.slice(0, 200) });
    } finally {
        mounted?.unmount();
        mounted = null;
        for (const process of boundary.processes)
            process.fail();
        for (const request of allRequests())
            request.fail();
        for (const file of boundary.files)
            file.fail();
        boundary.superuser.change(true);
        await delay();
    }
}

async function run(): Promise<void> {
    await test('V01/V51 QueryError retains candidate bridge stage without raw secret disclosure', async () => {
        const index = boundary.processes.length;
        const observing = runHfcache(['config', 'validate'], { stage: 'candidate-validate' });
        const process = await nextProcess(index);
        process.fail();
        let caught: unknown;
        try {
            await observing;
        } catch (error) {
            caught = error;
        }
        invariant(caught instanceof Error, 'Actual runner must reject interrupted validation');
        const classified = caught as Error & { stage?: unknown; problem?: unknown };
        invariant(classified.problem === 'reconnected', 'Original bridge problem was lost');
        invariant(classified.stage === 'candidate-validate', 'Candidate validation stage was lost');
        mount(<QueryError error={caught} />);
        await until(() => text().length > 0, 'actual QueryError mount');
        invariant(/candidate/i.test(text()) && /validat/i.test(text()), 'Recovery must identify candidate validation');
        invariant(!text().includes('SYNTHETIC_SECRET'), 'Raw rejection content leaked into the DOM');
        invariant(!text().includes('does not cancel accepted server work'),
                  'Synchronous validation must not invent an accepted operation');
    });

    await test('V49 useHfcache clears prior healthy evidence on refresh and failure', async () => {
        const index = boundary.processes.length;
        mount(<ReadProbe />);
        (await nextProcess(index)).succeed('version', 'healthy');
        await until(() => evidence().marker === 'healthy', 'healthy actual hook result');
        refresh();
        const pending = await nextProcess(index + 1);
        invariant(evidence().marker === null, 'Refresh retained healthy evidence that could authorize controls');
        pending.fail();
        await until(() => evidence().loading === false && evidence().error === true, 'actual hook failure');
        invariant(evidence().marker === null, 'Failed read retained healthy result');
        invariant(!text().includes('SYNTHETIC_SECRET'), 'Hook failure disclosed raw bridge text');
    });

    await test('V07 old useHfcache generations cannot overwrite a newer result', async () => {
        const index = boundary.processes.length;
        mount(<ReadProbe />);
        const old = await nextProcess(index);
        refresh();
        const current = await nextProcess(index + 1);
        current.succeed('version', 'current');
        await until(() => evidence().marker === 'current', 'current actual hook generation');
        old.succeed('version', 'obsolete');
        await delay(75);
        invariant(evidence().marker === 'current', 'Obsolete generation overwrote the current read');
    });

    await test('V07/V49 useUnitPoll clears healthy state and reports unavailable property reads', async () => {
        const start = allRequests().length;
        mount(<UnitProbe name="hfcache-sync.service" />);
        await resolvePoll(start, 'healthy-unit');
        await until(() => evidence().state === 'healthy-unit' && evidence().result === 'healthy-unit',
                    'actual healthy unit poll');
        const failedStart = allRequests().length;
        refresh();
        const pending = await propertyRequests(failedStart, 1);
        invariant(evidence().state === null && evidence().result === null, 'Poll refresh retained healthy evidence');
        for (const request of pending)
            request.fail();
        await until(() => evidence().loading === false && evidence().error === true, 'actual unavailable unit poll');
        invariant(evidence().state === null && evidence().result === null, 'Failed unit read retained healthy evidence');
    });

    await test('V07 prior unit generations cannot mix state with a later unit', async () => {
        const start = allRequests().length;
        mount(<UnitProbe name="hfcache-sync.service" />);
        await propertyRequests(start, 1);
        await delay();
        const old = allRequests().slice(start);
        const next = allRequests().length;
        mount(<UnitProbe name="hfcache-verify.service" />);
        await resolvePoll(next, 'current-unit');
        await until(() => evidence().state === 'current-unit' && evidence().result === 'current-unit',
                    'current actual unit generation');
        const lateStart = allRequests().length;
        resolveProperties(old, 'obsolete-unit');
        await delay();
        resolveProperties(allRequests().slice(lateStart), 'obsolete-unit');
        await delay(75);
        invariant(evidence().state === 'current-unit' && evidence().result === 'current-unit',
                  'Obsolete unit results overwrote current evidence');
    });

    await test('V06/V08 a failed unit mutation is observed once and never replayed', async () => {
        const start = allRequests().length;
        const changing = startUnit('hfcache-sync.service');
        const observed = changing.then(() => false, () => true);
        const request = await until(() => allRequests().slice(start)
                .find(item => item.method === 'StartUnit') ?? null,
                                    'actual guarded systemd mutation boundary');
        request.fail(bridgeFailure('disconnected'));
        invariant(await observed, 'Uncertain unit mutation must remain a failure');
        await delay(75);
        invariant(allRequests().slice(start)
                .filter(item => item.method === 'StartUnit').length === 1,
                  'Connection recovery replayed a unit mutation');
    });

    await test('V06 pending D-Bus reads retry through a fresh client with a finite budget', async () => {
        const start = allRequests().length;
        const reading = unitState('hfcache-sync.service');
        const observed = reading.catch(() => null);
        await propertyRequests(start, 1);
        const clients = boundary.buses.length;
        boundary.buses[clients - 1]?.close();
        resolveProperties(await propertyRequests(start + 1, 1), 'after-pending-close');
        invariant((await observed)?.activeState === 'after-pending-close', 'Interrupted read did not use its finite retry');
        invariant(boundary.buses.length === clients + 1, 'Interrupted read did not acquire exactly one fresh client');

        const failingStart = allRequests().length;
        const failing = unitState('hfcache-sync.service').catch(() => null);
        await propertyRequests(failingStart, 1);
        boundary.buses[boundary.buses.length - 1]?.close();
        await propertyRequests(failingStart + 1, 1);
        boundary.buses[boundary.buses.length - 1]?.close();
        invariant(await failing === null, 'Exhausted read retry budget must remain unavailable');
        await delay(175);
        invariant(allRequests().slice(failingStart)
                .filter(item => item.method === 'GetAll').length === 2,
                  'Repeated connection failure caused an unbounded read loop');
    });

    await test('V06 a closed cached D-Bus client is disposed and replaced for reads', async () => {
        const start = allRequests().length;
        const first = unitState('hfcache-sync.service');
        resolveProperties(await propertyRequests(start, 1), 'before-close');
        invariant((await first).activeState === 'before-close', 'Initial actual systemd read failed');
        const previous = boundary.buses[boundary.buses.length - 1];
        invariant(previous, 'Actual systemd adapter created no D-Bus client');
        const clients = boundary.buses.length;
        previous.close();
        const next = allRequests().length;
        const reading = unitState('hfcache-sync.service');
        const observed = reading.catch(() => null);
        resolveProperties(await propertyRequests(next, 1), 'after-close');
        invariant((await observed)?.activeState === 'after-close', 'Read did not recover through a fresh client');
        invariant(boundary.buses.length === clients + 1, 'Closed cached D-Bus client was reused');
        invariant(previous.closeListeners === 0, 'Old D-Bus close listeners were retained');
    });

    await test('V08 privilege/session changes invalidate prior read evidence before reconnect', async () => {
        const index = boundary.processes.length;
        mount(<ReadProbe />);
        await nextProcess(index);
        await delay(75);
        for (const process of boundary.processes.slice(index))
            process.succeed('version', 'prior-session');
        await until(() => evidence().marker === 'prior-session', 'prior administrative session result');
        boundary.superuser.change(false);
        await until(() => evidence().marker === null, 'administrative privilege loss invalidates prior evidence');
        const before = boundary.processes.length;
        boundary.superuser.change(true);
        boundary.superuser.reconnect();
        await nextProcess(before);
        await delay(75);
        for (const process of boundary.processes.slice(before))
            process.succeed('version', 'fresh-session');
        await until(() => evidence().marker === 'fresh-session', 'read after permitted reconnect');
        invariant(!text().includes('SYNTHETIC_SECRET'), 'Session failure disclosed raw content');
    });

    await test('V08/V49 ScheduleEditor requires a fresh read after privilege changes and exposes failed reads', async () => {
        const start = boundary.files.length;
        const processes = boundary.processes.length;
        const requests = allRequests().length;
        mount(<ScheduleEditor onApplied={() => undefined} />);
        (await nextFile(start)).succeed('[Timer]\nOnCalendar=\nOnCalendar=daily\n');
        await until(() => button('Reset to shipped schedule')?.disabled === false, 'fresh managed schedule enables Reset');
        boundary.superuser.change(false);
        await until(() => text().includes('unavailable'), 'privilege loss invalidates schedule evidence');
        invariant(button('Reset to shipped schedule')?.disabled, 'Privilege loss left Reset enabled');
        boundary.superuser.change(true);
        const fresh = await nextFile(start + 1);
        invariant(button('Reset to shipped schedule')?.disabled, 'Old schedule evidence re-enabled Reset before a fresh read');
        invariant(button('Apply override')?.disabled, 'Old validation re-enabled Apply before a fresh read');
        fresh.fail();
        await until(() => text().includes('schedule-read'), 'actual failed schedule read alert');
        invariant(text().includes('unavailable'), 'Failed schedule read looked available');
        invariant(!text().includes('none — the shipped schedule is in effect'), 'Unavailable schedule looked like an absent override');
        invariant(button('Reset to shipped schedule')?.disabled, 'Failed schedule read left Reset enabled');
        invariant(!text().includes('SYNTHETIC_SECRET'), 'Schedule read failure disclosed raw host text');
        boundary.superuser.reconnect();
        const recovered = await nextFile(start + 2);
        invariant(button('Reset to shipped schedule')?.disabled, 'Reconnect reused failed or old schedule evidence');
        recovered.succeed('[Timer]\nOnCalendar=\nOnCalendar=weekly\n');
        await until(() => button('Reset to shipped schedule')?.disabled === false, 'new successful schedule read restores Reset');
        invariant(boundary.processes.length === processes && allRequests().length === requests,
                  'Schedule reconnect replayed a write, reload or unit mutation');
    });

    await test('V07/V49 a late schedule read cannot restore prior-session Reset authority', async () => {
        const start = boundary.files.length;
        mount(<ScheduleEditor onApplied={() => undefined} />);
        const old = await nextFile(start);
        boundary.superuser.reconnect();
        const current = await nextFile(start + 1);
        old.succeed('[Timer]\nOnCalendar=\nOnCalendar=daily\n');
        await delay(75);
        invariant(button('Reset to shipped schedule')?.disabled, 'Late old read restored Reset before current observation');
        invariant(text().includes('unavailable'), 'Late old read restored healthy schedule presentation');
        current.succeed(null);
        await until(() => text().includes('none — the shipped schedule is in effect'), 'fresh absent override result');
        invariant(button('Reset to shipped schedule')?.disabled, 'Absent override enabled Reset');
        invariant(old.closeCalls === 1 && current.closeCalls === 1, 'Schedule file read handles were not closed');
    });

    await test('V08 a maintenance confirmation portal disables its action after privilege loss', async () => {
        const start = boundary.processes.length;
        mount(<Maintenance />);
        const dryRun = await until(() => button('Dry run'), 'actual maintenance mount');
        dryRun.click();
        (await nextProcess(start)).succeed('prune', 'safe dry-run result');
        const apply = await until(() => {
            const found = button('Apply');
            return found && !found.disabled ? found : null;
        }, 'actual dry run enables Apply');
        apply.click();
        await until(() => button('Run prune --apply'), 'actual maintenance confirmation portal');
        boundary.superuser.change(false);
        await until(() => button('Run prune --apply')?.disabled === true, 'privilege loss disables portal action');
        invariant(boundary.processes.length === start + 1, 'Privilege loss submitted Apply or replayed Dry run');
    });
}

async function report(): Promise<void> {
    try {
        await run();
        await fetch(window.cprResultPath, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: tests.every(test => test.passed) ? 'passed' : 'failed', tests }),
        });
    } catch {
        await fetch(window.cprResultPath, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: 'failed', message: 'Mounted fixture failed outside an assertion', tests }),
        });
    }
}

report();
