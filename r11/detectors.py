"""P11 — the detector matrix: every transducer has a sensitivity domain.

A detector is not a general-purpose window onto the world. It is a
**transducer**: one physical quantity in, one electrical quantity out,
through one mechanism. A piezoelectric element converts strain into
charge because a strained lattice separates bound charge. A Hall element
converts magnetic flux density into a transverse voltage because moving
carriers feel a Lorentz force. A CCD converts photons into stored charge
because a photon lifts an electron across the silicon gap. Each of those
mechanisms answers exactly one question, and it answers that question
over a bounded band, above a bounded amplitude floor.

That bounded region is the detector's **sensitivity domain**: the
measurand it actually transduces, the frequency range over which its
mechanism responds, the amplitude below which its own noise dominates,
and the explicit set of observables it couples to. Every capability in
this module therefore carries two halves. ``couples_to`` is the half
that is usually quoted. ``cannot_detect`` is the honest half, and it is
required to be non-empty: a transducer that is claimed to detect
everything has had its mechanism removed from the description.

**A detector used outside its sensitivity domain produces an artifact,
not a measurement.** The reading still exists -- there is always a
number -- but the number is the response of some *other* mechanism:
pickup, drift, thermal expansion, a mundane optical consequence of
something else. Reading it as the intended measurand is a category
error, and the error is invisible if the domain was never written down.
:func:`refuse_out_of_domain` is the general guard, and it fires for any
pairing outside ``couples_to`` -- a Hall probe asked for an acoustic
field, a CCD asked for a magnetic field, an interferometer asked for
strain inside a solid.

**The headline refusal: a CCD cannot detect phonons.** A CCD transduces
*integrated* optical intensity: photons arriving anywhere within an
exposure are summed into one charge packet per pixel, and the frame is
read out at rates of order hertz to kilohertz. There is no mechanical
port. Lattice vibration does not deposit charge in a pixel well; only
photons do. Two consequences follow and both are load-bearing. First,
the coupling is absent: a CCD has no phonon channel at all, so no
exposure, however long, integrates one into existence. Second, even the
optical route is time-averaged: an image can at best show a *smeared or
static optical consequence* of motion -- a blurred fringe, a shifted
speckle, a changed intensity -- which is a statement about light over
the exposure, not a detection of a lattice mode. Asking a kilohertz
frame-rate integrator to resolve a kilohertz-scale waveform per cycle
fails on the same physics from the other direction, which is what
:func:`bandwidth_ok` and :func:`refuse_out_of_band` enforce.
:func:`refuse_ccd_phonon_claim` always raises, and the module's verdict
is ``CCD_PHONON_DETECTION_REFUSED``.

Nothing here is measured. Every capability is a conventional,
order-of-magnitude ANALYTIC_MODEL description of a class of transducer,
not a datasheet for any device and not a calibration of any instrument.
No detector is built, powered, pointed at anything, or read out.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DEFAULT_VERDICT = "CCD_PHONON_DETECTION_REFUSED"
EVIDENCE_CLASS = "ANALYTIC_MODEL"
MODEL_ONLY = "MODEL_ONLY"


class DetectorError(RuntimeError):
    """Raised when a detector is used outside its sensitivity domain."""


# --- what can be asked for ----------------------------------------------

class Observable(Enum):
    """A physical quantity a detector might be asked to report.

    These are *questions*, not devices. A detector answers the question
    its mechanism can answer and no other.
    """

    STRAIN = "strain"
    ACOUSTIC = "acoustic"
    PHONON = "phonon"
    DISPLACEMENT = "displacement"
    MAGNETIC_FIELD = "magnetic_field"
    OPTICAL_INTENSITY = "optical_intensity"
    OPTICAL_PHASE = "optical_phase"


#: One line on what each observable actually is, so that a pairing can be
#: judged against physics rather than against a word.
OBSERVABLE_MEANINGS: dict[Observable, str] = {
    Observable.STRAIN:
        "fractional deformation inside a solid, dimensionless",
    Observable.ACOUSTIC:
        "a propagating mechanical vibration field in bulk or at a "
        "surface, as a continuum quantity",
    Observable.PHONON:
        "an INDIVIDUAL quantized lattice vibration mode; a quantum of "
        "mechanical excitation, not a continuum amplitude",
    Observable.DISPLACEMENT:
        "the position of a surface or electrode relative to a reference",
    Observable.MAGNETIC_FIELD:
        "magnetic flux density at the sensing element",
    Observable.OPTICAL_INTENSITY:
        "optical power per unit area arriving at the sensing element",
    Observable.OPTICAL_PHASE:
        "the phase of an optical field, which only becomes a measurable "
        "intensity after interference",
}


class DetectorKind(Enum):
    """A class of transducer, named by its transduction mechanism."""

    PIEZOELECTRIC = "piezoelectric"
    CAPACITIVE = "capacitive"
    HALL = "hall"
    OPTICAL = "optical"
    CCD = "ccd"


# --- the sensitivity domain ---------------------------------------------

@dataclass(frozen=True)
class DetectorCapability:
    """One transducer's sensitivity domain, stated in full.

    ``couples_to`` and ``cannot_detect`` must together cover every
    :class:`Observable` exactly once. That is the whole discipline of
    this module: there is no observable a detector is silently
    unclassified against, so no pairing can be waved through because
    nobody wrote down whether the mechanism reaches it.
    """

    kind: DetectorKind
    measurand: str
    mechanism: str
    frequency_range_hz: tuple[float, float]
    amplitude_floor: float
    amplitude_floor_units: str
    couples_to: frozenset
    cannot_detect: frozenset
    notes: str = ""
    status: str = MODEL_ONLY
    evidence_class: str = EVIDENCE_CLASS
    measured_here: str = "nothing"

    def __post_init__(self) -> None:
        if not self.measurand:
            raise DetectorError(
                f"{self.kind.value}: a capability needs a measurand; a "
                f"detector without a stated measurand has no domain")
        if not self.couples_to:
            raise DetectorError(
                f"{self.kind.value}: couples_to is empty; a transducer "
                f"that transduces nothing is not a detector")
        if not self.cannot_detect:
            raise DetectorError(
                f"{self.kind.value}: cannot_detect is empty; a detector "
                f"claimed to reach every observable has had its mechanism "
                f"removed from the description")
        overlap = self.couples_to & self.cannot_detect
        if overlap:
            raise DetectorError(
                f"{self.kind.value}: observable(s) "
                f"{sorted(o.value for o in overlap)} are listed as both "
                f"coupled and not coupled")
        covered = self.couples_to | self.cannot_detect
        missing = set(Observable) - covered
        if missing:
            raise DetectorError(
                f"{self.kind.value}: observable(s) "
                f"{sorted(o.value for o in missing)} are unclassified; "
                f"every observable is either coupled or explicitly "
                f"refused")
        lo, hi = self.frequency_range_hz
        if lo < 0 or hi <= 0 or hi <= lo:
            raise DetectorError(
                f"{self.kind.value}: frequency_range_hz must be an "
                f"increasing, non-negative (min, max)")
        if self.amplitude_floor <= 0:
            raise DetectorError(
                f"{self.kind.value}: the amplitude floor must be "
                f"positive; a floor of zero claims infinite sensitivity")
        if not self.amplitude_floor_units:
            raise DetectorError(
                f"{self.kind.value}: an amplitude floor without units is "
                f"not a floor")
        if self.status != MODEL_ONLY:
            raise DetectorError(
                f"{self.kind.value}: status must be {MODEL_ONLY!r}; no "
                f"capability here is measured or calibrated")

    @property
    def f_min_hz(self) -> float:
        return self.frequency_range_hz[0]

    @property
    def f_max_hz(self) -> float:
        return self.frequency_range_hz[1]

    def as_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "measurand": self.measurand,
            "mechanism": self.mechanism,
            "frequency_range_hz": list(self.frequency_range_hz),
            "amplitude_floor": self.amplitude_floor,
            "amplitude_floor_units": self.amplitude_floor_units,
            "couples_to": sorted(o.value for o in self.couples_to),
            "cannot_detect": sorted(o.value for o in self.cannot_detect),
            "notes": self.notes,
            "status": self.status,
            "evidence_class": self.evidence_class,
            "measured_here": self.measured_here,
        }


def _rest(*coupled: Observable) -> frozenset:
    """Everything the detector does NOT couple to, stated explicitly."""
    return frozenset(set(Observable) - set(coupled))


#: The matrix. Every number is a conventional order-of-magnitude figure
#: for a CLASS of transducer, carried as an ANALYTIC_MODEL description.
#: None of it is a datasheet value for any device, and none of it is
#: measured here.
DETECTOR_MATRIX: dict[DetectorKind, DetectorCapability] = {
    DetectorKind.PIEZOELECTRIC: DetectorCapability(
        kind=DetectorKind.PIEZOELECTRIC,
        measurand="mechanical strain / stress -> surface charge",
        mechanism=(
            "a strained piezoelectric lattice separates bound charge, "
            "producing a charge (or voltage) proportional to the applied "
            "stress; the element is a mechanical port with an electrical "
            "terminal"),
        frequency_range_hz=(1e-3, 1e7),
        amplitude_floor=1e-11,
        amplitude_floor_units="strain (dimensionless)",
        couples_to=frozenset({Observable.STRAIN, Observable.ACOUSTIC}),
        cannot_detect=_rest(Observable.STRAIN, Observable.ACOUSTIC),
        notes=(
            "the one transducer here with a genuine mechanical port: it "
            "sees bulk and surface acoustic modes as a CONTINUUM "
            "amplitude, across a wide band set by the element's cut, "
            "size and mounting. That is not the same as resolving an "
            "INDIVIDUAL phonon: a bulk vibration amplitude is a "
            "many-mode ensemble average, and single-quantum mechanical "
            "detection needs cryogenic, resonant, quantum-limited "
            "apparatus that is not modelled anywhere in this module. It "
            "has no magnetic and no optical port"),
    ),
    DetectorKind.CAPACITIVE: DetectorCapability(
        kind=DetectorKind.CAPACITIVE,
        measurand="electrode gap displacement -> capacitance",
        mechanism=(
            "a change in the gap between two electrodes changes the "
            "capacitance between them; the change is read out against a "
            "carrier excitation, so the bandwidth is bounded by the "
            "carrier and the front-end impedance"),
        frequency_range_hz=(1e-3, 1e5),
        amplitude_floor=1e-12,
        amplitude_floor_units="m (gap displacement)",
        couples_to=frozenset({Observable.DISPLACEMENT}),
        cannot_detect=_rest(Observable.DISPLACEMENT),
        notes=(
            "sub-nanometre gap resolution is routine, but the measurand "
            "is GAP, and the band is limited by the carrier scheme. An "
            "acoustic field is not transduced directly: what reaches the "
            "readout is the electrode displacement that field happens to "
            "produce, which is a different quantity with a different "
            "transfer function. It has no coupling to individual "
            "phonons, to magnetic flux, or to light"),
    ),
    DetectorKind.HALL: DetectorCapability(
        kind=DetectorKind.HALL,
        measurand="magnetic flux density -> transverse Hall voltage",
        mechanism=(
            "carriers drifting through a biased semiconductor plate are "
            "deflected by the Lorentz force, developing a transverse "
            "voltage proportional to the normal component of the flux "
            "density"),
        frequency_range_hz=(0.0, 1e6),
        amplitude_floor=1e-6,
        amplitude_floor_units="T",
        couples_to=frozenset({Observable.MAGNETIC_FIELD}),
        cannot_detect=_rest(Observable.MAGNETIC_FIELD),
        notes=(
            "responds to DC, which is its distinguishing virtue. It has "
            "no mechanical port and no optical port: strain, acoustic "
            "vibration and light intensity are not transduced. A Hall "
            "element in an acoustically noisy room still reads a "
            "magnetic field, and any correlation with the sound is "
            "mounting, cabling or supply, not acoustic sensitivity"),
    ),
    DetectorKind.OPTICAL: DetectorCapability(
        kind=DetectorKind.OPTICAL,
        measurand=(
            "optical phase or intensity -> photocurrent "
            "(interferometer plus fast photodiode)"),
        mechanism=(
            "an interferometer converts optical phase into intensity, "
            "and a photodiode converts intensity into photocurrent with "
            "no integration stage between them, so the response is fast"),
        frequency_range_hz=(1.0, 1e9),
        amplitude_floor=1e-15,
        amplitude_floor_units="m (interferometric displacement)",
        couples_to=frozenset({Observable.DISPLACEMENT,
                              Observable.OPTICAL_INTENSITY,
                              Observable.OPTICAL_PHASE}),
        cannot_detect=_rest(Observable.DISPLACEMENT,
                            Observable.OPTICAL_INTENSITY,
                            Observable.OPTICAL_PHASE),
        notes=(
            "the fast optical route: bandwidth up to GHz because the "
            "photodiode does not integrate over a frame. It reads "
            "SURFACE displacement through phase, not strain inside a "
            "solid, and it has no magnetic port. It does not resolve "
            "individual phonons: an interferometer reads a continuum "
            "surface amplitude, and single-quantum mechanical readout is "
            "not modelled here"),
    ),
    DetectorKind.CCD: DetectorCapability(
        kind=DetectorKind.CCD,
        measurand=(
            "INTEGRATED optical intensity (photons summed over an "
            "exposure) -> stored charge per pixel"),
        mechanism=(
            "a photon absorbed in silicon promotes an electron, which is "
            "held in a pixel potential well for the whole exposure and "
            "then clocked out; the pixel value is a TIME INTEGRAL of "
            "intensity, not an instantaneous sample"),
        frequency_range_hz=(1e-3, 1e3),
        amplitude_floor=5.0,
        amplitude_floor_units="photoelectrons per pixel per frame",
        couples_to=frozenset({Observable.OPTICAL_INTENSITY}),
        cannot_detect=_rest(Observable.OPTICAL_INTENSITY),
        notes=(
            "the frequency range is a FRAME RATE, of order hertz to "
            "kilohertz, and each frame is an integral over its exposure. "
            "A CCD has no mechanical port whatsoever: lattice vibration "
            "deposits no charge in a pixel well, so there is no phonon "
            "coupling to bound, integrate or amplify. What an image can "
            "show is a TIME-AVERAGED OPTICAL consequence of motion -- a "
            "blurred fringe, a shifted speckle, a changed intensity -- "
            "which is a statement about light over the exposure, not a "
            "detection of a mechanical mode. Optical phase reaches it "
            "only after an interferometer has already converted phase "
            "into intensity"),
    ),
}


def capability(kind: DetectorKind) -> DetectorCapability:
    """The sensitivity domain of one detector class."""
    if not isinstance(kind, DetectorKind):
        raise DetectorError(
            "kind must be a DetectorKind; an unnamed detector has no "
            "declared sensitivity domain")
    return DETECTOR_MATRIX[kind]


# --- domain queries ------------------------------------------------------

def can_detect(kind: DetectorKind, observable: Observable) -> bool:
    """Does this detector's mechanism reach this observable at all?"""
    if not isinstance(observable, Observable):
        raise DetectorError(
            "observable must be an Observable; an unnamed quantity "
            "cannot be checked against a sensitivity domain")
    return observable in capability(kind).couples_to


