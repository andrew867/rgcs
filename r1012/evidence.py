"""R10.12 Phase 02 — executable evidence tiers.

Every API result in this package carries exactly one tier. Tier
ordering is epistemic, not numeric: SOURCE_KNOWN outranks any
conditional tier; REVOKED/HISTORICAL_ONLY can never be active.
"""

from __future__ import annotations

from enum import Enum


class Tier(str, Enum):
    SOURCE_KNOWN = "SOURCE_KNOWN"
    CONDITIONAL_CONSENSUS = "CONDITIONAL_CONSENSUS"
    CONDITIONAL_COMPLETION = "CONDITIONAL_COMPLETION"
    UNDERDETERMINED = "UNDERDETERMINED"
    FALSIFIED_FAMILY = "FALSIFIED_FAMILY"
    UNSUPPORTED = "UNSUPPORTED"
    HISTORICAL_ONLY = "HISTORICAL_ONLY"
    REVOKED = "REVOKED"


#: Tiers that may back an ACTIVE computation.
ACTIVE_TIERS = frozenset({Tier.SOURCE_KNOWN, Tier.CONDITIONAL_CONSENSUS,
                          Tier.CONDITIONAL_COMPLETION})

#: Tiers that must REFUSE when asked to produce a definite value.
REFUSING_TIERS = frozenset({Tier.UNDERDETERMINED, Tier.FALSIFIED_FAMILY,
                            Tier.UNSUPPORTED, Tier.HISTORICAL_ONLY,
                            Tier.REVOKED})


class TierError(ValueError):
    """A revoked/historical/underdetermined artifact was asked to act."""


def assert_active(tier: Tier, what: str) -> None:
    if tier not in ACTIVE_TIERS:
        raise TierError(
            f"refused: {what} carries evidence tier {tier.value}, which "
            f"cannot back an active computation")
