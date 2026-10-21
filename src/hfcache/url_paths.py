"""Encode trusted raw application paths without changing their JSON identity."""

from pathlib import PurePosixPath
from urllib.parse import quote

_SAFE_PATH_CHARACTERS = "/:@[]!$&'()*+,;="


def uri_path(raw: str) -> str:
    """Return one canonical ASCII URI path, never a network-path reference.

    Configuration and domain authorities supply raw normalized paths. JSON links
    retain that spelling; Location and browser navigation use this UTF-8 encoding.
    Refuse already encoded or ambiguous input rather than normalizing it silently.
    """
    if (
        not isinstance(raw, str)
        or not raw.startswith("/")
        or raw.startswith("//")
        or not raw.isprintable()
        or any(character.isspace() or character in "?#\\%" for character in raw)
        or ".." in PurePosixPath(raw).parts
        or str(PurePosixPath(raw)) != (raw.removesuffix("/") if raw != "/" else "/")
    ):
        message = "application path must be a normalized absolute raw path"
        raise ValueError(message)
    return quote(raw, safe=_SAFE_PATH_CHARACTERS, encoding="utf-8", errors="strict")
