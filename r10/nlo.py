"""P10 — second-harmonic generation in quartz, and why bulk quartz
cannot be phase-matched for it.

Quartz is trigonal, crystal class **32** (point group ``D3``), and it is
**non-centrosymmetric**. That symmetry is not a detail: it is exactly the
condition a crystal must satisfy to have a non-vanishing second-order
susceptibility, so quartz genuinely has one. It was the very first
material in which optical second-harmonic generation (SHG) was observed
-- Franken, Hill, Peters and Weinreich, *Phys. Rev. Lett.* **7**, 118
(1961), doubling a ruby laser through a quartz plate. SHG in quartz is
real, and it is old. This module does not dispute any of that.

What this module refuses is the next step that the numbers do **not**
support: that bulk quartz is a *useful* frequency doubler. Two honest
facts block it.

**The nonlinearity is small.** Quartz's dominant coefficient is
``d11 ~ 0.3 pm/V`` (:data:`D11_PM_PER_V`) -- roughly an order of
magnitude below KDP and two below common engineered doublers. The
material has a nonlinearity; it is just a weak one.

**And it cannot be phase-matched.** SHG is efficient only when the
fundamental and the second harmonic stay in step, i.e. when the phase
mismatch ``Delta_k = (4*pi/lambda)*(n(2w) - n(w))`` is driven to zero.
Normal dispersion makes ``n(2w) > n(w)``, so ``Delta_k != 0`` and the
harmonic reradiated over a coherence length
``L_c = lambda / (4|n(2w)-n(w)|)`` interferes with itself; for quartz in
the visible ``|n(2w)-n(w)| ~ 0.01-0.02``, giving ``L_c`` of only tens of
microns and a vanishing conversion without quasi-phase-matching. The
standard escape -- **birefringent phase matching** -- uses the crystal's
own birefringence to cancel the dispersion, but that needs the
birefringence to be *at least as large* as the dispersion to compensate.
Quartz's birefringence is only ``n_e - n_o ~ +0.009`` at 589 nm, smaller
than the dispersion it would have to offset, so the cancellation cannot
happen. :func:`birefringent_phase_matchable` returns ``False`` for
quartz's numbers, and the verdict is
``NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ``.

Nothing here is measured. The coefficients and indices are literature
values; the arithmetic is derived. No crystal was cut, no beam was
doubled, and no efficiency is claimed. The point of the module is the
honest negative: a real but weak nonlinearity in a crystal that bulk
optics cannot phase-match.
"""

from __future__ import annotations

import math
from enum import Enum

# --- provenance for every literature constant --------------------------

#: Dominant second-order coefficient of alpha-quartz, ~0.3 pm/V. A small
#: nonlinearity, quoted widely (e.g. against the standard KDP scale).
D11_PM_PER_V = 0.3

#: Birefringence of quartz at the sodium D line (589 nm): positive
#: uniaxial, n_e - n_o ~ +0.009. Real, and too small to phase-match SHG.
QUARTZ_BIREFRINGENCE_589NM = 0.009

#: Representative visible-band dispersion for quartz across a
#: fundamental/second-harmonic pair: |n(2w) - n(w)| ~ 0.013. Larger than
#: the birefringence above -- which is why the cancellation fails.
QUARTZ_DISPERSION_VISIBLE = 0.013

PROVENANCE = {
    "D11_PM_PER_V": (
        "~0.3 pm/V, the dominant d11 of alpha-quartz; a small "
        "second-order coefficient quoted throughout the NLO literature"),
    "QUARTZ_BIREFRINGENCE_589NM": (
        "n_e - n_o ~ +0.009 at 589 nm; quartz is a weak positive "
        "uniaxial crystal"),
    "QUARTZ_DISPERSION_VISIBLE": (
        "|n(2w) - n(w)| ~ 0.01-0.02 across a visible SHG pair under "
        "normal dispersion; ~0.013 taken as representative"),
    "SHG_FIRST_OBSERVED": (
        "Franken, Hill, Peters & Weinreich, Phys. Rev. Lett. 7, 118 "
        "(1961): first SHG, a ruby laser doubled in a quartz plate"),
}

PRIMARY_SOURCES = (
    "Franken, P. A.; Hill, A. E.; Peters, C. W.; Weinreich, G. "
    "'Generation of Optical Harmonics.' Phys. Rev. Lett. 7, 118 (1961).",
    "Boyd, R. W. 'Nonlinear Optics.' (symmetry of the d-tensor; class "
    "32 nonzero elements; birefringent phase matching).",
    "Nye, J. F. 'Physical Properties of Crystals.' (point group 32 = D3 "
    "and the piezoelectric/second-order tensor form).",
)

