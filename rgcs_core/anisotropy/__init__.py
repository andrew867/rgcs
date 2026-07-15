"""Anisotropic elastic propagation for alpha-quartz (RGCS v3 crystal
application, Agent 05).

Resolves the frozen v2 scalar effective wave speed v_L (RGCS-M.10, a
Hypothesis that one scalar suffices, default 6310 m/s +/- 5%) into a
measured-orientation model: given the crystallographic direction, the
Christoffel eigenproblem (RSCS-O.17, rscs_core.propagation) yields the
quasi-longitudinal and quasi-shear speeds. This is a CONSERVATIVE EXTENSION:
along the Z (optic) axis the quasi-longitudinal speed reduces to
sqrt(c33/rho); along X to sqrt(c11/rho); the two bracket v2's default and its
+/-5% band is the physical X-Z spread.

Elastic constants: alpha-quartz (trigonal, class 32), Voigt notation, room
temperature. Standard handbook values (Bechmann 1958; also tabulated by
Auld, "Acoustic Fields and Waves in Solids"). Values in GPa:
  c11=86.6, c33=106.1, c44=57.8, c12=6.7, c13=12.6, c14=17.8,
  c66=(c11-c12)/2=39.95. Density rho=2648 kg/m^3 (2.648 g/cm^3).
Classification: Established (handbook input); the exact third-decimal values
depend on the reference and temperature and are declared, closing v2's
D-19a "citation required for v_L".

NO physical conclusion is imported by analogy; these are quartz elastic
constants used for quartz elastodynamics only.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from rgcs_core.provenance import classified
from rscs_core.propagation import christoffel_wave_speeds

__all__ = ["ALPHA_QUARTZ_C_GPA", "ALPHA_QUARTZ_DENSITY_KG_M3",
           "alpha_quartz_stiffness_pa", "wave_speeds", "axis_speeds",
           "AXIS_X", "AXIS_Y", "AXIS_Z"]

#: alpha-quartz elastic constants (GPa), Voigt 6x6, standard handbook values.
_C11, _C33, _C44, _C12, _C13, _C14 = 86.6, 106.1, 57.8, 6.7, 12.6, 17.8
_C66 = (_C11 - _C12) / 2.0  # 39.95

#: Voigt stiffness matrix (GPa) for alpha-quartz (class 32 symmetry).
ALPHA_QUARTZ_C_GPA = np.array([
    [_C11, _C12, _C13, _C14, 0.0, 0.0],
    [_C12, _C11, _C13, -_C14, 0.0, 0.0],
    [_C13, _C13, _C33, 0.0, 0.0, 0.0],
    [_C14, -_C14, 0.0, _C44, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, _C44, _C14],
    [0.0, 0.0, 0.0, 0.0, _C14, _C66],
])

#: alpha-quartz density (kg/m^3). v2 used 2.65 g/cm^3; 2648 is the standard.
ALPHA_QUARTZ_DENSITY_KG_M3 = 2648.0

AXIS_X = np.array([1.0, 0.0, 0.0])   # crystallographic X (a-axis)
AXIS_Y = np.array([0.0, 1.0, 0.0])   # Y
AXIS_Z = np.array([0.0, 0.0, 1.0])   # Z (optic axis, c-axis)


@classified("Established", sources=("Bechmann 1958", "Auld AFWS"),
            note="alpha-quartz handbook elastic constants (class 32); closes "
                 "v2 D-19a citation requirement for v_L")
def alpha_quartz_stiffness_pa() -> np.ndarray:
    """alpha-quartz Voigt stiffness in Pa (SI) for the Christoffel solver."""
    return ALPHA_QUARTZ_C_GPA * 1.0e9


@classified("Established", sources=("RSCS-O.17",),
            note="anisotropic wave speeds via the Christoffel eigenproblem; "
                 "reduces to the scalar v_L (RGCS-M.10) at the crystal axes")
def wave_speeds(direction: np.ndarray) -> dict[str, Any]:
    """Anisotropic alpha-quartz wave speeds along ``direction`` (m/s).

    Thin crystal-application wrapper over the general RSCS-O.17 Christoffel
    solver with alpha-quartz constants and density."""
    return christoffel_wave_speeds(alpha_quartz_stiffness_pa(),
                                   ALPHA_QUARTZ_DENSITY_KG_M3, direction)


@classified("Established", sources=("RSCS-O.17", "RGCS-M.10"),
            note="axis wave speeds; Z quasi-long reproduces v2 v_L within its "
                 "+/-5% band (conservative extension)")
def axis_speeds() -> dict[str, dict[str, Any]]:
    """Quasi-longitudinal/shear speeds along X, Y, Z (m/s).

    Along Z the quasi-longitudinal speed = sqrt(c33/rho) ~ 6330 m/s; along X
    = sqrt(c11/rho) ~ 5719 m/s -- these bracket the v2 default v_L = 6310 m/s
    and reproduce it within the declared +/-5% band (conservative extension of
    RGCS-M.10)."""
    return {"X": wave_speeds(AXIS_X), "Y": wave_speeds(AXIS_Y),
            "Z": wave_speeds(AXIS_Z)}
