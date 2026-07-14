"""rgcs_core.coupled_modes — two-mode and N-mode eigenproblems, avoided
crossings, and complex modal dynamics (RGCS-M.23..M.29, M.46..M.49).

Units: matrix entries and frequencies in Hz; mixing angle in rad
(reported also in deg); damping/coupling rates in 1/s (rad/s where noted).

Consistency contract: a fitted time-domain coupling K_nm must reproduce
the frequency-domain splitting, K_nm = pi * g_nm (g in Hz); disagreement
is a pre-registered warning flag (RGCS-M.46 table).
"""

from .static import (coupled_two_mode, n_mode_eigenproblem,
                     avoided_crossing_sweep, coupling_geometry_scaling,
                     coupling_rate_from_g_hz, g_hz_from_coupling_rate,
                     coupling_consistency)
from .dynamics import integrate_stuart_landau, stuart_landau_pair

__all__ = ["coupled_two_mode", "n_mode_eigenproblem",
           "avoided_crossing_sweep", "coupling_geometry_scaling",
           "coupling_rate_from_g_hz", "g_hz_from_coupling_rate",
           "coupling_consistency", "integrate_stuart_landau",
           "stuart_landau_pair"]
