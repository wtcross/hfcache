"""Fixed REST route/mode authorities without transport startup (decision 145).

Request DTOs are lazy export-only imports. Operation results bind the original
public receipt route and command; they never select a replay target (INV-013).
"""

from dataclasses import dataclass
from importlib import import_module
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field, create_model

from hfcache import ui_models
from hfcache import wire_models as payloads
from hfcache.card_models import RepositoryCardRead
from hfcache.catalog_query_models import (
    CatalogDetailPayload,
    CatalogFacetPayload,
    CatalogSearchPayload,
    CatalogVariantsPayload,
)
from hfcache.catalog_refresh_models import CatalogRefreshResult
from hfcache.client_models import Acceptance, Capabilities, ClientEvents, ClientProblem, ClientRead
from hfcache.config_models import (
    ConfigApplicationOutcome,
    ConfigRead,
    ManagedAssessment,
    ManagedValidation,
)
from hfcache.host_actions_models import (
    HostJournalPage,
    HostObserverStatus,
    ObserverStopOutcome,
    ScheduleChangeOutcome,
    ScheduleValidation,
)
from hfcache.host_models import HostStatus
from hfcache.reporting import RunReport, VerificationReport


@dataclass(frozen=True, slots=True)
class FlatExtension:
    """Reuse final report models while declaring the existing flat locator field."""

    base: type[BaseModel]
    locator: str = "report"


AUTHORITIES: dict[str, Any] = {
    "ClientRead": ClientRead,
    "Acceptance": Acceptance,
    "ApiProblem": ClientProblem,
    "Capabilities": Capabilities,
    "HostStatus": HostStatus,
    "HostObserverStatus": HostObserverStatus,
    "HostJournalPage": HostJournalPage,
    "ObserverStopOutcome": ObserverStopOutcome,
    "ScheduleChangeOutcome": ScheduleChangeOutcome,
    "ScheduleValidation": ScheduleValidation,
    "RepositoryCardRead": RepositoryCardRead,
    "ConfigRead": ConfigRead,
    "ConfigApplicationOutcome": ConfigApplicationOutcome,
    "ManagedValidation": ManagedValidation,
    "ManagedAssessment": ManagedAssessment,
    "PlanResultPayload": payloads.PlanPayload | ManagedAssessment,
    "ClientEvents": ClientEvents,
    "HealthPayload": payloads.ReadyHealthPayload | payloads.UnavailableHealthPayload,
    "CatalogSearchPayload": CatalogSearchPayload,
    "CatalogFacetPayload": CatalogFacetPayload,
    "CatalogDetailPayload": CatalogDetailPayload,
    "CatalogVariantsPayload": CatalogVariantsPayload,
    "CatalogRefreshResult": CatalogRefreshResult,
    "RunResultPayload": FlatExtension(RunReport),
    "VerificationResultPayload": FlatExtension(VerificationReport),
    "VerificationReport": VerificationReport,
}
AUTHORITIES.update(
    (name, value)
    for name, value in vars(payloads).items()
    if isinstance(value, type)
    and issubclass(value, BaseModel)
    and value.__module__ == payloads.__name__
)
AUTHORITIES.update(
    (name, value)
    for name, value in vars(ui_models).items()
    if name.startswith("Ui")
    and name != "UiModel"
    and isinstance(value, type)
    and issubclass(value, BaseModel)
)


@dataclass(frozen=True, slots=True)
class Route:
    id: str
    method: str
    path: str
    mode: str
    response_kind: str
    commands: tuple[str, ...]
    success: str | None
    failure: tuple[str, ...] = ("EmptyPayload",)
    cursor: str = "none"
    binding_ids: tuple[str, ...] = ()
    request_body: str | None = None
    query_group: str = "none"


@dataclass(frozen=True, slots=True)
class ResultRoute:
    origin_path: str
    commands: tuple[str, ...]
    success: str
    failure: tuple[str, ...]
    binding_ids: tuple[str, ...] = ("operation.result",)


PREFIX = "/api/v1"


def _read(  # noqa: PLR0913 - fixed route declaration grammar
    name: str,
    path: str,
    command: str,
    model: str,
    *,
    paged: bool = False,
    query: str = "none",
    bindings: tuple[str, ...] = (),
    failures: tuple[str, ...] = ("EmptyPayload",),
) -> Route:
    return Route(
        name,
        "GET",
        PREFIX + path,
        "default",
        "read",
        (command,),
        model,
        failures,
        "opaque" if paged else "none",
        bindings,
        query_group=query,
    )


