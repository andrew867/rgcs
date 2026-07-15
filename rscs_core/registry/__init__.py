"""RSCS registry: classification firewall + machine-readable ID registry.

This is the RSCS-layer analogue of ``rgcs_core.provenance``. It is
deliberately SEPARATE from the v2 module so that RSCS can add the ``ENG``
class and the EP-* provenance/exclusion fields WITHOUT modifying any frozen
v2 code (docs/DECISION_LOG.md D3-006; migration rule 4.4).

Two responsibilities:

1. The ``rscs_classified`` decorator attaches an :class:`RSCSClassification`
   to every claim-bearing RSCS object (coordinate builder or operator):
   registry ID(s), class in {EST,DER,HYP,SRC,ENG}, units action, source
   provenance (EP-* ids from references/equation_provenance.yaml), explicit
   exclusions, and the tolerance/test hook. Tests assert its presence and
   that the recorded ID actually exists in the yaml registry.

2. :func:`load_registry` reads ``rscs_core/registry/rscs_registry.yaml`` (the
   single machine-readable map from RSCS-C.*/RSCS-O.* to implementation,
   classification, units, provenance, and tests) and validates it.

Firewall rule (Agent 03 design principle 4): a class ordering
EST > DER > HYP > SRC is enforced by :func:`assert_no_src_upgrade`; an SRC or
HYP input may never be laundered into an EST/DER output without passing
through an explicit HYP/ENG boundary node.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

import yaml

__all__ = [
    "RSCS_MODEL_VERSION", "VALID_CLASSES", "CLASS_RANK", "RSCSClassification",
    "rscs_classified", "classification_of", "assert_no_src_upgrade",
    "load_registry", "registry_ids", "REGISTRY_PATH",
]

#: Version tag for the RSCS mathematical model (schema of this registry layer).
RSCS_MODEL_VERSION = "RSCS-1.0 (RSCS_MATHEMATICAL_MODEL.md 2026-07-14; rscs registry schema 1)"

#: The five claim classes. ENG (engineering heuristic) is new in RSCS/v3 and
#: is why this layer is separate from v2's four-label VALID_LABELS.
VALID_CLASSES = ("EST", "DER", "HYP", "SRC", "ENG")

#: Strength ordering used by the firewall. Higher = stronger epistemic claim.
#: ENG sits with HYP: an engineering heuristic is never evidence.
CLASS_RANK = {"EST": 4, "DER": 3, "HYP": 2, "ENG": 2, "SRC": 1}

REGISTRY_PATH = pathlib.Path(__file__).with_name("rscs_registry.yaml")


@dataclass(frozen=True)
class RSCSClassification:
    """Machine-readable RSCS classification metadata."""

    label: str
    registry: tuple[str, ...] = ()      # RSCS-C.* / RSCS-O.* ids
    provenance: tuple[str, ...] = ()     # EP-* ids (equation_provenance.yaml)
    units: str = ""                      # human-readable unit action
    exclusions: tuple[str, ...] = ()     # forbidden transfers that apply
    note: str = ""

    def __post_init__(self) -> None:
        if self.label not in VALID_CLASSES:
            raise ValueError(
                f"invalid RSCS class {self.label!r}; must be one of "
                f"{VALID_CLASSES}")

    def as_string(self) -> str:
        refs = "; ".join([*self.registry, *self.provenance])
        return f"{self.label} [{refs}]" if refs else self.label

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "registry": list(self.registry),
                "provenance": list(self.provenance), "units": self.units,
                "exclusions": list(self.exclusions), "note": self.note}


F = TypeVar("F", bound=Callable[..., Any])


def rscs_classified(label: str, *, registry: tuple[str, ...] | list[str] = (),
                    provenance: tuple[str, ...] | list[str] = (),
                    units: str = "", exclusions: tuple[str, ...] | list[str] = (),
                    note: str = "") -> Callable[[F], F]:
    """Attach :class:`RSCSClassification` to a claim-bearing RSCS callable."""
    meta = RSCSClassification(label, tuple(registry), tuple(provenance),
                              units, tuple(exclusions), note)

    def deco(fn: F) -> F:
        fn.rscs_classification = meta  # type: ignore[attr-defined]
        return fn
    return deco


def classification_of(fn: Callable[..., Any]) -> RSCSClassification:
    """Return the RSCSClassification of a decorated callable (raises if none)."""
    meta = getattr(fn, "rscs_classification", None)
    if meta is None:
        raise AttributeError(f"{getattr(fn, '__name__', fn)!r} is not "
                             f"rscs_classified")
    return meta


#: Rank at/above which a claim is "strong" (grounded): DER and EST.
STRONG_RANK = 3


def assert_no_src_upgrade(output_label: str, *input_labels: str) -> None:
    """Firewall: weak evidence may not be laundered into a strong claim.

    Enforces design principle 4: "No SRC claim may flow directly into EST or
    DER output without an explicit HYP or ENG boundary node." Concretely, a
    STRONG output (DER/EST, rank >= 3) is forbidden whenever ANY input is WEAK
    (HYP/ENG/SRC, rank < 3): reaching a grounded claim from weak evidence
    requires NEW evidence (a passed test), not relabeling. The allowed
    boundary move SRC/HYP -> HYP/ENG (weak -> weak) is permitted. Raises
    ValueError on a forbidden upgrade."""
    if output_label not in VALID_CLASSES:
        raise ValueError(f"invalid output class {output_label!r}")
    for lbl in input_labels:
        if lbl not in VALID_CLASSES:
            raise ValueError(f"invalid input class {lbl!r}")
    if CLASS_RANK[output_label] >= STRONG_RANK:
        weak = [lbl for lbl in input_labels if CLASS_RANK[lbl] < STRONG_RANK]
        if weak:
            raise ValueError(
                f"claim firewall violation: strong output {output_label!r} "
                f"from weak input(s) {weak}; route through an explicit "
                f"HYP/ENG boundary node (design principle 4)")


_REGISTRY_CACHE: dict[str, Any] | None = None


def load_registry(path: pathlib.Path | None = None) -> dict[str, Any]:
    """Load and validate the machine-readable RSCS registry yaml."""
    global _REGISTRY_CACHE
    if path is None and _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE
    p = path or REGISTRY_PATH
    with open(p, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    _validate_registry(data)
    if path is None:
        _REGISTRY_CACHE = data
    return data


def _validate_registry(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("rscs_registry.yaml schema_version must be 1")
    seen: set[str] = set()
    for kind in ("coordinates", "operators"):
        for entry in data.get(kind, []):
            rid = entry["id"]
            if rid in seen:
                raise ValueError(f"duplicate registry id {rid}")
            seen.add(rid)
            if entry["class"] not in VALID_CLASSES:
                raise ValueError(f"{rid}: bad class {entry['class']!r}")
            for req in ("name", "units", "module", "tests"):
                if not entry.get(req):
                    raise ValueError(f"{rid}: missing '{req}'")


def registry_ids(path: pathlib.Path | None = None) -> set[str]:
    """Set of all RSCS-C.*/RSCS-O.* ids declared in the registry."""
    data = load_registry(path)
    ids: set[str] = set()
    for kind in ("coordinates", "operators"):
        ids.update(e["id"] for e in data.get(kind, []))
    return ids
