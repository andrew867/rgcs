"""P09 (A55-A63) — localized optical spin addressing, typed and gated.

SAM and OAM are distinct EM angular-momentum categories (core/04) and
never merge. Spin "initialization" and "readout" are OPERATIONAL
HYPOTHESES about light-matter interaction with named mechanisms; the
relaxation ledger makes any stored polarization decay (T1/T2 finite),
so optical spin cannot become a perfect-memory claim. The voxel/dose
model enforces the v4.6 optical safety gates numerically.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import ClaimBoundaryError
from .spin_torsion import SpinQuantity

#: Conservative enclosed-bench dose ceiling for this programme's
#: planning documents (not a laser-safety certification).
MAX_INTENSITY_W_CM2 = 1.0


@dataclass(frozen=True)
class OpticalSpinState:
    """One addressed voxel's optical angular-momentum bookkeeping."""
    voxel_id: str
    sam: SpinQuantity                 # EM_SPIN_ANGULAR_MOMENTUM
    oam: SpinQuantity                 # EM_ORBITAL_ANGULAR_MOMENTUM
    polarization: str
    wavelength_nm: float

    def __post_init__(self):
        if self.sam.category != "EM_SPIN_ANGULAR_MOMENTUM":
            raise ClaimBoundaryError("sam field must carry the SAM "
                                     "category")
        if self.oam.category != "EM_ORBITAL_ANGULAR_MOMENTUM":
            raise ClaimBoundaryError("oam field must carry the OAM "
                                     "category")

    @property
    def total(self):
        """Deliberately absent as a scalar: SAM+OAM is a category
        merge. Report both, always."""
        raise ClaimBoundaryError(
            "SAM and OAM do not merge into one scalar (core/04); "
            "report both components")


def voxel_dose(power_w: float, spot_diameter_um: float,
               exposure_s: float) -> dict:
    """A56: intensity and fluence for one addressed voxel, with the
    enclosed-bench ceiling enforced."""
    if power_w <= 0 or spot_diameter_um <= 0 or exposure_s <= 0:
        raise ClaimBoundaryError("dose inputs must be positive")
    area_cm2 = math.pi * (spot_diameter_um * 1e-4 / 2) ** 2
    intensity = power_w / area_cm2
    ok = intensity <= MAX_INTENSITY_W_CM2
    return {"intensity_w_cm2": intensity,
            "fluence_j_cm2": intensity * exposure_s,
            "within_programme_ceiling": ok,
            "verdict": "PLAN_OK" if ok else "REFUSED_DOSE",
            "note": "enclosed beam, lowest practical class, no eye-"
                    "height path (v4.6 optical gates); this is a "
                    "planning bound, not a certification",
            "evidence_class": "ANALYTIC_MODEL"}


def sam_oam_transfer_audit(mechanism: str) -> dict:
    """A59: what optical AM transfer to matter is actually established
    vs hypothesised for quartz."""
    known = {
        "absorption_sam_to_electron_spin":
            ("ESTABLISHED_ELSEWHERE", "optical orientation in "
             "semiconductors; NOT demonstrated in quartz here"),
        "oam_to_mechanical_rotation":
            ("ESTABLISHED_ELSEWHERE", "optical torque on trapped "
             "particles; irrelevant to a mounted crystal at these "
             "powers"),
        "sam_to_lattice_spin_texture":
            ("OPERATIONAL_HYPOTHESIS", "no mechanism demonstrated in "
             "alpha-quartz; remains a plan"),
    }
    if mechanism not in known:
        raise ClaimBoundaryError(f"unknown transfer {mechanism!r}")
    status, note = known[mechanism]
    return {"mechanism": mechanism, "status": status, "note": note,
            "evidence_class": "SOURCE_CLAIM" if status ==
            "OPERATIONAL_HYPOTHESIS" else "ANALYTIC_MODEL"}


def relaxation_ledger(t1_s: float, t2_s: float,
                      hold_s: float) -> dict:
    """A61: any stored polarization decays; T2 <= 2*T1 always, and the
    surviving fraction after a hold is exp(-hold/T)."""
    if t1_s <= 0 or t2_s <= 0:
        raise ClaimBoundaryError("relaxation times must be positive "
                                 "and finite — infinite T is the "
                                 "perfect-memory claim again")
    if t2_s > 2 * t1_s:
        raise ClaimBoundaryError("T2 > 2*T1 is unphysical")
    return {"t1_s": t1_s, "t2_s": t2_s, "hold_s": hold_s,
            "population_remaining": math.exp(-hold_s / t1_s),
            "coherence_remaining": math.exp(-hold_s / t2_s),
            "evidence_class": "ANALYTIC_MODEL"}