def select_detectors(observable: Observable) -> tuple:
    """Which detectors legitimately couple to a given observable.

    An empty result is a real answer, not a failure: it says nothing in
    this matrix has a mechanism that reaches the quantity. That is the
    case for :attr:`Observable.PHONON`, where every entry lists it under
    ``cannot_detect``.
    """
    if not isinstance(observable, Observable):
        raise DetectorError(
            "observable must be an Observable; an unnamed quantity "
            "selects nothing")
    return tuple(k for k in DetectorKind
                 if observable in DETECTOR_MATRIX[k].couples_to)


def bandwidth_ok(kind: DetectorKind, freq_hz: float) -> bool:
    """Is the frequency inside the detector's declared response band?

    Above the band the mechanism no longer follows the signal. For an
    integrating imager the ceiling is a frame rate, and beyond it the
    device does not roll off gracefully: it averages the waveform away
    inside a single exposure and returns a smooth frame that looks like
    a measurement.
    """
    cap = capability(kind)
    f = float(freq_hz)
    if f < 0:
        raise DetectorError("a frequency must be non-negative")
    return cap.f_min_hz <= f <= cap.f_max_hz


def above_floor(kind: DetectorKind, amplitude: float) -> bool:
    """Is the amplitude above the detector's own noise floor?"""
    cap = capability(kind)
    return float(amplitude) >= cap.amplitude_floor


