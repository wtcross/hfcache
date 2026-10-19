"""Scoped static weight declarations/indexes, without runtime imports or unpickling."""

import re
import struct
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from hfcache.catalog_extractors import ExtractionResult, Observations
from hfcache.catalog_models import MAXIMUM_MEMBERS, ModelVariant, VariantMember, variant_identity
from hfcache.catalog_parsing import MAXIMUM_SOURCE_BYTES, ExtractionError, parse_json
from hfcache.paths import parse_repository_relative

if TYPE_CHECKING:
    from hfcache.catalog_extractors import SourceAccess, SourceStream

INDEXES = {
    "model.safetensors.index.json": "safetensors",
    "pytorch_model.bin.index.json": "pytorch_bin",
}
SINGLE_NAMES = {
    "model.safetensors",
    "pytorch_model.bin",
    "adapter_model.safetensors",
    "adapter_model.bin",
}
NON_WEIGHTS = {"training_args.bin", "optimizer.bin", "scheduler.bin", "rng_state.bin"}
LEGACY_CONFIGS = {"quantize_config.json", "quant_config.json"}
DTYPE_BYTES = {
    "F64": 8,
    "F32": 4,
    "F16": 2,
    "BF16": 2,
    "I64": 8,
    "I32": 4,
    "I16": 2,
    "I8": 1,
    "U64": 8,
    "U32": 4,
    "U16": 2,
    "U8": 1,
    "BOOL": 1,
}
SUPPORTED_BITS = frozenset({2, 3, 4, 8})
MAXIMUM_INTEGER = 2**63 - 1
MAXIMUM_DIMENSIONS = 64
OFFSET_COUNT = 2
PREFIX_BYTES = 8
MINIMUM_BINARY_BYTES = 128
INTEGER_DTYPES = frozenset({"I64", "I32", "I16", "I8", "U64", "U32", "U16", "U8"})
MODEL_TYPES = frozenset(
    {
        "llama",
        "mistral",
        "mixtral",
        "qwen2",
        "qwen3",
        "gemma",
        "gemma2",
        "gemma3_text",
        "phi",
        "phi3",
        "gpt2",
        "gpt_neox",
        "falcon",
        "mpt",
        "bert",
        "t5",
        "deepseek_v2",
        "deepseek_v3",
    }
)
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"
SHARD = re.compile(r"(.+)-([0-9]{5})-of-([0-9]{5})\.(safetensors|bin)")


@dataclass(slots=True)
class Declaration:
    source: str | None = None
    method: str | None = None
    bits: int | None = None
    group_size: int | None = None
    role: str = "unknown"
    valid: bool = True
    quantized: bool = False
    diagnostics: set[str] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class Bundle:
    format: str
    members: tuple[str, ...]
    index: str | None = None
    recognized: bool = True


def _declaration(access: SourceAccess, paths: list[str]) -> Declaration:
    config_path = next((path for path in paths if PurePosixPath(path).name == "config.json"), None)
    result = Declaration(source=config_path)
    if any(PurePosixPath(path).name in LEGACY_CONFIGS for path in paths):
        result.valid = False
        result.quantized = True
        result.diagnostics.add("legacy_quantization_layout_unsupported")
    if config_path is None:
        result.valid = False
        result.diagnostics.add("weight_configuration_missing")
        return result
    config = parse_json(access.read(config_path))
    if not isinstance(config, dict):
        msg = "invalid_weight_configuration"
        raise ExtractionError(msg)
    model_type = config.get("model_type")
    if isinstance(model_type, str) and model_type in MODEL_TYPES:
        result.role = "primary"
    if any(PurePosixPath(path).name == "adapter_config.json" for path in paths):
        result.role = "adapter"
    quantization = config.get("quantization_config")
    if quantization is not None:
        result.quantized = True
        _quantization(result, quantization)
    return result


