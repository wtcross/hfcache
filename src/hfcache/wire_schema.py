"""Deterministic audited browser schema IR (decision 145; FW-03/INV-005).

Pydantic's core structure preserves array bounds that its JSON Schema currently
mislabels. Both exported schema modes are separately checked for unsupported
keywords; every custom hook is pinned by reviewed source rather than ignored.
"""

import hashlib
import inspect
import json
import math
import re
import unicodedata
from collections.abc import Callable  # noqa: TC003 - exported runtime callable contract
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from hfcache.wire_audit import AUDITED_HOOKS, AUDITED_SOURCES
from hfcache.wire_registry import (
    AUTHORITIES,
    RESULT_ROUTES,
    ROUTES,
    FlatExtension,
    request_authorities,
)

type Node = dict[str, Any]
_KEYWORDS = frozenset(
    {
        "$defs",
        "$ref",
        "additionalProperties",
        "anyOf",
        "oneOf",
        "discriminator",
        "const",
        "default",
        "description",
        "enum",
        "format",
        "items",
        "maxLength",
        "maximum",
        "minLength",
        "minimum",
        "properties",
        "propertyNames",
        "required",
        "title",
        "type",
        "minItems",
        "maxItems",
        "pattern",
    }
)
_CORE_KEYS = frozenset(
    {
        "type",
        "schema",
        "ref",
        "schema_ref",
        "metadata",
        "function",
        "serialization",
        "cls",
        "config",
        "custom_init",
        "root_model",
        "fields",
        "model_name",
        "computed_fields",
        "choices",
        "items_schema",
        "variadic_item_index",
        "min_length",
        "max_length",
        "pattern",
        "ge",
        "le",
        "strict",
        "default",
        "default_factory",
        "default_factory_takes_data",
        "validate_default",
        "keys_schema",
        "values_schema",
        "definitions",
        "expected",
        "json_schema",
        "python_schema",
        "lax_schema",
        "strict_schema",
        "json_return_type",
        "info_arg",
        "return_schema",
        "when_used",
        "discriminator",
        "from_attributes",
        "serialization_alias",
        "validation_alias",
        "serialization_exclude",
        "frozen",
        "microseconds_precision",
    }
)


def check_json_schema(node: object) -> None:
    """Never silently lower a newly introduced validation keyword."""
    if not isinstance(node, dict):
        message = "JSON Schema must be an object"
        raise TypeError(message)
    unknown = node.keys() - _KEYWORDS
    if unknown:
        message = f"Unaudited JSON Schema keywords: {sorted(unknown)}"
        raise ValueError(message)
    for key, value in node.items():
        if key == "format":
            if value not in {"date-time", "path"}:
                message = f"Unaudited JSON Schema format {value}"
                raise ValueError(message)
            continue
        if key in {"$defs", "properties"}:
            for child in value.values():
                check_json_schema(child)
        elif key in {"anyOf", "oneOf"}:
            for child in value:
                check_json_schema(child)
        elif key == "discriminator":
            if (
                not isinstance(value, dict)
                or set(value) != {"propertyName", "mapping"}
                or value["propertyName"] != "kind"
                or not isinstance(value["mapping"], dict)
                or any(not isinstance(target, str) for target in value["mapping"].values())
            ):
                message = "Only the fixed managed-edit kind discriminator is audited"
                raise ValueError(message)
        elif key in {"items", "additionalProperties", "propertyNames"} and isinstance(value, dict):
            check_json_schema(value)


def hook_identity(function: Callable[..., object]) -> tuple[str, Callable[..., object]]:
    held = function.func if isinstance(function, partial) else function
    return held.__module__ + "." + held.__qualname__, held


def source_hash(function: Callable[..., object]) -> str:
    return hashlib.sha256(inspect.getsource(function).encode()).hexdigest()


