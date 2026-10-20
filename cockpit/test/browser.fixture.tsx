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
import { Configuration } from '../src/configuration';
import { createConfigurationSession } from '../src/lib/configuration-session';
import type { ConfigurationSession } from '../src/lib/configuration-session';
import type { Envelope } from '../src/lib/envelope';
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

const CONFIG_BASE = 'schema_version=1\n[[repositories]]\nid="org/model"\ntype="model"\nrevision="main"\nenabled=false\ndeclared_dependencies=[]\ntags=["base"]\n';
const CONFIG_DRAFT = CONFIG_BASE.replace('tags=["base"]', 'tags=["coding"]');
const FINGERPRINT = 'a'.repeat(64);

function configEnvelope(data: Record<string, unknown>, exit = 0, code = 'HFAPI003'): Envelope {
    return {
        schema_version: 1,
        command: 'config validate',
        run_id: 'c'.repeat(32),
        started_at: '2026-10-19T12:00:00.000000Z',
        completed_at: '2026-10-19T12:00:01.000000Z',
        exit_code: exit,
        outcome: exit === 0 ? 'success' : 'failed',
        data,
        warnings: [],
        errors: exit === 0
            ? []
            : [{
                code,
                message: 'Synthetic classified validation refusal',
                repository: null,
                context: { key: 'storage.archive_id' }
            }],
    };
}

function assessment(changes: Record<string, unknown> = {}, exit = 0): Envelope {
    return configEnvelope({
        valid: true,
        syntax_valid: true,
        installed_policy_valid: true,
        authority_compatible: true,
        authority_mismatches: [],
        config_fingerprint: FINGERPRINT,
        ...changes,
    }, exit, 'HFCFG004');
}

async function guardedProcess(index: number, action: ProcessBoundary['action']): Promise<ProcessBoundary> {
    const process = await nextProcess(index);
    invariant(process.action === action, 'Unexpected fixed configuration stage: expected ' + action);
    return process;
}

async function mountConfiguration(draft = CONFIG_DRAFT): Promise<ConfigurationSession> {
    const session = createConfigurationSession();
    const index = boundary.processes.length;
    mount(<Configuration session={session} />);
    (await guardedProcess(index, 'read')).rawSuccess(CONFIG_BASE);
    const textMode = await until(() => button('Text (verbatim)'), 'actual Configuration initial read');
    textMode.click();
    const textarea = await until(() => document.querySelector<HTMLTextAreaElement>('#config-text'), 'actual text editing mode');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
    invariant(setter, 'Native textarea value setter is missing');
    setter.call(textarea, draft);
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    await until(() => session.snapshot().text === draft, 'actual controlled Configuration draft');
    return session;
}

async function beginValidation(draft = CONFIG_DRAFT): Promise<{
    session: ConfigurationSession; start: number; validation: ProcessBoundary;
}> {
    const session = await mountConfiguration(draft);
    const start = boundary.processes.length;
    const validate = button('Validate candidate');
    invariant(validate && !validate.disabled, 'Actual validation control is unavailable');
    validate.click();
    const write = await guardedProcess(start, 'write');
    invariant(write.input === draft + '\0' + CONFIG_BASE + '\0', 'Actual host write lost exact captured candidate/base bytes');
    write.rawSuccess();
    const validation = await guardedProcess(start + 1, 'guard');
    invariant(validation.clientArgv?.slice(-2).join(' ') === 'config validate', 'Actual candidate validation must use the fixed CLI');
    return { session, start, validation };
}