# --- load-bearing refusals ----------------------------------------------

def refuse_ccd_phonon_claim(
        claim: str = "the CCD image shows phonons",
        exposure_s: float = 1.0) -> None:
    """A CCD cannot detect phonons. This ALWAYS raises.

    A CCD integrates optical intensity over an exposure and has no
    mechanical coupling of any kind. An image can at best carry a
    time-averaged *optical* consequence of motion; that is a statement
    about light, not a detection of a lattice mode.
    """
    ccd = capability(DetectorKind.CCD)
    raise DetectorError(
        f"refusing {claim!r} (exposure {exposure_s} s): a CCD transduces "
        f"{ccd.measurand}. Its pixel value is a TIME INTEGRAL of "
        f"intensity over the whole exposure, read out at a frame rate of "
        f"order {ccd.f_min_hz:g} Hz to {ccd.f_max_hz:g} Hz. It has NO "
        f"mechanical or phonon coupling: a lattice vibration deposits no "
        f"charge in a pixel well, so there is nothing for the exposure "
        f"to integrate, and a longer exposure integrates more photons, "
        f"never a first phonon. The most an image can carry is a "
        f"TIME-AVERAGED OPTICAL consequence of motion -- blur, a shifted "
        f"fringe or speckle, a changed intensity -- which is evidence "
        f"about light during the exposure, not a phonon measurement. "
        f"Individual phonons are not detected by anything in this "
        f"matrix; a piezoelectric element sees bulk acoustic amplitude "
        f"as a continuum, which is a different claim. "
        f"{DEFAULT_VERDICT}.")


