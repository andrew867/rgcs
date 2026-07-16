"""v4-completion multiphysics core (Agent M2): material capability
firewall, block-structured coupled state, typed coupling graph, and
the public result envelope. Every v4-completion module request passes
through this layer; unsupported mechanisms yield typed NOT_APPLICABLE
results, never numeric zeros."""

from .capabilities import (ALLOWED_STATUS, CAPABILITY_KEYS,
                           CapabilityRecord, MaterialCapabilities,
                           applicability)
from .coupling import BLOCK_IDS, CouplingEdge, CouplingGraph
from .envelope import make_result, not_applicable_result
from .materials import MATERIALS, get_material

__all__ = ["ALLOWED_STATUS", "CAPABILITY_KEYS", "CapabilityRecord",
           "MaterialCapabilities", "applicability", "BLOCK_IDS",
           "CouplingEdge", "CouplingGraph", "make_result",
           "not_applicable_result", "MATERIALS", "get_material"]
