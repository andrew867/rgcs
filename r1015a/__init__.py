"""RGCS R10.15A — Scale A mechanical (bulk-acoustic) crystal candidate.

A SEPARATE research lane from ``rgcs_surface_wave``. That package
studies an *electromagnetic* annular surface-wave device and returned a
negative result for 4096 Hz as its carrier. This package studies a
*mechanical* bulk-acoustic candidate: a six-sided Vogel-terminated
quartz body whose first-order half-wave shear path lands on 4096 Hz.

The two lanes share nothing but the number 4096, and that coincidence
is not evidence. Nothing here reopens or weakens the R10.15
electromagnetic result, which is preserved verbatim in
``EM_NEGATIVE_RESULT`` and guarded by ``assert_em_boundary``.

STATUS OF EVERY OUTPUT: geometry and analytic proxy only. The
463.8671875 mm figure is an exact first-order half-wave path candidate
under a scalar 3800 m/s shear proxy. It is NOT a measured resonance
and NOT the final physical tip-to-tip cut length. The physical length
requires termination, electrode, fixture, temperature and machining
corrections that are not yet solved, and the actual eigenmodes require
full anisotropic 3D FEM that this release specifies but does not run
to convergence.
"""

__version__ = "0.10.15a"
DESIGN_ID = "SCALE_A_4096HZ_SHEAR_463P867_SIX_SIDED"
PUBLICATION_STATUS = "HOLD"
STATUS = "GEOMETRY_AND_HALF_WAVE_PROXY_ONLY"

#: The R10.15 electromagnetic findings, frozen. This package must not
#: modify, reinterpret, or "supersede" any of them.
EM_NEGATIVE_RESULT = {
    "lane": "rgcs_surface_wave (electromagnetic, R10.15)",
    "annular_eigenmode_hz": 1150903000.0,
    "annular_eigenmode_note": "approximately 1.150903 GHz",
    "4096_hz_as_em_carrier": "FALSIFIED for that geometry",
    "sideband_resolution": "16 Hz sidebands required an unattainable Q "
                           "for that model (Q > 3.6e7 needed, <= 49 "
                           "available)",
    "reversed_modulation": "zero nonreciprocal contrast",
    "lateral_force": "tracked ordinary mask asymmetry and closed "
                     "against the support reaction",
    "verification": "manufactured solutions, independent formulations, "
                    "and privacy gates all passed",
    "status": "FROZEN_DO_NOT_REOPEN",
}

#: Claims this lane may never advance.
FORBIDDEN_CLAIMS = (
    "propulsion", "anomalous force", "gravity modification",
    "free energy", "measured phryll", "over-unity", "reactionless",
)


class ScaleAError(ValueError):
    """Typed refusal for the Scale A lane."""


def assert_em_boundary(claimed_carrier_hz=None, new_geometry=False,
                       new_eigenproblem=False, holdout_criteria=False,
                       explicit_result=False) -> None:
    """4096 Hz may never become the electromagnetic carrier again
    without ALL FOUR of: a new geometry, a new eigenproblem, declared
    holdout criteria, and an explicit executed result.

    This is deliberately hard to satisfy. The R10.15 result was
    obtained before the device was changed, and changing the device
    after seeing the result is exactly the failure mode this guard
    exists to prevent.
    """
    if claimed_carrier_hz is None:
        return
    if not (new_geometry and new_eigenproblem and holdout_criteria
            and explicit_result):
        missing = [n for n, v in (("new_geometry", new_geometry),
                                  ("new_eigenproblem", new_eigenproblem),
                                  ("holdout_criteria", holdout_criteria),
                                  ("explicit_result", explicit_result))
                   if not v]
        raise ScaleAError(
            f"refused: {claimed_carrier_hz} Hz cannot be treated as an "
            f"electromagnetic carrier. Missing {missing}. The R10.15 "
            "result falsified 4096 Hz as the EM carrier for the tested "
            "annular geometry; this lane is MECHANICAL and its 4096 Hz "
            "candidate is an acoustic half-wave path, not an "
            "electromagnetic one.")