class Exporter:
    """Lower known pure model structures and refuse every unreviewed hook."""

    def __init__(self) -> None:
        self.definitions: dict[str, Node] = {}
        self.semantics: dict[str, Node] = {}
        self.sources: dict[str, str] = {}
        self.request = False

    def hook(self, function: Callable[..., object], *, phase: str) -> str | None:
        identity, held = hook_identity(function)
        digest = source_hash(held)
        if AUDITED_HOOKS.get(identity) != digest:
            message = f"Unaudited or changed wire validator: {identity}"
            raise ValueError(message)
        module = inspect.getmodule(held)
        if module is not None and module.__file__ is not None:
            path = Path(module.__file__)
            # Identity is portable across editable installs and wheels.
            relative = "src/" + "/".join(module.__name__.split(".")) + ".py"
            self.sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        if identity in {
            "hfcache.models.as_tuple",
            "hfcache.config._as_tuple",
            "hfcache.models.format_timestamp",
            "pydantic._internal._validators.max_length_validator",
            "pydantic._internal._validators.min_length_validator",
            "pydantic._internal._generate_schema.GenerateSchema._path_schema.<locals>.path_validator",
            "pydantic._internal._generate_schema.GenerateSchema._path_schema.<locals>.ser_path",
        }:
            return None
        identifier = (
            "timestamp.serialized" if identity == "hfcache.models.parse_timestamp" else identity
        )
        self.semantics[identifier] = {"phase": phase, "source_hash": digest}
        return identifier

    def node(self, schema: dict[str, Any], *, path: str = "") -> Node:  # noqa: PLR0911, PLR0912, PLR0915 - explicit closed grammar
        _audit_metadata(schema)
        unknown = schema.keys() - _CORE_KEYS
        if unknown:
            message = f"Unaudited core schema keys: {sorted(unknown)}"
            raise ValueError(message)
        if "ref" in schema:
            name = schema["ref"].split(":", 1)[0].rsplit(".", 1)[-1]
            name = ("Request" if self.request else "") + name
            if name not in self.definitions:
                self.definitions[name] = {"kind": "null", "semantic_ids": []}
                self.definitions[name] = self.node(
                    {key: value for key, value in schema.items() if key != "ref"}, path=name
                )
            return {"kind": "ref", "name": name, "semantic_ids": []}
        kind = schema["type"]
        serial = schema.get("serialization")
        if isinstance(serial, dict) and "function" in serial:
            self.hook(serial["function"], phase="field")
        if kind in {"function-before", "function-after"}:
            function = schema["function"]["function"]
            identity, _ = hook_identity(function)
            inner = schema["schema"]
            if identity == "hfcache.models.parse_timestamp":
                if (
                    inner["type"] != "datetime"
                    or not isinstance(serial, dict)
                    or hook_identity(serial["function"])[0] != "hfcache.models.format_timestamp"
                ):
                    message = "Timestamp requires its audited canonical serializer"
                    raise ValueError(message)
                inner = {"type": "str"}
            node = self.node(inner, path=path)
            semantic = self.hook(
                function, phase="model" if node["kind"] in {"ref", "object"} else "field"
            )
            if isinstance(function, partial) and identity.startswith(
                "pydantic._internal._validators."
            ):
                keywords = function.keywords
                bound = "min" if "min_length" in keywords else "max"
                key = bound + ("_items" if node["kind"] == "array" else "_codepoints")
                node[key] = keywords[bound + "_length"]
            if semantic is not None:
                node["semantic_ids"] = list(dict.fromkeys([*node["semantic_ids"], semantic]))
            return node
        if kind == "definitions":
            for definition in schema["definitions"]:
                self.node(definition)
            return self.node(schema["schema"], path=path)
        if kind == "definition-ref":
            name = schema["schema_ref"].split(":", 1)[0].rsplit(".", 1)[-1]
            return {
                "kind": "ref",
                "name": ("Request" if self.request else "") + name,
                "semantic_ids": [],
            }
        if kind in {"default", "model-field"}:
            return self.node(schema["schema"], path=path)
        if kind == "model":
            config = schema["config"]
            if config.get("strict") is not True or config.get("extra_fields_behavior") != "forbid":
                message = "Wire models require strict validation and forbidden extra fields"
                raise ValueError(message)
            return self.node(schema["schema"], path=path)
        if kind == "model-fields":
            if schema["computed_fields"]:
                message = "Computed fields require a serialization audit"
                raise ValueError(message)
            fields = []
            for name, field in schema["fields"].items():
                _audit_metadata(field)
                if field.get("serialization_alias") or field.get("serialization_exclude"):
                    message = "Field serialization aliases/exclusions require an audit"
                    raise TypeError(message)
                node = self.node(field["schema"], path=path + "." + name)
                if name in {
                    "created_at",
                    "updated_at",
                    "completed_at",
                    "started_at",
                    "at",
                    "published_at",
                    "grace_expires_at",
                }:
                    self.semantics["timestamp.wire"] = {
                        "phase": "field",
                        "source_hash": AUDITED_HOOKS["hfcache.models.parse_timestamp"],
                    }
                    # Durable Timestamp already has the stricter serializer profile.
                    _timestamp_wire(node)
                fields.append(
                    {
                        "name": name,
                        "node": node,
                        "required": not self.request or field["schema"]["type"] != "default",
                    }
                )
            return {"kind": "object", "fields": fields, "extra": "forbid", "semantic_ids": []}
        if kind == "tagged-union":
            if schema["discriminator"] != "kind" or set(schema["choices"]) != {
                "repository-upsert",
                "repository-remove",
                "settings-replace",
            }:
                message = "Only the closed managed-edit union is audited"
                raise ValueError(message)
            return {
                "kind": "union",
                "choices": [self.node(choice, path=path) for choice in schema["choices"].values()],
                "semantic_ids": [],
            }
        if kind in {"nullable", "union"}:
            choices = (
                [schema["schema"], {"type": "none"}] if kind == "nullable" else schema["choices"]
            )
            return {
                "kind": "union",
                "choices": [self.node(choice, path=path) for choice in choices],
                "semantic_ids": [],
            }
        if kind == "literal":
            choices = []
            for value in schema["expected"]:
                if (
                    isinstance(value, int)
                    and not isinstance(value, bool)
                    and abs(value) > 2**53 - 1
                ):
                    message = "Unsafe numeric literal"
                    raise TypeError(message)
                if isinstance(value, float) or not isinstance(value, (str, int, bool, type(None))):
                    message = "Unaudited literal type"
                    raise TypeError(message)
                choices.append({"kind": "literal", "value": value, "semantic_ids": []})
            return (
                choices[0]
                if len(choices) == 1
                else {"kind": "union", "choices": choices, "semantic_ids": []}
            )
        if kind in {"str", "datetime"}:
            if kind == "datetime":
                message = "Datetime requires an audited timestamp serializer"
                raise ValueError(message)
            semantics = []
            return {
                "kind": "string",
                "min_codepoints": schema.get("min_length"),
                "max_codepoints": schema.get("max_length"),
                "pattern": schema.get("pattern"),
                "semantic_ids": semantics,
            }
        if kind in {"int", "float"}:
            for key in ("ge", "le"):
                if key in schema and not math.isfinite(schema[key]):
                    message = "Nonfinite schema bound"
                    raise ValueError(message)
            return {
                "kind": "integer" if kind == "int" else "number",
                "minimum": str(schema["ge"]) if "ge" in schema else None,
                "maximum": str(schema["le"]) if "le" in schema else None,
                "semantic_ids": [],
            }
        if kind in {"bool", "none"}:
            return {"kind": "boolean" if kind == "bool" else "null", "semantic_ids": []}
        if kind == "tuple":
            items = schema["items_schema"]
            if len(items) != 1 or schema.get("variadic_item_index") != 0:
                message = "Only homogeneous JSON arrays are audited"
                raise ValueError(message)
            return {
                "kind": "array",
                "items": self.node(items[0], path=path + "[]"),
                "min_items": schema.get("min_length"),
                "max_items": schema.get("max_length"),
                "semantic_ids": [],
            }
        if kind == "dict" and path in {
            "Envelope.data",
            "EnvelopeProblem.context",
            "Remediation.evidence",
        }:
            return {
                "kind": "json_value",
                "object_only": True,
                "max_depth": 32,
                "max_nodes": 100000,
                "semantic_ids": [],
            }
        if kind == "dict" and path == "HostFacts.units":
            # This finite-key mapping is also constrained by exact_units. Lower
            # only that reviewed combination to four required object fields;
            # there is no generic dictionary or permissive JSON fallback.
            keys = schema["keys_schema"]
            expected = {
                "hfcache-sync.service",
                "hfcache-verify.service",
                "hfcache-sync.timer",
                "hfcache-verify.timer",
            }
            if keys.get("type") != "literal" or set(keys.get("expected", ())) != expected:
                message = "Host unit keys changed; review finite mapping lowering"
                raise ValueError(message)
            return {
                "kind": "object",
                "fields": [
                    {
                        "name": name,
                        "node": self.node(schema["values_schema"], path=path + "." + name),
                        "required": True,
                    }
                    for name in sorted(expected)
                ],
                "extra": "forbid",
                "semantic_ids": [],
            }
        if kind == "lax-or-strict" and "json_schema" in schema.get("strict_schema", {}):
            # Pydantic's standard pathlib adapter; custom input grammar remains audited.
            strict = schema["strict_schema"]["json_schema"]
            self.hook(strict["function"]["function"], phase="field")
            return {
                "kind": "string",
                "min_codepoints": None,
                "max_codepoints": None,
                "pattern": None,
                "semantic_ids": [],
            }
        message = f"Unaudited core schema type {kind} at {path}"
        raise ValueError(message)

    def authority(self, name: str, authority: object, *, request: bool = False) -> None:
        self.request = request
        flat = isinstance(authority, FlatExtension)
        adapter = TypeAdapter(authority.base if flat else authority)
        for mode in ("validation", "serialization"):
            check_json_schema(adapter.json_schema(mode=mode))
        node = self.node(dict(adapter.core_schema))
        if flat:
            base = self.definitions[node["name"]]
            node = {
                **base,
                "fields": [
                    *base["fields"],
                    {
                        "name": authority.locator,
                        "node": {
                            "kind": "string",
                            "min_codepoints": None,
                            "max_codepoints": None,
                            "pattern": None,
                            "semantic_ids": ["hfcache.models._archive_path"],
                        },
                        "required": True,
                    },
                ],
            }
        if name in self.definitions and self.definitions[name] != node and node.get("name") != name:
            message = f"Conflicting schema name {name}"
            raise ValueError(message)
        if node.get("name") != name:
            self.definitions[name] = node


