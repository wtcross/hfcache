"""WEB-003 synthetic wire oracle from original serializers, never schema synthesis.

Only an owned temporary tree is read/written. There is no Hub, manager, archive
initialization, authentication claim or installed acceptance in these factories.
IR names are used solely to select/measure coverage, never to create values.
"""

import json
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from pydantic import BaseModel

from hfcache.api.command_models import CommandModel
from hfcache.archive import InitializationResult
from hfcache.card_models import RepositoryCardRead
from hfcache.catalog_query_models import (
    CatalogCoverage,
    CatalogDetailPayload,
    CatalogEntry,
    CatalogFacetPayload,
    CatalogFacetValue,
    CatalogSearchPayload,
    CatalogVariantsPayload,
    ObservationSummary,
    QualifiedVariant,
)
from hfcache.catalog_refresh_models import (
    CatalogRefreshResult,
    PublicationRefresh,
    RepositoryRefresh,
    refresh_counts,
    refresh_state,
)
from hfcache.client_models import (
    Acceptance,
    Capabilities,
    ClientEvent,
    ClientEvents,
    ClientLinks,
    ClientOperation,
    ClientProblem,
    ClientRead,
)
from hfcache.config import ApplicationConfig, RepositoryConfig
from hfcache.config_models import (
    ConfigApplicationSubmission,
    ConfigPreviewReference,
    ManagedEditRequest,
)
from hfcache.errors import Problem
from hfcache.hashing import ObjectIdentity
from hfcache.host_actions_models import HostActionRequest, ObserverStopRequest
from hfcache.identity import CommitSha, PublicationId, RunId, TransactionId
from hfcache.preflight import Check
from hfcache.quarantine import QuarantineCleanupPlan, QuarantineFile
from hfcache.recovery import (
    ArchiveHealth,
    AreaFinding,
    PlannedRemediation,
    Reconciliation,
    RecoveryPlan,
)
from hfcache.repair import RepairOutcome
from hfcache.reporting import PrunedRevision, RecoveryReport, Remediation
from hfcache.services.bootstrap import validate_config
from hfcache.services.candidates import validate_candidate
from hfcache.services.commands import _planned
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.services.queries import LocalQueries, RepositoryQuery
from hfcache.verification import VerificationEstimate
from hfcache.wire_registry import AUTHORITIES, ROUTES, request_authorities, validate_payload
from hfcache.wire_schema import build_contracts
from tests.fixtures import examples
from tests.fixtures.host_actions_examples import EXPECTED, host_action_examples
from tests.unit.test_hub import Entry, FakeApi, client


