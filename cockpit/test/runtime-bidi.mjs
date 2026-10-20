/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Test-only WebDriver BiDi client. It controls one owned Firefox profile;
 * it never patches Cockpit, its promises, transport, bridge or host commands.
 */
import { spawn } from 'node:child_process';
import { lstat, mkdtemp, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export class RuntimeCheckError extends Error {
    /** @param {string} code */
    constructor(code) {
        super(code);
        this.name = 'RuntimeCheckError';
        this.code = code;
    }
}

/** @template T @param {Promise<T>} promise @param {number} milliseconds @param {string} code */
export async function deadline(promise, milliseconds, code) {
    let timer;
    try {
        return await Promise.race([
            promise,
            new Promise((_resolve, reject) => {
                timer = setTimeout(() => reject(new RuntimeCheckError(code)), milliseconds);
            }),
        ]);
    } finally {
        clearTimeout(timer);
    }
}

/** @param {string} [existingProfile] */
export async function startFirefox(existingProfile) {
    const profile = existingProfile ?? await mkdtemp(join(tmpdir(), 'hfcache-cpr008-bidi-'));
    if (existingProfile !== undefined) {
        const info = await lstat(profile);
        if (!profile.startsWith(join(tmpdir(), 'hfcache-cpr008-bidi-')) || await realpath(profile) !== profile ||
            !info.isDirectory() || info.uid !== process.getuid?.() || (info.mode & 0o077) !== 0)
            throw new RuntimeCheckError('unsafe-owned-browser-profile');
    }
    await writeFile(join(profile, 'user.js'), [
        'user_pref("datareporting.policy.dataSubmissionEnabled", false);',
        'user_pref("toolkit.telemetry.enabled", false);',
        'user_pref("app.normandy.enabled", false);',
        'user_pref("network.captive-portal-service.enabled", false);',
        'user_pref("network.connectivity-service.enabled", false);',
        'user_pref("network.prefetch-next", false);',
        'user_pref("browser.safebrowsing.downloads.enabled", false);',
        'user_pref("browser.safebrowsing.malware.enabled", false);',
        'user_pref("browser.safebrowsing.phishing.enabled", false);',
        'user_pref("browser.newtabpage.enabled", false);',
        'user_pref("browser.shell.checkDefaultBrowser", false);',
    ].join('\n'), { mode: 0o600 });
    const browser = spawn('/usr/bin/firefox', [
        '--headless', '--new-instance', '--profile', profile,
        '--remote-debugging-port', '0', 'about:blank',
    ], {
        env: {
            PATH: '/usr/bin:/bin',
            LANG: 'C.UTF-8',
            XDG_CACHE_HOME: join(profile, 'cache'),
            XDG_CONFIG_HOME: join(profile, 'config'),
            XDG_DATA_HOME: join(profile, 'data'),
        },
        stdio: ['ignore', 'ignore', 'pipe'],
    });
    /** @type {WebSocket | undefined} */
    let socket;
    const pending = new Map();
    let sequence = 0;
    let closed = false;
    /** @param {boolean} [preserveProfile] */
    const close = async (preserveProfile = existingProfile !== undefined) => {
        if (closed) return;
        closed = true;
        socket?.close();
        for (const request of pending.values())
            request.reject(new RuntimeCheckError('browser-closed'));
        pending.clear();
        const ended = new Promise(resolve => browser.once('close', resolve));
        if (browser.exitCode === null && browser.signalCode === null)
            browser.kill('SIGTERM'); // Only the owned browser; never an application process.
        await Promise.race([ended, new Promise(resolve => setTimeout(resolve, 3000))]);
        if (browser.exitCode === null && browser.signalCode === null)
            browser.kill('SIGKILL');
        if (!preserveProfile)
            await rm(profile, { recursive: true, force: true });
    };
    try {
        const endpoint = await deadline(new Promise((resolve, reject) => {
            let tail = '';
            browser.once('error', () => reject(new RuntimeCheckError('firefox-start')));
            browser.once('exit', () => reject(new RuntimeCheckError('firefox-exit')));
            browser.stderr.on('data', chunk => {
                tail = (tail + chunk.toString('utf8')).slice(-2048);
                const match = /WebDriver BiDi listening on (ws:\/\/127\.0\.0\.1:\d+)/.exec(tail);
                if (match) resolve(match[1]);
            });
        }), 15000, 'firefox-listen-deadline');
        const connection = new WebSocket(endpoint + '/session');
        socket = connection;
        connection.addEventListener('message', event => {
            // Never print protocol payloads: login requests contain a synthetic password.
            if (typeof event.data !== 'string' || Buffer.byteLength(event.data) > 256 * 1024) {
                for (const request of pending.values())
                    request.reject(new RuntimeCheckError('bidi-message-bound'));
                pending.clear();
                return;
            }
            let response;
            try { response = JSON.parse(event.data) } catch { return }
            const request = pending.get(response.id);
            if (!request) return;
            pending.delete(response.id);
            if (response.type === 'success') request.resolve(response.result);
            else request.reject(new RuntimeCheckError('bidi-command-refused'));
        });
        await deadline(new Promise((resolve, reject) => {
            connection.addEventListener('open', resolve, { once: true });
            connection.addEventListener('error', () => reject(new RuntimeCheckError('bidi-open')), { once: true });
        }), 5000, 'bidi-open-deadline');
        /** @param {string} method @param {object} params @param {number} [milliseconds] */
        const send = async (method, params, milliseconds = 15000) => {
            if (closed || pending.size >= 8)
                throw new RuntimeCheckError('bidi-pending-bound');
            const id = ++sequence;
            try {
                return await deadline(new Promise((resolve, reject) => {
                    pending.set(id, { resolve, reject });
                    connection.send(JSON.stringify({ id, method, params }));
                }), milliseconds, 'bidi-command-deadline');
            } finally {
                pending.delete(id);
            }
        };
        // This disposable owned profile visits only the separately certificate-pinned
        // loopback guest. It does not change host trust or Cockpit transport policy.
        const session = await send('session.new', { capabilities: { alwaysMatch: { acceptInsecureCerts: true } } });
        const created = await send('browsingContext.create', { type: 'tab' });
        /** @param {string} context @param {string} expression */
        const evaluate = async (context, expression) => {
            const result = await send('script.evaluate', {
                // awaitPromise awaits the result of a classic script; an async
                // wrapper is required for expressions containing await.
                expression: '(async () => (' + expression + '))()',
                target: { context },
                awaitPromise: true,
                resultOwnership: 'none',
            }, 30000);
            if (result.type !== 'success' || result.result?.type !== 'string')
                throw new RuntimeCheckError('browser-evaluation-refused');
            try { return JSON.parse(result.result.value) } catch {
                throw new RuntimeCheckError('browser-result-shape');
            }
        };
        return { send, evaluate, context: created.context, capabilities: session.capabilities, profile, close };
    } catch (error) {
        await close(existingProfile !== undefined);
        throw error;
    }
}
