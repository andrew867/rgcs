"""RGCS R13.

A complete cross-domain discovery-and-experiment architecture: a common
linear-response core (response functions, Green functions, S-matrices),
an atomistic-to-continuum-to-electrical quartz chain, symplectic /
Floquet / quasi-phase-matching transform models, a full home-lab
apparatus and detector stack (all preregistered, none built), synthetic
neutron and X-ray scattering predictions, and the finalized coordinate
codec with its decoder holdout.

Three rules carry across everything here.

**Simulation is not measurement, and a certificate is not evidence.** The
bridge architecture (extending R12) permits a cross-domain transfer only
with a certificate that declares its operator, units, constitutive law,
overlap, detuning, damping, phase matching, symmetry, energy path,
calibration, uncertainty, null model, and a falsifying measurement. Until
that measurement is performed -- and none can be, here -- the certificate
is an engineering candidate, never a bench result.

**No promotion.** Algebraic similarity does not become physical
equivalence; a numeric match does not become source authentication; an
unclosed energy ledger does not become new energy; angular uniformity in
a plane does not become three-dimensional isotropic emission; a
coordinate alias does not become a decoded destination; and a theoretical
exotic-particle paper does not become evidence for an RGCS carrier.

**Blocked is stated, not hidden.** Where a phase needs a bench, a neutron
facility, beam time, or data that does not exist in this environment, it
carries a complete ``BLOCKED_MISSING_INPUT`` receipt and every other
phase continues.

No physical measurement is performed by any module here.
"""

from __future__ import annotations

__all__ = [
    "apparatus",
    "atomistic",
    "avoided",
    "boundaryenergy",
    "bridgegraph",
    "chiral",
    "claimtypes",
    "coordfinal",
    "crystalframe",
    "daq",
    "diskdrive",
    "epochsolve",
    "euphonic",
    "experiments",
    "floquet",
    "heterodyne",
    "holdout",
    "homogenize",
    "imaging",
    "magroot",
    "piezobridge",
    "preregister",
    "qcmstack",
    "qpm",
    "quadfield",
    "response",
    "scattering",
    "serialize",
    "shellmap",
    "sixangle",
    "srcregistry",
    "symplectic",
]