def request_samples() -> dict[str, dict[str, Any]]:
    """Hand inputs are validated/canonicalized by the original request models."""
    selector = f"model:{examples.REPOSITORY_ID}"
    candidate = "schema_version=1\n# exact literal candidate fixture\n"
    bodies = {
        "ScheduleValidationRequest": {"on_calendar": "daily", "randomized_delay_sec": None},
        "ScheduleChangeRequest": {
            "action": "replace",
            "expected_revision": "a" * 64,
            "on_calendar": "daily",
            "randomized_delay_sec": None,
        },
        "ObserverStopRequest": {"expected": EXPECTED},
        "SyncSubmission": {"selectors": [selector]},
        "PlanSubmission": {"selectors": [selector]},
        "DiagnosticsSubmission": {"read_only": True},
        "VerificationSubmission": {"mode": "new", "run_id": examples.RUN},
        "ValidationSubmission": {},
        "CatalogRefreshSubmission": {"selectors": [selector]},
        "PruneSubmission": {"selectors": [selector]},
        "PurgeSubmission": {"selectors": [selector]},
        "RecoverySubmission": {},
        "QuarantineSubmission": {"transaction_ids": [examples.TRANSACTION]},
        "RepairSubmission": {"revision": selector + "@" + examples.SHA},
        "InitializationSubmission": {
            "archive_root": "/tmp/hfcache-wire-fixture",
            "archive_id": examples.ARCHIVE_ID,
            "confirm": True,
        },
        "InstalledPlan": {"selectors": [selector]},
        "LiteralCandidatePlan": {"candidate": candidate, "selectors": [selector]},
        "InstalledValidation": {},
        "LiteralCandidateValidation": {"candidate": candidate},
        "ManagedValidationRequest": {
            "managed": managed_request().model_dump(mode="json", exclude_none=True)
        },
        "ManagedPlanRequest": {
            "managed": managed_request().model_dump(mode="json", exclude_none=True)
        },
        "ConfigApplicationSubmission": {
            "managed": managed_request().model_dump(mode="json", exclude_none=True),
            "preview": {"operation_id": examples.RUN, "key": "owned-preview"},
        },
        "ReadOnlyDiagnostics": {"read_only": True},
        "ProbeDiagnostics": {"read_only": False},
        "NewVerification": {"mode": "new", "run_id": examples.RUN},
        "FullVerification": {"mode": "full"},
        "RevisionVerification": {"mode": "revision", "revision": selector + "@" + examples.SHA},
    }
    result = {}
    for name, model in request_authorities().items():
        parsed = model.model_validate(bodies[name])
        if not isinstance(parsed, (CommandModel, ConfigApplicationSubmission, HostActionRequest)):
            message = "request authority is not an original command model"
            raise TypeError(message)
        body = parsed.canonical_body()
        if name in {"ManagedValidationRequest", "ManagedPlanRequest"}:
            body = parsed.model_dump(mode="json", exclude_none=True)
        if name == "ValidationSubmission":
            # client.validate_installed sends {}, never explicit candidate:null.
            body = {}
        result["Request" + name] = body
        result["Request" + type(parsed).__name__] = body
    return result


def managed_request() -> ManagedEditRequest:
    """Hand-authored edit vocabulary exercises every strict nested request table."""
    return ManagedEditRequest.model_validate(
        {
            "base_revision": "a" * 64,
            "edits": [
                {
                    "kind": "repository-upsert",
                    "repository": {
                        "id": examples.REPOSITORY_ID,
                        "type": "model",
                        "tags": ["coding"],
                    },
                },
                {
                    "kind": "repository-remove",
                    "repository_type": "dataset",
                    "repository_id": "organization/removed",
                },
                {
                    "kind": "settings-replace",
                    "settings": {
                        "storage": {"maximum_revisions": 5},
                        "sync": {"max_workers": 2},
                        "verification": {"lock_wait_seconds": 0},
                        "repair": {"retired_instance_grace_hours": 168},
                    },
                },
            ],
        }
    )


def _operation(route: str = "/api/v1/syncs") -> ClientOperation:
    return ClientOperation(
        schema_version=1,
        operation_id=examples.RUN,
        principal="rest-writer",
        route=route,
        archive_id=examples.ARCHIVE_ID,
        config_fingerprint=examples.FINGERPRINT,
        state="queued",
        created_at="2026-10-20T12:00:00Z",
        updated_at="2026-10-20T12:00:00Z",
        completed_at=None,
        domain_run_id=None,
        transaction_ids=(),
        next_event_sequence=1,
        result_recorded=False,
    )


