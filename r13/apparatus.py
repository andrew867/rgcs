"""P20/P21 — the apparatus, as a preregistered design set that is not built.

R13 needs a bench it does not have. This module writes that bench down as
a *design*: the coils, the transducer, the fixture, and the excitation and
readout chains that would drive and record a specimen, each carried as a
:class:`Component` with a bill-of-materials line and nothing more. It
follows the shape of :mod:`r12.homelab`, which preregisters the four
experiments; here the object preregistered is the apparatus those
experiments would run on.

**Nothing is built.** There is no Helmholtz pair, no piezo element, no
amplifier, no lock-in, no thermostat and no fixture in this repository.
Every component is a ``DESIGN_ONLY`` line with a generic vendor *category*
(never a real vendor or part number), a set of nominal ratings, and an
order-of-magnitude cost estimate. The claim class is
``ENGINEERING_CANDIDATE``: a plausible design that has not been procured,
assembled, powered, or measured. :class:`Component` refuses at
construction to carry status ``BUILT`` or ``MEASURED``, and
:func:`refuse_design_as_built` and :func:`refuse_design_as_measurement`
refuse to let the design be read as either.

**The two chains are connectivity, not signal.** :func:`excitation_chain`
and :func:`readout_chain` return ordered pipelines of registered
components in which the output port of each stage matches the input port
of the next, so the design is a *connected* chain rather than a bag of
parts. That the ports connect on paper says nothing about what any stage
would do to a real signal, because no stage exists.

**The safety envelope is a design bound, not a clearance.** Each drive
rating -- voltage, current, magnetic field, temperature -- is kept inside
a declared envelope, and :func:`check_safety` reports whether a proposed
setting sits inside it. A pass is a statement about numbers against a
declared bound; it is emphatically **not** a validation, an approval, or a
clearance to energise anything, and :func:`check_safety` refuses to mark
anything validated.

No component is procured, assembled, wired, energised, or read out. No
measurement is produced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# --- verdict and claim vocabulary ----------------------------------------

#: The standing verdict for this module.
VERDICT = "APPARATUS_DESIGN_PREREGISTERED_NOT_BUILT"

#: The typed claim vocabulary, exact strings, shared across the release.
CLAIM_CLASSES: tuple[str, ...] = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "ANALYTIC_MODEL",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

#: The one status a component may carry here. A component is a design line,
#: never a built or measured object.
DESIGN_ONLY = "DESIGN_ONLY"

#: The statuses that assert hardware exists; forbidden at construction.
FORBIDDEN_STATUSES = frozenset({"BUILT", "MEASURED"})

EVIDENCE_CLASS = "ANALYTIC_MODEL"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class ApparatusError(RuntimeError):
    """Raised when a design is asked to be more than a design.

    Covers the structural guards (a component with no function, a chain
    that names an unregistered part or does not connect) and the
    load-bearing refusals :func:`refuse_design_as_built`,
    :func:`refuse_design_as_measurement`, and the safety refusal to mark
    anything validated.
    """


# --- one component of the apparatus --------------------------------------

@dataclass(frozen=True)
class Component:
    """One line of the apparatus design: a part that has not been bought.

    ``spec`` is a dict of nominal ratings (an order-of-magnitude design
    target, not a datasheet). ``vendor_class`` is a generic *category*
    (e.g. "laboratory signal generator"), never a real vendor or part
    number. ``input_port`` and ``output_port`` name the signal a stage
    accepts and emits so the chains can be checked for connectivity;
    environmental components (a thermostat) carry ``None`` for both and
    sit in no chain.

    ``status`` is fixed at ``DESIGN_ONLY`` and the claim class at
    ``ENGINEERING_CANDIDATE``. Constructing a component with status
    ``BUILT`` or ``MEASURED`` is refused: no hardware exists here.
    """

    name: str
    function: str
    spec: dict
    vendor_class: str
    est_cost_usd: float
    input_port: str | None = None
    output_port: str | None = None
    status: str = DESIGN_ONLY
    claim_class: str = ENGINEERING_CANDIDATE

    def __post_init__(self) -> None:
        if not str(self.name).strip():
            raise ApparatusError("a component needs a name")
        if not str(self.function).strip():
            raise ApparatusError(
                f"{self.name}: a component needs a stated function; a part "
                f"without a function is not a design line")
        if not isinstance(self.spec, dict) or not self.spec:
            raise ApparatusError(
                f"{self.name}: spec must be a non-empty dict of nominal "
                f"ratings")
        if not str(self.vendor_class).strip():
            raise ApparatusError(
                f"{self.name}: a generic vendor_class category is required "
                f"(never a real vendor or part number)")
        try:
            cost = float(self.est_cost_usd)
        except (TypeError, ValueError):
            raise ApparatusError(
                f"{self.name}: est_cost_usd must be a number") from None
        if cost < 0.0:
            raise ApparatusError(
                f"{self.name}: est_cost_usd must be non-negative")
        if self.status in FORBIDDEN_STATUSES:
            raise ApparatusError(
                f"{self.name}: status {self.status!r} is refused. No "
                f"component here is built or measured; a component is a "
                f"{DESIGN_ONLY} design line with claim class "
                f"{ENGINEERING_CANDIDATE}, not hardware. {VERDICT}")
        if self.status != DESIGN_ONLY:
            raise ApparatusError(
                f"{self.name}: status must be {DESIGN_ONLY!r}; nothing here "
                f"is procured, assembled, powered, or read out")
        if self.claim_class != ENGINEERING_CANDIDATE:
            raise ApparatusError(
                f"{self.name}: a design component is an "
                f"{ENGINEERING_CANDIDATE}, not {self.claim_class!r}")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "function": self.function,
            "spec": dict(self.spec),
            "vendor_class": self.vendor_class,
            "est_cost_usd": float(self.est_cost_usd),
            "input_port": self.input_port,
            "output_port": self.output_port,
            "status": self.status,
            "claim_class": self.claim_class,
            "measured_here": MEASURED_HERE,
        }


# --- the design registry --------------------------------------------------

#: The apparatus, as an ordered registry of design lines. Every rating is
#: a nominal, order-of-magnitude design target, and every vendor_class is a
#: generic category. Ports are named so the excitation and readout chains
#: can be checked for connectivity.
DESIGN: dict[str, Component] = {
    "signal_generator": Component(
        name="signal_generator",
        function=("synthesise the low-level drive waveform (stepped or "
                  "swept sine, gated tone burst) that excites the specimen"),
        spec={
            "frequency_range_hz": [1.0, 2.0e7],
            "amplitude_vpp": 10.0,
            "frequency_resolution_hz": 1e-3,
            "output_impedance_ohm": 50.0,
        },
        vendor_class="laboratory arbitrary/function generator",
        est_cost_usd=1500.0,
        input_port="reference_clock",
        output_port="drive_waveform_lowlevel",
    ),
    "power_amplifier": Component(
        name="power_amplifier",
        function=("raise the low-level waveform to the drive current the "
                  "coils need, at constant gain across the band"),
        spec={
            "gain_db": 40.0,
            "output_current_a_max": 2.0,
            "bandwidth_hz": [1.0, 1.0e6],
            "load_impedance_ohm": 8.0,
        },
        vendor_class="laboratory power amplifier",
        est_cost_usd=1200.0,
        input_port="drive_waveform_lowlevel",
        output_port="drive_current",
    ),
    "drive_coils_helmholtz": Component(
        name="drive_coils_helmholtz",
        function=("a Helmholtz pair producing a uniform axial magnetic "
                  "drive field over the specimen volume"),
        spec={
            "geometry": "Helmholtz pair",
            "coil_radius_m": 0.10,
            "turns_per_coil": 200,
            "field_per_amp_mt_per_a": 1.8,
            "max_continuous_current_a": 2.0,
        },
        vendor_class="wound magnetic drive coil set",
        est_cost_usd=600.0,
        input_port="drive_current",
        output_port="magnetic_drive_field",
    ),
    "mechanical_fixture": Component(
        name="mechanical_fixture",
        function=("hold the specimen rigidly in the drive field and couple "
                  "its motion to the pickup transducer, with mechanical "
                  "isolation from the bench"),
        spec={
            "specimen_envelope_mm": [30.0, 30.0, 10.0],
            "mount": "kinematic three-point",
            "isolation": "elastomer sub-mount",
            "return_repeatability_deg": 0.1,
        },
        vendor_class="machined specimen fixture / mount",
        est_cost_usd=400.0,
        input_port="magnetic_drive_field",
        output_port="specimen_excitation",
    ),
    "piezo_transducer": Component(
        name="piezo_transducer",
        function=("transduce specimen surface motion into a charge signal "
                  "for the readout chain (mechanical port, electrical "
                  "terminal)"),
        spec={
            "mechanism": "piezoelectric",
            "charge_sensitivity_pc_per_n": 4.0,
            "resonance_hz": 2.0e5,
            "capacitance_pf": 500.0,
        },
        vendor_class="piezoelectric transducer element",
        est_cost_usd=300.0,
        input_port="specimen_excitation",
        output_port="pickup_charge",
    ),
    "low_noise_preamp": Component(
        name="low_noise_preamp",
        function=("buffer and amplify the transducer charge signal at low "
                  "added noise before demodulation"),
        spec={
            "input_type": "charge/voltage",
            "input_noise_nv_per_rthz": 1.5,
            "gain_db": 40.0,
            "bandwidth_hz": [0.1, 1.0e7],
        },
        vendor_class="low-noise preamplifier",
        est_cost_usd=900.0,
        input_port="pickup_charge",
        output_port="buffered_voltage",
    ),
    "lock_in_receiver": Component(
        name="lock_in_receiver",
        function=("heterodyne / lock-in demodulation of the buffered signal "
                  "against the drive reference to baseband amplitude and "
                  "phase"),
        spec={
            "frequency_range_hz": [1.0e-3, 6.0e5],
            "input_noise_nv_per_rthz": 5.0,
            "time_constant_s": [1e-5, 30.0],
            "dynamic_reserve_db": 100.0,
        },
        vendor_class="lock-in / heterodyne receiver",
        est_cost_usd=6000.0,
        input_port="buffered_voltage",
        output_port="demodulated_baseband",
    ),
    "temperature_control": Component(
        name="temperature_control",
        function=("stabilise and log the specimen temperature; quartz "
                  "frequency and Q drift with temperature, so an unlogged "
                  "thermal drift is a standing false positive"),
        spec={
            "setpoint_range_c": [15.0, 45.0],
            "stability_c": 0.02,
            "sensor": "platinum RTD",
            "logging": "continuous",
        },
        vendor_class="benchtop temperature controller",
        est_cost_usd=800.0,
        input_port=None,
        output_port=None,
    ),
}


def component(name: str) -> Component:
    """The design line for one component."""
    try:
        return DESIGN[name]
    except KeyError:
        raise ApparatusError(
            f"{name!r} is not a registered component; the design registry "
            f"holds {sorted(DESIGN)}") from None


# --- bill of materials ----------------------------------------------------

def bill_of_materials() -> dict:
    """The design registry as a bill of materials, with a total estimate.

    Every line is ``DESIGN_ONLY``; the total is the exact sum of the line
    estimates. A bill of materials is a shopping list for a bench that has
    not been bought, not an inventory of one that has.
    """
    items = [c.as_dict() for c in DESIGN.values()]
    total = sum(c.est_cost_usd for c in DESIGN.values())
    return {
        "items": items,
        "n_items": len(items),
        "total_est_cost_usd": float(total),
        "all_design_only": all(c.status == DESIGN_ONLY
                               for c in DESIGN.values()),
        "claim_class": ENGINEERING_CANDIDATE,
        "measured_here": MEASURED_HERE,
        "note": ("an order-of-magnitude cost estimate for an unbuilt "
                 "design; no part has been procured"),
    }


# --- the excitation and readout chains -----------------------------------

#: The drive path: generator -> amplifier -> coils -> fixture/specimen.
EXCITATION_CHAIN: tuple[str, ...] = (
    "signal_generator",
    "power_amplifier",
    "drive_coils_helmholtz",
    "mechanical_fixture",
)

#: The record path: fixture/specimen -> transducer -> preamp -> receiver.
READOUT_CHAIN: tuple[str, ...] = (
    "mechanical_fixture",
    "piezo_transducer",
    "low_noise_preamp",
    "lock_in_receiver",
)


def _validate_chain(names: tuple[str, ...], label: str) -> list[Component]:
    """Resolve a chain to components and check it connects, or refuse.

    Every name must be a registered component, and the output port of each
    stage must equal the input port of the next, so the pipeline is a
    connected chain rather than an unordered set. A chain that names an
    unregistered part, or whose stages do not join, is refused.
    """
    if len(names) < 2:
        raise ApparatusError(
            f"the {label} needs at least two stages to be a chain")
    stages: list[Component] = []
    for name in names:
        if name not in DESIGN:
            raise ApparatusError(
                f"the {label} references {name!r}, which is not a registered "
                f"component; a chain may only use registered design lines")
        stages.append(DESIGN[name])
    for upstream, downstream in zip(stages, stages[1:]):
        if upstream.output_port is None or downstream.input_port is None:
            raise ApparatusError(
                f"the {label} is not connected: {upstream.name} -> "
                f"{downstream.name} joins a stage with no port")
        if upstream.output_port != downstream.input_port:
            raise ApparatusError(
                f"the {label} is not connected: {upstream.name} emits "
                f"{upstream.output_port!r} but {downstream.name} accepts "
                f"{downstream.input_port!r}")
    return stages


def excitation_chain() -> list[Component]:
    """The ordered drive pipeline, verified connected and registered."""
    return _validate_chain(EXCITATION_CHAIN, "excitation chain")


def readout_chain() -> list[Component]:
    """The ordered record pipeline, verified connected and registered."""
    return _validate_chain(READOUT_CHAIN, "readout chain")


def chain_is_connected(names: tuple[str, ...]) -> bool:
    """Whether a proposed chain references registered parts and connects."""
    try:
        _validate_chain(tuple(names), "chain")
    except ApparatusError:
        return False
    return True


# --- the safety envelope --------------------------------------------------

@dataclass(frozen=True)
class SafetyEnvelope:
    """The declared design bounds the drive settings are kept within.

    A bound, not a clearance: keeping a proposed setting inside the
    envelope is a design discipline, and it does not authorise energising
    anything, because nothing is built.
    """

    max_drive_voltage_vpp: float = 10.0
    max_drive_current_a: float = 2.0
    max_magnetic_field_mt: float = 5.0
    min_temperature_c: float = 15.0
    max_temperature_c: float = 45.0


#: The single declared envelope for the design.
SAFETY_ENVELOPE = SafetyEnvelope()


def check_safety(settings: dict,
                 envelope: SafetyEnvelope = SAFETY_ENVELOPE) -> dict:
    """Check proposed drive settings against the declared envelope.

    Returns a per-limit and overall pass/fail. A pass means only that the
    proposed *numbers* sit inside a declared design bound; it is not a
    validation, an approval, or a clearance to energise anything, and this
    function refuses to mark anything validated: ``validated`` is always
    ``False`` and ``physical_validation`` is
    ``PHYSICAL_VALIDATION_NOT_CLAIMED``.
    """
    if not isinstance(settings, dict):
        raise ApparatusError("settings must be a dict of proposed drive "
                             "values")
    checks: dict[str, dict] = {}

    def _within(key: str, value, low, high) -> None:
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise ApparatusError(
                f"setting {key!r} = {value!r} is not a number") from None
        ok = (low is None or v >= low) and (high is None or v <= high)
        checks[key] = {"value": v, "low": low, "high": high, "pass": bool(ok)}

    if "drive_voltage_vpp" in settings:
        _within("drive_voltage_vpp", settings["drive_voltage_vpp"],
                0.0, envelope.max_drive_voltage_vpp)
    if "drive_current_a" in settings:
        _within("drive_current_a", settings["drive_current_a"],
                0.0, envelope.max_drive_current_a)
    if "magnetic_field_mt" in settings:
        _within("magnetic_field_mt", settings["magnetic_field_mt"],
                0.0, envelope.max_magnetic_field_mt)
    if "temperature_c" in settings:
        _within("temperature_c", settings["temperature_c"],
                envelope.min_temperature_c, envelope.max_temperature_c)

    if not checks:
        raise ApparatusError(
            "no recognised setting to check; supply one or more of "
            "drive_voltage_vpp, drive_current_a, magnetic_field_mt, "
            "temperature_c")

    overall = all(c["pass"] for c in checks.values())
    return {
        "checks": checks,
        "pass": bool(overall),
        "within_envelope": bool(overall),
        # the refusal: a pass is never a validation or a clearance
        "validated": False,
        "is_clearance_to_energise": False,
        "claim_class": ENGINEERING_CANDIDATE,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": ("a pass means the proposed numbers sit inside a declared "
                 "design bound; it is NOT a validation, an approval, or a "
                 "clearance to energise anything, and nothing is built"),
    }


# --- the load-bearing refusals -------------------------------------------

def refuse_design_as_built(
        claim: str = "the apparatus is built",
        component_name: str | None = None) -> None:
    """Refuse to read the design as assembled hardware. Always raises.

    No component in the registry has been procured, machined, wound,
    wired, or assembled. Every line is ``DESIGN_ONLY`` with claim class
    ``ENGINEERING_CANDIDATE``.
    """
    named = f" ({component_name})" if component_name else ""
    raise ApparatusError(
        f"refused: {claim!r}{named}. The apparatus is a preregistered "
        f"DESIGN: every one of the {len(DESIGN)} components is a "
        f"{DESIGN_ONLY} line with a generic vendor category and an "
        f"order-of-magnitude cost estimate, and none has been procured, "
        f"machined, wound, wired, or assembled. A design read as built is "
        f"an {ENGINEERING_CANDIDATE} mistaken for hardware. {VERDICT}")


def refuse_design_as_measurement(
        claim: str = "the apparatus produced a measurement",
        quantity: str | None = None) -> None:
    """Refuse to read the design as having measured anything. Always raises.

    A design that is not built produces no reading. Any physical number
    from this apparatus is ``BLOCKED_MISSING_INPUT`` -- it needs a bench
    that does not exist here.
    """
    named = f" of {quantity}" if quantity else ""
    raise ApparatusError(
        f"refused: {claim!r}{named}. The apparatus is not built, so it has "
        f"measured nothing: there is no drive, no field, no transducer "
        f"charge, no demodulated amplitude or phase, and no temperature "
        f"log anywhere in this repository. Any physical number from this "
        f"apparatus is {BLOCKED_MISSING_INPUT}, pending a built and "
        f"calibrated bench. {PHYSICAL_VALIDATION}. {VERDICT}")


# --- report ---------------------------------------------------------------

def apparatus_report() -> dict:
    """The standing statement of what the apparatus design is and is not."""
    bom = bill_of_materials()
    return {
        "what_this_is": (
            "the P20/P21 apparatus -- drive coils, a piezo transducer, a "
            "mechanical fixture, a signal generator, a power amplifier, a "
            "low-noise preamp, a lock-in/heterodyne receiver and a "
            "temperature control -- as a preregistered DESIGN set with a "
            "bill of materials, connected excitation and readout chains, "
            "and a declared safety envelope"),
        "components": {name: c.as_dict() for name, c in DESIGN.items()},
        "n_components": len(DESIGN),
        "bill_of_materials": bom,
        "excitation_chain": [c.name for c in excitation_chain()],
        "readout_chain": [c.name for c in readout_chain()],
        "chains_connected": (chain_is_connected(EXCITATION_CHAIN)
                             and chain_is_connected(READOUT_CHAIN)),
        "safety_envelope": {
            "max_drive_voltage_vpp": SAFETY_ENVELOPE.max_drive_voltage_vpp,
            "max_drive_current_a": SAFETY_ENVELOPE.max_drive_current_a,
            "max_magnetic_field_mt": SAFETY_ENVELOPE.max_magnetic_field_mt,
            "temperature_range_c": [SAFETY_ENVELOPE.min_temperature_c,
                                    SAFETY_ENVELOPE.max_temperature_c],
        },
        "all_design_only": bom["all_design_only"],
        "refusals": [
            "refuse_design_as_built",
            "refuse_design_as_measurement",
            "check_safety never marks anything validated",
        ],
        "hardware_status": (
            f"{BLOCKED_MISSING_INPUT} - no coil, transducer, fixture, "
            f"generator, amplifier, preamp, receiver or thermostat exists "
            f"here; every component is a {DESIGN_ONLY} design line"),
        "claim_class": ENGINEERING_CANDIDATE,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_would_change_this": (
            "the components procured against their generic categories, the "
            "chains wired and their transfer functions measured in "
            "loopback, the safety envelope verified on the built hardware "
            "by a qualified operator, and each drive setting cleared "
            "before any specimen is energised"),
        "what_this_does_not_say": (
            "It does not say the apparatus exists: every component is a "
            "DESIGN_ONLY line with a generic vendor category and an "
            "order-of-magnitude cost estimate, and none has been procured, "
            "assembled, powered, or read out. It does not say the "
            "apparatus measured anything -- there is no drive, field, "
            "transducer charge, demodulated signal or temperature log "
            "here, and any physical number is BLOCKED_MISSING_INPUT. That "
            "the excitation and readout chains connect on paper says "
            "nothing about what any stage would do to a real signal, "
            "because no stage exists. A check_safety pass is a statement "
            "about numbers against a declared bound, not a validation, an "
            "approval, or a clearance to energise anything. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASSES", "ENGINEERING_CANDIDATE",
    "BLOCKED_MISSING_INPUT", "DESIGN_ONLY", "FORBIDDEN_STATUSES",
    "EVIDENCE_CLASS", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "ApparatusError", "Component", "DESIGN", "component",
    "bill_of_materials", "EXCITATION_CHAIN", "READOUT_CHAIN",
    "excitation_chain", "readout_chain", "chain_is_connected",
    "SafetyEnvelope", "SAFETY_ENVELOPE", "check_safety",
    "refuse_design_as_built", "refuse_design_as_measurement",
    "apparatus_report",
]
