#!/usr/bin/env python3
"""Check repository documentation, local links and the complete helper catalog offline.

Run through the locked development environment. Markdown parsing uses the existing
markdown-it-py dependency; no application, credentials, manager or network is used.
"""

import argparse
import html
import os
import posixpath
import re
import stat
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

CATALOG_CELLS = 7
MINIMUM_CELLS = 3

EXCLUDED = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache"}
GENERATED = {".scratch", "dist", "cockpit/dist", "build", ".hypothesis", ".coverage"}
TECHNICAL_IDS = {
    "AD",
    "FS",
    "TX",
    "FW",
    "NG",
    "CP",
    "INV",
    "T",
    "SHA",
    "AES",
    "UTF",
    "ISO",
    "RFC",
    "HTTP",
    "DECISION",
    "UID",
    "GID",
}
# Every helper has an explicit inspection mode; discovering a new file never
# authorizes executing it. The library is sourced only by its reviewed callers.
HELP_MODES = {
    "build-caddy-container.py": "python",
    "build-container.py": "python",
    "check-container-foundation.py": "python",
    "check-container-worker.py": "python",
    "check-docs.py": "python",
    "check-hardening.sh": "bash",
    "check-installations.py": "python",
    "check.sh": "bash",
    "consumer-serve-hfcache-model.sh": "bash",
    "container-service.py": "python",
    "fetch-container-python.py": "python",
    "hardening-probe.py": "python",
    "hfcache-client": "bash",
    "hold-readonly-guard.py": "python",
    "install-container-release.py": "python",
    "install-release.sh": "bash",
    "release-functions.sh": "library",
    "release-profile.py": "python",
    "setup-hfcache-consumer-model-store.sh": "bash",
}


def audience_errors(text):
    """Scan raw prose, markup and code, independently of link rendering."""
    decoded = html.unescape(text)
    for _ in range(3):
        decoded = unquote(decoded)
    errors = [
        "implementation identifier: " + match[0]
        for match in re.finditer(r"\b([A-Z][A-Z0-9]{1,7})-\d{3}\b", decoded, re.IGNORECASE)
        if match[1].upper() not in TECHNICAL_IDS
    ]
    patterns = {
        "execution record path": (
            r"(?:\bdocs/agents(?:/|\b)|(?:^|[\s(`/])(?:\.\./)*agents/|"
            r"\b(?:docs/)?(?:plan|progress)\.md\b|\bdocs/plans/|"
            r"\b(?:AGENTS|CLAUDE)\.md\b)"
        ),
        "execution record link": r"(?:^|[\s(`])(?:\.\./)*(?:plans|tasks)/[^\s`)]*\.md\b",
        "implementation chronology": (
            r"\b(?:implementation\s+(?:plan|phase|stage)|work[ -]package|"
            r"phase\s+(?:\d+|one|two|three)\b|"
            r"stage\s+\d+\s+(?:adds?|introduces?|implements?|enables?)\b)"
        ),
        "numbered acceptance hold": r"\b(?:acceptance|deployment|rollout)\s+holds?\s+\d+",
        "unbounded client claim": (
            r"\b(?:local|operational)\s+(?:CLI|client)"
            r"\b[^.\n]{0,50}\bunbounded\b"
        ),
    }
    for label, pattern in patterns.items():
        if re.search(pattern, decoded, re.IGNORECASE | re.MULTILINE):
            errors.append(label)
    return errors


class HtmlReferences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value is None:
                continue
            if key in {"href", "src"}:
                self.links.append(value)
            if key == "id" or (tag == "a" and key == "name"):
                self.anchors.add(value)


def markdown_references(text):
    """CommonMark links/headings plus explicit HTML; code stays inert."""
    tokens = MarkdownIt("commonmark").parse(text)
    links = []
    anchors = set()
    used = set()
    parser = HtmlReferences()

    def visit(items):
        for token in items:
            if token.type == "link_open":
                links.append(token.attrGet("href"))
            elif token.type == "image":
                links.append(token.attrGet("src"))
            elif token.type in {"html_inline", "html_block"}:
                parser.feed(token.content)
            if token.children:
                visit(token.children)

    visit(tokens)
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        children = tokens[index + 1].children or []
        label = "".join(
            child.content for child in children if child.type in {"text", "code_inline", "image"}
        )
        slug = "".join(c for c in label.lower() if c.isalnum() or c in " _-").replace(" ", "-")
        candidate = slug
        number = 0
        while candidate in used:
            number += 1
            candidate = f"{slug}-{number}"
        used.add(candidate)
        anchors.add(candidate)
    return [link for link in [*links, *parser.links] if link is not None], anchors | parser.anchors


def repository_index(root):
    """Index repository names without following directory or file symlinks."""
    entries = {}
    for directory, names, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        names[:] = [
            name
            for name in names
            if name not in EXCLUDED
            and (parent / name).relative_to(root).as_posix() not in GENERATED
        ]
        for name in [*names, *files]:
            path = parent / name
            entries[path.relative_to(root).as_posix()] = path
    return entries


def human_documents(entries):
    return [
        path
        for name, path in sorted(entries.items())
        if name.endswith(".md")
        and name not in {"AGENTS.md", "CLAUDE.md"}
        and not name.startswith("docs/agents/")
    ]