def _catalog_samples() -> list[BaseModel]:
    observed = examples.publication_observation()
    variant = observed.variants[0]
    qualified = QualifiedVariant(
        commit_sha=examples.SHA,
        publication_id=examples.PUBLICATION,
        publication_generation=1,
        variant=variant,
    )
    coverage = CatalogCoverage(
        repositories=1,
        tags_known=1,
        tags_unknown=0,
        publications=1,
        usable=1,
        partial=0,
        unsupported=0,
        failed=0,
        missing=0,
        technical_required=False,
        incomplete=False,
    )
    entry = CatalogEntry(
        repository_type="model",
        repository_id=examples.REPOSITORY_ID,
        tags=("coding",),
        tag_origin="configured",
        tag_observed_at=None,
        curation_fingerprint=examples.FINGERPRINT,
        configured=True,
        enabled=False,
        archived=True,
        matching_variant_count=1,
        representative_variant=qualified,
        dataset_formats=(),
    )
    summary = ObservationSummary(
        commit_sha=observed.commit_sha,
        publication_id=observed.publication_id,
        publication_generation=observed.publication_generation,
        extractor_version=observed.extractor_version,
        observed_at=observed.observed_at,
        status=observed.status,
        sources=observed.sources,
        dataset_formats=observed.dataset_formats,
        diagnostics=observed.diagnostics,
    )
    common = {"catalog_identity": examples.DIGEST, "coverage": coverage}
    publication = PublicationRefresh(
        commit_sha=examples.SHA,
        publication_id=examples.PUBLICATION,
        publication_generation=1,
        write_status="written",
        observation_status="complete",
        observed_at=observed.observed_at,
        manifest_digest=examples.DIGEST,
    )
    row = RepositoryRefresh(
        repository_type="model",
        repository_id=examples.REPOSITORY_ID,
        tag_status="captured",
        technical_status="complete",
        publications=(publication,),
    )
    counts = refresh_counts((row,))
    return [
        CatalogSearchPayload(**common, total_matches=1, entries=(entry,)),
        CatalogDetailPayload(**common, entry=entry, observations=(summary,)),
        CatalogFacetPayload(
            **common,
            facet="tag",
            total_matches=1,
            entries=(CatalogFacetValue(value="coding", repository_count=1),),
        ),
        CatalogVariantsPayload(**common, total_matches=1, entries=(qualified,)),
        CatalogRefreshResult(
            state=refresh_state((row,), counts),
            archive_id=examples.ARCHIVE_ID,
            revision_scope="retained",
            tags=True,
            technical=True,
            curation_fingerprint=examples.FINGERPRINT,
            curation_observed_at=observed.observed_at,
            counts=counts,
            repositories=(row,),
        ),
    ]


