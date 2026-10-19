"""Bounded GGUF v3 little-endian headers and exact-publication shard sets.

Primary format/mapping pins are recorded in docs/discovery.md. No tensor data is read.
"""

import math
import re
import struct
from dataclasses import dataclass, replace
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

from hfcache.catalog_extractors import MAXIMUM_VALUE_CHARACTERS, ExtractionResult, Observations
from hfcache.catalog_models import MAXIMUM_MEMBERS, ModelVariant, VariantMember, variant_identity
from hfcache.catalog_parsing import ExtractionError
from hfcache.redaction import redact_text

if TYPE_CHECKING:
    from hfcache.catalog_extractors import SourceAccess, SourceStream

VERSION = 3
MAXIMUM_COUNT = 100_000
MAXIMUM_ARRAY_COUNT = 1_048_576
MAXIMUM_STRING = 64 * 1024
MAXIMUM_KEY = 256
MAXIMUM_TENSOR_NAME = 64
MAXIMUM_DIMENSIONS = 4
MAXIMUM_DEPTH = 64
MAXIMUM_ALIGNMENT = 65536
MINIMUM_ALIGNMENT = 8
MAXIMUM_INTEGER = 2**63 - 1
CONTROL_END = 32
SURROGATE_START = 0xD800
SURROGATE_END = 0xDFFF
STRING = 8
ARRAY = 9
BOOL = 7
BF16_TENSOR = 30
SCALARS = {
    0: "B",
    1: "b",
    2: "H",
    3: "h",
    4: "I",
    5: "i",
    6: "f",
    7: "B",
    10: "Q",
    11: "q",
    12: "d",
}

