#!/usr/bin/env node
/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Mount actual components in an owned Firefox profile. Only Cockpit's external
 * process, D-Bus and privilege event boundaries are controlled; no host command,
 * API, PAM session or archive is used by the browser fixture.
 */

import { execFileSync, spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { build } from 'esbuild';

/** @typedef {{name:string, passed:boolean, message?:string}} TestResult */
/** @typedef {{state:string, tests?:TestResult[], message?:string}} BrowserResult */

async function main() {
    const cockpit = fileURLToPath(new URL('../', import.meta.url));
    const repository = resolve(cockpit, '..');
    const sourceRef = process.argv[2];
    const manualBaseline = process.env.CPR_BROWSER_MANUAL_BASELINE;
    const reportBaseline = process.env.CPR_BROWSER_REPORT_BASELINE;
    const journalBaseline = process.env.CPR_BROWSER_JOURNAL_BASELINE;
    if (sourceRef !== undefined && !/^[0-9a-f]{40}$/.test(sourceRef))
        throw new Error('An optional baseline must be an exact forty-character commit SHA');
    if (manualBaseline !== undefined && !/^[0-9a-f]{40}$/.test(manualBaseline))
        throw new Error('A manual-component baseline must be an exact forty-character commit SHA');
    if ([reportBaseline, journalBaseline].some(value => value !== undefined && !/^[0-9a-f]{40}$/.test(value)))
        throw new Error('Report/journal baselines must be exact forty-character commit SHAs');
    const RESULT_BYTES = 32768;
    const resultPath = '/result/' + randomUUID();
    const profileParent = await mkdtemp(join(tmpdir(), 'hfcache-cpr-mounted-'));
    const profile = join(profileParent, 'profile');
    await mkdir(profile, { mode: 0o700 });
    await writeFile(join(profile, 'user.js'), [
        'user_pref("browser.shell.checkDefaultBrowser", false);',
        'user_pref("browser.startup.homepage_override.mstone", "ignore");',
        'user_pref("browser.newtabpage.enabled", false);',
        'user_pref("browser.aboutwelcome.enabled", false);',
        'user_pref("datareporting.policy.dataSubmissionEnabled", false);',
        'user_pref("toolkit.telemetry.enabled", false);',
        'user_pref("network.captive-portal-service.enabled", false);',
        'user_pref("network.connectivity-service.enabled", false);',
        'user_pref("network.prefetch-next", false);',
        'user_pref("signon.rememberSignons", false);',
    ].join('\n'), { mode: 0o600 });

    const built = await build({
        entryPoints: [join(cockpit, 'test/browser.fixture.tsx')],
        absWorkingDir: cockpit,
        bundle: true,
        write: false,
        format: 'iife',
        platform: 'browser',
        define: { 'process.env.NODE_ENV': '"test"' },
        loader: { '.css': 'empty', '.scss': 'empty' },
        logLevel: 'silent',
        plugins: [{
            name: 'controlled-cockpit-boundaries',
            setup(builder) {
                builder.onResolve({ filter: /^(cockpit|superuser)$/ }, args => ({
                    path: args.path, namespace: 'fixture',
                }));
                builder.onLoad({ filter: /.*/, namespace: 'fixture' }, args => ({
                    contents: 'import { controlledCockpit } from ' + JSON.stringify(join(cockpit, 'test/cockpit-fixture.ts')) + ';' +
                    (args.path === 'superuser'
                        ? 'export const superuser = controlledCockpit.superuser;'
                        : 'export default { transport: controlledCockpit.transport, gettext: value => value, assert: value => { if (!value) throw new Error("Controlled Cockpit assertion failed"); }, spawn: (...args) => controlledCockpit.spawn(...args), dbus: (...args) => controlledCockpit.dbus(...args), file: (...args) => controlledCockpit.file(...args) };'),
                    loader: 'js',
                    resolveDir: cockpit,
                }));
                if (sourceRef !== undefined) {
                    builder.onLoad({ filter: /[/\\]cockpit[/\\]src[/\\].*\.[jt]sx?$/ }, args => ({
                        contents: execFileSync('rtk', [
                            'proxy', 'git', 'show', sourceRef + ':' + relative(repository, args.path),
                        ], { cwd: repository, maxBuffer: 2 * 1024 * 1024 }).toString('utf8'),
                        loader: args.path.endsWith('.tsx') ? 'tsx' : 'ts',
                    }));
                } else if (reportBaseline !== undefined || journalBaseline !== undefined) {
                    builder.onLoad({ filter: /[/\\]cockpit[/\\]src[/\\](reports\.tsx|api[/\\]archive\.ts)$/ }, args => {
                        const baseline = args.path.endsWith('reports.tsx') ? reportBaseline : reportBaseline ?? journalBaseline;
                        return baseline === undefined
                            ? undefined
                            : {
                                contents: execFileSync('rtk', ['proxy', 'git', 'show', baseline + ':' + relative(repository, args.path)],
                                                       { cwd: repository, maxBuffer: 2 * 1024 * 1024 }).toString('utf8'),
                                loader: args.path.endsWith('.tsx') ? 'tsx' : 'ts',
                            };
                    });
                } else if (manualBaseline !== undefined) {
                    builder.onLoad({ filter: /[/\\]cockpit[/\\]src[/\\](sync|verify)\.tsx$/ }, args => ({
                        contents: execFileSync('rtk', [
                            'proxy', 'git', 'show', manualBaseline + ':' + relative(repository, args.path),
                        ], { cwd: repository, maxBuffer: 2 * 1024 * 1024 }).toString('utf8'),
                        loader: 'tsx',
                    }));
                }
            },
        }],
    });
    const bundle = built.outputFiles[0]?.contents;
    if (bundle === undefined || bundle.byteLength > 16 * 1024 * 1024)
        throw new Error('Mounted test bundle is absent or exceeds its bound');
    const bundleSha256 = createHash('sha256').update(bundle)
            .digest('hex');
    /** @type {(value:BrowserResult) => void} */
    let deliver = () => undefined;
    /** @type {Promise<BrowserResult>} */
    const delivered = new Promise(resolve => { deliver = resolve });
    const server = createServer((request, response) => {
        const pathname = new URL(request.url ?? '/', 'http://fixture.invalid').pathname;
        if (request.method === 'GET' && pathname === '/') {
            response.setHeader('Content-Type', 'text/html; charset=utf-8');
            response.end('<!doctype html><meta charset="utf-8"><title>Owned mounted hfcache tests</title>' +
            '<div id="fixture"></div><script>window.cprTestFilter=' + JSON.stringify(process.env.CPR_BROWSER_TEST_FILTER ?? '') + ';window.cprResultPath=' + JSON.stringify(resultPath) +
            '</script><script src="/bundle.js"></script>');
        } else if (request.method === 'GET' && request.url === '/bundle.js') {
            response.setHeader('Content-Type', 'application/javascript');
            response.end(bundle);
        } else if (request.method === 'POST' && request.url === resultPath) {
        /** @type {Buffer[]} */
            const chunks = [];
            let bytes = 0;
            request.on('data', chunk => {
                bytes += chunk.length;
                if (bytes > RESULT_BYTES) {
                    response.writeHead(413).end();
                    request.destroy();
                    deliver({ state: 'failed', message: 'Browser result exceeds its bound' });
                } else {
                    chunks.push(chunk);
                }
            });
            request.on('end', () => {
                try {
                    const result = JSON.parse(Buffer.concat(chunks).toString('utf8'));
                    response.writeHead(204).end();
                    deliver(result);
                } catch {
                    response.writeHead(400).end();
                    deliver({ state: 'failed', message: 'Browser result is not JSON' });
                }
            });
        } else {
            response.writeHead(404).end();
        }
    });
    await new Promise((resolve, reject) => {
        server.once('error', reject);
        server.listen(0, '127.0.0.1', () => resolve(undefined));
    });
    const address = server.address();
    if (address === null || typeof address === 'string')
        throw new Error('Mounted test listener is not an owned loopback socket');
    const browser = spawn('/usr/bin/firefox', [
        '--headless', '--new-instance', '--profile', profile, `http://127.0.0.1:${address.port}/`,
    ], {
        env: {
            PATH: '/usr/bin:/bin',
            HOME: process.env.HOME,
            LANG: 'C.UTF-8',
            XDG_CACHE_HOME: join(profileParent, 'cache'),
            XDG_CONFIG_HOME: join(profileParent, 'config'),
            XDG_DATA_HOME: join(profileParent, 'data'),
        },
        stdio: ['ignore', 'pipe', 'pipe'],
    });
    let browserLog = '';
    for (const stream of [browser.stdout, browser.stderr])
        stream.on('data', chunk => { browserLog = (browserLog + chunk.toString('utf8')).slice(-4096) });
    /** @type {ReturnType<typeof setTimeout>|undefined} */
    let timeout;
    /** @type {BrowserResult} */
    const result = await Promise.race([
        delivered,
        new Promise(resolve => {
            timeout = setTimeout(() => resolve({ state: 'failed', message: 'Browser deadline exceeded' }), 60000);
        }),
        new Promise(resolve => {
            browser.once('error', () => resolve({ state: 'failed', message: 'Firefox could not start' }));
            browser.once('exit', () => resolve({ state: 'failed', message: 'Firefox exited before reporting' }));
        }),
    ]);
    clearTimeout(timeout);
    const closed = new Promise(resolve => browser.once('close', resolve));
    if (browser.exitCode === null && browser.signalCode === null)
        browser.kill('SIGTERM'); // Owned fixture process only; no application execution exists.
    await Promise.race([closed, new Promise(resolve => setTimeout(resolve, 5000))]);
    if (browser.exitCode === null && browser.signalCode === null)
        browser.kill('SIGKILL');
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
    const passed = result.state === 'passed' && Array.isArray(result.tests) &&
    result.tests.length >= (process.env.CPR_BROWSER_TEST_FILTER ? 1 : 6) && result.tests.every(test => test.passed === true);
    console.log(JSON.stringify({
        fixture: 'actual mounted React with controlled Cockpit boundaries',
        real_pam: false,
        real_api_or_shell: false,
        source_ref: sourceRef ?? 'working-tree',
        ...(manualBaseline === undefined ? {} : { manual_component_baseline: manualBaseline }),
        ...(reportBaseline === undefined ? {} : { report_component_baseline: reportBaseline }),
        ...(journalBaseline === undefined ? {} : { journal_adapter_baseline: journalBaseline }),
        bundle_sha256: bundleSha256,
        ...result,
    }));
    if (passed) {
        await rm(profileParent, { recursive: true });
    } else {
        await writeFile(join(profileParent, 'firefox-tail.log'), browserLog, { mode: 0o600 });
        console.log(JSON.stringify({ bounded_browser_log: join(profileParent, 'firefox-tail.log') }));
        process.exitCode = 1;
    }
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
