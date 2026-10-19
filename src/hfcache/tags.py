"""Pure operator-tag normalization shared by configuration and discovery (INV-018)."""

import re
from typing import Annotated

from pydantic import BeforeValidator, Field

MAXIMUM_TAGS = 64
MAXIMUM_RAW_TAG_LENGTH = 128

_TAG = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,63}")
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def normalize_tags(value: object) -> tuple[str, ...]:
    """Validate before deduplication; rejected contents never enter diagnostics."""
    if not isinstance(value, (list, tuple)) or len(value) > MAXIMUM_TAGS:
        msg = "tags must be a list or tuple of at most 64 strings"
        raise ValueError(msg)
    tags: set[str] = set()
    for raw in value:
        if not isinstance(raw, str) or len(raw) > MAXIMUM_RAW_TAG_LENGTH:
            msg = "each tag must be a string of at most 128 raw characters"
            raise ValueError(msg)
        canonical = raw.strip(" ").translate(_ASCII_LOWER)
        if not _TAG.fullmatch(canonical):
            msg = "each canonical tag must match [a-z0-9][a-z0-9._:/-]{0,63}"
            raise ValueError(msg)
        tags.add(canonical)
    return tuple(sorted(tags))


Tags = Annotated[tuple[str, ...], BeforeValidator(normalize_tags), Field(max_length=MAXIMUM_TAGS)]