# general.file_type (llama_ftype), NOT ggml tensor-type numbers. Removed/guessed
# entries stay unsupported. Nominal bits for mixed/K/IQ schemes stay unknown.
FILE_TYPES = {
    0: ("F32", None, 32),
    1: ("F16", None, 16),
    2: ("Q4_0", "Q4_0", 4),
    3: ("Q4_1", "Q4_1", 4),
    7: ("Q8_0", "Q8_0", 8),
    8: ("Q5_0", "Q5_0", 5),
    9: ("Q5_1", "Q5_1", 5),
    10: ("Q2_K", "Q2_K", None),
    11: ("Q3_K_S", "Q3_K_S", None),
    12: ("Q3_K_M", "Q3_K_M", None),
    13: ("Q3_K_L", "Q3_K_L", None),
    14: ("Q4_K_S", "Q4_K_S", None),
    15: ("Q4_K_M", "Q4_K_M", None),
    16: ("Q5_K_S", "Q5_K_S", None),
    17: ("Q5_K_M", "Q5_K_M", None),
    18: ("Q6_K", "Q6_K", None),
    19: ("IQ2_XXS", "IQ2_XXS", None),
    20: ("IQ2_XS", "IQ2_XS", None),
    21: ("Q2_K_S", "Q2_K_S", None),
    22: ("IQ3_XS", "IQ3_XS", None),
    23: ("IQ3_XXS", "IQ3_XXS", None),
    24: ("IQ1_S", "IQ1_S", None),
    25: ("IQ4_NL", "IQ4_NL", None),
    26: ("IQ3_S", "IQ3_S", None),
    27: ("IQ3_M", "IQ3_M", None),
    28: ("IQ2_S", "IQ2_S", None),
    29: ("IQ2_M", "IQ2_M", None),
    30: ("IQ4_XS", "IQ4_XS", None),
    31: ("IQ1_M", "IQ1_M", None),
    32: ("BF16", None, 16),
}
# ggml tensor type -> (elements/block, bytes/block); only used for safe offset
# arithmetic. It never establishes a majority/mixed file quantization scheme.
TENSOR_SIZES = {
    0: (1, 4),
    1: (1, 2),
    2: (32, 18),
    3: (32, 20),
    6: (32, 22),
    7: (32, 24),
    8: (32, 34),
    9: (32, 36),
    10: (256, 84),
    11: (256, 110),
    12: (256, 144),
    13: (256, 176),
    14: (256, 210),
    15: (256, 292),
    16: (256, 66),
    17: (256, 74),
    18: (256, 98),
    19: (256, 50),
    20: (32, 18),
    21: (256, 110),
    22: (256, 82),
    23: (256, 136),
    24: (1, 1),
    25: (1, 2),
    26: (1, 4),
    27: (1, 8),
    28: (1, 8),
    29: (256, 56),
    30: (1, 2),
}
PRIMARY_ARCHITECTURES = frozenset(
    {
        "llama",
        "qwen2",
        "qwen2moe",
        "qwen3",
        "qwen3moe",
        "gemma",
        "gemma2",
        "gemma3",
        "gpt2",
        "gptneox",
        "phi2",
        "phi3",
        "mpt",
        "falcon",
        "mistral",
        "deepseek2",
        "bert",
        "t5",
    }
)
SELECTED = {
    "general.file_type": 4,
    "general.alignment": 4,
    "general.architecture": STRING,
    "general.type": STRING,
    "general.name": STRING,
    "general.uuid": STRING,
    "adapter.type": STRING,
    "clip.projector_type": STRING,
    "clip.has_llava_projector": BOOL,
    "split.no": 2,
    "split.count": 2,
    "split.tensors.count": 5,
}
SHARD = re.compile(r"(.+)-([0-9]{5})-of-([0-9]{5})\.gguf", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Header:
    path: str
    metadata: dict[str, Any]
    tensors: tuple[str, ...]
    kinds: frozenset[int]
    data_offset: int


class _Reader:
    def __init__(self, source: SourceStream) -> None:
        self.source = source

    def number(self, fmt: str) -> Any:  # noqa: ANN401 - bounded inert numeric scalar
        return struct.unpack("<" + fmt, self.source.read(struct.calcsize(fmt)))[0]

    def string(self, maximum: int = MAXIMUM_STRING) -> str:
        length = self.number("Q")
        if length > maximum or length > self.source.entry.size - self.source.position:
            msg = "gguf_string_limit"
            raise ExtractionError(msg)
        try:
            value = self.source.read(length).decode("utf-8")
        except UnicodeError as exc:
            msg = "gguf_invalid_unicode"
            raise ExtractionError(msg) from exc
        if any(SURROGATE_START <= ord(c) <= SURROGATE_END for c in value):
            msg = "gguf_invalid_unicode"
            raise ExtractionError(msg)
        return value

    def value(self, kind: int, depth: int = 0) -> Any:  # noqa: ANN401 - arrays discarded in place
        if depth > MAXIMUM_DEPTH:
            msg = "gguf_depth_limit"
            raise ExtractionError(msg)
        if kind == STRING:
            return self.string()
        if kind == ARRAY:
            element_kind, count = self.number("I"), self.number("Q")
            if count > MAXIMUM_ARRAY_COUNT:
                msg = "gguf_count_limit"
                raise ExtractionError(msg)
            self.source.budget.step(count)
            if element_kind not in {*SCALARS, STRING, ARRAY}:
                msg = "gguf_unknown_value_type"
                raise ExtractionError(msg, unsupported=True)
            for _ in range(count):
                self.value(element_kind, depth + 1)
            return None
        if kind not in SCALARS:
            msg = "gguf_unknown_value_type"
            raise ExtractionError(msg, unsupported=True)
        value = self.number(SCALARS[kind])
        if (kind == BOOL and value not in (0, 1)) or (
            isinstance(value, float) and not math.isfinite(value)
        ):
            msg = "gguf_invalid_scalar"
            raise ExtractionError(msg)
        return value

    def tensors(self, count: int, alignment: int) -> tuple[tuple[str, ...], frozenset[int], int]:
        names: set[str] = set()
        kinds: set[int] = set()
        spans = []
        for _ in range(count):
            name = self.string(MAXIMUM_TENSOR_NAME)
            if not name or name in names or any(ord(c) < CONTROL_END for c in name):
                msg = "gguf_duplicate_tensor"
                raise ExtractionError(msg)
            names.add(name)
            dimensions = self.number("I")
            if not 1 <= dimensions <= MAXIMUM_DIMENSIONS:
                msg = "gguf_dimension_limit"
                raise ExtractionError(msg)
            sizes = [self.number("Q") for _ in range(dimensions)]
            elements = math.prod(sizes)
            kind, offset = self.number("I"), self.number("Q")
            if kind not in TENSOR_SIZES:
                msg = "gguf_unknown_tensor_type"
                raise ExtractionError(msg, unsupported=True)
            block, size = TENSOR_SIZES[kind]
            kinds.add(kind)
            if (
                not all(sizes)
                or elements > MAXIMUM_INTEGER
                or sizes[0] % block
                or offset % alignment
            ):
                msg = "gguf_invalid_tensor_extent"
                raise ExtractionError(msg)
            end = offset + elements // block * size
            if end > self.source.entry.size:
                msg = "gguf_invalid_tensor_extent"
                raise ExtractionError(msg)
            spans.append((offset, end))
        base = (self.source.position + alignment - 1) // alignment * alignment
        if base > self.source.entry.size:
            msg = "gguf_truncated_tensor_data"
            raise ExtractionError(msg)
        previous = 0
        for start, end in sorted(spans):
            if start < previous or end > self.source.entry.size - base:
                msg = "gguf_invalid_tensor_extent"
                raise ExtractionError(msg)
            previous = end
        return tuple(sorted(names)), frozenset(kinds), base

    def header(self) -> Header:
        if self.source.read(4) != b"GGUF":
            msg = "gguf_invalid_magic"
            raise ExtractionError(msg)
        version = self.source.read(4)
        if version == struct.pack(">I", VERSION):
            msg = "gguf_big_endian_unsupported"
            raise ExtractionError(msg, unsupported=True)
        if version != struct.pack("<I", VERSION):
            msg = "gguf_version_unsupported"
            raise ExtractionError(msg, unsupported=True)
        tensors, pairs = self.number("Q"), self.number("Q")
        if tensors > MAXIMUM_COUNT or pairs > MAXIMUM_COUNT:
            msg = "gguf_count_limit"
            raise ExtractionError(msg)
        self.source.budget.step(tensors + pairs)
        keys: set[str] = set()
        metadata = {}
        for _ in range(pairs):
            key, kind = self.string(MAXIMUM_KEY), self.number("I")
            if not re.fullmatch(r"[a-z0-9_]+(?:\.[a-z0-9_]+)*", key) or key in keys:
                msg = "gguf_duplicate_key"
                raise ExtractionError(msg)
            keys.add(key)
            value = self.value(kind)
            if key in SELECTED:
                if kind != SELECTED[key] or (
                    isinstance(value, str)
                    and (
                        len(value) > MAXIMUM_VALUE_CHARACTERS
                        or any(ord(c) < CONTROL_END for c in value)
                    )
                ):
                    msg = "gguf_invalid_selected_type"
                    raise ExtractionError(msg)
                if isinstance(value, str) and redact_text(value) != value:
                    msg = "gguf_redacted_identity"
                    raise ExtractionError(msg, unsupported=True)
                metadata[key] = value
        alignment = metadata.get("general.alignment", 32)
        if not MINIMUM_ALIGNMENT <= alignment <= MAXIMUM_ALIGNMENT or alignment % MINIMUM_ALIGNMENT:
            msg = "gguf_alignment_unsupported"
            raise ExtractionError(msg, unsupported=True)
        names, kinds, base = self.tensors(tensors, alignment)
        return Header(self.source.entry.path, metadata, names, kinds, base)


def _role(path: str, metadata: dict[str, Any], tensors: tuple[str, ...]) -> str:
    name = PurePosixPath(path).name.lower()
    matched = SHARD.fullmatch(name)
    stem = matched[1] if matched else name.removesuffix(".gguf")
    if (
        "adapter.type" in metadata
        or metadata.get("general.type") == "adapter"
        or name.startswith(("adapter", "lora-"))
        or stem.endswith("-lora")
        or any(tensor.endswith((".lora_a", ".lora_b")) for tensor in tensors)
    ):
        return "adapter"
    if (
        metadata.get("general.type") == "mmproj"
        or "clip.projector_type" in metadata
        or metadata.get("clip.has_llava_projector")
        or name.startswith("mmproj")
    ):
        return "projector"
    if (
        metadata.get("general.type") == "imatrix"
        or name.startswith(("imatrix", "mtp-"))
        or stem.endswith("-vocab")
    ):
        return "auxiliary"
    if (
        metadata.get("general.type", "model") == "model"
        and metadata.get("general.architecture") in PRIMARY_ARCHITECTURES
    ):
        return "primary"
    return "unknown"


def _variant(
    access: SourceAccess,
    paths: list[str],
    header: Header | None,
    diagnostics: set[str],
    *,
    complete: bool,
) -> ModelVariant:
    members = tuple(
        VariantMember(path=path, size_bytes=access.files[path].size) for path in sorted(paths)
    )
    metadata = header.metadata if header else {}
    file_type = metadata.get("general.file_type")
    encoding, quantization, bits = (
        FILE_TYPES.get(file_type, (None, None, None))
        if type(file_type) is int
        else (None, None, None)
    )
    supported = encoding is not None and header is not None
    if not supported:
        diagnostics.add("gguf_file_type_unsupported")
    quantized_kinds = set(TENSOR_SIZES) - {0, 1, 24, 25, 26, 27, 28, 30}
    if header is not None and (
        (quantization is not None and not header.kinds.intersection(quantized_kinds))
        or (encoding in {"F32", "F16", "BF16"} and header.kinds.intersection(quantized_kinds))
        or (encoding == "F32" and header.kinds != {0})
        or (encoding == "F16" and (1 not in header.kinds or header.kinds - {0, 1}))
        or (
            encoding == "BF16"
            and (BF16_TENSOR not in header.kinds or header.kinds - {0, BF16_TENSOR})
        )
    ):
        diagnostics.add("gguf_contradictory_file_type")
        complete = False
    authority_path = header.path if header else paths[0]
    role = _role(authority_path, metadata, header.tensors if header else ())
    if header is not None and not header.tensors and not complete and role == "primary":
        role = "unknown"
    return ModelVariant.model_validate(
        {
            "variant_id": variant_identity(members),
            "format": "gguf",
            "encoding": encoding,
            "quantization": quantization,
            "quantization_method": "ggml" if quantization else None,
            "bits": bits,
            "role": role,
            "members": [m.to_payload() for m in members],
            "total_bytes": sum(m.size_bytes for m in members),
            "completeness": "complete"
            if complete and supported
            else ("incomplete" if diagnostics - {"gguf_file_type_unsupported"} else "unknown"),
            "evidence": "header" if header else "filename",
            "source_paths": [authority_path],
            "diagnostics": sorted(diagnostics),
        }
    )


def _group(access: SourceAccess, paths: list[str], headers: dict[str, Header]) -> ModelVariant:  # noqa: PLR0912 - explicit independent header consistency checks
    diagnostics: set[str] = set()
    first = None
    indices = []
    counts = set()
    totals = set()
    names: set[str] = set()
    for path in sorted(paths):
        access.budget.step()
        header = headers.get(path)
        matched = SHARD.fullmatch(PurePosixPath(path).name)
        if header is None or matched is None:
            diagnostics.add("gguf_missing_shard_metadata")
            continue
        metadata = header.metadata
        index, count, total = (
            metadata.get(k) for k in ("split.no", "split.count", "split.tensors.count")
        )
        if (
            index is None
            or count is None
            or total is None
            or not 0 <= index < count <= MAXIMUM_MEMBERS
            or total < 1
            or int(matched[2]) != index + 1
            or int(matched[3]) != count
        ):
            diagnostics.add("gguf_conflicting_split")
            continue
        if index == 0:
            first = header
        indices.append(index)
        counts.add(count)
        totals.add(total)
        if names.intersection(header.tensors):
            diagnostics.add("gguf_duplicate_split_tensor")
        names.update(header.tensors)
    if first is None:
        diagnostics.add("gguf_missing_first_shard")
    else:
        for header in headers.values():
            for key, value in header.metadata.items():
                if key.startswith("split.") or key == "general.alignment":
                    continue
                if key not in first.metadata or first.metadata[key] != value:
                    diagnostics.add("gguf_conflicting_shard_identity")
    if (
        len(counts) != 1
        or len(totals) != 1
        or len(indices) != len(set(indices))
        or (counts and sorted(indices) != list(range(next(iter(counts)))))
        or (totals and sum(len(h.tensors) for h in headers.values()) != next(iter(totals)))
    ):
        diagnostics.add("gguf_incomplete_shard_set")
    if first is not None:
        first = replace(
            first,
            tensors=tuple(sorted(names)),
            kinds=frozenset(kind for header in headers.values() for kind in header.kinds),
        )
    return _variant(
        access,
        sorted(paths),
        first,
        diagnostics,
        complete=not diagnostics,
    )


def _single(access: SourceAccess, path: str, header: Header | None) -> ModelVariant:
    split = header is not None and any(key.startswith("split.") for key in header.metadata)
    diagnostics = {"gguf_unbound_split"} if split else set()
    if header is not None and not header.tensors:
        diagnostics.add("gguf_no_tensors")
    return _variant(
        access, [path], header, diagnostics, complete=not diagnostics and header is not None
    )


def extract_gguf(access: SourceAccess) -> ExtractionResult:  # noqa: PLR0912 - source/group failure classifications
    """Inspect bounded headers, then group exact explicit shard declarations only."""
    if access.manifest.repository_type != "model":
        return ExtractionResult("complete")
    out = Observations(access)
    groups: dict[tuple[str, str, str], list[str]] = {}
    headers = {}
    candidates = 0
    for path in access.files:
        try:
            access.budget.step()
            if not path.lower().endswith(".gguf"):
                continue
            candidates += 1
            if candidates > MAXIMUM_MEMBERS:
                msg = "candidate_limit"
                raise ExtractionError(msg)  # noqa: TRY301 - one source classification boundary
            matched = SHARD.fullmatch(PurePosixPath(path).name)
            key = (
                "split" if matched else "single",
                str(PurePosixPath(path).parent),
                matched[1] if matched else PurePosixPath(path).name,
            )
            groups.setdefault(key, []).append(path)
            with access.open(path) as source:
                headers[path] = _Reader(source).header()
        except ExtractionError as exc:
            out.issue(exc)
        except OSError, ValueError:
            out.issue(ExtractionError("unsafe_or_unreadable_source"))
        if (
            access.budget.work > access.budget.maximum_work
            or access.budget.candidates > access.budget.maximum_candidates
        ):
            break
    for paths in groups.values():
        try:
            access.budget.step()
            selected = {path: headers[path] for path in paths if path in headers}
            if len(paths) > 1 or SHARD.fullmatch(PurePosixPath(paths[0]).name):
                variant = _group(access, paths, selected)
            else:
                variant = _single(access, paths[0], selected.get(paths[0]))
            out.variants.append(variant)
            if variant.completeness != "complete":
                out.issue(ExtractionError("gguf_incomplete_or_unsupported", unsupported=True))
            elif variant.role == "unknown":
                out.issue(ExtractionError("gguf_role_unknown", unsupported=True))
        except ExtractionError as exc:
            out.issue(exc)
            break
    result = out.result()
    if (out.failed or out.unsupported) and not any(
        v.completeness == "complete" for v in result.variants
    ):
        return replace(result, status="failed" if out.failed else "unsupported")
    return result
