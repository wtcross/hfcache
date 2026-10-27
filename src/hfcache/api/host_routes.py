"""The two fixed non-archive effect routes (INV-022, decision156)."""

SCHEDULE_CHANGES = "/api/v1/host/sync-schedule/changes"
OBSERVER_STOPS = "/api/v1/host/sync-observer/stops"
HOST_EFFECT_ROUTES = frozenset({SCHEDULE_CHANGES, OBSERVER_STOPS})
