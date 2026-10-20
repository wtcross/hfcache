/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Manual, environment-gated real Cockpit/PAM acceptance (V54).
 * No controlled Cockpit boundary, application replacement or default test hook.
 */
import { createHash, randomUUID } from 'node:crypto';
import { lstat, readFile, realpath, writeFile } from 'node:fs/promises';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { connect } from 'node:tls';
import { build } from 'esbuild';
import { hfcacheArgv } from '../src/lib/command.ts';

import { deadline, RuntimeCheckError, startFirefox } from './runtime-bidi.mjs';

const repository = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const pipeCandidateOnly = process.env.CPR_RUNTIME_BROWSER_MODE === 'fresh-pipe-candidate-only';
const framedCandidateOnly = process.env.CPR_RUNTIME_BROWSER_MODE === 'fresh-candidate-only';
const freshCandidateOnly = pipeCandidateOnly || framedCandidateOnly;
const fixtureRoot = join(repository, pipeCandidateOnly
    ? '.local-fixtures/cpr-runtime/cpr008-pipe'
    : framedCandidateOnly ? '.local-fixtures/cpr-runtime/cpr008-framed' : '.local-fixtures/cpr-runtime/cpr008-fixed');
const cockpitUrl = pipeCandidateOnly ? 'https://127.0.0.1:19058' : framedCandidateOnly ? 'https://127.0.0.1:19057' : 'https://127.0.0.1:19056';
const cockpitPort = pipeCandidateOnly ? 19058 : framedCandidateOnly ? 19057 : 19056;
const guestHostname = pipeCandidateOnly ? 'cpr-pipe.local' : framedCandidateOnly ? 'cpr-framed.local' : 'cpr-current.local';
const fixtureIdentity = pipeCandidateOnly
    ? /^cpr008-pipe-[0-9a-f]{32}$/
    : framedCandidateOnly ? /^cpr008-framed-[0-9a-f]{32}$/ : /^cpr008-[0-9a-f]{32}$/;
const SOURCE = '41d818e13c1f4860a286f24ba91bd0f384b09172';
/** @type {Record<string, unknown>[]} */
const checks = [];
/** @type {Record<string, unknown>} */
let publicIdentity = {};
let fixtureVerified = false;

/** @param {boolean} condition @param {string} code */
function requireCheck(condition, code) {
    if (!condition) throw new RuntimeCheckError(code);
}

/** @param {string} path @param {number} maximum */
async function privateFile(path, maximum) {
    requireCheck(path.startsWith(fixtureRoot + '/') && await realpath(path) === path, 'unsafe-fixture-path');
    const info = await lstat(path);
    requireCheck(info.isFile() && info.uid === process.getuid?.() && info.nlink === 1 &&
        (info.mode & 0o077) === 0 && info.size > 0 && info.size <= maximum, 'unsafe-fixture-file');
    return await readFile(path, 'utf8');
}

async function manifest() {
    const path = process.env.CPR_RUNTIME_BROWSER_MANIFEST;
    requireCheck(typeof path === 'string' && path === join(fixtureRoot, 'browser-manifest.json'), 'fixture-not-provisioned');
    const info = await lstat(fixtureRoot);
    requireCheck(info.isDirectory() && info.uid === process.getuid?.() && (info.mode & 0o077) === 0 &&
        await realpath(fixtureRoot) === fixtureRoot, 'unsafe-fixture-directory');
    const data = JSON.parse(await privateFile(String(path), 16384));
    const fields = ['schema_version', 'fixture_id', 'source_commit', 'cockpit_url', 'tls_sha256',
        'username', 'password_file', 'guest_hostname', 'bundle_sha256', 'image', 'artifact_index_sha256',
        'source_dirty', 'helper_sha256', 'patch_sha256', 'closure_sha256'];
    requireCheck(data !== null && typeof data === 'object' && !Array.isArray(data) &&
        Object.keys(data).length === fields.length && fields.every(field => Object.prototype.hasOwnProperty.call(data, field)), 'fixture-manifest-shape');
    requireCheck(data.schema_version === 1 && fixtureIdentity.test(data.fixture_id) &&
        data.source_commit === SOURCE && data.source_dirty === true && data.cockpit_url === cockpitUrl &&
        data.username === 'cprtester' && data.guest_hostname === guestHostname &&
        data.password_file === join(fixtureRoot, 'keys/cprtester.password') &&
        /^[0-9a-f]{64}$/.test(data.tls_sha256) && /^[0-9a-f]{64}$/.test(data.bundle_sha256) &&
        /^sha256:[0-9a-f]{64}$/.test(data.image) &&
        ['artifact_index_sha256', 'helper_sha256', 'patch_sha256', 'closure_sha256'].every(field => /^[0-9a-f]{64}$/.test(data[field])), 'fixture-manifest-identity');
    return data;
}

/** @param {string} expected */
async function pinCertificate(expected) {
    const socket = connect({ host: '127.0.0.1', port: cockpitPort, rejectUnauthorized: false });
    try {
        await deadline(new Promise((resolve, reject) => {
            socket.once('secureConnect', resolve);
            socket.once('error', () => reject(new RuntimeCheckError('fixture-tls-connect')));
        }), 5000, 'fixture-tls-deadline');
        const cert = socket.getPeerCertificate();
        requireCheck(Buffer.isBuffer(cert.raw) && createHash('sha256').update(cert.raw)
                .digest('hex') === expected,
                     'fixture-certificate-mismatch');
    } finally {
        socket.destroy();
    }
}

/** @param {Awaited<ReturnType<typeof startFirefox>>} browser @param {string} context @param {string} query @param {string} code @param {number} [milliseconds] */
async function until(browser, context, query, code, milliseconds = 90000) {
    const end = Date.now() + milliseconds;
    while (Date.now() < end) {
        if (await browser.evaluate(context, 'JSON.stringify(Boolean(' + query + '))')) return;
        await new Promise(resolve => setTimeout(resolve, 200));
    }
    throw new RuntimeCheckError(code);
}

/** @param {Awaited<ReturnType<typeof startFirefox>>} browser @param {string} context @param {string} label */
async function click(browser, context, label) {
    const result = await browser.evaluate(context, `JSON.stringify((() => {
        const control = [...document.querySelectorAll('button')].find(item => item.textContent.trim() === ${JSON.stringify(label)});
        if (!control || control.matches(':disabled') || !control.getClientRects().length) return false;
        control.click(); return true;
    })())`);
    requireCheck(result === true, 'ui-action-unavailable');
}