def _quantization(result: Declaration, quantization: object) -> None:
    if not isinstance(quantization, dict):
        msg = "invalid_quantization_configuration"
        raise ExtractionError(msg)
    method = quantization.get("quant_method")
    if not isinstance(method, str) or method not in {"awq", "gptq"}:
        result.valid = False
        result.diagnostics.add("quantization_method_unsupported")
        return
    result.method = method
    bits, group = quantization.get("bits"), quantization.get("group_size")
    if type(bits) is not int or bits not in (SUPPORTED_BITS if method == "gptq" else {4}):
        result.valid = False
        result.diagnostics.add("quantization_bits_unknown_or_unsupported")
    else:
        result.bits = bits
    if group == -1 and type(group) is int:
        result.diagnostics.add("per_column_group_size")
    elif group is None:
        result.diagnostics.add("group_size_unknown")
    elif type(group) is not int or not 1 <= group <= MAXIMUM_INTEGER:
        result.valid = False
        result.diagnostics.add("invalid_group_size")
    else:
        result.group_size = group
    if quantization.get("dynamic") or quantization.get("modules_in_block_to_quantize"):
        result.valid = False
        result.diagnostics.add("dynamic_quantization_unsupported")


def _index(access: SourceAccess, path: str, fmt: str) -> Bundle:
    payload = parse_json(access.read(path))
    mapping = payload.get("weight_map") if isinstance(payload, dict) else None
    if not isinstance(mapping, dict) or not mapping:
        msg = "invalid_weight_index"
        raise ExtractionError(msg)
    members: set[str] = set()
    for value in mapping.values():
        access.budget.step()
        try:
            relative = parse_repository_relative(value)
        except ValueError as exc:
            msg = "unsafe_weight_index_member"
            raise ExtractionError(msg) from exc
        if str(relative) != value or relative.parent != PurePosixPath("."):
            msg = "out_of_scope_weight_index_member"
            raise ExtractionError(msg)
        if relative.name in NON_WEIGHTS:
            msg = "non_weight_index_member"
            raise ExtractionError(msg)
        suffix = ".safetensors" if fmt == "safetensors" else ".bin"
        if not relative.name.endswith(suffix):
            msg = "mixed_weight_index_format"
            raise ExtractionError(msg)
        member = str(PurePosixPath(path).parent / relative)
        if member not in access.files:
            msg = "missing_weight_index_member"
            raise ExtractionError(msg)
        members.add(member)  # repeated tensor->shard values are normal, not duplicate members
        if len(members) > MAXIMUM_MEMBERS:
            msg = "weight_member_limit"
            raise ExtractionError(msg)
    shards = [SHARD.fullmatch(PurePosixPath(member).name) for member in members]
    if any(shards):
        if not all(shards):
            msg = "inconsistent_weight_shards"
            raise ExtractionError(msg)
        identities = {(match[1], int(match[3]), match[4]) for match in shards if match}
        indices = sorted(int(match[2]) for match in shards if match)
        if (
            len(identities) != 1
            or indices != list(range(1, len(members) + 1))
            or next(iter(identities))[1] != len(members)
        ):
            msg = "incomplete_weight_shards"
            raise ExtractionError(msg)
    return Bundle(fmt, tuple(sorted(members)), path)


def _tensor_span(info: object, body_bytes: int) -> tuple[int, int, str]:
    if not isinstance(info, dict) or set(info) != {"dtype", "shape", "data_offsets"}:
        msg = "invalid_safetensors_tensor"
        raise ExtractionError(msg)
    dtype, shape, offsets = info["dtype"], info["shape"], info["data_offsets"]
    if not isinstance(dtype, str) or dtype not in DTYPE_BYTES:
        msg = "safetensors_dtype_unsupported"
        raise ExtractionError(msg, unsupported=True)
    if (
        not isinstance(shape, list)
        or len(shape) > MAXIMUM_DIMENSIONS
        or any(type(v) is not int or not 0 <= v <= MAXIMUM_INTEGER for v in shape)
    ):
        msg = "invalid_safetensors_shape"
        raise ExtractionError(msg)
    if (
        not isinstance(offsets, list)
        or len(offsets) != OFFSET_COUNT
        or any(type(v) is not int for v in offsets)
    ):
        msg = "invalid_safetensors_offsets"
        raise ExtractionError(msg)
    start, end = offsets
    elements = 1
    for dimension in shape:
        if dimension and elements > MAXIMUM_INTEGER // dimension:
            msg = "invalid_safetensors_extent"
            raise ExtractionError(msg)
        elements *= dimension
    if not 0 <= start <= end <= body_bytes or end - start != elements * DTYPE_BYTES[dtype]:
        msg = "invalid_safetensors_extent"
        raise ExtractionError(msg)
    return start, end, dtype


