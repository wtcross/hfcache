"""Scoped declarations and bounded physical members without runtimes (V20-22)."""

import builtins
import json
import socket
import struct

import pytest

import hfcache.catalog_weights as weights
from hfcache.catalog_extractors import ExtractionBudget, SourceStream
from hfcache.catalog_weights import extract_weights
from tests.unit.test_catalog_extractors import publication


def config(method="awq", bits=4, group_size=128):
    return json.dumps(
        {
            "model_type": "llama",
            "quantization_config": {"quant_method": method, "bits": bits, "group_size": group_size},
        }
    ).encode()


def safetensors(name="weight", *, dtype="I32", shape=None, offsets=None, body=b"\xa5" * 16):
    header = json.dumps(
        {
            name: {
                "dtype": dtype,
                "shape": [4] if shape is None else shape,
                "data_offsets": [0, 16] if offsets is None else offsets,
            }
        },
        separators=(",", ":"),
    ).encode()
    return struct.pack("<Q", len(header)) + header + body


@pytest.mark.parametrize(
    ("method", "bits"), [("awq", 4), ("gptq", 2), ("gptq", 3), ("gptq", 4), ("gptq", 8)]
)
def test_explicit_supported_declarations_bind_one_same_directory_bundle(tmp_path, method, bits):
    raw = safetensors()
    result = extract_weights(
        publication(tmp_path, {"config.json": config(method, bits), "model.safetensors": raw})
    )
    assert result.status == "complete"
    (variant,) = result.variants
    assert variant.format == "safetensors"
    assert variant.quantization_method == method
    assert variant.quantization is None
    assert variant.encoding is None
    assert variant.bits == bits
    assert variant.group_size == 128
    assert variant.completeness == "complete"
    assert variant.role == "primary"
    assert variant.source_paths == ("config.json",)
    assert variant.total_bytes == len(raw)


def test_complete_index_deduplicates_normal_repeated_shard_values(tmp_path):
    one, two = safetensors("one"), safetensors("two")
    index = {
        "weight_map": {
            "one": "model-00001-of-00002.safetensors",
            "another": "model-00001-of-00002.safetensors",
            "two": "model-00002-of-00002.safetensors",
        }
    }
    result = extract_weights(
        publication(
            tmp_path,
            {
                "config.json": config(),
                "model.safetensors.index.json": json.dumps(index).encode(),
                "model-00001-of-00002.safetensors": one,
                "model-00002-of-00002.safetensors": two,
            },
        )
    )
    (variant,) = result.variants
    assert result.status == "complete"
    assert len(variant.members) == 2
    assert variant.total_bytes == len(one) + len(two)
    assert variant.source_paths == ("config.json", "model.safetensors.index.json")


@pytest.mark.parametrize(
    "value",
    [
        "../model.safetensors",
        "/model.safetensors",
        "nested/model.safetensors",
        "./model.safetensors",
        "model.bin",
        "missing.safetensors",
        42,
        ["model.safetensors"],
    ],
)
def test_invalid_index_never_falls_back_to_available_singleton(tmp_path, value):
    result = extract_weights(
        publication(
            tmp_path,
            {
                "config.json": config(),
                "model.safetensors.index.json": json.dumps({"weight_map": {"x": value}}).encode(),
                "model.safetensors": safetensors(),
            },
        )
    )
    assert result.status == "failed"
    assert all(v.completeness != "complete" for v in result.variants)


def test_duplicate_json_tensor_key_and_incomplete_named_shards_refuse(tmp_path):
    cases = [
        b'{"weight_map":{"x":"model.safetensors","x":"model.safetensors"}}',
        b'{"weight_map":{"x":"model-00001-of-00002.safetensors"}}',
    ]
    for i, index in enumerate(cases):
        result = extract_weights(
            publication(
                tmp_path / str(i),
                {
                    "config.json": config(),
                    "model.safetensors.index.json": index,
                    "model.safetensors": safetensors(),
                    "model-00001-of-00002.safetensors": safetensors(),
                },
            )
        )
        assert result.status == "failed"
        assert all(v.completeness != "complete" for v in result.variants)


def test_multiple_quantized_directories_keep_methods_and_bytes_separate(tmp_path):
    files = {
        "config.json": config("awq"),
        "awq/config.json": config("awq"),
        "awq/model.safetensors": safetensors(),
        "gptq/config.json": config("gptq", 8),
        "gptq/model.safetensors": safetensors("other"),
    }
    result = extract_weights(publication(tmp_path, files))
    variants = {v.members[0].path: v for v in result.variants}
    assert result.status == "partial"  # root declares quantization but has no weights
    assert variants["awq/model.safetensors"].quantization_method == "awq"
    assert variants["awq/model.safetensors"].bits == 4
    assert variants["gptq/model.safetensors"].quantization_method == "gptq"
    assert variants["gptq/model.safetensors"].bits == 8
    assert all(v.completeness == "complete" for v in variants.values())