def _source_payloads(root: Path) -> dict[str, Any]:
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {"archive_root": str(root), "archive_id": examples.ARCHIVE_ID},
            "repositories": [{"type": "model", "id": examples.REPOSITORY_ID, "enabled": False}],
        }
    )
    queries = LocalQueries(config)
    reference = examples.reference()
    repository = queries.layout.repository(reference.identity)
    for path, model in (
        (repository.current_ref, reference),
        (repository.revision_ref(CommitSha(examples.SHA)), reference),
        (
            repository.manifest(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION)),
            examples.manifest(),
        ),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(model.to_json())
    repository.instance(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION)).mkdir(
        parents=True
    )
    inspection = queries.inspect_archive().as_payload()
    listed = queries.list_repositories(RepositoryQuery(revisions=True)).data
    revisions = [
        {
            "repository_type": repo["repository_type"],
            "repository_id": repo["repository_id"],
            **revision,
        }
        for repo in listed["repositories"]
        for revision in repo["revisions"]
    ]
    finding = AreaFinding(
        ".store/staging",
        ".store/staging/" + examples.TRANSACTION,
        examples.TRANSACTION,
        48.0,
        stale=True,
    )
    reconciliation = Reconciliation((finding,), ("unknown-preserved",), ())
    health = ArchiveHealth(4096, 8192, 1024, reconciliation)
    summary = examples.verification_catalog().last_full_verification
    assert summary is not None
    verification = {
        "degraded": False,
        "last_full_verification": summary.model_dump(mode="json"),
        "outstanding_failures": 0,
    }
    archive = {
        "archive_id": examples.ARCHIVE_ID,
        "root": str(root),
        "reachable": True,
        **health.as_payload(),
        "verification": verification,
        "quarantined_bytes": 0,
    }
    planned = PlannedRemediation(
        examples.TRANSACTION,
        "publication",
        "open",
        "staging_created",
        "quarantine_staging",
        "owned synthetic recovery evidence",
    )
    recovery = RecoveryPlan((planned,)).as_payload()
    quarantine_file = QuarantineFile(
        "tree/model.bin",
        0,
        examples.DIGEST,
        examples.TREE + "/model.bin",
        ObjectIdentity(0, 0, 0),
        (),
        (),
    )
    quarantine = QuarantineCleanupPlan(
        TransactionId(examples.TRANSACTION),
        "model:" + examples.REPOSITORY_ID,
        ".store/quarantine/" + examples.TRANSACTION,
        TransactionId(examples.PLAN),
        (quarantine_file,),
        ("tree",),
        already_absent=False,
    ).to_dict()
    applied_quarantine = quarantine | {
        "removed_files": 1,
        "removed_directories": 1,
        "removed_logical_bytes": 0,
    }
    repaired = RepairOutcome(
        examples.SHA,
        examples.at("2026-10-28T12:00:00.000000Z"),
        examples.REPLACEMENT,
        examples.PUBLICATION,
        "audit/retired/fixture.json",
        examples.TRANSACTION,
    ).as_payload()
    initialized = InitializationResult(
        queries.layout,
        examples.sentinel(),
        ("published",),
        adopted_published=False,
        removed_temporaries=(),
    ).as_payload()
    # Existing candidate service receives literal TOML, never synthesized from IR.
    content = (
        "schema_version=1\n[storage]\narchive_root="
        + json.dumps(str(root))
        + "\narchive_id="
        + json.dumps(examples.ARCHIVE_ID)
        + "\n"
    )
    valid = validate_candidate(content, config).data
    missing_config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": str(root / "missing-owned-tree"),
                "archive_id": examples.ARCHIVE_ID,
            },
        }
    )
    unreachable = LocalQueries(missing_config).archive_status().data["archive"]
    planned_repository, failure = _planned(
        client(FakeApi(tree=[Entry("README.md", 0)])),
        RepositoryConfig(type="model", id=examples.REPOSITORY_ID),
        config,
        cache_dir=queries.layout.hub_cache,
    )
    if failure is not None:
        message = "offline synthetic Hub fixture refused"
        raise ValueError(message)
    diagnostics = {
        "checks": [
            Check.passed("configuration", "owned fixture").as_entry(),
            Check.skipped("write_probe", "read-only fixture").as_entry(),
        ]
    }
    return {
        "VersionPayload": queries.version().data,
        "InspectionPayload": inspection,
        "HealthPayload": {"ready": True, "policy_valid": True, "archive": inspection},
        "ReadyHealthPayload": {"ready": True, "policy_valid": True, "archive": inspection},
        "UnavailableHealthPayload": {"ready": True, "policy_valid": None, "archive": None},
        "StatusPayload": queries.archive_status().data,
        "ReachableArchivePayload": archive,
        "UnreachableArchivePayload": unreachable,
        "RepositoriesPayload": queries.list_repositories().data,
        "RevisionsPayload": {"revisions": revisions},
        "EstimatePayload": VerificationEstimate(1, 1, 1, 0, 0, None).as_payload(),
        "RunsPayload": {"runs": [examples.RUN]},
        "ReferencePayload": {
            "locator_base": "published/",
            "reference": reference.model_dump(mode="json"),
        },
        "ManifestPayload": {
            "tree_base": "archive-root/",
            "manifest": examples.manifest().model_dump(mode="json"),
        },
        "ReportPayload": {"report": examples.run_report().model_dump(mode="json")},
        "InstalledValidationPayload": validate_config(config, token_source="not-resolved").data,
        "CandidateValidPayload": valid,
        "CandidateInvalidPayload": validate_candidate("invalid=toml=content", config).data,
        "DiagnosticsPayload": diagnostics,
        "PlanPayload": {"repositories": [planned_repository]},
        "PrunePayload": {
            "plans": [examples.prune_plan().model_dump(mode="json")],
            "applied": [examples.pruned_record().model_dump(mode="json")],
        },
        "PurgePayload": {"plans": [examples.purge_plan().model_dump(mode="json")], "applied": []},
        "RecoveryPlanPayload": recovery,
        "RecoveryAppliedPayload": recovery | {"applied": 1, "report": "runs/recovery.json"},
        "QuarantinePayload": {"plans": [quarantine], "applied": [applied_quarantine]},
        "RepairPayload": repaired,
        "InitializationPayload": initialized,
        "EmptyPayload": {},
    }


