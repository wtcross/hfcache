"""Authenticated catalog read adapters; all semantics remain in the shared reader."""

from typing import TYPE_CHECKING, Any, Protocol

from fastapi import Request  # noqa: TC002 - FastAPI resolves route annotations
from starlette.responses import Response  # noqa: TC002 - FastAPI resolves return annotation

from hfcache.api.models import ReadResponse
from hfcache.catalog_query_models import (
    CatalogDetailPayload,
    CatalogFacetPayload,
    CatalogQuery,
    CatalogSearchPayload,
    CatalogVariantsPayload,
)
from hfcache.errors import RequestError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI

    from hfcache.services.catalog_queries import CatalogQueries
    from hfcache.services.mcp_queries import QueryPage

PREFIX = "/api/v1/catalog"
FILTERS = frozenset(
    {
        "type",
        "q",
        "tag_all",
        "tag_any",
        "tag_source",
        "scope",
        "revision_scope",
        "format",
        "quantization",
        "quantization_method",
        "bits",
        "max_variant_bytes",
        "limit",
        "cursor",
    }
)
EXACT = frozenset({"revision_scope", "commit_sha", "publication_id"})
REPEATED = {"tag_all": "tags_all", "tag_any": "tags_any"}
NUMBERS = frozenset({"bits", "max_variant_bytes", "limit"})
MAXIMUM_NUMBER_DIGITS = 19


class ExecuteCatalog(Protocol):
    async def __call__(
        self,
        request: Request,
        read: Callable[[CatalogQueries], QueryPage],
    ) -> Response: ...


def _arguments(request: Request, allowed: frozenset[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name, value in request.query_params.multi_items():
        if name not in allowed:
            raise RequestError
        key = REPEATED.get(name, "repository_type" if name == "type" else name)
        if name in REPEATED:
            values.setdefault(key, []).append(value)
        elif key in values:
            raise RequestError
        elif name in NUMBERS:
            if (
                not value.isascii()
                or not value.isdecimal()
                or len(value) > MAXIMUM_NUMBER_DIGITS
                or (value != "0" and value.startswith("0"))
            ):
                raise RequestError
            values[key] = int(value)
        else:
            values[key] = value
    return values


def _exact(request: Request, *, paged: bool) -> dict[str, Any]:
    values = _arguments(request, EXACT | {"limit", "cursor"} if paged else EXACT)
    sha, publication = values.get("commit_sha"), values.get("publication_id")
    if (sha is None) != (publication is None):
        raise RequestError
    if sha is not None and publication is not None:
        CommitSha(sha)
        PublicationId(publication)
    # Validate revision/page grammar before submitting work, including an empty result.
    CatalogQuery(
        **{
            key: value
            for key, value in values.items()
            if key not in {"commit_sha", "publication_id"}
        }
    )
    return values


def _parameter(name: str) -> dict[str, Any]:
    choices = {
        "type": ["model", "dataset"],
        "scope": ["archived", "configured", "all"],
        "revision_scope": ["current", "retained"],
        "tag_source": ["current_or_last_observed", "current_only"],
        "facet": ["tag", "format", "quantization_method", "quantization"],
    }
    if name in REPEATED:
        return {"type": "array", "items": {"type": "string", "maxLength": 128}, "maxItems": 64}
    if name in NUMBERS:
        return {
            "type": "integer",
            "minimum": 0 if name == "max_variant_bytes" else 1,
            "maximum": {"bits": 64, "limit": 10000, "max_variant_bytes": 2**63 - 1}[name],
            "description": "Canonical unsigned decimal; configured page ceiling also applies",
        }
    if name in choices:
        return {"type": "string", "enum": choices[name]}
    if name in {"commit_sha", "publication_id"}:
        return {
            "type": "string",
            "pattern": "^[0-9a-f]{" + ("40" if name == "commit_sha" else "32") + "}$",
        }
    return {"type": "string", "maxLength": 256 if name in {"q", "cursor"} else 64}


def _schema(model: type[Any], keys: frozenset[str]) -> dict[str, Any]:
    return {
        "x-catalog-payload": model.model_json_schema(),
        "parameters": [
            {
                "name": name,
                "in": "query",
                "required": name == "facet",
                "schema": _parameter(name),
            }
            for name in sorted(keys)
        ],
    }


def install_catalog_routes(app: FastAPI, execute: ExecuteCatalog) -> None:
    @app.get(
        PREFIX + "/search",
        response_model=ReadResponse,
        openapi_extra=_schema(CatalogSearchPayload, FILTERS),
    )
    async def search(request: Request) -> Response:
        query = CatalogQuery(**_arguments(request, FILTERS))
        return await execute(request, lambda reads: reads.search(query))

    @app.get(
        PREFIX + "/facets",
        response_model=ReadResponse,
        openapi_extra=_schema(CatalogFacetPayload, FILTERS | {"facet"}),
    )
    async def facets(request: Request) -> Response:
        values = _arguments(request, FILTERS | {"facet"})
        facet = values.pop("facet", None)
        if facet not in {"tag", "format", "quantization_method", "quantization"}:
            raise RequestError
        query = CatalogQuery(**values)
        return await execute(request, lambda reads: reads.facets(facet, query))

    @app.get(
        PREFIX + "/repositories/{repository_type}/{namespace}/{name}",
        response_model=ReadResponse,
        openapi_extra=_schema(CatalogDetailPayload, EXACT),
    )
    async def detail(request: Request, repository_type: str, namespace: str, name: str) -> Response:
        identity = RepositoryIdentity.of(repository_type, f"{namespace}/{name}")
        values = _exact(request, paged=False)
        return await execute(request, lambda reads: reads.detail(identity, **values))

    @app.get(
        PREFIX + "/repositories/{repository_type}/{namespace}/{name}/variants",
        response_model=ReadResponse,
        openapi_extra=_schema(CatalogVariantsPayload, EXACT | {"limit", "cursor"}),
    )
    async def variants(
        request: Request, repository_type: str, namespace: str, name: str
    ) -> Response:
        identity = RepositoryIdentity.of(repository_type, f"{namespace}/{name}")
        if identity.type != "model":
            raise RequestError
        values = _exact(request, paged=True)
        return await execute(request, lambda reads: reads.variants(identity, **values))
