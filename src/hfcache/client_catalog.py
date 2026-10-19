"""Pure catalog wire validation and bounded complete collections (decision 118/133)."""

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from hfcache.catalog_query_models import (
    CatalogEntry,
    CatalogFacetPayload,
    CatalogFacetValue,
    CatalogPayload,
    CatalogSearchPayload,
    CatalogVariantsPayload,
    QualifiedVariant,
)
from hfcache.catalog_refresh_models import CatalogRefreshResult
from hfcache.client_errors import ClientProtocolError
from hfcache.client_models import ClientRead, exact_version
from hfcache.errors import HfcacheError
from hfcache.models import serialize
from hfcache.redaction import redact_text

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from hfcache.reporting import Envelope

type CollectionPayload = CatalogSearchPayload | CatalogFacetPayload | CatalogVariantsPayload


@dataclass(frozen=True, slots=True)
class CatalogRead[PayloadT: CatalogPayload]:
    """Keep exact server evidence alongside its independently validated typed data."""

    response: ClientRead
    payload: PayloadT | None


@dataclass(frozen=True, slots=True)
class RefreshRead:
    """Exact observed operation evidence with a pure typed refresh payload when present."""

    response: ClientRead
    payload: CatalogRefreshResult | None


def validate_catalog[PayloadT: CatalogPayload](
    response: ClientRead,
    model: type[PayloadT],
    command: str,
) -> CatalogRead[PayloadT]:
    if (
        response.archive_id is None
        or response.config_fingerprint is None
        or response.envelope.command != command
        or (
            response.next_cursor is not None
            and (
                not response.next_cursor.isascii()
                or redact_text(response.next_cursor) != response.next_cursor
            )
        )
    ):
        raise ClientProtocolError
    if response.envelope.exit_code:
        if response.next_cursor is not None:
            raise ClientProtocolError
        return CatalogRead(response, None)
    try:
        exact_version(response.envelope.data.get("schema_version"))
        payload = model.model_validate(response.envelope.data)
    except ValueError, HfcacheError:
        raise ClientProtocolError from None
    coverage = payload.coverage
    known_missing = (
        coverage.tags_unknown
        + coverage.partial
        + coverage.unsupported
        + coverage.failed
        + coverage.missing
    )
    if (known_missing and not coverage.incomplete) or (
        coverage.incomplete != any(item.code == "HFWRN011" for item in response.envelope.warnings)
    ):
        raise ClientProtocolError
    if isinstance(payload, CatalogFacetPayload) and any(
        entry.repository_count == 0 for entry in payload.entries
    ):
        raise ClientProtocolError
    return CatalogRead(response, payload)


def validate_refresh(response: ClientRead) -> CatalogRefreshResult | None:
    if response.envelope.command != "catalog refresh" or response.next_cursor is not None:
        raise ClientProtocolError
    if not response.envelope.data:
        if not response.envelope.exit_code:
            raise ClientProtocolError
        return None
    try:
        exact_version(response.envelope.data.get("schema_version"))
        payload = CatalogRefreshResult.model_validate(response.envelope.data)
    except ValueError, HfcacheError:
        raise ClientProtocolError from None
    if payload.archive_id != response.archive_id:
        raise ClientProtocolError
    return payload


def _row_key(row: CatalogEntry | QualifiedVariant | CatalogFacetValue) -> tuple[Any, ...]:
    if isinstance(row, CatalogEntry):
        return row.repository_type, row.repository_id
    if isinstance(row, QualifiedVariant):
        return (
            row.publication_generation,
            row.commit_sha,
            row.publication_id,
            row.variant.variant_id,
        )
    return (row.value,)


def walk_catalog[PayloadT: CollectionPayload](  # noqa: PLR0912 - complete bounded cursor walk
    fetch: Callable[[str | None], CatalogRead[PayloadT]],
    *,
    maximum_pages: int,
    maximum_bytes: int,
    page_size: int,
    initial_cursor: str | None = None,
) -> Iterator[CatalogRead[PayloadT]]:
    """Require exact totals, stable full coverage/identity and strictly ordered distinct rows."""
    if initial_cursor is not None:
        raise ClientProtocolError  # complete collection starts at the beginning
    cursor = None
    seen: set[str] = set()
    identity = None
    previous = None
    count = budget = 0
    for _ in range(maximum_pages):
        page = fetch(cursor)
        response, payload = page.response, page.payload
        if response.envelope.exit_code:
            if (
                identity is not None
                and (response.archive_id, response.config_fingerprint, response.envelope.command)
                != identity[1:4]
            ):
                raise ClientProtocolError
            yield page
            return
        if payload is None or len(payload.entries) > page_size:
            raise ClientProtocolError
        current = (
            type(payload),
            response.archive_id,
            response.config_fingerprint,
            response.envelope.command,
            payload.catalog_identity,
            payload.coverage,
            payload.total_matches,
            payload.facet if isinstance(payload, CatalogFacetPayload) else None,
        )
        if identity is None:
            identity = current
        if current != identity:
            raise ClientProtocolError
        budget += len(json.dumps(response.envelope.data["entries"], ensure_ascii=True).encode())
        if budget > maximum_bytes:
            raise ClientProtocolError
        for row in payload.entries:
            key = _row_key(row)
            if previous is not None and key <= previous:
                raise ClientProtocolError
            previous = key
        count += len(payload.entries)
        if count > payload.total_matches:
            raise ClientProtocolError
        cursor = response.next_cursor
        if cursor is None:
            if count != payload.total_matches:
                raise ClientProtocolError
            yield page
            return
        if not payload.entries or cursor in seen:
            raise ClientProtocolError
        seen.add(cursor)
        yield page
    raise ClientProtocolError


def collect_catalog[PayloadT: CollectionPayload](
    pages: Iterator[CatalogRead[PayloadT]],
    *,
    maximum_bytes: int,
) -> Envelope:
    """Only completed collections become output; preserve the first invocation metadata."""
    first = None
    rows = []
    for page in pages:
        if page.response.envelope.exit_code:
            return page.response.envelope
        if first is None:
            first = page.response.envelope
        rows.extend(page.response.envelope.data["entries"])
    if first is None:
        raise ClientProtocolError
    result = first.model_copy(update={"data": first.data | {"entries": rows}})
    if len(serialize(result.to_payload()).encode()) > maximum_bytes:
        raise ClientProtocolError
    return result