def local_target(root, source, raw, entries):
    """Resolve indexed local paths; refuse escapes before inspecting a target."""
    parsed = urlsplit(html.unescape(raw))
    if parsed.scheme or parsed.netloc:
        return None, ""
    relative = unquote(parsed.path)
    name = (
        source.relative_to(root).as_posix()
        if not relative
        else posixpath.normpath(
            relative.lstrip("/")
            if relative.startswith("/")
            else posixpath.join(source.relative_to(root).parent.as_posix(), relative)
        )
    )
    for _ in range(40):
        if name == ".." or name.startswith("../"):
            return None, "repository escape"
        parts = name.split("/")
        redirected = False
        for length in range(1, len(parts) + 1):
            prefix = "/".join(parts[:length])
            path = entries.get(prefix)
            if path is None or not path.is_symlink():
                continue
            destination = path.readlink()
            if destination.is_absolute():
                try:
                    base = destination.relative_to(root).as_posix()
                except ValueError:
                    return None, "symlink escape"
            else:
                base = posixpath.join(posixpath.dirname(prefix), destination.as_posix())
            name = posixpath.normpath(posixpath.join(base, *parts[length:]))
            redirected = True
            break
        if not redirected:
            if name == ".":
                return root, unquote(parsed.fragment)
            return entries.get(name), unquote(parsed.fragment)
    return None, "symlink cycle"


def check_links(root, documents, entries=None):
    entries = repository_index(root) if entries is None else entries
    errors = []
    cache = {}
    for document in documents:
        if document.relative_to(root).as_posix() not in entries or document.is_symlink():
            errors.append(f"{document.relative_to(root)}: unsafe source document")
            continue
        links, _ = markdown_references(document.read_text())
        for link in links:
            try:
                parsed = urlsplit(html.unescape(link))
                if parsed.scheme or parsed.netloc:
                    continue
                target, fragment = local_target(root, document, link, entries)
            except ValueError:
                target, fragment = None, "invalid local URL"
            if target is None:
                errors.append(
                    f"{document.relative_to(root)}: missing/unsafe link {link} ({fragment})"
                )
            elif (
                target.relative_to(root).as_posix() == "docs/agents"
                or target.relative_to(root).as_posix().startswith("docs/agents/")
            ) or target.name in {
                "AGENTS.md",
                "CLAUDE.md",
            }:
                errors.append(f"{document.relative_to(root)}: agent record target {link}")
            elif fragment and target.suffix.lower() == ".md":
                if target not in cache:
                    cache[target] = markdown_references(target.read_text())[1]
                if fragment not in cache[target]:
                    errors.append(f"{document.relative_to(root)}: missing anchor {link}")
    return errors


def indexed_helpers(entries):
    helpers = set()
    errors = []
    for name, path in entries.items():
        if name == "scripts" and path.is_symlink():
            errors.append("unsafe helper directory symlink")
        if name.startswith("scripts/"):
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                errors.append("unsafe helper symlink: " + name)
            elif stat.S_ISREG(mode) and path.suffix != ".pyc":
                helpers.add(name.removeprefix("scripts/"))
    return helpers, errors


def inventory_errors(root, modes=None):
    modes = HELP_MODES if modes is None else modes
    entries = repository_index(root)
    helpers, errors = indexed_helpers(entries)
    rows = []
    catalog = entries.get("docs/scripts.md")
    if catalog is None or not stat.S_ISREG(catalog.lstat().st_mode):
        errors.append("missing or unsafe helper catalog")
    else:
        for line in catalog.read_text().splitlines():
            cells = re.split(r"(?<!\\)\|", line)
            if len(cells) < MINIMUM_CELLS:
                continue
            targets = re.findall(r"\]\(\.\./scripts/([^)]+)\)", cells[1])
            if targets:
                rows.extend(targets)
                if (
                    len(targets) != 1
                    or len(cells) != CATALOG_CELLS
                    or any(not cell.strip() for cell in cells[1:-1])
                ):
                    errors.append("incomplete helper row: " + cells[1].strip())
    if Counter(rows) != Counter(dict.fromkeys(helpers, 1)):
        errors.append(
            f"helper catalog differs: missing={sorted(helpers - set(rows))}, "
            f"stale={sorted(set(rows) - helpers)}, "
            f"duplicates={sorted(name for name, count in Counter(rows).items() if count != 1)}"
        )
    if set(modes) != helpers or any(
        value not in {"python", "bash", "library"} for value in modes.values()
    ):
        errors.append("helper inspection classifications differ from repository")
    return errors


def check(root):
    entries = repository_index(root)
    documents = human_documents(entries)
    errors = []
    for path in documents:
        if path.is_symlink():
            errors.append(f"{path.relative_to(root)}: unsupported human symlink")
            continue
        source = path.read_text()
        rendered = " ".join(
            token.content
            for block in MarkdownIt("commonmark").parse(source)
            for token in (block.children or [])
            if token.type in {"text", "code_inline"}
        )
        # Inline formatting must not split an implementation identifier.
        rendered_compact = "".join(
            token.content
            for block in MarkdownIt("commonmark").parse(source)
            for token in (block.children or [])
            if token.type in {"text", "code_inline"}
        )
        errors.extend(
            f"{path.relative_to(root)}: {error}"
            for error in sorted(
                set(
                    audience_errors(source)
                    + audience_errors(rendered)
                    + audience_errors(rendered_compact)
                )
            )
        )
    return documents, [*errors, *check_links(root, documents, entries), *inventory_errors(root)]


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    documents, errors = check(root)
    for error in errors:
        print(error)
    if errors:
        return 1
    print(
        f"documentation alignment passed: {len(documents)} human documents; "
        f"{len(HELP_MODES)} helpers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