def serialized_corpus() -> list[dict[str, Any]]:  # noqa: PLR0915 - explicit independent source factories
    """Return strictly validated original serialized values for named decoders."""
    entries: list[dict[str, Any]] = []
    serial = 0

    def add(name, value):
        nonlocal serial
        serial += 1
        entries.append(
            {
                "case_id": f"source-{serial:04d}-{name}",
                "definition": name,
                "value": json.loads(json.dumps(value)),
            }
        )

    def model(value):
        if isinstance(value, BaseModel):
            add(type(value).__name__, value.model_dump(mode="json"))
            for name in type(value).model_fields:
                model(getattr(value, name))
        elif isinstance(value, (list, tuple)):
            for item in value:
                model(item)
        elif isinstance(value, dict):
            for item in value.values():
                model(item)

    for factory in (
        examples.manifest,
        examples.repair_manifest,
        examples.reference,
        examples.run_report,
        examples.verification_report,
        examples.prune_plan,
        examples.purge_plan,
        examples.pruned_record,
        examples.verification_catalog,
        examples.ui_asset_manifest,
        examples.ui_bootstrap,
        examples.host_status,
        examples.configuration_read,
        examples.managed_validation,
        examples.managed_assessment,
        examples.configuration_application_outcome,
    ):
        model(factory())
    model(PrunedRevision(commit_sha=examples.OTHER_SHA, logical_bytes=0, publication_generation=1))
    run = examples.run_report().model_dump(mode="json")
    recovery_fields = {
        key: value for key, value in run.items() if key not in {"repositories", "totals"}
    }
    recovery_fields["command"] = "recover --apply"
    recovery_fields["remediations"] = [
        Remediation(
            outcome="applied",
            reason="fixture",
            remedy="close_journal",
            transaction_id=examples.TRANSACTION,
        ).model_dump(mode="json")
    ]
    model(RecoveryReport.model_validate(recovery_fields))
    for value in _catalog_samples():
        model(value)
    for value in host_action_examples():
        model(value)
    model(examples.repository_card_read())
    missing_card = examples.repository_card().to_payload()
    missing_card.update(
        state="not_captured",
        captured_at=None,
        presentation_version=None,
        markdown=None,
        presentation_sha256=None,
        diagnostics=[],
    )
    model(RepositoryCardRead.model_validate(missing_card))
    model(
        Capabilities(
            api_version=1,
            credential_class="rest-writer",
            capabilities=("read", "write"),
            instance_id=examples.RUN,
            reads=True,
            operations=True,
            operation_history=True,
            mcp=False,
            maintenance_enabled=False,
            max_page_size=10000,
        )
    )
    operation = _operation()
    links = ClientLinks(
        status="/api/v1/operations/" + examples.RUN,
        result="/api/v1/operations/" + examples.RUN + "/result",
        events="/api/v1/operations/" + examples.RUN + "/events",
    )
    model(
        Acceptance(
            schema_version=1,
            request_id=examples.PLAN,
            archive_id=examples.ARCHIVE_ID,
            config_fingerprint=examples.FINGERPRINT,
            operation=operation,
            created=True,
            links=links,
        )
    )
    model(
        ClientEvents(
            operation_id=examples.RUN,
            events=(
                ClientEvent(
                    schema_version=1,
                    sequence=1,
                    at="2026-10-20T12:00:00Z",
                    kind="operation.admitted",
                    message="fixture",
                ),
            ),
            next_cursor=1,
            oldest_sequence=1,
            truncated=False,
        )
    )
    problem = ClientProblem(
        request_id=examples.RUN, code="HFMNT002", message="fixture refusal", exit_code=20
    )
    model(problem)
    add("ApiProblem", problem.model_dump(mode="json"))
    with TemporaryDirectory(prefix="hfcache-wire-corpus-") as temporary:
        payloads = _source_payloads(Path(temporary))
        payloads["OperationPayload"] = {"operation": operation.model_dump(mode="json")}
        payloads["OperationsPayload"] = {"operations": [operation.model_dump(mode="json")]}
        payloads["PlanResultPayload"] = payloads["PlanPayload"]
        for name, value in payloads.items():
            decoded = validate_payload(name, value)
            add(name, value)
            model(decoded)
        context = ExecutionContext(RunId(examples.RUN), datetime(2026, 10, 20, 12, tzinfo=UTC))
        envelope = ServiceResult(
            "version", payloads["VersionPayload"], warnings=(Problem("HFWRN003", "fixture"),)
        ).envelope(context, completed_at=datetime(2026, 10, 20, 12, 1, tzinfo=UTC))
        model(envelope)
        add(
            "ClientRead",
            {
                "schema_version": 1,
                "request_id": examples.PLAN,
                "archive_id": examples.ARCHIVE_ID,
                "config_fingerprint": examples.FINGERPRINT,
                "envelope": envelope.model_dump(mode="json"),
                "next_cursor": None,
            },
        )
    for name, value in request_samples().items():
        add(name, value)

    def request_model(value):
        if isinstance(value, BaseModel):
            add("Request" + type(value).__name__, value.model_dump(mode="json", exclude_none=True))
            for field in type(value).model_fields:
                request_model(getattr(value, field))
        elif isinstance(value, (list, tuple)):
            for item in value:
                request_model(item)

    request_model(managed_request())
    request_model(ConfigPreviewReference(operation_id=examples.RUN, key="owned-preview"))
    request_model(ObserverStopRequest.model_validate({"expected": EXPECTED}).expected)
    add("PlanResultPayload", examples.managed_assessment().model_dump(mode="json"))
    for name, report in (
        ("RunResultPayload", examples.run_report()),
        ("VerificationResultPayload", examples.verification_report()),
    ):
        value = report.model_dump(mode="json") | {"report": "runs/original.json"}
        validate_payload(name, value)
        add(name, value)
    first = {}
    for entry in entries:
        first.setdefault(entry["definition"], entry["value"])
    covered_route_modes()
    context = ExecutionContext(RunId(examples.RUN), datetime(2026, 10, 20, 12, tzinfo=UTC))
    for route in ROUTES:
        if route.response_kind == "acceptance":
            accepted = Acceptance(
                schema_version=1,
                request_id=examples.PLAN,
                archive_id=examples.ARCHIVE_ID,
                config_fingerprint=examples.FINGERPRINT,
                operation=_operation(route.path),
                created=True,
                links=links,
            )
            add("Acceptance", accepted.model_dump(mode="json"))
        else:
            payload = (
                first[route.success] if route.success is not None else first["RunResultPayload"]
            )
            command = route.commands[0] if route.commands else "sync"
            assert isinstance(payload, dict)
            envelope = ServiceResult(command, payload).envelope(
                context, completed_at=datetime(2026, 10, 20, 12, 1, tzinfo=UTC)
            )
            assert isinstance(payload, dict)
            response = ClientRead.model_validate(
                {
                    "schema_version": 1,
                    "request_id": examples.PLAN,
                    "archive_id": examples.ARCHIVE_ID,
                    "config_fingerprint": examples.FINGERPRINT,
                    "envelope": envelope.model_dump(mode="json"),
                    "next_cursor": None,
                }
            )
            add("ClientRead", response.model_dump(mode="json"))
    # Selection is metadata-only; no sample's fields or values come from the IR.
    allowed = build_contracts()["definitions"].keys()
    return [entry for entry in entries if entry["definition"] in allowed]


