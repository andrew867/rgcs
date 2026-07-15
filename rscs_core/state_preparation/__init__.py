"""RSCS-O.9 state-preparation operator.

Prepares a ModalState (RSCS-C.7) from a polarization/spin coordinate
(RSCS-C.9) and a selection coordinate (RSCS-C.10). Adapted from the
state-dependent-coupling and velocity-selection templates (EP-04-02 Wang,
EP-05-01 Zhang). Occupancy is conserved: the prepared state is normalized so
that sum |psi|^2 equals the input population weight. No atomic-vapor /
single-photon physics is imported (EXCLUSION_MATRIX SRC-3-04, SRC-3-05).
"""

from __future__ import annotations

import numpy as np

from ..coordinates import ModalState, PolarizationState, SelectionCoordinate
from ..registry import rscs_classified

__all__ = ["prepare_two_level"]


@rscs_classified("DER", registry=("RSCS-O.9",),
                 provenance=("EP-04-02", "EP-05-01"),
                 units="dimensionless (prepared occupancy)",
                 exclusions=("no atomic-vapor NLNR physics (SRC-3-04)",
                             "no single-photon/quantum-regime physics "
                             "(SRC-3-05)"),
                 note="two-level preparation: helicity sets the relative "
                      "phase/weight, population sets total occupancy")
def prepare_two_level(pol: PolarizationState,
                      sel: SelectionCoordinate) -> ModalState:
    """Prepare a two-mode ModalState from a spin state and a selection class.

    The circular helicity s3 in [-1, 1] maps to the population split between
    the two levels: weight_up = (1 + s3)/2, weight_dn = (1 - s3)/2. The
    selection ``population`` scales the total occupancy. Occupancy is
    conserved: sum |psi|^2 == sel.population."""
    if not isinstance(pol, PolarizationState):
        raise TypeError("pol must be a PolarizationState (RSCS-C.9)")
    if not isinstance(sel, SelectionCoordinate):
        raise TypeError("sel must be a SelectionCoordinate (RSCS-C.10)")
    h = pol.helicity
    w_up = (1.0 + h) / 2.0
    w_dn = (1.0 - h) / 2.0
    scale = sel.population
    amp = np.array([np.sqrt(w_up * scale), np.sqrt(w_dn * scale)],
                   dtype=complex)
    return ModalState(amp)
