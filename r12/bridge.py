"""Typed cross-domain coupling certificates.

R11.1 refused every transfer between physical domains outright. That was
the right default and the wrong permanent rule: two systems really can be
coupled, and physics does it all the time -- piezoelectricity couples
strain to polarisation, magnetostriction couples magnetisation to strain,
optomechanics couples an optical mode to a mechanical one. A blanket
refusal cannot express any of that.

R12 replaces the blanket rule with two statements that must be held
together:

    NO_AUTOMATIC_EQUIVALENCE
    TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE

The default is still refusal. What changes is that a transfer can now be
*licensed* -- by a certificate that declares, in full, what the coupling
actually is. Nine declarations are required, and a certificate missing any
one of them is not a weak certificate, it is not a certificate:

1. source and target domains
2. state variables and their units
3. the coupling operator or constitutive law
4. the overlap or participation factor
5. detuning and damping
6. phase matching and symmetry
7. input-output energy accounting
8. uncertainty and a null model
9. a measurement capable of falsifying it

**A certificate is a licence to model, not evidence that the coupling
exists.** Requirement 9 is the one that keeps it honest: until the
falsifying measurement is actually performed, a fully-formed certificate
is still `ENGINEERING_CANDIDATE`, never `BENCH_MEASUREMENT`. In this
repository no such measurement exists, so every certificate here is
awaiting falsification.

This module supersedes but does not delete
:func:`r11.modemix.refuse_cross_domain_transfer`. That refusal remains
correct for an *uncertified* transfer, and is what you get by default.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class BridgeError(RuntimeError):
    """Raised on an uncertified transfer or an incomplete certificate."""


class Domain(Enum):
    """Physical domains a bridge may connect. Units differ across all."""

    ATOMIC_LATTICE_PHONON = "atomic_lattice_phonon"
    MACROSCOPIC_ELASTIC = "macroscopic_elastic"
    ELECTRICAL_BVD = "electrical_bvd"
    OPTICAL_CAVITY = "optical_cavity"
    MAGNETIC = "magnetic"
    THERMAL = "thermal"
    DYNAMIC_BOUNDARY = "dynamic_boundary"


#: The nine declarations. A certificate must carry every one.
REQUIRED_DECLARATIONS = (
    "source_target_domains",
    "state_variables_and_units",
    "coupling_operator_or_constitutive_law",
    "overlap_or_participation_factor",
    "detuning_and_damping",
    "phase_matching_and_symmetry",
    "energy_accounting",
    "uncertainty_and_null_model",
    "falsifying_measurement",
)


class CertificateStatus(Enum):
    INCOMPLETE = "INCOMPLETE"
    #: Fully declared, but the falsifying measurement has not been run.
    AWAITING_FALSIFICATION = "AWAITING_FALSIFICATION"
    #: Only reachable with real bench data, which this repo does not have.
    FALSIFIED = "FALSIFIED"
    SURVIVED_FALSIFICATION = "SURVIVED_FALSIFICATION"


@dataclass(frozen=True)
class CouplingCertificate:
    """A licence for ONE directed transfer between two domains.

    Every field below is a *declaration*, not a result. The certificate
    says what the coupling is claimed to be and how it could be shown
    wrong; it does not assert that it is real.
    """

    certificate_id: str
    source: Domain
    target: Domain
    state_variables: tuple[str, ...]
    units: tuple[str, ...]
    coupling_operator: str
    overlap_factor: float
    detuning: float
    damping: float
    phase_matching: str
    symmetry_allowed: bool
    energy_in: str
    energy_out: str
    uncertainty: str
    null_model: str
    falsifying_measurement: str
    measurement_performed: bool = False

    def __post_init__(self) -> None:
        if self.source is self.target:
            raise BridgeError(
                "a bridge connects two DIFFERENT domains; a same-domain "
                "transfer needs no certificate")
        if len(self.state_variables) != len(self.units):
            raise BridgeError(
                "every state variable must carry its own unit; a variable "
                "without a declared unit is how domains get equated by "
                "number alone")
        if not (0.0 <= self.overlap_factor <= 1.0):
            raise BridgeError("overlap/participation must lie in [0, 1]")
        if self.damping < 0:
            raise BridgeError("damping may not be negative")
        for name, value in (("coupling_operator", self.coupling_operator),
                            ("phase_matching", self.phase_matching),
                            ("energy_in", self.energy_in),
                            ("energy_out", self.energy_out),
                            ("uncertainty", self.uncertainty),
                            ("null_model", self.null_model),
                            ("falsifying_measurement",
                             self.falsifying_measurement)):
            if not str(value).strip():
                raise BridgeError(
                    f"declaration {name!r} is empty. A certificate missing "
                    f"any of the nine required declarations is not a weak "
                    f"certificate -- it is not a certificate.")

    # -- completeness ----------------------------------------------------
    def missing_declarations(self) -> tuple[str, ...]:
        """Which of the nine are absent. Empty means complete."""
        missing: list[str] = []
        if not self.state_variables:
            missing.append("state_variables_and_units")
        if not self.symmetry_allowed and not self.phase_matching:
            missing.append("phase_matching_and_symmetry")
        return tuple(missing)

    @property
    def status(self) -> CertificateStatus:
        if self.missing_declarations():
            return CertificateStatus.INCOMPLETE
        if not self.measurement_performed:
            return CertificateStatus.AWAITING_FALSIFICATION
        return CertificateStatus.SURVIVED_FALSIFICATION

    @property
    def claim_class(self) -> str:
        """A certificate is never BENCH_MEASUREMENT without a measurement."""
        if self.status is CertificateStatus.INCOMPLETE:
            return "UNSUPPORTED"
        if self.status is CertificateStatus.AWAITING_FALSIFICATION:
            return "ENGINEERING_CANDIDATE"
        return "BENCH_MEASUREMENT"

    @property
    def digest(self) -> str:
        parts = (self.certificate_id, self.source.value, self.target.value,
                 self.coupling_operator, self.phase_matching,
                 self.falsifying_measurement)
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()

    def transfer_efficiency(self) -> float:
        """A Lorentzian-style transfer weight from the declared numbers.

        Purely a consequence of the declarations: peak at zero detuning,
        scaled by overlap, broadened by damping. It is a model output,
        never a measurement.
        """
        d, g = float(self.detuning), float(self.damping)
        if g == 0.0 and d == 0.0:
            return float(self.overlap_factor)
        return float(self.overlap_factor) * (g * g) / (d * d + g * g)


# --- the rule ----------------------------------------------------------

#: Registry of certificates, keyed by (source, target).
_REGISTRY: dict[tuple[Domain, Domain], CouplingCertificate] = {}


def register(cert: CouplingCertificate) -> str:
    _REGISTRY[(cert.source, cert.target)] = cert
    return cert.digest


def certificate_for(source: Domain, target: Domain) -> CouplingCertificate | None:
    return _REGISTRY.get((source, target))


def transfer_allowed(source: Domain, target: Domain) -> bool:
    """True only if a COMPLETE certificate licenses this directed pair."""
    cert = certificate_for(source, target)
    return cert is not None and not cert.missing_declarations()


def refuse_uncertified_transfer(source: Domain, target: Domain) -> None:
    """The default. No certificate, no transfer.

    This is the R11.1 rule, preserved: `NO_AUTOMATIC_EQUIVALENCE`. What
    R12 adds is a way to lift it deliberately, not a way to skip it.
    """
    if source is target:
        return
    if not transfer_allowed(source, target):
        raise BridgeError(
            f"refused: no complete coupling certificate licenses "
            f"{source.value!r} -> {target.value!r}. NO_AUTOMATIC_EQUIVALENCE "
            f"-- shared mathematics is not shared mechanism, and a transfer "
            f"is permitted only with an explicit certificate declaring all "
            f"nine required items.")


def refuse_certificate_as_evidence(cert: CouplingCertificate) -> None:
    """A certificate licenses modelling; it does not evidence coupling."""
    if not cert.measurement_performed:
        raise BridgeError(
            f"refused: certificate {cert.certificate_id!r} is complete but "
            f"its falsifying measurement has not been performed. It is an "
            f"ENGINEERING_CANDIDATE licensing a model, not evidence that "
            f"the coupling exists. Required: "
            f"{cert.falsifying_measurement!r}.")


def refuse_reverse_direction(cert: CouplingCertificate) -> None:
    """A certificate licenses ONE direction. Reciprocity is a claim."""
    raise BridgeError(
        f"refused: certificate {cert.certificate_id!r} licenses "
        f"{cert.source.value!r} -> {cert.target.value!r} only. The reverse "
        f"transfer needs its own certificate; reciprocity is a physical "
        f"claim about the medium, not a property of the paperwork.")


def refuse_chained_transfer(*_certs: CouplingCertificate) -> None:
    """A -> B and B -> C do not compose into a licensed A -> C."""
    raise BridgeError(
        "refused: certificates do not compose. A licensed A->B and a "
        "licensed B->C do not license A->C; the composite has its own "
        "overlap, detuning, phase matching and energy budget, and needs "
        "its own certificate and its own falsifying measurement.")


#: No falsifying measurement can be performed in this environment.
MEASUREMENT_STATUS = "BLOCKED_MISSING_DATA"


def bridge_report() -> dict:
    return {
        "what_this_is": (
            "typed cross-domain coupling certificates: the R12 replacement "
            "for R11.1's categorical transfer refusal"),
        "rule": ["NO_AUTOMATIC_EQUIVALENCE",
                 "TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE"],
        "required_declarations": list(REQUIRED_DECLARATIONS),
        "registered_certificates": len(_REGISTRY),
        "measurement_status": MEASUREMENT_STATUS,
        "supersedes": ("r11.modemix.refuse_cross_domain_transfer remains "
                       "correct for an uncertified transfer and is the "
                       "default; it is superseded, not deleted"),
        "claim_class": "ENGINEERING_CANDIDATE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "COUPLING_CERTIFICATES_TYPED_AWAITING_FALSIFICATION",
        "what_this_does_not_say": (
            "A certificate does not say the coupling is real. It says what "
            "is claimed, how strong it is claimed to be, and what "
            "measurement would show it false. Every certificate here is "
            "AWAITING_FALSIFICATION because no bench exists, so none has "
            "risen above ENGINEERING_CANDIDATE. Certificates license one "
            "direction, do not compose, and never become evidence by being "
            "well-formed."),
    }
