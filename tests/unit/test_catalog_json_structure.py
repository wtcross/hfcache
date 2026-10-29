"""INV-018: reject excessive authority structure before allocating JSON containers."""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import hfcache.catalog_storage as storage
from hfcache.catalog_models import RepositoryTagSnapshot
from hfcache.errors import IntegrityError
from hfcache.models import dump
from tests.fixtures import examples


def refused(raw):
    with pytest.raises(IntegrityError) as error:
        storage._json_structure(raw)
    assert [problem.code for problem in error.value.problems] == ["HFVER007"]


@pytest.mark.parametrize("opening", [b"[", b"{"])
def test_exact_existing_depth_bound_and_next_container_refused(opening):
    closing = b"]" if opening == b"[" else b"}"
    assert storage.MAXIMUM_JSON_DEPTH == 32
    storage._json_structure(opening * 32 + closing * 32)
    refused(opening * 33 + closing * 33)


def test_exact_existing_structural_token_bound_and_next_member_refused():
    assert storage.MAXIMUM_JSON_NODES == 100_000
    storage._json_structure(b"[" + b",".join([b"0"] * 100_000) + b"]")
    refused(b"[" + b",".join([b"0"] * 100_001) + b"]")
    # Each object pair contributes one colon, plus inter-pair commas and its opener.
    storage._json_structure(b"{" + b",".join([b'"key":0'] * 50_000) + b"}")
    refused(b"{" + b",".join([b'"key":0'] * 50_001) + b"}")


@pytest.mark.parametrize("budget", ["depth", "tokens"])
def test_unknown_field_structure_is_refused_before_json_container_allocation(monkeypatch, budget):
    extra = (
        b"[" * 33 + b"]" * 33 if budget == "depth" else b"[" + b",".join([b"0"] * 100_001) + b"]"
    )

    def forbidden_decode(*_args, **_kwargs):
        pytest.fail("The authoritative JSON decoder ran before the structural budget refusal.")

    monkeypatch.setattr(storage.json, "loads", forbidden_decode)
    with pytest.raises(IntegrityError) as error:
        storage.parse_record(
            RepositoryTagSnapshot, b'{"schema_version":1,"skipped":' + extra + b"}"
        )
    assert [problem.code for problem in error.value.problems] == ["HFVER007"]


@pytest.mark.parametrize("backslashes", [0, 1, 2, 3, 4, 63, 64, 4095, 4096])
def test_quote_escaping_uses_entire_raw_backslash_run_parity(backslashes):
    raw = b'["' + b"\\" * backslashes + b'"' + b"[" * 33 + b'"]'
    if backslashes % 2:
        # The escaped quote and following brackets remain one actual JSON string.
        assert isinstance(json.loads(raw)[0], str)
        storage._json_structure(raw)
    else:
        # An unescaped quote exposes the nesting even though later grammar is invalid.
        refused(raw)


def test_unicode_escapes_are_raw_string_content_not_decoded_structural_bytes():
    raw = b'["\\u0022\\u005c' + b"[{:}]" * 50_000 + b'"]'
    assert isinstance(json.loads(raw)[0], str)
    storage._json_structure(raw)


def test_long_utf8_quoted_punctuation_and_unterminated_string_have_no_structure():
    payload = ("資料 [ ] { } , : " * 100_000).encode()
    storage._json_structure(b'["' + payload + b'"]')
    # Grammar validation remains the responsibility of the existing JSON parser.
    storage._json_structure(b'["' + payload + b"\\")


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":"unterminated',
        b'{"x":"\\',
        b"[]:",
        b'{"x":0,"x":1}',
        b'{"schema_version":NaN}',
        b'{"schema_version":1,"x":"\xff"}',
        b"]" * 32,
    ],
)
def test_original_parser_keeps_malformed_duplicate_nonfinite_and_utf8_refusals(raw):
    with pytest.raises(IntegrityError) as error:
        storage.parse_record(RepositoryTagSnapshot, raw)
    assert [problem.code for problem in error.value.problems] == ["HFVER007"]


def test_real_tag_record_still_roundtrips_without_structural_reinterpretation():
    original = examples.tag_snapshot()
    assert storage.parse_record(RepositoryTagSnapshot, dump(original)) == original


def tree_structure(value):
    """Independent tree oracle: count containers, separators and object key/value pairs."""
    pending = [(value, 1)]
    maximum_depth = tokens = 0
    while pending:
        node, depth = pending.pop()
        if isinstance(node, dict):
            tokens += 1 + len(node) + max(0, len(node) - 1)
            maximum_depth = max(maximum_depth, depth)
            pending.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            tokens += 1 + max(0, len(node) - 1)
            maximum_depth = max(maximum_depth, depth)
            pending.extend((child, depth + 1) for child in node)
    return maximum_depth, tokens


_TEXT = st.text(alphabet='字é\\"{}[],:\n\t0a', max_size=20)
_TREES = st.recursive(
    st.none() | st.booleans() | st.integers(-5, 5) | _TEXT,
    lambda children: st.lists(children, max_size=6) | st.dictionaries(_TEXT, children, max_size=5),
    max_leaves=80,
)


@settings(max_examples=250, deadline=None)
@given(
    value=_TREES,
    ascii_only=st.booleans(),
    node_limit=st.integers(0, 80),
    depth_limit=st.integers(0, 7),
)
def test_structural_budget_matches_independent_tree_oracle(
    value, ascii_only, node_limit, depth_limit
):
    raw = json.dumps(value, ensure_ascii=ascii_only).encode()
    depth, tokens = tree_structure(value)
    # Lowered test budgets exercise both decisions without changing product limits.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(storage, "MAXIMUM_JSON_DEPTH", depth_limit)
        patch.setattr(storage, "MAXIMUM_JSON_NODES", node_limit)
        if depth > depth_limit or tokens > node_limit:
            refused(raw)
        else:
            storage._json_structure(raw)