def test_root_config_never_lends_method_or_role_to_child_weights(tmp_path):
    result = extract_weights(
        publication(tmp_path, {"config.json": config(), "nested/model.safetensors": safetensors()})
    )
    (variant,) = result.variants
    assert variant.quantization_method is None
    assert variant.bits is None
    assert variant.role == "unknown"
    assert variant.completeness != "complete"


@pytest.mark.parametrize(
    "extra",
    [
        {"other.safetensors": safetensors("other")},
        {"pytorch_model.bin": b"PK\x03\x04" + b"opaque" * 30},
        {
            "model-00001-of-00002.safetensors": safetensors("one"),
            "model-00002-of-00002.safetensors": safetensors("two"),
        },
    ],
)
def test_unindexed_multiple_alternative_and_mixed_bundles_are_ambiguous(tmp_path, extra):
    result = extract_weights(
        publication(
            tmp_path, {"config.json": config(), "model.safetensors": safetensors(), **extra}
        )
    )
    assert result.status == "unsupported"
    assert all(v.completeness != "complete" for v in result.variants)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"0" * 64 + b"\nsize 1000\n",
        struct.pack("<Q", 2**64 - 1),
        safetensors(offsets=[0, 1000]),
        safetensors(dtype="FUTURE"),
        safetensors(shape=[2**63, 2]),
        safetensors(shape=[True]),
        safetensors(offsets=[False, 16]),
    ],
)
def test_pointer_empty_hostile_or_inconsistent_members_never_become_complete(tmp_path, raw):
    result = extract_weights(
        publication(tmp_path, {"config.json": config(), "model.safetensors": raw})
    )
    assert result.status in {"failed", "unsupported"}
    assert result.variants[0].completeness != "complete"


@pytest.mark.parametrize(
    "quantization",
    [
        {"quant_method": []},
        {"quant_method": {}},
        {"quant_method": "unknown"},
        {"quant_method": "awq", "bits": 8},
        {"quant_method": "gptq", "bits": True},
        {"quant_method": "gptq", "bits": "4"},
        {"quant_method": "gptq"},
        {"quant_method": "gptq", "bits": 4, "group_size": False},
        {"quant_method": "gptq", "bits": 4, "dynamic": {"x": {"bits": 8}}},
        [],
    ],
)
def test_invalid_unknown_or_dynamic_quantization_does_not_use_runtime_defaults(
    tmp_path, quantization
):
    raw = json.dumps({"model_type": "llama", "quantization_config": quantization}).encode()
    result = extract_weights(
        publication(tmp_path, {"config.json": raw, "model.safetensors": safetensors()})
    )
    assert result.status in {"failed", "unsupported"}
    assert result.variants[0].completeness != "complete"


def test_group_minus_one_and_missing_group_stay_nullable(tmp_path):
    result = extract_weights(
        publication(
            tmp_path, {"config.json": config("gptq", 4, -1), "model.safetensors": safetensors()}
        )
    )
    assert result.status == "complete"
    assert result.variants[0].group_size is None
    assert "per_column_group_size" in result.variants[0].diagnostics
    result = extract_weights(
        publication(
            tmp_path / "unknown",
            {
                "config.json": (
                    b'{"model_type":"llama","quantization_config":{"quant_method":"gptq","bits":4}}'
                ),
                "model.safetensors": safetensors(),
            },
        )
    )
    assert result.variants[0].group_size is None
    assert "group_size_unknown" in result.variants[0].diagnostics


def test_no_declaration_is_unknown_not_unquantized_and_absence_is_optional(tmp_path):
    result = extract_weights(
        publication(
            tmp_path, {"config.json": b'{"model_type":"llama"}', "model.safetensors": safetensors()}
        )
    )
    assert result.status == "complete"
    assert result.variants[0].quantization_method is None
    assert result.variants[0].bits is None
    result = extract_weights(
        publication(tmp_path / "gguf-config-only", {"config.json": b'{"model_type":"llama"}'})
    )
    assert result.status == "complete"
    assert result.variants == ()
    result = extract_weights(publication(tmp_path / "quant-config-only", {"config.json": config()}))
    assert result.status == "unsupported"
    assert result.variants == ()


def test_legacy_sidecar_is_not_arbitrarily_merged_with_nested_declaration(tmp_path):
    result = extract_weights(
        publication(
            tmp_path,
            {
                "config.json": config(),
                "quantize_config.json": b'{"quant_method":"gptq","bits":8}',
                "model.safetensors": safetensors(),
            },
        )
    )
    assert result.status == "unsupported"
    assert result.variants[0].completeness != "complete"


@pytest.mark.parametrize("path", ["adapter_model.safetensors", "mmproj.safetensors"])
def test_auxiliary_weights_are_never_primary(tmp_path, path):
    result = extract_weights(publication(tmp_path, {"config.json": config(), path: safetensors()}))
    assert result.variants[0].role in {"adapter", "auxiliary"}