VERDICTS = (
    "NLO_MODEL_ONLY",
    "NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)


class NloError(RuntimeError):
    """Raised when the module is asked to claim an efficient or usable
    SHG process from bulk quartz that the physics does not support."""


# --- (1) phase mismatch and coherence length ---------------------------

def phase_mismatch(n_w: float, n_2w: float,
                   lambda_fundamental_m: float) -> float:
    """Wavevector mismatch for collinear SHG, ``Delta_k`` in rad/m.

    ``Delta_k = k(2w) - 2 k(w) = (4*pi/lambda) * (n(2w) - n(w))`` with
    ``lambda`` the *fundamental* free-space wavelength. Under normal
    dispersion ``n(2w) > n(w)``, so ``Delta_k > 0`` and the harmonic
    slips out of step with the polarization that drives it.
    """
    if lambda_fundamental_m <= 0:
        raise ValueError("wavelength must be positive")
    return (4.0 * math.pi / lambda_fundamental_m) * (n_2w - n_w)


def coherence_length_m(n_w: float, n_2w: float,
                       lambda_fundamental_m: float) -> float:
    """Coherence length ``L_c = pi / |Delta_k| = lambda / (4|n2w-nw|)``.

    The distance over which the harmonic stays within pi of phase with
    its drive; beyond it the contribution reverses and cancels. Larger
    ``|n(2w)-n(w)|`` gives a *shorter* ``L_c`` -- the power relation the
    tests pin down. Returns ``inf`` at perfect phase matching.
    """
    if lambda_fundamental_m <= 0:
        raise ValueError("wavelength must be positive")
    dn = abs(n_2w - n_w)
    if dn == 0.0:
        return math.inf
    return lambda_fundamental_m / (4.0 * dn)


# --- (2) the honest negative: birefringent phase matching --------------

def required_birefringence(dispersion_delta_n: float) -> float:
    """Birefringence needed to cancel a given dispersion for SHG.

    Birefringent phase matching works by letting the fundamental and
    harmonic travel on different polarization branches whose index split
    (the birefringence) offsets the dispersive split. To reach
    ``Delta_k = 0`` the available birefringence must be at least the
    dispersion it has to compensate.
    """
    return abs(dispersion_delta_n)


def birefringent_phase_matchable(delta_n_birefringence: float,
                                 dispersion_delta_n: float) -> bool:
    """Can birefringence offset the dispersion for SHG? ``True`` only if
    the birefringence is at least the dispersion.

    For quartz (``birefringence ~ 0.009`` vs ``dispersion ~ 0.013``) this
    is ``False`` -- the crystal cannot be phase-matched in bulk. For a
    hypothetical crystal whose birefringence exceeds its dispersion it is
    ``True``. This is the module's central result.
    """
    return abs(delta_n_birefringence) >= required_birefringence(
        dispersion_delta_n)


def quartz_phase_match_status() -> dict:
    """Apply the test to quartz's own literature numbers."""
    matchable = birefringent_phase_matchable(
        QUARTZ_BIREFRINGENCE_589NM, QUARTZ_DISPERSION_VISIBLE)
    return {
        "birefringence": QUARTZ_BIREFRINGENCE_589NM,
        "dispersion": QUARTZ_DISPERSION_VISIBLE,
        "required_birefringence": required_birefringence(
            QUARTZ_DISPERSION_VISIBLE),
        "birefringent_phase_matchable": matchable,
        "shortfall": QUARTZ_DISPERSION_VISIBLE - QUARTZ_BIREFRINGENCE_589NM,
        "verdict": "NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ",
        "why": (
            "quartz's birefringence (~0.009 at 589 nm) is smaller than "
            "the dispersion it would have to cancel (~0.013), so no cut "
            "of bulk quartz brings Delta_k to zero for SHG in the "
            "visible/near-IR"),
    }


# --- (3) the class-32 second-order tensor ------------------------------

class CrystalClass(Enum):
    """The two symmetry cases that matter here."""

    CLASS_32 = "32"                   # D3, non-centrosymmetric (quartz)
    CENTROSYMMETRIC = "centro"        # inversion symmetry: all d = 0


#: Non-zero elements of the second-order d-tensor for point group 32.
#: In contracted (Voigt) notation quartz's independent coefficients are
#: d11 and d14, with the symmetry-forced relations d12 = -d11 and
#: d26 = -d11 (and d25 = -d14). d14 is small; d11 dominates.
CLASS_32_NONZERO = ("d11", "d12", "d14", "d25", "d26")


def class_32_d_tensor(d11: float = D11_PM_PER_V,
                      d14: float = 0.0) -> dict[str, float]:
    """Contracted d-tensor for crystal class 32, from its two independent
    coefficients. Encodes ``d12 = -d11``, ``d26 = -d11``, ``d25 = -d14``;
    every element not listed is zero by symmetry.
    """
    return {
        "d11": d11,
        "d12": -d11,
        "d26": -d11,
        "d14": d14,
        "d25": -d14,
    }


def centrosymmetric_d_tensor() -> dict[str, float]:
    """Every second-order coefficient of a centrosymmetric medium is
    identically zero: inversion symmetry forbids SHG. This is the control
    against which quartz's non-zero tensor is meaningful."""
    return {name: 0.0 for name in CLASS_32_NONZERO}


def second_harmonic_allowed(crystal_class: CrystalClass) -> bool:
    """SHG (a second-order effect) is allowed iff the medium lacks
    inversion symmetry. Class 32 -> ``True``; centrosymmetric -> ``False``.
    """
    return crystal_class is not CrystalClass.CENTROSYMMETRIC


# --- (4) the refusal ---------------------------------------------------

def refuse_efficient_shg_claim(context: str = "") -> None:
    """Refuse any claim of efficient or usable SHG from bulk quartz.

    Quartz has a real second-order nonlinearity, but it is weak
    (``d11 ~ 0.3 pm/V``) and -- decisively -- bulk quartz cannot be
    birefringently phase-matched for SHG, so the harmonic never
    accumulates over more than a coherence length of tens of microns.
    The process is a textbook *weak, non-phase-matched* one. Claiming an
    efficient doubler here is inventing an efficiency the numbers deny.
    """
    tail = f" ({context})" if context else ""
    raise NloError(
        "bulk quartz cannot be claimed as an efficient or usable "
        "second-harmonic generator" + tail + ": its dominant "
        "coefficient is only ~0.3 pm/V and its birefringence (~0.009) is "
        "too small to phase-match against the dispersion (~0.013), so the "
        "harmonic cancels every coherence length (~tens of microns). SHG "
        "in quartz is real but weak and non-phase-matched; efficiency is "
        "NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ.")


# --- report ------------------------------------------------------------

def nlo_report() -> dict:
    pm = quartz_phase_match_status()
    return {
        "what_this_is": (
            "an honest model of second-harmonic generation in crystalline "
            "quartz: a real but weak second-order nonlinearity in a "
            "non-centrosymmetric crystal (class 32) that bulk optics "
            "cannot phase-match"),
        "the_real_facts": [
            "quartz is class 32 (D3), non-centrosymmetric, so it has a "
            "non-zero second-order susceptibility",
            "SHG was first observed in quartz (Franken et al. 1961)",
            "its dominant coefficient d11 is small, ~0.3 pm/V",
        ],
        "the_honest_negative": (
            "bulk quartz is NOT birefringently phase-matchable for SHG: "
            "its birefringence (~0.009) is smaller than the dispersion "
            "(~0.013) it would have to cancel, so Delta_k never reaches "
            "zero and the coherence length is only tens of microns"),
        "quartz_phase_match": pm,
        "d11_pm_per_v": D11_PM_PER_V,
        "class_32_nonzero_elements": list(CLASS_32_NONZERO),
        "provenance": PROVENANCE,
        "primary_sources": list(PRIMARY_SOURCES),
        "verdict": "NLO_MODEL_ONLY",
        "phase_matching_verdict": "NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ",
        "verdicts": list(VERDICTS),
        "evidence_class": ["DERIVED_MATHEMATICS", "CONVENTIONAL_LITERATURE"],
        "hardware_status": "DEFERRED — no crystal cut, no beam doubled",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say quartz makes a useful or efficient frequency "
            "doubler, that any SHG efficiency was measured, or that a "
            "crystal was cut or a beam doubled here. The nonlinearity is "
            "real but weak, the process is non-phase-matched in bulk, and "
            "the coefficients and indices are literature values, not "
            "measurements. The negative -- NOT_PHASE_MATCHABLE_IN_BULK_"
            "QUARTZ -- is the point, not a caveat."),
    }
