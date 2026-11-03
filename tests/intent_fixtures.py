"""Explicit offline activation of owned test stores; never used by application startup."""

from collections.abc import Callable  # noqa: TC003 - explicit inherited attribute contract
from pathlib import Path

from hfcache.api.app import create_app as unactivated_app
from hfcache.api.operations import OperationStore as UnactivatedStore
from hfcache.server_config import InstalledPolicy
from tests.fixtures import examples


class OperationStore(UnactivatedStore):
    """Existing execution fixtures start from an explicitly activated local store."""

    checkpoint: Callable[[str], None] | None

    def __init__(self, root, *, archive_id=examples.ARCHIVE_ID, **kwargs):
        super().__init__(root, **kwargs)
        self.intent_lock_path = root.parent / "intent.lock"
        if not self.intent_lock_path.exists():
            self.intent_lock_path.touch(mode=0o600)
        if not self.private and not (root / "intent-dispositions.json").exists():
            checkpoint, self.checkpoint = self.checkpoint, None
            try:
                self.prepare_intent_state(archive_id)
            finally:
                self.checkpoint = checkpoint


def create_app(server, **kwargs):
    policy = kwargs.get("policy") or InstalledPolicy.open(server)
    state = Path(server.state_directory)
    if state.is_relative_to(policy.root) or policy.root.is_relative_to(state):
        return unactivated_app(server, **kwargs)
    if kwargs.get("operation_store") is None:
        kwargs["operation_store"] = OperationStore(
            Path(server.state_directory), archive_id=policy.archive_id
        )
    return unactivated_app(server, **kwargs)