def test_no_runtime_import_network_unpickle_or_tensor_body_read(tmp_path, monkeypatch):
    raw = safetensors()
    end = 8 + struct.unpack("<Q", raw[:8])[0]
    access = publication(tmp_path, {"config.json": config(), "model.safetensors": raw})
    original_read = SourceStream.read

    def checked_read(source, count):
        if source.entry.path.endswith(".safetensors"):
            assert source.position + count <= end
        return original_read(source, count)

    def denied(*_args, **_kwargs):
        pytest.fail("static extraction attempted network")

    original_import = builtins.__import__

    def checked_import(name, *args, **kwargs):
        assert name.split(".")[0] not in {
            "torch",
            "transformers",
            "autoawq",
            "awq",
            "auto_gptq",
            "gptqmodel",
            "pickle",
            "safetensors",
        }
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(SourceStream, "read", checked_read)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(builtins, "__import__", checked_import)
    result = extract_weights(access)
    assert result.status == "complete"


def test_binary_container_is_only_sniffed_and_never_deserialized(tmp_path):
    result = extract_weights(
        publication(
            tmp_path,
            {
                "config.json": config("gptq"),
                "pytorch_model.bin": b"\x80\x04" + b"untrusted pickle code" * 10,
            },
        )
    )
    assert result.status == "complete"
    assert result.variants[0].format == "pytorch_bin"


def test_symlink_member_and_malformed_configuration_are_safe_failures(tmp_path):
    access = publication(tmp_path, {"config.json": config(), "model.safetensors": safetensors()})
    target = tmp_path / "outside"
    target.write_bytes(safetensors())
    (access.tree / "model.safetensors").unlink()
    (access.tree / "model.safetensors").symlink_to(target)
    assert extract_weights(access).status == "failed"
    result = extract_weights(
        publication(
            tmp_path / "bad",
            {"config.json": b"private invalid json", "model.safetensors": safetensors()},
        )
    )
    assert result.status == "failed"
    assert "private" not in repr(result)


def test_shared_read_work_and_candidate_bounds_refuse_honestly(tmp_path, monkeypatch):
    access = publication(
        tmp_path,
        {"config.json": config(), "model.safetensors": safetensors()},
        budget=ExtractionBudget(maximum_bytes=1),
    )
    assert extract_weights(access).status == "failed"
    assert access.budget.read_bytes <= 1
    monkeypatch.setattr(weights, "MAXIMUM_MEMBERS", 1)
    access = publication(
        tmp_path / "count", {"config.json": config(), "model.safetensors": safetensors()}
    )
    result = extract_weights(access)
    assert result.status == "failed"
    assert "weight_scope_limit" in result.diagnostics


def test_index_cannot_promote_known_training_artifacts(tmp_path):
    result = extract_weights(
        publication(
            tmp_path,
            {
                "config.json": config(),
                "pytorch_model.bin.index.json": b'{"weight_map":{"x":"optimizer.bin"}}',
                "optimizer.bin": b"PK\x03\x04" + b"opaque" * 30,
            },
        )
    )
    assert result.status == "failed"
    assert result.variants == ()
    assert "non_weight_index_member" in result.diagnostics


@pytest.mark.parametrize("raw", [b"PK\x03\x04xxxx", b"\x80\x04xxxxxx"])
def test_tiny_binary_prefix_stubs_are_not_complete_containers(tmp_path, raw):
    result = extract_weights(
        publication(tmp_path, {"config.json": config(), "pytorch_model.bin": raw})
    )
    assert result.status == "failed"
    assert result.variants[0].completeness != "complete"


def test_float_only_quantized_storage_is_inspectable_but_not_positive(tmp_path):
    result = extract_weights(
        publication(
            tmp_path,
            {"config.json": config(), "model.safetensors": safetensors(dtype="F16", shape=[8])},
        )
    )
    assert result.status == "unsupported"
    assert result.variants[0].completeness != "complete"
    assert "contradictory_quantized_storage" in result.variants[0].diagnostics


def test_huge_shape_integers_refuse_before_large_product(tmp_path):
    result = extract_weights(
        publication(
            tmp_path,
            {
                "config.json": config(),
                "model.safetensors": safetensors(shape=[10**2000] * 63 + [0]),
            },
        )
    )
    assert result.status == "failed"
    assert "invalid_safetensors_shape" in result.diagnostics


def test_legacy_only_configuration_is_explicitly_unsupported(tmp_path):
    result = extract_weights(publication(tmp_path, {"quantize_config.json": b'{"bits":4}'}))
    assert result.status == "unsupported"
    assert result.variants == ()


def test_empty_integer_declaration_does_not_prove_quantized_storage(tmp_path):
    header = json.dumps(
        {
            "empty": {"dtype": "I32", "shape": [0], "data_offsets": [0, 0]},
            "float": {"dtype": "F16", "shape": [8], "data_offsets": [0, 16]},
        }
    ).encode()
    raw = struct.pack("<Q", len(header)) + header + b"\xa5" * 16
    result = extract_weights(
        publication(tmp_path, {"config.json": config(), "model.safetensors": raw})
    )
    assert result.status == "unsupported"
    assert result.variants[0].completeness != "complete"
