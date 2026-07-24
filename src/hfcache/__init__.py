"""Archive complete revisions of public Hugging Face repositories.

`hfcache` resolves a configured branch or tag to an immutable commit SHA,
downloads the complete repository snapshot at that SHA, verifies every newly
introduced object with SHA-256, and atomically publishes an immutable
ordinary-file tree that downstream systems copy over a read-only NFS export.

The contracts this package implements live in `docs/`: `architecture.md`,
`configuration.md`, `schemas.md`, `cli.md`, and `security.md`.
"""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("hfcache")
except PackageNotFoundError:  # pragma: no cover - only when running from a tree
    __version__ = "0.0.0+unknown"
