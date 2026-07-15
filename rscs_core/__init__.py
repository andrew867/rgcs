"""rscs_core: Resonant Spacetime Coordinate System (RSCS 1.0) framework.

Typed coordinate/state-space foundation for RGCS v3. Agent 03 implements the
mathematical backbone: 14 typed coordinates (RSCS-C.*), 13 operators
(RSCS-O.*), the RGCS->RSCS embedding (iota) and its Conservative Extension
Property. See docs/RSCS_MATHEMATICAL_MODEL.md and docs/RSCS_OPERATOR_REGISTRY.md.

Layout:
  units.py           canonical units + CEP tolerances
  registry/          classification firewall + machine-readable id registry
  coordinates/       RSCS-C.1 .. RSCS-C.14 typed records
  transforms/ coupling/ modes/ propagation/ state_preparation/
  observation/ uncertainty/ provenance/ memory/   the RSCS-O.* operators
  operators/         flat re-export facade over all 13 operators
  embedding/         iota adapters + Conservative Extension Property checks

RSCS never redefines or mutates frozen v2 mathematics (RGCS-M.1..61); where an
operator generalizes a v2 equation it reproduces it exactly on the v2 domain.
"""

from __future__ import annotations

__version__ = "1.0.0a1"

from .registry import (RSCS_MODEL_VERSION, VALID_CLASSES, rscs_classified,
                       classification_of, load_registry, registry_ids)

__all__ = ["RSCS_MODEL_VERSION", "VALID_CLASSES", "rscs_classified",
           "classification_of", "load_registry", "registry_ids"]
