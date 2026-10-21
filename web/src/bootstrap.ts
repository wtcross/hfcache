/** A separately typed, bounded bootstrap precedes every production app mount. */
import { decodeUiBootstrap, WIRE_SOURCE_DIGEST } from "./wire/generated";
import type { UiBootstrap } from "./wire/generated";
import { readBoundedJson, WireError } from "./wire/json";
import { canonicalHex, createApiScope } from "./api/identity";
import type { ApiScope } from "./api/identity";
import { canonicalToolchain, canonicalUiPrefix } from "./wire/ui-semantics";
import { uriPath } from "./api/url-paths";

export const BOOTSTRAP_LIMITS = Object.freeze({
    maxBytes: 32768,
    maxDepth: 16,
    maxTokens: 2048,
    maxKeys: 128,
    maxNumberCharacters: 128,
});
export interface InertMetadata {
    readonly base: string;
    readonly bootstrap: string;
    readonly fingerprint: string;
}
export interface CompiledIdentity {
    readonly source: string;
    readonly application: string;
    readonly wire: string;
}
function hasWebCrypto(value: unknown): value is Pick<Crypto, "subtle"> {
    return (
        typeof value === "object" &&
        value !== null &&
        "subtle" in value &&
        typeof value.subtle === "object" &&
        value.subtle !== null &&
        "digest" in value.subtle &&
        typeof value.subtle.digest === "function"
    );
}
export function readInertMetadata(document: Document): InertMetadata {
    const bases = document.querySelectorAll("base"),
        base = bases[0];
    if (
        bases.length !== 1 ||
        base === undefined ||
        base.attributes.length !== 1
    )
        throw new WireError("schema");
    function slot(name: string): string {
        const slots = document.querySelectorAll(`meta[name="${name}"]`),
            meta = slots[0];
        if (
            slots.length !== 1 ||
            meta === undefined ||
            meta.attributes.length !== 2
        )
            throw new WireError("schema");
        const value = meta.getAttribute("content");
        if (value === null) throw new WireError("schema");
        return value;
    }
    const encoded = slot("hfcache-ui-base"),
        bootstrap = slot("hfcache-ui-bootstrap"),
        fingerprint = slot("hfcache-ui-fingerprint");
    if (
        slot("hfcache-ui-contract") !== "1" ||
        base.getAttribute("href") !== encoded ||
        !canonicalHex(fingerprint, 64) ||
        !encoded.endsWith("/ui/")
    )
        throw new WireError("schema");
    let prefix: string;
    try {
        prefix = decodeURIComponent(encoded.slice(0, -4));
    } catch {
        throw new WireError("schema");
    }
    canonicalUiPrefix(prefix);
    if (
        encoded !== (prefix === "" ? "" : uriPath(prefix)) + "/ui/" ||
        bootstrap !== encoded + "bootstrap.json"
    )
        throw new WireError("schema");
    return Object.freeze({ base: encoded, bootstrap, fingerprint });
}
export async function verifyBootstrapContext(
    bootstrap: UiBootstrap,
    metadata: InertMetadata,
    origin: string,
    compiled: CompiledIdentity,
    crypto?: { readonly subtle?: SubtleCrypto },
): Promise<void> {
    if (
        bootstrap.configured_origin !== origin ||
        bootstrap.paths.ui_base !== metadata.base ||
        bootstrap.paths.bootstrap !== metadata.bootstrap ||
        bootstrap.build.asset_manifest_sha256 !== metadata.fingerprint ||
        bootstrap.wire_source_digest !== compiled.wire ||
        bootstrap.wire_source_digest !== WIRE_SOURCE_DIGEST ||
        bootstrap.build.metadata.source_snapshot_sha256 !== compiled.source ||
        bootstrap.build.metadata.application_version !== compiled.application
    )
        throw new WireError("semantic");
    const platform: unknown = crypto ?? globalThis.crypto;
    if (!hasWebCrypto(platform)) throw new WireError("unsupported_engine");
    const hash = await platform.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(
            canonicalToolchain(bootstrap.build.metadata.toolchain),
        ),
    );
    const digest = Array.from(new Uint8Array(hash), (byte) =>
        byte.toString(16).padStart(2, "0"),
    ).join("");
    if (digest !== bootstrap.build.metadata.toolchain_sha256)
        throw new WireError("semantic");
}
export function bootstrapScope(bootstrap: UiBootstrap): ApiScope {
    return createApiScope({
        origin: bootstrap.configured_origin,
        publicPrefix: bootstrap.paths.effective_prefix,
        authorityEpoch: bootstrap.authority_epoch,
        subject: bootstrap.user.subject,
        credentialClass: bootstrap.user.credential_class,
        instanceId: bootstrap.instance_id,
        archiveId: bootstrap.configured_archive_id,
        configFingerprint: bootstrap.config_fingerprint,
    });
}
export async function loadBootstrap(
    document: Document,
    origin: string,
    compiled: CompiledIdentity,
    fetcher: typeof fetch = globalThis.fetch,
): Promise<UiBootstrap> {
    const metadata = readInertMetadata(document);
    const bootstrap = await readBootstrap(origin, metadata.bootstrap, fetcher);
    await verifyBootstrapContext(bootstrap, metadata, origin, compiled);
    bootstrapScope(bootstrap);
    return bootstrap;
}
async function readBootstrap(
    origin: string,
    path: string,
    fetcher: typeof fetch,
): Promise<UiBootstrap> {
    const controller = new AbortController();
    const timeout = setTimeout(() => {
        controller.abort();
    }, 10000);
    try {
        const response = await fetcher(origin + path, {
            method: "GET",
            credentials: "same-origin",
            cache: "no-store",
            redirect: "error",
            headers: { Accept: "application/json" },
            signal: controller.signal,
        });
        if (response.status !== 200 || response.redirected) {
            void response.body?.cancel().catch(() => undefined);
            throw new WireError("schema");
        }
        return decodeUiBootstrap(
            await readBoundedJson(response, {
                limits: BOOTSTRAP_LIMITS,
                signal: controller.signal,
            }),
        );
    } finally {
        clearTimeout(timeout);
        controller.abort();
    }
}
export async function checkRelease(
    previous: UiBootstrap,
    fetcher: typeof fetch = globalThis.fetch,
): Promise<boolean> {
    const next = await readBootstrap(
        previous.configured_origin,
        previous.paths.bootstrap,
        fetcher,
    );
    if (
        next.configured_origin !== previous.configured_origin ||
        JSON.stringify(next.paths) !== JSON.stringify(previous.paths)
    )
        throw new WireError("semantic");
    if (
        releaseChanged(previous, next) ||
        next.instance_id !== previous.instance_id ||
        next.authority_epoch !== previous.authority_epoch ||
        next.user.subject !== previous.user.subject ||
        next.configured_archive_id !== previous.configured_archive_id
    )
        return true;
    await verifyBootstrapContext(
        next,
        {
            base: previous.paths.ui_base,
            bootstrap: previous.paths.bootstrap,
            fingerprint: previous.build.asset_manifest_sha256,
        },
        previous.configured_origin,
        {
            wire: previous.wire_source_digest,
            source: previous.build.metadata.source_snapshot_sha256,
            application: previous.build.metadata.application_version,
        },
    );
    return false;
}
export function releaseChanged(
    previous: UiBootstrap,
    next: UiBootstrap,
): boolean {
    return (
        previous.build.asset_manifest_sha256 !==
            next.build.asset_manifest_sha256 ||
        previous.wire_source_digest !== next.wire_source_digest ||
        previous.build.metadata.source_snapshot_sha256 !==
            next.build.metadata.source_snapshot_sha256
    );
}
