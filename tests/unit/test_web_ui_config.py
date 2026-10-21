"""UI-only startup configuration bounds and the explicit prefix migration."""

import pytest

from hfcache.errors import ConfigurationError
from hfcache.server_config import validate_server_config_mapping
from tests.fixtures.web_ui import make_profile


@pytest.mark.parametrize(
    "web",
    [
        {"enabled": True},
        {"enabled": "true"},
        {"enabled": 1},
        {"enabled": True, "asset_root": "relative", "manifest_sha256": "a" * 64},
        {"enabled": True, "asset_root": "/owned/assets", "manifest_sha256": "A" * 64},
        {"enabled": False, "unknown_private_key": "must-not-be-echoed"},
    ],
)
def test_strict_web_configuration_has_no_coercion_and_sanitizes_diagnostics(web):
    profile = make_profile()
    mapping = profile.server.model_dump(mode="json")
    mapping["web"] = web
    with pytest.raises(ConfigurationError) as caught:
        validate_server_config_mapping(mapping)
    assert "must-not-be-echoed" not in str(caught.value)
    assert "unknown_private_key" not in str(caught.value)


def test_enabled_web_requires_basic_but_disabled_retained_paths_need_no_provider():
    profile = make_profile()
    mapping = profile.server.model_dump(mode="json")
    mapping["basic"] = None
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping)
    mapping["web"]["enabled"] = False
    assert not validate_server_config_mapping(mapping).web.enabled


def test_utf8_prefix_limit_is_enabled_only_and_has_an_exact_boundary():
    profile = make_profile()
    mapping = profile.server.model_dump(mode="json")
    mapping["listener"]["root_path"] = "/" + "管" * 341
    assert len(validate_server_config_mapping(mapping).listener.root_path.encode()) == 1024
    mapping["listener"]["root_path"] += "管"
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping)
    mapping["web"]["enabled"] = False
    assert len(validate_server_config_mapping(mapping).listener.root_path.encode()) > 1024


def test_only_the_documented_leading_double_slash_migrates_backend_prefix_grammar():
    profile = make_profile()
    mapping = profile.server.model_dump(mode="json")
    mapping["web"]["enabled"] = False
    mapping["listener"]["root_path"] = "//management"
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(mapping)
    for prefix in ("/管理", "/quote'", '/quote"', "/angle<>", "/a:@[]!$&'()*+,;="):
        mapping["listener"]["root_path"] = prefix
        assert validate_server_config_mapping(mapping).listener.root_path == prefix