def refuse_out_of_domain(kind: DetectorKind,
                         observable: Observable,
                         context: str = "") -> None:
    """Refuse any detector asked for an observable outside its domain.

    Returns ``None`` for a legitimate pairing. Raises
    :class:`DetectorError` otherwise, because the reading a detector
    gives outside its sensitivity domain is the response of some other
    mechanism -- pickup, drift, thermal expansion, a mundane optical
    side effect -- and reading it as the intended measurand is an
    artifact, not a measurement. ``(CCD, PHONON)`` is the canonical
    case; the guard is general and fires for every such pairing.
    """
    if not isinstance(observable, Observable):
        raise DetectorError(
            "observable must be an Observable; an unnamed quantity "
            "cannot be checked against a sensitivity domain")
    cap = capability(kind)
    if observable in cap.couples_to:
        return None
    if kind is DetectorKind.CCD and observable is Observable.PHONON:
        refuse_ccd_phonon_claim(
            claim=context or "a CCD is asked to report phonons")
    where = f" ({context})" if context else ""
    legit = [k.value for k in select_detectors(observable)]
    legit_text = str(legit) if legit else "NONE in this matrix"
    raise DetectorError(
        f"{kind.value} cannot be asked for {observable.value}{where}: it "
        f"transduces {cap.measurand}, and {observable.value} "
        f"({OBSERVABLE_MEANINGS[observable]}) is listed in its "
        f"cannot_detect set. It couples only to "
        f"{sorted(o.value for o in cap.couples_to)}. A detector used "
        f"outside its sensitivity domain still returns a number, but "
        f"that number is the response of some other mechanism -- "
        f"pickup, drift, thermal expansion, an incidental optical "
        f"consequence -- so it is an ARTIFACT, not a measurement of "
        f"{observable.value}. "
        f"Legitimate detectors for {observable.value}: {legit_text}.")


