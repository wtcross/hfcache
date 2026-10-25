"""Source constraints for the separate SELinux reader domain.

These inspect the shipped policy, not an installed policy or role acceptance.
Actual target-policy compilation and enforcing alias-denial remain mandatory.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "packaging/selinux/hfcache-host-helper.cil"
SUBJECT = "hfcache_host_helper_t"


def forms():
    source = POLICY.read_text()
    source = re.sub(r";[^\n]*", "", source)
    tokens = re.findall(r"[()]|[^\s()]+", source)
    stack: list[list] = [[]]
    for token in tokens:
        if token == "(":
            child: list = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            assert len(stack) > 1
            stack.pop()
        else:
            stack[-1].append(token)
    assert len(stack) == 1
    return stack[0]


def access_rules(kind):
    result = []
    for form in forms():
        if form[0] == kind:
            assert len(form) == 4
            access_class, permissions = form[3]
            assert type(permissions) is list
            assert len(permissions) == len(set(permissions))
            result.append((form[1], form[2], access_class, frozenset(permissions)))
    return result


def test_policy_has_no_optional_global_or_permissive_escape():
    permitted = {"type", "typeattributeset", "roletype", "allow", "typetransition", "neverallow"}
    assert {form[0] for form in forms()} <= permitted
    assert {source for source, _, _, _ in access_rules("allow")} == {
        SUBJECT,
        "init_t",
        "container_t",
        "container_runtime_t",
    }
    forbidden_targets = {"domain", "file_type", "exec_type", "unconfined_domain_type", "*", "all"}
    assert all(target not in forbidden_targets for _, target, _, _ in access_rules("allow"))
    assert all(
        "*" not in permissions and "all" not in permissions
        for _, _, _, permissions in access_rules("allow")
    )
    source = POLICY.read_text()
    assert "(permissive" not in source
    assert "(auditallow" not in source
    assert "(dontaudit" not in source
    assert "(optional" not in source


def test_only_explicit_system_manager_enters_domain_and_no_child_leaves():
    transitions = [form for form in forms() if form[0] == "typetransition"]
    assert transitions == [
        ["typetransition", "init_t", "hfcache_host_helper_exec_t", "process", SUBJECT]
    ]
    assert ("init_t", SUBJECT, "process", frozenset({"transition"})) in access_rules("allow")
    assert ("init_t", SUBJECT, "process2", frozenset({"nnp_transition"})) in access_rules("allow")
    forbidden = {"transition", "dyntransition", "setexec"}
    assert not any(
        source == SUBJECT and cls == "process" and permissions & forbidden
        for source, _, cls, permissions in access_rules("allow")
    )
    assert (SUBJECT, "domain", "process", frozenset(forbidden)) in access_rules("neverallow")
    attributes = [form for form in forms() if form[0] == "typeattributeset"]
    assert ["typeattributeset", "domain", [SUBJECT]] in attributes
    assert not any(
        form[1] in {"unconfined_domain_type", "unconfined_service_type"} for form in attributes
    )


def test_host_and_namespace_capabilities_are_distinct_and_closed():
    caps = [
        (cls, permissions)
        for source, target, cls, permissions in access_rules("allow")
        if source == SUBJECT
        and target == "self"
        and cls in {"capability", "capability2", "cap_userns", "cap2_userns"}
    ]
    assert caps == [
        ("capability", frozenset({"setuid", "setgid"})),
        ("cap_userns", frozenset({"sys_admin", "setpcap", "sys_ptrace", "dac_read_search"})),
    ]
    required = {
        "sys_admin",
        "sys_ptrace",
        "dac_override",
        "dac_read_search",
        "setpcap",
        "sys_module",
        "sys_rawio",
    }
    assert (SUBJECT, "self", "capability", frozenset(required)) in access_rules("neverallow")
    assert (SUBJECT, "self", "cap_userns", frozenset({"dac_override"})) in access_rules(
        "neverallow"
    )


@pytest.mark.parametrize(
    "target",
    [
        "nfs_t",
        "hfcache_archive_t",
        "hfcache_host_helper_secret_t",
        "hfcache_host_helper_hub_state_t",
    ],
)
def test_payload_object_types_never_allow_helper_reads_or_mapping(target):
    forbidden = frozenset({"read", "open", "map", "execute"})
    assert (SUBJECT, target, "file", forbidden) in access_rules("neverallow")
    assert not any(
        source == SUBJECT and selected == target and cls == "file" and rights & forbidden
        for source, selected, cls, rights in access_rules("allow")
    )


def test_container_compatibility_is_closed_to_inputs_endpoint_and_hub_state():
    expected = {
        ("hfcache_host_helper_application_conf_t", "file"): {"getattr", "open", "read"},
        ("hfcache_host_helper_hub_state_t", "dir"): {
            "getattr",
            "search",
            "open",
            "read",
            "write",
            "add_name",
            "remove_name",
            "create",
            "setattr",
            "rmdir",
        },
        ("hfcache_host_helper_hub_state_t", "file"): {
            "getattr",
            "open",
            "read",
            "write",
            "append",
            "create",
            "setattr",
            "unlink",
            "rename",
            "link",
            "lock",
            "map",
        },
        ("hfcache_host_helper_hub_state_t", "lnk_file"): {
            "getattr",
            "read",
            "create",
            "setattr",
            "unlink",
            "rename",
        },
        ("hfcache_archive_t", "dir"): {"getattr", "search", "open", "read"},
        ("hfcache_archive_t", "file"): {"getattr", "open", "read", "map"},
        ("hfcache_host_helper_secret_t", "dir"): {"getattr", "search"},
        ("hfcache_host_helper_secret_t", "file"): {"getattr", "open", "read", "map"},
        ("hfcache_host_helper_runtime_t", "dir"): {"getattr", "search"},
        ("hfcache_host_helper_runtime_t", "file"): {"getattr", "open", "read"},
        ("hfcache_host_helper_runtime_t", "sock_file"): {"getattr", "open", "read", "write"},
        (SUBJECT, "unix_stream_socket"): {"connectto"},
    }
    observed = {
        (target, cls): set(rights)
        for source, target, cls, rights in access_rules("allow")
        if source == "container_t"
    }
    assert observed == expected


def test_fixed_metadata_observation_never_grants_process_attach_or_policy_write():
    rules = access_rules("allow")
    assert not any(
        source == SUBJECT and cls == "process" and "ptrace" in rights
        for source, _, cls, rights in rules
    )
    assert not any(source == SUBJECT and cls == "security" for source, _, cls, _ in rules)
    assert (
        SUBJECT,
        "security_t",
        "security",
        frozenset({"load_policy", "setenforce", "setbool"}),
    ) in access_rules("neverallow")
    assert (SUBJECT, "nsfs_t", "file", frozenset({"getattr", "open", "read", "ioctl"})) in rules
    assert (SUBJECT, "init_t", "file", frozenset({"getattr", "open", "read"})) in rules
    assert (SUBJECT, "container_runtime_t", "file", frozenset({"getattr", "open", "read"})) in rules


def test_installed_unit_requires_domain_without_optional_fallback():
    unit = (ROOT / "packaging/systemd/hfcache-host-helper.service").read_text()
    assert "SELinuxContext=system_u:system_r:hfcache_host_helper_t:s0\n" in unit
    assert "SELinuxContext=-" not in unit
    assert "CapabilityBoundingSet=CAP_SETUID CAP_SETGID\n" in unit
    assert "AmbientCapabilities=CAP_SETUID\n" in unit
    assert "RestrictNamespaces=user\n" in unit
    assert "NoNewPrivileges=true\n" in unit
    assert "RestrictAddressFamilies=AF_UNIX\n" in unit
    assert "InaccessiblePaths=-/srv/hfcache " in unit


def test_owned_child_sigkill_is_same_domain_only_without_host_kill_capability():
    rules = access_rules("allow")
    assert (
        SUBJECT,
        "self",
        "process",
        frozenset({"fork", "sigchld", "sigkill", "getcap", "setcap", "getsched", "getattr"}),
    ) in rules
    assert not any(
        source == SUBJECT and target != "self" and "sigkill" in rights
        for source, target, _, rights in rules
    )
    assert not any(
        source == SUBJECT and cls == "capability" and "kill" in rights
        for source, _, cls, rights in rules
    )


def test_stdio_and_child_pipes_have_only_narrow_fixed_channel_permissions():
    rules = access_rules("allow")
    assert (
        SUBJECT,
        "null_device_t",
        "chr_file",
        frozenset({"getattr", "open", "read", "write"}),
    ) in rules
    assert (SUBJECT, "self", "fifo_file", frozenset({"getattr", "read", "write", "ioctl"})) in rules
    assert {
        (target, cls, rights)
        for source, target, cls, rights in rules
        if source == SUBJECT and cls == "fd"
    } == {
        ("self", "fd", frozenset({"use"})),
        ("init_t", "fd", frozenset({"use"})),
    }


def test_actual_targeted_kernel_and_fixed_stdio_bus_labels_are_explicit():
    rules = access_rules("allow")
    assert "selinuxfs_t" not in POLICY.read_text()
    assert (SUBJECT, "security_t", "file", frozenset({"getattr", "open", "read"})) in rules
    assert (
        SUBJECT,
        "syslogd_var_run_t",
        "sock_file",
        frozenset({"getattr", "read", "write"}),
    ) in rules
    assert (
        SUBJECT,
        "session_dbusd_tmp_t",
        "sock_file",
        frozenset({"getattr", "open", "read", "write"}),
    ) in rules


def _assert_fixed_session_broker_permissions():
    rules = access_rules("allow")
    broker = "unconfined_dbusd_t"
    assert [rule for rule in rules if broker in rule[:2]] == [
        (SUBJECT, broker, "unix_stream_socket", frozenset({"connectto"})),
        (SUBJECT, broker, "dbus", frozenset({"send_msg"})),
    ]
    assert {
        (target, rights)
        for source, target, cls, rights in rules
        if source == SUBJECT and cls == "dbus"
    } == {
        ("init_t", frozenset({"send_msg"})),
        ("unconfined_t", frozenset({"send_msg"})),
        (broker, frozenset({"send_msg"})),
        ("system_dbusd_t", frozenset({"send_msg"})),
    }
    assert {
        (target, rights)
        for source, target, cls, rights in rules
        if source == SUBJECT and target != "self" and cls == "unix_stream_socket"
    } == {
        ("init_t", frozenset({"getattr", "read", "write", "getopt", "setopt", "shutdown"})),
        ("init_t", frozenset({"connectto"})),
        ("unconfined_t", frozenset({"connectto"})),
        ("unconfined_dbusd_t", frozenset({"connectto"})),
        ("system_dbusd_t", frozenset({"connectto"})),
    }


def test_fixed_session_broker_has_only_connection_and_driver_message_permissions():
    _assert_fixed_session_broker_permissions()


@pytest.mark.parametrize(
    "replacement",
    [
        "",
        "(allow hfcache_host_helper_t unconfined_dbusd_t (dbus (send_msg acquire_svc)))",
        "(allow hfcache_host_helper_t unconfined_dbusd_t (file (read)))",
        "(allow hfcache_host_helper_t unconfined_service_t (dbus (send_msg)))",
        (
            "(allow hfcache_host_helper_t unconfined_dbusd_t (dbus (send_msg)))\n"
            "(allow unconfined_dbusd_t hfcache_host_helper_t (dbus (send_msg)))"
        ),
        (
            "(allow hfcache_host_helper_t unconfined_dbusd_t (dbus (send_msg)))\n"
            "(allow hfcache_host_helper_t unconfined_service_t (dbus (send_msg)))"
        ),
    ],
    ids=["old-policy", "extra-right", "wrong-class", "wrong-target", "reverse", "extra-peer"],
)
def test_fixed_session_broker_rejects_old_or_broader_policy(replacement, tmp_path, monkeypatch):
    source = POLICY.read_text()
    new_rule = "(allow hfcache_host_helper_t unconfined_dbusd_t (dbus (send_msg)))"
    assert source.count(new_rule) == 1
    candidate = tmp_path / "candidate.cil"
    candidate.write_text(source.replace(new_rule, replacement))
    monkeypatch.setitem(globals(), "POLICY", candidate)
    with pytest.raises(AssertionError):
        _assert_fixed_session_broker_permissions()


def test_fixed_manager_append_channel_does_not_grant_payload_access():
    rules = access_rules("allow")
    assert (
        "init_t",
        "hfcache_host_helper_runtime_t",
        "file",
        frozenset({"open", "append"}),
    ) in rules
    assert [
        (target, cls, rights)
        for source, target, cls, rights in rules
        if source == "init_t" and target == "hfcache_host_helper_runtime_t"
    ] == [
        ("hfcache_host_helper_runtime_t", "file", frozenset({"open", "append"})),
        ("hfcache_host_helper_runtime_t", "dir", frozenset({"mounton"})),
    ]
    runtime = [
        rights
        for source, target, cls, rights in rules
        if source == SUBJECT and target == "hfcache_host_helper_runtime_t" and cls == "file"
    ]
    assert len(runtime) == 1
    assert {"append", "write"} <= runtime[0]


def test_readiness_send_is_only_to_fixed_manager_socket_domains():
    rules = access_rules("allow")
    assert {
        (target, rights)
        for source, target, cls, rights in rules
        if source == SUBJECT and target != "self" and cls == "unix_dgram_socket"
    } == {
        ("init_t", frozenset({"sendto"})),
        ("kernel_t", frozenset({"sendto"})),
    }
    assert not any(
        source == SUBJECT and target == "kernel_t" and cls != "unix_dgram_socket"
        for source, target, cls, _rights in rules
    )


def test_indexed_systemd_link_observation_grants_only_metadata_and_target_text():
    rules = access_rules("allow")
    assert [
        rights
        for source, target, cls, rights in rules
        if source == SUBJECT and target == "systemd_unit_file_t" and cls == "lnk_file"
    ] == [frozenset({"getattr", "read"})]


def test_stock_keeper_temporary_type_has_only_readonly_file_access():
    rules = access_rules("allow")
    assert [
        rights
        for source, target, cls, rights in rules
        if source == SUBJECT and target == "user_tmp_t" and cls == "file"
    ] == [frozenset({"getattr", "open", "read"})]
    assert not any(
        source == SUBJECT and target == "user_tmp_t" and cls in {"lnk_file", "sock_file"}
        for source, target, cls, _rights in rules
    )


def test_stock_runtime_directory_allows_only_observation_and_fixed_chmod_metadata():
    assert [
        rights
        for source, target, cls, rights in access_rules("allow")
        if source == SUBJECT and target == "user_tmp_t" and cls == "dir"
    ] == [frozenset({"getattr", "search", "open", "read", "setattr"})]


def test_filesystem_metadata_grants_are_only_cgroup_and_backing_filesystem_getattr():
    assert [
        (target, rights)
        for source, target, cls, rights in access_rules("allow")
        if source == SUBJECT and cls == "filesystem"
    ] == [("cgroup_t", frozenset({"getattr"})), ("fs_t", frozenset({"getattr"}))]


def test_backing_filesystem_type_gets_no_file_directory_or_other_class_grant():
    assert [
        (cls, rights)
        for source, target, cls, rights in access_rules("allow")
        if source == SUBJECT and target == "fs_t"
    ] == [("filesystem", frozenset({"getattr"}))]


def test_stock_overlay_type_has_only_directory_listing_and_file_reading():
    assert [
        (cls, rights)
        for source, target, cls, rights in access_rules("allow")
        if source == SUBJECT and target == "container_ro_file_t"
    ] == [
        ("dir", frozenset({"getattr", "search", "open", "read"})),
        ("file", frozenset({"getattr", "open", "read"})),
    ]


def test_conmon_selection_has_metadata_only_without_open_or_execution():
    assert [
        (cls, rights)
        for source, target, cls, rights in access_rules("allow")
        if source == SUBJECT and target == "conmon_exec_t"
    ] == [("file", frozenset({"getattr"}))]


def test_existing_fixed_process_types_allow_only_readonly_proc_file_access():
    targets = {
        "init_t",
        "unconfined_t",
        "unconfined_service_t",
        "container_t",
        "container_runtime_t",
    }
    rules = access_rules("allow")
    assert [
        (target, rights)
        for source, target, cls, rights in rules
        if source == SUBJECT and target in targets and cls == "file"
    ] == [
        (target, frozenset({"getattr", "open", "read"}))
        for target in (
            "init_t",
            "unconfined_t",
            "unconfined_service_t",
            "container_t",
            "container_runtime_t",
        )
    ]
    assert not any(
        source == SUBJECT and cls == "process" and "ptrace" in rights
        for source, _target, cls, rights in rules
    )
    assert not any(
        source == SUBJECT and cls in {"capability", "capability2"} and "sys_ptrace" in rights
        for source, _target, cls, rights in rules
    )


def test_namespace_owner_mediation_never_grants_process_attach():
    rules = access_rules("allow")
    assert (
        SUBJECT,
        "self",
        "cap_userns",
        frozenset({"sys_admin", "setpcap", "sys_ptrace", "dac_read_search"}),
    ) in rules
    assert (SUBJECT, "domain", "process", frozenset({"ptrace"})) in access_rules("neverallow")
    assert not any(
        source == SUBJECT and cls == "process" and "ptrace" in rights
        for source, _target, cls, rights in rules
    )
    assert not any(
        source == SUBJECT and cls in {"capability", "capability2"} and "sys_ptrace" in rights
        for source, _target, cls, rights in rules
    )


def test_shared_application_config_is_readonly_and_private_authority_stays_private():
    rules = access_rules("allow")
    assert (
        SUBJECT,
        "hfcache_host_helper_application_conf_t",
        "file",
        frozenset({"getattr", "open", "read"}),
    ) in rules
    assert not any(
        source == "container_t" and target == "hfcache_host_helper_conf_t"
        for source, target, _cls, _rights in rules
    )
    assert not any(
        source == SUBJECT and target == "hfcache_host_helper_hub_state_t"
        for source, target, _cls, _rights in rules
    )
    unit = (ROOT / "packaging/systemd/hfcache-host-helper.service").read_text()
    assert " -/var/cache/hfcache " in unit
    assert "-/var/cache/hfcache/xet" not in unit


def test_engine_lock_type_only_adds_fixed_coordination_permissions():
    rules = access_rules("allow")
    assert [
        (source, cls, rights)
        for source, target, cls, rights in rules
        if target == "hfcache_host_helper_engine_lock_t"
    ] == [
        (SUBJECT, "file", frozenset({"getattr", "open", "read", "write", "lock"})),
        ("container_runtime_t", "file", frozenset({"getattr", "open", "read", "write", "lock"})),
    ]
    assert [
        (target, cls, rights)
        for source, target, cls, rights in rules
        if source == "container_runtime_t"
    ] == [
        (
            "hfcache_host_helper_engine_lock_t",
            "file",
            frozenset({"getattr", "open", "read", "write", "lock"}),
        ),
        (
            "hfcache_host_helper_engine_shm_t",
            "file",
            frozenset({"getattr", "open", "read", "write", "map"}),
        ),
    ]
    assert (
        SUBJECT,
        "hfcache_host_helper_engine_lock_t",
        "file",
        frozenset({"append", "create", "setattr", "unlink", "rename", "link", "map", "execute"}),
    ) in access_rules("neverallow")


def test_image_file_and_directory_mutation_are_compile_checked_denials():
    assert (
        SUBJECT,
        "container_ro_file_t",
        "file",
        frozenset({"write", "append", "create", "setattr", "unlink", "rename", "link"}),
    ) in access_rules("neverallow")
    assert (
        SUBJECT,
        "container_ro_file_t",
        "dir",
        frozenset({"write", "add_name", "remove_name", "create", "setattr", "rmdir", "rename"}),
    ) in access_rules("neverallow")
    for source, target, cls, rights in access_rules("allow"):
        if source == SUBJECT and target == "container_ro_file_t":
            assert (cls, rights) in {
                ("file", frozenset({"getattr", "open", "read"})),
                ("dir", frozenset({"getattr", "search", "open", "read"})),
            }


@pytest.mark.parametrize(
    "target",
    [
        "hfcache_host_helper_secret_t",
        "hfcache_host_helper_hub_state_t",
        "hfcache_archive_t",
        "hfcache_host_helper_runtime_t",
    ],
)
def test_manager_mask_attachment_and_native_directory_setup_are_separate(target):
    assert [
        (source, cls, rights)
        for source, found, cls, rights in access_rules("allow")
        if source == "init_t" and found == target and cls == "dir"
    ] == [("init_t", "dir", frozenset({"mounton"}))] + (
        [("init_t", "dir", frozenset({"setattr"}))]
        if target == "hfcache_host_helper_hub_state_t"
        else []
    )


def test_trusted_manager_explicit_rights_are_closed_and_do_not_expand_helper_access():
    rules = access_rules("allow")
    assert [
        (target, cls, rights) for source, target, cls, rights in rules if source == "init_t"
    ] == [
        (SUBJECT, "process", frozenset({"transition"})),
        (SUBJECT, "process2", frozenset({"nnp_transition"})),
        ("hfcache_host_helper_exec_t", "file", frozenset({"getattr", "open", "read", "execute"})),
        ("hfcache_host_helper_runtime_t", "file", frozenset({"open", "append"})),
        ("hfcache_host_helper_secret_t", "dir", frozenset({"mounton"})),
        ("hfcache_host_helper_hub_state_t", "dir", frozenset({"mounton"})),
        ("hfcache_archive_t", "dir", frozenset({"mounton"})),
        ("hfcache_host_helper_hub_state_t", "dir", frozenset({"setattr"})),
        ("hfcache_host_helper_secret_t", "file", frozenset({"read", "open"})),
        ("hfcache_host_helper_runtime_t", "dir", frozenset({"mounton"})),
    ]
    for target in ("hfcache_host_helper_secret_t", "hfcache_host_helper_hub_state_t"):
        assert not any(source == SUBJECT and found == target for source, found, _, _ in rules)
        assert (
            SUBJECT,
            target,
            "file",
            frozenset({"read", "open", "map", "execute"}),
        ) in access_rules("neverallow")


def test_manager_mask_mounton_never_becomes_helper_mount_or_payload_authority():
    assert {
        (target, cls, rights)
        for source, target, cls, rights in access_rules("allow")
        if source == "init_t" and "mounton" in rights
    } == {
        (target, "dir", frozenset({"mounton"}))
        for target in (
            "hfcache_host_helper_secret_t",
            "hfcache_host_helper_hub_state_t",
            "hfcache_archive_t",
            "hfcache_host_helper_runtime_t",
        )
    }
    assert not any(
        source == SUBJECT and "mounton" in rights
        for source, _target, _cls, rights in access_rules("allow")
    )


def test_rootless_network_state_directory_only_getattr_is_allowed():
    assert [
        (cls, rights)
        for source, target, cls, rights in access_rules("allow")
        if source == SUBJECT and target == "ifconfig_var_run_t"
    ] == [("dir", frozenset({"getattr"}))]


def test_fixed_existing_shared_segment_has_separate_closed_type_and_only_rw_map():
    target = "hfcache_host_helper_engine_shm_t"
    assert [f for f in forms() if f == ["type", target]] == [["type", target]]
    assert [
        (source, cls, rights)
        for source, selected, cls, rights in access_rules("allow")
        if selected == target
    ] == [
        (SUBJECT, "file", frozenset({"getattr", "open", "read", "write", "map"})),
        ("container_runtime_t", "file", frozenset({"getattr", "open", "read", "write", "map"})),
    ]
    forbidden = frozenset(
        {
            "append",
            "create",
            "setattr",
            "unlink",
            "rename",
            "link",
            "execute",
            "execute_no_trans",
            "entrypoint",
        }
    )
    assert (SUBJECT, target, "file", forbidden) in access_rules("neverallow")
    assert not any(f[0] == "typetransition" and target in f for f in forms())


def test_existing_general_tmpfs_type_receives_no_read_write_map_grant():
    assert not any(
        source == SUBJECT and target == "container_runtime_tmpfs_t"
        for source, target, _cls, _rights in access_rules("allow")
    )
    assert not any(
        source == SUBJECT and target == "hfcache_host_helper_engine_lock_t" and "map" in rights
        for source, target, _cls, rights in access_rules("allow")
    )


def test_fixed_manager_authorization_is_status_only():
    # Contextless units use the manager SID/system class; known fragments use
    # their file SID/service class. Neither authorization is a property selector.
    metadata = {
        (source, target, cls, permissions)
        for source, target, cls, permissions in access_rules("allow")
        if source == SUBJECT and cls in {"system", "service"}
    }
    assert metadata == {
        (SUBJECT, "init_t", "system", frozenset({"status"})),
        (SUBJECT, "systemd_unit_file_t", "service", frozenset({"status"})),
    }
    control = {"start", "stop", "reload", "enable", "disable", "kill", "load"}
    assert all(not (permissions & control) for _source, _target, _cls, permissions in metadata)
