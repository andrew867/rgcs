"""A43-A54 — crystal geometry, the pyramid-ratio audit, bidirectional
transfer, excitation lanes, the translation matrix, the ordinary
output matrix, the energy ledger, and the Phryll latent registry.

The source hypothesis (source_claims/, preserved verbatim elsewhere):
an asymmetrically terminated crystal may act as a directional phase/
frequency translation device. In v4.7 that is a SOURCE_CLAIM with an
engineering lane around it — nothing here asserts the crystal does
any of it.

The geometry contract (core/07): for a square pyramid with half-base
a and face slope θ through the apothem, tanθ = h/a and 2a/h = 2/tanθ.
At 51.843°, 2a/h ≈ 1.5714158, numerically near π/2 ≈ 1.5707963. That
proximity is a GEOMETRY_IDENTITY observation about a chosen angle —
not a mechanism, and quoting it as one is refused.

No DETECTED-style Phryll state exists in this module or anywhere else
in v4.7; the registry's terminal success state is
``CANDIDATE_NEW_MECHANISM``, reachable only through independent
replication.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import ClaimBoundaryError, PHRYLL_LADDER

# --- geometry (A43/A44) ----------------------------------------------------

#: Angle candidates from the pack CSV, degrees. Controls included.
ANGLE_CANDIDATES = {
    "360_over_7": 360.0 / 7.0,
    "51_843": 51.843,
    "51_51_51_DMS": 51.0 + 51.0 / 60.0 + 51.0 / 3600.0,
    "Great_Pyramid_nominal": 51.84,
    "rounded_52": 52.0,
    "emitter_58": 58.0,
    "emitter_60": 60.0,
}


@dataclass(frozen=True)
class CrystalGeometry:
    """Schema for a terminated crystal body (A43). Every field the
    directional hypothesis depends on is explicit, so a bench record
    can never claim geometry it did not measure."""
    id: str
    length_mm: float
    top_termination_deg: float
    bottom_termination_deg: float
    c_axis_orientation_deg: float
    n_facets_top: int
    n_facets_bottom: int
    taper: bool
    material: str = "quartz"
    inclusions_note: str = ""
    fixture: str = ""
    provenance: str = ""
    evidence_class: str = "SOURCE_CLAIM"

    @property
    def asymmetric(self) -> bool:
        return self.top_termination_deg != self.bottom_termination_deg

    def reversed(self) -> "CrystalGeometry":
        """The mandatory both-orientations control (A45)."""
        return CrystalGeometry(
            self.id + "-REVERSED", self.length_mm,
            self.bottom_termination_deg, self.top_termination_deg,
            self.c_axis_orientation_deg, self.n_facets_bottom,
            self.n_facets_top, self.taper, self.material,
            self.inclusions_note, self.fixture,
            self.provenance + " | reversed control",
            self.evidence_class)


def pyramid_ratio(theta_deg: float) -> dict:
    """tanθ = h/a; 2a/h = 2/tanθ. Exact trig, GEOMETRY_IDENTITY."""
    t = math.tan(math.radians(theta_deg))
    return {"theta_deg": theta_deg, "h_over_half_base": t,
            "full_base_over_height": 2.0 / t}


def pyramid_ratio_audit() -> dict:
    """A44: every candidate angle with its ratios, the π/2 proximity
    stated for what it is, and the mechanism claim refused."""
    rows = {}
    for label, deg in ANGLE_CANDIDATES.items():
        r = pyramid_ratio(deg)
        rows[label] = {
            **r,
            "abs_diff_from_pi_over_2": abs(r["full_base_over_height"]
                                           - math.pi / 2),
        }
    closest = min(rows.items(),
                  key=lambda kv: kv[1]["abs_diff_from_pi_over_2"])
    return {
        "angles": rows,
        "closest_to_pi_over_2": closest[0],
        "pi_over_2": math.pi / 2,
        "observation":
            "2a/h at ~51.84-51.86 degrees sits within ~5e-4 of pi/2. "
            "This is a statement about a chosen angle's tangent",
        "not_a_mechanism":
            "numerical proximity of a ratio to pi/2 establishes no "
            "energy flow, no directionality, and no function "
            "(firewall PYRAMID_PROVES_MECHANISM). The Great Pyramid "
            "is an ANTHROPOGENIC_STRUCTURE; its slope is a design "
            "choice, not a physics constant.",
        "required_controls": list(ANGLE_CANDIDATES),
        "evidence_class": "GEOMETRY_IDENTITY",
    }


# --- excitation and outputs (A46-A53) ---------------------------------------

EXCITATIONS = ("ELECTRODE_PIEZO", "CROSSED_COIL", "ACOUSTIC",
               "OPTICAL", "MIXED", "ACTIVE_FEEDBACK")

#: The eleven ordinary output channels that must be bounded BEFORE any
#: residual talk (core/06).
OUTPUT_CHANNELS = (
    "electrical", "magnetic_near_field", "charge_impedance",
    "displacement_strain_vibration", "acoustic_ultrasonic",
    "temperature_heat_flow", "optical",
    "electrostatic_ions_ozone_air", "force_torque_mass_buoyancy",
    "chemistry_material", "crosstalk_environment",
)


@dataclass(frozen=True)
class ExcitationPlan:
    id: str
    kind: str
    drive_hz: float
    power_w: float
    feedback_loop_closed: bool = False
    energy_source: str = ""

    def __post_init__(self):
        if self.kind not in EXCITATIONS:
            raise ClaimBoundaryError(f"unknown excitation {self.kind!r}")
        if self.kind == "ACTIVE_FEEDBACK":
            if not self.feedback_loop_closed or not self.energy_source:
                raise ClaimBoundaryError(
                    "self-oscillation requires a closed feedback loop "
                    "AND a declared energy source; an oscillator "
                    "without a power source is a free-energy claim")


def translation_matrix_entry(input_domain: str, input_hz: float,
                             output_domain: str, output_hz: float,
                             mechanism: str) -> dict:
    """A51: one hypothesised (input -> output) translation. Every entry
    is a HYPOTHESIS with a named ordinary mechanism candidate; an entry
    with no mechanism is UNSUPPORTED, not mysterious."""
    known = ("piezoelectric_direct", "piezoelectric_converse",
             "photoelastic", "photothermal", "acousto_optic_sideband",
             "electrostriction", "nonlinear_mixing", "thermal",
             "NONE_PROPOSED")
    if mechanism not in known:
        raise ClaimBoundaryError(f"unknown mechanism {mechanism!r}")
    return {
        "input": {"domain": input_domain, "hz": input_hz},
        "output": {"domain": output_domain, "hz": output_hz},
        "mechanism_candidate": mechanism,
        "status": "UNSUPPORTED" if mechanism == "NONE_PROPOSED"
        else "OPERATIONAL_HYPOTHESIS",
        "evidence_class": "SOURCE_CLAIM" if mechanism == "NONE_PROPOSED"
        else "ANALYTIC_MODEL",
        "note": "a hypothesised translation; no transfer has been "
                "measured",
    }


def output_matrix_template() -> dict:
    """A53: the synchronized multi-sensor record every bench run must
    fill. A channel left None is UNMEASURED — and an unmeasured
    channel blocks residual claims."""
    return {ch: None for ch in OUTPUT_CHANNELS}


# --- energy ledger (A54) -----------------------------------------------------

def energy_ledger(power_in_w: dict, power_out_w: dict) -> dict:
    """Power accounting with the free-energy refusal.

    Output exceeding input beyond uncertainty is an ACCOUNTING ERROR
    until proven otherwise — the ledger refuses to bless it.
    """
    pin = sum(power_in_w.values())
    pout = sum(v for v in power_out_w.values() if v is not None)
    unmeasured = [k for k, v in power_out_w.items() if v is None]
    if pin <= 0:
        raise ClaimBoundaryError("no declared input power; every "
                                 "output needs a source")
    ratio = pout / pin
    verdict = "CONSISTENT" if ratio <= 1.0 else "ACCOUNTING_ERROR"
    return {
        "power_in_w": pin, "power_out_accounted_w": pout,
        "unmeasured_channels": unmeasured,
        "efficiency_bound": ratio,
        "verdict": verdict,
        "note": ("output>input is treated as measurement or "
                 "accounting error (firewall DEVICE_MIRACLES); it is "
                 "never reported as free energy" if verdict ==
                 "ACCOUNTING_ERROR" else
                 "all accounted output within input"),
        "evidence_class": "ANALYTIC_MODEL",
    }


# --- Phryll latent registry (A52) ---------------------------------------------

@dataclass(frozen=True)
class LatentEntry:
    """One unresolved source-attributed output. Its state can only walk
    the PHRYLL_LADDER, each step gated on the evidence that arrow
    requires. There is no DETECTED state."""
    id: str
    description: str
    state: str = "SOURCE_CLAIM"
    history: tuple = field(default=())

    def __post_init__(self):
        if self.state not in PHRYLL_LADDER:
            raise ClaimBoundaryError(
                f"{self.state!r} is not on the Phryll ladder; "
                "DETECTED-style states do not exist in v4.7")


#: What each promotion arrow demands (core/06).
PROMOTION_GATES = {
    "OPERATIONAL_HYPOTHESIS":
        "a preregistered, falsifiable operational definition",
    "UNEXPLAINED_INSTRUMENT_RESIDUAL":
        "ALL eleven ordinary output channels measured and bounded, "
        "calibration current, controls (incl. sham-drive) run, energy "
        "accounted",
    "REPLICATED_ANOMALY":
        "independent replication: different operator, different "
        "apparatus, preregistered protocol",
    "CANDIDATE_NEW_MECHANISM":
        "replicated anomaly plus a falsifiable model making a "
        "prospective prediction that survives",
}


def promote_latent(entry: LatentEntry, to_state: str,
                   evidence: dict | None) -> LatentEntry:
    ladder = list(PHRYLL_LADDER)
    if to_state not in ladder:
        raise ClaimBoundaryError(f"{to_state!r} is not on the ladder")
    if ladder.index(to_state) != ladder.index(entry.state) + 1:
        raise ClaimBoundaryError(
            f"{entry.state} -> {to_state} skips a rung; promotion is "
            "one arrow at a time")
    gate = PROMOTION_GATES[to_state]
    if not evidence:
        raise ClaimBoundaryError(
            f"promotion to {to_state} requires: {gate}")
    if to_state == "UNEXPLAINED_INSTRUMENT_RESIDUAL":
        matrix = evidence.get("output_matrix", {})
        missing = [ch for ch in OUTPUT_CHANNELS
                   if matrix.get(ch) is None]
        if missing:
            raise ClaimBoundaryError(
                "cannot register a residual with unmeasured ordinary "
                f"channels: {missing} (firewall SENSOR_CHANGE_IS_PHRYLL)")
        if not evidence.get("sham_control_run"):
            raise ClaimBoundaryError(
                "sham-drive control missing. The source itself records "
                "an episode where an effect was reported before anyone "
                "noticed output power was not engaged; that is the "
                "expectation-effect warning this gate encodes.")
    if to_state == "REPLICATED_ANOMALY" and not \
            evidence.get("independent_replication"):
        raise ClaimBoundaryError(
            "replication requires a different operator and apparatus")
    return LatentEntry(entry.id, entry.description, to_state,
                       entry.history + ((entry.state, to_state,
                                         str(sorted(evidence))),))
