"""Exact schemes, bounded hostile headers, declared shard completeness (V15-19)."""

import os
import struct

import pytest

from hfcache.catalog_extractors import ExtractionBudget
from hfcache.catalog_gguf import extract_gguf
from hfcache.catalog_models import variant_identity
from tests.fixtures.gguf import gguf, split, string
from tests.unit.test_catalog_extractors import publication


@pytest.mark.parametrize(
    ("file_type", "encoding", "kind"),
    [
        (0, "F32", 0),
        (1, "F16", 1),
        (2, "Q4_0", 2),
        (3, "Q4_1", 3),
        (7, "Q8_0", 8),
        (8, "Q5_0", 6),
        (9, "Q5_1", 7),
        (10, "Q2_K", 10),
        (11, "Q3_K_S", 11),
        (12, "Q3_K_M", 11),
        (13, "Q3_K_L", 11),
        (14, "Q4_K_S", 12),
        (15, "Q4_K_M", 12),
        (16, "Q5_K_S", 13),
        (17, "Q5_K_M", 13),
        (18, "Q6_K", 14),
        (19, "IQ2_XXS", 16),
        (20, "IQ2_XS", 17),
        (21, "Q2_K_S", 10),
        (22, "IQ3_XS", 18),
        (23, "IQ3_XXS", 18),
        (24, "IQ1_S", 19),
        (25, "IQ4_NL", 20),
        (26, "IQ3_S", 21),
        (27, "IQ3_M", 21),
        (28, "IQ2_S", 22),
        (29, "IQ2_M", 22),
        (30, "IQ4_XS", 23),
        (31, "IQ1_M", 29),
        (32, "BF16", 30),
    ],
)
def test_pinned_file_type_mapping_not_tensor_type_or_filename(tmp_path, file_type, encoding, kind):
    raw, _ = gguf(
        {"general.file_type": (4, file_type), "general.architecture": (8, "llama")},
        tensors=[("weight", (256,), kind, 0)],
    )
    result = extract_gguf(publication(tmp_path, {"misleading-Q4_K_M.gguf": raw}))
    assert result.status == "complete"
    (variant,) = result.variants
    assert variant.encoding == encoding
    assert variant.role == "primary"
    assert variant.completeness == "complete"
    assert variant.variant_id == variant_identity(variant.members)
    assert variant.total_bytes == len(raw)
    if file_type in {0, 1, 32}:
        assert variant.quantization is None
        assert variant.quantization_method is None
    else:
        assert variant.quantization == encoding
        assert variant.quantization_method == "ggml"
    if file_type == 15:
        assert variant.bits is None


@pytest.mark.parametrize("file_type", [None, 4, 5, 6, 33, 1024, 99999])
def test_missing_unknown_removed_or_guessed_file_type_stays_candidate(tmp_path, file_type):
    metadata = {"general.architecture": (8, "llama")}
    if file_type is not None:
        metadata["general.file_type"] = (4, file_type)
    raw, _ = gguf(metadata)
    result = extract_gguf(publication(tmp_path, {"definitely-Q4_K_M.gguf": raw}))
    assert result.status == "unsupported"
    (variant,) = result.variants
    assert variant.quantization is None
    assert variant.completeness != "complete"


def test_os_source_reads_never_fetch_padding_or_tensor_bytes(tmp_path, monkeypatch):
    raw, header_end = gguf()
    access = publication(tmp_path, {"model.gguf": raw})
    original = os.fdopen
    reads = []

    def exact_stream(fd, *args, **kwargs):
        assert kwargs.get("buffering") == 0
        stream = original(fd, *args, **kwargs)
        read = stream.read

        def checked(count=-1):
            assert 0 <= count <= header_end - stream.tell()
            data = read(count)
            reads.append(len(data))
            return data

        monkeypatch.setattr(stream, "read", checked)
        return stream

    monkeypatch.setattr(os, "fdopen", exact_stream)
    result = extract_gguf(access)
    assert result.status == "complete"
    assert sum(reads) == header_end == access.budget.read_bytes