READ_ROUTES = (
    Route(
        "ui_bootstrap",
        "GET",
        "/ui/bootstrap.json",
        "default",
        "ui_bootstrap",
        (),
        "UiBootstrap",
        failure=(),
        binding_ids=("ui.bootstrap",),
    ),
    _read("version", "/version", "version", "VersionPayload"),
    _read("capabilities", "/capabilities", "capabilities", "Capabilities"),
    _read("health", "/health", "health", "HealthPayload"),
    _read("host_status", "/host/status", "host status", "HostStatus", bindings=("host.status",)),
    _read(
        "host_observer",
        "/host/sync-observer",
        "host observer status",
        "HostObserverStatus",
        bindings=("host.observer",),
    ),
    _read(
        "schedule_outcome",
        "/host/sync-schedule/changes/{operation_id}",
        "host schedule outcome",
        "ScheduleChangeOutcome",
        bindings=("host.outcome",),
    ),
    _read(
        "observer_outcome",
        "/host/sync-observer/stops/{operation_id}",
        "host observer outcome",
        "ObserverStopOutcome",
        bindings=("host.outcome",),
    ),
    _read(
        "host_journal",
        "/host/journal",
        "host journal",
        "HostJournalPage",
        paged=True,
        query="journal",
        bindings=("host.journal",),
    ),
    _read("config_read", "/config", "config read", "ConfigRead"),
    _read(
        "config_outcome",
        "/config/applications/{operation_id}",
        "config outcome",
        "ConfigApplicationOutcome",
    ),
    _read(
        "inspection",
        "/archive/inspection",
        "archive init",
        "InspectionPayload",
        failures=("InspectionPayload", "EmptyPayload"),
    ),
    _read("status", "/status", "status", "StatusPayload", paged=True, query="inventory"),
    _read(
        "repositories",
        "/repositories",
        "list",
        "RepositoriesPayload",
        paged=True,
        query="inventory",
    ),
    _read(
        "revisions",
        "/repositories/revisions",
        "list",
        "RevisionsPayload",
        paged=True,
        query="inventory",
    ),
    _read("estimate", "/verification/estimate", "verify --estimate", "EstimatePayload"),
    _read("runs", "/runs", "runs", "RunsPayload", paged=True, query="page"),
    _read("report", "/runs/{run_id}", "runs read", "ReportPayload", bindings=("run.report",)),
    _read(
        "reference",
        "/repositories/{repository_type}/{namespace}/{name}/references/{revision}",
        "reference read",
        "ReferencePayload",
        bindings=("publication.reference",),
    ),
    _read(
        "manifest",
        "/repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}",
        "manifest read",
        "ManifestPayload",
        bindings=("publication.manifest",),
    ),
    _read(
        "repository_card",
        "/repositories/{repository_type}/{namespace}/{name}/publications/{commit_sha}/{publication_id}/card",
        "card read",
        "RepositoryCardRead",
        bindings=("publication.card",),
    ),
    _read(
        "operations",
        "/operations",
        "operations list",
        "OperationsPayload",
        paged=True,
        query="page",
    ),
    _read(
        "operation_lookup",
        "/operations/lookup",
        "operations lookup",
        "OperationPayload",
        bindings=("operation.identity",),
    ),
    _read(
        "operation",
        "/operations/{operation_id}",
        "operations show",
        "OperationPayload",
        bindings=("operation.identity",),
    ),
    _read(
        "operation_events",
        "/operations/{operation_id}/events",
        "operations events",
        "ClientEvents",
        query="events",
        bindings=("operation.events",),
    ),
    Route(
        "operation_result",
        "GET",
        PREFIX + "/operations/{operation_id}/result",
        "by_original_operation",
        "operation_result",
        (),
        None,
        (),
        binding_ids=("operation.result",),
    ),
    _read(
        "catalog_search",
        "/catalog/search",
        "catalog.search",
        "CatalogSearchPayload",
        paged=True,
        query="catalog",
        bindings=("catalog.response",),
    ),
    _read(
        "catalog_facets",
        "/catalog/facets",
        "catalog.facets",
        "CatalogFacetPayload",
        paged=True,
        query="facets",
        bindings=("catalog.response", "catalog.facet"),
    ),
    _read(
        "catalog_detail",
        "/catalog/repositories/{repository_type}/{namespace}/{name}",
        "catalog.detail",
        "CatalogDetailPayload",
        query="exact",
        bindings=("catalog.response", "catalog.publication"),
    ),
    _read(
        "catalog_variants",
        "/catalog/repositories/{repository_type}/{namespace}/{name}/variants",
        "catalog.variants",
        "CatalogVariantsPayload",
        paged=True,
        query="variants",
        bindings=("catalog.response", "catalog.publication"),
    ),
)

