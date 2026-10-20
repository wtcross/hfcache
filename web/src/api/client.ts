/** Fixed same-origin transport. Responses become usable only after reconstruction. */
import * as wire from "../wire/generated";
import {
    ARTIFACT_JSON_LIMITS,
    NORMAL_JSON_LIMITS,
    parseWireJson,
    readBoundedJson,
    WireError,
} from "../wire/json";
import { isRecord, wireObject } from "../wire/runtime";
import type { JsonObject } from "../wire/runtime";
import { createApiScope, repositorySegments } from "./identity";
import type { ApiScope, ExactPublication } from "./identity";
import {
    applyBindings,
    validateApiProblem,
    validateOperationTransition,
} from "./bindings";
import type { RequestBinding } from "./bindings";
import type {
    PreservedFailure,
    ReadOptions,
    ReadResponse,
    ReadResult,
} from "./types";
import { buildRequestInput, serializeRequestJson } from "./request";

type Decoder<T> = (value: unknown) => T;
interface Contract<S, F> {
    readonly method: "GET" | "POST";
    readonly path: string;
    readonly commands: readonly string[];
    readonly bindingIds: readonly string[];
    readonly decodeSuccess: (value: unknown, command?: string) => S;
    readonly decodeFailure: (value: unknown, command?: string) => F;
    readonly decodePath: Decoder<Readonly<Record<string, string>>>;
    readonly decodeQuery: Decoder<object>;
    readonly repeated: readonly string[];
}
type Query<K extends keyof typeof wire.routeContracts> = ReturnType<
    (typeof wire.routeContracts)[K]["decodeQuery"]
>;
export type PageQuery = Query<"status_default">;
export type CatalogQuery = Query<"catalog_search_default">;
export interface ApiClientOptions {
    readonly scope: ApiScope;
    readonly fetcher?: typeof globalThis.fetch;
    readonly timeoutMs?: number;
}
export interface SubmissionOptions extends ReadOptions {
    readonly idempotencyKey: string;
}
export type SubmissionResult =
    | {
          readonly kind: "accepted";
          readonly acceptance: wire.Acceptance;
          readonly idempotencyKey: string;
          readonly route: string;
      }
    | {
          readonly kind: "api_problem";
          readonly status: number;
          readonly problem: wire.ClientProblem;
      }
    | {
          readonly kind: "uncertain";
          readonly idempotencyKey: string;
          readonly route: string;
          readonly reason: "network" | "timeout" | "aborted" | "protocol";
      }
    | { readonly kind: "refused"; readonly reason: "schema" | "authority" };

const wrapperFields = [
    "schema_version",
    "request_id",
    "archive_id",
    "config_fingerprint",
    "envelope",
    "next_cursor",
];
const envelopeFields = [
    "command",
    "completed_at",
    "data",
    "errors",
    "exit_code",
    "outcome",
    "run_id",
    "schema_version",
    "started_at",
    "warnings",
];
function wrapper(raw: unknown): {
    response: wire.ClientRead;
    payload: unknown;
} {
    const top = wireObject(raw, wrapperFields),
        envelope = wireObject(top.envelope, envelopeFields);
    // Retain raw numeric lexemes in the selected payload until its own decoder.
    return {
        response: wire.decodeClientRead({
            ...top,
            envelope: { ...envelope, data: {} },
        }),
        payload: envelope.data,
    };
}
function preserved(response: wire.ClientRead): PreservedFailure {
    return {
        request_id: response.request_id,
        archive_id: response.archive_id,
        config_fingerprint: response.config_fingerprint,
        command: response.envelope.command,
        exit_code: response.envelope.exit_code,
        errors: response.envelope.errors,
        warnings: response.envelope.warnings,
        run_id: response.envelope.run_id,
        started_at: response.envelope.started_at,
        completed_at: response.envelope.completed_at,
        outcome: response.envelope.outcome,
        schema_version: response.envelope.schema_version,
    };
}
function typedResponse<T>(
    response: wire.ClientRead,
    payload: T,
): ReadResponse<T> {
    return Object.freeze({
        ...response,
        envelope: Object.freeze({ ...response.envelope, data: payload }),
    });
}
function canonicalInput(value: unknown): unknown {
    return parseWireJson(serializeRequestJson(value));
}
function key(value: string): string {
    if (
        /^[A-Za-z0-9._~+-]{1,128}$/u.exec(value)?.[0] !== value ||
        /hf_[A-Za-z0-9]{8,}/iu.test(value)
    )
        throw new WireError("schema");
    return value;
}
function wasAborted(signal: AbortSignal | undefined): boolean {
    return signal?.aborted === true;
}

