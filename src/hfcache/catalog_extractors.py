"""Writer-only bounded static extraction, without loaders, network or payload scans."""

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, Literal

from hfcache.catalog_models import MAXIMUM_MEMBERS, ModelVariant, SourceObservation
from hfcache.catalog_parsing import (
    MAXIMUM_SOURCE_BYTES,
    ExtractionError,
    parse_card,
    parse_json,
)
from hfcache.identity import CommitSha, PublicationId
from hfcache.metadata import MetadataReader
from hfcache.redaction import redact_text

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO

    from hfcache.manifests import FileEntry, RevisionManifest
    from hfcache.paths import ArchiveLayout

MAXIMUM_READ_BYTES = 64 * 1024 * 1024
MAXIMUM_WORK = 8_000_000
MAXIMUM_MANIFEST_FILES = 100_000
MAXIMUM_TEXT_BYTES = 64 * 1024
MAXIMUM_VALUES = 64
MAXIMUM_VALUE_CHARACTERS = 2048
EXTRACTION_WARNING_CODE = "HFWRN011"
JSON_NAMES = frozenset(
    {"config.json", "adapter_config.json", "dataset_info.json", "dataset_infos.json"}
)
DATASET_FORMATS = {
    ".parquet": "parquet",
    ".arrow": "arrow",
    ".csv": "csv",
    ".tsv": "tsv",
    ".jsonl": "jsonl",
    ".ndjson": "jsonl",
    ".json": "json",
    ".txt": "text",
    ".avro": "avro",
}


@dataclass(slots=True)
class ExtractionBudget:
    """Shared across files/publications; charge actual failed reads and skipped work."""

    maximum_bytes: int = MAXIMUM_READ_BYTES
    maximum_candidates: int = MAXIMUM_MEMBERS
    maximum_work: int = MAXIMUM_WORK
    read_bytes: int = 0
    candidates: int = 0
    work: int = 0

    def step(self, count: int = 1) -> None:
        self.work += count
        if self.work > self.maximum_work:
            msg = "work_limit"
            raise ExtractionError(msg)

    def candidate(self) -> None:
        self.candidates += 1
        self.step()
        if self.candidates > self.maximum_candidates:
            msg = "candidate_limit"
            raise ExtractionError(msg)


class SourceStream:
    """Pinned ordinary source; all reads/discards count against the same byte budget."""

    def __init__(self, stream: BinaryIO, entry: FileEntry, budget: ExtractionBudget) -> None:
        self.stream, self.entry, self.budget = stream, entry, budget
        self.position = 0

    def read(self, count: int) -> bytes:
        self.budget.step()
        if count < 0 or count > self.budget.maximum_bytes - self.budget.read_bytes:
            msg = "read_byte_limit"
            raise ExtractionError(msg)
        try:
            raw = self.stream.read(count)
        except OSError:
            self.budget.read_bytes += (
                count  # conservative accounting when consumed bytes are unknown
            )
            raise
        self.budget.read_bytes += len(raw)  # charge even truncated/error-producing input
        self.position += len(raw)
        if len(raw) != count:
            msg = "truncated_source"
            raise ExtractionError(msg)
        return raw

    def skip(self, count: int) -> None:
        if count < 0 or count > self.entry.size - self.position:
            msg = "truncated_source"
            raise ExtractionError(msg)
        while count:
            amount = min(count, 65536)
            self.read(amount)
            count -= amount