def test_normal_split_uses_first_header_only_and_exact_complete_members(tmp_path):
    one, _ = split(0)
    two, _ = split(1)
    result = extract_gguf(
        publication(tmp_path, {"model-00001-of-00002.gguf": one, "model-00002-of-00002.gguf": two})
    )
    (variant,) = result.variants
    assert result.status == "complete"
    assert variant.quantization == "Q4_K_M"
    assert variant.completeness == "complete"
    assert variant.source_paths == ("model-00001-of-00002.gguf",)
    assert len(variant.members) == 2
    assert variant.total_bytes == len(one) + len(two)


def test_header_only_first_split_is_allowed_but_zero_tensor_standalone_is_unknown(tmp_path):
    first, _ = split(0, total=1, name="")
    second, _ = split(1, total=1)
    result = extract_gguf(
        publication(tmp_path, {"m-00001-of-00002.gguf": first, "m-00002-of-00002.gguf": second})
    )
    assert result.variants[0].completeness == "complete"
    raw, _ = gguf(tensors=[])
    result = extract_gguf(publication(tmp_path / "single", {"vocab.gguf": raw}))
    assert result.variants[0].role == "unknown"
    assert result.variants[0].completeness != "complete"


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "missing_first",
        "duplicate",
        "count",
        "total",
        "directory",
        "stem",
        "scheme",
        "identity",
        "duplicate_tensor",
        "no_explicit_split",
    ],
)
def test_incomplete_or_contradictory_shards_never_form_positive_variants(tmp_path, case):
    one, _ = split(0)
    two, _ = split(1)
    files = {"m-00001-of-00002.gguf": one, "m-00002-of-00002.gguf": two}
    if case == "missing":
        files.pop("m-00002-of-00002.gguf")
    elif case == "missing_first":
        files.pop("m-00001-of-00002.gguf")
    elif case == "duplicate":
        files["m-00002-of-00002.gguf"] = split(0)[0]
    elif case == "count":
        files["m-00002-of-00002.gguf"] = split(1, count=3)[0]
    elif case == "total":
        files["m-00002-of-00002.gguf"] = split(1, total=3)[0]
    elif case == "directory":
        files["nested/m-00002-of-00002.gguf"] = files.pop("m-00002-of-00002.gguf")
    elif case == "stem":
        files["other-00002-of-00002.gguf"] = files.pop("m-00002-of-00002.gguf")
    elif case == "scheme":
        files["m-00002-of-00002.gguf"] = split(1, first_metadata={"general.file_type": (4, 7)})[0]
    elif case == "identity":
        files["m-00002-of-00002.gguf"] = split(
            1, first_metadata={"general.name": (8, "different")}
        )[0]
    elif case == "duplicate_tensor":
        files["m-00002-of-00002.gguf"] = split(1, name="weight0")[0]
    elif case == "no_explicit_split":
        files = {path: gguf()[0] for path in files}
    result = extract_gguf(publication(tmp_path, files))
    assert result.status != "complete"
    assert all(v.completeness != "complete" for v in result.variants)


@pytest.mark.parametrize(
    ("metadata", "path", "role"),
    [
        ({"general.type": (8, "adapter")}, "model.gguf", "adapter"),
        ({"adapter.type": (8, "lora")}, "model.gguf", "adapter"),
        ({"general.type": (8, "mmproj")}, "model.gguf", "projector"),
        ({"clip.projector_type": (8, "mlp")}, "model.gguf", "projector"),
        ({}, "mmproj-model.gguf", "projector"),
        ({}, "mtp-model.gguf", "auxiliary"),
        ({"general.architecture": (8, "future-architecture")}, "model.gguf", "unknown"),
    ],
)
def test_auxiliary_adapter_and_unknown_roles_do_not_promote_to_primary(
    tmp_path, metadata, path, role
):
    base = {"general.file_type": (4, 15), "general.architecture": (8, "llama")}
    base.update(metadata)
    result = extract_gguf(publication(tmp_path, {path: gguf(base)[0]}))
    assert result.variants[0].role == role