def build_contracts() -> dict[str, Any]:
    """Return portable IR; no request, policy or application has been created."""
    exporter = Exporter()
    _audit_sources(exporter)
    for name, authority in sorted(AUTHORITIES.items()):
        exporter.authority(name, authority)
    for name, authority in sorted(request_authorities().items()):
        exporter.authority("Request" + name, authority, request=True)
    routes = []
    for route in ROUTES:
        row: Node = asdict(route)
        query = row.pop("query_group")
        if row["request_body"] is not None:
            row["request_body"] = "Request" + row["request_body"]
        row["path_parameters"] = [
            {"name": name, "node": _parameter(name)}
            for name in re.findall(r"\{([^{}]+)\}", route.path)
        ]
        row["query_parameters"] = _queries(query)
        routes.append(row)
    for name in ("wire_models", "wire_registry", "wire_schema", "wire_audit", "wire_unicode"):
        path = Path(__file__).with_name(name + ".py")
        exporter.sources["src/hfcache/" + name + ".py"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    source = json.dumps(
        {"sources": exporter.sources, "unicode": unicodedata.unidata_version},
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "schema_version": 1,
        "source_digest": hashlib.sha256(source.encode()).hexdigest(),
        "definitions": exporter.definitions,
        "semantics": exporter.semantics,
        "routes": routes,
        "operation_results": [asdict(route) for route in RESULT_ROUTES],
    }


def installed_source_digest() -> str:
    """Compute the installed Python authority identity without frontend files.

    Enabled UI startup calls this once. Full source/semantic auditing is retained;
    neither the configured manifest nor a generated digest constant is trusted.
    Optional transport applications and archive policy are never initialized.
    """
    digest = build_contracts()["source_digest"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        message = "Invalid installed wire authority digest"
        raise ValueError(message)
    return digest


def _audit_sources(exporter: Exporter) -> None:
    from importlib.util import find_spec  # noqa: PLC0415 - does not initialize application modules

    for name, expected in AUDITED_SOURCES.items():
        spec = find_spec(name)
        if spec is None or spec.origin is None:
            message = f"Missing audited source module {name}"
            raise ValueError(message)
        actual = hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest()
        if actual != expected:
            message = f"Changed audited source module {name}; review helpers and semantic ports"
            raise ValueError(message)
        exporter.sources["python/" + name] = actual
    contexts = {
        "api.problem.classification": ("hfcache.taxonomy", "hfcache.client"),
        "run.report": ("hfcache.client", "hfcache.reporting"),
        "publication.reference": ("hfcache.identity", "hfcache.paths", "hfcache.models"),
        "publication.manifest": ("hfcache.identity", "hfcache.manifests", "hfcache.paths"),
        "publication.card": (
            "hfcache.card_models",
            "hfcache.services.card_queries",
            "hfcache.catalog_storage",
            "hfcache.metadata",
            "hfcache.identity",
            "hfcache.paths",
        ),
        "operation.identity": ("hfcache.client", "hfcache.client_models"),
        "operation.events": ("hfcache.client", "hfcache.client_models"),
        "operation.result": ("hfcache.client", "hfcache.client_models"),
        "catalog.response": ("hfcache.client_catalog", "hfcache.catalog_query_models"),
        "catalog.facet": ("hfcache.client_catalog", "hfcache.catalog_query_models"),
        "catalog.publication": ("hfcache.client", "hfcache.catalog_query_models"),
        "host.status": ("hfcache.host_models", "hfcache.api.host_status"),
        "host.observer": (
            "hfcache.host_actions_models",
            "hfcache.api.host_actions",
            "hfcache.api.host_routes",
            "hfcache.api.auth",
        ),
        "host.outcome": (
            "hfcache.host_actions_models",
            "hfcache.api.host_actions",
            "hfcache.api.host_routes",
            "hfcache.api.auth",
        ),
        "host.validation": (
            "hfcache.host_actions_models",
            "hfcache.api.host_actions",
            "hfcache.api.host_routes",
            "hfcache.api.auth",
        ),
        "host.journal": (
            "hfcache.host_actions_models",
            "hfcache.logging",
            "hfcache.api.host_actions",
            "hfcache.api.host_routes",
            "hfcache.api.auth",
        ),
        "ui.bootstrap": (
            "hfcache.ui_models",
            "hfcache.api.ui_serving",
            "hfcache.url_paths",
            "hfcache.server_config",
            "hfcache.api.auth",
        ),
        "ui.html": ("hfcache.api.ui_assets", "hfcache.ui_models"),
    }
    for identifier, names in contexts.items():
        digest = hashlib.sha256(
            "".join(AUDITED_SOURCES[name] for name in names).encode()
        ).hexdigest()
        exporter.semantics[identifier] = {"phase": "context", "source_hash": digest}


def _timestamp_wire(node: Node) -> None:
    if node["kind"] == "union":
        for choice in node["choices"]:
            _timestamp_wire(choice)
    elif node["kind"] == "string" and "timestamp.serialized" not in node["semantic_ids"]:
        node["semantic_ids"].append("timestamp.wire")


def _audit_metadata(schema: Node) -> None:
    metadata = schema.get("metadata", {})
    if metadata.keys() - {"pydantic_js_functions", "pydantic_js_updates"}:
        message = "Unaudited JSON Schema metadata hook"
        raise ValueError(message)
    for function in metadata.get("pydantic_js_functions", ()):
        identity, _ = hook_identity(function)
        if identity not in {
            "pydantic.main.BaseModel.__get_pydantic_json_schema__",
            "pydantic._internal._generate_schema.GenerateSchema._path_schema.<locals>.<lambda>",
        }:
            message = f"Unaudited JSON Schema generation hook {identity}"
            raise ValueError(message)
    updates = metadata.get("pydantic_js_updates", {})
    if updates:
        function = schema.get("function", {}).get("function")
        if not isinstance(function, partial) or schema["type"] != "function-after":
            message = "Unaudited JSON Schema constraint override"
            raise ValueError(message)
        expected = {
            {"min_length": "minLength", "max_length": "maxLength"}[key]: value
            for key, value in function.keywords.items()
            if key in {"min_length", "max_length"}
        }
        if updates != expected:
            message = "JSON Schema and Python core length constraints disagree"
            raise ValueError(message)


def _parameter(name: str) -> Node:
    if name == "revision":
        return {
            "kind": "union",
            "choices": [
                {"kind": "literal", "value": "current", "semantic_ids": []},
                _parameter("commit_sha"),
            ],
            "semantic_ids": [],
        }
    semantics = {
        "commit_sha": "hfcache.identity.parse_commit_sha",
        "publication_id": "hfcache.identity.parse_publication_id",
        "run_id": "hfcache.identity.parse_run_id",
        "operation_id": "hfcache.identity.parse_run_id",
        "repository_type": "hfcache.identity.parse_repository_type",
    }
    node = {
        "kind": "string",
        "min_codepoints": 1,
        "max_codepoints": 256,
        "pattern": None,
        "semantic_ids": [semantics[name]] if name in semantics else [],
    }
    if name in {"namespace", "name"}:
        node.update(min_codepoints=1, max_codepoints=96, pattern="^[A-Za-z0-9][A-Za-z0-9._-]*$")
    return node


def _queries(group: str) -> list[Node]:
    groups: dict[str, tuple[str, ...]] = {
        "none": (),
        "page": ("limit", "cursor"),
        "inventory": ("limit", "cursor", "selector", "type"),
        "events": ("after", "limit"),
        "journal": ("source", "cursor", "limit"),
        "catalog": (
            "type",
            "q",
            "tag_all",
            "tag_any",
            "tag_source",
            "scope",
            "revision_scope",
            "format",
            "quantization",
            "quantization_method",
            "bits",
            "max_variant_bytes",
            "limit",
            "cursor",
        ),
        "exact": ("revision_scope", "commit_sha", "publication_id"),
    }
    groups["facets"] = (*groups["catalog"], "facet")
    groups["variants"] = (*groups["exact"], "limit", "cursor")
    result = []
    choices = {
        "type": ("model", "dataset"),
        "scope": ("archived", "configured", "all"),
        "revision_scope": ("current", "retained"),
        "tag_source": ("current_or_last_observed", "current_only"),
        "facet": ("tag", "format", "quantization_method", "quantization"),
        "source": ("sync-observer", "verify-observer"),
    }
    for name in groups[group]:
        node: Node = _parameter(name)
        if name in choices:
            node = {
                "kind": "union",
                "choices": [
                    {"kind": "literal", "value": choice, "semantic_ids": []}
                    for choice in choices[name]
                ],
                "semantic_ids": [],
            }
        if node["kind"] == "string":
            node["min_codepoints"] = 0
            node["max_codepoints"] = (
                128
                if name in {"tag_all", "tag_any"}
                else 256
                if name in {"q", "cursor", "selector"}
                else 64
            )
        if name in {"after", "limit", "bits", "max_variant_bytes"}:
            node = {
                "kind": "integer",
                "minimum": "0" if name in {"after", "max_variant_bytes"} else "1",
                "maximum": "64"
                if name == "bits"
                else ("10000" if name == "limit" else "9223372036854775807"),
                "semantic_ids": [],
            }
            if name == "after":
                node["maximum"] = "9999999999"
        repeated = name in {"selector", "tag_all", "tag_any"}
        if group == "journal" and name == "cursor":
            node["max_codepoints"] = 2048
            node["min_codepoints"] = 1
            node["semantic_ids"] = ["hfcache.host_actions_models._printable"]
        if group == "journal" and name == "limit":
            node["maximum"] = "80"
        if repeated:
            node = {
                "kind": "array",
                "items": node,
                "min_items": None,
                "max_items": 100 if name == "selector" else 64,
                "semantic_ids": [],
            }
        result.append({"name": name, "node": node, "repeated": repeated})
    return result


def render_contracts() -> str:
    return json.dumps(build_contracts(), ensure_ascii=True, sort_keys=True, indent=2) + "\n"
