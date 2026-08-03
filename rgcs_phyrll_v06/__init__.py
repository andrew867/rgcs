"""RGCS Phyrll / craft model v0.6 (supersedes v0.5).

Implements the v0.5 research lane upgraded per the v0.6 correction note:
coefficients carry typed ROLES (force/coupling vs geometry vs geodesic
calibration), the Bermuda/Miami calibration lane is separate, and the
public-release filter lives in ``rgcs_terra_release``.

Hard boundaries, enforced by tests as well as stated:

    No claim of antigravity, reactionless propulsion, free energy,
    source authentication, verified flight, or proven nonhuman
    communication. A successful run does NOT prove the craft; it gives a
    reproducible mathematical scaffold whose remaining blockers are
    measured material parameters, field maps and bench receipts.

Every exported quantity carries one claim tag from ``CLAIM_TAGS``.

    PUBLICATION: HOLD
"""

from __future__ import annotations

RUN_ID = "R10.71-PHYRLL-TERRA-V06"

CLAIM_TAGS = (
    "EXACT_ARITHMETIC", "SOURCE_PROVENANCE", "MODEL_OUTPUT",
    "PRIOR_ART_ANALOGUE", "BENCH_REQUIRED", "UNRESOLVED", "REFUTED",
    "PUBLIC_RELEASE_ALLOWED", "PRIVATE_EXCLUDED",
)

FORBIDDEN_CLAIMS = (
    "antigravity", "reactionless_propulsion", "free_energy",
    "source_authentication", "flight_validation",
    "proven_nonhuman_communication",
)

PUBLICATION_STATUS = "HOLD"

__all__ = ["RUN_ID", "CLAIM_TAGS", "FORBIDDEN_CLAIMS", "PUBLICATION_STATUS"]
