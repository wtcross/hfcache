#!/usr/bin/env node
/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Bounded mounted-browser baseline investigation; never invokes application
 * commands or authenticates to Cockpit. It owns one loopback server, browser
 * process and fresh temporary profile. No sandbox/security control is disabled.
 *
 * Run from the repository:
 * rtk node docs/agents/plans/support/cockpit-rest-repair/baseline-browser.mjs
 */

import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = new URL('.', import.meta.url);
const cockpit = new URL('../../../../../cockpit/', here);
const require = createRequire(new URL('package.json', cockpit));
const { build } = require('esbuild');
const TIMEOUT_MS = 60000;
const ARTIFACT_BYTES = 8192;
const output = new URL('baseline-browser-evidence.json', here);
const profileParent = await mkdtemp(join(tmpdir(), 'hfcache-cpr-browser-'));
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

const buildResult = await build({
    entryPoints: [fileURLToPath(new URL('baseline-browser.tsx', here))],
    absWorkingDir: fileURLToPath(cockpit),
    bundle: true, write: false, format: 'iife', platform: 'browser',
    define: { 'process.env.NODE_ENV': '"test"' },
    loader: { '.css': 'empty' }, logLevel: 'silent',
    plugins: [{
        name: 'controlled-cockpit-process-boundary',
        setup(builder) {
            builder.onResolve({ filter: /^cockpit$/ }, () => ({ path: 'cockpit', namespace: 'fixture' }));
            builder.onLoad({ filter: /.*/, namespace: 'fixture' }, () => ({
                contents: 'export default { spawn: (...args) => window.cprFixture.spawn(...args) };',
                loader: 'js',
            }));
        },
    }],
});
const bundle = buildResult.outputFiles[0].contents;
if (bundle.byteLength > 16 * 1024 * 1024)
    throw new Error('Investigation bundle exceeds its bound');
const bundleSha256 = createHash('sha256').update(bundle).digest('hex');
let deliver;
const delivered = new Promise(resolve => { deliver = resolve });
const server = createServer((request, response) => {
    if (request.method === 'GET' && request.url === '/') {
        response.setHeader('Content-Type', 'text/html; charset=utf-8');
        response.end('<!doctype html><meta charset="utf-8"><title>Owned CPR baseline fixture</title>' +
            '<div id="maintenance"></div><div id="query-error"></div><script src="/bundle.js"></script>');
    } else if (request.method === 'GET' && request.url === '/bundle.js') {
        response.setHeader('Content-Type', 'application/javascript');
        response.end(bundle);
    } else if (request.method === 'POST' && request.url === '/result') {
        const chunks = [];
        let bytes = 0;
        request.on('data', chunk => {
            bytes += chunk.length;
            if (bytes > ARTIFACT_BYTES) {
                response.writeHead(413).end();
                request.destroy();
                deliver({ state: 'fixture-failed', message: 'Browser result exceeds bound' });
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
                deliver({ state: 'fixture-failed', message: 'Browser result is not JSON' });
            }
        });
    } else {
        response.writeHead(404).end();
    }
});
await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
});
const address = server.address();
if (address === null || typeof address === 'string')
    throw new Error('Investigation listener is not an owned loopback socket');
const browser = spawn('/usr/bin/firefox', [
    '--headless', '--new-instance', '--profile', profile, `http://127.0.0.1:${address.port}/`,
], {
    env: {
        PATH: '/usr/bin:/bin', HOME: process.env.HOME, LANG: 'C.UTF-8',
        XDG_CACHE_HOME: join(profileParent, 'cache'),
        XDG_CONFIG_HOME: join(profileParent, 'config'),
        XDG_DATA_HOME: join(profileParent, 'data'),
    },
    stdio: ['ignore', 'pipe', 'pipe'],
});
let browserLog = '';
for (const stream of [browser.stdout, browser.stderr])
    stream.on('data', chunk => { browserLog = (browserLog + chunk.toString('utf8')).slice(-4096) });
let timeout;
const result = await Promise.race([
    delivered,
    new Promise(resolve => {
        timeout = setTimeout(() => resolve({ state: 'fixture-failed', message: 'Browser result deadline exceeded' }), TIMEOUT_MS);
    }),
    new Promise(resolve => {
        browser.once('error', () => resolve({ state: 'fixture-failed', message: 'Firefox could not start' }));
        browser.once('exit', (code, signal) => resolve({ state: 'fixture-failed', message: 'Firefox exited before reporting', code, signal }));
    }),
]);
clearTimeout(timeout);
const closed = new Promise(resolve => browser.once('close', resolve));
if (browser.exitCode === null && browser.signalCode === null)
    browser.kill('SIGTERM'); // Only this owned synthetic browser; no server execution exists.
await Promise.race([closed, new Promise(resolve => setTimeout(resolve, 5000))]);
if (browser.exitCode === null && browser.signalCode === null)
    browser.kill('SIGKILL');
await new Promise(resolve => server.close(resolve));
const artifact = {
    schema_version: 1,
    fixture: 'CPR-001 actual mounted baseline investigation',
    reviewed_baseline: 'dcc2c562b52304541d0cb85d20fc046072038e79',
    browser: '/usr/bin/firefox',
    bundle_sha256: bundleSha256,
    process_profile_directory: profileParent,
    isolation: { owned_profile: true, loopback_only_fixture: true, cockpit_process_boundary_controlled: true, real_pam: false },
    result,
};
const serialized = JSON.stringify(artifact, null, 2) + '\n';
if (Buffer.byteLength(serialized, 'utf8') > ARTIFACT_BYTES)
    throw new Error('Investigation evidence exceeds its bound');
await writeFile(output, serialized, { mode: 0o600 });
if (result.state !== 'observed') {
    await writeFile(join(profileParent, 'firefox-tail.log'), browserLog, { mode: 0o600 });
    console.log(JSON.stringify({ ...artifact, evidence: fileURLToPath(output), bounded_browser_log: join(profileParent, 'firefox-tail.log') }));
    process.exitCode = 1;
} else {
    console.log(JSON.stringify({ ...artifact, evidence: fileURLToPath(output) }));
}
