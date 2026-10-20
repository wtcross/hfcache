#!/usr/bin/env python3
"""Check or explicitly regenerate decision 145's source-owned browser contract IR."""

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="fail on generated source drift (default)"
    )
    mode.add_argument("--write", action="store_true", help="explicitly replace generated source")
    parser.add_argument(
        "--output", type=Path, help="override destination for an owned test fixture"
    )
    args = parser.parse_args()

    # --help completes above without importing runtime/model/dependency modules.
    from hfcache.wire_schema import render_contracts
    from hfcache.wire_unicode import unicode_bytes

    root = Path(__file__).resolve().parents[1]
    output = args.output or root / "web/src/wire/contracts.json"
    rendered = render_contracts()
    unicode_output = output.with_name("unicode-data.json")
    unicode_rendered = unicode_bytes()
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
        unicode_output.write_bytes(unicode_rendered)
        print("Browser contract IR written.")
        return 0
    if (
        not output.is_file()
        or output.read_text() != rendered
        or not unicode_output.is_file()
        or unicode_output.read_bytes() != unicode_rendered
    ):
        print("Browser contract IR differs; review sources and regenerate explicitly with --write.")
        return 1
    print("Browser contract IR matches audited sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
