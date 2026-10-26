"""ADR142/schema18.1: bounded, inert, publication-pinned README presentation.

This conservative Markdown subset retains ordinary links as inert source, not
navigation authority. It neither loads repository code nor fetches any asset.
"""

import hashlib
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, NoReturn
from urllib.parse import urlsplit

from hfcache.catalog_models import (
    MAXIMUM_CARD_PRESENTATION_BYTES,
    RepositoryCard,
)
from hfcache.catalog_parsing import ExtractionError
from hfcache.identity import CommitSha, PublicationId
from hfcache.redaction import contains_secret

if TYPE_CHECKING:
    from hfcache.catalog_extractors import ExtractionBudget, SourceAccess
    from hfcache.catalog_models import CardDiagnostic, CardState

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)\r?\n?$")
_LANGUAGE = re.compile(r"[A-Za-z0-9_+.-]{0,64}")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_REFERENCE = re.compile(r"^ {0,3}\[[^\[\]\r\n]+\]:[ \t]*(.*?)[\r\n]*$")
_DESTINATION = re.compile(r"""([^ \t]*)(?:[ \t]+(?:"[^"\r\n]*"|'[^'\r\n]*'))?[ \t]*""")
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
_ENTITY = re.compile(r"&(?:\#[0-9]+|\#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);")
_ASSET_PLACEHOLDER = r"\[image omitted\]"
_PRINTABLE_MINIMUM = 33
_PRINTABLE_MAXIMUM = 126
_CONTROL_END = 32


def _unsupported() -> NoReturn:
    msg = "unsupported_markdown"
    raise ExtractionError(msg, unsupported=True)


def _target(value: str) -> None:
    """Closed simple destinations; uncertain Markdown URL spellings are refused."""
    if (
        any(
            not _PRINTABLE_MINIMUM <= ord(char) <= _PRINTABLE_MAXIMUM or char in "\\<>`{}()"
            for char in value
        )
        or _ENTITY.search(value)
        or value.startswith("//")
    ):
        _unsupported()
    if _SCHEME.match(value):
        try:
            parsed = urlsplit(value)
        except ValueError:
            _unsupported()
            return
        if parsed.scheme.lower() not in {"http", "https"}:
            msg = "unsafe_content"
            raise ExtractionError(msg)
        if not parsed.hostname or parsed.username is not None or parsed.password is not None:
            _unsupported()


def _destination(value: str) -> None:
    matched = _DESTINATION.fullmatch(value)
    if matched is None or any(char in value for char in "<>{}"):
        _unsupported()
    _target(matched[1])


def _closing(line: str, opening: int, left: str, right: str) -> int:
    """A single linear scan; nested/escaped labels and destinations are unsupported."""
    for index in range(opening + 1, len(line)):
        char = line[index]
        if char == right:
            return index
        if char in {left, "\\", "\r", "\n"}:
            _unsupported()
    _unsupported()


def _code_end(line: str, opening: int, budget: ExtractionBudget) -> int:
    following = opening + 1
    while following < len(line) and line[following] == "`":
        following += 1
    budget.step(len(line) - following)  # before a possibly long span search
    width = following - opening
    closing = following
    while closing < len(line):
        if line[closing] != "`":
            closing += 1
            continue
        ending = closing + 1
        while ending < len(line) and line[ending] == "`":
            ending += 1
        if ending - closing == width:
            return ending
        closing = ending
    _unsupported()


def _link_end(line: str, opening: int, *, image: bool) -> int:
    closing = _closing(line, opening, "[", "]")
    if not image and any(char in line[opening:closing] for char in "<>{}"):
        _unsupported()
    following = closing + 1
    if following < len(line) and line[following] == "(":
        ending = _closing(line, following, "(", ")")
        if not image:
            _destination(line[following + 1 : ending])
        return ending + 1
    if following < len(line) and line[following] == "[":
        return _closing(line, following, "[", "]") + 1
    return following


def _prose(line: str, budget: ExtractionBudget) -> str:  # noqa: PLR0912 - closed inline grammar
    reference = _REFERENCE.fullmatch(line)
    if reference is not None:
        if any(char in line for char in "<>{}\\"):
            _unsupported()
        _destination(reference[1])
        return line
    if line.lstrip().startswith(("import ", "export ")):
        _unsupported()  # MDX module forms are outside this presentation version.
    parts: list[str] = []
    size = 0
    start = index = 0
    while index < len(line):
        char = line[index]
        if char == "\\":
            index += 2  # escaped punctuation cannot open a Markdown construct
            continue
        if char == "`":
            index = _code_end(line, index, budget)
            continue
        if char == "<":
            closing = line.find(">", index + 1)
            if closing < 0 or not line[index + 1 : closing].startswith(("http://", "https://")):
                _unsupported()
            _target(line[index + 1 : closing])
            index = closing + 1
            continue
        if char in "{}":
            _unsupported()  # MDX expressions/attributes are not interpreted.
        image = char == "!" and line[index + 1 : index + 2] == "["
        if char == "[" or image:
            following = _link_end(line, index + int(image), image=image)
            if image:
                prefix = line[start:index]
                size += len(prefix.encode("utf-8")) + len(_ASSET_PLACEHOLDER)
                if size > MAXIMUM_CARD_PRESENTATION_BYTES:
                    msg = "presentation_oversize"
                    raise ExtractionError(msg)
                parts.extend((prefix, _ASSET_PLACEHOLDER))
                start = following
            index = following
            continue
        if char == "]":
            _unsupported()
        index += 1
    remaining = line[start:]
    if size + len(remaining.encode("utf-8")) > MAXIMUM_CARD_PRESENTATION_BYTES:
        msg = "presentation_oversize"
        raise ExtractionError(msg)
    parts.append(remaining)
    return "".join(parts)