def covered_route_modes() -> set[tuple[str, str, str]]:
    """Source-known schema modes represented; this does not claim HTTP execution."""
    defaults = {
        "ui_bootstrap",
        "version",
        "capabilities",
        "health",
        "host_status",
        "host_observer",
        "schedule_outcome",
        "observer_outcome",
        "host_journal",
        "schedule_validate",
        "schedule_change",
        "observer_stop",
        "config_read",
        "config_outcome",
        "config_apply",
        "inspection",
        "status",
        "repositories",
        "revisions",
        "estimate",
        "runs",
        "report",
        "reference",
        "manifest",
        "repository_card",
        "operations",
        "operation_lookup",
        "operation",
        "operation_events",
        "catalog_search",
        "catalog_facets",
        "catalog_detail",
        "catalog_variants",
        "sync",
        "prune_preview",
        "prune_apply",
        "purge_preview",
        "purge_apply",
        "recovery_preview",
        "recovery_apply",
        "quarantine_preview",
        "quarantine_apply",
        "repair",
        "initialization",
        "catalog_refresh",
    }
    expected = {(name, "default") for name in defaults} | {
        ("operation_result", "by_original_operation"),
        ("plan", "installed"),
        ("plan", "literal_candidate"),
        ("plan", "managed"),
        ("config_validate", "installed"),
        ("config_validate", "literal_candidate"),
        ("config_validate", "managed"),
        ("diagnostics", "read_only"),
        ("diagnostics", "probe"),
        ("verification", "new"),
        ("verification", "full"),
        ("verification", "revision"),
    }
    if {(route.id, route.mode) for route in ROUTES} != expected:
        message = "Source-known route mode oracle needs explicit review"
        raise ValueError(message)
    bodies = request_samples()
    for route in ROUTES:
        if route.request_body is not None and "Request" + route.request_body not in bodies:
            message = "Missing explicit source request mode"
            raise ValueError(message)
        if route.success not in AUTHORITIES and route.success is not None:
            message = "Missing source response authority"
            raise ValueError(message)
    return {(route.method, route.path, route.mode) for route in ROUTES}


