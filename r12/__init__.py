"""RGCS R12.

The icosahedral packet grammar (F5 | Q22 | S3), quaternary triangular
refinement, eight radial shells, a South-referenced body frame that does
not force a hemisphere inversion, an IGRF-14 magnetic-root certificate at
an explicit epoch, isotopic and astronomical epoch candidates, a
reciprocal-space crystal and scattering model, typed cross-domain
coupling certificates, and home-lab experiment plans.

Two disciplines carry across every module here.

**The grammar is not a decoder.** A 30-bit word parses cleanly into a
face, a refinement path and a shell, and that is a statement about
arithmetic. It becomes a location only when face numbering, body
orientation, magnetic root, handedness and shell projection are each
independently frozen -- and none of them is.

**Cross-domain transfer is no longer categorically refused; it is
licensed.** R11.1 refused every transfer between physical domains. R12
replaces that with ``NO_AUTOMATIC_EQUIVALENCE`` plus
``TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE``: a bridge may be
built, but only if it declares its domains, state variables and units,
coupling operator, overlap factor, detuning and damping, phase matching
and symmetry, energy accounting, uncertainty and null model, and a
measurement capable of falsifying it. The default remains refusal.

Everything here is arithmetic, literature values, and software. No
physical measurement is performed by any module.
"""

from __future__ import annotations

__all__ = [
    "bodylock",
    "bridge",
    "epochcand",
    "homelab",
    "icosapacket",
    "icosarefine",
    "igrf14root",
    "reciprocal",
    "shells8",
]