def _presentation(text: str, budget: ExtractionBudget, *, frontmatter: bool = True) -> str:
    # Charge before split/retained-parts allocation and before examining omitted
    # frontmatter/code. Each source character belongs to exactly one line.
    budget.step(len(text))
    if _CONTROL.search(text):
        msg = "unsafe_content"
        raise ExtractionError(msg)
    lines = text.splitlines(keepends=True)
    in_frontmatter = bool(frontmatter and lines and lines[0].strip() == "---")
    fence: tuple[str, int] | None = None
    parts: list[str] = []
    size = 0
    for number, line in enumerate(lines):
        if in_frontmatter:
            if number and line.strip() in {"---", "..."}:
                in_frontmatter = False
            continue
        matched = _FENCE.fullmatch(line)
        if fence is not None:
            if (
                matched is not None
                and matched[1][0] == fence[0]
                and len(matched[1]) >= fence[1]
                and not matched[2].strip()
            ):
                fence = None
            selected = line
        elif matched is not None:
            if _LANGUAGE.fullmatch(matched[2].strip()) is None:
                _unsupported()
            fence = (matched[1][0], len(matched[1]))
            selected = line
        else:
            selected = _prose(line, budget)
        size += len(selected.encode("utf-8"))
        if size > MAXIMUM_CARD_PRESENTATION_BYTES:
            msg = "presentation_oversize"
            raise ExtractionError(msg)
        parts.append(selected)
    if in_frontmatter or fence is not None:
        _unsupported()
    result = "".join(parts)
    _presentation_bound(result, budget)
    return result


def validate_card_presentation(markdown: str, budget: ExtractionBudget) -> None:
    """Validate derived source on write/read without repairing unsafe evidence.

    Capture has already omitted original YAML. A leading horizontal rule in the
    retained body must therefore be treated as Markdown, not omitted again.
    """
    if contains_secret(markdown, charge=budget.step):
        msg = "secret_suppressed"
        raise ExtractionError(msg)
    if _presentation(markdown, budget, frontmatter=False) != markdown:
        msg = "unsafe_content"
        raise ExtractionError(msg)


def _presentation_bound(result: str, budget: ExtractionBudget) -> None:
    budget.step(len(result))  # before the JSON-string expansion-size pass
    serialized = 2  # JSON opening and closing quotes count independently of UTF-8.
    for char in result:
        serialized += (
            2
            if char in '\\"\b\f\n\r\t'
            else (6 if ord(char) < _CONTROL_END else len(char.encode("utf-8")))
        )
        if serialized > MAXIMUM_CARD_PRESENTATION_BYTES:
            msg = "presentation_oversize"
            raise ExtractionError(msg)


def _failure(reason: str) -> tuple[CardState, CardDiagnostic]:
    classifications: dict[str, tuple[CardState, CardDiagnostic]] = {
        "source_byte_limit": ("oversize", "source_oversize"),
        "presentation_oversize": ("oversize", "presentation_oversize"),
        "unsafe_content": ("unsafe", "unsafe_content"),
        "unsupported_markdown": ("unsupported", "unsupported_markdown"),
        "source_changed": ("failed", "source_changed"),
        "source_size_changed": ("failed", "source_changed"),
        "truncated_source": ("failed", "source_changed"),
        "source_digest_mismatch": ("failed", "source_digest_mismatch"),
        "work_limit": ("failed", "work_limit"),
        "candidate_limit": ("failed", "work_limit"),
        "read_byte_limit": ("failed", "work_limit"),
    }
    return classifications.get(reason, ("failed", "read_failed"))


def capture_repository_card(
    access: SourceAccess, manifest_digest: str, *, archive_id: str
) -> RepositoryCard:
    """Capture only root README, returning fixed non-present failure evidence.

    Original README/manifests/observations stay untouched, including when a
    credential occurs only in frontmatter or an omitted image destination.
    """
    manifest = access.manifest
    entry = access.files.get("README.md")
    state: CardState = "absent"
    diagnostic: CardDiagnostic | None = "readme_absent"
    markdown = None
    if entry is not None:
        try:
            raw = access.read_card()
            access.budget.step(len(raw))  # before UTF-8 decoding/secret inspection
            text = raw.decode("utf-8")
            if contains_secret(text, charge=access.budget.step):
                state, diagnostic = "unsafe", "secret_suppressed"
            else:
                markdown = _presentation(text, access.budget)
                state, diagnostic = "present", None
        except UnicodeError:
            state, diagnostic = "unsupported", "invalid_utf8"
        except ExtractionError as exc:
            state, diagnostic = _failure(exc.reason)
        except OSError, ValueError:
            state, diagnostic = "failed", "read_failed"
    identity = manifest.identity
    return RepositoryCard(
        archive_id=archive_id,
        repository_type=identity.type,
        repository_id=identity.id,
        commit_sha=manifest.commit_sha,
        publication_id=manifest.publication_id,
        publication_generation=manifest.publication_generation,
        manifest_path=str(
            access.layout.archive_relative(
                access.layout.repository(identity).manifest(
                    CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
                )
            )
        ),
        manifest_digest=manifest_digest,
        source_path="README.md" if entry is not None else None,
        expected_source_sha256=entry.sha256 if entry is not None else None,
        captured_at=datetime.now(UTC),
        state=state,
        markdown=markdown,
        presentation_sha256=hashlib.sha256(markdown.encode()).hexdigest()
        if markdown is not None
        else None,
        diagnostics=(diagnostic,) if diagnostic is not None else (),
    )
