"""Local bootstrap descriptions without archive or credential execution (decision 120)."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from importlib.util import find_spec
from typing import TYPE_CHECKING

from hfcache.reporting import RuntimeVersions
from hfcache.services.context import ServiceResult

if TYPE_CHECKING:
    from hfcache.config import ApplicationConfig


def query_version() -> ServiceResult:
    """Report the installed stack without reading configuration or archive state."""
    versions = RuntimeVersions.measured()
    backend = "http"
    if find_spec("hf_xet") is not None:
        try:
            backend = f"xet {package_version('hf-xet')}"
        except PackageNotFoundError:  # pragma: no cover - broken installation
            backend = "xet unknown"
    return ServiceResult(
        "version",
        {
            "application": versions.application,
            "huggingface_hub": versions.huggingface_hub,
            "python": versions.python,
            "transfer_backend": backend,
        },
    )


def validate_config(config: ApplicationConfig, *, token_source: str) -> ServiceResult:
    """Describe already validated policy and nonsecret credential source.

    Credential resolution belongs to the trusted execution boundary; the read
    capability never receives the resolver or token (AD-21, decision 108).
    """
    return ServiceResult(
        "config validate",
        {
            "config_fingerprint": config.fingerprint(),
            "enabled_repositories": len(config.enabled_repositories),
            "repositories": len(config.repositories),
            "token_source": token_source,
        },
    )
