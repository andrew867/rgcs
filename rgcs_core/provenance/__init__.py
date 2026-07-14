"""Provenance, classification metadata, and serialization for rgcs_core.

Implements the enforcement requirements of
docs/SCIENTIFIC_CLASSIFICATION_POLICY.md section 4.1:

* every claim-bearing public function carries machine-readable
  classification metadata (the ``classified`` decorator);
* JSON serialization uses null, never NaN (D-03);
* forbidden-vocabulary terms are registered here (assembled at runtime so
  the source text itself never contains the phrases);
* sha256 helpers for dataset/file provenance.

Units: not applicable (metadata module).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, is_dataclass, asdict
from typing import Any, Callable, TypeVar

import numpy as np

__all__ = [
    "MODEL_VERSION", "Classification", "classified", "classification_string",
    "FORBIDDEN_TERMS", "contains_forbidden_vocabulary", "to_jsonable",
    "json_dumps", "sha256_file", "sha256_of_jsonable",
]

#: Version of the mathematical model implemented by this package.
MODEL_VERSION = "RGCS-v2.0 (MATHEMATICAL_MODEL.md 2026-07-14; registry schema 1)"

VALID_LABELS = ("Established", "Derived", "Hypothesis", "Source claim")


@dataclass(frozen=True)
class Classification:
    """Machine-readable classification metadata (policy section 4.1)."""

    label: str
    registry: tuple[str, ...] = ()   # RGCS-M.x ids from docs/model_registry.yaml
    sources: tuple[str, ...] = ()    # SOURCE_EVIDENCE_LEDGER rows (RG-xx, LT-xx, ...)
    note: str = ""

    def __post_init__(self) -> None:
        if self.label not in VALID_LABELS:
            raise ValueError(f"invalid classification label {self.label!r}; "
                             f"must be one of {VALID_LABELS} (no hybrid labels)")

    def as_string(self) -> str:
        refs = "; ".join([*self.registry, *self.sources])
        return f"{self.label} [{refs}]" if refs else self.label

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "registry": list(self.registry),
                "sources": list(self.sources), "note": self.note}


F = TypeVar("F", bound=Callable[..., Any])


def classified(label: str, *, registry: tuple[str, ...] | list[str] = (),
               sources: tuple[str, ...] | list[str] = (),
               note: str = "") -> Callable[[F], F]:
    """Attach classification metadata to a public function.

    Every claim-bearing public function in rgcs_core must carry this
    decorator; tests assert its presence (policy section 4.1)."""
    meta = Classification(label, tuple(registry), tuple(sources), note)

    def deco(fn: F) -> F:
        fn.classification = meta  # type: ignore[attr-defined]
        return fn
    return deco


def classification_string(fn: Callable[..., Any]) -> str:
    """The classification string of a decorated function (for dict outputs)."""
    meta: Classification = getattr(fn, "classification")
    return meta.as_string()


def _assemble(*parts: str) -> str:
    # Assembled at runtime so the forbidden phrases never appear verbatim
    # in this repository's source text (QA vocabulary gate).
    return "".join(parts)


#: Forbidden physical-equivalence vocabulary (policy section 4.1 lint list
#: plus the Agent 03 handoff list). Matching is case-insensitive for phrases
#: and case-sensitive for the all-caps acronym.
FORBIDDEN_TERMS: tuple[tuple[str, bool], ...] = (
    (_assemble("quantum", " ", "shear"), False),         # (term, case_sensitive)
    (_assemble("B", "E", "C"), True),
    (_assemble("conden", "sate"), False),
    (_assemble("the crystal's ", "KK", " modes"), False),
    (_assemble("Kaluza-Klein mode", " of the crystal"), False),
    (_assemble("quantum", " ", "damping"), False),
    (_assemble("dark", " ", "matter"), False),
)


def contains_forbidden_vocabulary(text: str) -> list[str]:
    """Return the forbidden terms present in ``text`` (empty list = clean)."""
    found: list[str] = []
    for term, case_sensitive in FORBIDDEN_TERMS:
        haystack = text if case_sensitive else text.lower()
        needle = term if case_sensitive else term.lower()
        if needle in haystack:
            found.append(term)
    return found


def to_jsonable(obj: Any) -> Any:
    """Convert to JSON-compatible values. NaN/inf become null (D-03:
    JSON serialization uses null, never NaN)."""
    if obj is None or isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, complex):
        return {"re": to_jsonable(obj.real), "im": to_jsonable(obj.imag)}
    if isinstance(obj, np.generic):
        return to_jsonable(obj.item())
    if isinstance(obj, np.ndarray):
        return [to_jsonable(v) for v in obj.tolist()]
    if is_dataclass(obj) and not isinstance(obj, type):
        return to_jsonable(asdict(obj))
    if hasattr(obj, "model_dump"):          # pydantic v2 models
        return to_jsonable(obj.model_dump())
    if hasattr(obj, "to_dict"):
        return to_jsonable(obj.to_dict())
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    raise TypeError(f"cannot serialize {type(obj).__name__} to JSON")


def json_dumps(obj: Any, **kwargs: Any) -> str:
    """JSON dump through :func:`to_jsonable`; ``allow_nan=False`` guarantees
    no NaN token can ever be emitted."""
    return json.dumps(to_jsonable(obj), allow_nan=False, **kwargs)


def sha256_file(path: str) -> str:
    """Hex sha256 of a file's bytes (provenance of golden datasets)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_jsonable(obj: Any) -> str:
    """Hex sha256 of the canonical JSON form of ``obj``."""
    payload = json_dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
