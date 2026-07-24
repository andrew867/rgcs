"""P10 — piezoelectric coupling reduced to a Butterworth-Van Dyke circuit.

Piezoelectricity is the one place where a mechanical domain and an
electrical domain genuinely couple: a strained polar lattice separates
bound charge, so a stress produces a voltage and a field produces a
strain. The linear constitutive relations state it as a pair,

    T = c^E S - e^t E        (stress from strain and field)
    D = e S + eps^S E        (electric displacement from strain and field)

with ``c^E`` the stiffness at constant field, ``e`` the piezoelectric
stress constant, and ``eps^S`` the permittivity at constant strain. The
strength of the coupling is the electromechanical coupling factor
``k^2 = e^2 / (c^E eps^S)``, which is bounded in ``[0, 1)`` for any passive
material and is exactly zero when ``e`` is zero — no polar term, no bridge.

Near a mechanical resonance the whole electromechanical response of a
resonator collapses onto four numbers: a motional branch ``R``, ``L``,
``C`` in series (the mechanical resonance seen from the terminals) in
parallel with the static electrode capacitance ``C0``. That is the
**Butterworth-Van Dyke** equivalent circuit. It has a series resonance
``f_s = 1/(2*pi*sqrt(L C))`` where the motional branch impedance is
smallest, and a parallel resonance ``f_p = f_s sqrt(1 + C/C0)`` where the
motional and static branches cancel and the impedance is largest. The
separation ``f_p > f_s`` is set entirely by ``C/C0``, and ``C/C0`` is a
function of ``k^2`` — the coupling factor and the resonance split are the
same physics measured two ways. :func:`bvd_impedance` exhibits the minimum
near ``f_s`` and the maximum near ``f_p`` on a frequency sweep.

**The bridge requires a certificate, and a certificate is not evidence.**
Carrying a number from the mechanical resonance to the electrical
terminals is a cross-domain transfer, and R12 licenses it only with a
:class:`~r12.bridge.CouplingCertificate` declaring all nine items,
including a measurement that could falsify it — here, measuring ``f_s``,
``f_p`` and the motional parameters on a real crystal.
:func:`certificate` returns that certificate; it is ``ENGINEERING_CANDIDATE``
and ``AWAITING_FALSIFICATION`` because no such measurement exists in this
environment. :func:`refuse_bvd_as_measured_crystal` refuses to read the
BVD numbers as a measured device, and
:func:`refuse_coupling_without_certificate` refuses the transfer outright
when no certificate licenses it.

Nothing here is measured. The material constants are conventional
literature placeholders, no crystal is cut or driven, and every impedance
is arithmetic on a declared model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r12 import bridge as B

# --- verdict, claim classes ----------------------------------------------

DEFAULT_VERDICT = "PIEZO_TO_BVD_CERTIFICATE_ENGINEERING_CANDIDATE"

#: A BVD circuit built from a declared coupling and geometry is an
#: engineering candidate: it is a licensed model of a resonator, not a
#: measured device.
CLAIM_CLASS = "ENGINEERING_CANDIDATE"

#: The material constants are not fitted or measured here.
CONSTANTS_PROVENANCE = "CONVENTIONAL_LITERATURE"

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class PiezoBridgeError(RuntimeError):
    """Raised when a piezo-to-BVD claim exceeds what the model licenses.

    Covers the structural refusals (non-positive material constants or
    geometry, an unphysical coupling ``k^2 >= 1``) and the two load-bearing
    governance refusals :func:`refuse_bvd_as_measured_crystal` and
    :func:`refuse_coupling_without_certificate`.
    """


def _positive(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise PiezoBridgeError(f"{what} must be finite")
    if x <= 0.0:
        raise PiezoBridgeError(f"{what} must be positive")
    return x


# --- (1) the linear constitutive constants -------------------------------

@dataclass(frozen=True)
class PiezoConstants:
    """The three reduced constants of a linear piezoelectric coupling.

    ``c_E`` is the elastic stiffness at constant electric field (Pa),
    ``e`` the piezoelectric stress constant (C/m^2), and ``eps_S`` the
    permittivity at constant strain (F/m). The default constructor allows
    ``e == 0`` (a non-piezoelectric material, a legitimate null), and the
    magnitudes are ``CONVENTIONAL_LITERATURE`` placeholders, not a fitted
    or measured set.
    """

    c_E: float
    e: float
    eps_S: float
    provenance: str = CONSTANTS_PROVENANCE

    def __post_init__(self) -> None:
        _positive(self.c_E, "the stiffness c_E")
        _positive(self.eps_S, "the permittivity eps_S")
        if not math.isfinite(float(self.e)):
            raise PiezoBridgeError("the piezoelectric constant e must be finite")

    @classmethod
    def alpha_quartz(cls) -> "PiezoConstants":
        """A conventional-literature placeholder for alpha-quartz.

        Reduced thickness-mode magnitudes chosen so that ``k^2`` lands in
        the physical few-percent range typical of quartz. Not a measurement.
        """
        return cls(c_E=2.947e10, e=0.171, eps_S=3.99e-11,
                   provenance=CONSTANTS_PROVENANCE)


# --- (2) the electromechanical coupling factor ---------------------------

def coupling_factor(constants: PiezoConstants) -> float:
    """``k^2 = e^2 / (c^E eps^S)``, the electromechanical coupling factor.

    It measures the fraction of energy the polar term carries between the
    mechanical and electrical domains. For any passive material it lies in
    ``[0, 1)``; ``e == 0`` gives exactly zero, which is the statement that a
    non-polar lattice has no piezoelectric bridge at all. A value ``>= 1``
    is unphysical for a passive medium and is refused rather than returned.
    """
    if not isinstance(constants, PiezoConstants):
        raise PiezoBridgeError("coupling_factor needs PiezoConstants")
    k2 = float(constants.e) ** 2 / (float(constants.c_E) * float(constants.eps_S))
    if k2 < 0.0:
        raise PiezoBridgeError("k^2 came out negative; check the constants")
    if k2 >= 1.0:
        raise PiezoBridgeError(
            f"k^2 = {k2:g} >= 1 is unphysical for a passive piezoelectric: "
            f"e^2 cannot exceed c^E eps^S, or the coupling would return more "
            f"energy than is stored")
    return k2


# --- (3) the Butterworth-Van Dyke equivalent circuit ---------------------

@dataclass(frozen=True)
class BVDCircuit:
    """A Butterworth-Van Dyke equivalent circuit: motional R, L, C || C0.

    ``R``, ``L``, ``C`` are the motional (series) branch and ``C0`` is the
    static electrode capacitance. Every value is a model output derived
    from a declared coupling and geometry, never a measured component.
    """

    R: float
    L: float
    C: float
    C0: float

    def __post_init__(self) -> None:
        _positive(self.R, "the motional resistance R")
        _positive(self.L, "the motional inductance L")
        _positive(self.C, "the motional capacitance C")
        _positive(self.C0, "the static capacitance C0")

    @property
    def series_resonance_hz(self) -> float:
        """``f_s = 1/(2*pi*sqrt(L C))``: the motional-branch resonance."""
        return 1.0 / (2.0 * math.pi * math.sqrt(self.L * self.C))

    @property
    def parallel_resonance_hz(self) -> float:
        """``f_p = f_s sqrt(1 + C/C0)``: the antiresonance, above ``f_s``."""
        return self.series_resonance_hz * math.sqrt(1.0 + self.C / self.C0)

    @property
    def capacitance_ratio(self) -> float:
        """``C/C0``, which sets the resonance split and tracks ``k^2``."""
        return self.C / self.C0

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.R, self.L, self.C, self.C0)


def bvd_from_piezo(constants: PiezoConstants, thickness_m: float,
                   area_m2: float, density: float,
                   quality_factor: float = 1e4) -> BVDCircuit:
    """Reduce a thickness-mode piezo resonator to its BVD circuit.

    The static capacitance is ``C0 = eps^S A / t``. The fundamental
    thickness resonance is ``f_s = (1/2t) sqrt(c^E/rho)``. The motional-to-
    static capacitance ratio follows from the coupling factor through the
    standard fundamental-mode relation ``k^2 = (pi^2/8) (C/(C0+C))``, so
    ``C/C0 = q/(1-q)`` with ``q = 8 k^2/pi^2``; the motional inductance is
    fixed by ``f_s`` and ``C``, and the resistance by the quality factor.
    All four numbers are model outputs of a declared coupling and geometry.
    """
    t = _positive(thickness_m, "the plate thickness")
    A = _positive(area_m2, "the electrode area")
    rho = _positive(density, "the density")
    Q = _positive(quality_factor, "the quality factor")

    k2 = coupling_factor(constants)
    c0 = float(constants.eps_S) * A / t
    f_s = math.sqrt(float(constants.c_E) / rho) / (2.0 * t)

    q = 8.0 * k2 / (math.pi ** 2)
    if q >= 1.0:
        raise PiezoBridgeError(
            "the fundamental-mode capacitance ratio diverges; k^2 is too "
            "large for the pi^2/8 reduction")
    ratio = q / (1.0 - q)          # C/C0
    c1 = ratio * c0
    if c1 <= 0.0:
        # e == 0: no motional branch. A degenerate BVD is refused because a
        # resonator with no coupling has no series-resonance channel.
        raise PiezoBridgeError(
            "the coupling is zero, so there is no motional branch and no "
            "BVD resonator; a non-piezoelectric plate is just C0")
    omega_s = 2.0 * math.pi * f_s
    l1 = 1.0 / (omega_s ** 2 * c1)
    r1 = omega_s * l1 / Q
    return BVDCircuit(R=r1, L=l1, C=c1, C0=c0)


def bvd_impedance(circuit: BVDCircuit, f_hz) -> np.ndarray:
    """The complex terminal impedance ``Z(f)`` of a BVD circuit.

    ``Z = Z_m || Z_c0`` with the motional branch
    ``Z_m = R + i w L + 1/(i w C)`` and the static branch
    ``Z_c0 = 1/(i w C0)``. ``|Z|`` dips to near ``R`` at the series
    resonance ``f_s`` and rises to a maximum at the parallel resonance
    ``f_p``; a frequency sweep exhibits both, which is the model output the
    tests probe.
    """
    w = 2.0 * np.pi * np.asarray(f_hz, dtype=float)
    if np.any(w <= 0.0):
        raise PiezoBridgeError("BVD impedance needs positive frequencies")
    z_m = circuit.R + 1j * w * circuit.L + 1.0 / (1j * w * circuit.C)
    z_c0 = 1.0 / (1j * w * circuit.C0)
    return z_m * z_c0 / (z_m + z_c0)


# --- (4) the coupling certificate (R12) ----------------------------------

#: The identifier used for the mechanical -> electrical bridge certificate.
CERTIFICATE_ID = "piezo_mechanical_to_electrical_bvd"


def certificate(constants: PiezoConstants | None = None) -> B.CouplingCertificate:
    """The R12 coupling certificate licensing MECHANICAL -> ELECTRICAL.

    Declares all nine required items, including the falsifying measurement:
    measure ``f_s``, ``f_p`` and the motional ``R``, ``L``, ``C``, ``C0`` on
    a real crystal and check them against the BVD reduction. Because no such
    measurement exists here, ``measurement_performed`` is ``False`` and the
    certificate is ``AWAITING_FALSIFICATION`` with claim class
    ``ENGINEERING_CANDIDATE``. It licenses one direction only.
    """
    c = constants if constants is not None else PiezoConstants.alpha_quartz()
    k2 = coupling_factor(c)
    return B.CouplingCertificate(
        certificate_id=CERTIFICATE_ID,
        source=B.Domain.MACROSCOPIC_ELASTIC,
        target=B.Domain.ELECTRICAL_BVD,
        state_variables=("strain S", "electric displacement D"),
        units=("dimensionless", "C/m^2"),
        coupling_operator=(
            "linear piezoelectric law T = c^E S - e^t E, D = e S + eps^S E, "
            "reduced near resonance to a Butterworth-Van Dyke motional "
            "branch R,L,C in parallel with the static capacitance C0"),
        overlap_factor=float(min(max(k2, 0.0), 1.0)),
        detuning=0.0,
        damping=1.0,
        phase_matching="none required; quasi-static electromechanical coupling",
        symmetry_allowed=True,
        energy_in="mechanical strain energy in the vibrating plate",
        energy_out="electrical energy at the resonator terminals",
        uncertainty=(
            "material constants are CONVENTIONAL_LITERATURE placeholders; "
            "k^2, C/C0 and f_p/f_s carry the corresponding model uncertainty"),
        null_model=(
            "a centrosymmetric (non-polar) plate has e = 0, hence k^2 = 0, "
            "no motional branch, and a flat capacitive |Z(f)| with no "
            "series or parallel resonance"),
        falsifying_measurement=(
            "cut and electrode a real crystal, sweep its terminal impedance, "
            "and measure f_s, f_p and the motional R, L, C, C0; the "
            "certificate is falsified if the measured f_p/f_s and coupling "
            "do not match the BVD reduction of the declared constants"),
        measurement_performed=False,
    )


def coupling_factor_from_resonances(f_s: float, f_p: float) -> float:
    """The IEEE effective coupling ``(f_p^2 - f_s^2)/f_p^2`` from resonances.

    This is the terminal-measurable partner of :func:`coupling_factor`: the
    resonance split ``f_p > f_s`` encodes the same coupling that ``e``
    carries in the constitutive law. It is a model relation here, not a
    reading of a measured pair.
    """
    fs = _positive(f_s, "the series resonance f_s")
    fp = _positive(f_p, "the parallel resonance f_p")
    if fp <= fs:
        raise PiezoBridgeError(
            "the parallel resonance must exceed the series resonance; "
            "f_p <= f_s has no positive coupling")
    return (fp ** 2 - fs ** 2) / fp ** 2


# --- (5) the load-bearing refusals ---------------------------------------

def refuse_bvd_as_measured_crystal(
        quantity: str = "a BVD parameter") -> None:
    """The BVD numbers are model outputs, not a measured device. Raises.

    ``R``, ``L``, ``C``, ``C0``, ``f_s`` and ``f_p`` here are computed from
    a declared coupling factor and a declared geometry. No crystal was cut,
    electroded, mounted or swept; no impedance analyzer read anything.
    Reading the BVD reduction as a measured resonator is exactly the
    promotion this refuses.
    """
    raise PiezoBridgeError(
        f"refused: {quantity!r} is a Butterworth-Van Dyke MODEL output, not "
        f"a measured crystal. The motional R, L, C, the static C0, and the "
        f"resonances f_s, f_p are computed from CONVENTIONAL_LITERATURE "
        f"constants and a declared geometry; no resonator was cut, "
        f"electroded, mounted or swept, and no impedance was recorded. "
        f"{PHYSICAL_VALIDATION}.")


def refuse_coupling_without_certificate(
        source: B.Domain = B.Domain.MACROSCOPIC_ELASTIC,
        target: B.Domain = B.Domain.ELECTRICAL_BVD) -> None:
    """Refuse the mechanical -> electrical transfer with no certificate.

    Carrying a number from the mechanical resonance to the electrical
    terminals is a cross-domain transfer. R12 permits it only under a
    complete :class:`~r12.bridge.CouplingCertificate`; without one
    registered, the transfer is refused by the default rule
    ``NO_AUTOMATIC_EQUIVALENCE``. Even with the certificate present the
    transfer stays an ``ENGINEERING_CANDIDATE`` until its falsifying
    measurement is performed, which cannot happen here.
    """
    # The R12 default rule is the ground truth; surface it, then restate the
    # refusal in this module's own exception type so callers see one class.
    try:
        B.refuse_uncertified_transfer(source, target)
    except B.BridgeError as exc:
        raise PiezoBridgeError(str(exc)) from exc
    raise PiezoBridgeError(
        f"refused: the piezoelectric mechanical -> electrical bridge from "
        f"{source.value!r} to {target.value!r} carries a number across "
        f"domains, and a certificate is a LICENCE TO MODEL, not evidence "
        f"the coupling is real. Its falsifying measurement -- measuring "
        f"f_s, f_p and the motional parameters on a real crystal -- has not "
        f"been performed, so the bridge is AWAITING_FALSIFICATION and stays "
        f"an ENGINEERING_CANDIDATE. {PHYSICAL_VALIDATION}.")


# --- (6) the report ------------------------------------------------------

def piezobridge_report() -> dict:
    return {
        "what_this_is": (
            "the piezoelectric electromechanical coupling and its reduction "
            "to a Butterworth-Van Dyke equivalent circuit: the mechanical "
            "<-> electrical bridge, gated by an R12 coupling certificate"),
        "constitutive_law": (
            "T = c^E S - e^t E ; D = e S + eps^S E, with coupling factor "
            "k^2 = e^2/(c^E eps^S) in [0, 1), zero when e = 0"),
        "bvd": (
            "motional R, L, C in series (the mechanical resonance seen from "
            "the terminals) in parallel with the static capacitance C0; "
            "f_s = 1/(2 pi sqrt(L C)), f_p = f_s sqrt(1 + C/C0) > f_s, and "
            "C/C0 tracks k^2 so the resonance split and the coupling factor "
            "are the same physics measured two ways"),
        "constants_provenance": CONSTANTS_PROVENANCE,
        "certificate": {
            "id": CERTIFICATE_ID,
            "source": B.Domain.MACROSCOPIC_ELASTIC.value,
            "target": B.Domain.ELECTRICAL_BVD.value,
            "required_declarations": len(B.REQUIRED_DECLARATIONS),
            "status": B.CertificateStatus.AWAITING_FALSIFICATION.value,
            "claim_class": CLAIM_CLASS,
        },
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any crystal exists, was cut, electroded, "
            "mounted or swept, or that any resonance, motional parameter or "
            "impedance was measured. The material constants are "
            "CONVENTIONAL_LITERATURE placeholders. The BVD numbers are model "
            "outputs of a declared coupling and geometry, and the "
            "mechanical -> electrical bridge is licensed by a certificate "
            "that is AWAITING_FALSIFICATION -- a licence to model, never "
            "evidence that the coupling is real, because its falsifying "
            "measurement cannot be performed here."),
    }
