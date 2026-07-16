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


#: V4C-D-003 (Q1 adversarial find): operator-id families carry a
#: MINIMUM required capability. An edge whose declared
#: capability_requirement does not match its operator family is
#: capability LAUNDERING and is rejected — a forged edge cannot
#: activate a banned mechanism through a capability the material
#: legitimately has.
OPERATOR_CAPABILITY_FLOOR = {
    "op.iome": "domain_writing",
    "op.domain": "domain_writing",
    "op.magnon": "magnon_modes",
    "op.exciton": "exciton_frenkel",
    "op.spin": "magnetic_order",
    "op.me": "magnetoelectric_dynamic",
    "op.toroidal": "ferrotoroidic_order",
    "op.metacrystal": "quantum_statistical_response",
    "op.plasmon": "plasmonic_near_field",
    "op.tunnel": "microscopic_tunnelling_model",
    "op.chiral_phonon": "chiral_phonons",
    "op.fdt": None,          # never activatable through the graph
}


def _operator_floor(operator_id: str):
    matches = [(p, c) for p, c in OPERATOR_CAPABILITY_FLOOR.items()
               if operator_id.startswith(p)]
    if not matches:
        return False, None
    # longest prefix wins
    return True, max(matches, key=lambda t: len(t[0]))[1]


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
        floored, floor_cap = _operator_floor(edge.operator_id)
        if floored:
            if floor_cap is None:
                raise CouplingRejected(
                    f"operator {edge.operator_id} can never activate "
                    "through the coupling graph (quarantined family)")
            if edge.capability_requirement != floor_cap:
                raise CouplingRejected(
                    f"capability laundering: operator "
                    f"{edge.operator_id} requires capability "
                    f"'{floor_cap}', not "
                    f"'{edge.capability_requirement}' (V4C-D-003)")
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