@pytest.mark.parametrize(
    "raw",
    [
        b"nope" + b"\x00" * 20,
        b"GGUF" + struct.pack("<IQQ", 3, 2**64 - 1, 1),
        b"GGUF" + struct.pack("<IQQ", 3, 1, 2**64 - 1),
        b"GGUF" + struct.pack("<IQQQ", 3, 1, 1, 2**64 - 1),
        b"GGUF" + struct.pack("<IQQ", 3, 1, 1) + string("x") + struct.pack("<I", 999),
        b"GGUF" + struct.pack("<IQQ", 3, 1, 1) + string("x") + struct.pack("<IIQ", 9, 8, 2**64 - 1),
    ],
)
def test_hostile_counts_lengths_types_and_magic_terminate_bounded(tmp_path, raw):
    access = publication(tmp_path, {"hostile.gguf": raw})
    result = extract_gguf(access)
    assert result.status in {"failed", "unsupported"}
    assert access.budget.read_bytes <= len(raw)
    assert all(v.completeness != "complete" for v in result.variants)


@pytest.mark.parametrize(("version", "endian"), [(1, "<"), (2, "<"), (4, "<"), (3, ">")])
def test_unsupported_versions_and_endian_are_explicit(tmp_path, version, endian):
    raw, _ = gguf(version=version, endian=endian)
    result = extract_gguf(publication(tmp_path, {"m.gguf": raw}))
    assert result.status == "unsupported"


@pytest.mark.parametrize(
    "tensors",
    [
        [("x", (256,), 999, 0)],
        [("x", (256,), 12, 1)],
        [("x", (256,), 12, 2**64 - 32)],
        [("x", (2**63,), 0, 0)],
        [("x", (0,), 0, 0)],
        [("x", (1, 2, 3, 4, 5), 0, 0)],
        [("x", (256,), 12, 0), ("x", (256,), 12, 256)],
        [("x", (256,), 12, 0), ("y", (256,), 12, 0)],
    ],
)
def test_invalid_tensor_extents_names_offsets_and_unknown_types(tmp_path, tensors):
    result = extract_gguf(publication(tmp_path, {"m.gguf": gguf(tensors=tensors)[0]}))
    assert result.status != "complete"
    assert all(v.completeness != "complete" for v in result.variants)


def test_ignored_multiline_metadata_and_nested_arrays_still_count(tmp_path):
    metadata = {
        "general.file_type": (4, 15),
        "general.architecture": (8, "llama"),
        "tokenizer.chat_template": (8, "line\nline"),
        "unknown": (9, (9, [(8, ["x", "y"])])),
    }
    result = extract_gguf(publication(tmp_path, {"m.gguf": gguf(metadata)[0]}))
    assert result.status == "complete"
    deep = (8, ["x"])
    for _ in range(100):
        deep = (9, [deep])
    raw, _ = gguf({"ignored": (9, deep)})
    result = extract_gguf(publication(tmp_path / "deep", {"m.gguf": raw}))
    assert result.status == "failed"
    assert "gguf_depth_limit" in result.diagnostics


def test_duplicate_metadata_invalid_unicode_and_truncation(tmp_path):
    cases = [
        gguf(pairs=[("x", (8, "a")), ("x", (8, "b"))])[0],
        gguf({"x": (8, b"\xff")})[0],
        gguf()[0][:40],
        gguf(tensors=[("x", (256,), 12, 0)], body_bytes=0)[0],
    ]
    for index, raw in enumerate(cases):
        result = extract_gguf(publication(tmp_path / str(index), {"m.gguf": raw}))
        assert result.status == "failed"


def test_declared_quantization_contradicting_float_only_tensors_is_not_positive(tmp_path):
    result = extract_gguf(publication(tmp_path, {"m.gguf": gguf(tensors=[("x", (256,), 0, 0)])[0]}))
    assert result.variants[0].completeness != "complete"
    assert "gguf_contradictory_file_type" in result.variants[0].diagnostics


def test_work_and_read_exhaustion_are_honest_and_bounded(tmp_path):
    raw, _ = gguf()
    access = publication(tmp_path, {"m.gguf": raw}, budget=ExtractionBudget(maximum_bytes=10))
    result = extract_gguf(access)
    assert result.status == "failed"
    assert "read_byte_limit" in result.diagnostics
    assert access.budget.read_bytes <= 10
    access = publication(
        tmp_path / "work", {"m.gguf": raw}, budget=ExtractionBudget(maximum_work=10)
    )
    result = extract_gguf(access)
    assert result.status == "failed"
    assert "work_limit" in result.diagnostics


