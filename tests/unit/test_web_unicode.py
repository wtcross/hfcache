"""Independent Unicode source identities and exact pinned browser table export."""

import gzip
import hashlib
import json
import unicodedata
from pathlib import Path

import pytest

from hfcache.wire_unicode import UNICODE_VERSION, unicode_bytes

ROOT = Path(__file__).resolve().parents[2]


def test_unicode_export_is_deterministic_and_uses_the_reviewed_python_authority():
    raw = unicode_bytes()
    assert unicode_bytes() == raw
    assert raw == (ROOT / "web/src/wire/unicode-data.json").read_bytes()
    payload = json.loads(raw)
    assert payload["schema_version"] == 1
    assert payload["unicode_version"] == UNICODE_VERSION == "16.0.0"
    assert {
        name: len(payload[name])
        for name in ("combining", "decompositions", "compositions", "casefold")
    } == {"combining": 934, "decompositions": 2081, "compositions": 961, "casefold": 1557}
    assert payload["casefold"]["223"] == "ss"
    assert payload["casefold"]["64257"] == "fi"
    assert payload["decompositions"]["233"] == [101, 769]
    assert payload["compositions"]["101,769"] == 233
    assert str(0xAC00) not in payload["decompositions"]
    # Exercise every point against Python, independently expanding compact ranges.
    excluded = {point for start, end in payload["nonprintable"] for point in range(start, end + 1)}
    assert all((point not in excluded) == chr(point).isprintable() for point in range(0x110000))


def test_unicode_authority_upgrade_requires_deliberate_review(monkeypatch):
    unicode_bytes.cache_clear()
    with monkeypatch.context() as change:
        change.setattr(unicodedata, "unidata_version", "future")
        with pytest.raises(ValueError, match="reviewed version"):
            unicode_bytes()
    unicode_bytes.cache_clear()


@pytest.mark.parametrize(
    ("path", "digest", "compressed"),
    [
        (
            "tests/fixtures/unicode16/NormalizationTest.txt.gz",
            "d811971453e7075e1ad56fb1b301eece5aa80757b81f6156e74a1bfb3ae5ceb1",
            True,
        ),
        (
            "tests/fixtures/unicode16/CaseFolding.txt.gz",
            "6f1f9c588eb4a5c718d9e8f93b782685e5c7fec872cf05e8e6878053599e09bb",
            True,
        ),
        (
            "web/dependencies/UNICODE-LICENSE.txt",
            "e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96",
            False,
        ),
    ],
)
def test_official_unicode_vectors_and_license_keep_exact_original_bytes(path, digest, compressed):
    raw = (ROOT / path).read_bytes()
    if compressed:
        raw = gzip.decompress(raw)
    assert hashlib.sha256(raw).hexdigest() == digest
