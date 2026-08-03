"""Publication-hold and public-path filter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class ReleaseManifestRefused(RuntimeError):
    """Raised when an excluded path is proposed for a public manifest."""


@dataclass(frozen=True)
class ReleaseAudit:
    publication_hold: bool
    accepted_paths: tuple[str, ...]
    rejected_paths: tuple[str, ...]


_ALLOWED_PREFIXES = ("rgcs_ardk/", "docs/proofs/r1074-annular-devkit/")
_EXCLUDED_COMPONENTS = ("private", "message", "ascii", "phenomenology")


def publication_hold() -> bool:
    return True


def audit_release_paths(paths: Iterable[str | Path]) -> ReleaseAudit:
    accepted: list[str] = []
    rejected: list[str] = []
    for candidate in paths:
        normalized = Path(candidate).as_posix().lstrip("./")
        lowered = normalized.lower()
        allowed = any(normalized.startswith(prefix) for prefix in _ALLOWED_PREFIXES)
        excluded = any(component in lowered.split("/") for component in _EXCLUDED_COMPONENTS)
        if allowed and not excluded:
            accepted.append(normalized)
        else:
            rejected.append(normalized)
    return ReleaseAudit(True, tuple(sorted(accepted)), tuple(sorted(rejected)))


def require_public_paths(paths: Iterable[str | Path]) -> tuple[str, ...]:
    audit = audit_release_paths(paths)
    if audit.rejected_paths:
        raise ReleaseManifestRefused(f"release paths rejected: {audit.rejected_paths}")
    return audit.accepted_paths