REQUEST_MODELS = (
    {
        name: "hfcache.api.command_models:" + name
        for name in (
            "SyncSubmission",
            "PlanSubmission",
            "DiagnosticsSubmission",
            "VerificationSubmission",
            "ValidationSubmission",
            "CatalogRefreshSubmission",
        )
    }
    | {
        name: "hfcache.api.maintenance_models:" + name
        for name in (
            "PruneSubmission",
            "PurgeSubmission",
            "RecoverySubmission",
            "QuarantineSubmission",
            "RepairSubmission",
            "InitializationSubmission",
        )
    }
    | {"ConfigApplicationSubmission": "hfcache.config_models:ConfigApplicationSubmission"}
    | {
        name: "hfcache.host_actions_models:" + name
        for name in ("ScheduleValidationRequest", "ScheduleChangeRequest", "ObserverStopRequest")
    }
)


def request_authorities() -> dict[str, type[BaseModel]]:
    """Resolve schema-only DTOs deliberately during full development export."""
    result = {}
    for name, source in REQUEST_MODELS.items():
        module, attribute = source.split(":")
        model = getattr(import_module(module), attribute)
        if not isinstance(model, type) or not issubclass(model, BaseModel):
            message = "Request authority is not a Pydantic model"
            raise TypeError(message)
        result[name] = model
    commands = import_module("hfcache.api.command_models")
    result["InstalledPlan"] = result["SyncSubmission"]
    result["LiteralCandidatePlan"] = create_model(
        "LiteralCandidatePlan",
        __base__=result["SyncSubmission"],
        candidate=(commands.CandidateText, ...),
    )
    result["InstalledValidation"] = commands.InstalledValidationSubmission
    result["LiteralCandidateValidation"] = commands.CandidatePayload
    result["ManagedValidationRequest"] = create_model(
        "ManagedValidationRequest",
        __base__=commands.CommandModel,
        managed=(commands.ManagedEditRequest, ...),
    )
    result["ManagedPlanRequest"] = create_model(
        "ManagedPlanRequest",
        __base__=result["ManagedValidationRequest"],
        selectors=(
            Annotated[tuple[str, ...], BeforeValidator(payloads.as_tuple), Field(max_length=0)],
            (),
        ),
    )
    for name, read_only in (
        ("ReadOnlyDiagnostics", Literal[True]),
        ("ProbeDiagnostics", Literal[False]),
    ):
        result[name] = create_model(
            name, __base__=result["DiagnosticsSubmission"], read_only=(read_only, ...)
        )
    for mode, mode_type in (
        ("new", Literal["new"]),
        ("full", Literal["full"]),
        ("revision", Literal["revision"]),
    ):
        fields: dict[str, Any] = {"mode": (mode_type, ...)}
        fields["revision"] = (
            (str, Field(max_length=256)) if mode == "revision" else (type(None), None)
        )
        if mode != "new":
            fields["run_id"] = (type(None), None)
        result[mode.title() + "Verification"] = create_model(
            mode.title() + "Verification",
            __base__=result["VerificationSubmission"],
            **fields,
        )
    return result


_JOBS = (
    (
        "schedule_change",
        "/host/sync-schedule/changes",
        "host schedule change",
        "ScheduleChangeRequest",
        "ScheduleChangeOutcome",
        ("ScheduleChangeOutcome",),
    ),
    (
        "observer_stop",
        "/host/sync-observer/stops",
        "host observer stop",
        "ObserverStopRequest",
        "ObserverStopOutcome",
        ("ObserverStopOutcome",),
    ),
    (
        "config_apply",
        "/config/applications",
        "config apply",
        "ConfigApplicationSubmission",
        "ConfigApplicationOutcome",
        ("ConfigApplicationOutcome",),
    ),
    ("sync", "/syncs", "sync", "SyncSubmission", "RunResultPayload", ("RunResultPayload",)),
    ("plan", "/plans", "plan", "PlanSubmission", "PlanResultPayload", ("PlanResultPayload",)),
    (
        "diagnostics",
        "/diagnostics",
        "doctor",
        "DiagnosticsSubmission",
        "DiagnosticsPayload",
        ("DiagnosticsPayload",),
    ),
    (
        "verification",
        "/verifications",
        "verify",
        "VerificationSubmission",
        "VerificationResultPayload",
        ("VerificationResultPayload", "VerificationReport"),
    ),
    ("prune_preview", "/prune-plans", "prune --dry-run", "PruneSubmission", "PrunePayload", ()),
    ("prune_apply", "/prunes", "prune --apply", "PruneSubmission", "PrunePayload", ()),
    ("purge_preview", "/purge-plans", "purge --dry-run", "PurgeSubmission", "PurgePayload", ()),
    ("purge_apply", "/purges", "purge --apply", "PurgeSubmission", "PurgePayload", ()),
    (
        "recovery_preview",
        "/recovery-plans",
        "recover --dry-run",
        "RecoverySubmission",
        "RecoveryPlanPayload",
        ("RecoveryPlanPayload",),
    ),
    (
        "recovery_apply",
        "/recoveries",
        "recover --apply",
        "RecoverySubmission",
        "RecoveryAppliedPayload",
        ("RecoveryPlanPayload", "RecoveryAppliedPayload"),
    ),
    (
        "quarantine_preview",
        "/quarantine-plans",
        "quarantine --dry-run",
        "QuarantineSubmission",
        "QuarantinePayload",
        (),
    ),
    (
        "quarantine_apply",
        "/quarantine-cleanups",
        "quarantine --apply",
        "QuarantineSubmission",
        "QuarantinePayload",
        (),
    ),
    ("repair", "/repairs", "repair", "RepairSubmission", "RepairPayload", ()),
    (
        "initialization",
        "/archive/initializations",
        "archive init",
        "InitializationSubmission",
        "InitializationPayload",
        ("InspectionPayload",),
    ),
    (
        "catalog_refresh",
        "/catalog/refreshes",
        "catalog refresh",
        "CatalogRefreshSubmission",
        "CatalogRefreshResult",
        ("CatalogRefreshResult",),
    ),
)


