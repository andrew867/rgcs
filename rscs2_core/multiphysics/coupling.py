"""Typed block-structured coupling graph (Agent M2; shared schema
section 2). The graph compiler REFUSES an edge whose capability
predicate the material record does not satisfy — before any numerics."""

from __future__ import annotations

from dataclasses import dataclass, field

from .capabilities import MaterialCapabilities, applicability

BLOCK_IDS = ("mechanical", "electrical", "optical", "thermal", "spin",
             "magnon", "exciton", "phonon_internal", "domain",
             "plasmonic", "statistical", "calibration",
             "source_hypothesis")


class CouplingRejected(ValueError):
    """Raised when an edge cannot activate for the material."""


@dataclass(frozen=True)
class CouplingEdge:
    source_block: str
    target_block: str
    operator_id: str
    units: str
    symmetry: str
    capability_requirement: str          # a registered capability key
    classification: str
    source_ids: tuple = ()
    equation_ids: tuple = ()
    reversible: bool = True
    energy_accounting: str = "conservative"
    parameter_set_id: str | None = None
    null_behavior: str = "zero-coupling limit reproduces uncoupled blocks"

    def __post_init__(self):
        for b in (self.source_block, self.target_block):
            if b not in BLOCK_IDS:
                raise ValueError(f"unknown state block '{b}'")
        if not self.operator_id or not self.units:
            raise ValueError("operator_id and units are required")


@dataclass
class CouplingGraph:
    material: MaterialCapabilities
    edges: list = field(default_factory=list)
    _compiled: bool = False

    def add_edge(self, edge: CouplingEdge) -> None:
        if self._compiled:
            raise CouplingRejected("graph already compiled (frozen)")
        # source_hypothesis blocks may never couple into physics blocks
        if edge.source_block == "source_hypothesis" and \
                edge.target_block != "source_hypothesis":
            raise CouplingRejected(
                "source_hypothesis block cannot drive physics blocks "
                "(FDT/lore quarantine)")
        app = applicability(self.material, edge.capability_requirement)
        if app["applicability"] in ("NOT_APPLICABLE",):
            raise CouplingRejected(
                f"edge {edge.operator_id} requires capability "
                f"'{edge.capability_requirement}' which "
                f"{self.material.material_id} lacks: {app['reason']}")
        if app["applicability"] == "INTERFACE_ONLY" and \
                edge.classification not in ("INTERFACE_ONLY",
                                            "SOURCE_HYPOTHESIS"):
            raise CouplingRejected(
                f"edge {edge.operator_id}: capability is "
                "INTERFACE_ONLY; a computing edge may not activate")
        self.edges.append(edge)

    def compile(self) -> dict:
        """Freeze and return the typed graph description."""
        self._compiled = True
        return {
            "material_id": self.material.material_id,
            "blocks": sorted({e.source_block for e in self.edges}
                             | {e.target_block for e in self.edges}),
            "edges": [
                {"operator_id": e.operator_id,
                 "source": e.source_block, "target": e.target_block,
                 "units": e.units, "symmetry": e.symmetry,
                 "capability": e.capability_requirement,
                 "classification": e.classification,
                 "source_ids": list(e.source_ids),
                 "equation_ids": list(e.equation_ids),
                 "reversible": e.reversible,
                 "energy_accounting": e.energy_accounting,
                 "null_behavior": e.null_behavior}
                for e in self.edges],
        }