/** @param {Awaited<ReturnType<typeof startFirefox>>} browser @param {string} context @param {string} password */
export async function authenticate(browser, context, password) {
    return await browser.evaluate(context, `JSON.stringify(await new Promise(resolve => {
        const bus = window.cockpit.dbus(null, {bus:'internal'});
        const proxy = bus.proxy('cockpit.Superuser', '/superuser');
        let prompts = 0;
        let settled = false;
        let started = false;
        let timer;
        const prompt = () => { prompts++; if (prompts === 1) proxy.Answer(${JSON.stringify(password)}).catch(()=>finish(false,'answer-refused')); };
        const finish = (ok,phase) => {
            if(settled) return;
            settled=true; clearTimeout(timer);
            proxy.removeEventListener('Prompt',prompt); proxy.removeEventListener('changed',changed);
            resolve({ok,prompts,phase,current:['none','init','sudo','pkexec','root'].includes(proxy.Current)?proxy.Current:'other'});
        };
        const changed = () => {if(started && proxy.valid && typeof proxy.Current==='string' && proxy.Current!=='none' && proxy.Current!=='init')finish(true,'current-confirmed');};
        proxy.wait(() => {
            if (!proxy.valid) { finish(false,'proxy-unavailable'); return; }
            if (typeof proxy.Current==='string' && proxy.Current !== 'none' && proxy.Current !== 'init') { finish(true,'already-administrative'); return; }
            const method = Object.keys(proxy.Methods || {})[0] || (proxy.Bridges||[])[0];
            if (!method) { finish(false,'no-method'); return; }
            proxy.addEventListener('Prompt', prompt);
            proxy.addEventListener('changed',changed);
            timer=setTimeout(()=>finish(false,'current-notification-deadline'),15000);
            proxy.Start(method).then(() => {started=true;changed();}, () => finish(false,'start-rejected'));
        });
    }))`);
}

/** @param {string} name @param {string} fixtureId @param {string|null} [nonce] */
async function handshake(name, fixtureId, nonce = null) {
    const end = Date.now() + 120000;
    const path = join(fixtureRoot, 'evidence', name);
    while (Date.now() < end) {
        try {
            const value = JSON.parse(await privateFile(path, 4096));
            requireCheck(value.fixture_id === fixtureId && value.source_commit === SOURCE && value.state === 'ready' &&
                (nonce === null || value.nonce === nonce), 'lock-handshake-identity');
            return value;
        } catch (error) {
            if (error instanceof RuntimeCheckError || !(error instanceof Error) || !('code' in error) || error.code !== 'ENOENT') throw error;
        }
        await new Promise(resolve => setTimeout(resolve, 250));
    }
    throw new RuntimeCheckError('lock-handshake-deadline');
}

/** @param {Awaited<ReturnType<typeof startFirefox>>} browser @param {string} context */
async function originalSnapshot(browser, context) {
    return await browser.evaluate(context, `JSON.stringify((() => {
        const record=JSON.parse(sessionStorage.getItem('hfcache.operations.v1')).records.find(item=>item.action==='prune-dry-run');
        return {key:record.key,operation_id:record.operationId,scope:record.scope,state:record.state,terminal:record.terminal};
    })())`);
}

/** @param {*} current @param {*} prepared @param {*} original */
function assertOriginal(current, prepared, original) {
    requireCheck(current.key === prepared.key && current.operation_id === original.operation_id && current.state === 'terminal' &&
        Object.keys(prepared.scope).every(key => current.scope[key] === prepared.scope[key]) &&
        current.terminal?.command === 'prune --dry-run' && current.terminal?.runId === original.run_id &&
        current.terminal?.exitCode === original.exit_code && current.terminal?.outcome === original.outcome &&
        current.terminal?.code === original.terminal_code, 'original-observation-identity-changed');
}

/** Actual strict observation code, bundled only into this test expression.
 * It calls the real Cockpit bridge and fixed launcher; no page/module/storage
 * state is replaced and no submission command is accepted by this helper.
 * @param {Awaited<ReturnType<typeof startFirefox>>} browser @param {string} context
 * @param {*} prepared @param {*} expected @param {string} runner
 */
export async function nativeOriginalReads(browser, context, prepared, expected, runner) {
    /** @param {'lookup'|'wait'} mode @param {string} handle */
    const invoke = async (mode, handle) => {
        requireCheck(mode === 'lookup' || mode === 'wait', 'readonly-original-mode');
        const argv = hfcacheArgv(['operations', mode, '--', handle], {
            expectedClientScope: prepared.scope.authorityFingerprint,
        });
        return await browser.evaluate(context, `JSON.stringify(await (async () => {
            ${runner}
            const envelope=await cprReadRunner.runSpawned(${JSON.stringify(argv)},
                argv=>window.cockpit.spawn(argv,{superuser:'require',err:'out'}),
                {stage:${JSON.stringify('operation-' + mode)}});
            const sort=value=>Array.isArray(value)?value.map(sort):value!==null&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,sort(value[key])])):value;
            const bytes=new TextEncoder().encode(JSON.stringify(sort(envelope),null,2)+'\\n');
            const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
            const operation=envelope.data?.operation;
            return {command:envelope.command,run_id:envelope.run_id,exit_code:envelope.exit_code,outcome:envelope.outcome,
                warning_codes:envelope.warnings.map(issue=>issue.code),error_codes:envelope.errors.map(issue=>issue.code),
                result_sha256:digest,empty_prune:envelope.data&&Object.keys(envelope.data).sort().join(',')==='applied,plans'&&Array.isArray(envelope.data.plans)&&envelope.data.plans.length===0&&Array.isArray(envelope.data.applied)&&envelope.data.applied.length===0,
                operation:operation?{operation_id:operation.operation_id,principal:operation.principal,route:operation.route,archive_id:operation.archive_id,state:operation.state,domain_run_id:operation.domain_run_id,result_recorded:operation.result_recorded}:null};
        })())`);
    };
    const lookup = await invoke('lookup', prepared.key);
    requireCheck(lookup.command === 'operations lookup' && lookup.exit_code === 0 && lookup.error_codes.length === 0 &&
        lookup.operation?.operation_id === expected.operation_id && lookup.operation.principal === prepared.scope.credentialClass &&
        lookup.operation.route === '/api/v1/prune-plans' && lookup.operation.archive_id === prepared.scope.archiveId &&
        lookup.operation.state === expected.receipt_state && lookup.operation.domain_run_id === expected.run_id &&
        lookup.operation.result_recorded === true, 'native-original-lookup-mismatch');
    checks.push({
        name: 'fresh native fixed-launcher authenticated original lookup',
        passed: true,
        key: prepared.key,
        operation_id: lookup.operation.operation_id,
        scope_pin: prepared.scope.authorityFingerprint
    });
    const observed = await invoke('wait', lookup.operation.operation_id);
    requireCheck(observed.command === expected.command && observed.run_id === expected.run_id && observed.exit_code === expected.exit_code &&
        observed.outcome === expected.outcome && JSON.stringify(observed.warning_codes) === JSON.stringify(expected.warning_codes) &&
        JSON.stringify(observed.error_codes) === JSON.stringify(expected.error_codes) && observed.result_sha256 === expected.result_sha256 &&
        observed.empty_prune === true, 'native-original-wait-mismatch');
    checks.push({
        name: 'fresh native fixed-launcher observation of exact original durable result',
        passed: true,
        key: prepared.key,
        operation_id: lookup.operation.operation_id,
        run_id: observed.run_id,
        exit_code: observed.exit_code,
        outcome: observed.outcome,
        result_sha256: observed.result_sha256,
        job_replayed: false
    });
    return Object.freeze({
        key: prepared.key,
        operation_id: lookup.operation.operation_id,
        run_id: observed.run_id,
        exit_code: observed.exit_code,
        outcome: observed.outcome,
        result_sha256: observed.result_sha256,
        scope_pin: prepared.scope.authorityFingerprint,
        job_replayed: false
    });
}