class SourceAccess:
    """Exact manifest-contained no-follow capability; never created by read queries."""

    def __init__(
        self,
        layout: ArchiveLayout,
        manifest: RevisionManifest,
        *,
        budget: ExtractionBudget | None = None,
    ) -> None:
        self.budget = budget or ExtractionBudget()
        self.manifest = manifest
        repository = layout.repository(manifest.identity)
        self.tree = repository.instance(
            CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
        )
        if str(layout.archive_relative(self.tree)) != manifest.tree:
            msg = "publication_identity"
            raise ExtractionError(msg)
        self.reader = MetadataReader(layout.root)
        self.files: dict[str, FileEntry] = {}
        for index, entry in enumerate(manifest.files):
            if index >= MAXIMUM_MANIFEST_FILES:
                msg = "manifest_entry_limit"
                raise ExtractionError(msg)
            self.budget.step()
            self.files[entry.path] = entry

    @contextmanager
    def open(self, path: str) -> Iterator[SourceStream]:
        self.budget.candidate()
        entry = self.files.get(path)
        if entry is None:
            msg = "source_not_in_manifest"
            raise ExtractionError(msg)
        descriptor = self.reader.open(self.tree / path)
        try:
            if os.fstat(descriptor).st_size != entry.size:
                msg = "source_size_changed"
                raise ExtractionError(msg)
            with os.fdopen(descriptor, "rb", buffering=0, closefd=False) as stream:
                yield SourceStream(stream, entry, self.budget)
        finally:
            os.close(descriptor)

    def read(self, path: str) -> bytes:
        with self.open(path) as source:
            if source.entry.size > MAXIMUM_SOURCE_BYTES:
                msg = "source_byte_limit"
                raise ExtractionError(msg)
            return source.read(source.entry.size)


Status = Literal["complete", "partial", "unsupported", "failed"]


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    status: Status
    sources: tuple[SourceObservation, ...] = ()
    variants: tuple[ModelVariant, ...] = ()
    dataset_formats: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(slots=True)
class Observations:
    """Bound retained output before allocation/deduplication; never store arbitrary input."""

    access: SourceAccess
    sources: list[SourceObservation] = field(default_factory=list)
    variants: list[ModelVariant] = field(default_factory=list)
    formats: set[str] = field(default_factory=set)
    diagnostics: set[str] = field(default_factory=set)
    failed: bool = False
    unsupported: bool = False
    text_bytes: int = 0

    def issue(self, issue: ExtractionError) -> None:
        self.failed |= not issue.unsupported
        self.unsupported |= issue.unsupported
        self.diagnostics.add(issue.reason)

    def add(self, path: str, name: str, raw: object, *, evidence: str = "declaration") -> None:
        if raw is None:
            return
        values = raw if isinstance(raw, list) else [raw]
        if len(values) > MAXIMUM_VALUES or len(self.sources) >= MAXIMUM_MEMBERS:
            msg = "retained_value_limit"
            raise ExtractionError(msg)
        selected = []
        for value in values:
            self.access.budget.step()
            if not isinstance(value, str) or len(value) > MAXIMUM_VALUE_CHARACTERS:
                msg = "unsupported_declaration"
                raise ExtractionError(msg, unsupported=True)
            size = len(value.encode("utf-8"))
            if size > MAXIMUM_TEXT_BYTES - self.text_bytes:
                msg = "retained_text_limit"
                raise ExtractionError(msg)
            self.text_bytes += size
            if value and redact_text(value) == value:
                selected.append(value)
            elif value:
                self.issue(ExtractionError("redacted_declaration", unsupported=True))
        if selected:
            self.sources.append(
                SourceObservation.model_validate(
                    {
                        "path": path,
                        "sha256": self.access.files[path].sha256,
                        "field": name,
                        "values": tuple(sorted(set(selected))),
                        "evidence": evidence,
                    }
                )
            )

    def result(self) -> ExtractionResult:
        useful = bool(self.sources or self.variants or self.formats)
        status: Status = "complete"
        if self.failed or self.unsupported:
            status = "partial" if useful else ("failed" if self.failed else "unsupported")
        grouped: dict[tuple[str, str, str], SourceObservation] = {}
        for source in self.sources:
            key = source.path, source.field, source.evidence
            previous = grouped.get(key)
            values = sorted(set(source.values) | (set(previous.values) if previous else set()))
            if len(values) > MAXIMUM_VALUES:
                msg = "retained_value_limit"
                raise ExtractionError(msg)
            grouped[key] = source.model_copy(update={"values": tuple(values)})
        return ExtractionResult(
            status,
            tuple(grouped[key] for key in sorted(grouped)),
            tuple(sorted(self.variants, key=lambda item: item.variant_id)),
            tuple(sorted(self.formats)),
            tuple(sorted(self.diagnostics)),
        )