def _safetensors(source: SourceStream, first: bytes) -> set[str]:
    length = struct.unpack("<Q", first)[0]
    if not 1 <= length <= MAXIMUM_SOURCE_BYTES or length > source.entry.size - source.position:
        msg = "safetensors_header_limit"
        raise ExtractionError(msg)
    raw = source.read(length)
    if not raw.startswith(b"{"):
        msg = "invalid_safetensors_header"
        raise ExtractionError(msg)
    payload = parse_json(raw)
    if not isinstance(payload, dict):
        msg = "invalid_safetensors_header"
        raise ExtractionError(msg)
    spans = []
    dtypes: set[str] = set()
    for name, info in payload.items():
        source.budget.step()
        if name == "__metadata__":
            if not isinstance(info, dict) or not all(isinstance(v, str) for v in info.values()):
                msg = "invalid_safetensors_metadata"
                raise ExtractionError(msg)
            continue
        start, end, dtype = _tensor_span(info, source.entry.size - source.position)
        if end > start:
            dtypes.add(dtype)
        spans.append((start, end))
    previous = 0
    for start, end in sorted(spans):
        if start != previous:
            msg = "safetensors_overlap_or_hole"
            raise ExtractionError(msg)
        previous = end
    if not spans or previous != source.entry.size - source.position or not previous:
        msg = "safetensors_unindexed_or_empty_data"
        raise ExtractionError(msg)
    return dtypes


def _member(access: SourceAccess, path: str, fmt: str) -> set[str]:
    with access.open(path) as source:
        first = source.read(min(PREFIX_BYTES, source.entry.size))
        if first == b"version ":
            prefix = first + source.read(
                min(len(LFS_PREFIX) - len(first), source.entry.size - source.position)
            )
            if prefix == LFS_PREFIX:
                msg = "weight_lfs_pointer"
                raise ExtractionError(msg)
        if len(first) < PREFIX_BYTES:
            msg = "weight_empty_or_truncated"
            raise ExtractionError(msg)
        if fmt == "safetensors":
            return _safetensors(source, first)
        if not first.startswith(
            (b"PK\x03\x04", b"\x80\x02", b"\x80\x03", b"\x80\x04", b"\x80\x05")
        ):
            msg = "pytorch_container_unsupported"
            raise ExtractionError(msg, unsupported=True)
        if source.entry.size < MINIMUM_BINARY_BYTES:
            msg = "weight_binary_too_small"
            raise ExtractionError(msg)
        return set()


def _variant(
    out: Observations, bundle: Bundle, declaration: Declaration, *, ambiguous: bool
) -> ModelVariant:
    access = out.access
    diagnostics = set(declaration.diagnostics)
    complete = declaration.valid and bundle.recognized and not ambiguous
    if ambiguous:
        diagnostics.add("ambiguous_weight_bundle")
    if not bundle.recognized:
        diagnostics.add("unrecognized_or_unindexed_weight_bundle")
    role = declaration.role
    dtypes: set[str] = set()
    if any(PurePosixPath(path).name.startswith(("adapter", "lora")) for path in bundle.members):
        role = "adapter"
    elif any(PurePosixPath(path).name.startswith(("mmproj", "mtp-")) for path in bundle.members):
        role = "auxiliary"
    for path in bundle.members:
        try:
            dtypes.update(_member(access, path, bundle.format))
        except ExtractionError as exc:
            out.issue(exc)
            diagnostics.add(exc.reason)
            complete = False
            if (
                access.budget.work > access.budget.maximum_work
                or access.budget.candidates > access.budget.maximum_candidates
            ):
                raise
        except OSError, ValueError:
            out.issue(ExtractionError("unsafe_or_unreadable_weight"))
            diagnostics.add("unsafe_or_unreadable_weight")
            complete = False
    if (
        declaration.method
        and bundle.format == "safetensors"
        and not dtypes.intersection(INTEGER_DTYPES)
    ):
        diagnostics.add("contradictory_quantized_storage")
        out.issue(ExtractionError("contradictory_quantized_storage", unsupported=True))
        complete = False
    members = tuple(
        VariantMember(path=path, size_bytes=access.files[path].size) for path in bundle.members
    )
    sources = sorted({path for path in (declaration.source, bundle.index) if path is not None}) or [
        bundle.members[0]
    ]
    return ModelVariant.model_validate(
        {
            "variant_id": variant_identity(members),
            "format": bundle.format,
            "quantization_method": declaration.method,
            "bits": declaration.bits,
            "group_size": declaration.group_size,
            "role": role,
            "members": [member.to_payload() for member in members],
            "total_bytes": sum(member.size_bytes for member in members),
            "completeness": "complete" if complete else "unknown",
            "evidence": "declaration" if declaration.source else "filename",
            "source_paths": sources,
            "diagnostics": sorted(diagnostics),
        }
    )


