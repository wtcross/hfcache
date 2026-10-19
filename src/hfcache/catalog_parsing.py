"""Small bounded data parsers; repository content never supplies constructors."""

import json
import re
from typing import Any

MAXIMUM_SOURCE_BYTES = 1024 * 1024
MAXIMUM_NODES = 100_000
MAXIMUM_YAML_DEPTH = 64
MAXIMUM_JSON_DEPTH = 32
MAXIMUM_LINES = 20_000
CONTROL_END = 32
SURROGATE_START = 0xD800
SURROGATE_END = 0xDFFF


class ExtractionError(ValueError):
    """A fixed diagnostic classification, never rejected source text."""

    def __init__(self, reason: str, *, unsupported: bool = False) -> None:
        self.reason = reason
        self.unsupported = unsupported
        super().__init__(reason)


def text_source(raw: bytes) -> str:
    if len(raw) > MAXIMUM_SOURCE_BYTES:
        msg = "source_byte_limit"
        raise ExtractionError(msg)
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        msg = "invalid_unicode"
        raise ExtractionError(msg) from exc
    _unicode(text)
    return text


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            msg = "duplicate_key"
            raise ExtractionError(msg)
        result[key] = value
    return result


def _constant(_: str) -> None:
    msg = "nonfinite_number"
    raise ExtractionError(msg)


def _structure(text: str) -> None:
    depth = nodes = 0
    quoted = escaped = False
    for c in text:
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c in "[{":
            depth += 1
            nodes += 1
        elif c in "]}":
            depth -= 1
        elif c in ",:":
            nodes += 1
        if depth > MAXIMUM_JSON_DEPTH or nodes > MAXIMUM_NODES:
            msg = "structure_limit"
            raise ExtractionError(msg)


def parse_json(raw: bytes) -> Any:  # noqa: ANN401 - constrained inert JSON values
    text = text_source(raw)
    _structure(text)  # before json.loads can allocate nested containers
    try:
        result = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError) as exc:
        if isinstance(exc, ExtractionError):
            raise
        msg = "invalid_json"
        raise ExtractionError(msg) from exc
    pending = [(result, 0)]
    nodes = 0
    while pending:
        value, depth = pending.pop()
        nodes += 1
        if nodes > MAXIMUM_NODES or depth > MAXIMUM_JSON_DEPTH:
            msg = "structure_limit"
            raise ExtractionError(msg)
        if isinstance(value, dict):
            for key, child in value.items():
                _unicode(key)
                pending.append((child, depth + 1))
        elif isinstance(value, list):
            pending.extend((child, depth + 1) for child in value)
        elif isinstance(value, str):
            _unicode(value)
        elif isinstance(value, float) and not (-float("inf") < value < float("inf")):
            msg = "nonfinite_number"
            raise ExtractionError(msg)
    return result


def _unicode(value: str) -> None:
    if any(
        SURROGATE_START <= ord(c) <= SURROGATE_END or (ord(c) < CONTROL_END and c not in "\n\r\t")
        for c in value
    ):
        msg = "invalid_unicode"
        raise ExtractionError(msg)


def _uncomment(line: str) -> str:
    quote = ""
    escaped = False
    for i, c in enumerate(line):
        if escaped:
            escaped = False
        elif quote == '"' and c == "\\":
            escaped = True
        elif c == quote:
            quote = ""
        elif not quote and c in "\"'" and (not i or line[i - 1] in " [:,-"):
            quote = c
        elif not quote and c == "#" and (not i or line[i - 1].isspace()):
            return line[:i].rstrip()
    if quote:
        msg = "unsupported_yaml"
        raise ExtractionError(msg, unsupported=True)
    return line.rstrip()


def _scalar(value: str) -> Any:  # noqa: ANN401 - only inert scalar/list values
    if value.startswith("[") and value.endswith("]"):
        if '"' in value:
            try:
                parsed = parse_json(value.encode())
            except ExtractionError as exc:
                if exc.reason != "invalid_json":
                    raise
                msg = "unsupported_yaml"
                raise ExtractionError(msg, unsupported=True) from exc
            if not isinstance(parsed, list) or any(isinstance(v, (list, dict)) for v in parsed):
                msg = "unsupported_yaml"
                raise ExtractionError(msg, unsupported=True)
            return parsed
        # Other flow lists accept plain scalars; no general flow YAML grammar.
        if any(c in value[1:-1] for c in "[]{}\"'"):
            msg = "unsupported_yaml"
            raise ExtractionError(msg, unsupported=True)
        items = [] if not value[1:-1].strip() else value[1:-1].split(",")
        return [_plain(item.strip()) for item in items]
    if value.startswith('"'):
        parsed = parse_json(value.encode())
        if isinstance(parsed, str):
            return parsed
    elif value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    else:
        return _plain(value)
    msg = "unsupported_yaml"
    raise ExtractionError(msg, unsupported=True)


