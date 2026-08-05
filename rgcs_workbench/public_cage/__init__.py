"""RGCS public workbench release cage (RC1 cage stage).

The cage is the boundary layer that goes in BEFORE any physical
hypothesis module is imported into the public workbench. It holds the
public module registry, the claim firewall, and the frozen Terra RC4
reference. Nothing in this package computes force, thrust, lift, or
any power-to-performance quantity, and nothing in it may promote a
hypothesis to a validated physical claim.

Status strings used here are contractual and exact:

    PUBLIC_WORKBENCH
    OPERATIONAL_CALIBRATED_PROFILE
    MEASUREMENT_HYPOTHESIS_NOT_VALIDATED
    PHYSICAL_VALIDATION_PENDING
    HOLDOUT_REQUIRED
    NO_PHYSICAL_CLAIM_ADVANCED

This package does release gating. It does not claim propulsion, lift,
antigravity, gravity control, source authentication, free energy, or
validated craft performance. Bench receipts and independent
replication remain pending for every physical hypothesis lane.
"""

from __future__ import annotations

CAGE_STAGE = "RGCS_WORKBENCH_PUBLIC_RC1_CAGE"

__all__ = ["CAGE_STAGE"]
