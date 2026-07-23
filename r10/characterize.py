"""P05 — axis, growth-sector, and defect characterization ladders.

The source material would like a quartz specimen to *be* a
characterization: to say a stone "is right-handed", "is defect-free",
or "has its c-axis here" from a glance at its habit. This module refuses
that leap and does the one honest thing. It writes down two ordered
**characterization ladders** -- a LOW-COST optical/visual tier and an
ADVANCED instrumental tier -- and represents every rung as a
*measurement request*, never a measurement. There is no bench in this
repository: no polariscope, no goniometer, no diffractometer, no
spectrometer, no balance with a specimen on it. So every proxy this
module can build is born ``REQUESTED`` and can never be promoted to
``MEASURED`` here, because nothing measured it.

**The low-cost ladder** (visual / optical, first): crossed polarizers
for twinning and internal strain; goniometry for crystallographic axis
from face angles; immersion for inclusion counting; scratch (Mohs)
hardness; and density by Archimedes weighing. **The advanced ladder**
(instrumental, second): X-ray Laue diffraction for c-axis and
handedness; FTIR for hydroxyl / structural water; EPR for paramagnetic
point defects; acoustic-Q ringdown; dielectric loss tan-delta;
cathodoluminescence for growth sectors; and ICP-MS for trace elements.

**What is real here (and it is small, closed-form, and testable).**
Two pieces of arithmetic are exact and carry power:

* Archimedes density, ``rho = m_air / (m_air - m_water) * rho_water``,
  recovers the bulk density of a planted mass pair (quartz ~2.65
  g/cm^3). It is a definition applied to numbers, not a weighing.
* A c-axis orientation is *determined* only by two non-parallel
  crystallographic direction measurements; their common normal (a small
  Gram-Schmidt / cross-product) fixes it. **A single direction is
  underdetermined** and raises :class:`CharacterizeError` -- the same
  roll-identifiability fact that governs a root frame.

**The load-bearing refusals.** Handedness (left vs. right quartz) is
never inferred from external shape or habit; it requires an oriented
measurement -- etch figures or the sign of optical rotation -- and
:func:`refuse_handedness_from_shape` raises rather than guess. And a
defect proxy cannot carry a value, an uncertainty, or the status
``MEASURED`` unless a method actually produced one;
:func:`refuse_result_without_measurement` raises, because no method ran.

Nothing here is measured. The ladders record what a characterization
*would* request; the arithmetic computes only what a definition
defines.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class CharacterizeError(RuntimeError):
    """Raised for any refusal in this module: an underdetermined c-axis,
    handedness read off shape, or a result claimed without a measurement."""


# --- the ladder tiers ---------------------------------------------------

class Tier(Enum):
    """Which characterization tier a method belongs to. Low-cost first."""

    LOW_COST = "LOW_COST"
    ADVANCED = "ADVANCED"


class Method(Enum):
    """A rung on a characterization ladder.

    Each member carries a human label, its :class:`Tier`, and a plain
    statement of what it measures. Membership on this enum asserts only
    that the method exists in the literature -- not that it was ever run.
    """

    # --- low-cost ladder: visual / optical, no instrument bench ---------
    CROSSED_POLARIZERS = (
        "crossed-polariser inspection", Tier.LOW_COST,
        "twinning and internal strain under crossed polarizers")
    GONIOMETRY = (
        "reflection goniometry", Tier.LOW_COST,
        "crystallographic axis orientation from interfacial face angles")
    IMMERSION_INCLUSION_COUNT = (
        "immersion inclusion counting", Tier.LOW_COST,
        "fluid and solid inclusions by index-matched immersion")
    MOHS_HARDNESS = (
        "Mohs scratch hardness", Tier.LOW_COST,
        "scratch hardness against a reference set")
    ARCHIMEDES_DENSITY = (
        "Archimedes density", Tier.LOW_COST,
        "bulk density by weighing in air and in water")

    # --- advanced ladder: instrumental --------------------------------
    XRD_LAUE = (
        "X-ray Laue diffraction", Tier.ADVANCED,
        "c-axis orientation and handedness by back-reflection Laue")
    FTIR = (
        "Fourier-transform infrared spectroscopy", Tier.ADVANCED,
        "hydroxyl and structural water by infrared absorption")
    EPR = (
        "electron paramagnetic resonance", Tier.ADVANCED,
        "paramagnetic point defects and colour-centre precursors")
    ACOUSTIC_Q_RINGDOWN = (
        "acoustic Q ringdown", Tier.ADVANCED,
        "acoustic quality factor by resonant ringdown")
    DIELECTRIC_TAN_DELTA = (
        "dielectric loss tan-delta", Tier.ADVANCED,
        "dielectric loss tangent versus frequency")
    CATHODOLUMINESCENCE = (
        "cathodoluminescence imaging", Tier.ADVANCED,
        "growth sectors and zoning by cathodoluminescence")
    ICP_MS = (
        "inductively-coupled-plasma mass spectrometry", Tier.ADVANCED,
        "trace-element concentrations by ICP-MS")

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def tier(self) -> Tier:
        return self.value[1]

    @property
    def measures(self) -> str:
        return self.value[2]


def methods_in_tier(tier: Tier) -> tuple[Method, ...]:
    """The ladder rungs of one tier, in definition order."""
    return tuple(m for m in Method if m.tier is tier)


# --- the defect registry ------------------------------------------------

class DefectKind(Enum):
    """The kinds of defect a proxy can stand in for."""

    TWINNING = "TWINNING"
    DISLOCATION = "DISLOCATION"
    HYDROXYL = "HYDROXYL"
    COLOR_CENTRE = "COLOR_CENTRE"
    INCLUSION = "INCLUSION"
    GROWTH_SECTOR = "GROWTH_SECTOR"
    INTERNAL_STRESS = "INTERNAL_STRESS"
    TRACE_ELEMENT = "TRACE_ELEMENT"


#: Which method a given defect kind is characterized by. This is a
#: routing table for *requests*, not a claim that any run occurred.
DEFECT_METHOD = {
    DefectKind.TWINNING: Method.CROSSED_POLARIZERS,
    DefectKind.INTERNAL_STRESS: Method.CROSSED_POLARIZERS,
    DefectKind.INCLUSION: Method.IMMERSION_INCLUSION_COUNT,
    DefectKind.DISLOCATION: Method.XRD_LAUE,
    DefectKind.HYDROXYL: Method.FTIR,
    DefectKind.COLOR_CENTRE: Method.EPR,
    DefectKind.GROWTH_SECTOR: Method.CATHODOLUMINESCENCE,
    DefectKind.TRACE_ELEMENT: Method.ICP_MS,
}


@dataclass
class DefectProxy:
    """A stand-in for a defect that a method *would* characterize.

    A proxy is born ``REQUESTED`` and carries no value: it names the
    defect kind and the method required, nothing more. It cannot be
    constructed as ``MEASURED`` -- there is no bench to have measured it
    -- and :func:`refuse_result_without_measurement` guards the promotion.
    """

    kind: DefectKind
    method_required: Method
    value: float | None = None
    uncertainty: float | None = None
    status: str = "REQUESTED"

    def __post_init__(self) -> None:
        if self.uncertainty is not None and self.uncertainty < 0:
            raise CharacterizeError("uncertainty must be non-negative")
        if self.status != "REQUESTED":
            # The only status a software-only module can honestly assign.
            refuse_result_without_measurement(self)


def request_defect(kind: DefectKind) -> DefectProxy:
    """A REQUESTED proxy for a defect kind, routed to its method."""
    if kind not in DEFECT_METHOD:
        raise CharacterizeError(f"no method routing for {kind!r}")
    return DefectProxy(kind=kind, method_required=DEFECT_METHOD[kind])


def refuse_result_without_measurement(proxy: DefectProxy) -> None:
    """A proxy cannot carry a value or ``MEASURED`` without a real run.

    There is no instrument in this repository. A ``value``, an
    ``uncertainty``, or the status ``MEASURED`` may only come from a
    method that actually produced them; naming the method is not running
    it. So this refuses unconditionally -- the point of the module.
    """
    raise CharacterizeError(
        f"the {proxy.kind.name} proxy requests "
        f"{proxy.method_required.label} but no bench has run it. A defect "
        f"proxy cannot be promoted to MEASURED, and cannot carry a value "
        f"or an uncertainty, until a real instrument produces one. There "
        f"is no apparatus here; the request is not the result. "
        f"RESULT_WITHOUT_MEASUREMENT_REFUSED.")


# --- the c-axis: determined only by two non-parallel directions ---------

def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n == 0:
        raise CharacterizeError("zero-length direction")
    return v / n


def resolve_c_axis(directions) -> np.ndarray:
    """The c-axis unit vector from two non-parallel measured directions.

    Two crystallographic direction measurements known to lie in the zone
    of the c-axis (e.g. two prism-face normals) determine it: the c-axis
    is their common normal, normalized. A single direction leaves the
    orientation underdetermined -- one rotational degree of freedom is
    unfixed -- and parallel directions determine no plane at all. Both
    raise :class:`CharacterizeError`.
    """
    dirs = [np.asarray(d, float) for d in directions]
    if len(dirs) < 2:
        raise CharacterizeError(
            "a single direction is UNDERDETERMINED: one measured "
            "crystallographic direction leaves a rotational degree of "
            "freedom unfixed and cannot resolve the c-axis. Two "
            "non-parallel directions are required.")
    d1 = _unit(dirs[0])
    d2 = _unit(dirs[1])
    if abs(np.dot(d1, d2)) > 1 - 1e-9:
        raise CharacterizeError(
            "the two directions are parallel, so they determine no plane "
            "and cannot resolve the c-axis. Two non-parallel directions "
            "are required.")
    c = np.cross(d1, d2)
    return c / np.linalg.norm(c)


def refuse_handedness_from_shape(habit: str | None = None,
                                 morphology: str | None = None) -> None:
    """Left/right quartz is never read off external shape or habit.

    Handedness is a property of the atomic screw sense, not of the
    crystal's outward form: a specimen's habit, the presence or absence
    of trigonal trapezohedral (``s``/``x``) faces, or any morphological
    cue is not a reliable determinant. Handedness requires an *oriented*
    measurement -- etch figures on a known face, or the sign of optical
    rotation along the c-axis. So this refuses; the arguments exist only
    to name the cues that are *not* sufficient.
    """
    raise CharacterizeError(
        "handedness (left- vs. right-handed quartz) cannot be inferred "
        "from external shape, habit, or the pattern of faces. It is fixed "
        "by the atomic screw sense and read only by an oriented "
        "measurement: etch figures on a known face, or the sign of "
        "optical rotation along the c-axis. HANDEDNESS_FROM_SHAPE_REFUSED.")


# --- Archimedes density: a definition applied to numbers ----------------

#: Density of water at ~20 C, g/cm^3. A literature constant, not measured.
RHO_WATER_20C_G_PER_CM3 = 0.998207


def archimedes_density(m_air: float, m_water: float,
                       rho_water: float = RHO_WATER_20C_G_PER_CM3) -> float:
    """Bulk density rho = m_air / (m_air - m_water) * rho_water.

    ``m_air`` is the specimen weighed in air, ``m_water`` its apparent
    weight suspended in water; the difference is the buoyant weight of
    the displaced water. For a planted quartz pair this recovers ~2.65
    g/cm^3. It is arithmetic on supplied masses, not a weighing.
    """
    if m_air <= 0:
        raise CharacterizeError("mass in air must be positive")
    if rho_water <= 0:
        raise CharacterizeError("water density must be positive")
    buoyant = m_air - m_water
    if buoyant <= 0:
        raise CharacterizeError(
            "mass in water must be less than mass in air (the specimen "
            "must sink and displace water)")
    return m_air / buoyant * rho_water


# --- the plan: an ordered ladder of REQUESTS ----------------------------

@dataclass(frozen=True)
class MeasurementRequest:
    """One rung of a characterization plan, as a request only."""

    method: Method
    target: str
    tier: Tier
    status: str = "REQUESTED"


def characterization_plan(specimen_material_class: str
                          ) -> tuple[MeasurementRequest, ...]:
    """The ordered ladder for a specimen: low-cost first, then advanced.

    Every rung is a :class:`MeasurementRequest` with status
    ``REQUESTED``. Nothing is measured, scheduled, or promised; the plan
    records what a characterization *would* ask for, in the order a
    careful worker would ask -- cheap non-destructive optics before
    expensive instrumental methods.
    """
    if not specimen_material_class or not specimen_material_class.strip():
        raise CharacterizeError("a specimen material class is required")
    requests = []
    for tier in (Tier.LOW_COST, Tier.ADVANCED):
        for method in methods_in_tier(tier):
            requests.append(MeasurementRequest(
                method=method, target=method.measures, tier=tier,
                status="REQUESTED"))
    return tuple(requests)


# --- the report ---------------------------------------------------------

def characterize_report() -> dict:
    return {
        "what_this_is": (
            "two ordered characterization ladders for a quartz specimen "
            "-- a low-cost optical/visual tier and an advanced "
            "instrumental tier -- represented as measurement requests"),
        "low_cost_ladder": [m.name for m in methods_in_tier(Tier.LOW_COST)],
        "advanced_ladder": [m.name for m in methods_in_tier(Tier.ADVANCED)],
        "the_real_arithmetic": (
            "Archimedes density rho = m_air/(m_air - m_water)*rho_water "
            "recovers ~2.65 g/cm^3 for a planted quartz pair; a c-axis is "
            "determined only by two non-parallel directions (a single one "
            "is underdetermined)"),
        "defect_kinds": [k.name for k in DefectKind],
        "refusals": [
            "handedness is never inferred from external shape or habit; it "
            "needs an oriented measurement (etch figures or optical "
            "rotation sign) -- HANDEDNESS_FROM_SHAPE_REFUSED",
            "a single crystallographic direction cannot resolve the c-axis "
            "-- it is UNDERDETERMINED",
            "a defect proxy cannot carry a value or MEASURED status without "
            "a method that produced it -- RESULT_WITHOUT_MEASUREMENT_REFUSED",
        ],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "hardware_status": (
            "DEFERRED — no polariscope, goniometer, diffractometer, "
            "spectrometer, or balance with a specimen on it exists here"),
        "verdict": "CHARACTERIZATION_LADDER_SOFTWARE_ONLY",
        "what_this_does_not_say": (
            "It does not say any specimen was inspected, weighed, "
            "diffracted, or scanned, or that any twinning, strain, "
            "inclusion, hydroxyl, colour centre, dislocation, growth "
            "sector, or trace element was found. It does not say a "
            "specimen is left- or right-handed, or where its c-axis lies. "
            "The ladders are requests and the arithmetic is a definition "
            "applied to planted numbers; nothing here is a measurement."),
    }
