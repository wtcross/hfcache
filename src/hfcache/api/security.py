"""Optional FastAPI bearer integration over application-owned verification.

API-005 provides reusable authentication dependencies only. API-006 wires them
to every route; this module starts no application, listener or endpoint.
"""

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from hfcache.api.auth import (
    AuthenticationError,
    AuthorizationError,
    Capability,
    CredentialRegistry,
    Principal,
    require_capability,
)


class BearerAuthentication(HTTPBearer):
    """Use FastAPI's schema integration while retaining strict application validation."""

    def __init__(self, registry: CredentialRegistry) -> None:
        super().__init__(auto_error=False, scheme_name="hfcacheBearer")
        self.registry = registry

    async def __call__(self, request: Request) -> Principal:
        try:
            values = request.headers.getlist("authorization")
            # Validate the original bounded field before the framework extractor
            # can trim whitespace or normalize malformed input (INV-013).
            principal = self.registry.authenticate(values[0] if len(values) == 1 else None)
            await super().__call__(request)
        except AuthenticationError as exc:
            raise HTTPException(exc.status_code, exc.detail, headers=dict(exc.headers)) from None
        return principal


class RequireCapability:
    """One reusable FastAPI dependency; no endpoint can create a stronger principal."""

    def __init__(self, authentication: BearerAuthentication, capability: Capability) -> None:
        self.authentication = authentication
        self.capability = capability

    async def __call__(self, request: Request) -> Principal:
        principal = await self.authentication(request)
        try:
            return require_capability(principal, self.capability)
        except AuthorizationError as exc:
            raise HTTPException(exc.status_code, exc.detail, headers=dict(exc.headers)) from None