def _original_models() -> dict[str, type[BaseModel]]:
    result = {}
    for module in (
        "hfcache.card_models",
        "hfcache.catalog_models",
        "hfcache.catalog_query_models",
        "hfcache.catalog_refresh_models",
        "hfcache.client_models",
        "hfcache.models",
        "hfcache.manifests",
        "hfcache.reporting",
        "hfcache.wire_models",
        "hfcache.ui_models",
        "hfcache.host_models",
        "hfcache.host_actions_models",
        "hfcache.config_models",
        "hfcache.config",
    ):
        for value in vars(import_module(module)).values():
            if isinstance(value, type) and issubclass(value, BaseModel):
                result[value.__name__] = value
                result["Request" + value.__name__] = value
    for name, model in request_authorities().items():
        result["Request" + name] = model
        result["Request" + model.__name__] = model
    return result


def _malformed_candidates(value):
    """Independent JSON type substitutions, without consulting the exported IR."""
    yield from (None, False, [], {})
    if isinstance(value, dict):
        for field, original in value.items():
            if original is None:
                for replacement in (False, [], {}):
                    yield value | {field: replacement}
            elif isinstance(original, list) and not original:
                yield value | {field: [None]}
                yield value | {field: [{}]}
        for field in value:
            for replacement in (None, False, [], {}):
                yield value | {field: replacement}


def malformed_serialized_corpus() -> list[dict[str, Any]]:
    """At most 2,000 original-authority refusals, balanced across named models.

    This is a differential test oracle: accepted mutations are omitted rather
    than relabelled invalid. The values and substitutions never come from IR.
    """
    originals = {}
    for entry in serialized_corpus():
        originals.setdefault(entry["definition"], entry["value"])
    models = _original_models()
    candidates = {
        name: iter(_malformed_candidates(value)) for name, value in sorted(originals.items())
    }
    result = []
    seen = set()
    while candidates and len(result) < 2000:
        for name in tuple(candidates):
            candidate = next(candidates[name], ...)
            if candidate is ...:
                del candidates[name]
                continue
            identity = json.dumps([name, candidate], sort_keys=True)
            if identity in seen:
                continue
            seen.add(identity)
            try:
                if name in AUTHORITIES:
                    validate_payload(name, candidate)
                else:
                    models[name].model_validate(candidate)
            except ValueError, TypeError:
                result.append(
                    {
                        "case_id": f"source-negative-{len(result) + 1:04d}-{name}",
                        "definition": name,
                        "value": candidate,
                    }
                )
                if len(result) == 2000:
                    break
    return result
