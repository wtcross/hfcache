"""Inert host-schema evidence, never an installed profile or permission grant."""

from hfcache.host_models import HostStatus


def host_status() -> HostStatus:
    return HostStatus.model_validate(
        {
            "schema_version": 1,
            "state": "supported",
            "reason": None,
            "profile": "rootless",
            "binding": {
                "deployment_sha256": "a" * 64,
                "policy_sha256": "b" * 64,
                "release_version": "0.2.2",
                "source_commit": "c" * 40,
                "source_snapshot_sha256": "d" * 64,
                "source_dirty": True,
                "archive_id": "01234567-89ab-cdef-0123-456789abcdef",
                "archive_root": "/srv/hfcache",
            },
            "permissions": {
                "archive": False,
                "hub": False,
                "control": False,
                "schedule": False,
                "configuration": True,
                "observer": False,
            },
            "permission_reasons": {
                "archive": "policy-denied",
                "hub": "policy-denied",
                "control": "policy-denied",
                "schedule": "profile-unproved",
                "configuration": "granted",
                "observer": "profile-unproved",
            },
            "facts": {
                "guard": "absent",
                "archive_mount": "local-ro",
                "units": {
                    "hfcache-sync.service": {
                        "load": "masked",
                        "active": "inactive",
                        "unit_file": "masked",
                    },
                    "hfcache-verify.service": {
                        "load": "masked",
                        "active": "inactive",
                        "unit_file": "masked",
                    },
                    "hfcache-sync.timer": {
                        "load": "masked",
                        "active": "inactive",
                        "unit_file": "masked",
                    },
                    "hfcache-verify.timer": {
                        "load": "masked",
                        "active": "inactive",
                        "unit_file": "masked",
                    },
                },
                "sync_schedule": {
                    "state": "unavailable",
                    "reason": "profile-unproved",
                    "revision": None,
                    "source": None,
                    "on_calendar": None,
                    "randomized_delay_sec": None,
                },
            },
        }
    )