async function main() {
    requireCheck(process.env.CPR_RUNTIME_BROWSER_MODE === undefined || freshCandidateOnly, 'unsupported-runtime-mode');
    requireCheck(!freshCandidateOnly || (process.env.CPR_RUNTIME_BROWSER_CONTINUE_ORIGINAL === undefined &&
        process.env.CPR_RUNTIME_BROWSER_RESUME_KNOWN_PREWRITE === undefined && process.env.CPR_RUNTIME_BROWSER_INTERRUPTION === '1'), 'fresh-mode-refuses-legacy-continuation');
    const freshNonce = freshCandidateOnly ? randomUUID() : null;
    const continuation = process.env.CPR_RUNTIME_BROWSER_CONTINUE_ORIGINAL === '1';
    const knownPrewrite = process.env.CPR_RUNTIME_BROWSER_RESUME_KNOWN_PREWRITE === '1';
    const knownPrewriteNonce = knownPrewrite ? randomUUID() : null;
    requireCheck(!knownPrewrite || continuation, 'known-prewrite-requires-original-only');
    const identity = await manifest();
    /** @type {*} */
    let initialState = null;
    let pinnedConfigLock = null;
    if (freshCandidateOnly) {
        initialState = JSON.parse(await privateFile(join(fixtureRoot, 'evidence/browser-initial-state.json'), 4096));
        const fields = ['fixture_id', 'source_commit', 'state', 'artifact_index_sha256', 'archive_id', 'installed_sha256', 'installed_inode', 'installed_device', 'candidate', 'backup', 'configuration_lock'];
        requireCheck(initialState !== null && typeof initialState === 'object' && !Array.isArray(initialState) &&
            Object.keys(initialState).length === fields.length && fields.every(field => Object.prototype.hasOwnProperty.call(initialState, field)) &&
            initialState.fixture_id === identity.fixture_id && initialState.source_commit === SOURCE && initialState.state === 'ready' &&
            initialState.artifact_index_sha256 === identity.artifact_index_sha256 &&
            /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(initialState.archive_id) &&
            /^[0-9a-f]{64}$/.test(initialState.installed_sha256) && Number.isSafeInteger(initialState.installed_inode) && initialState.installed_inode > 0 &&
            Number.isSafeInteger(initialState.installed_device) && initialState.installed_device > 0 &&
            initialState.candidate === 'absent' && initialState.backup === 'absent' && initialState.configuration_lock === 'absent', 'fresh-initial-state-not-proven');
        for (const name of ['browser-submission-barrier.json', 'browser-original-operation.json', 'browser-candidate-phase-barrier.json',
            'browser-candidate-validate-sent.json', 'browser-install-sent.json', 'browser-interrupted-write-sent.json']) {
            try {
                await lstat(join(fixtureRoot, 'evidence', name));
                throw new RuntimeCheckError('fresh-fixture-already-attempted-preserve-state');
            } catch (error) {
                if (!(error instanceof Error) || !('code' in error) || error.code !== 'ENOENT') throw error;
            }
        }
    }
    let retained = null;
    let expected = null;
    let runner = '';
    if (continuation) {
        const barrier = JSON.parse(await privateFile(join(fixtureRoot, 'evidence/browser-submission-barrier.json'), 4096));
        retained = JSON.parse(await privateFile(join(fixtureRoot, 'evidence/browser-original-operation.json'), 4096));
        expected = JSON.parse(await privateFile(join(fixtureRoot, 'evidence/original-terminal-projection.json'), 4096));
        if (knownPrewrite) {
            try {
                await lstat(join(fixtureRoot, 'evidence/browser-candidate-validate-sent.json'));
                throw new RuntimeCheckError('candidate-validation-already-sent-preserve-state');
            } catch (error) {
                if (!(error instanceof Error) || !('code' in error) || error.code !== 'ENOENT') throw error;
            }
            const prior = JSON.parse(await privateFile(join(fixtureRoot, 'evidence/browser-candidate-phase-barrier.json'), 4096));
            const refusal = JSON.parse(await readFile(join(repository, 'docs/agents/plans/support/cockpit-rest-repair/gates/cpr-008-browser-known-prewrite-refused.json'), 'utf8'));
            requireCheck(prior.fixture_id === identity.fixture_id && prior.source_commit === SOURCE && prior.state === 'candidate-only-phase-starting' &&
                refusal.fixture_id === identity.fixture_id && refusal.code === 'candidate-base-read-mismatch' &&
                !refusal.checks.some((/** @type {{name:string}} */ check) => check.name === 'actual guarded candidate write and fixed-launcher API validation'), 'known-prewrite-refusal-not-proven');
        }
        requireCheck(barrier.fixture_id === identity.fixture_id && barrier.source_commit === SOURCE &&
            barrier.state === 'one-deliberate-submission-starting' && retained.operation_id === null &&
            retained.key === expected.key && /^[A-Za-z0-9._~+-]{1,128}$/.test(retained.key) &&
            retained.scope?.host === 'localhost' && retained.scope.endpoint === 'unix:/run/hfcache/api/api.sock' &&
            retained.scope.credentialClass === 'rest-writer' && retained.scope.archiveId === expected.archive_id &&
            /^[0-9a-f]{64}$/.test(retained.scope.profile) && /^[0-9a-f]{64}$/.test(retained.scope.authorityFingerprint) &&
            /^[0-9a-f]{32}$/.test(retained.scope.instanceId) && /^[0-9a-f]{32}$/.test(expected.operation_id) &&
            /^[0-9a-f]{32}$/.test(expected.run_id) && /^[0-9a-f]{64}$/.test(expected.result_sha256) &&
            expected.command === 'prune --dry-run' && expected.principal === 'rest-writer' && expected.receipt_state === 'succeeded' &&
            expected.outcome === 'success' && expected.exit_code === 0 && expected.warning_codes.length === 0 && expected.error_codes.length === 0,
                     'original-continuation-precondition');
        const bundled = await build({
            entryPoints: [join(repository, 'cockpit/src/lib/runner.ts')],
            bundle: true,
            format: 'iife',
            globalName: 'cprReadRunner',
            platform: 'browser',
            write: false,
            logLevel: 'silent'
        });
        runner = bundled.outputFiles[0].text;
        requireCheck(Buffer.byteLength(runner) <= 131072, 'actual-runner-test-bundle-bound');
    }
    await pinCertificate(identity.tls_sha256);
    publicIdentity = {
        fixture_id: identity.fixture_id,
        source_commit: SOURCE,
        source_dirty: true,
        helper_sha256: identity.helper_sha256,
        patch_sha256: identity.patch_sha256,
        closure_sha256: identity.closure_sha256,
        bundle_sha256: identity.bundle_sha256,
        artifact_index_sha256: identity.artifact_index_sha256,
        image: identity.image
    };
    let password = (await privateFile(identity.password_file, 512)).replace(/\r?\n$/, '');
    requireCheck(password.length >= 16 && !/[\r\n\0]/.test(password), 'fixture-password-shape');
    const browser = await startFirefox();
    let succeeded = false;
    try {
        await browser.send('browsingContext.navigate', { context: browser.context, url: identity.cockpit_url + '/', wait: 'complete' });
        await until(browser, browser.context, "document.querySelector('#login-user-input')?.getClientRects().length && document.querySelector('#login-password-input')?.getClientRects().length && document.querySelector('#login-button')?.matches(':disabled') === false", 'pam-login-form');
        requireCheck(await browser.evaluate(browser.context, `JSON.stringify((() => {
            document.querySelector('#login-user-input').value = ${JSON.stringify(identity.username)};
            document.querySelector('#login-password-input').value = ${JSON.stringify(password)};
            document.querySelector('#login-button').click(); return true;
        })())`) === true, 'pam-login-submit');
        await until(browser, browser.context, "!document.querySelector('#login-password-input') || document.querySelector('#login-password-input').getClientRects().length === 0", 'pam-login-refused');
        checks.push({ name: 'real Cockpit PAM login', passed: true });
        await browser.send('browsingContext.navigate', {
            context: browser.context, url: identity.cockpit_url + '/cockpit/@localhost/hfcache/index.html', wait: 'complete',
        });
        await until(browser, browser.context, "window.cockpit && document.querySelector('#app')", 'installed-plugin-load');
        const fixture = await browser.evaluate(browser.context, `JSON.stringify(await new Promise(resolve => {
            window.cockpit.spawn(['/usr/bin/cat', '/etc/cpr-runtime-identity.json'], {err:'ignore'})
                .then(output => { try { resolve(JSON.parse(output)) } catch { resolve(null) } }, () => resolve(null));
        }))`);
        requireCheck(fixture?.fixture_id === identity.fixture_id && fixture?.source_commit === SOURCE,
                     'guest-marker-mismatch');
        fixtureVerified = true;
        checks.push({ name: 'real unprivileged Cockpit bridge and guest identity', passed: true });
        const bundle = await browser.evaluate(browser.context, `JSON.stringify(await (async () => {
            const response = await fetch('index.js');
            if (!response.ok) return null;
            const bytes = await response.arrayBuffer();
            if (bytes.byteLength > 16 * 1024 * 1024) return null;
            return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v => v.toString(16).padStart(2,'0')).join('');
        })())`);
        requireCheck(bundle === identity.bundle_sha256, 'served-bundle-mismatch');
        const privilege = await authenticate(browser, browser.context, password);
        password = '';
        checks.push({ name: 'real Cockpit administrative bridge authentication', ...privilege, passed: privilege?.ok === true });
        requireCheck(privilege?.ok === true && privilege.current !== 'none' && privilege.prompts <= 3, 'real-superuser-refused');
        const helper = await browser.evaluate(browser.context, `JSON.stringify(await new Promise(resolve => {
            window.cockpit.spawn(['/usr/bin/sha256sum','/usr/local/libexec/hfcache-container-service'],{superuser:'require',err:'ignore'})
                .then(output=>resolve(/^[0-9a-f]{64}  \\/usr\\/local\\/libexec\\/hfcache-container-service\\n$/.test(output)?output.slice(0,64):null),()=>resolve(null));
        }))`);
        requireCheck(helper === identity.helper_sha256, 'physical-helper-mismatch');
        const profile = await browser.evaluate(browser.context, `JSON.stringify(await new Promise(resolve => {
            window.cockpit.spawn(['/usr/local/libexec/hfcache-container-service','inspect-cockpit'], {superuser:'require',err:'ignore'})
                .then(output => {try {resolve(JSON.parse(output))} catch {resolve(null)}}, () => resolve(null));
        }))`);
        requireCheck(profile?.state === 'guarded' && profile.source_commit === SOURCE &&
            profile.image === identity.image && profile.index_sha256 === identity.artifact_index_sha256 &&
            profile.facts?.guard === 'held' && profile.facts?.archive_mount === 'nfs-ro' &&
            profile.permissions?.control === true && profile.permissions?.configuration === true &&
            ['archive', 'hub', 'schedule', 'observer'].every(key => profile.permissions[key] === false), 'guarded-profile-mismatch');
        checks.push({ name: 'real protected guarded profile identity and narrow explicit permissions', passed: true });
        await until(browser, browser.context,
                    "document.body.textContent.includes('Credential class: rest-writer') && !document.body.textContent.includes('Administrative access is required for client and host actions')",
                    'fixed-client-authority-unavailable');
        if (freshCandidateOnly) await until(browser, browser.context, `document.body.textContent.includes(${JSON.stringify(initialState.archive_id)})`, 'fresh-client-archive-mismatch');
        checks.push({ name: 'actual fixed systemd/rootless client authenticated authority', passed: true });
        let prepared;
        let original;
        let restoredPresentation = '';
        if (freshCandidateOnly) {
            requireCheck(await browser.evaluate(browser.context, "JSON.stringify(!sessionStorage.getItem('hfcache.operations.v1') || JSON.parse(sessionStorage.getItem('hfcache.operations.v1')).records.length === 0)") === true, 'fresh-mode-has-no-operation-state');
            checks.push({ name: 'fresh fixture candidate-only mode; no job or old operation import', passed: true, operation_submission_executed: false });
        } else if (continuation) {
            prepared = retained;
            original = { ...expected, terminal_code: null };
            requireCheck(await browser.evaluate(browser.context, "JSON.stringify(!sessionStorage.getItem('hfcache.operations.v1') || JSON.parse(sessionStorage.getItem('hfcache.operations.v1')).records.length === 0)") === true, 'unexpected-retained-browser-registry');
            await nativeOriginalReads(browser, browser.context, prepared, expected, runner);
            checks.push({ name: 'private original-handle recovery in a fresh native browser tab; no browser storage reconstruction', passed: true, job_submission_path_executed: false });
        } else {
            await click(browser, browser.context, 'Maintenance');
            await until(browser, browser.context, "[...document.querySelectorAll('button')].some(item => item.textContent.trim() === 'Dry run' && !item.matches(':disabled'))", 'guarded-control-unavailable');
            // Never retry the whole harness after an uncertain submission. Retain
            // the barrier and original handles for a separate operator decision.
            await writeFile(join(fixtureRoot, 'evidence/browser-submission-barrier.json'), JSON.stringify({
                fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'one-deliberate-submission-starting',
            }), { mode: 0o600, flag: 'wx' });
            await click(browser, browser.context, 'Dry run');
            await until(browser, browser.context, "JSON.parse(sessionStorage.getItem('hfcache.operations.v1') || '{\"records\":[]}').records.some(item=>item.action==='prune-dry-run')", 'original-presend-key-unavailable');
            prepared = await browser.evaluate(browser.context, `JSON.stringify((() => {
            const record=JSON.parse(sessionStorage.getItem('hfcache.operations.v1')).records.find(item=>item.action==='prune-dry-run');
            return {key:record.key,operation_id:record.operationId,scope:{host:record.scope.host,profile:record.scope.profile,endpoint:record.scope.endpoint,credentialClass:record.scope.credentialClass,archiveId:record.scope.archiveId,instanceId:record.scope.instanceId,authorityFingerprint:record.scope.authorityFingerprint}};
        })())`);
            requireCheck(/^[A-Za-z0-9._~+-]{1,128}$/.test(prepared.key) &&
            /^[0-9a-f]{64}$/.test(prepared.scope?.authorityFingerprint), 'original-presend-key-invalid');
            await writeFile(join(fixtureRoot, 'evidence/browser-original-operation.json'), JSON.stringify(prepared), { mode: 0o600, flag: 'wx' });
            await until(browser, browser.context, "document.querySelector('[aria-label=\"Original prune-dry-run\"]')?.textContent.includes('prune-dry-run: terminal')", 'real-original-terminal');
            original = await browser.evaluate(browser.context, `JSON.stringify((() => {
            const section = document.querySelector('[aria-label="Original prune-dry-run"]');
            const text = section.textContent;
            const key=[...section.querySelectorAll('p')].find(item=>item.textContent.includes('Original key: '))?.querySelector('code')?.textContent;
            const terminal=JSON.parse(sessionStorage.getItem('hfcache.operations.v1')).records.find(item=>item.key===key)?.terminal;
            return {key,operation_id:/Original operation: ([0-9a-f]{32})/.exec(text)?.[1],codes:[...new Set(text.match(/HF[A-Z]{2,4}[0-9]{3}/g) || [])],exit_code:terminal?.exitCode,outcome:terminal?.outcome,run_id:terminal?.runId,terminal_code:terminal?.code};
        })())`);
            requireCheck(/^[A-Za-z0-9._~+-]{1,128}$/.test(original?.key) && /^[0-9a-f]{32}$/.test(original?.operation_id) &&
            [0, 10, 20, 30, 40, 50].includes(original.exit_code) &&
            /^[0-9a-f]{32}$/.test(original.run_id) && original.key === prepared.key &&
            (original.exit_code === 0
                ? original.outcome === 'success' && original.terminal_code === null && original.codes.length === 0
                : original.codes.includes(original.terminal_code)), 'original-terminal-domain-identity');
            if (original.exit_code === 0)
                await until(browser, browser.context, "(() => {const section=document.querySelector('[aria-label=\"Original prune-dry-run\"]');return section && !section.querySelector('.pf-v6-c-alert') && ['plans','applied'].every(name=>[...section.querySelectorAll('dt')].some(item=>item.textContent.trim()===name&&item.nextElementSibling?.textContent.trim()==='0 entries'));})()", 'original-empty-prune-result');
            await click(browser, browser.context, 'Look up original key');
            // Prior terminal metadata survives failed observations. Require the
            // CURRENT successful lookup's unique `operation` payload presentation.
            await until(browser, browser.context, "(() => {const section=document.querySelector('[aria-label=\"Original prune-dry-run\"]');return section && [...section.querySelectorAll('dt')].some(item=>item.textContent.trim()==='operation') && !section.querySelector('.pf-v6-c-alert') && [...section.querySelectorAll('button')].some(item=>item.textContent.trim()==='Observe original operation'&&!item.matches(':disabled'));})()", 'original-authenticated-lookup');
            assertOriginal(await originalSnapshot(browser, browser.context), prepared, original);
            checks.push({ name: 'fresh successful authenticated lookup of the original key', passed: true, key: prepared.key, operation_id: original.operation_id });
            await click(browser, browser.context, 'Observe original operation');
            // A failed transport leaves lookup data visible. Require its replacement
            // by the original empty success payload or exact failed-domain Alert.
            restoredPresentation = original.exit_code === 0
                ? "!section.querySelector('.pf-v6-c-alert') && ['plans','applied'].every(name=>[...section.querySelectorAll('dt')].some(item=>item.textContent.trim()===name&&item.nextElementSibling?.textContent.trim()==='0 entries'))"
                : `[...section.querySelectorAll('.pf-v6-c-alert')].some(item=>item.textContent.includes(${JSON.stringify(original.terminal_code)}))`;
            await until(browser, browser.context, `(() => {const section=document.querySelector('[aria-label="Original prune-dry-run"]');return section && ![...section.querySelectorAll('dt')].some(item=>item.textContent.trim()==='operation') && (${restoredPresentation}) && [...section.querySelectorAll('button')].some(item=>item.textContent.trim()==='Observe original operation'&&!item.matches(':disabled'));})()`, 'original-authenticated-wait');
            assertOriginal(await originalSnapshot(browser, browser.context), prepared, original);
            checks.push({
                name: 'one deliberate guarded dry run and authenticated original lookup/wait',
                passed: true,
                ...original,
                classification: original.exit_code === 0 ? 'successful lock-free dry run on an empty fixture; no archive workload' : 'failed domain result; no workload success claimed'
            });
        }
        await click(browser, browser.context, 'Configuration');
        await until(browser, browser.context, "[...document.querySelectorAll('button')].some(item => item.textContent.trim() === 'Text (verbatim)' && !item.matches(':disabled'))", 'installed-config-read');
        let originalBaseSha = null;
        if (freshCandidateOnly) {
            await writeFile(join(fixtureRoot, 'evidence/browser-fresh-before-awaiting.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'fresh-installed-read-awaiting-proof', nonce: freshNonce, installed_sha256: initialState.installed_sha256 }), { mode: 0o600, flag: 'wx' });
            const before = await handshake('browser-fresh-before-proof.json', identity.fixture_id, freshNonce);
            requireCheck(before.installed_sha256 === initialState.installed_sha256 && before.installed_inode === initialState.installed_inode &&
                before.installed_device === initialState.installed_device && before.installed_unchanged === true && before.candidate === 'absent' && before.backup === 'absent' &&
                before.original_lock_unchanged === true && Number.isSafeInteger(before.lock_device) && Number.isSafeInteger(before.lock_inode) &&
                before.lock_uid === 0 && before.lock_mode === '0600', 'fresh-original-state-not-proven');
            pinnedConfigLock = { device: before.lock_device, inode: before.lock_inode };
            originalBaseSha = before.installed_sha256;
            checks.push({ name: 'fresh independent initial base and newly pinned original lock proof', passed: true, installed_sha256: before.installed_sha256, lock_device: before.lock_device, lock_inode: before.lock_inode });
        } else if (continuation) {
            if (!knownPrewrite) await writeFile(join(fixtureRoot, 'evidence/browser-before-candidate-awaiting.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'installed-read-complete-awaiting-proof' }), { mode: 0o600, flag: 'wx' });
            if (knownPrewrite) await writeFile(join(fixtureRoot, 'evidence/browser-known-prewrite-awaiting.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'known-prewrite-awaiting-fresh-proof', nonce: knownPrewriteNonce }), { mode: 0o600, flag: 'wx' });
            const before = await handshake(knownPrewrite ? 'browser-known-prewrite-proof.json' : 'browser-before-candidate-proof.json', identity.fixture_id, knownPrewriteNonce);
            requireCheck(before.installed_sha256 === '69d9bf35381c62531829b0679bc6c56d6e04fa6e52eb592b41f5fc764b525df3' &&
                before.installed_unchanged === true && before.candidate === 'absent' && before.backup === 'absent' &&
                before.original_lock_unchanged === true && (!knownPrewrite || before.zero_candidate_write_effects === true), 'candidate-only-original-state-not-proven');
            originalBaseSha = before.installed_sha256;
            checks.push({ name: 'fresh independent read-only original installed base and absent candidate/backup proof', passed: true, installed_sha256: before.installed_sha256 });
        }
        // A second candidate-phase run is never an automatic recovery/replay.
        await writeFile(join(fixtureRoot, knownPrewrite ? 'evidence/browser-candidate-write-attempt-barrier.json' : 'evidence/browser-candidate-phase-barrier.json'), JSON.stringify({ fixture_id:identity.fixture_id, source_commit:SOURCE, state:'candidate-only-phase-starting', ...(freshCandidateOnly ? { nonce: freshNonce } : {}) }), { mode:0o600, flag:'wx' });
        await click(browser, browser.context, 'Text (verbatim)');
        const captured = await browser.evaluate(browser.context, `JSON.stringify(await (async () => {
            const input = document.querySelector('#config-text');
            if (!input || input.matches(':disabled')) return null;
            const baseBytes = new TextEncoder().encode(input.value);
            const base_sha256 = [...new Uint8Array(await crypto.subtle.digest('SHA-256', baseBytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
            const text = input.value + '\\n# CPR008 disposable browser candidate\\n';
            Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(input, text);
            input.dispatchEvent(new Event('input', {bubbles:true}));
            const bytes = new TextEncoder().encode(text);
            return {bytes:bytes.length, base_sha256, sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v=>v.toString(16).padStart(2,'0')).join('')};
        })())`);
        requireCheck(captured !== null && captured.bytes > 0 && captured.bytes <= 1024 * 1024, 'candidate-capture');
        // Form->Text is a proposed canonical draft, not the installed byte view.
        // The independent guarded proof binds the original installed base.
        await writeFile(join(fixtureRoot, 'evidence/browser-candidate-validate-sent.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'deliberate-candidate-validation-starting', candidate_sha256: captured.sha256, ...(freshCandidateOnly ? { nonce: freshNonce } : {}) }), { mode: 0o600, flag: 'wx' });
        await click(browser, browser.context, 'Validate candidate');
        await until(browser, browser.context,
                    "[...document.querySelectorAll('button')].some(item => item.textContent.trim() === 'Install validated candidate' && !item.matches(':disabled'))",
                    'real-candidate-validation');
        checks.push({
            name: 'actual guarded candidate write and fixed-launcher API validation',
            passed: true,
            candidate_bytes: captured.bytes,
            candidate_sha256: captured.sha256,
            proposed_text_differs_from_installed: originalBaseSha !== null && captured.base_sha256 !== originalBaseSha,
            installed: false
        });
        await writeFile(join(fixtureRoot, 'evidence/browser-candidate-ready.json'), JSON.stringify({ fixture_id:identity.fixture_id, source_commit:SOURCE, state:'candidate-ready', candidate_sha256:captured.sha256, candidate_bytes:captured.bytes, ...(freshCandidateOnly ? { nonce: freshNonce } : {}) }), { mode:0o600, flag:'wx' });
        const candidateProof = await handshake('browser-candidate-proof.json', identity.fixture_id, freshNonce);
        if (freshCandidateOnly) {
            requireCheck(candidateProof.candidate_sha256 === captured.sha256 && candidateProof.candidate_bytes === captured.bytes &&
                candidateProof.installed_sha256 === originalBaseSha && candidateProof.original_lock_unchanged === true &&
                candidateProof.lock_device === pinnedConfigLock?.device && candidateProof.lock_inode === pinnedConfigLock?.inode, 'fresh-candidate-proof-mismatch');
            await writeFile(join(fixtureRoot, 'evidence/browser-install-sent.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'one-deliberate-install-starting', nonce: freshNonce, candidate_sha256: captured.sha256 }), { mode: 0o600, flag: 'wx' });
            await click(browser, browser.context, 'Install validated candidate');
            await until(browser, browser.context, "document.body.textContent.includes('Installed and re-validated. Configuration fingerprint: ') && document.querySelector('[aria-label=\"Configuration stage evidence\"]')?.textContent.includes('install: acknowledged') && document.querySelector('[aria-label=\"Configuration stage evidence\"]')?.textContent.includes('installed-confirm: result')", 'fresh-exact-installed-confirmation');
            const confirmation = await browser.evaluate(browser.context, "JSON.stringify({fingerprint:/Installed and re-validated\\. Configuration fingerprint: ([0-9a-f]{64})/.exec(document.body.textContent)?.[1]||null})");
            requireCheck(/^[0-9a-f]{64}$/.test(confirmation.fingerprint), 'fresh-installed-fingerprint-missing');
            await writeFile(join(fixtureRoot, 'evidence/browser-install-confirmed.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'installed-and-confirmed', nonce: freshNonce, installed_sha256: captured.sha256, installed_bytes: captured.bytes, backup_sha256: originalBaseSha, fingerprint: confirmation.fingerprint }), { mode: 0o600, flag: 'wx' });
            const installedProof = await handshake('browser-install-proof.json', identity.fixture_id, freshNonce);
            requireCheck(installedProof.installed_sha256 === captured.sha256 && installedProof.backup_sha256 === originalBaseSha &&
                installedProof.candidate === 'absent' && installedProof.original_lock_unchanged === true &&
                installedProof.lock_device === pinnedConfigLock?.device && installedProof.lock_inode === pinnedConfigLock?.inode, 'fresh-installed-proof-mismatch');
            checks.push({ name: 'actual guarded install, exact API confirmation and independent installed/backup proof', passed: true, installed_sha256: captured.sha256, backup_sha256: originalBaseSha, fingerprint: confirmation.fingerprint });
        }
        if (process.env.CPR_RUNTIME_BROWSER_INTERRUPTION === '1') {
            // Fresh mode uses the confirmed installed base. Historical mode
            // deliberately discards a fully known candidate before uncertainty.
            // The interrupted action never triggers cleanup.
            if (!freshCandidateOnly) await click(browser, browser.context, 'Discard candidate');
            await until(browser, browser.context, "[...document.querySelectorAll('button')].some(item => item.textContent.trim() === 'Validate candidate' && !item.matches(':disabled'))", freshCandidateOnly ? 'known-installed-base-ready' : 'known-candidate-discard');
            await writeFile(join(fixtureRoot, 'evidence/browser-awaiting-lock.json'), JSON.stringify({
                schema_version: 1,
                fixture_id: identity.fixture_id,
                source_commit: SOURCE,
                state: freshCandidateOnly ? 'known-installed-base-awaiting-bounded-holder' : 'known-candidate-discarded-awaiting-bounded-holder',
                ...(freshCandidateOnly ? { nonce: freshNonce, installed_sha256: captured.sha256 } : {}),
            }), { mode: 0o600, flag: 'wx' });
            await handshake('browser-lock-ready.json', identity.fixture_id, freshNonce);
            const interrupted = await browser.evaluate(browser.context, `JSON.stringify(await (async () => {
                const input = document.querySelector('#config-text');
                const baseBytes=new TextEncoder().encode(input.value);
                const base_sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',baseBytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
                Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(input,input.value+'\\n# CPR008 separate interrupted write\\n');
                input.dispatchEvent(new Event('input',{bubbles:true}));
                const bytes=new TextEncoder().encode(input.value);
                return {base_sha256,bytes:bytes.length,sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('')};
            })())`);
            requireCheck(!freshCandidateOnly || interrupted.base_sha256 === captured.sha256, 'interrupted-write-base-not-installed');
            await writeFile(join(fixtureRoot, 'evidence/browser-interrupted-write-sent.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'separate-deliberate-interrupted-write-starting', candidate_sha256: interrupted.sha256, candidate_bytes: interrupted.bytes, ...(freshCandidateOnly ? { nonce: freshNonce } : {}) }), { mode: 0o600, flag: 'wx' });
            await click(browser, browser.context, 'Validate candidate');
            await handshake('browser-writer-waiting.json', identity.fixture_id, freshNonce);
            requireCheck(await browser.evaluate(browser.context, `JSON.stringify(await new Promise(resolve => {
                const proxy=window.cockpit.dbus(null,{bus:'internal'}).proxy('cockpit.Superuser','/superuser');
                proxy.wait(()=>proxy.Stop().then(()=>resolve(true),()=>resolve(false)));
            }))`) === true, 'real-bridge-stop-refused');
            await until(browser, browser.context, "document.body.textContent.includes('candidate-write:') && document.body.textContent.includes('Candidate acknowledgement is uncertain')", 'original-write-cause-not-visible');
            const cause = await browser.evaluate(browser.context, `JSON.stringify((() => {
                const text=[...document.querySelectorAll('.pf-v6-c-alert')].find(item=>item.textContent.includes('candidate-write:'))?.textContent || '';
                return {stage:'candidate-write',category:text.includes('Host connection interrupted')?'bridge':text.includes('Host process failed')?'process':null,problem:/Host problem: (reconnected|terminated|disconnected|no-session|timeout)/.exec(text)?.[1]||null,exit_status:/Process exit status: ([0-9]{1,3})/.exec(text)?.[1]||null,exit_signal:/Process exit signal: ((?:SIG)?[A-Z]{1,8}|[0-9]{1,2})/.exec(text)?.[1]||null,uncertain:document.body.textContent.includes('Candidate acknowledgement is uncertain')};
            })())`);
            requireCheck(cause.uncertain === true && ((cause.category === 'bridge' && typeof cause.problem === 'string') ||
                (cause.category === 'process' && (cause.exit_status !== null || cause.exit_signal !== null))), 'original-interruption-cause-missing');
            password = (await privateFile(identity.password_file, 512)).replace(/\r?\n$/, '');
            const restored = await authenticate(browser, browser.context, password);
            password = '';
            requireCheck(restored?.ok === true, 'real-bridge-reauthentication');
            await handshake('browser-holder-expired.json', identity.fixture_id, freshNonce);
            await until(browser, browser.context, "[...document.querySelectorAll('button')].some(item => item.textContent.trim() === 'Inspect captured configuration' && !item.matches(':disabled'))", 'explicit-inspection-unavailable');
            await click(browser, browser.context, 'Inspect captured configuration');
            await until(browser, browser.context, "document.body.textContent.includes('Captured candidate:')", 'real-readonly-inspection', 60000);
            const inspection = await browser.evaluate(browser.context, `JSON.stringify((() => {
                const text=document.body.textContent;
                const original=[...document.querySelectorAll('.pf-v6-c-alert')].find(item=>item.textContent.includes('candidate-write:'))?.textContent || '';
                const previous=${JSON.stringify(cause)};
                return {candidate:/Captured candidate: (matching|absent|changed|unknown)/.exec(text)?.[1],installedBase:/Installed base: (matching|absent|changed|unknown)/.exec(text)?.[1],causeRetained:(previous.problem===null||original.includes('Host problem: '+previous.problem))&&(previous.exit_status===null||original.includes('Process exit status: '+previous.exit_status))&&(previous.exit_signal===null||original.includes('Process exit signal: '+previous.exit_signal)),ordinaryValidateDisabled:[...document.querySelectorAll('button')].find(item=>item.textContent.trim()==='Validate candidate')?.matches(':disabled')===true};
            })())`);
            requireCheck(['matching', 'absent', 'changed', 'unknown'].includes(inspection.candidate) && inspection.installedBase === 'matching' &&
                inspection.causeRetained === true && inspection.ordinaryValidateDisabled === true, 'uncertain-write-evidence-lost');
            if (freshCandidateOnly) {
                await writeFile(join(fixtureRoot, 'evidence/browser-inspection-observed.json'), JSON.stringify({ fixture_id: identity.fixture_id, source_commit: SOURCE, state: 'inspection-observed', nonce: freshNonce, installed_sha256: captured.sha256, backup_sha256: originalBaseSha, captured_candidate_sha256: interrupted.sha256, candidate_state: inspection.candidate }), { mode: 0o600, flag: 'wx' });
                const finalProof = await handshake('browser-final-proof.json', identity.fixture_id, freshNonce);
                requireCheck(finalProof.installed_sha256 === captured.sha256 && finalProof.backup_sha256 === originalBaseSha &&
                    finalProof.candidate_state === inspection.candidate &&
                    (finalProof.candidate_state !== 'matching' || finalProof.candidate_sha256 === interrupted.sha256) &&
                    (finalProof.candidate_state !== 'absent' || finalProof.candidate_sha256 === null) &&
                    finalProof.original_lock_unchanged === true && finalProof.lock_device === pinnedConfigLock?.device && finalProof.lock_inode === pinnedConfigLock?.inode &&
                    finalProof.domain_guard_unchanged === true && finalProof.legacy_masks_unchanged === 8 && finalProof.nfs_readonly === true &&
                    finalProof.selinux_enforcing === true && finalProof.job_receipts === 0, 'fresh-final-independent-proof-mismatch');
                checks.push({
                    name: 'independent final filesystem, original guard/lock, masks, SELinux and zero-job proof',
                    passed: true,
                    installed_sha256: finalProof.installed_sha256,
                    backup_sha256: finalProof.backup_sha256,
                    candidate_state: finalProof.candidate_state,
                    candidate_sha256: finalProof.candidate_sha256,
                    job_receipts: 0
                });
            }
            checks.push({
                name: 'real privileged bridge interruption and explicit read-only reconciliation',
                passed: true,
                ...cause,
                ...inspection,
                replayed: false,
                installation_after_uncertainty: false,
                cleanup_after_uncertainty: false
            });
            // Reauthentication may only observe the already admitted operation;
            // configuration remains uncertain and no submission is repeated.
            if (freshCandidateOnly) {
                checks.push({ name: 'fresh fixture has no operation submission or imported old handles; original observation is separate third-fixture evidence', passed: true });
            } else if (continuation) {
                await nativeOriginalReads(browser, browser.context, prepared, expected, runner);
            } else {
                await until(browser, browser.context, "[...document.querySelector('[aria-label=\"Original prune-dry-run\"]').querySelectorAll('button')].some(item=>item.textContent.trim()==='Look up original key'&&!item.matches(':disabled'))", 'reconnected-original-authority');
                await click(browser, browser.context, 'Look up original key');
                await until(browser, browser.context, "(() => {const section=document.querySelector('[aria-label=\"Original prune-dry-run\"]');return section && [...section.querySelectorAll('dt')].some(item=>item.textContent.trim()==='operation') && !section.querySelector('.pf-v6-c-alert') && [...section.querySelectorAll('button')].some(item=>item.textContent.trim()==='Observe original operation'&&!item.matches(':disabled'));})()", 'reconnected-original-lookup');
                assertOriginal(await originalSnapshot(browser, browser.context), prepared, original);
                await click(browser, browser.context, 'Observe original operation');
                await until(browser, browser.context, `(() => {const section=document.querySelector('[aria-label="Original prune-dry-run"]');return section && ![...section.querySelectorAll('dt')].some(item=>item.textContent.trim()==='operation') && (${restoredPresentation}) && [...section.querySelectorAll('button')].some(item=>item.textContent.trim()==='Observe original operation'&&!item.matches(':disabled'));})()`, 'reconnected-original-wait');
                assertOriginal(await originalSnapshot(browser, browser.context), prepared, original);
            }
            if (!freshCandidateOnly) checks.push({
                name: 'after genuine bridge reauthentication lookup/wait retain the same original operation',
                passed: true,
                key: prepared.key,
                operation_id: original.operation_id,
                run_id: original.run_id,
                exit_code: original.exit_code,
                replayed: false
            });
        }
        console.log(JSON.stringify({
            fixture: 'real disposable Cockpit/PAM browser',
            state: 'passed',
            ...publicIdentity,
            firefox: browser.capabilities.browserVersion,
            fresh_candidate_only: freshCandidateOnly,
            fresh_pipe_candidate_only: pipeCandidateOnly,
            operation_submission_executed: !freshCandidateOnly && !continuation,
            continuation_original_only: continuation,
            known_prewrite_continuation: knownPrewrite,
            interruption_executed: process.env.CPR_RUNTIME_BROWSER_INTERRUPTION === '1',
            independent_wire_post_counter: false,
            fixed_client_launch_counts_require_provisioner_evidence: true,
            checks,
            preserved: freshCandidateOnly ? 'Known installation was confirmed before the separate uncertain write; its draft, cause and evidence remain retained.' : 'Captured draft and original evidence retained; installation was not requested.'
        }));
        succeeded = true;
    } finally {
        password = '';
        if (!succeeded) {
            try {
                const failure = await browser.evaluate(browser.context, `JSON.stringify((() => {
                    const alerts=[...document.querySelectorAll('.pf-v6-c-alert')].slice(0,8);
                    const stages=['installed-read','candidate-write','candidate-validate','candidate-preview','install','installed-confirm','operation-lookup','operation-wait'];
                    const categories={access:'Administrative access is required',bridge:'Host connection interrupted',launcher:'Client launcher could not start',process:'Host process failed',protocol:'Client output could not be validated',observation:'Operation observation interrupted'};
                    const facts=alerts.map(alert=>{
                        const text=alert.textContent;
                        return {stage:stages.find(stage=>text.includes(stage+':'))||null,
                            category:Object.keys(categories).find(key=>text.includes(categories[key]))||null,
                            problem:/Host problem: (reconnected|terminated|disconnected|no-session|timeout|access-denied|authentication-failed)\\b/.exec(text)?.[1]||null,
                            exit_status:/Process exit status: ([0-9]{1,3})\\b/.exec(text)?.[1]||null,
                            exit_signal:/Process exit signal: ((?:SIG)?(?:HUP|INT|QUIT|ILL|ABRT|FPE|KILL|SEGV|PIPE|ALRM|TERM)|[0-9]{1,2})\\b/.exec(text)?.[1]||null,
                            codes:[...new Set(text.match(/\\bHF[A-Z]{2,4}[0-9]{3}\\b/g)||[])].slice(0,8)};
                    });
                    const validate=[...document.querySelectorAll('button')].find(item=>item.textContent.trim()==='Validate candidate');
                    const install=[...document.querySelectorAll('button')].find(item=>item.textContent.trim()==='Install validated candidate');
                    return {facts,validate_visible:Boolean(validate?.getClientRects().length),validate_effectively_disabled:validate?validate.matches(':disabled'):null,
                        install_ready:Boolean(install?.getClientRects().length&&!install.matches(':disabled')),
                        administrative_warning:document.body.textContent.includes('Administrative access is required for client and host actions'),
                        host_permissions_warning:alerts.some(alert=>alert.textContent.includes('Host permissions require attention')),
                        candidate_uncertain:document.body.textContent.includes('Candidate acknowledgement is uncertain'),
                        installation_uncertain:document.body.textContent.includes('Installation acknowledgement is uncertain')};
                })())`);
                checks.push({ name: 'safe live failure projection before browser close; future attempts only', ...failure });
            } catch { /* Missing live facts remain unknown, never reconstructed. */ }
        }
        const preserve = !succeeded || process.env.CPR_RUNTIME_BROWSER_INTERRUPTION === '1';
        if (preserve)
            await writeFile(join(fixtureRoot, 'evidence/browser-retained-profile-' + basename(browser.profile) + '.json'), JSON.stringify({
                fixture_id: identity.fixture_id,
                profile: browser.profile,
                reason: succeeded ? 'Preserve private browser evidence after uncertain host execution; no cleanup.' : 'Preserve private original-handle/session evidence after a failed check.',
            }), { mode: 0o600, flag: 'wx' }).catch(() => undefined);
        await browser.close(preserve); // Detach only; retain evidence after uncertainty.
    }
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(error => {
    const code = error instanceof RuntimeCheckError ? error.code : 'runtime-prerequisite-or-check-failed';
    console.log(JSON.stringify({
        fixture: 'real disposable Cockpit/PAM browser',
        state: fixtureVerified ? 'failed' : 'blocked',
        ...publicIdentity,
        checks,
        code,
        acceptance: 'V54 remains unpassed; no controlled boundary substitutes for this check.'
    }));
    process.exitCode = fixtureVerified ? 1 : 69;
});
