"""Reading bytes and saying what they are.

`AD-18` is why this exists at all: a digest is what the writer computed from the
bytes on this dataset, never an identifier the Hub supplied. The tests therefore
check the digest against the standard library's own answer rather than against a
value copied from anywhere.
"""

import hashlib
from typing import TYPE_CHECKING

import pytest

from hfcache.errors import ExitCode, IntegrityError, SynchronizationError
from hfcache.hashing import CHUNK_BYTES, DIGEST_ALGORITHM, sha256_file
from hfcache.taxonomy import classify

if TYPE_CHECKING:
    from pathlib import Path


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


def test_the_only_algorithm_schema_version_one_permits():
    assert DIGEST_ALGORITHM == "sha256"


def test_a_file_is_hashed_and_measured_in_one_read(tmp_path: Path):
    payload = b"the bytes that were actually published\n"
    target = tmp_path / "model.safetensors"
    target.write_bytes(payload)

    result = sha256_file(target)

    assert result.digest == hashlib.sha256(payload).hexdigest()
    assert result.size == len(payload)


def test_an_empty_file_hashes_to_the_empty_digest(tmp_path: Path):
    target = tmp_path / "empty"
    target.write_bytes(b"")

    result = sha256_file(target)

    assert result.digest == hashlib.sha256(b"").hexdigest()
    assert result.size == 0


def test_a_file_larger_than_one_chunk_is_streamed_correctly(tmp_path: Path):
    # Memory is bounded regardless of size, which matters because the largest
    # objects here are exactly the ones that would not fit.
    payload = bytes(range(256)) * ((CHUNK_BYTES // 256) + 7)
    target = tmp_path / "large.bin"
    target.write_bytes(payload)

    result = sha256_file(target)

    assert result.size > CHUNK_BYTES
    assert result.digest == hashlib.sha256(payload).hexdigest()


def test_an_unreadable_object_is_reported_with_the_callers_code(tmp_path: Path):
    with pytest.raises(IntegrityError) as caught:
        sha256_file(tmp_path / "absent")

    assert codes(caught.value.problems) == ["HFVER006"]
    assert caught.value.exit_code == ExitCode.INTEGRITY


def test_the_code_is_the_callers_because_the_same_failure_means_different_things(
    tmp_path: Path,
):
    # `HFVER006` while `verify` reads the archive; a synchronization code while a
    # run is ingesting.
    with pytest.raises(SynchronizationError) as caught:
        sha256_file(tmp_path / "absent", error=SynchronizationError, code="HFSYN005")

    assert codes(caught.value.problems) == ["HFSYN005"]


def test_the_error_class_travels_with_the_code_so_the_exit_agrees_with_it(tmp_path: Path):
    # The exit an error carries comes from its class; the classification
    # `docs/cli.md` §5 publishes comes from the code's family. An ingestion
    # failure raised as `IntegrityError` would exit `40` and tell an operator the
    # archive is corrupt when a download failed.
    with pytest.raises(SynchronizationError) as caught:
        sha256_file(tmp_path / "absent", error=SynchronizationError, code="HFSYN009")

    assert caught.value.exit_code == classify("HFSYN009") == ExitCode.SYNC


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (IntegrityError, "HFVER006"),
        (SynchronizationError, "HFSYN005"),
        (SynchronizationError, "HFSYN009"),
    ],
)
def test_every_call_site_pairs_a_code_with_the_class_the_taxonomy_gives_it(
    tmp_path: Path, error, code
):
    # One case per pairing used in `src/`. A new pairing that disagreed with the
    # taxonomy fails here rather than at exit time during an incident.
    with pytest.raises(error) as caught:
        sha256_file(tmp_path / "absent", error=error, code=code)

    assert caught.value.exit_code == classify(code)
