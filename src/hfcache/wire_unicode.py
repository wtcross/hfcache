"""Build-only exact Unicode tables for browser validation (decision 145).

The Python archive authority uses Unicode 16 NFC followed by full casefold. Browser
engines may carry a different Unicode release, so native normalization is not its
oracle. This pure export reads no filesystem, policy, credentials or archive.
"""

import json
import unicodedata
from functools import cache

UNICODE_VERSION = "16.0.0"
_HANGUL_START = 0xAC00
_HANGUL_END = 0xD7A4
_COMPOSITION_PAIR_LENGTH = 2


@cache
def unicode_bytes() -> bytes:
    """Return deterministic tables; a Python Unicode upgrade requires explicit review."""
    if unicodedata.unidata_version != UNICODE_VERSION:
        message = "browser Unicode authority requires a reviewed version update"
        raise ValueError(message)
    combining: dict[str, int] = {}
    decompositions: dict[str, list[int]] = {}
    compositions: dict[str, int] = {}
    casefold: dict[str, str] = {}
    nonprintable: list[list[int]] = []
    for point in range(0x110000):
        character = chr(point)
        if not character.isprintable():
            if nonprintable and nonprintable[-1][1] == point - 1:
                nonprintable[-1][1] = point
            else:
                nonprintable.append([point, point])
        if order := unicodedata.combining(character):
            combining[str(point)] = order
        decomposition = unicodedata.decomposition(character)
        # Hangul uses the normative arithmetic algorithm in the browser.
        if (
            decomposition
            and not decomposition.startswith("<")
            and not _HANGUL_START <= point < _HANGUL_END
        ):
            points = [int(item, 16) for item in decomposition.split()]
            decompositions[str(point)] = points
            if (
                len(points) == _COMPOSITION_PAIR_LENGTH
                and unicodedata.normalize("NFC", "".join(chr(item) for item in points)) == character
            ):
                compositions[",".join(str(item) for item in points)] = point
        folded = character.casefold()
        if folded != character:
            casefold[str(point)] = folded
    return (
        json.dumps(
            {
                "schema_version": 1,
                "unicode_version": UNICODE_VERSION,
                "combining": combining,
                "decompositions": decompositions,
                "compositions": compositions,
                "casefold": casefold,
                "nonprintable": nonprintable,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