def refuse_out_of_band(kind: DetectorKind, freq_hz: float,
                       context: str = "") -> None:
    """Refuse a detector asked to resolve a frequency outside its band.

    Returns ``None`` inside the band. Above it the mechanism cannot
    follow the signal per cycle: an integrating imager averages the
    waveform away inside one exposure and hands back a smooth frame,
    which is the most dangerous kind of artifact because it looks like
    a clean measurement.
    """
    if bandwidth_ok(kind, freq_hz):
        return None
    cap = capability(kind)
    f = float(freq_hz)
    where = f" ({context})" if context else ""
    side = "above" if f > cap.f_max_hz else "below"
    extra = ""
    if kind is DetectorKind.CCD and f > cap.f_max_hz:
        extra = (
            " A CCD's ceiling is a FRAME RATE, and each frame is an "
            "integral over its exposure, so resolving a waveform "
            "per-cycle would need at least two frames per cycle. Beyond "
            "that the cycles are averaged inside a single exposure and "
            "the frame shows a time-averaged optical result, not the "
            "waveform.")
    raise DetectorError(
        f"{kind.value} cannot resolve {f:g} Hz{where}: that is {side} "
        f"its declared band of {cap.f_min_hz:g} Hz to {cap.f_max_hz:g} "
        f"Hz.{extra} A reading taken outside the response band is an "
        f"artifact of the readout, not a measurement of the signal.")