def _names(raw: object) -> list[str]:
    if not isinstance(raw, list) or len(raw) > MAXIMUM_VALUES:
        msg = "unsupported_declaration"
        raise ExtractionError(msg, unsupported=True)
    result = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            msg = "unsupported_declaration"
            raise ExtractionError(msg, unsupported=True)
        result.append(item["name"])
    return result


def _dataset_info(out: Observations, path: str, value: object) -> None:
    infos = value if isinstance(value, list) else [value]
    if len(infos) > MAXIMUM_VALUES:
        msg = "retained_value_limit"
        raise ExtractionError(msg)
    for info in infos:
        out.access.budget.step()
        if not isinstance(info, dict):
            msg = "unsupported_declaration"
            raise ExtractionError(msg, unsupported=True)
        out.add(path, "dataset_config", info.get("config_name"))
        for key, field_name in (("splits", "dataset_split"), ("features", "dataset_feature")):
            if key in info:
                if isinstance(info[key], dict) and len(info[key]) > MAXIMUM_VALUES:
                    msg = "retained_value_limit"
                    raise ExtractionError(msg)
                names = list(info[key]) if isinstance(info[key], dict) else _names(info[key])
                out.add(path, field_name, names)


def _declarations(out: Observations, path: str, value: Any) -> None:  # noqa: ANN401
    if not isinstance(value, dict):
        msg = "unsupported_declaration"
        raise ExtractionError(msg, unsupported=True)
    fields = {
        "pipeline_tag": "task",
        "task_categories": "task",
        "language": "language",
        "license": "license",
        "base_model": "base_model",
        "base_model_name_or_path": "base_model",
        "tags": "upstream_tags",
    }
    for key, field_name in fields.items():
        out.add(path, field_name, value.get(key))
    if out.access.manifest.repository_type != "dataset":
        return
    _dataset_declarations(out, path, value)


def _dataset_declarations(out: Observations, path: str, value: dict[str, Any]) -> None:
    if "configs" in value:
        configs = value["configs"]
        if not isinstance(configs, list) or len(configs) > MAXIMUM_VALUES:
            msg = "unsupported_declaration"
            raise ExtractionError(msg, unsupported=True)
        for config in configs:
            if not isinstance(config, dict):
                msg = "unsupported_declaration"
                raise ExtractionError(msg, unsupported=True)
            out.add(path, "dataset_config", config.get("config_name"))
            data_files = config.get("data_files")
            if isinstance(data_files, list):
                if len(data_files) > MAXIMUM_VALUES:
                    msg = "retained_value_limit"
                    raise ExtractionError(msg)
                for item in data_files:
                    out.access.budget.step()
                    if isinstance(item, dict):
                        out.add(path, "dataset_split", item.get("split"))
    if "dataset_info" in value:
        _dataset_info(out, path, value["dataset_info"])
    if PurePosixPath(path).name == "dataset_info.json":
        _dataset_info(out, path, value)
    elif PurePosixPath(path).name == "dataset_infos.json":
        for name, info in value.items():
            out.access.budget.step()
            out.add(path, "dataset_config", name)
            _dataset_info(out, path, info)


def extract_static(access: SourceAccess) -> ExtractionResult:
    """Extract declarations and dataset filename formats; absence is not a failure."""
    out = Observations(access)
    for path in access.files:
        try:
            access.budget.step()
            name = PurePosixPath(path).name
            if path == "README.md":
                _declarations(out, path, parse_card(access.read(path)))
            elif name in JSON_NAMES:
                _declarations(out, path, parse_json(access.read(path)))
            elif access.manifest.repository_type == "dataset":
                fmt = DATASET_FORMATS.get(PurePosixPath(path).suffix.lower())
                if fmt is not None:
                    access.budget.candidate()
                    out.add(path, "format", fmt, evidence="filename")
                    out.formats.add(fmt)
        except ExtractionError as exc:
            out.issue(exc)
        except OSError, ValueError:
            out.issue(ExtractionError("unsafe_or_unreadable_source"))
        if (
            access.budget.work > access.budget.maximum_work
            or access.budget.candidates > access.budget.maximum_candidates
        ):
            break
    try:
        return out.result()
    except ExtractionError as exc:
        out.issue(exc)
        return ExtractionResult("failed", diagnostics=tuple(sorted(out.diagnostics)))