async function readyConfiguration(): Promise<{ session: ConfigurationSession; start: number }> {
    const { session, start, validation } = await beginValidation();
    validation.succeedEnvelope(assessment());
    await until(() => button('Install validated candidate'), 'strict compatible candidate readiness');
    return { session, start };
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

    await test('V11/V12 Configuration renders a real failed validation Envelope without an assessment', async () => {
        const { session, start, validation } = await beginValidation();
        const refused = configEnvelope({}, 10);
        validation.failEnvelope(refused);
        await until(() => text().includes('HFAPI003'), 'original candidate API refusal');
        invariant(!text().includes('evidence is incompatible'), 'General API refusal became an incompatible assessment');
        invariant(session.snapshot().validation?.errors[0]?.code === 'HFAPI003', 'Original failed Envelope was not retained');
        invariant(!button('Install validated candidate'), 'Failed validation granted installation');
        await delay(75);
        invariant(boundary.processes.length === start + 2, 'Failed validation submitted preview or installation');
    });

    await test('V10 Configuration retains negative candidate assessment and field errors', async () => {
        const { session, start, validation } = await beginValidation();
        validation.failEnvelope(assessment({
            valid: false,
            syntax_valid: false,
            authority_compatible: null,
            authority_mismatches: [],
            config_fingerprint: undefined,
        }, 10));
        await until(() => text().includes('HFCFG004'), 'original negative candidate assessment');
        invariant(session.snapshot().preparation?.blocked === 'invalid', 'Negative candidate assessment was not distinct');
        invariant(session.snapshot().fieldErrors['storage.archive_id'] === 'Synthetic classified validation refusal',
                  'Authentic field location and original negative-assessment message were lost');
        invariant(!button('Install validated candidate'), 'Invalid syntax granted installation');
        invariant(boundary.processes.length === start + 2, 'Invalid candidate invoked a sizing job');
    });

    await test('V13 Configuration distinguishes installed-policy and authority refusal', async () => {
        const { session, start, validation } = await beginValidation();
        validation.succeedEnvelope(assessment({ installed_policy_valid: false, authority_compatible: null }));
        await until(() => text().includes('Candidate cannot be previewed or installed'), 'installed-policy refusal guidance');
        invariant(session.snapshot().preparation?.blocked === 'authority', 'Installed-policy refusal lost its classification');
        invariant(!button('Install validated candidate'), 'Unknown installed policy granted installation');
        invariant(boundary.processes.length === start + 2, 'Unknown installed policy invoked sizing');
    });

    await test('V09/V14 Configuration installs and confirms exact tag-only bytes with no sizing job', async () => {
        const { session, start } = await readyConfiguration();
        button('Install validated candidate')?.click();
        const install = await guardedProcess(start + 2, 'install');
        invariant(install.input === CONFIG_DRAFT + '\0' + CONFIG_BASE + '\0', 'Installation lost exact tag-only bytes');
        install.rawSuccess();
        const confirmation = await guardedProcess(start + 3, 'confirm');
        invariant(confirmation.input === CONFIG_DRAFT + '\0' + CONFIG_DRAFT + '\0', 'Confirmation did not bind exact expected installed bytes');
        confirmation.succeedEnvelope(configEnvelope({ config_fingerprint: FINGERPRINT }));
        await until(() => text().includes('Installed and re-validated'), 'actual confirmed installation result');
        invariant(session.snapshot().installedText === CONFIG_DRAFT, 'Confirmed installed document was not retained exactly');
        invariant(boundary.processes.slice(start).every(process => !process.clientArgv?.includes('plan')),
                  'Tag-only candidate created an unnecessary sizing job');
    });

    await test('V09/V18 Configuration retains validation and original preview notices after bridge loss', async () => {
        const { session, start, validation } = await beginValidation(CONFIG_DRAFT.replace('enabled=false', 'enabled=true'));
        validation.succeedEnvelope(assessment());
        const preview = await guardedProcess(start + 2, 'guard');
        invariant(preview.clientArgv?.includes('plan'), 'Enabled repository did not use the keyed preview route');
        preview.emit('Idempotency key: original-preview-key\nOperation: ' + 'd'.repeat(32) + '\n');
        preview.fail();
        await until(() => text().includes('Sizing observation is uncertain'), 'uncertain preview guidance');
        invariant(session.snapshot().validation?.exit_code === 0, 'Preview failure discarded validation evidence');
        invariant(text().includes('candidate-validate: result') && text().includes('candidate-preview'), 'Stage evidence was lost');
        invariant(session.snapshot().evidence.some(event => event.stage === 'candidate-preview' &&
            event.status === 'notice' && event.notice.kind === 'key' && event.notice.key === 'original-preview-key'),
                  'Original preview key was not retained at the pipeline seam');
        invariant(!button('Install validated candidate'), 'Uncertain preview granted installation');
        invariant(boundary.processes.length === start + 3, 'Uncertain preview was automatically repeated');
    });

    await test('V09/V16 Configuration grants readiness only to the captured successful sizing candidate', async () => {
        const draft = CONFIG_DRAFT.replace('enabled=false', 'enabled=true');
        const { session, start, validation } = await beginValidation(draft);
        validation.succeedEnvelope(assessment());
        const preview = await guardedProcess(start + 2, 'guard');
        preview.succeedEnvelope({
            ...configEnvelope({
                repositories: [{
                    enabled: true,
                    repository_type: 'model',
                    repository_id: 'org/model',
                    requested_revision: 'main',
                    resolved_commit_sha: 'b'.repeat(40),
                    upstream_state: 'available',
                    file_count: 1,
                    logical_bytes: 16,
                    estimated_new_bytes: 16,
                    projected_publication_bytes: 0,
                    publication_mode: 'hardlink',
                }]
            }),
            command: 'plan',
        });
        await until(() => button('Install validated candidate'), 'captured strict required-sizing readiness');
        invariant(session.snapshot().plan?.exit_code === 0 && session.snapshot().diskGuard?.candidateContent === draft,
                  'Strict sizing evidence was not retained with its exact captured document');
        const textarea = document.querySelector<HTMLTextAreaElement>('#config-text');
        const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
        invariant(textarea && setter && !textarea.disabled, 'Prepared candidate editor is unavailable');
        const edited = draft.replace('tags=["coding"]', 'tags=["edited"]');
        setter.call(textarea, edited);
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        await until(() => session.snapshot().text === edited, 'actual edit after successful sizing');
        invariant(!button('Install validated candidate'), 'Old sizing result authorized an edited candidate');
        invariant(session.snapshot().diskGuard?.candidateContent === draft,
                  'Editing silently adopted or overwrote the staged file');
        invariant(boundary.processes.length === start + 3, 'Editing repeated sizing, write or installation');
    });

    await test('V09 Configuration rejects a required sizing success without the strict repository evidence', async () => {
        const { session, start, validation } = await beginValidation(CONFIG_DRAFT.replace('enabled=false', 'enabled=true'));
        validation.succeedEnvelope(assessment());
        const preview = await guardedProcess(start + 2, 'guard');
        preview.succeedEnvelope({ ...configEnvelope({}), command: 'plan' });
        await until(() => text().includes('candidate-preview') && text().includes('Client output could not be validated'),
                    'classified malformed required-sizing evidence');
        invariant(session.snapshot().proposal === null && !button('Install validated candidate'),
                  'Missing repository sizing evidence authorized installation');
        invariant(session.snapshot().validation?.exit_code === 0, 'Malformed sizing discarded authentic validation evidence');
        invariant(boundary.processes.length === start + 3, 'Malformed sizing triggered replay or installation');
    });

    await test('V08 Configuration preserves a late valid assessment without readiness after privilege changes', async () => {
        const { session, start, validation } = await beginValidation();
        boundary.superuser.change(false);
        await until(() => text().includes('Connection changed; installation readiness was invalidated'),
                    'actual in-flight candidate privilege invalidation');
        validation.succeedEnvelope(assessment());
        await until(() => text().includes('Draft or administrative session changed; captured stage evidence was retained'),
                    'superseded candidate assessment warning');
        boundary.superuser.change(true);
        await delay(75);
        invariant(session.snapshot().validation?.exit_code === 0 && !text().includes('reconnected'),
                  'Valid late assessment was replaced with an invented bridge failure');
        invariant(session.snapshot().diskGuard?.candidateContent === CONFIG_DRAFT &&
            session.snapshot().uncertainty === 'candidate', 'Reconnect discarded captured candidate uncertainty');
        invariant(!button('Install validated candidate') && button('Validate candidate')?.disabled,
                  'Late old-session assessment granted readiness or another submission');
        invariant(button('Inspect captured configuration'), 'Reconnect lost the explicit guarded inspection control');
        invariant(boundary.processes.length === start + 2, 'Privilege restoration replayed validation, write or installation');
    });

    await test('V08 Configuration retains an actual validation bridge failure through privilege restoration', async () => {
        const { session, start, validation } = await beginValidation();
        boundary.superuser.change(false);
        await until(() => text().includes('Connection changed; installation readiness was invalidated'),
                    'actual candidate administrative-session invalidation');
        validation.fail(bridgeFailure());
        await until(() => text().includes('candidate-validate') && text().includes('reconnected'),
                    'original validation bridge failure stage');
        boundary.superuser.change(true);
        await delay(75);
        invariant(session.snapshot().diskGuard?.candidateContent === CONFIG_DRAFT &&
            session.snapshot().uncertainty === 'candidate', 'Privilege restoration discarded uncertain candidate ownership');
        invariant(!button('Install validated candidate') && button('Validate candidate')?.disabled,
                  'Actual bridge failure enabled another mutation or installation');
        invariant(text().includes('candidate-validate') && text().includes('reconnected'),
                  'Privilege restoration replaced the original classified error');
        invariant(boundary.processes.length === start + 2, 'Privilege restoration replayed an interrupted pipeline');
    });

    await test('V17 Configuration keeps a lost-write draft across remount and revalidates only after inspection', async () => {
        const session = await mountConfiguration();
        const start = boundary.processes.length;
        button('Validate candidate')?.click();
        (await guardedProcess(start, 'write')).fail();
        await until(() => text().includes('Candidate acknowledgement is uncertain'), 'lost candidate-write acknowledgement');
        invariant(button('Validate candidate')?.disabled, 'Uncertain write enabled a new candidate write');
        invariant(!button('Discard candidate') && !button('Install validated candidate'), 'Uncertain write offered cleanup or installation');
        mounted?.unmount();
        mounted = null;
        mount(<Configuration session={session} />);
        await until(() => document.querySelector<HTMLTextAreaElement>('#config-text')?.value === CONFIG_DRAFT,
                    'captured draft after actual component remount');
        invariant(boundary.processes.length === start + 1, 'Remount replayed candidate write or initial load');
        button('Inspect captured configuration')?.click();
        const inspect = await guardedProcess(start + 1, 'inspect');
        inspect.rawSuccess(JSON.stringify({
            candidate: 'matching',
            installedBase: 'matching',
            installedCandidate: 'changed',
            backupBase: 'absent'
        }));
        const revalidate = await until(() => button('Revalidate captured candidate'), 'explicit inspected-candidate revalidation');
        revalidate.click();
        const validation = await guardedProcess(start + 2, 'guard');
        validation.succeedEnvelope(assessment());
        await until(() => button('Install validated candidate'), 'fresh revalidated captured candidate');
        invariant(boundary.processes.slice(start).filter(process => process.action === 'write').length === 1,
                  'Read-only reconciliation replayed a host write');
    });

    await test('V16/V21 Configuration preserves changed or unknown staged evidence without cleanup authority', async () => {
        const session = await mountConfiguration();
        const start = boundary.processes.length;
        button('Validate candidate')?.click();
        (await guardedProcess(start, 'write')).fail();
        await until(() => button('Inspect captured configuration'), 'uncertain fixed-file inspection control');
        button('Inspect captured configuration')?.click();
        (await guardedProcess(start + 1, 'inspect')).rawSuccess(JSON.stringify({
            candidate: 'unknown', installedBase: 'changed', installedCandidate: 'changed', backupBase: 'unknown',
        }));
        await until(() => text().includes('Captured candidate: unknown'), 'unknown guarded filesystem evidence');
        invariant(session.snapshot().diskGuard?.candidateContent === CONFIG_DRAFT, 'Unknown inspection discarded captured bytes');
        invariant(!button('Revalidate captured candidate') && !button('Discard candidate') && !button('Install validated candidate'),
                  'Unknown ownership offered write, cleanup or installation authority');
        invariant(boundary.processes.length === start + 2, 'Unknown inspection triggered recovery or cleanup');
    });

    await test('V19 Configuration requires inspect, exact confirmation and acknowledgement after an uncertain install', async () => {
        const { session, start } = await readyConfiguration();
        button('Install validated candidate')?.click();
        (await guardedProcess(start + 2, 'install')).fail();
        await until(() => text().includes('Installation may have completed'), 'uncertain installation warning');
        invariant(text().includes('install:') && text().includes('reconnected'), 'Original install cause or stage was lost');
        invariant(button('Validate candidate')?.disabled && !button('Discard candidate'), 'Uncertain install offered replay or cleanup');
        button('Inspect captured configuration')?.click();
        (await guardedProcess(start + 3, 'inspect')).rawSuccess(JSON.stringify({
            candidate: 'absent', installedBase: 'changed', installedCandidate: 'matching', backupBase: 'matching',
        }));
        const confirm = await until(() => button('Confirm captured installation'), 'explicit exact installation confirmation');
        confirm.click();
        (await guardedProcess(start + 4, 'confirm')).succeedEnvelope(configEnvelope({ config_fingerprint: FINGERPRINT }));
        const acknowledge = await until(() => button('Acknowledge confirmed installation'), 'explicit installation acknowledgement');
        invariant(session.snapshot().uncertainty === 'install', 'Confirmation silently cleared operator acknowledgement');
        invariant(text().includes('reconnected'), 'Successful reconciliation hid the original cause');
        acknowledge.click();
        await until(() => text().includes('Installed and re-validated'), 'acknowledged exact installed document');
        invariant(session.snapshot().uncertainty === null && session.snapshot().installedText === CONFIG_DRAFT,
                  'Acknowledgement did not reconcile expected installed bytes');
        invariant(boundary.processes.slice(start).filter(process => process.action === 'install').length === 1,
                  'Uncertain installation was repeated');
        invariant(boundary.processes.slice(start).every(process => process.action !== 'remove'), 'Reconciliation removed unknown evidence');
    });

    await test('V20 Configuration never accepts success stdout after a failed confirmation process', async () => {
        const { session, start } = await readyConfiguration();
        button('Install validated candidate')?.click();
        (await guardedProcess(start + 2, 'install')).rawSuccess();
        const confirmation = await guardedProcess(start + 3, 'confirm');
        confirmation.emit(JSON.stringify(configEnvelope({ config_fingerprint: FINGERPRINT })) + '\n');
        confirmation.fail(bridgeFailure());
        await until(() => text().includes('Installation may have completed'), 'failed confirmation postcheck warning');
        invariant(session.snapshot().uncertainty === 'install' && !text().includes('Installed and re-validated'),
                  'Plausible stdout became confirmed installation');
        invariant(text().includes('installed-confirm') && text().includes('reconnected'), 'Original confirmation stage/cause disappeared');
        invariant(boundary.processes.length === start + 4, 'Failed confirmation retried or reinstalled');
    });

    await test('V11/V20 Configuration preserves a classified failed installed-confirm Envelope', async () => {
        const { session, start } = await readyConfiguration();
        button('Install validated candidate')?.click();
        (await guardedProcess(start + 2, 'install')).rawSuccess();
        (await guardedProcess(start + 3, 'confirm')).failEnvelope(configEnvelope({}, 10, 'HFAPI017'));
        await until(() => text().includes('HFAPI017'), 'original failed installed-validation Envelope');
        invariant(session.snapshot().uncertainty === 'install', 'Failed installed validation cleared installation uncertainty');
        invariant(!text().includes('Installed and re-validated'), 'Failed installed validation announced success');
    });

    await test('V15 Configuration rejects an empty captured draft before any host effect', async () => {
        const session = await mountConfiguration('');
        const calls = boundary.processes.length;
        button('Validate candidate')?.click();
        await until(() => text().includes('at most 1 MiB'), 'local bounded-candidate refusal');
        invariant(session.snapshot().diskGuard === null, 'Empty candidate acquired write ownership evidence');
        invariant(boundary.processes.length === calls, 'Empty candidate reached a host process');
    });

    await test('V15 Configuration renders the CLI server-413 refusal for a bounded escaped candidate without echo or readiness', async () => {
        const draft = CONFIG_DRAFT + '# SYNTHETIC_ESCAPED_CANDIDATE ' + '\\'.repeat(550000) + '\n';
        invariant(new TextEncoder().encode(draft).length < 1024 * 1024 &&
            new TextEncoder().encode(JSON.stringify({ content: draft })).length > 1024 * 1024,
                  'Escaped candidate must fit the file bound and exceed the encoded server request bound');
        const { session, start, validation } = await beginValidation(draft);
        validation.failEnvelope(configEnvelope({}, 10, 'HFAPI006'));
        await until(() => text().includes('HFAPI006'), 'classified server request-size refusal');
        invariant(session.snapshot().text === draft, 'Request-size refusal truncated the captured draft');
        const presentation = container?.cloneNode(true) as HTMLElement | undefined;
        for (const retainedEditor of presentation?.querySelectorAll('textarea') ?? [])
            retainedEditor.remove();
        invariant(!presentation?.textContent?.includes('SYNTHETIC_ESCAPED_CANDIDATE'),
                  'Request-size refusal echoed candidate text outside the retained draft editor');
        invariant(!button('Install validated candidate') && session.snapshot().proposal === null,
                  'Request-size refusal granted installation readiness');
        invariant(boundary.processes.length === start + 2, 'Request-size refusal submitted sizing or retried validation');
    });

    await test('V08 Configuration can read after administrative access was initially unavailable', async () => {
        boundary.superuser.change(false);
        const session = createConfigurationSession();
        const start = boundary.processes.length;
        mount(<Configuration session={session} />);
        await until(() => text().includes('Administrative access'), 'initial configuration access refusal');
        invariant(boundary.processes.length === start, 'Unavailable administrative access invoked a host read');
        boundary.superuser.change(true);
        const retry = await until(() => {
            const read = boundary.processes.slice(start).find(process => process.action === 'read');
            if (read)
                return read;
            button('Reload installed configuration')?.click();
            return null;
        }, 'initial read recovery after administrative access');
        retry.rawSuccess(CONFIG_BASE);
        await until(() => button('Text (verbatim)'), 'recovered initial installed read');
        invariant(boundary.processes.slice(start).every(process => process.action === 'read'),
                  'Read recovery replayed a candidate pipeline');
    });

    await test('V09 Configuration renders backend defaults when installed repository fields are omitted', async () => {
        const session = createConfigurationSession();
        const index = boundary.processes.length;
        mount(<Configuration session={session} />);
        (await guardedProcess(index, 'read')).rawSuccess('schema_version=1\n[[repositories]]\nid="org/model"\ntype="model"\n');
        await until(() => button('Text (verbatim)'), 'form rendering for valid defaulted repository fields');
        invariant(document.querySelector<HTMLInputElement>('[aria-label="Revision"]')?.value === 'main',
                  'Omitted repository revision did not render its backend main default');
        invariant(document.querySelector<HTMLInputElement>('#repo-enabled-0')?.checked === true,
                  'Omitted repository enabled field did not render its backend true default');
        invariant(document.querySelector<HTMLInputElement>('[aria-label="Declared dependencies"]')?.value === '',
                  'Omitted dependencies did not render their backend empty-list default');
        invariant(session.snapshot().installedText === 'schema_version=1\n[[repositories]]\nid="org/model"\ntype="model"\n',
                  'Rendering defaults changed the exact installed-byte evidence');
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
