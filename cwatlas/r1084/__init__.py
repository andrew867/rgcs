"""R10.8.4 — Recursive Interleaved XYZ Hedron decoder (``cwatlas.r1084``).

Locked interpretation (operator, 2026-07-25): a CW source vector's decimal
digits group into ordered XYZ triplets; **each triplet is one hierarchical
refinement instruction**, not a column of a completed decimal fraction.

    165876523 -> L1 (1,6,5) -> L2 (8,7,6) -> L3 (5,2,3)

X and Y refine the current spherical-triangle surface cell; Z refines the
current radial shell interval. Latitude/longitude appear only after the final
level, through the locked Wilkes/SAA/epoch Earth frame.

Superseded (rejected, regression-tested): five base-100 tokens, contiguous
XYZ blocks, completed decimal fractions, direct XYZ->lat/lon, shell from the
final digit, fixed nine-digit maximum length.

SOURCE_ORIGIN_VALIDATED: no. PHYSICAL_ANOMALOUS_GRAVITY_VALIDATED: no.
Everything here is DERIVED_MATHEMATICS at the SOFTWARE level
(:mod:`cwatlas.r1082.claims` discipline applies).
"""

from cwatlas.r1084.cw_recursive_xyz import (  # noqa: F401
    CWLevelInstruction, CWPartialLevel, CWRawVector, parse_levels,
    REJECTED_MODELS)
from cwatlas.r1084.cw_recursive_decoder import decode  # noqa: F401
from cwatlas.r1084.cw_recursive_encoder import encode_point  # noqa: F401
