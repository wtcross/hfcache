"""Detecting what a repository depends on, without ever running it.

docs/architecture.md AD-07 and `AD-07`. The archive is repository-complete at one commit, and
nothing else: a LoRA adapter is archived exactly as published, which means the
base model it is useless without is *not* in the archive unless someone
configured it separately. Detection exists so that gap is visible before it is
discovered by a consumer with an adapter and nothing to apply it to.

Three rules shape everything here.

**Read, never execute.** Only a fixed set of known metadata files is opened, and
only as data: a model card's YAML front matter through the library's own
`safe_load`-based reader, and `adapter_config.json` through `json.load`. No
repository code is imported, no model is instantiated, no pickle is opened, and
`trust_remote_code` never appears (`AD-15`, `NG-*`, `docs/security.md` T-04).

**Warn, never act.** An undeclared dependency is `HFDEP001`, is written into the
immutable manifest, makes the repository `completed_with_warnings`, and leaves
the exit code at `0`. It never downloads anything: a detector that fetched what
it found would turn one configured repository into an unbounded transitive
closure, which is exactly what `NG-05` forbids.

**Report ambiguity rather than resolve it.** Metadata that will not parse, or a
field whose value is not a repository identifier, is recorded at `low`
confidence with what was seen. Guessing produces a warning an operator cannot
check; saying "this file did not parse" produces one they can.
"""

import json
from typing import TYPE_CHECKING, Final, Literal

from hfcache.identity import parse_repository_id
from hfcache.manifests import DependencyObservation

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

__all__ = [
    "ADAPTER_CONFIG",
    "ADAPTER_FIELDS",
    "MODEL_CARD",
    "MODEL_CARD_FIELDS",
    "detect_dependencies",
    "undeclared",
    "undeclared_warnings",
]

MODEL_CARD: Final = "README.md"
"""The only model card the Hub recognises, and so the only one read."""

MODEL_CARD_FIELDS: Final = ("base_model",)
"""Model-card metadata keys that name another repository (docs/architecture.md AD-07).

`base_model` is the Hub's own standardized field and carries either one string
or a list of them — a merged model legitimately names several parents.
"""

ADAPTER_CONFIG: Final = "adapter_config.json"
"""PEFT's adapter configuration, the file that makes an adapter an adapter."""

ADAPTER_FIELDS: Final = ("base_model_name_or_path",)
"""Adapter and derived-model configuration keys that name another repository.

`base_model_name_or_path` is PEFT's, and it is the highest-confidence signal in
this module: an adapter without its base is not merely incomplete, it cannot be
loaded at all.
"""


def detect_dependencies(
    tree: Path,
    *,
    declared: Sequence[str] = (),
    managed: Sequence[str] = (),
) -> tuple[DependencyObservation, ...]:
    """Every dependency this revision's static metadata names (docs/architecture.md AD-07).

    `tree` is the published or staged tree, so detection reads the same bytes
    that were hashed and will be published — not the Hub's copy of them, and not
    a re-fetch. A detector that read anything else could report a dependency the
    archived revision does not actually declare.

    `declared` is `[[repositories]].declared_dependencies` for this repository
    and `managed` is every repository this archive is configured to hold. They
    are separate questions and the manifest records both: a dependency can be
    declared but unmanaged (the operator knows and has decided not to archive it)
    or managed but undeclared (it is archived, and the declaration is stale).

    Sorted by `(source_file, source_field, detected_id)`, which is what
    `RevisionManifest` requires and what makes two runs over one revision produce
    the same manifest bytes.
    """
    declared_ids = {_normalized(value) for value in declared}
    managed_ids = {_normalized(value) for value in managed}
    observations = [
        *_from_model_card(tree),
        *_from_adapter_config(tree),
    ]
    resolved = [
        observation.model_copy(
            update={
                "declared": _normalized(observation.detected_id) in declared_ids,
                "managed": _normalized(observation.detected_id) in managed_ids,
            }
        )
        for observation in observations
    ]
    return tuple(
        sorted(resolved, key=lambda item: (item.source_file, item.source_field, item.detected_id))
    )


def _normalized(value: str) -> str:
    """Fold a dependency identifier for comparison.

    Case-insensitively, because the Hub treats `Org/Model` and `org/model` as the
    same repository while a `declared_dependencies` entry is typed by hand. A
    declaration that differs only in case is a declaration, not a near-miss —
    reporting it as undeclared would train an operator to ignore the warning.
    """
    return value.strip().casefold()