def job_routes() -> tuple[Route, ...]:
    result = []
    for name, path, command, request, _, _ in _JOBS:
        modes = {
            "plan": ("installed", "literal_candidate", "managed"),
            "diagnostics": ("read_only", "probe"),
            "verification": ("new", "full", "revision"),
        }.get(name, ("default",))
        for mode in modes:
            commands = (f"verify --{mode}",) if name == "verification" else (command,)
            mode_request = {
                ("plan", "installed"): "InstalledPlan",
                ("plan", "literal_candidate"): "LiteralCandidatePlan",
                ("plan", "managed"): "ManagedPlanRequest",
                ("diagnostics", "read_only"): "ReadOnlyDiagnostics",
                ("diagnostics", "probe"): "ProbeDiagnostics",
                ("verification", "new"): "NewVerification",
                ("verification", "full"): "FullVerification",
                ("verification", "revision"): "RevisionVerification",
            }.get((name, mode), request)
            result.append(
                Route(
                    name,
                    "POST",
                    PREFIX + path,
                    mode,
                    "acceptance",
                    commands,
                    "Acceptance",
                    (),
                    request_body=mode_request,
                )
            )
    return tuple(result)


ROUTES = (
    READ_ROUTES
    + job_routes()
    + (
        Route(
            "schedule_validate",
            "POST",
            PREFIX + "/host/sync-schedule/validations",
            "default",
            "read",
            ("host schedule validate",),
            "ScheduleValidation",
            binding_ids=("host.validation",),
            request_body="ScheduleValidationRequest",
        ),
        Route(
            "config_validate",
            "POST",
            PREFIX + "/config/validate",
            "installed",
            "read",
            ("config validate",),
            "InstalledValidationPayload",
            request_body="InstalledValidation",
        ),
        Route(
            "config_validate",
            "POST",
            PREFIX + "/config/validate",
            "literal_candidate",
            "read",
            ("config validate",),
            "CandidateValidPayload",
            ("CandidateInvalidPayload",),
            request_body="LiteralCandidateValidation",
        ),
        Route(
            "config_validate",
            "POST",
            PREFIX + "/config/validate",
            "managed",
            "read",
            ("config validate",),
            "ManagedValidation",
            request_body="ManagedValidationRequest",
        ),
    )
)
RESULT_ROUTES = tuple(
    ResultRoute(
        PREFIX + path,
        (f"verify --{mode}" if name == "verification" else command,),
        success,
        (*failure, "EmptyPayload"),
    )
    for name, path, command, _, success, failure in _JOBS
    for mode in (("new", "full", "revision") if name == "verification" else ("default",))
)


def validate_payload(name: str, value: object) -> object:
    """Independent Python model authority for serializer/oracle tests."""
    from pydantic import TypeAdapter  # noqa: PLC0415 - preserve cheap pure registry import

    authority = AUTHORITIES[name]
    if isinstance(authority, FlatExtension):
        if not isinstance(value, dict) or authority.locator not in value:
            message = "Missing report locator"
            raise ValueError(message)
        locator = TypeAdapter(payloads.ArchivePath).validate_python(value[authority.locator])
        base = authority.base.model_validate(
            {key: item for key, item in value.items() if key != authority.locator}
        )
        return base.model_dump(mode="json") | {authority.locator: locator}
    return TypeAdapter(authority).validate_python(value)