def _scope(out: Observations, paths: list[str]) -> None:
    access = out.access
    config_path = next((path for path in paths if PurePosixPath(path).name == "config.json"), None)
    try:
        declaration = _declaration(access, paths)
    except ExtractionError as exc:
        out.issue(exc)
        declaration = Declaration(
            source=config_path, valid=False, diagnostics={"invalid_weight_configuration"}
        )
    except OSError, ValueError:
        out.issue(ExtractionError("unsafe_or_unreadable_weight_configuration"))
        declaration = Declaration(
            source=config_path, valid=False, diagnostics={"invalid_weight_configuration"}
        )
    bundles = []
    invalid_index = False
    failed_indexes: dict[str, str] = {}
    for path in paths:
        fmt = INDEXES.get(PurePosixPath(path).name)
        if fmt is not None:
            try:
                bundles.append(_index(access, path, fmt))
            except ExtractionError as exc:
                out.issue(exc)
                invalid_index = True
                failed_indexes[fmt] = path
            except OSError, ValueError:
                out.issue(ExtractionError("unsafe_or_unreadable_weight_index"))
                invalid_index = True
                failed_indexes[fmt] = path
    indexed = {member for bundle in bundles for member in bundle.members}
    for path in paths:
        name = PurePosixPath(path).name
        if (
            path not in indexed
            and name.endswith((".safetensors", ".bin"))
            and name not in NON_WEIGHTS
        ):
            fmt = "safetensors" if name.endswith(".safetensors") else "pytorch_bin"
            bundles.append(
                Bundle(
                    fmt,
                    (path,),
                    index=failed_indexes.get(fmt),
                    recognized=name in SINGLE_NAMES,
                )
            )
    if not bundles and (declaration.quantized or invalid_index):
        out.issue(ExtractionError("weight_bundle_missing", unsupported=True))
    ambiguous = invalid_index or len(bundles) > 1
    for bundle in bundles:
        access.budget.step()
        variant = _variant(out, bundle, declaration, ambiguous=ambiguous)
        out.variants.append(variant)
        if variant.completeness != "complete" or variant.role == "unknown":
            out.issue(ExtractionError("weight_bundle_incomplete_or_unsupported", unsupported=True))


def extract_weights(access: SourceAccess) -> ExtractionResult:
    """One explicit config/index/weight scope per directory; never inherit root policy."""
    if access.manifest.repository_type != "model":
        return ExtractionResult("complete")
    out = Observations(access)
    scopes: dict[str, list[str]] = {}
    candidates = 0
    try:
        for path in access.files:
            access.budget.step()
            name = PurePosixPath(path).name
            if name in {
                "config.json",
                "adapter_config.json",
                *INDEXES,
                *LEGACY_CONFIGS,
            } or name.endswith((".safetensors", ".bin")):
                candidates += 1
                if candidates > MAXIMUM_MEMBERS:
                    msg = "weight_scope_limit"
                    raise ExtractionError(msg)  # noqa: TRY301 - one bounded extraction refusal
                scopes.setdefault(str(PurePosixPath(path).parent), []).append(path)
        for paths in scopes.values():
            _scope(out, paths)
    except ExtractionError as exc:
        out.issue(exc)
    result = out.result()
    if (out.failed or out.unsupported) and not any(
        v.completeness == "complete" for v in result.variants
    ):
        return ExtractionResult(
            "failed" if out.failed else "unsupported",
            variants=result.variants,
            diagnostics=result.diagnostics,
        )
    return result
