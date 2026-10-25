"""Authenticated UI projections and separately bounded immutable body streams."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from starlette.responses import Response

from hfcache.api.auth import AdminCapability, AuthenticationMethod, CredentialClass
from hfcache.errors import SafetyError
from hfcache.models import dump
from hfcache.ui_models import (
    UiAdminPermission,
    UiBootstrap,
    UiBuildIdentity,
    UiPaths,
    UiUser,
)
from hfcache.url_paths import uri_path

if TYPE_CHECKING:
    from starlette.types import Receive, Scope, Send

    from hfcache.api.auth import Principal
    from hfcache.api.ui_assets import UiCapture
    from hfcache.server_config import InstalledPolicy, ServerConfig

MAX_ACTIVE_STREAMS = 16
MAX_CHUNK_BYTES = 65536
STREAM_DEADLINE_SECONDS = 30.0
MAX_BOOTSTRAP_BYTES = 32768
UI_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
    "font-src 'self'; connect-src 'self'; base-uri 'self'; object-src 'none'; "
    "frame-ancestors 'none'; form-action 'none'; worker-src 'none'"
)
UI_PERMISSIONS = "camera=(), microphone=(), geolocation=()"


def unavailable() -> SafetyError:
    message = "UI response service is full or draining"
    return SafetyError.single(message, code="HFAPI009")


@dataclass(slots=True)
class UiLease:
    owner: UiStreams
    released: bool = False

    def release(self) -> None:
        if not self.released:
            self.released = True
            self.owner.active -= 1
            if not self.owner.active:
                self.owner._idle.set()  # noqa: SLF001 - lease and owner are one admission lifetime


class UiStreams:
    """Event-loop-owned admission: no queued awaiters and no metadata-pool work."""

    def __init__(self) -> None:
        self.active = 0
        self.accepting = True
        self.tasks: set[asyncio.Task[None]] = set()
        self._idle = asyncio.Event()
        self._idle.set()

    def acquire(self) -> UiLease:
        if not self.accepting or self.active >= MAX_ACTIVE_STREAMS:
            raise unavailable()
        self.active += 1
        self._idle.clear()
        return UiLease(self)

    def stop_admission(self) -> None:
        self.accepting = False

    async def aclose(self) -> None:
        self.stop_admission()
        await self._idle.wait()


async def _finish_tasks(tasks: tuple[asyncio.Task[None], ...]) -> None:
    for task in tasks:
        if not task.done():
            task.cancel()
    joined = asyncio.gather(*tasks, return_exceptions=True)
    cancelled = False
    while not joined.done():
        try:
            await asyncio.shield(joined)
        except asyncio.CancelledError:
            cancelled = True
    joined.result()
    if cancelled:
        raise asyncio.CancelledError


class UiResponse(Response):
    """One selected captured body; send chunks and the header under one deadline."""

    def __init__(self, body: bytes, *, mime: str, policy: str, streams: UiStreams) -> None:
        super().__init__(content=body, media_type=mime)
        self.policy = policy
        self.streams = streams

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.setdefault("state", {})["ui_response_class"] = self.policy
        if scope["method"] == "HEAD":
            if not self.streams.accepting:
                raise unavailable()
            async with asyncio.timeout(STREAM_DEADLINE_SECONDS):
                await send(
                    {
                        "type": "http.response.start",
                        "status": self.status_code,
                        "headers": self.raw_headers,
                    }
                )
                await send({"type": "http.response.body", "body": b""})
            return
        lease = self.streams.acquire()

        async def stream() -> None:
            await send(
                {
                    "type": "http.response.start",
                    "status": self.status_code,
                    "headers": self.raw_headers,
                }
            )
            for offset in range(0, len(self.body), MAX_CHUNK_BYTES):
                await send(
                    {
                        "type": "http.response.body",
                        "body": self.body[offset : offset + MAX_CHUNK_BYTES],
                        "more_body": True,
                    }
                )
            await send({"type": "http.response.body", "body": b"", "more_body": False})

        async def disconnect() -> None:
            while (await receive())["type"] != "http.disconnect":
                pass

        sender = asyncio.create_task(stream(), name="hfcache-ui-send")
        observer = asyncio.create_task(disconnect(), name="hfcache-ui-disconnect")
        self.streams.tasks.update((sender, observer))
        try:
            async with asyncio.timeout(STREAM_DEADLINE_SECONDS):
                done, _ = await asyncio.wait(
                    (sender, observer), return_when=asyncio.FIRST_COMPLETED
                )
                if sender in done:
                    await sender
                else:
                    await observer
        finally:
            try:
                await _finish_tasks((sender, observer))
            finally:
                self.streams.tasks.difference_update((sender, observer))
                lease.release()


def bootstrap_bytes(  # noqa: PLR0913 - independently sourced configured/build/principal identities
    capture: UiCapture,
    server: ServerConfig,
    policy: InstalledPolicy,
    principal: Principal,
    *,
    instance_id: str,
    effective_prefix: str,
) -> bytes:
    """Configured identity only: no policy reload, archive query, helper or Hub call."""
    if (
        server.basic is None
        or principal.subject is None
        or principal.authentication_method is not AuthenticationMethod.BASIC
        or principal.credential_class is not CredentialClass.REST_WRITER
    ):
        raise unavailable()
    permissions = tuple(
        UiAdminPermission.model_validate(
            {
                "capability": capability.value,
                "granted": capability in principal.admin_capabilities,
                "effective": capability is AdminCapability.HOST_READ
                and capability in principal.admin_capabilities,
                "reason": "allowed"
                if capability is AdminCapability.HOST_READ
                and capability in principal.admin_capabilities
                else "feature_unavailable"
                if capability in principal.admin_capabilities
                else "not_granted",
            }
        )
        for capability in sorted(AdminCapability, key=lambda value: value.value)
    )
    result = UiBootstrap(
        schema_version=1,
        kind="hfcache_ui_bootstrap",
        ui_contract_version=1,
        rest_api_schema_version=1,
        wire_source_digest=capture.manifest.build.wire_source_digest,
        instance_id=instance_id,
        authority_epoch=instance_id,
        configured_archive_id=policy.archive_id,
        archive_identity_source="installed_policy",
        config_fingerprint=None,
        configured_origin=server.basic.origin,
        paths=UiPaths(
            public_prefix=server.listener.root_path,
            effective_prefix=effective_prefix,
            ui_base=uri_path(effective_prefix + "/ui/"),
            bootstrap=uri_path(effective_prefix + "/ui/bootstrap.json"),
            api_base=uri_path(effective_prefix + "/api/v1"),
            mcp_base=uri_path(effective_prefix + "/mcp/") if server.mcp_enabled else None,
        ),
        user=UiUser(
            subject=principal.subject,
            display_name=principal.subject,
            authentication_method="basic",
            credential_class="rest-writer",
            rest_capabilities=("read", "write"),
            admin_permissions=permissions,
        ),
        build=UiBuildIdentity(
            asset_manifest_sha256=capture.fingerprint, metadata=capture.manifest.build
        ),
    )
    encoded = dump(result)
    if len(encoded) > MAX_BOOTSTRAP_BYTES:
        raise unavailable()
    return encoded
