"""A18-A24 — optical candidate screening, the water/microwave
translation, and preregistered experiment definitions.

**A20 water and 2.45 GHz.** The source says 2.45 GHz is "the frequency
of water". The actual physics is Debye dipolar relaxation, which is a
broad *relaxation* (not a sharp resonance) whose loss peak for bulk
liquid water at room temperature sits near 19 GHz. 2.45 GHz is an ISM
allocation chosen for penetration depth and component economics — at
that frequency water's dielectric loss is roughly a quarter of its
peak. ``debye_water`` computes this, so the correction is quantitative
rather than asserted.

**A18 optical candidate.** 4096 × 2³⁷ Hz is exact arithmetic
(``cspc.exact``). This module asks the physical question instead: what
would it take for a ~20 kHz mechanical mode to exchange energy with a
563 THz optical field? The honest answer is a nonlinear process with a
declared efficiency, and none is implemented or demonstrated. The
octave relation supplies no mechanism.

**A21/A24 experiments.** Every recipe is preregistered: target,
controls, randomisation, blinding, stopping rule, and the analysis are
fixed before data exists. Neighbour controls are mandatory — an effect
that also appears at 18.0 and 18.5 Hz is not specific to 18.25 Hz.

No apparatus has been built and no data has been collected. Every
recipe here is a PLAN.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction

from . import require_non_physical
from .exact import CONTROLS_HZ, FOLDS, OPTICAL_HZ
from .units import C_VACUUM, Quantity

# --- A20: water dielectric physics --------------------------------------

#: Single-Debye parameters for bulk liquid water at ~25 C.
WATER_EPS_STATIC = 78.4
WATER_EPS_INF = 5.2
WATER_TAU_S = 8.27e-12


def debye_water(frequency_hz: float, eps_s: float = WATER_EPS_STATIC,
                eps_inf: float = WATER_EPS_INF,
                tau_s: float = WATER_TAU_S) -> dict:
    """Complex permittivity of bulk water under a single-Debye model.

    eps(w) = eps_inf + (eps_s - eps_inf)/(1 + i*w*tau)
    """
    w = 2 * math.pi * frequency_hz
    wt = w * tau_s
    denom = 1 + wt ** 2
    eps_real = eps_inf + (eps_s - eps_inf) / denom
    eps_imag = (eps_s - eps_inf) * wt / denom
    return {"frequency_hz": frequency_hz, "eps_real": eps_real,
            "eps_imag": eps_imag, "omega_tau": wt,
            "evidence_class": "ANALYTIC_MODEL"}


def water_loss_peak_hz(tau_s: float = WATER_TAU_S) -> float:
    """Debye loss maximum: omega*tau = 1."""
    return 1.0 / (2 * math.pi * tau_s)


def water_2g45_correction() -> dict:
    """The quantitative form of CSPC-CORR-001."""
    peak = water_loss_peak_hz()
    at_ism = debye_water(2.45e9)
    at_peak = debye_water(peak)
    ratio = at_ism["eps_imag"] / at_peak["eps_imag"]
    return {
        "source_claim": "2.45 GHz is the frequency of water.",
        "status": "CORRECTED",
        "debye_loss_peak_hz": peak,
        "debye_loss_peak_ghz": peak / 1e9,
        "ism_frequency_hz": 2.45e9,
        "loss_at_2g45_relative_to_peak": ratio,
        "factor_below_peak": peak / 2.45e9,
        "is_a_resonance": False,
        "correction":
            "Water's microwave response is broad DIPOLAR RELAXATION, "
            "not a resonance. The loss maximum for bulk liquid water "
            f"at room temperature is near {peak / 1e9:.1f} GHz, about "
            f"{peak / 2.45e9:.1f}x above the ISM frequency, where the "
            f"loss is only ~{ratio * 100:.0f}% of its peak. 2.45 GHz "
            "was chosen for penetration depth, component cost, and "
            "spectrum allocation.",
        "evidence_class": "ANALYTIC_MODEL",
    }


# --- A18: optical candidate screening -----------------------------------

def optical_candidate_screening() -> dict:
    """What would coupling a ~20 kHz mode to the optical candidate
    require? (Not: does the arithmetic work — it does.)"""
    f_opt = float(OPTICAL_HZ.exact_hz)
    f_mech = float(FOLDS[9].exact_hz)          # ~18.25 Hz
    f_mech_khz = 20480.0
    lam = float((C_VACUUM / Quantity.of(int(OPTICAL_HZ.exact_hz), "Hz")
                 ).in_unit("nm"))
    return {
        "optical_hz": f_opt,
        "optical_wavelength_nm": lam,
        "mechanical_hz": f_mech_khz,
        "octaves_between": math.log2(f_opt / f_mech_khz),
        "orders_of_magnitude": math.log10(f_opt / f_mech_khz),
        "arithmetic_relation": "4096 * 2^37 = 2^49, exact",
        "required_mechanism":
            "a nonlinear process (e.g. acousto-optic or "
            "electro-optic modulation) with a declared conversion "
            "efficiency; direct linear coupling across ~35 octaves "
            "has no mechanism",
        "what_acousto_optics_actually_does":
            "an acoustic wave modulates the refractive index, "
            "producing optical SIDEBANDS at f_optical +/- f_acoustic. "
            "That is a 20 kHz offset on a 563 THz carrier — a "
            "fractional shift of ~4e-11 — not a conversion of one into "
            "the other.",
        "implemented_here": False,
        "status": "UNSUPPORTED",
        "firewall": "OPTICAL_FREQUENCY_TO_PHOTON_CONVERSION",
        "evidence_class": "ANALYTIC_MODEL",
    }


# --- A21/A24: preregistered experiment definitions -----------------------

@dataclass(frozen=True)
class Preregistration:
    """A plan fixed before data exists."""
    id: str
    question: str
    target_hz: tuple
    control_hz: tuple
    n_per_condition: int
    randomisation: str
    blinding: str
    stopping_rule: str
    primary_outcome: str
    analysis: str
    correction: str
    safety: tuple
    apparatus_status: str = "NOT BUILT"
    data_status: str = "NO DATA COLLECTED"
    evidence_class: str = "ANALYTIC_MODEL"

    def to_dict(self) -> dict:
        d = {k: (list(v) if isinstance(v, tuple) else v)
             for k, v in self.__dict__.items()}
        d["target_hz"] = [str(x) for x in self.target_hz]
        d["control_hz"] = [str(x) for x in self.control_hz]
        d["claim_boundary"] = (
            "PLAN ONLY. No apparatus was built, no data collected, and "
            "no result is implied. Registering a hypothesis is not "
            "evidence for it.")
        return d


def low_frequency_fold_experiment() -> Preregistration:
    """A21: does a specimen respond selectively at the 18.25 Hz fold?

    The controls are the experiment. 18.0, 18.5, 19.8, 20.0, 20.48 and
    21.0 Hz are driven identically; a response that appears at all of
    them is not specific to the candidate.
    """
    return Preregistration(
        id="CSPC-EXP-FOLD-18",
        question="Does the specimen show a response at "
                 "18.25392246246337890625 Hz that it does not show at "
                 "power-matched neighbouring frequencies?",
        target_hz=(FOLDS[9].exact_hz,),
        control_hz=tuple(Fraction(c) for c in CONTROLS_HZ),
        n_per_condition=20,
        randomisation="condition order randomised per block from a "
                      "seeded permutation; seed recorded before the "
                      "first run",
        blinding="the operator and the analyst are blind to which "
                 "frequency is driven; the mapping is sealed until "
                 "analysis is complete",
        stopping_rule="fixed N of 20 blocks per condition; no interim "
                      "peeking, no extension on a promising trend",
        primary_outcome="amplitude of the specimen's mechanical "
                        "response at the drive frequency, normalised "
                        "to drive level",
        analysis="preregistered: candidate vs pooled controls, "
                 "two-sided, effect size with CI reported alongside p",
        correction="Holm-Bonferroni across all conditions "
                   "(cspc.nulls.family_report)",
        safety=("isolated low-voltage current-limited drive",
                "piezo or dummy load only, no radiator",
                "separate thermal channel so heating cannot read as "
                "resonance",
                "stop on heating, arcing, fracture or smoke"),
    )


def optical_detuning_experiment() -> Preregistration:
    """A19: an optical plan whose controls include the fact that a
    stock 532.0 nm laser is NOT the candidate (0.1012% off)."""
    return Preregistration(
        id="CSPC-EXP-OPT-532",
        question="Does illumination near 532.538 nm produce a "
                 "specimen response beyond power, absorption, thermal "
                 "and ordinary optomechanical effects?",
        target_hz=(OPTICAL_HZ.exact_hz,),
        control_hz=(Fraction(563519657894737),),   # ~532.0 nm source
        n_per_condition=20,
        randomisation="illumination order randomised; power matched "
                      "across conditions to within 1%",
        blinding="analyst blind to condition labels",
        stopping_rule="fixed N; no extension",
        primary_outcome="specimen response above the unilluminated "
                        "thermal control",
        analysis="candidate vs detuned vs dark, preregistered",
        correction="Holm-Bonferroni across conditions",
        safety=("enclosed beam path, no exposed beam at eye height",
                "lowest practical laser class",
                "wavelength-appropriate eye protection",
                "unilluminated thermal control mandatory"),
    )


REGISTERED_EXPERIMENTS = {
    "CSPC-EXP-FOLD-18": low_frequency_fold_experiment,
    "CSPC-EXP-OPT-532": optical_detuning_experiment,
}


def compile_experiments() -> dict:
    """A24: the cross-domain compiler output — plans only."""
    plans = {k: f().to_dict() for k, f in REGISTERED_EXPERIMENTS.items()}
    for p in plans.values():
        require_non_physical(p["evidence_class"], "experiment plan")
        assert p["apparatus_status"] == "NOT BUILT"
    return {
        "n_experiments": len(plans),
        "experiments": plans,
        "apparatus_status": "NOT BUILT",
        "data_status": "NO DATA COLLECTED",
        "physical_status": "UNTESTED",
        "evidence_class": "ANALYTIC_MODEL",
        "claim_boundary":
            "These are preregistered plans. Every hypothesis in the "
            "programme remains UNTESTED. Controls are mandatory and an "
            "effect appearing equally at neighbouring frequencies is "
            "not a candidate effect.",
    }