def test_large_ignored_tokenizer_arrays_fit_finite_metadata_budget(tmp_path):
    metadata = {
        "general.file_type": (4, 15),
        "general.architecture": (8, "llama"),
        "tokenizer.ggml.tokens": (9, (8, ["token"] * 151936)),
        "tokenizer.ggml.scores": (9, (6, [0.0] * 151936)),
    }
    raw, end = gguf(metadata)
    access = publication(tmp_path, {"m.gguf": raw})
    result = extract_gguf(access)
    assert result.status == "complete"
    assert access.budget.read_bytes == end
    assert access.budget.work <= access.budget.maximum_work


@pytest.mark.parametrize(
    ("path", "tensors", "role"),
    [
        ("model-Q4-LoRA.gguf", None, "adapter"),
        ("model-Q4-vocab.gguf", None, "auxiliary"),
        ("model.gguf", [("layer.lora_a", (256,), 12, 0)], "adapter"),
    ],
)
def test_canonical_filename_and_tensor_adapter_evidence_only_downgrades_role(
    tmp_path, path, tensors, role
):
    result = extract_gguf(publication(tmp_path, {path: gguf(tensors=tensors)[0]}))
    assert result.variants[0].role == role


@pytest.mark.parametrize(
    "metadata",
    [
        {"general.alignment": (4, 1)},
        {"general.alignment": (4, 4)},
        {"general.alignment": (4, 12)},
        {"UPPER.key": (8, "x")},
        {"nonascii.é": (8, "x")},
        {"general.file_type": (8, "Q4_K_M")},
        {"flag": (7, 2)},
    ],
)
def test_invalid_keys_alignment_selected_types_and_booleans_never_produce_complete_variant(
    tmp_path, metadata
):
    base = {"general.file_type": (4, 15), "general.architecture": (8, "llama")}
    base.update(metadata)
    result = extract_gguf(publication(tmp_path, {"m.gguf": gguf(base)[0]}))
    assert result.status != "complete"


def test_header_truncation_at_every_offset_never_escapes_or_claims_complete(tmp_path):
    raw, end = gguf()
    for size in range(end):
        result = extract_gguf(publication(tmp_path / str(size), {"m.gguf": raw[:size]}))
        assert result.status != "complete"


def test_same_name_single_and_shard_prefix_do_not_collide(tmp_path):
    files = {
        "m.gguf": gguf()[0],
        "m.gguf-00001-of-00002.gguf": split(0)[0],
        "m.gguf-00002-of-00002.gguf": split(1)[0],
    }
    result = extract_gguf(publication(tmp_path, files))
    assert result.status == "complete"
    assert len(result.variants) == 2


def test_separate_publications_never_supply_each_others_missing_shards(tmp_path):
    first = extract_gguf(publication(tmp_path / "first", {"m-00001-of-00002.gguf": split(0)[0]}))
    second = extract_gguf(publication(tmp_path / "second", {"m-00002-of-00002.gguf": split(1)[0]}))
    assert first.variants[0].completeness != "complete"
    assert second.variants[0].completeness != "complete"


def test_valid_non_power_of_two_alignment_and_auxiliary_tensor_role(tmp_path):
    raw, _ = gguf(
        {
            "general.file_type": (4, 15),
            "general.architecture": (8, "llama"),
            "general.alignment": (4, 24),
        }
    )
    result = extract_gguf(publication(tmp_path, {"m.gguf": raw}))
    assert result.status == "complete"


def test_unknown_primary_role_is_visible_in_coverage(tmp_path):
    result = extract_gguf(
        publication(tmp_path, {"m.gguf": gguf({"general.file_type": (4, 15)})[0]})
    )
    assert result.status == "partial"
    assert result.variants[0].role == "unknown"
    assert "gguf_role_unknown" in result.diagnostics


@pytest.mark.parametrize(("file_type", "kind"), [(0, 1), (1, 0), (32, 0)])
def test_float_declaration_must_have_compatible_aggregate_tensor_kinds(tmp_path, file_type, kind):
    raw, _ = gguf(
        {"general.file_type": (4, file_type), "general.architecture": (8, "llama")},
        tensors=[("x", (256,), kind, 0)],
    )
    result = extract_gguf(publication(tmp_path, {"m.gguf": raw}))
    assert result.variants[0].completeness != "complete"
    assert "gguf_contradictory_file_type" in result.variants[0].diagnostics