export class ApiClient {
    readonly scope: ApiScope;
    private readonly fetcher: typeof globalThis.fetch;
    private readonly timeoutMs: number;
    private readonly operations = new Map<string, wire.ClientOperation>();
    constructor(options: ApiClientOptions) {
        this.scope = createApiScope(options.scope);
        if (
            typeof location !== "undefined" &&
            location.origin !== this.scope.origin
        )
            throw new WireError("semantic");
        this.fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis);
        this.timeoutMs = options.timeoutMs ?? 30000;
        if (
            !Number.isSafeInteger(this.timeoutMs) ||
            this.timeoutMs < 1 ||
            this.timeoutMs > 120000
        )
            throw new WireError("bounds");
    }
    private authority(
        response: {
            readonly archive_id: string | null;
            readonly config_fingerprint: string | null;
        },
        historical = false,
        nullable = false,
        nullableFingerprint = nullable,
    ): void {
        if (
            (this.scope.archiveId !== null &&
                this.scope.archiveId !== response.archive_id &&
                !(nullable && response.archive_id === null)) ||
            (!nullable && response.archive_id === null) ||
            (!nullableFingerprint && response.config_fingerprint === null) ||
            (!historical &&
                this.scope.configFingerprint !== null &&
                !(
                    nullableFingerprint && response.config_fingerprint === null
                ) &&
                this.scope.configFingerprint !== response.config_fingerprint)
        )
            throw new WireError("semantic");
    }
    private remember(operation: wire.ClientOperation): void {
        validateOperationTransition(
            this.operations.get(operation.operation_id),
            operation,
        );
        if (
            !this.operations.has(operation.operation_id) &&
            this.operations.size >= 128
        ) {
            const first = this.operations.keys().next().value;
            if (first !== undefined) this.operations.delete(first);
        }
        this.operations.set(operation.operation_id, operation);
    }
    private url<S, F>(
        contract: Contract<S, F>,
        path: unknown,
        query: unknown,
    ): URL {
        const parameters = contract.decodePath(canonicalInput(path));
        const decoded = contract.decodeQuery(canonicalInput(query));
        let pathname = contract.path;
        for (const [name, value] of Object.entries(parameters))
            pathname = pathname.replace(`{${name}}`, encodeURIComponent(value));
        if (pathname.includes("{") || pathname.includes("}"))
            throw new WireError("schema");
        const url = new URL(
            this.scope.origin + this.scope.publicPrefix + pathname,
        );
        if (url.origin !== this.scope.origin) throw new WireError("semantic");
        if (!isRecord(decoded)) throw new WireError("schema");
        for (const [name, value] of Object.entries(decoded)) {
            const entries: readonly unknown[] =
                contract.repeated.includes(name) && Array.isArray(value)
                    ? value
                    : [value];
            for (const entry of entries) {
                if (
                    typeof entry !== "string" &&
                    typeof entry !== "number" &&
                    typeof entry !== "boolean"
                )
                    throw new WireError("schema");
                url.searchParams.append(name, String(entry));
            }
        }
        return url;
    }
    private async read<S extends JsonObject, F extends JsonObject>(
        contract: Contract<S, F>,
        path: unknown,
        query: unknown,
        options: ReadOptions,
        context: RequestBinding = {},
        artifact = false,
        body?: unknown,
        lookupKey?: string,
    ): Promise<ReadResult<S, F>> {
        let evidence: PreservedFailure | undefined;
        const controller = new AbortController();
        const deadline = { expired: false };
        const abort = () => {
            controller.abort();
        };
        options.signal?.addEventListener("abort", abort, { once: true });
        if (options.signal?.aborted === true) controller.abort();
        const timer = setTimeout(() => {
            deadline.expired = true;
            controller.abort();
        }, this.timeoutMs);
        try {
            const url = this.url(contract, path, query);
            const headers = new Headers({ Accept: "application/json" });
            if (body !== undefined) {
                headers.set("Content-Type", "application/json");
                headers.set("X-Hfcache-Request", "1");
            }
            if (lookupKey !== undefined)
                headers.set("Idempotency-Key", key(lookupKey));
            if (controller.signal.aborted) return { kind: "aborted" };
            const response = await this.fetcher(url, {
                method: contract.method,
                headers,
                credentials: "same-origin",
                mode: "same-origin",
                redirect: "error",
                cache: "no-store",
                referrerPolicy: "no-referrer",
                signal: controller.signal,
                ...(body === undefined ? {} : { body: JSON.stringify(body) }),
            });
            const raw = await readBoundedJson(response, {
                signal: controller.signal,
                limits: artifact ? ARTIFACT_JSON_LIMITS : NORMAL_JSON_LIMITS,
            });
            if (response.status !== 200) {
                const problem = wire.decodeClientProblem(raw);
                validateApiProblem(problem);
                if (response.status < 400 || response.status > 599)
                    throw new WireError("schema");
                return {
                    kind: "api_problem",
                    status: response.status,
                    problem,
                };
            }
            const decoded = wrapper(raw),
                result = decoded.response;
            const historical = contract.path.startsWith("/api/v1/operations/");
            const nullable = [
                "/api/v1/version",
                "/api/v1/capabilities",
                "/api/v1/health",
                "/api/v1/config/validate",
            ].includes(contract.path);
            this.authority(
                result,
                historical,
                nullable,
                nullable || contract.path === "/api/v1/operations",
            );
            if (!contract.commands.includes(result.envelope.command))
                throw new WireError("semantic");
            if (result.envelope.exit_code !== 0) evidence = preserved(result);
            if (result.envelope.exit_code === 0) {
                const payload = contract.decodeSuccess(
                        decoded.payload,
                        result.envelope.command,
                    ),
                    complete = typedResponse(result, payload);
                applyBindings(contract.bindingIds, complete, context);
                if (
                    contract.path === "/api/v1/status" &&
                    isRecord(payload.archive) &&
                    payload.archive.archive_id !== result.archive_id
                )
                    throw new WireError("semantic");
                if ("operation" in payload)
                    this.remember(
                        wire.decodeClientOperation(
                            canonicalInput(payload.operation),
                        ),
                    );
                if (
                    "operations" in payload &&
                    Array.isArray(payload.operations)
                )
                    for (const operation of payload.operations)
                        this.remember(
                            wire.decodeClientOperation(
                                canonicalInput(operation),
                            ),
                        );
                if (contract.path === "/api/v1/capabilities") {
                    const capabilities = wire.decodeCapabilities(
                        canonicalInput(payload),
                    );
                    if (
                        capabilities.credential_class !==
                            this.scope.credentialClass ||
                        (this.scope.instanceId !== null &&
                            capabilities.instance_id !== this.scope.instanceId)
                    )
                        throw new WireError("semantic");
                }
                return { kind: "success", response: complete, payload };
            }
            const payload = contract.decodeFailure(
                    decoded.payload,
                    result.envelope.command,
                ),
                complete = typedResponse(result, payload);
            applyBindings(contract.bindingIds, complete, context);
            return { kind: "domain_failure", response: complete, payload };
        } catch (error) {
            if (options.signal?.aborted === true) return { kind: "aborted" };
            if (deadline.expired)
                return { kind: "transport_failure", reason: "timeout" };
            if (error instanceof WireError)
                return evidence === undefined
                    ? { kind: "protocol_failure", reason: error.reason }
                    : {
                          kind: "protocol_failure",
                          reason: error.reason,
                          preserved: evidence,
                      };
            return { kind: "transport_failure", reason: "network" };
        } finally {
            clearTimeout(timer);
            options.signal?.removeEventListener("abort", abort);
            controller.abort();
        }
    }
    readVersion(options: ReadOptions = {}) {
        return this.read(wire.routeContracts.version_default, {}, {}, options);
    }
    readCapabilities(options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.capabilities_default,
            {},
            {},
            options,
        );
    }
    readHealth(options: ReadOptions = {}) {
        return this.read(wire.routeContracts.health_default, {}, {}, options);
    }
    readArchiveInspection(options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.inspection_default,
            {},
            {},
            options,
        );
    }
    readStatus(options: ReadOptions = {}, query: PageQuery = {}) {
        return this.read(
            wire.routeContracts.status_default,
            {},
            query,
            options,
        );
    }
    readRepositories(query: PageQuery = {}, options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.repositories_default,
            {},
            query,
            options,
        );
    }
    readRevisions(query: PageQuery = {}, options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.revisions_default,
            {},
            query,
            options,
        );
    }
    readVerificationEstimate(options: ReadOptions = {}) {
        return this.read(wire.routeContracts.estimate_default, {}, {}, options);
    }
    readRuns(query: Query<"runs_default"> = {}, options: ReadOptions = {}) {
        return this.read(wire.routeContracts.runs_default, {}, query, options);
    }
    readReport(runId: string, options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.report_default,
            { run_id: runId },
            {},
            options,
            { runId },
            true,
        );
    }
    readReference(
        repositoryType: "model" | "dataset",
        repositoryId: string,
        revision: string,
        options: ReadOptions = {},
    ) {
        const [namespace, name] = repositorySegments(
            repositoryType,
            repositoryId,
        );
        return this.read(
            wire.routeContracts.reference_default,
            { repository_type: repositoryType, namespace, name, revision },
            {},
            options,
            { repositoryType, repositoryId, revision },
            true,
        );
    }
    readManifest(publication: ExactPublication, options: ReadOptions = {}) {
        const { repositoryType, repositoryId, commitSha, publicationId } =
            publication;
        const [namespace, name] = repositorySegments(
            repositoryType,
            repositoryId,
        );
        return this.read(
            wire.routeContracts.manifest_default,
            {
                repository_type: repositoryType,
                namespace,
                name,
                commit_sha: commitSha,
                publication_id: publicationId,
            },
            {},
            options,
            publication,
            true,
        );
    }
    readOperations(
        query: Query<"operations_default"> = {},
        options: ReadOptions = {},
    ) {
        return this.read(
            wire.routeContracts.operations_default,
            {},
            query,
            options,
        );
    }
    lookupOperation(idempotencyKey: string, options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.operation_lookup_default,
            {},
            {},
            options,
            {},
            false,
            undefined,
            idempotencyKey,
        );
    }
    readOperation(operationId: string, options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.operation_default,
            { operation_id: operationId },
            {},
            options,
            { operationId },
        );
    }
    readOperationEvents(
        operation: wire.ClientOperation,
        query: Query<"operation_events_default"> = {},
        options: ReadOptions = {},
    ) {
        return this.read(
            wire.routeContracts.operation_events_default,
            { operation_id: operation.operation_id },
            query,
            options,
            { operation, ...query },
        );
    }
    readCatalogSearch(query: CatalogQuery = {}, options: ReadOptions = {}) {
        return this.read(
            wire.routeContracts.catalog_search_default,
            {},
            query,
            options,
        );
    }
    readCatalogFacets(
        query: Query<"catalog_facets_default"> = {},
        options: ReadOptions = {},
    ) {
        return this.read(
            wire.routeContracts.catalog_facets_default,
            {},
            query,
            options,
            { ...(query.facet === undefined ? {} : { facet: query.facet }) },
        );
    }
    readCatalogDetail(
        repositoryType: "model" | "dataset",
        repositoryId: string,
        query: Query<"catalog_detail_default"> = {},
        options: ReadOptions = {},
    ) {
        const [namespace, name] = repositorySegments(
            repositoryType,
            repositoryId,
        );
        return this.read(
            wire.routeContracts.catalog_detail_default,
            { repository_type: repositoryType, namespace, name },
            query,
            options,
            {
                repositoryType,
                repositoryId,
                ...(query.commit_sha === undefined
                    ? {}
                    : { commitSha: query.commit_sha }),
                ...(query.publication_id === undefined
                    ? {}
                    : { publicationId: query.publication_id }),
            },
        );
    }
    readCatalogVariants(
        repositoryType: "model" | "dataset",
        repositoryId: string,
        query: Query<"catalog_variants_default"> = {},
        options: ReadOptions = {},
    ) {
        const [namespace, name] = repositorySegments(
            repositoryType,
            repositoryId,
        );
        return this.read(
            wire.routeContracts.catalog_variants_default,
            { repository_type: repositoryType, namespace, name },
            query,
            options,
            {
                repositoryType,
                repositoryId,
                ...(query.commit_sha === undefined
                    ? {}
                    : { commitSha: query.commit_sha }),
                ...(query.publication_id === undefined
                    ? {}
                    : { publicationId: query.publication_id }),
            },
        );
    }
    readOperationResult(
        original: wire.ClientOperation,
        options: ReadOptions = {},
    ) {
        const operation = wire.decodeClientOperation(canonicalInput(original));
        this.authority(operation, true);
        this.remember(operation);
        const commands = wire.operationResultDefinitions
            .filter((entry) => entry.origin_path === operation.route)
            .flatMap((entry) => entry.commands);
        const contract: Contract<wire.OperationSuccess, wire.OperationFailure> =
            {
                ...wire.routeContracts.operation_result_by_original_operation,
                commands,
                decodeSuccess: (value, command) => {
                    if (command === undefined) throw new WireError("semantic");
                    return wire.decodeOriginalOperationPayload(
                        operation.route,
                        command,
                        false,
                        value,
                    );
                },
                decodeFailure: (value, command) => {
                    if (command === undefined) throw new WireError("semantic");
                    return wire.decodeOriginalOperationPayload(
                        operation.route,
                        command,
                        true,
                        value,
                    );
                },
            };
        return this.read(
            contract,
            { operation_id: operation.operation_id },
            {},
            options,
            { operation },
            true,
        );
    }
    validateInstalledConfiguration(options: ReadOptions = {}) {
        const contract = wire.routeContracts.config_validate_installed;
        const body = contract.decodeBody(canonicalInput({}));
        return this.read(contract, {}, {}, options, {}, false, body);
    }
    validateCandidateConfiguration(
        candidate: wire.RequestLiteralCandidateValidation,
        options: ReadOptions = {},
    ) {
        const contract = wire.routeContracts.config_validate_literal_candidate;
        const body = contract.decodeBody(canonicalInput(candidate));
        return this.read(contract, {}, {}, options, {}, false, body);
    }
    private async submit<B>(
        contract: Contract<wire.Acceptance, never> & {
            readonly decodeBody: Decoder<B>;
        },
        request: B,
        options: SubmissionOptions,
        requiredCapability: "read" | "write" = "write",
    ): Promise<SubmissionResult> {
        let retained: string, body: B, url: URL;
        try {
            if (
                requiredCapability === "write" &&
                this.scope.credentialClass !== "rest-writer"
            )
                return { kind: "refused", reason: "authority" };
            retained = key(options.idempotencyKey);
            body = contract.decodeBody(
                buildRequestInput(contract.path, request),
            );
            url = this.url(contract, {}, {});
        } catch {
            return { kind: "refused", reason: "schema" };
        }
        if (wasAborted(options.signal))
            return { kind: "refused", reason: "schema" };
        const controller = new AbortController();
        const deadline = { expired: false };
        const abort = () => {
            controller.abort();
        };
        options.signal?.addEventListener("abort", abort, { once: true });
        const timer = setTimeout(() => {
            deadline.expired = true;
            controller.abort();
        }, this.timeoutMs);
        try {
            const response = await this.fetcher(url, {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                    "X-Hfcache-Request": "1",
                    "Idempotency-Key": retained,
                },
                credentials: "same-origin",
                mode: "same-origin",
                redirect: "error",
                cache: "no-store",
                referrerPolicy: "no-referrer",
                signal: controller.signal,
                body: JSON.stringify(body),
            });
            const raw = await readBoundedJson(response, {
                signal: controller.signal,
            });
            if (response.status >= 400 && response.status <= 599) {
                const problem = wire.decodeClientProblem(raw);
                validateApiProblem(problem);
                return {
                    kind: "api_problem",
                    status: response.status,
                    problem,
                };
            }
            if (response.status !== 202) throw new WireError("schema");
            const acceptance = wire.decodeAcceptance(raw),
                operation = acceptance.operation;
            this.authority(acceptance);
            const status =
                this.scope.publicPrefix +
                "/api/v1/operations/" +
                operation.operation_id;
            if (
                operation.route !== contract.path ||
                operation.principal !== this.scope.credentialClass ||
                acceptance.links.status !== status ||
                acceptance.links.result !== status + "/result" ||
                acceptance.links.events !== status + "/events" ||
                response.headers.get("Location") !== status
            )
                throw new WireError("semantic");
            this.remember(operation);
            return {
                kind: "accepted",
                acceptance,
                idempotencyKey: retained,
                route: contract.path,
            };
        } catch (error) {
            return {
                kind: "uncertain",
                idempotencyKey: retained,
                route: contract.path,
                reason:
                    options.signal?.aborted === true
                        ? "aborted"
                        : deadline.expired
                          ? "timeout"
                          : error instanceof WireError
                            ? "protocol"
                            : "network",
            };
        } finally {
            clearTimeout(timer);
            options.signal?.removeEventListener("abort", abort);
            controller.abort();
        }
    }
    submitSync(
        request: wire.RequestSyncSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(wire.routeContracts.sync_default, request, options);
    }
    submitInstalledPlan(
        request: wire.RequestInstalledPlan,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.plan_installed,
            request,
            options,
            "read",
        );
    }
    submitCandidatePlan(
        request: wire.RequestLiteralCandidatePlan,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.plan_literal_candidate,
            request,
            options,
        );
    }
    submitReadOnlyDiagnostics(
        request: wire.RequestReadOnlyDiagnostics,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.diagnostics_read_only,
            request,
            options,
            "read",
        );
    }
    submitProbeDiagnostics(
        request: wire.RequestProbeDiagnostics,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.diagnostics_probe,
            request,
            options,
        );
    }
    submitNewVerification(
        request: wire.RequestNewVerification,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.verification_new,
            request,
            options,
        );
    }
    submitFullVerification(
        request: wire.RequestFullVerification,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.verification_full,
            request,
            options,
        );
    }
    submitRevisionVerification(
        request: wire.RequestRevisionVerification,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.verification_revision,
            request,
            options,
        );
    }
    submitPrunePreview(
        request: wire.RequestPruneSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.prune_preview_default,
            request,
            options,
            "read",
        );
    }
    submitPruneApply(
        request: wire.RequestPruneSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.prune_apply_default,
            request,
            options,
        );
    }
    submitPurgePreview(
        request: wire.RequestPurgeSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.purge_preview_default,
            request,
            options,
            "read",
        );
    }
    submitPurgeApply(
        request: wire.RequestPurgeSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.purge_apply_default,
            request,
            options,
        );
    }
    submitRecoveryPreview(
        request: wire.RequestRecoverySubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.recovery_preview_default,
            request,
            options,
            "read",
        );
    }
    submitRecoveryApply(
        request: wire.RequestRecoverySubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.recovery_apply_default,
            request,
            options,
        );
    }
    submitQuarantinePreview(
        request: wire.RequestQuarantineSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.quarantine_preview_default,
            request,
            options,
            "read",
        );
    }
    submitQuarantineApply(
        request: wire.RequestQuarantineSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.quarantine_apply_default,
            request,
            options,
        );
    }
    submitRepair(
        request: wire.RequestRepairSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.repair_default,
            request,
            options,
        );
    }
    submitCatalogRefresh(
        request: wire.RequestCatalogRefreshSubmission,
        options: SubmissionOptions,
    ) {
        return this.submit(
            wire.routeContracts.catalog_refresh_default,
            request,
            options,
        );
    }
}
export function createApiClient(options: ApiClientOptions): ApiClient {
    return new ApiClient(options);
}