def _plain(value: str) -> Any:  # noqa: ANN401 - retain scalar types without coercing declarations
    if not value or value[0] in "!&*|>{}[?%@`" or ": " in value:
        msg = "unsupported_yaml"
        raise ExtractionError(msg, unsupported=True)
    if value in {"true", "false", "null"} or re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value):
        return parse_json(value.encode())
    return value


class _Yaml:
    """Conservative block mappings/sequences and scalar lists, no YAML constructors."""

    def __init__(self, text: str) -> None:
        self.lines: list[tuple[int, str]] = []
        self.position = 0
        if sum(text.count(c) for c in ",:\n") > MAXIMUM_NODES:
            msg = "structure_limit"
            raise ExtractionError(msg)
        if text.count("\n") >= MAXIMUM_LINES:
            msg = "structure_limit"
            raise ExtractionError(msg)
        for line in text.split("\n"):
            if len(self.lines) >= MAXIMUM_LINES or "\t" in line:
                msg = "structure_limit"
                raise ExtractionError(msg)
            clean = _uncomment(line)
            if clean.strip():
                self.lines.append((len(clean) - len(clean.lstrip(" ")), clean.lstrip(" ")))

    def block(self, indent: int, depth: int) -> Any:  # noqa: ANN401 - inert parsed tree
        if depth > MAXIMUM_YAML_DEPTH:
            msg = "structure_limit"
            raise ExtractionError(msg)
        if self.lines[self.position][0] != indent:
            msg = "invalid_yaml"
            raise ExtractionError(msg)
        if self.lines[self.position][1].startswith("- ") or self.lines[self.position][1] == "-":
            result = []
            while self.position < len(self.lines) and self.lines[self.position][0] == indent:
                line = self.lines[self.position][1]
                if line != "-" and not line.startswith("- "):
                    break
                self.position += 1
                tail = line[1:].strip()
                if re.match(r"[A-Za-z_][A-Za-z0-9_.-]*:", tail):
                    result.append(self.mapping(indent + 2, depth + 1, initial=tail))
                else:
                    result.append(self.value(tail, indent, depth + 1))
            return result
        return self.mapping(indent, depth + 1)

    def value(self, tail: str, indent: int, depth: int) -> Any:  # noqa: ANN401
        if tail:
            return _scalar(tail)
        if self.position < len(self.lines):
            next_indent, line = self.lines[self.position]
            if next_indent > indent or (next_indent == indent and line.startswith("-")):
                return self.block(next_indent, depth + 1)
        return None

    def mapping(self, indent: int, depth: int, *, initial: str | None = None) -> dict[str, Any]:
        if depth > MAXIMUM_YAML_DEPTH:
            msg = "structure_limit"
            raise ExtractionError(msg)
        result: dict[str, Any] = {}
        while initial is not None or (
            self.position < len(self.lines) and self.lines[self.position][0] == indent
        ):
            if initial is not None:
                line, initial = initial, None
            else:
                line = self.lines[self.position][1]
                self.position += 1
            matched = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_.-]*):(?: +(.*))?", line)
            if matched is None:
                msg = "unsupported_yaml"
                raise ExtractionError(msg, unsupported=True)
            key, tail = matched.group(1), matched.group(2) or ""
            if key in result:
                msg = "duplicate_key"
                raise ExtractionError(msg)
            result[key] = self.value(tail, indent, depth + 1)
        return result


def parse_card(raw: bytes) -> dict[str, Any]:
    text = text_source(raw)
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}  # a body without optional front matter is not an error
    if text.count("\n") >= MAXIMUM_LINES:
        msg = "structure_limit"
        raise ExtractionError(msg)
    lines = text.replace("\r\n", "\n").split("\n")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        msg = "unterminated_frontmatter"
        raise ExtractionError(msg) from exc
    frontmatter = "\n".join(lines[1:end])
    parser = _Yaml(frontmatter)
    if not parser.lines:
        return {}
    result = parser.block(0, 0)
    if parser.position != len(parser.lines) or not isinstance(result, dict):
        msg = "unsupported_yaml"
        raise ExtractionError(msg, unsupported=True)
    return result