def refuse_measured_claim(
        quantity: str = "any value in this module") -> None:
    """Nothing in this module is measured. This ALWAYS raises."""
    raise DetectorError(
        f"{quantity!r} is not measured here. Every entry in the detector "
        f"matrix is a conventional, order-of-magnitude ANALYTIC_MODEL "
        f"description of a CLASS of transducer -- not a datasheet for "
        f"any device, not a calibration, and not a reading. No detector "
        f"is built, powered, mounted, pointed at anything or read out; "
        f"no strain, displacement, magnetic field, light level or frame "
        f"is recorded. PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- report -------------------------------------------------------------

def detectors_report() -> dict:
    return {
        "what_this_is": (
            "a detector matrix in which every transducer carries an "
            "explicit SENSITIVITY DOMAIN -- measurand, frequency range, "
            "amplitude floor, the observables it couples to and the "
            "observables it explicitly cannot detect -- plus the guards "
            "that refuse any use outside that domain"),
        "why_sensitivity_domains": (
            "a transducer answers only the question its physics can "
            "answer. Outside its domain it still returns a number, but "
            "the number is the response of a different mechanism, so it "
            "is an ARTIFACT rather than a measurement. Writing the "
            "domain down -- including the non-empty cannot_detect half "
            "-- is what makes that failure visible instead of silent"),
        "detectors": {k.value: DETECTOR_MATRIX[k].as_dict()
                      for k in DetectorKind},
        "observables": {o.value: OBSERVABLE_MEANINGS[o] for o in Observable},
        "coupling_matrix": {
            k.value: {o.value: can_detect(k, o) for o in Observable}
            for k in DetectorKind},
        "selection": {o.value: [k.value for k in select_detectors(o)]
                      for o in Observable},
        "phonon_selection_is_empty":
            select_detectors(Observable.PHONON) == (),
        "distinctions_enforced": [
            "a CCD integrates optical intensity over an exposure at a "
            "hertz-to-kilohertz frame rate and has NO phonon coupling; "
            "an image can at best show a time-averaged OPTICAL "
            "consequence of motion -- refuse_ccd_phonon_claim",
            "any detector asked for an observable outside its "
            "couples_to set is refused, generally and not only for the "
            "canonical CCD/phonon case -- refuse_out_of_domain",
            "a detector asked to resolve a frequency outside its "
            "declared band is refused; a frame-rate integrator cannot "
            "resolve a kilohertz waveform per cycle -- "
            "refuse_out_of_band",
            "bulk acoustic amplitude (a continuum quantity a "
            "piezoelectric element does transduce) is NOT an individual "
            "phonon; nothing in this matrix detects individual phonons",
            "nothing here is measured -- refuse_measured_claim",
        ],
        "verdict": DEFAULT_VERDICT,
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not measure strain, displacement, acoustic "
            "amplitude, magnetic flux, optical intensity or any phonon "
            "population. It does not describe, calibrate or endorse any "
            "particular instrument: the frequency ranges and amplitude "
            "floors are conventional order-of-magnitude figures for "
            "classes of transducer, carried as an analytic model. It "
            "does not say that a CCD image can detect phonons, that a "
            "long exposure can integrate a mechanical mode into "
            "existence, that a time-averaged optical effect is a "
            "mechanical measurement, or that any detector here resolves "
            "individual quanta of lattice vibration. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }
