"""RSCS-O.5 parity / supermode basis-change operator.

Even/odd (symmetric/antisymmetric) supermode basis for two coupled modes
(EP-02-02 Cheng, EP-06-02 Chao). The change of basis is the fixed unitary

    P = (1/sqrt(2)) [[1, 1], [1, -1]]

which is its own inverse (P = P^dagger = P^-1). Applied to a two-mode
ModalState it returns the (even, odd) amplitudes; applied twice it is the
identity. This reproduces the eigenbasis of the degenerate two-mode problem
(RGCS-M.23-25): for f_a = f_b the even/odd states ARE the hybrid eigenstates.
Exclusion: no waveguide/TMOKE device physics imported.
"""

from __future__ import annotations

import numpy as np

from ..coordinates import ModalState
from ..registry import rscs_classified

__all__ = ["parity_matrix", "to_parity_basis", "from_parity_basis"]

_INV_SQRT2 = 1.0 / np.sqrt(2.0)
#: The symmetric/antisymmetric change-of-basis (its own inverse).
_P = _INV_SQRT2 * np.array([[1.0, 1.0], [1.0, -1.0]])


@rscs_classified("EST", registry=("RSCS-O.5",),
                 provenance=("EP-02-02", "EP-06-02"), units="dimensionless",
                 note="fixed unitary even/odd basis change; self-inverse")
def parity_matrix() -> np.ndarray:
    """The 2x2 symmetric/antisymmetric (even/odd) basis-change matrix."""
    return _P.copy()


def _require_pair(state: ModalState) -> None:
    if not isinstance(state, ModalState):
        raise TypeError("state must be a ModalState (RSCS-C.7)")
    if state.n_modes != 2:
        raise ValueError("parity basis change is defined for 2 modes")


@rscs_classified("EST", registry=("RSCS-O.5",),
                 provenance=("EP-02-02", "EP-06-02"), units="dimensionless",
                 exclusions=("no waveguide/TMOKE device physics "
                             "(SRC-3-02, SRC-3-06)",),
                 note="(psi_1, psi_2) -> (even, odd); unitary, occupancy "
                      "conserved")
def to_parity_basis(state: ModalState) -> ModalState:
    """Map a two-mode state into the even/odd supermode basis."""
    _require_pair(state)
    return ModalState(_P @ state.amplitudes)


@rscs_classified("EST", registry=("RSCS-O.5",),
                 provenance=("EP-02-02", "EP-06-02"), units="dimensionless",
                 note="inverse of to_parity_basis (P is self-inverse)")
def from_parity_basis(state: ModalState) -> ModalState:
    """Map an (even, odd) state back to the individual-mode basis."""
    _require_pair(state)
    return ModalState(_P @ state.amplitudes)
