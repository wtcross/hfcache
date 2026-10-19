"""Synthetic GGUF headers with opaque tensor bytes; never real model fixtures."""

import struct


def string(value, endian="<"):
    raw = value.encode() if isinstance(value, str) else value
    return struct.pack(endian + "Q", len(raw)) + raw


def value(kind, data, endian="<"):
    if kind == 8:
        return string(data, endian)
    if kind == 9:
        child_kind, items = data
        return struct.pack(endian + "IQ", child_kind, len(items)) + b"".join(
            value(child_kind, item, endian) for item in items
        )
    formats = {
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
    return struct.pack(endian + formats[kind], data)


def gguf(metadata=None, *, tensors=None, pairs=None, version=3, endian="<", body_bytes=4096):  # noqa: PLR0913 - explicit header mutation fixtures
    metadata = (
        {
            "general.file_type": (4, 15),
            "general.architecture": (8, "llama"),
            "general.name": (8, "fixture"),
        }
        if metadata is None
        else metadata
    )
    pairs = list(metadata.items()) if pairs is None else pairs
    tensors = [("weight", (256,), 12, 0)] if tensors is None else tensors
    raw = b"GGUF" + struct.pack(endian + "IQQ", version, len(tensors), len(pairs))
    for key, (kind, data) in pairs:
        raw += string(key, endian) + struct.pack(endian + "I", kind) + value(kind, data, endian)
    for name, dimensions, kind, offset in tensors:
        raw += string(name, endian) + struct.pack(endian + "I", len(dimensions))
        raw += b"".join(struct.pack(endian + "Q", dimension) for dimension in dimensions)
        raw += struct.pack(endian + "IQ", kind, offset)
    header_end = len(raw)
    alignment = metadata.get("general.alignment", (4, 32))[1]
    padding = (
        (-header_end) % alignment if isinstance(alignment, int) and 0 < alignment <= 65536 else 0
    )
    return raw + b"\x00" * padding + b"\xa5" * body_bytes, header_end


def split(index, count=2, *, total=2, first_metadata=None, name=None):
    metadata = {
        "split.no": (2, index),
        "split.count": (2, count),
        "split.tensors.count": (5, total),
    }
    if index == 0:
        metadata.update(
            {
                "general.file_type": (4, 15),
                "general.architecture": (8, "llama"),
                "general.name": (8, "fixture"),
            }
        )
    if first_metadata:
        metadata.update(first_metadata)
    return gguf(metadata, tensors=[] if name == "" else [(name or f"weight{index}", (256,), 12, 0)])
