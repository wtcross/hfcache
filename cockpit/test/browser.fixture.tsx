/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Real React roots, hooks, adapters and runner; controlled external Cockpit ports.
 */

import React from 'react';
import { createRoot, Root } from 'react-dom/client';

import { runHfcache } from '../src/api/hfcache';
import { hostActionAllowed, readHostProfile, requireHostAction } from '../src/api/profile';
import { writeCandidate, installCandidate, removeCandidate } from '../src/api/config';
import { removeDropIn, writeDropIn } from '../src/api/schedule';
import { Application } from '../src/app';
import { ManualFullJob } from '../src/manual-job';
import { SyncOperations } from '../src/sync';
import { Verification } from '../src/verify';
import { RunReports } from '../src/reports';
import { listRunReports as readReportPage, readRunReport as readReportDetail } from '../src/api/reports';
import { READ_METADATA_PREFIX } from '../src/lib/read-metadata';
import type { RunReadMetadata } from '../src/lib/read-metadata';
import { OriginalOperations } from '../src/operations';
import { operationRegistry, operationViews } from '../src/api/operations';
import { enableUnit, startUnit, unitState } from '../src/api/systemd';
import { QueryError } from '../src/components';
import { useHfcache, useHostProfile, useUnitPoll } from '../src/hooks';
import { Maintenance } from '../src/maintenance';
import { Dashboard } from '../src/dashboard';
import { ScheduleEditor } from '../src/schedule';
import { Configuration } from '../src/configuration';
import { createConfigurationSession } from '../src/lib/configuration-session';
import type { ConfigurationSession } from '../src/lib/configuration-session';
import type { Envelope } from '../src/lib/envelope';
import { CONFIGURATION_PATHS } from '../src/lib/candidate-guard';
import { MAX_OPERATION_STORAGE_BYTES, OPERATION_STORAGE_KEY } from '../src/lib/operation-registry';
import type { OperationRecord } from '../src/lib/operation-registry';
import {
    bridgeFailure, BusRequest, controlledCockpit, DEFAULT_CLIENT_METADATA, DEFAULT_HOST_PROFILE, FileBoundary, invariant, ProcessBoundary,
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
        cprProbeReady?: boolean;
        cprTestFilter?: string;
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

function readyButton(label: string, within: ParentNode = document): HTMLButtonElement | null {
    const control = button(label, within);
    return control && !control.disabled ? control : null;
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

function ProfileProbe(): React.ReactElement {
    const profile = useHostProfile();
    return <pre>{JSON.stringify({ archive: profile.permissions.archive, loading: profile.loading, reason: profile.reason })}</pre>;
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

function originalSection(key: string, within: Document = document): HTMLElement | null {
    return [...within.querySelectorAll<HTMLElement>('section[aria-label]')]
            .find(section => section.textContent?.includes(key)) ?? null;
}

function retainedRecord(key: string): Readonly<OperationRecord> {
    const record = operationRegistry.snapshot().records.find(item => item.key === key);
    invariant(record, 'Original operation record is absent');
    return record;
}

async function keyedProcess(start: number, port = boundary): Promise<ProcessBoundary> {
    return until(() => port.processes.slice(start).find(process => process.key !== null) ?? null,
                 'actual pre-keyed client invocation');
}

function lookupEnvelope(record: Readonly<OperationRecord>, operationId: string): Envelope {
    return {
        ...configEnvelope({
            operation: {
                operation_id: operationId,
                route: record.route,
                archive_id: record.scope.archiveId,
                principal: record.scope.credentialClass,
                config_fingerprint: 'a'.repeat(64),
                state: 'running',
                created_at: '2026-10-19T12:00:00.000000Z',
                updated_at: '2026-10-19T12:00:01.000000Z',
                completed_at: null,
                domain_run_id: 'c'.repeat(32),
                transaction_ids: [],
                next_event_sequence: 1,
                result_recorded: false,
            }
        }),
        command: 'operations lookup',
    };
}

async function frameApplication(host: string): Promise<HTMLIFrameElement> {
    const frame = document.createElement('iframe');
    frame.title = 'Owned fresh application module';
    frame.src = '/?cpr-probe=application&host=' + encodeURIComponent(host);
    document.body.appendChild(frame);
    await until(() => frame.contentWindow?.cprProbeReady === true &&
        frame.contentWindow.cprFixture.transport.host === host, 'fresh same-origin application module');
    return frame;
}

async function withFreshStorage(body: () => Promise<void>): Promise<void> {
    const retained = sessionStorage.getItem(OPERATION_STORAGE_KEY);
    sessionStorage.removeItem(OPERATION_STORAGE_KEY);
    try {
        await body();
    } finally {
        for (const frame of document.querySelectorAll('iframe'))
            frame.remove();
        if (retained === null)
            sessionStorage.removeItem(OPERATION_STORAGE_KEY);
        else
            sessionStorage.setItem(OPERATION_STORAGE_KEY, retained);
    }
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

const REPORT_A = 'd'.repeat(32);
const REPORT_B = 'e'.repeat(32);
function historicalReport(runId = REPORT_A): Record<string, unknown> {
    return {
        schema_version: 1,
        application_version: '1.0.0',
        archive_id: DEFAULT_CLIENT_METADATA.archive_id,
        command: 'sync',
        completed_at: '2026-07-24T20:41:46.002000Z',
        config_fingerprint: '9'.repeat(64),
        errors: [],
        exit_code: 0,
        hostname: 'disposable-report-fixture',
        huggingface_hub_version: '1.24.0',
        invocation_mode: 'systemd',
        outcome: 'success',
        python_version: '3.14.6',
        run_id: runId,
        started_at: '2026-07-24T20:38:11.500000Z',
        warnings: [],
        repositories: [],
        totals: { downloaded_bytes: 0, hashed_bytes: 0, published_bytes: 0, pruned_logical_bytes: 0, reused_bytes: 0, xet_cache_peak_bytes: 0 },
    };
}
function reportPageEnvelope(ids: string[]): Envelope { return { ...configEnvelope({ runs: ids }), command: 'runs' } }
function reportDetailEnvelope(runId = REPORT_A, report = historicalReport(runId)): Envelope {
    return { ...configEnvelope({ report }), command: 'runs read', run_id: runId };
}
function succeedRunRead(process: ProcessBoundary, result: Envelope, cursor: string | null = null, changes: Record<string, unknown> = {}): void {
    process.emit(READ_METADATA_PREFIX + JSON.stringify({
        schema_version: 1,
        command: result.command,
        run_id: result.run_id,
        request_id: '7'.repeat(32),
        archive_id: DEFAULT_CLIENT_METADATA.archive_id,
        config_fingerprint: '8'.repeat(64),
        next_cursor: cursor,
        ...changes
    }) + '\n');
    process.succeedEnvelope(result);
}

async function mountReports(ids = [REPORT_A, REPORT_B]): Promise<number> {
    const start = boundary.processes.length;
    mount(<RunReports />);
    const request = await nextProcess(start);
    invariant(request.command.join(' ') === 'runs list --limit 50' && request.key === null, 'Report inventory did not use its fixed keyless REST command');
    succeedRunRead(request, reportPageEnvelope(ids));
    await until(() => readyButton('Open report ' + ids[0]), 'actual authenticated report inventory');
    return start;
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

async function mountConfiguration(draft = CONFIG_DRAFT, withRecovery = false): Promise<ConfigurationSession> {
    const session = createConfigurationSession();
    const index = boundary.processes.length;
    mount(withRecovery
        ? <><OriginalOperations /><Configuration session={session} /></>
        : <Configuration session={session} />);
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

async function beginValidation(draft = CONFIG_DRAFT, withRecovery = false): Promise<{
    session: ConfigurationSession; start: number; validation: ProcessBoundary;
}> {
    const session = await mountConfiguration(draft, withRecovery);
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
    if (window.cprTestFilter && !name.includes(window.cprTestFilter))
        return;
    try {
        boundary.transport.host = 'cpr-test-' + tests.length;
        await body();
        tests.push({ name, passed: true });
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown fixture assertion';
        tests.push({ name, passed: false, message: message.slice(0, 200) });
    } finally {
        mounted?.unmount();
        mounted = null;
        for (const process of boundary.invocations)
            process.fail();
        for (const request of allRequests())
            request.fail();
        for (const file of boundary.files)
            file.fail();
        boundary.superuser.change(true);
        boundary.metadataMode = 'automatic';
        boundary.metadata = { ...DEFAULT_CLIENT_METADATA };
        boundary.profileMode = 'automatic';
        boundary.profile = structuredClone(DEFAULT_HOST_PROFILE);
        await delay(75);
    }
}

async function run(): Promise<void> {
    await test('V41 report detail loading serializes repeated and alternate row clicks', async () => {
        const start = await mountReports();
        const first = await until(() => readyButton('Open report ' + REPORT_A), 'first selectable report row');
        const second = await until(() => readyButton('Open report ' + REPORT_B), 'second selectable report row');
        first.click(); first.click(); second.click();
        const pending = await nextProcess(start + 1);
        await delay(75);
        invariant(boundary.processes.slice(start + 1).filter(item => item.command[0] === 'runs' && item.command[1] === 'show').length === 1,
                  'Repeated or alternate row clicks started concurrent detail client processes');
        invariant(button('Open report ' + REPORT_A)?.disabled === true && button('Open report ' + REPORT_B)?.disabled === true,
                  'Pending detail read left report row controls enabled');
        succeedRunRead(pending, reportDetailEnvelope());
        await until(() => text().includes('Recorded run ' + REPORT_A), 'first serialized report detail');
        (await until(() => readyButton('Open report ' + REPORT_B), 'report row after original detail completion')).click();
        const next = await nextProcess(start + 2);
        succeedRunRead(next, reportDetailEnvelope(REPORT_B));
        await until(() => text().includes('Recorded run ' + REPORT_B), 'deliberate subsequent report selection');
    });

    await test('V41/V43 reports use one authenticated page and exact run detail without client archive access', async () => {
        boundary.profile = { schema_version: 1, state: 'unknown', reason: 'policy-missing' };
        const records = operationRegistry.snapshot().records.length;
        const start = boundary.processes.length;
        mount(<RunReports />);
        const request = await nextProcess(start);
        invariant(request.command.join(' ') === 'runs list --limit 50', 'Report list did not use the fixed REST CLI adapter');
        const ids = Array.from({ length: 50 }, (_, index) => (index + 1).toString(16).padStart(32, '0'));
        succeedRunRead(request, reportPageEnvelope(ids), '-opaque-next-page');
        await until(() => document.querySelectorAll('button').length > 50, 'bounded actual report page');
        invariant([...document.querySelectorAll('button')].filter(node => node.textContent?.startsWith('Open report ')).length === 50, 'Report page was truncated or accumulated');
        (await until(() => readyButton('Next report page'), 'explicit next report page')).click();
        const next = await nextProcess(start + 1);
        invariant(next.command.join(' ') === 'runs list --limit 50 --cursor=-opaque-next-page', 'Cursor was changed, replayed or interpreted as an option');
        invariant(button('Open report ' + ids[0]) === null, 'Previous page remained healthy during next-page loading');
        succeedRunRead(next, reportPageEnvelope([REPORT_A]));
        (await until(() => readyButton('Open report ' + REPORT_A), 'replacement report page')).click();
        const detail = await nextProcess(start + 2);
        invariant(detail.command.join(' ') === 'runs show -- ' + REPORT_A, 'Detail used a filename, URL or changed run identity');
        succeedRunRead(detail, reportDetailEnvelope());
        await until(() => text().includes('Recorded run ' + REPORT_A) && text().includes('9'.repeat(64)), 'historical report identity and policy');
        invariant([...document.querySelectorAll('button')].filter(node => node.textContent?.startsWith('Open report ')).length === 1, 'Explicit pages accumulated an inventory');
        invariant(operationRegistry.snapshot().records.length === records && boundary.processes.slice(start).every(item => item.key === null), 'Report reads created a domain operation');
        (await until(() => readyButton('Return to first report page'), 'explicit first-page navigation')).click();
        const first = await nextProcess(start + 3);
        invariant(first.command.join(' ') === 'runs list --limit 50' && !text().includes('Recorded run ' + REPORT_A), 'First-page navigation retained selected detail or reused a cursor');
        succeedRunRead(first, reportPageEnvelope([]));
        await until(() => text().includes('No run reports on this page'), 'authentic observed empty inventory');
    });

    await test('V41/V42 report refresh clears healthy data and preserves exact failed read Envelopes', async () => {
        const start = await mountReports();
        (await until(() => readyButton('Refresh run reports'), 'explicit report refresh')).click();
        const refresh = await nextProcess(start + 1);
        invariant(button('Open report ' + REPORT_A) === null, 'Refresh left prior report inventory looking current');
        refresh.failEnvelope({ ...configEnvelope({}, 40, 'HFVER007'), command: 'runs' });
        await until(() => text().includes('HFVER007'), 'original classified corrupt report inventory refusal');
        invariant(!text().includes('No run reports on this page'), 'Failed read became empty inventory success');
        (await until(() => readyButton('Refresh run reports'), 'explicit retry after failed report read')).click();
        const retry = await nextProcess(start + 2);
        succeedRunRead(retry, reportPageEnvelope([REPORT_A]), 'stale-cursor');
        (await until(() => readyButton('Next report page'), 'explicit stale-cursor request')).click();
        const stale = await nextProcess(start + 3);
        stale.failEnvelope({ ...configEnvelope({}, 10, 'HFAPI003'), command: 'runs' });
        await until(() => text().includes('HFAPI003'), 'original stale-cursor refusal');
        await delay(75);
        invariant(boundary.processes.length === start + 4 && button('Open report ' + REPORT_A) === null, 'Stale cursor silently restarted or mixed pages');
    });

    await test('V42 report selection discards late detail responses and session-stale report pages', async () => {
        const start = await mountReports();
        button('Open report ' + REPORT_A)?.click();
        const old = await nextProcess(start + 1);
        button('Refresh run reports')?.click();
        const replacement = await nextProcess(start + 2);
        succeedRunRead(replacement, reportPageEnvelope([REPORT_B]));
        await until(() => button('Open report ' + REPORT_B), 'replacement page during pending original detail');
        invariant(button('Open report ' + REPORT_B)?.disabled === true, 'Page navigation bypassed the pending detail-read latch');
        invariant(text().includes('A report read is finishing'), 'Navigation hid the explanation for a pending detail read');
        succeedRunRead(old, reportDetailEnvelope());
        const second = await until(() => readyButton('Open report ' + REPORT_B), 'new selection after stale original detail completes');
        invariant(!text().includes('Recorded run ' + REPORT_A), 'Late detail repopulated a selection cleared by navigation');
        second.click();
        const current = await nextProcess(start + 3);
        succeedRunRead(current, reportDetailEnvelope(REPORT_B));
        await until(() => text().includes('Recorded run ' + REPORT_B), 'newer selected run detail');
        button('Refresh run reports')?.click();
        const stale = await nextProcess(start + 4);
        const reconnect = boundary.processes.length;
        boundary.superuser.change(false);
        await until(() => !text().includes('Recorded run ' + REPORT_B), 'stale report removed on privilege loss');
        boundary.superuser.change(true);
        const fresh = await until(() => boundary.processes.slice(reconnect).find(item => item.command[0] === 'runs') ?? null, 'fresh report list after privilege restoration');
        succeedRunRead(fresh, reportPageEnvelope([REPORT_B]));
        await until(() => readyButton('Open report ' + REPORT_B), 'fresh report inventory');
        succeedRunRead(stale, reportPageEnvelope([REPORT_A]));
        await delay(75);
        invariant(button('Open report ' + REPORT_A) === null && button('Open report ' + REPORT_B) !== null, 'Old-session report inventory replaced current evidence');
    });

    await test('V42 report detail failures and hostile success fields never become healthy report data', async () => {
        const start = await mountReports();
        button('Open report ' + REPORT_A)?.click();
        (await nextProcess(start + 1)).failEnvelope({ ...configEnvelope({}, 10, 'HFARG004'), command: 'runs read' });
        await until(() => text().includes('HFARG004'), 'exact missing historical report refusal');
        invariant(!text().includes('Recorded run '), 'Missing report was substituted or accessed as success data');
        button('Open report ' + REPORT_B)?.click();
        const hostile = await nextProcess(start + 2);
        succeedRunRead(hostile, reportDetailEnvelope(REPORT_B, { ...historicalReport(REPORT_B), extra_secret: 'SYNTHETIC_SECRET' }));
        await until(() => text().includes('Client output could not be validated'), 'classified incompatible report schema');
        invariant(!text().includes('SYNTHETIC_SECRET') && !text().includes('Recorded run '), 'Unknown report fields reached browser display');
        button('Open report ' + REPORT_A)?.click();
        const changed = await nextProcess(start + 3);
        succeedRunRead(changed, reportDetailEnvelope(), null, { archive_id: '11111111-1111-1111-1111-111111111111' });
        await until(() => text().includes('Client output could not be validated'), 'wrong archive report refusal');
        invariant(!text().includes('Recorded run '), 'Changed archive was accepted for a selected historical report');
    });

    await test('V41/V45 optional bounded host journal never decides or blocks an authenticated report result', async () => {
        const start = await mountReports([REPORT_A]);
        button('Open report ' + REPORT_A)?.click();
        succeedRunRead(await nextProcess(start + 1), reportDetailEnvelope());
        const journalStart = boundary.runJournals.length;
        (await until(() => readyButton('Show host journal trail for this run'), 'optional host-local report diagnostic')).click();
        const journal = await until(() => boundary.runJournals[journalStart] ?? null, 'fixed bounded host journal invocation');
        invariant(journal.runId === REPORT_A, 'Host journal correlated another run');
        journal.emit('event=run.completed level=info run_id=' + REPORT_A + ' token=SYNTHETIC_SECRET\n');
        journal.fail();
        await until(() => text().includes('reconnected') && text().includes('event=run.completed'), 'safe partial journal and original bridge failure')
                .catch(() => { throw new Error('Journal render flags ' + JSON.stringify({ bridge: text().includes('reconnected'), event: text().includes('event=run.completed'), stage: text().includes('journal-read'), record: text().includes('Recorded run ' + REPORT_A) })) });
        invariant(text().includes('Recorded run ' + REPORT_A) && !text().includes('SYNTHETIC_SECRET'), 'Optional journal replaced the report or exposed arbitrary prose');
        (await until(() => readyButton('Show host journal trail for this run'), 'explicit bounded journal retry')).click();
        const capped = await until(() => boundary.runJournals[journalStart + 1] ?? null, 'explicit second diagnostic');
        capped.emit(('event=run.completed level=info run_id=' + REPORT_A + '\n').repeat(201));
        await until(() => text().includes('Host journal diagnostic is incomplete'), 'explicit journal truncation');
        invariant(capped.closeCalls === 1 && text().includes('Recorded run ' + REPORT_A) && text().includes('latest seven days, newest first'), 'Journal cap changed domain evidence or lacked diagnostic bounds');
    });

    await test('V42/V44 report adapters reject unsafe IDs and cursors before any target invocation', async () => {
        const start = boundary.processes.length;
        for (const value of ['../runs/report', '--dangerous', 'https://host/report', 'A'.repeat(32), 'SYNTHETIC_SECRET\n']) {
            let failed = false;
            try { await readReportDetail(value) } catch { failed = true }
            invariant(failed, 'Unsafe report identity was accepted');
        }
        for (const cursor of ['', 'SYNTHETIC_SECRET\n', 'x'.repeat(257)]) {
            let failed = false;
            try { await readReportPage(cursor) } catch { failed = true }
            invariant(failed, 'Unsafe report cursor was accepted');
        }
        invariant(boundary.processes.length === start, 'Invalid report selector reached a process, local path or proxy');
    });

    await test('V41 a successful report read preserves the historical failed verification result independently', async () => {
        const start = await mountReports([REPORT_A]);
        button('Open report ' + REPORT_A)?.click();
        const report = historicalReport();
        delete report.repositories; delete report.totals;
        Object.assign(report, {
            command: 'verify --full',
            exit_code: 40,
            outcome: 'failed',
            errors: ['HFVER001'],
            mode: 'full',
            scope: { repositories: 1, revisions: 1, unique_bytes_read: 1, unique_objects_read: 1 },
            throughput_bytes_per_second: 1,
            verification_outcome: 'failed',
            findings: [{
                commit_sha: 'a'.repeat(40),
                expected: 'a'.repeat(64),
                observed: 'b'.repeat(64),
                kind: 'digest_mismatch',
                path: 'weights.bin',
                publication_id: 'f'.repeat(32),
                repository_id: 'org/model',
                repository_type: 'model'
            }]
        });
        succeedRunRead(await nextProcess(start + 1), reportDetailEnvelope(REPORT_A, report));
        await until(() => text().includes('Recorded run failed (exit 40)') && text().includes('HFVER001'), 'recorded failed historical domain result');
        invariant(text().includes('verify --full') && text().includes('Historical policy fingerprint'), 'Report read success erased domain result or historical identity');
    });

    await test('V41 caller-owned expected report identity is captured before asynchronous reads', async () => {
        const expected: RunReadMetadata = {
            schema_version: 1,
            command: 'runs',
            run_id: 'c'.repeat(32),
            request_id: '7'.repeat(32),
            archive_id: DEFAULT_CLIENT_METADATA.archive_id,
            config_fingerprint: '8'.repeat(64),
            next_cursor: '-next'
        };
        const start = boundary.processes.length;
        const reading = readReportPage('-next', expected);
        expected.archive_id = '11111111-1111-1111-1111-111111111111';
        expected.config_fingerprint = '0'.repeat(64);
        const request = await nextProcess(start);
        succeedRunRead(request, reportPageEnvelope([REPORT_A]));
        const result = await reading;
        invariant(result.page?.runs[0] === REPORT_A, 'Caller mutation changed the captured report page identity comparison');
    });

    await test('V39 masked schedule facts refuse actual file and fixed system manager mutations', async () => {
        const profile = structuredClone(DEFAULT_HOST_PROFILE);
        profile.facts.units['hfcache-sync.timer'] = { load: 'masked', active: 'inactive', unit_file: 'masked' };
        boundary.profile = { ...profile, permissions: { ...profile.permissions, schedule: false } };
        const commands = [() => writeDropIn('*-*-* 03:00:00', null), () => removeDropIn(), () => startUnit('hfcache-sync.timer')];
        for (const command of commands) {
            const start = boundary.processes.length;
            const requests = allRequests().length;
            let failure: unknown;
            await command().catch(error => { failure = error });
            invariant(failure instanceof Error && boundary.processes.length === start && allRequests().length === requests,
                      'Masked schedule profile reached a file mutation or system manager effect');
        }
    });

    await test('V37 direct plugin commands reject global option prefixes unsupported local effects and mixed modes', async () => {
        const commands = [['--quiet', 'sync'], ['archive', 'init'], ['config', 'validate', '--local'],
            ['verify', '--estimate', '--full'], ['unsupported-command']];
        for (const command of commands) {
            const start = boundary.processes.length;
            let failure: unknown;
            const observing = Promise.resolve().then(() => runHfcache(command))
                    .catch(error => { failure = error });
            await delay(75);
            for (const process of boundary.processes.slice(start))
                process.fail();
            await observing;
            invariant(boundary.processes.length === start && failure instanceof Error,
                      'Unsupported plugin command reached the fixed client: ' + command.join(' '));
        }
    });

    await test('V37 caller command mutation cannot turn a Hub sizing permission into an archive job', async () => {
        boundary.profile = { ...structuredClone(DEFAULT_HOST_PROFILE), permissions: { ...DEFAULT_HOST_PROFILE.permissions, archive: false } };
        await readHostProfile();
        const start = boundary.processes.length;
        const command = ['plan'];
        let failure: unknown;
        const observing = runHfcache(command, { onNotice: notice => { if (notice.kind === 'key') command[0] = 'sync'; } })
                .catch(error => { failure = error });
        const process = await until(() => boundary.processes[start] ?? (failure instanceof Error ? false : null), 'captured original sizing invocation');
        process.succeed(process.command[0], 'captured-original-command');
        await observing;
        invariant(process.command.join(' ') === 'plan', 'Caller mutation submitted an archive job through Hub-only permission');
        invariant(process.key !== null && retainedRecord(process.key).route === '/api/v1/plans', 'Caller mutation changed the original route identity');
    });

    await test('V39 a completed schedule file mutation remains uncertain after Reload permission refusal until explicit reconciliation', async () => {
        await readHostProfile();
        const files = boundary.files.length;
        const start = boundary.processes.length;
        const schedule = (key: string) => mount(<div><ProfileProbe /><ScheduleEditor key={key} onApplied={() => undefined} /></div>);
        schedule('initial');
        (await nextFile(files)).succeed('[Timer]\nOnCalendar=*-*-* 03:00:00\nRandomizedDelaySec=15m\n');
        (await until(() => readyButton('Reset to shipped schedule'), 'permitted managed schedule reset')).click();
        (await until(() => readyButton('Remove drop-in and apply'), 'managed schedule reset confirmation')).click();
        const removal = await until(() => boundary.processes.slice(start).find(item => item.action === 'schedule-remove') ?? null, 'fixed schedule file removal');
        const pendingReads = boundary.files.length;
        schedule('pending-remount');
        (await nextFile(pendingReads)).succeed('[Timer]\nOnCalendar=*-*-* 03:00:00\nRandomizedDelaySec=15m\n');
        await delay(50);
        invariant(button('Reset to shipped schedule')?.disabled === true && button('Apply override')?.disabled === true,
                  'Remount permitted another schedule change before the original file mutation acknowledged');
        invariant(boundary.processes.slice(start).filter(item => item.action === 'schedule-remove').length === 1,
                  'Pending schedule remount repeated the original file mutation');
        boundary.profileMode = 'manual';
        const profiles = boundary.profileProcesses.length;
        removal.rawSuccess();
        const reloadProof = await until(() => boundary.profileProcesses[profiles] ?? null, 'fresh Reload permission inspection after removal');
        reloadProof.emit(JSON.stringify({ schema_version: 1, state: 'unknown', reason: 'policy-missing' }));
        reloadProof.rawSuccess();
        await until(() => text().includes('not provisioned'), 'classified post-removal permission refusal');
        boundary.profileMode = 'automatic';
        await readHostProfile();
        await delay(75);
        invariant(button('Reset to shipped schedule')?.disabled === true && button('Apply override')?.disabled === true,
                  'Post-removal Reload refusal enabled another file mutation without reconciliation');
        invariant(boundary.processes.slice(start).filter(item => item.action === 'schedule-remove').length === 1, 'Uncertain schedule mutation repeated automatically');
        const remountReads = boundary.files.length;
        schedule('uncertain-remount');
        (await nextFile(remountReads)).succeed(null);
        await until(() => text().includes('not provisioned') && button('Inspect changed schedule'), 'original schedule uncertainty retained through actual component remount');
        const input = await until(() => document.querySelector<HTMLInputElement>('#schedule-oncalendar'), 'remounted schedule calendar input');
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, '*-*-* 03:00:00');
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const checks = boundary.processes.length;
        (await until(() => readyButton('Check calendar'), 'fresh calendar validation after remount')).click();
        const check = await until(() => boundary.processes.slice(checks).find(item => item.action === 'schedule-validate') ?? null, 'fixed read-only calendar validation');
        check.rawSuccess('Normalized form: *-*-* 03:00:00\nNext elapse: Wed 2026-10-21 03:00:00 EDT\n');
        await until(() => text().includes('Normalized:'), 'fresh calendar evidence while schedule remains uncertain');
        invariant(button('Apply override')?.disabled === true && button('Reset to shipped schedule')?.disabled === true,
                  'Remount and fresh calendar validation bypassed retained schedule uncertainty');
        const reads = boundary.files.length;
        const requests = allRequests().length;
        (await until(() => readyButton('Inspect changed schedule'), 'explicit read-only changed schedule inspection')).click();
        (await nextFile(reads)).succeed(null);
        const [properties] = await propertyRequests(requests, 1);
        properties.succeed({ ActiveState: { v: 'inactive' }, SubState: { v: 'dead' }, UnitFileState: { v: 'enabled' } });
        (await until(() => readyButton('Acknowledge inspected schedule'), 'explicit exact schedule inspection acknowledgement')).click();
        await until(() => readyButton('Check calendar'), 'deliberate fresh schedule validation after acknowledgement');
        invariant(text().includes('not provisioned') && text().includes('does not establish the loaded calendar'),
                  'Acknowledgement erased the original refusal or claimed manager application');
        invariant(button('Apply override')?.disabled === true, 'Schedule acknowledgement reused the old calendar validation');
        invariant(boundary.processes.slice(start).filter(item => item.action === 'schedule-remove').length === 1 &&
                  allRequests().slice(requests)
                          .every(item => item.method === 'GetAll'), 'Schedule inspection or acknowledgement replayed a host mutation');
    });

    await test('V38 delayed permitted profile proof cannot supersede a newer denied profile', async () => {
        boundary.profileMode = 'manual';
        const start = boundary.profileProcesses.length;
        let authorized = false;
        let failure: unknown;
        const old = requireHostAction('archive').then(() => { authorized = true }, error => { failure = error });
        const first = await until(() => boundary.profileProcesses[start] ?? null, 'old pending host permission inspection');
        mount(<ProfileProbe />);
        const newest = readHostProfile();
        const second = await until(() => boundary.profileProcesses[start + 1] ?? null, 'newer host restriction inspection');
        second.emit(JSON.stringify({ schema_version: 1, state: 'unknown', reason: 'policy-missing' }));
        second.rawSuccess();
        await newest;
        first.emit(JSON.stringify(DEFAULT_HOST_PROFILE));
        first.rawSuccess();
        await old;
        await until(() => evidence().archive === false && evidence().loading === false, 'latest denied host permission rendered');
        invariant(!authorized && failure instanceof Error && !hostActionAllowed('archive'), 'Older permitted host proof authorized an effect after newer denial');
        invariant(boundary.profileProcesses.length === start + 2, 'Superseded host proof created an unbounded retry');
    });

    await test('V08/V38 profile permission remains unavailable through a session change until one fresh inspection completes', async () => {
        boundary.profileMode = 'manual';
        const start = boundary.profileProcesses.length;
        mount(<ProfileProbe />);
        const old = await until(() => boundary.profileProcesses[start] ?? null, 'pending old-session host inspection');
        boundary.superuser.change(false);
        await until(() => evidence().archive === false, 'permission cleared on privilege loss');
        boundary.superuser.change(true);
        await delay(50);
        invariant(boundary.profileProcesses.length === start + 1, 'Session change created overlapping host probe storm');
        old.emit(JSON.stringify(DEFAULT_HOST_PROFILE));
        old.rawSuccess();
        const fresh = await until(() => boundary.profileProcesses[start + 1] ?? null, 'fresh host inspection after stale completion');
        invariant(evidence().archive === false && !hostActionAllowed('archive'), 'Old-session host permission restored effect authority');
        fresh.emit(JSON.stringify(DEFAULT_HOST_PROFILE));
        fresh.rawSuccess();
        await until(() => evidence().archive === true && evidence().loading === false, 'fresh current-session host permission');
        await delay(75);
        invariant(boundary.profileProcesses.length === start + 2, 'Current host proof did not end the bounded inspection retry');
    });

    await test('V39 permitted sync timer enabling uses the fixed system manager without force or unmask', async () => {
        await readHostProfile();
        const start = allRequests().length;
        const enabling = enableUnit('hfcache-sync.timer');
        const enable = await until(() => allRequests().slice(start)
                .find(item => item.method === 'EnableUnitFiles') ?? null,
                                   'explicitly permitted fixed sync timer enable');
        invariant(JSON.stringify(enable.arguments) === JSON.stringify([['hfcache-sync.timer'], false, false]),
                  'Timer enable used force, runtime manager selection or another unit');
        enable.succeed();
        const reload = await until(() => allRequests().slice(start)
                .find(item => item.method === 'Reload') ?? null, 'fixed system manager reload after timer enable');
        reload.succeed();
        await enabling;
        invariant(allRequests().slice(start)
                .every(item => ['EnableUnitFiles', 'Reload'].includes(item.method)),
                  'Timer enable introduced an unmask or unrelated manager operation');
    });

    await test('V35 manual full sync uses one original keyed REST client and exact result without a service start', async () => {
        await readHostProfile();
        const start = boundary.processes.length;
        const requests = allRequests().length;
        mount(<SyncOperations />);
        const run = await until(() => { const control = button('Run full sync'); return control && !control.disabled ? control : null }, 'permitted manual full sync');
        run.click();
        const confirm = await until(() => button('Start full sync'), 'manual sync confirmation');
        confirm.click();
        confirm.click();
        const process = await keyedProcess(start);
        invariant(process.command.join(' ') === 'sync' && process.clientScope !== null, 'Full sync changed its fixed keyed REST command');
        process.succeed('sync', 'manual-sync-result');
        await until(() => text().includes('manual-sync-result'), 'exact manual sync terminal result');
        invariant(process.key !== null && retainedRecord(process.key).state === 'terminal', 'Manual sync lost its terminal original record');
        invariant(boundary.processes.slice(start).filter(item => item.key !== null).length === 1, 'Manual sync confirmation submitted twice');
        invariant(allRequests().slice(requests)
                .every(item => item.method !== 'StartUnit'), 'Manual sync started a systemd service');
        invariant(button('Start / resume full sync') === null, 'Legacy full service-start control remains');
    });

    await test('V36 manual full verification preserves the exact failed domain result through the REST operation flow', async () => {
        await readHostProfile();
        const start = boundary.processes.length;
        const requests = allRequests().length;
        mount(<Verification />);
        const run = await until(() => { const control = button('Run full verification'); return control && !control.disabled ? control : null }, 'permitted manual full verification');
        run.click();
        (await until(() => button('Start full verification'), 'manual verification confirmation')).click();
        const process = await keyedProcess(start);
        invariant(process.command.join(' ') === 'verify --full', 'Full verification changed its original command');
        process.emit('Idempotency key: ' + process.key + '\nOperation: ' + process.operationId + '\n');
        const failure = { ...configEnvelope({ marker: 'manual-corruption-result' }, 40, 'HFVER001'), command: 'verify --full' };
        process.failEnvelope(failure);
        await until(() => text().includes('manual-corruption-result') && text().includes('HFVER001'), 'classified full verification failure');
        invariant(process.key !== null && retainedRecord(process.key).terminal?.exitCode === 40, 'Domain verification exit was replaced with observer success');
        invariant(allRequests().slice(requests)
                .every(item => item.method !== 'StartUnit'), 'Manual full verification started a service');
        invariant(button('Start hfcache-verify.service') === null, 'Legacy full verification service start remains');
    });

    await test('V35/V36 detaching a manual display retains the original operation without closing or replaying execution', async () => {
        await readHostProfile();
        const start = boundary.processes.length;
        mount(<ManualFullJob mode="sync" />);
        (await until(() => { const control = button('Run full sync'); return control && !control.disabled ? control : null }, 'permitted detachable full sync')).click();
        (await until(() => button('Start full sync'), 'detachable full sync confirmation')).click();
        const process = await keyedProcess(start);
        invariant(process.key !== null, 'Detachable operation key is absent');
        process.emit('Idempotency key: ' + process.key + '\nOperation: ' + process.operationId + '\n');
        await until(() => text().includes(process.operationId), 'original handles before detach');
        (await until(() => button('Detach manual display'), 'manual detach control')).click();
        process.succeed('sync', 'late-detached-result');
        await until(() => retainedRecord(process.key!).state === 'terminal', 'original result after display detach');
        invariant(text().includes('Manual display detached') && text().includes(process.operationId), 'Detaching lost the original local evidence');
        invariant(!text().includes('late-detached-result'), 'Detached display accepted late callbacks');
        invariant(button('Run full sync')?.disabled === true, 'Detached display allowed a replacement job');
        invariant(boundary.processes.slice(start).filter(item => item.key !== null).length === 1, 'Detach replayed the original job');
    });

    await test('V40 scheduled observer journals and stopping remain separate from an active manual REST operation', async () => {
        await readHostProfile();
        const start = boundary.processes.length;
        const requests = allRequests().length;
        const journals = boundary.journals.length;
        mount(<SyncOperations />);
        for (let wave = 0; wave < 5; wave++) {
            resolveProperties(allRequests().slice(requests), 'active');
            await delay();
        }
        const journal = await until(() => boundary.journals[journals] ?? null, 'fixed scheduled observer journal');
        invariant(journal.unit === 'hfcache-sync.service', 'Scheduled journal changed its fixed unit');
        (await until(() => { const control = button('Run full sync'); return control && !control.disabled ? control : null }, 'manual sync beside scheduled observer')).click();
        (await until(() => button('Start full sync'), 'coexisting manual sync confirmation')).click();
        const process = await keyedProcess(start);
        invariant(process.key !== null, 'Coexisting manual operation key is absent');
        process.emit('Idempotency key: ' + process.key + '\nOperation: ' + process.operationId + '\n');
        journal.emit(JSON.stringify({ ...configEnvelope({ marker: 'scheduled-journal-only' }), command: 'sync' }) + '\n');
        await until(() => text().includes('scheduled-journal-only'), 'separate host journal display');
        invariant(retainedRecord(process.key).state !== 'terminal', 'Scheduled journal became a manual operation result');
        invariant(text().includes('Scheduled sync observer') && text().includes('observer process result') &&
                  text().includes('They do not establish the result of a manual server operation'), 'Scheduled state lacks separate observer labels');
        (await until(() => { const control = button('Stop scheduled sync observer'); return control && !control.disabled ? control : null }, 'independently permitted observer stop')).click();
        (await until(() => button('Stop observer'), 'scheduled observer stop confirmation')).click();
        const stop = await until(() => allRequests().slice(requests)
                .find(item => item.method === 'StopUnit') ?? null, 'fixed system observer stop');
        invariant(JSON.stringify(stop.arguments) === JSON.stringify(['hfcache-sync.service', 'replace']), 'Observer stop targeted another unit');
        stop.succeed();
        await delay(75);
        invariant(retainedRecord(process.key).state !== 'terminal', 'Stopping a scheduled observer cancelled or completed a manual job');
        process.succeed('sync', 'coexisting-manual-result');
        await until(() => text().includes('coexisting-manual-result'), 'manual result independent of observer stop');
        invariant(boundary.processes.slice(start).filter(item => item.key !== null).length === 1, 'Observer controls submitted another job');
        invariant(allRequests().slice(requests)
                .every(item => item.method !== 'StartUnit'), 'Observer display started a service');
    });

    await test('V37/V38 guarded and unknown profiles disable actual manual selected revision and maintenance controls', async () => {
        for (const state of ['unknown', 'guarded']) {
            boundary.profile = state === 'unknown'
                ? { schema_version: 1, state: 'unknown', reason: 'policy-missing' }
                : {
                    ...structuredClone(DEFAULT_HOST_PROFILE),
                    state: 'guarded',
                    permissions: { archive: false, hub: false, control: false, schedule: false, configuration: false, observer: false },
                    facts: { ...structuredClone(DEFAULT_HOST_PROFILE.facts), guard: 'held', archive_mount: 'nfs-ro' }
                };
            await readHostProfile();
            const start = boundary.processes.length;
            mount(<><SyncOperations /><Verification /><Maintenance /><Dashboard /></>);
            await until(() => button('Run full sync') && button('Run full verification') && button('Dry run'), 'denied actual job controls');
            const status = await until(() => boundary.processes.slice(start).find(item => item.command[0] === 'status') ?? null, 'selected sync status metadata');
            status.succeedEnvelope({ ...configEnvelope({ repositories: [{ repository_type: 'model', repository_id: 'org/model', managed: true, enabled: true }] }), command: 'status' });
            const checkbox = await until(() => document.querySelector<HTMLInputElement>('[id="select-model:org/model"]'), 'valid selected repository control');
            checkbox.click();
            const revision = await until(() => document.querySelector<HTMLInputElement>('#verify-revision-selector'), 'valid revision selector input');
            Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(revision, 'model:org/model@' + 'a'.repeat(40));
            revision.dispatchEvent(new Event('input', { bubbles: true }));
            await delay();
            for (const label of ['Run full sync', 'Run full verification', 'Sync selected (1)', 'Run verify --revision', 'Dry run', 'Run checks (read-only)', 'Run full checks (write probes)'])
                invariant(button(label)?.disabled === true, 'Denied profile enabled ' + label);
            invariant(button('Run verify --estimate')?.disabled === false, 'Denied profile blocked ordinary metadata estimation');
            invariant(text().includes(state === 'guarded' ? 'read-only' : 'not provisioned'), 'Denied controls omit the trusted restriction reason');
            invariant(boundary.processes.slice(start).every(item => item.key === null), 'Rendering denied controls submitted a job');
            const readStart = boundary.processes.length;
            const records = operationRegistry.snapshot().records.length;
            const validation = runHfcache(['config', 'validate']);
            const process = await nextProcess(readStart);
            invariant(process.command.join(' ') === 'config validate' && process.key === null,
                      'Denied workload profile rerouted synchronous validation into a job');
            process.succeed('config validate', 'validation-remains-available');
            await validation;
            invariant(operationRegistry.snapshot().records.length === records, 'Denied-profile synchronous validation invented a job');
            mounted?.unmount();
            mounted = null;
        }
    });

    await test('V37/V38 direct job adapters refuse unknown and guarded profiles before client submission', async () => {
        const commands = [['sync'], ['verify', '--full'], ['repair', 'model:org/model@' + 'a'.repeat(40), '--reason', 'synthetic fixture'],
            ['prune', '--apply'], ['recover', '--apply'], ['plan'], ['doctor', '--read-only'], ['doctor'],
            ['prune', '--dry-run'], ['recover', '--dry-run']];
        for (const state of ['unknown', 'guarded']) {
            boundary.profile = state === 'unknown'
                ? { schema_version: 1, state: 'unknown', reason: 'policy-missing' }
                : {
                    ...structuredClone(DEFAULT_HOST_PROFILE),
                    state: 'guarded',
                    permissions: { archive: false, hub: false, control: false, schedule: false, configuration: false, observer: false },
                    facts: { ...structuredClone(DEFAULT_HOST_PROFILE.facts), guard: 'held', archive_mount: 'nfs-ro' }
                };
            for (const command of commands) {
                boundary.transport.host = 'cpr-denied-' + state + '-' + command[0];
                await readHostProfile();
                const start = boundary.processes.length;
                let failure: unknown;
                const result = runHfcache(command).catch(error => { failure = error });
                await delay(75);
                for (const process of boundary.processes.slice(start))
                    process.fail();
                await result;
                invariant(boundary.processes.length === start,
                          'Direct ' + command.join(' ') + ' bypassed the ' + state + ' profile');
                invariant(failure instanceof Error, 'Denied direct job was not classified');
            }
        }
    });

    await test('V37 job categories enforce their own explicit Hub control and archive permissions', async () => {
        const cases: Array<{ command: string[]; permission: 'archive' | 'hub' | 'control' }> = [
            { command: ['plan'], permission: 'hub' },
            { command: ['doctor', '--read-only'], permission: 'hub' },
            { command: ['doctor'], permission: 'hub' },
            { command: ['doctor'], permission: 'archive' },
            { command: ['prune', '--dry-run'], permission: 'control' },
            { command: ['recover', '--dry-run'], permission: 'control' },
        ];
        for (const [index, item] of cases.entries()) {
            boundary.transport.host = 'cpr-effect-category-' + index;
            boundary.profile = {
                ...structuredClone(DEFAULT_HOST_PROFILE),
                permissions: { ...DEFAULT_HOST_PROFILE.permissions, [item.permission]: false }
            };
            const start = boundary.processes.length;
            const metadata = boundary.metadataProcesses.length;
            let failure: unknown;
            const result = runHfcache(item.command).catch(error => { failure = error });
            await delay(75);
            for (const process of boundary.processes.slice(start))
                process.fail();
            await result;
            invariant(failure instanceof Error && boundary.processes.length === start && boundary.metadataProcesses.length === metadata,
                      item.command.join(' ') + ' bypassed its denied ' + item.permission + ' permission');
        }
    });

    await test('V37/V38 direct configuration mutations refuse unknown and guarded profiles before filesystem effects', async () => {
        for (const state of ['unknown', 'guarded']) {
            boundary.profile = state === 'unknown'
                ? { schema_version: 1, state: 'unknown', reason: 'policy-missing' }
                : {
                    ...structuredClone(DEFAULT_HOST_PROFILE),
                    state: 'guarded',
                    permissions: { archive: false, hub: false, control: false, schedule: false, configuration: false, observer: false },
                    facts: { ...structuredClone(DEFAULT_HOST_PROFILE.facts), guard: 'held', archive_mount: 'nfs-ro' }
                };
            await readHostProfile();
            for (const mutate of [writeCandidate, installCandidate, removeCandidate]) {
                const start = boundary.processes.length;
                let failure: unknown;
                const result = mutate({ installedContent: CONFIG_BASE, candidateContent: CONFIG_DRAFT }).catch(error => { failure = error });
                await delay(75);
                for (const process of boundary.processes.slice(start))
                    process.fail();
                await result;
                invariant(boundary.processes.length === start, 'Direct configuration mutation bypassed the ' + state + ' profile');
                invariant(failure instanceof Error, 'Denied configuration mutation was not classified');
            }
        }
    });

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
        const changing = startUnit('hfcache-sync.timer');
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
        const dryRun = await until(() => readyButton('Dry run'), 'actual maintenance mount');
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
        invariant(preview.key !== null, 'Candidate sizing key must be recorded before spawn');
        preview.emit('Idempotency key: ' + preview.key + '\nOperation: ' + preview.operationId + '\n');
        preview.fail();
        await until(() => text().includes('Sizing observation is uncertain'), 'uncertain preview guidance');
        invariant(session.snapshot().validation?.exit_code === 0, 'Preview failure discarded validation evidence');
        invariant(text().includes('candidate-validate: result') && text().includes('candidate-preview'), 'Stage evidence was lost');
        invariant(session.snapshot().evidence.some(event => event.stage === 'candidate-preview' &&
            event.status === 'notice' && event.notice.kind === 'key' && event.notice.key === preview.key),
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

    await test('V17/V26 failed captured revalidation retains the original uncertain write cause beside the new classified refusal', async () => {
        const session = await mountConfiguration();
        const start = boundary.processes.length;
        button('Validate candidate')?.click();
        (await guardedProcess(start, 'write')).fail(bridgeFailure());
        await until(() => text().includes('candidate-write') && text().includes('reconnected'),
                    'original uncertain candidate-write cause');
        const original = session.snapshot().pipelineError;
        const guard = session.snapshot().diskGuard;
        invariant(original !== null && guard !== null, 'Original write failure or exact captured guard is absent');
        button('Inspect captured configuration')?.click();
        (await guardedProcess(start + 1, 'inspect')).rawSuccess(JSON.stringify({
            candidate: 'matching', installedBase: 'matching', installedCandidate: 'changed', backupBase: 'absent',
        }));
        const revalidate = await until(() => {
            const control = button('Revalidate captured candidate');
            return control && !control.disabled ? control : null;
        }, 'explicit inspected-candidate revalidation');
        boundary.metadataMode = 'manual';
        const metadata = boundary.metadataProcesses.length;
        revalidate.click();
        const authority = await until(() => boundary.metadataProcesses[metadata] ?? null,
                                      'fresh authority read before captured revalidation');
        authority.failEnvelope({ ...configEnvelope({}, 10, 'HFAPI003'), command: 'client describe' });
        await until(() => text().includes('HFAPI003') && session.snapshot().phase === 'idle',
                    'classified captured-revalidation metadata refusal');
        invariant(session.snapshot().pipelineError === original && text().includes('candidate-write') && text().includes('reconnected'),
                  'Captured revalidation replaced the original classified write failure');
        invariant(session.snapshot().reconciliationError !== null && session.snapshot().reconciliationError !== original,
                  'New classified revalidation refusal was not retained separately');
        invariant(session.snapshot().uncertainty === 'candidate' && session.snapshot().diskGuard === guard &&
            session.snapshot().text === CONFIG_DRAFT, 'Failed metadata observation discarded prior uncertainty or exact captured bytes');
        invariant(button('Validate candidate')?.disabled && !button('Discard candidate') && !button('Install validated candidate'),
                  'Failed captured revalidation enabled a new mutation, cleanup or installation');
        invariant(boundary.processes.length === start + 2 &&
            boundary.processes.slice(start).filter(item => item.action === 'write').length === 1,
                  'Failed captured revalidation repeated a write, validation, sizing, install or cleanup');
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

    await test('V22/V28 original operation key is persisted before a process can fail without its first notice', async () => {
        const start = boundary.processes.length;
        const observing = runHfcache(['prune', '--dry-run']).catch(error => error as Error);
        const process = await keyedProcess(start);
        invariant(process.key !== null && process.clientScope !== null, 'Submit process lacks its original key or authority pin');
        const saved = sessionStorage.getItem(OPERATION_STORAGE_KEY);
        invariant(saved?.includes(process.key), 'Process started before the original key was durably recorded');
        invariant(retainedRecord(process.key).state === 'prepared' && retainedRecord(process.key).operationId === null,
                  'Pre-notice record invented admission or an operation identity');
        process.fail();
        const failure = await observing;
        invariant(failure instanceof Error, 'Interrupted actual adapter did not reject');
        invariant(retainedRecord(process.key).state === 'uncertain', 'Lost first notice discarded original uncertainty');
        invariant(boundary.processes.length === start + 1, 'Interrupted process was automatically repeated');
    });

    await test('V11/V26 authentic metadata refusal Envelopes remain visible before any original job can be submitted', async () => {
        boundary.metadataMode = 'manual';
        const start = boundary.metadataProcesses.length;
        const records = operationRegistry.snapshot().records.length;
        mount(<Application />);
        const startup = await until(() => boundary.metadataProcesses[start] ?? null, 'actual startup client authority read');
        startup.failEnvelope({ ...configEnvelope({}, 10, 'HFAPI003'), command: 'capabilities' });
        await until(() => text().includes('HFAPI003'), 'original authenticated startup metadata refusal');
        const readOnlyDoctor = await until(() => readyButton('Run checks (read-only)'), 'actual diagnostic job control');
        readOnlyDoctor.click();
        const retry = await until(() => boundary.metadataProcesses[start + 1] ?? null, 'actual pre-submission metadata check');
        retry.failEnvelope({ ...configEnvelope({}, 10, 'HFAPI018'), command: 'version' });
        await until(() => text().includes('HFAPI018'), 'original diagnostic pre-submission metadata refusal');
        invariant(operationRegistry.snapshot().records.length === records, 'Metadata refusal invented an admitted job record');
        invariant(boundary.processes.every(item => item.key === null || retainedRecord(item.key).scope.host !== boundary.transport.host),
                  'Metadata refusal started a job before authoritative scope was known');
    });

    await test('V24/V27 actual Application tabs retain uncertain maintenance Apply and recover its original operation', async () => {
        mount(<Application />);
        (await until(() => button('Maintenance'), 'actual Application maintenance tab')).click();
        const dry = await until(() => readyButton('Dry run'), 'mounted prune maintenance card');
        const start = boundary.processes.length;
        dry.click();
        const preview = await keyedProcess(start);
        preview.succeed('prune', 'preview-complete');
        const apply = await until(() => {
            const control = button('Apply');
            return control && !control.disabled ? control : null;
        }, 'successful maintenance preview enables deliberate Apply');
        apply.click();
        const runApply = await until(() => button('Run prune --apply'), 'actual maintenance Apply confirmation');
        const submitted = boundary.processes.length;
        runApply.click();
        runApply.click();
        const process = await keyedProcess(submitted);
        invariant(process.key !== null, 'Apply key is absent before first notice');
        process.fail();
        await until(() => button('Apply')?.disabled === true && button('Dry run')?.disabled === true,
                    'uncertain Apply blocks both another Apply and another preview');
        invariant(boundary.processes.slice(submitted).filter(item => item.key !== null).length === 1,
                  'Double confirmation submitted duplicate Apply processes');
        const key = process.key;
        invariant(originalSection(key), 'Root recovery UI lost the original Apply key');
        button('Overview')?.click();
        await until(() => button('Dry run') === null, 'actual unmountOnExit removed maintenance controls');
        invariant(originalSection(key), 'Tab unmount removed original recovery controls');
        button('Maintenance')?.click();
        await until(() => button('Dry run')?.disabled === true && button('Apply')?.disabled === true,
                    'remounted maintenance remains blocked by the original unresolved operation');
        const section = originalSection(key);
        invariant(section, 'Original Apply recovery section is unavailable after remount');
        const lookupStart = boundary.processes.length;
        button('Look up original key', section)?.click();
        const lookup = await nextProcess(lookupStart);
        invariant(lookup.command.join(' ') === 'operations lookup -- ' + key && lookup.clientScope === process.clientScope,
                  'Authenticated lookup changed the original key or authority pin');
        const id = '9'.repeat(32);
        lookup.succeedEnvelope(lookupEnvelope(retainedRecord(key), id));
        await until(() => originalSection(key)?.textContent?.includes(id) === true, 'original accepted operation identity');
        const waitStart = boundary.processes.length;
        button('Observe original operation', originalSection(key)!)?.click();
        const wait = await nextProcess(waitStart);
        invariant(wait.command.join(' ') === 'operations wait -- ' + id && wait.clientScope === process.clientScope,
                  'Observation followed a replacement operation or changed authority');
        wait.succeedEnvelope({ ...configEnvelope({ marker: 'original-apply-terminal' }), command: 'prune --apply' });
        await until(() => originalSection(key)?.textContent?.includes('original-apply-terminal') === true,
                    'authenticated original terminal result');
        invariant(retainedRecord(key).state === 'terminal', 'Original terminal result did not resolve the retained record');
        invariant(boundary.processes.slice(submitted).filter(item => item.key !== null).length === 1,
                  'Lookup or observation resubmitted maintenance work');
    });

    await test('V29/V30 missing original history remains uncertain and never permits a replacement submission', async () => {
        const start = boundary.processes.length;
        const submitting = runHfcache(['recover', '--dry-run']).catch(error => error);
        const process = await keyedProcess(start);
        process.fail();
        await submitting;
        invariant(process.key !== null, 'Original recovery key is absent');
        mount(<Application />);
        const section = await until(() => originalSection(process.key!), 'original missing-history recovery section');
        const lookup = await until(() => {
            const control = button('Look up original key', section);
            return control && !control.disabled ? control : null;
        }, 'same-authority explicit lookup');
        const lookupStart = boundary.processes.length;
        lookup.click();
        const request = await nextProcess(lookupStart);
        request.failEnvelope({ ...configEnvelope({}, 20, 'HFAPI013'), command: 'operations lookup' });
        await until(() => originalSection(process.key!)?.textContent?.includes('does not prove nonexecution') === true,
                    'missing history uncertainty guidance');
        invariant(retainedRecord(process.key).state === 'missing', 'Missing history erased the original record');
        button('Maintenance')?.click();
        await until(() => button('Dry run')?.disabled === true, 'missing history keeps another maintenance submission blocked');
        invariant(boundary.processes.slice(start).filter(item => item.key !== null).length === 1,
                  'Missing history created a replacement operation');
    });

    await test('V32 an explicit original-operation wait refuses a conflicting notice despite successful terminal stdout', async () => {
        const start = boundary.processes.length;
        const submitting = runHfcache(['prune', '--apply']).catch(error => error);
        const process = await keyedProcess(start);
        invariant(process.key !== null, 'Original apply key is absent');
        const key = process.key;
        process.emit('Idempotency key: ' + key + '\nOperation: ' + process.operationId + '\n');
        process.fail();
        await submitting;
        invariant(retainedRecord(key).operationId === process.operationId, 'Original accepted operation identity was lost');
        mount(<Application />);
        const observe = await until(() => {
            const section = originalSection(key);
            const control = section && button('Observe original operation', section);
            return control && !control.disabled ? control : null;
        }, 'same-authority original operation observation');
        const before = boundary.processes.length;
        observe.click();
        const wait = await nextProcess(before);
        invariant(wait.command.join(' ') === 'operations wait -- ' + process.operationId, 'Wait command changed the original ID');
        wait.emit('Operation: ' + 'f'.repeat(32) + '\n');
        wait.succeedEnvelope({ ...configEnvelope({ marker: 'conflicting-stdout' }), command: 'prune --apply' });
        await until(() => operationViews().records.get(key)?.busy === false, 'explicit wait observation completion');
        const retained = retainedRecord(key);
        invariant(retained.state === 'conflict', 'Conflicting wait identity became terminal success');
        invariant(retained.key === key && retained.operationId === process.operationId, 'Wait conflict overwrote the original handles');
        invariant(boundary.processes.slice(start).filter(item => item.key !== null).length === 1,
                  'Conflicting wait replayed a submission');
    });

    await test('V26 changed client authority refuses following an original handle after refreshing metadata', async () => {
        const start = boundary.processes.length;
        const submitting = runHfcache(['doctor', '--read-only']).catch(error => error);
        const process = await keyedProcess(start);
        process.fail();
        await submitting;
        invariant(process.key !== null, 'Original diagnostic key is absent');
        mount(<Application />);
        const section = await until(() => originalSection(process.key!), 'original scoped diagnostic record');
        const lookup = await until(() => {
            const control = button('Look up original key', section);
            return control && !control.disabled ? control : null;
        }, 'original metadata enables same-scope observation');
        boundary.metadata = { ...boundary.metadata, profile_fingerprint: 'f'.repeat(64), authority_fingerprint: 'b'.repeat(64) };
        const before = boundary.processes.length;
        lookup.click();
        await until(() => operationViews().authority.scope?.profile === 'f'.repeat(64) &&
            operationViews().records.get(process.key!)?.busy === false,
                    'changed authority lookup finishes without following the original handle');
        await until(() => button('Look up original key', originalSection(process.key!)!)?.disabled === true,
                    'fresh changed authority disables old-handle observation');
        invariant(boundary.processes.slice(before).every(item => item.key === null && item.command[0] !== 'operations'),
                  'Changed profile followed an original key or submitted work');
        invariant(retainedRecord(process.key).scope.profile !== 'f'.repeat(64), 'Changed profile silently adopted the old record');
    });

    await test('V18/V22 a candidate sizing failure before its first notice recovers only the original captured operation', async () => {
        const draft = CONFIG_DRAFT.replace('enabled=false', 'enabled=true');
        const { session, start, validation } = await beginValidation(draft, true);
        validation.succeedEnvelope(assessment());
        const preview = await guardedProcess(start + 2, 'guard');
        invariant(preview.key !== null, 'Sizing key was not created before its process');
        const key = preview.key;
        preview.fail();
        await until(() => session.snapshot().previewUncertain && session.snapshot().previewKey === key,
                    'pre-notice candidate sizing identity and uncertainty retention');
        invariant(!button('Install validated candidate'), 'Unobserved sizing granted installation');
        const section = await until(() => originalSection(key), 'root sizing recovery section');
        const lookupStart = boundary.processes.length;
        button('Look up original key', section)?.click();
        const lookup = await nextProcess(lookupStart);
        invariant(lookup.command.join(' ') === 'operations lookup -- ' + key, 'Candidate recovery replaced its original key');
        lookup.succeedEnvelope(lookupEnvelope(retainedRecord(key), preview.operationId));
        await until(() => {
            const control = button('Observe original operation', originalSection(key)!);
            return control && !control.disabled ? control : null;
        }, 'original sizing receipt available for observation');
        const waitStart = boundary.processes.length;
        button('Observe original operation', originalSection(key)!)?.click();
        const wait = await nextProcess(waitStart);
        wait.succeedEnvelope({
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
            command: 'plan'
        });
        await until(() => !session.snapshot().previewUncertain, 'authenticated original sizing terminal evidence');
        invariant(!button('Install validated candidate'), 'Recovering sizing alone silently restored installation readiness');
        const inspectStart = boundary.processes.length;
        button('Inspect captured configuration')?.click();
        (await guardedProcess(inspectStart, 'inspect')).rawSuccess(JSON.stringify({
            candidate: 'matching', installedBase: 'matching', installedCandidate: 'changed', backupBase: 'absent',
        }));
        const revalidate = await until(() => {
            const control = button('Revalidate captured candidate');
            return control && !control.disabled ? control : null;
        }, 'captured files explicitly reconciled for revalidation');
        const revalidationStart = boundary.processes.length;
        revalidate.click();
        (await guardedProcess(revalidationStart, 'guard')).succeedEnvelope(assessment());
        await until(() => button('Install validated candidate'), 'fresh validation reuses the original exact sizing result');
        invariant(session.snapshot().diskGuard?.candidateContent === draft, 'Recovered sizing adopted different candidate bytes');
        invariant(boundary.processes.slice(start).filter(item => item.action === 'write').length === 1,
                  'Sizing recovery repeated a candidate write');
        invariant(boundary.processes.slice(start).filter(item => item.key !== null).length === 1,
                  'Sizing recovery submitted another plan');
        invariant(text().includes('reconnected'), 'Successful sizing reconciliation hid its original failure');
    });

    await test('V26 maintenance Apply cannot reuse a preview through a changed client profile', async () => {
        mount(<Maintenance />);
        const dry = await until(() => readyButton('Dry run'), 'actual maintenance preview');
        const start = boundary.processes.length;
        dry.click();
        (await keyedProcess(start)).succeed('prune', 'same-scope-preview');
        const apply = await until(() => {
            const control = button('Apply');
            return control && !control.disabled ? control : null;
        }, 'completed maintenance preview');
        boundary.metadata = { ...boundary.metadata, profile_fingerprint: 'f'.repeat(64), authority_fingerprint: 'b'.repeat(64) };
        apply.click();
        const confirm = await until(() => button('Run prune --apply'), 'actual changed-scope Apply confirmation');
        const before = boundary.processes.length;
        confirm.click();
        await until(() => button('Apply')?.disabled === true && button('Dry run')?.disabled === true,
                    'changed authority invalidates the prior maintenance preview');
        await delay(75);
        invariant(boundary.processes.slice(before).every(item => item.key === null), 'Changed authority transmitted maintenance Apply');
    });

    await test('V19/V26 a confirmed uncertain installation cannot be acknowledged after client authority changes', async () => {
        const { session, start, validation } = await beginValidation(CONFIG_DRAFT, true);
        validation.succeedEnvelope(assessment());
        (await until(() => button('Install validated candidate'), 'captured same-authority proposal')).click();
        (await guardedProcess(start + 2, 'install')).fail();
        await until(() => button('Inspect captured configuration'), 'uncertain installation inspection');
        button('Inspect captured configuration')?.click();
        (await guardedProcess(start + 3, 'inspect')).rawSuccess(JSON.stringify({
            candidate: 'absent', installedBase: 'changed', installedCandidate: 'matching', backupBase: 'matching',
        }));
        (await until(() => button('Confirm captured installation'), 'same-authority installed confirmation')).click();
        (await guardedProcess(start + 4, 'confirm')).succeedEnvelope(configEnvelope({ config_fingerprint: FINGERPRINT }));
        const acknowledge = await until(() => button('Acknowledge confirmed installation'), 'confirmed captured installation acknowledgement');
        invariant(!acknowledge.disabled, 'Same-authority explicit acknowledgement was unavailable');
        boundary.metadata = { ...boundary.metadata, profile_fingerprint: 'f'.repeat(64), authority_fingerprint: 'b'.repeat(64) };
        button('Refresh client authority')?.click();
        await until(() => operationViews().authority.scope?.profile === 'f'.repeat(64), 'new client authority observation');
        await delay(75);
        const changed = button('Acknowledge confirmed installation');
        invariant(changed === null || changed.disabled, 'Changed client authority retained stale acknowledgement readiness');
        acknowledge.click();
        invariant(session.snapshot().uncertainty === 'install' && session.snapshot().diskGuard !== null,
                  'Stale acknowledgement discarded original installation uncertainty');
        invariant(boundary.processes.slice(start).filter(item => item.action === 'install').length === 1,
                  'Changed authority repeated installation');
    });

    await test('V27/V28 an unresolved operation disables other actual job controls while metadata estimation remains available', async () => {
        const start = boundary.processes.length;
        const observing = runHfcache(['prune', '--dry-run']).catch(error => error);
        (await keyedProcess(start)).fail();
        await observing;
        mount(<Application />);
        await until(() => button('Run checks (read-only)')?.disabled === true &&
            button('Run full checks (write probes)')?.disabled === true, 'global uncertainty disables both diagnostic job controls');
        const syncStart = boundary.processes.length;
        button('Sync')?.click();
        const answered = new Set<ProcessBoundary>();
        const selected = await until(() => {
            for (const inventory of boundary.processes.slice(syncStart).filter(item => item.command.join(' ') === 'status')) {
                if (!answered.has(inventory)) {
                    answered.add(inventory);
                    inventory.succeedEnvelope({
                        ...configEnvelope({
                            repositories: [{
                                repository_type: 'model', repository_id: 'org/model', enabled: true, managed: true,
                            }]
                        }),
                        command: 'status'
                    });
                }
            }
            return document.getElementById('select-model:org/model') as HTMLInputElement | null;
        }, 'actual managed enabled selector checkbox');
        selected.click();
        const selectedAction = await until(() => button('Sync selected (1)'), 'actual valid selected-sync action');
        invariant(selectedAction.disabled, 'Unresolved operation enabled an additional selected sync');
        button('Verification')?.click();
        const selector = await until(() => document.querySelector<HTMLInputElement>('#verify-revision-selector'), 'actual revision verification input');
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
        invariant(setter, 'Native input setter is unavailable');
        setter.call(selector, 'model:org/model@' + 'a'.repeat(40));
        selector.dispatchEvent(new Event('input', { bubbles: true }));
        await delay(75);
        await until(() => button('Run verify --revision')?.disabled === true, 'unresolved operation blocks a valid revision submission');
        const estimate = button('Run verify --estimate');
        invariant(estimate && !estimate.disabled, 'Unresolved job incorrectly disabled synchronous metadata estimation');
        const before = boundary.processes.length;
        estimate.click();
        const request = await nextProcess(before);
        invariant(request.command.join(' ') === 'verify --estimate' && request.key === null,
                  'Metadata estimate became a new keyed operation');
        request.succeedEnvelope({ ...configEnvelope({}), command: 'verify --estimate' });
    });

    await test('V23/V28 all actual keyed adapters persist only original scoped recovery metadata', async () => {
        const commands = [
            ['plan'], ['plan', 'model:org/model'], ['doctor', '--read-only'], ['doctor'],
            ['prune', '--dry-run'], ['prune', '--apply'], ['recover', '--dry-run'], ['recover', '--apply'],
            ['repair', 'model:org/model@' + 'a'.repeat(40), '--reason', 'SYNTHETIC_PRIVATE_REASON'],
            ['sync'], ['sync', 'model:org/model'], ['verify', '--new'], ['verify', '--full'],
            ['verify', '--revision', 'model:org/model@' + 'a'.repeat(40)],
        ];
        for (const [index, command] of commands.entries()) {
            const start = boundary.processes.length;
            const candidate = index === 1;
            const observing = runHfcache(command, candidate
                ? {
                    config: CONFIGURATION_PATHS.candidate,
                    candidateGuard: { candidateContent: CONFIG_DRAFT + '# SYNTHETIC_PRIVATE_CANDIDATE\n', installedContent: CONFIG_BASE },
                }
                : {});
            const process = await keyedProcess(start);
            invariant(process.key !== null && process.clientScope !== null, 'Keyed adapter omitted pretransmission recovery metadata');
            const original = retainedRecord(process.key);
            invariant(original.operationId === null && original.state === 'prepared', 'Adapter invented admission before receipts');
            const canonical = command[0] === 'verify'
                ? command.includes('--full') ? 'verify --full' : command.includes('--new') ? 'verify --new' : 'verify --revision'
                : ['prune', 'recover'].includes(command[0]) ? command[0] + ' ' + command[1] : command[0];
            process.succeedEnvelope({ ...configEnvelope({}), command: canonical });
            await observing;
            invariant(retainedRecord(process.key).operationId === process.operationId && retainedRecord(process.key).state === 'terminal',
                      'Adapter lost its original receipt or exact terminal classification');
            const stored = sessionStorage.getItem(OPERATION_STORAGE_KEY) ?? '';
            invariant(!stored.includes('SYNTHETIC_PRIVATE_REASON') && !stored.includes('SYNTHETIC_PRIVATE_CANDIDATE') &&
                !stored.includes(CONFIG_BASE), 'Recovery storage persisted arbitrary reason, candidate or configuration bytes');
        }
    });

    await test('V28 synchronous validation and reads create no operation registry record or key', async () => {
        const before = operationRegistry.snapshot().records.length;
        for (const command of [['config', 'validate'], ['version', '--server'], ['status'], ['verify', '--estimate']]) {
            const start = boundary.processes.length;
            const reading = runHfcache(command);
            const process = await nextProcess(start);
            invariant(process.key === null, 'Synchronous read or validation invented an operation key');
            process.succeedEnvelope({ ...configEnvelope({}), command: command[0] === 'version' ? 'version' : command.join(' ') });
            await reading;
        }
        invariant(operationRegistry.snapshot().records.length === before, 'Non-job adapters created fake operation records');
    });

    await test('V24/V25 actual Application reload restores the original key without another submission', async () => {
        await withFreshStorage(async () => {
            const frame = await frameApplication('cpr-reload-original');
            let child = frame.contentWindow;
            invariant(child && frame.contentDocument, 'Owned application frame is inaccessible');
            button('Maintenance', frame.contentDocument)?.click();
            await until(() => readyButton('Dry run', frame.contentDocument!), 'fresh iframe maintenance tab');
            const first = child.cprFixture;
            const start = first.processes.length;
            button('Dry run', frame.contentDocument)?.click();
            const process = await keyedProcess(start, first);
            invariant(process.key !== null, 'Fresh module did not retain its original key');
            const key = process.key;
            process.fail();
            await until(() => originalSection(key, frame.contentDocument!)?.textContent?.includes('uncertain') === true,
                        'uncertain frame record before reload');
            child.location.reload();
            await until(() => frame.contentWindow?.cprProbeReady === true && frame.contentWindow.cprFixture !== first,
                        'actual same-origin reload creates a fresh application module');
            child = frame.contentWindow;
            invariant(child && frame.contentDocument, 'Reloaded owned frame is inaccessible');
            await until(() => originalSection(key, frame.contentDocument!), 'original key restored into global recovery after full reload');
            button('Maintenance', frame.contentDocument)?.click();
            await until(() => button('Dry run', frame.contentDocument!)?.disabled === true,
                        'restored uncertainty blocks a new submission');
            invariant(child.cprFixture.processes.every(item => item.key === null), 'Full reload automatically replayed an original or replacement submission');
            invariant(sessionStorage.getItem(OPERATION_STORAGE_KEY)?.includes(key), 'Full reload discarded persisted original identity');
        });
    });

    await test('V23/V25 fresh Application modules reject corrupt, unknown-schema and oversized stored recovery metadata', async () => {
        await withFreshStorage(async () => {
            const payloads = ['{broken', JSON.stringify({ schemaVersion: 99, records: [] }), 'x'.repeat(MAX_OPERATION_STORAGE_BYTES + 1)];
            for (const [index, payload] of payloads.entries()) {
                sessionStorage.setItem(OPERATION_STORAGE_KEY, payload);
                const frame = await frameApplication('cpr-hostile-storage-' + index);
                invariant(frame.contentDocument && frame.contentWindow, 'Owned hostile-storage module is inaccessible');
                await until(() => frame.contentDocument?.body.textContent?.includes('Operation recovery metadata is invalid') === true,
                            'explicit hostile storage refusal');
                button('Maintenance', frame.contentDocument)?.click();
                await until(() => button('Dry run', frame.contentDocument!)?.disabled === true,
                            'invalid persisted metadata blocks submission');
                invariant(frame.contentWindow.cprFixture.processes.every(item => item.key === null), 'Hostile storage created a job or command authority');
                invariant(sessionStorage.getItem(OPERATION_STORAGE_KEY) === payload, 'Invalid storage evidence was silently replaced');
                frame.remove();
            }
        });
    });

    await test('V23 actual browser session-storage quota failure refuses a job before its process starts', async () => {
        await withFreshStorage(async () => {
            const keys: string[] = [];
            let bytes = 0;
            try {
                for (const size of [256 * 1024, 4096, 256]) {
                    let refused = false;
                    while (bytes + size <= 16 * 1024 * 1024) {
                        const key = 'cpr-owned-quota-' + keys.length;
                        try {
                            sessionStorage.setItem(key, 'q'.repeat(size));
                            keys.push(key);
                            bytes += size;
                        } catch (error) {
                            invariant(error instanceof DOMException && error.name === 'QuotaExceededError',
                                      'Owned browser storage failed for a reason other than its actual quota');
                            refused = true;
                            break;
                        }
                    }
                    invariant(refused, 'Actual browser session quota was not reached within the 16 MiB investigation bound');
                }
                const frame = await frameApplication('cpr-actual-quota');
                invariant(frame.contentDocument && frame.contentWindow, 'Owned quota-test module is inaccessible');
                button('Maintenance', frame.contentDocument)?.click();
                const dry = await until(() => readyButton('Dry run', frame.contentDocument!), 'actual quota-test maintenance control');
                dry.click();
                await until(() => frame.contentDocument?.body.textContent?.includes('Operation recovery storage is unavailable') === true,
                            'explicit actual browser quota refusal');
                invariant(frame.contentWindow.cprFixture.processes.every(item => item.key === null),
                          'Failed durable preparation started a keyed process');
                invariant(sessionStorage.getItem(OPERATION_STORAGE_KEY) === null,
                          'Quota refusal claimed a durable original operation record');
                frame.remove();
            } finally {
                for (const key of keys)
                    sessionStorage.removeItem(key);
            }
        });
    });

    await test('V25/V31 restored terminal summaries cannot unlock jobs before original authenticated result confirmation', async () => {
        for (const forged of [false, true]) {
            await withFreshStorage(async () => {
                const host = 'cpr-restored-terminal-' + String(forged);
                const frame = await frameApplication(host);
                invariant(frame.contentDocument && frame.contentWindow, 'Owned terminal-restore module is inaccessible');
                button('Maintenance', frame.contentDocument)?.click();
                const dry = await until(() => readyButton('Dry run', frame.contentDocument!), 'owned terminal-restore maintenance control');
                const first = frame.contentWindow.cprFixture;
                const start = first.processes.length;
                dry.click();
                const submission = await keyedProcess(start, first);
                invariant(submission.key !== null, 'Original terminal-restore key is absent');
                const key = submission.key;
                if (forged) {
                    submission.emit('Idempotency key: ' + key + '\nOperation: ' + submission.operationId + '\n');
                    submission.fail();
                } else {
                    submission.succeedEnvelope({ ...configEnvelope({ marker: 'original-terminal' }), command: 'prune --dry-run' });
                }
                await until(() => originalSection(key, frame.contentDocument!)?.textContent?.includes(forged ? 'uncertain' : 'terminal') === true,
                            'original captured result before module reload');
                const stored = JSON.parse(sessionStorage.getItem(OPERATION_STORAGE_KEY) ?? '') as { records: OperationRecord[] };
                const record = stored.records.find(item => item.key === key);
                invariant(record, 'Serialized original record is absent');
                if (forged) {
                    record.state = 'terminal';
                    record.terminal = { command: 'prune --dry-run', exitCode: 0, outcome: 'success', runId: 'f'.repeat(32), code: null };
                    sessionStorage.setItem(OPERATION_STORAGE_KEY, JSON.stringify(stored));
                }
                frame.contentWindow.location.reload();
                await until(() => frame.contentWindow?.cprProbeReady === true && frame.contentWindow.cprFixture !== first,
                            'fresh module loading a syntactically valid terminal summary');
                const child = frame.contentWindow;
                invariant(child && frame.contentDocument, 'Reloaded terminal-restore module is inaccessible');
                button('Maintenance', frame.contentDocument)?.click();
                const blocked = await until(() => button('Dry run', frame.contentDocument!), 'restored maintenance job control');
                invariant(blocked.disabled, 'Untrusted restored terminal summary unlocked another submission');
                invariant(child.cprFixture.processes.every(item => item.key === null), 'Reloaded terminal metadata started a job');
                const lookup = await until(() => {
                    const section = originalSection(key, frame.contentDocument!);
                    const control = section && button('Look up original key', section);
                    return control && !control.disabled ? control : null;
                }, 'same-authority original lookup after terminal restoration');
                const lookupStart = child.cprFixture.processes.length;
                lookup.click();
                const lookupRequest = await until(() => child.cprFixture.processes.slice(lookupStart)
                        .find(item => item.command[0] === 'operations') ?? null, 'original restored-key lookup request');
                invariant(lookupRequest.command.join(' ') === 'operations lookup -- ' + key, 'Restored lookup changed its original key');
                lookupRequest.succeedEnvelope(lookupEnvelope(record, submission.operationId));
                const observe = await until(() => {
                    const section = originalSection(key, frame.contentDocument!);
                    const control = section && button('Observe original operation', section);
                    return control && !control.disabled ? control : null;
                }, 'original restored operation observation control');
                const waitStart = child.cprFixture.processes.length;
                observe.click();
                const wait = await until(() => child.cprFixture.processes.slice(waitStart)
                        .find(item => item.command[0] === 'operations') ?? null, 'authenticated original restored operation wait');
                invariant(wait.command.join(' ') === 'operations wait -- ' + submission.operationId, 'Restored wait changed its original operation ID');
                wait.succeedEnvelope({ ...configEnvelope({ marker: 'original-terminal' }), command: 'prune --dry-run' });
                await until(() => originalSection(key, frame.contentDocument!)?.textContent?.includes(forged ? 'conflict' : 'original-terminal') === true,
                            'authenticated result confirmation distinguishes changed terminal summaries');
                await delay(75);
                invariant(button('Dry run', frame.contentDocument!)?.disabled === forged,
                          'Authenticated result did not preserve the required restored-summary boundary');
                const confirmed = JSON.parse(sessionStorage.getItem(OPERATION_STORAGE_KEY) ?? '') as { records: OperationRecord[] };
                const retained = confirmed.records.find(item => item.key === key);
                invariant(retained?.key === key && retained.operationId === submission.operationId && retained.state === (forged ? 'conflict' : 'terminal'),
                          'Restored summary confirmation lost its original handles or conflict');
                invariant(child.cprFixture.processes.every(item => item.key === null), 'Terminal confirmation replayed or replaced a job');
            });
        }
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

const probe = new URLSearchParams(window.location.search);
if (probe.get('cpr-probe') === 'application') {
    const host = probe.get('host');
    invariant(host && /^[A-Za-z0-9][A-Za-z0-9._-]{0,100}$/.test(host), 'Invalid owned probe host');
    boundary.transport.host = host;
    mount(<Application />);
    until(() => document.querySelector('[aria-label="Original operation recovery"]'), 'fresh probe Application')
            .then(() => { window.cprProbeReady = true });
} else {
    report();
}
