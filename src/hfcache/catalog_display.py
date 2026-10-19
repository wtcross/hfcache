"""Qualified inert human catalog summaries; JSON evidence is rendered separately (INV-006)."""

from typing import Any, Literal


def _text(value: object) -> str:
    return "".join(
        character if character.isprintable() else f"\\u{ord(character):04x}"
        for character in str(value)
    )


def _variant(value: dict[str, Any], *, representative: bool = False) -> str:
    variant = value["variant"]
    parts = [
        "representative" if representative else "variant",
        value["commit_sha"],
        value["publication_id"],
        f"generation={value['publication_generation']}",
        variant["variant_id"],
        variant["format"],
        variant["role"],
        variant["completeness"],
        f"members={len(variant['members'])}",
        f"bytes={variant['total_bytes'] if variant['total_bytes'] is not None else 'unknown'}",
        f"bits={variant['bits'] if variant['bits'] is not None else 'unknown'}",
    ]
    parts.extend(
        f"{key}={variant[key]}"
        for key in ("encoding", "quantization", "quantization_method")
        if variant[key] is not None
    )
    if variant["diagnostics"]:
        parts.append("diagnostics=" + ", ".join(variant["diagnostics"]))
    return "  ".join(_text(part) for part in parts)


def _entry(entry: dict[str, Any]) -> list[str]:
    state = ("enabled" if entry["enabled"] else "disabled") if entry["configured"] else "unmanaged"
    labels = ", ".join(entry["tags"]) or (
        "unknown" if entry["tag_origin"] == "unknown" else "(empty)"
    )
    rows = [
        _text(
            f"{entry['repository_type']}:{entry['repository_id']}  {state}  "
            f"archived={entry['archived']}  tags [{entry['tag_origin']}]: {labels}"
        )
    ]
    if entry["tag_observed_at"] is not None:
        rows.append(_text(f"  tags observed at {entry['tag_observed_at']}"))
    if entry["repository_type"] == "model":
        rows.append(f"  {entry['matching_variant_count']} matching primary variants")
        if entry["representative_variant"] is not None:
            rows.append("  " + _variant(entry["representative_variant"], representative=True))
    elif entry["dataset_formats"]:
        rows.append("  observed formats: " + _text(", ".join(entry["dataset_formats"])))
    return rows


def catalog_rows(
    data: dict[str, Any],
    mode: Literal["search", "facets", "detail", "variants"],
) -> list[str]:
    coverage = data["coverage"]
    rows = [
        f"Coverage: {coverage['repositories']} repositories; "
        f"{coverage['usable']}/{coverage['publications']} usable observations; "
        + (
            "incomplete (zero known matches does not prove absence)"
            if coverage["incomplete"]
            else "complete selected coverage"
        )
    ]
    if mode == "facets":
        rows.extend(
            _text(f"{item['value']}  {item['repository_count']} repositories")
            for item in data["entries"]
        )
    elif mode == "variants":
        rows.extend(_variant(item) for item in data["entries"])
    elif mode == "search":
        for item in data["entries"]:
            rows.extend(_entry(item))
    else:
        rows.extend(_entry(data["entry"]))
        for observation in data["observations"]:
            rows.append(
                _text(
                    f"observation  {observation['commit_sha']}  {observation['publication_id']}  "
                    f"{observation['status']}  extractor={observation['extractor_version']}"
                )
            )
            rows.extend("  diagnostic: " + _text(item) for item in observation["diagnostics"])
            rows.extend(
                _text(
                    f"  {source['field']} [{source['evidence']}] {source['path']}: "
                    + ", ".join(source["values"])
                )
                for source in observation["sources"]
            )
    return rows