def _from_model_card(tree: Path) -> list[DependencyObservation]:
    """Read `base_model` out of the model card's YAML front matter.

    Through `huggingface_hub`'s own reader, which parses with `yaml.safe_load` —
    no object construction, no code execution, no tags that could reach a
    constructor (`docs/security.md` T-04). A card with no front matter, or with
    front matter that is not a mapping, yields nothing rather than an error: the
    overwhelming majority of repositories have neither a `base_model` field nor a
    problem.
    """
    card = tree / MODEL_CARD
    if not card.is_file():
        return []
    try:
        from huggingface_hub.repocard import metadata_load  # noqa: PLC0415 - see docstring

        metadata = metadata_load(card)
    except Exception:  # noqa: BLE001 - a repository's YAML; any parse failure is one finding
        # Deliberately broad. `yaml.safe_load` raises several unrelated types for
        # malformed input and the library adds its own for a non-mapping block,
        # and every one of them means the same thing to an operator: this card's
        # metadata could not be read. Narrowing it would let an unlisted parser
        # error escape as a traceback from the middle of an ingestion.
        return [_unparseable(MODEL_CARD, "front_matter")]
    if not isinstance(metadata, dict):
        return []
    return _observations(metadata, source_file=MODEL_CARD, fields=MODEL_CARD_FIELDS)


def _from_adapter_config(tree: Path) -> list[DependencyObservation]:
    """Read `base_model_name_or_path` out of an adapter configuration.

    `json.load` and nothing else. PEFT would import the file through its own
    loader; this application reads it as the JSON document it is, which is the
    whole difference between describing an adapter and running one.
    """
    config = tree / ADAPTER_CONFIG
    if not config.is_file():
        return []
    try:
        metadata = json.loads(config.read_text(encoding="utf-8"))
    except OSError, ValueError, UnicodeDecodeError:
        return [_unparseable(ADAPTER_CONFIG, ADAPTER_FIELDS[0])]
    if not isinstance(metadata, dict):
        return [_unparseable(ADAPTER_CONFIG, ADAPTER_FIELDS[0])]
    return _observations(
        metadata, source_file=ADAPTER_CONFIG, fields=ADAPTER_FIELDS, confidence="high"
    )


def _observations(
    metadata: Mapping[str, object],
    *,
    source_file: str,
    fields: Sequence[str],
    confidence: Literal["high", "medium", "low"] = "medium",
) -> list[DependencyObservation]:
    """Turn the recognised fields of one metadata document into observations.

    A field holding a list produces one observation per entry — a merged model
    names several parents and every one of them is a real dependency. A value
    that is not a repository identifier produces a `low`-confidence observation
    recording what was seen, because "this field held something unexpected" is
    a finding an operator can check and a silent skip is not.
    """
    found: list[DependencyObservation] = []
    for field in fields:
        value = metadata.get(field)
        if value is None:
            continue
        found.extend(
            _observation(candidate, source_file, field, confidence)
            for candidate in (value if isinstance(value, list) else [value])
        )
    return found


def _observation(
    candidate: object,
    source_file: str,
    field: str,
    confidence: Literal["high", "medium", "low"],
) -> DependencyObservation:
    """One value from one field, classified by whether it is an identifier."""
    text = str(candidate).strip()
    try:
        parse_repository_id(text)
    except ValueError:
        return DependencyObservation(
            confidence="low",
            declared=False,
            detected_id=text[:200] or "(empty)",
            managed=False,
            source_field=field,
            source_file=source_file,
        )
    return DependencyObservation(
        confidence=confidence,
        declared=False,
        detected_id=text,
        managed=False,
        source_field=field,
        source_file=source_file,
    )


def _unparseable(source_file: str, field: str) -> DependencyObservation:
    """Record metadata that would not parse, without guessing what it meant."""
    return DependencyObservation(
        confidence="low",
        declared=False,
        detected_id="(unparseable)",
        managed=False,
        source_field=field,
        source_file=source_file,
    )


def undeclared_warnings(observations: Sequence[DependencyObservation]) -> list[str]:
    """The `HFDEP001` codes an undeclared dependency contributes to a run.

    Returns codes rather than messages because that is what a run report and a
    catalog entry hold. The human-readable form is the CLI's, and the durable
    form is the manifest's `dependencies` array, which carries every observation
    including the declared ones — an operator asking "what does this depend on"
    gets an answer whether or not anything is wrong.

    One code however many observations: `HFDEP001` names the condition, not the
    instance, and a repository with four undeclared adapters has one problem.
    """
    if any(not observation.declared for observation in observations):
        return ["HFDEP001"]
    return []


def undeclared(
    observations: Sequence[DependencyObservation],
) -> tuple[DependencyObservation, ...]:
    """Just the observations that are not declared, for a message an operator reads."""
    return tuple(observation for observation in observations if not observation.declared)
