"""P08 - material, environmental and orientation controls.

The claim under test in R6 is a *difference*: that some response depends
on the specimen, or on how the specimen is pointed. A difference is only
a difference against something. This module holds the somethings.

Three families of control, in ascending order of how much they can save
you from yourself:

    MATERIAL      is the response a property of the specimen?
    ORIENTATION   is the response a property of the pointing?
    ENVIRONMENTAL is the response a property of the room?

and one control that outranks all of them - the EMPTY MOUNT. An
apparatus with no specimen in it still has coils, amplifiers, cables,
mounts, thermal mass and an operator. Everything the instrument does by
itself appears in the empty-mount condition, and any specimen result
that does not exceed it is an apparatus result wearing a crystal.

The orientation lane implements claim R6-C-003 ("the crystal must be
perpendicular to the planet's surface, in alignment with the planet's
center core"). That is a testable statement: it predicts a response that
depends on the angle between the crystal axis and the local geomagnetic
vector. It is tested against an orientation null, and the order in which
orientations are presented is randomized, because thermal drift is
monotonic in time and a fixed orientation order aliases drift straight
into the orientation axis.

Nothing here is bench data. No specimen has been mounted, no orientation
has been swept, no environmental channel has been logged. Every function
either describes a required design or operates on numbers the caller
supplied.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict

from . import ORDINARY_CHANNELS

#: Roles a material may play in the design.
MATERIAL_ROLES = (
    "SPECIMEN",
    "PARITY_CONTROL",
    "STRUCTURE_CONTROL",
    "PIEZOELECTRIC_CONTROL",
    "FIXTURE_CONTROL",
    "APPARATUS_CONTROL",
)


class ControlRefused(RuntimeError):
    """Raised when a design cannot be certified as controlled."""


# --------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------

@dataclass(frozen=True)
class MaterialControl:
    """One material in the design, and what its presence rules out.

    Fields follow data/MATERIAL_CONTROL_MATRIX.csv. ``control_property``
    is the single property that makes this material informative;
    ``rules_out`` names the alternative explanations that survive if the
    material is *absent* from the design.
    """

    material_id: str
    common_name: str
    role: str
    long_range_order: bool
    local_tetrahedral_order: str
    piezoelectric: bool
    #: "left", "right" or "none".
    crystal_handedness: str
    control_property: str
    rules_out: tuple[str, ...]
    #: True for the specimen under test rather than a control.
    is_specimen: bool = False
    #: True only for the no-specimen condition.
    is_empty_mount: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if self.role not in MATERIAL_ROLES:
            raise ValueError(f"unknown material role {self.role!r}")
        if self.crystal_handedness not in ("left", "right", "none"):
            raise ValueError(
                f"handedness must be left/right/none, got "
                f"{self.crystal_handedness!r}")
        if self.is_empty_mount and self.is_specimen:
            raise ValueError("the empty mount is not a specimen")
        if not self.rules_out:
            raise ValueError(
                f"{self.material_id}: a control that rules nothing out "
                f"is not a control")

    @property
    def amorphous(self) -> bool:
        """No long-range crystalline order.

        The point of an amorphous comparator: it can be matched in bulk
        permittivity and composition while having no crystal chirality
        and no piezoelectricity at all.
        """
        return not self.long_range_order

    def as_record(self) -> dict:
        d = asdict(self)
        d["rules_out"] = list(self.rules_out)
        d["amorphous"] = self.amorphous
        return d


MATERIAL_CONTROLS: tuple[MaterialControl, ...] = (
    MaterialControl(
        material_id="left_alpha_quartz",
        common_name="alpha-quartz, left-handed",
        role="SPECIMEN",
        long_range_order=True,
        local_tetrahedral_order="SiO4",
        piezoelectric=True,
        crystal_handedness="left",
        control_property=(
            "the specimen under test: chiral, piezoelectric, "
            "long-range ordered"),
        rules_out=("nothing; this is the test condition",),
        is_specimen=True,
    ),
    MaterialControl(
        material_id="right_alpha_quartz",
        common_name="alpha-quartz, right-handed",
        role="PARITY_CONTROL",
        long_range_order=True,
        local_tetrahedral_order="SiO4",
        piezoelectric=True,
        crystal_handedness="right",
        control_property=(
            "identical in composition, permittivity, stiffness and "
            "piezoelectric magnitude; opposite crystal handedness"),
        rules_out=(
            "any response attributed to chirality that does not reverse "
            "with handedness",
            "composition, density and permittivity as the cause",
        ),
        is_specimen=True,
        notes=(
            "the enantiomer is the only control that isolates "
            "handedness; everything else about it is matched"),
    ),
    MaterialControl(
        material_id="fused_silica",
        common_name="fused silica (amorphous SiO2)",
        role="STRUCTURE_CONTROL",
        long_range_order=False,
        local_tetrahedral_order="local_SiO4_only",
        piezoelectric=False,
        crystal_handedness="none",
        control_property=(
            "same chemistry and similar permittivity as quartz, but no "
            "long-range order, no crystal chirality and no "
            "piezoelectricity"),
        rules_out=(
            "chemistry (SiO2) as the cause",
            "bulk permittivity and dielectric loss as the cause",
            "local tetrahedral coordination as the cause",
        ),
        notes=(
            "amorphous: retains SiO4 tetrahedra locally while having no "
            "crystal order, which separates 'tetrahedral' from "
            "'crystalline' in the source claims"),
    ),
    MaterialControl(
        material_id="calcite",
        common_name="calcite (CaCO3), non-piezoelectric crystal",
        role="PIEZOELECTRIC_CONTROL",
        long_range_order=True,
        local_tetrahedral_order="carbonate_planar",
        piezoelectric=False,
        crystal_handedness="none",
        control_property=(
            "a well-ordered, birefringent single crystal that is "
            "centrosymmetric in the relevant class and therefore not "
            "piezoelectric"),
        rules_out=(
            "crystallinity alone as the cause",
            "optical anisotropy as the cause",
            "any response that does not require piezoelectric coupling",
        ),
        notes=(
            "substitutable with any matched non-piezoelectric single "
            "crystal; the requirement is order without piezoelectricity"),
    ),
    MaterialControl(
        material_id="metal_blank",
        common_name="metal blank (conductive dummy)",
        role="FIXTURE_CONTROL",
        long_range_order=True,
        local_tetrahedral_order="metallic_close_packed",
        piezoelectric=False,
        crystal_handedness="none",
        control_property=(
            "matched mass and geometry, but conductive: it loads the "
            "coil, shields the interior and eddy-current damps the "
            "drive"),
        rules_out=(
            "coil loading and impedance change as the cause",
            "mass loading and mechanical mounting as the cause",
            "capacitive and inductive pickup by a body in the cage",
        ),
    ),
    MaterialControl(
        material_id="empty_mount",
        common_name="empty mount (no specimen)",
        role="APPARATUS_CONTROL",
        long_range_order=False,
        local_tetrahedral_order="none",
        piezoelectric=False,
        crystal_handedness="none",
        control_property=(
            "the apparatus running with nothing in it: coils, drive, "
            "amplifiers, cables, mount, thermal mass and operator all "
            "present, specimen absent"),
        rules_out=(
            "the entire instrument response",
            "drive crosstalk, amplifier drift and cable microphonics",
            "thermal drift of the fixture",
            "operator presence and room coupling",
        ),
        is_empty_mount=True,
        notes=(
            "the most important control in the design. It isolates "
            "apparatus response from specimen response; a specimen "
            "result that does not exceed the empty mount is an "
            "apparatus result"),
    ),
)


def material_registry() -> dict[str, MaterialControl]:
    """All materials by id. Raises if any id is duplicated."""
    out: dict[str, MaterialControl] = {}
    for m in MATERIAL_CONTROLS:
        if m.material_id in out:
            raise ValueError(f"duplicate material id {m.material_id!r}")
        out[m.material_id] = m
    return out


def specimens() -> tuple[MaterialControl, ...]:
    return tuple(m for m in MATERIAL_CONTROLS if m.is_specimen)


def controls() -> tuple[MaterialControl, ...]:
    return tuple(m for m in MATERIAL_CONTROLS if not m.is_specimen)


def empty_mount() -> MaterialControl:
    """The no-specimen condition.

    Kept as its own accessor because every completeness check in this
    module turns on whether the design contains it.
    """
    for m in MATERIAL_CONTROLS:
        if m.is_empty_mount:
            return m
    raise ControlRefused(
        "the material registry has no empty-mount condition; without it "
        "no specimen result can be separated from an apparatus result")


# --------------------------------------------------------------------
# Orientation - claim R6-C-003
# --------------------------------------------------------------------

#: The reference axes core/05 insists on keeping separate. The source
#: wording blends them; a response "follows" one of them only when
#: reversal and rotation tests say so.
REFERENCE_AXES = (
    "LOCAL_GRAVITY_PLUMB_VERTICAL",
    "GEOMAGNETIC_FIELD_VECTOR",
    "GEOGRAPHIC_NORTH",
    "CRYSTAL_C_AXIS",
    "CRYSTAL_HANDEDNESS",
    "COIL_CAGE_AXIS",
    "ACOUSTIC_PROPAGATION_DIRECTION",
    "OPTICAL_PROPAGATION_DIRECTION",
)

#: Orientation conditions. The first five are the geomagnetic sweep
#: that claim R6-C-003 requires; the remainder are the gravity and
#: geographic conditions from core/05, kept distinct because "vertical"
#: and "along the field" are different axes almost everywhere on Earth.
ORIENTATION_CONDITIONS = (
    "AXIS_PARALLEL_GEOMAGNETIC",
    "AXIS_ANTIPARALLEL_GEOMAGNETIC",
    "AXIS_ORTHOGONAL_GEOMAGNETIC_1",
    "AXIS_ORTHOGONAL_GEOMAGNETIC_2",
    "AXIS_RANDOMIZED",
    "AXIS_PARALLEL_GRAVITY",
    "AXIS_ANTIPARALLEL_GRAVITY",
    "AXIS_GEOGRAPHIC_NORTH",
    "AXIS_HORIZONTAL",
)


@dataclass(frozen=True)
class Orientation:
    """One mounting condition in the sweep."""

    condition: str
    reference_axis: str
    #: Angle between the crystal axis and the reference axis, degrees.
    #: ``None`` for the randomized condition, which has no fixed angle.
    angle_to_reference_deg: float | None
    role: str
    rationale: str

    def __post_init__(self) -> None:
        if self.condition not in ORIENTATION_CONDITIONS:
            raise ValueError(f"undeclared condition {self.condition!r}")
        if self.reference_axis not in REFERENCE_AXES:
            raise ValueError(f"unknown axis {self.reference_axis!r}")

    @property
    def aligned(self) -> bool:
        return self.angle_to_reference_deg == 0.0

    @property
    def anti_aligned(self) -> bool:
        return self.angle_to_reference_deg == 180.0

    @property
    def orthogonal(self) -> bool:
        return self.angle_to_reference_deg == 90.0

    @property
    def randomized(self) -> bool:
        return self.angle_to_reference_deg is None


@dataclass(frozen=True)
class OrientationControl:
    """The orientation discriminator for claim R6-C-003.

    The source says the crystal must stand perpendicular to the planet's
    surface and in line with its core, "regarding the electromagnetic
    field of the planet". Those are two different axes: the local plumb
    vertical and the geomagnetic vector differ by the magnetic
    inclination, which is far from zero nearly everywhere. R6 sweeps
    both and reports which one, if either, the response follows.
    """

    claim_id: str = "R6-C-003"
    primary_axis: str = "GEOMAGNETIC_FIELD_VECTOR"
    secondary_axis: str = "LOCAL_GRAVITY_PLUMB_VERTICAL"

    def orientation_matrix(self) -> tuple[Orientation, ...]:
        """The full sweep: aligned, anti-aligned, orthogonal, random.

        Two orthogonal conditions, not one. A single perpendicular
        mounting cannot distinguish an axial response from a response
        that merely picks out one particular room direction; two
        mutually perpendicular ones can.
        """
        B = "GEOMAGNETIC_FIELD_VECTOR"
        G = "LOCAL_GRAVITY_PLUMB_VERTICAL"
        N = "GEOGRAPHIC_NORTH"
        return (
            Orientation(
                condition="AXIS_PARALLEL_GEOMAGNETIC",
                reference_axis=B, angle_to_reference_deg=0.0,
                role="aligned",
                rationale=(
                    "the condition the source claims is required; "
                    "crystal axis along the local field vector")),
            Orientation(
                condition="AXIS_ANTIPARALLEL_GEOMAGNETIC",
                reference_axis=B, angle_to_reference_deg=180.0,
                role="anti-aligned",
                rationale=(
                    "reversal test. A genuinely field-coupled response "
                    "either reverses sign or is even in the field; both "
                    "are informative, and an unchanged response points "
                    "at the apparatus")),
            Orientation(
                condition="AXIS_ORTHOGONAL_GEOMAGNETIC_1",
                reference_axis=B, angle_to_reference_deg=90.0,
                role="orthogonal",
                rationale=(
                    "first perpendicular mounting; the projection onto "
                    "the field vector vanishes")),
            Orientation(
                condition="AXIS_ORTHOGONAL_GEOMAGNETIC_2",
                reference_axis=N, angle_to_reference_deg=90.0,
                role="orthogonal",
                rationale=(
                    "second perpendicular mounting, rotated 90 degrees "
                    "about the field vector from the first; separates "
                    "an axial response from a fixed room direction")),
            Orientation(
                condition="AXIS_RANDOMIZED",
                reference_axis=B, angle_to_reference_deg=None,
                role="randomized",
                rationale=(
                    "randomly drawn mountings supplying the null "
                    "distribution the other four are measured against")),
            Orientation(
                condition="AXIS_PARALLEL_GRAVITY",
                reference_axis=G, angle_to_reference_deg=0.0,
                role="aligned",
                rationale=(
                    "the 'perpendicular to the planet's surface' "
                    "reading, which is the gravity axis and not the "
                    "field axis")),
            Orientation(
                condition="AXIS_ANTIPARALLEL_GRAVITY",
                reference_axis=G, angle_to_reference_deg=180.0,
                role="anti-aligned",
                rationale="inverted mounting; separates up from down"),
            Orientation(
                condition="AXIS_GEOGRAPHIC_NORTH",
                reference_axis=N, angle_to_reference_deg=0.0,
                role="aligned",
                rationale=(
                    "geographic north differs from magnetic north by "
                    "the local declination; kept separate so the two "
                    "cannot be confused in reporting")),
            Orientation(
                condition="AXIS_HORIZONTAL",
                reference_axis=G, angle_to_reference_deg=90.0,
                role="orthogonal",
                rationale="crystal axis in the horizontal plane"),
        )

    def geomagnetic_sweep(self) -> tuple[Orientation, ...]:
        """Just the five conditions claim R6-C-003 is tested on."""
        return tuple(o for o in self.orientation_matrix()
                     if o.condition.endswith("GEOMAGNETIC")
                     or "GEOMAGNETIC_" in o.condition
                     or o.condition == "AXIS_RANDOMIZED")

    def local_field_reference(self) -> dict:
        """What the local geomagnetic field actually is.

        The number matters because it bounds the claim. The field at the
        Earth's surface is roughly 25-65 microtesla, it is quasi-static
        on the timescale of a bench run, and it is four to five orders
        of magnitude below the fields a laboratory electromagnet
        produces. A claimed dependence on this field has to exceed the
        orientation null before it is a dependence at all.
        """
        return {
            "quantity": "local geomagnetic flux density",
            "surface_range_microtesla": (25.0, 65.0),
            "typical_mid_latitude_microtesla": 50.0,
            "temporal_character": "QUASI_STATIC",
            "temporal_note": (
                "secular variation is a fraction of a percent per year "
                "and diurnal variation is tens of nanotesla; over a "
                "bench session the field is constant to well within the "
                "measurement, so orientation is the only thing the "
                "experimenter is varying"),
            "model_source": (
                "IGRF or WMM evaluated at the laboratory coordinates, "
                "checked against a measured local field. R6 ships "
                "neither model and computes no field value here"),
            "requirement": (
                "a claimed orientation dependence must exceed the "
                "orientation null of orientation_null(); an effect "
                "smaller than the null is an effect of the ordering, "
                "the drift or the mounting, not of the field"),
            "evidence_class": "SOURCE_CLAIM",
            "status": "NO_FIELD_MEASURED",
        }


def randomized_presentation_order(conditions: tuple[str, ...],
                                  *, n_repeats: int, seed: int
                                  ) -> tuple[str, ...]:
    """A randomized presentation order for the orientation sweep.

    Not decoration. Thermal drift, amplifier warm-up, humidity and
    operator fatigue are all monotonic or slowly varying in time. If
    orientations are presented in a fixed order, every one of those
    becomes perfectly confounded with orientation, and the resulting
    "orientation dependence" is a drift measurement with a compass
    glued to it. Randomizing the order converts that confound from a
    bias into variance the null can see.
    """
    if not conditions:
        raise ValueError("no conditions to order")
    if n_repeats < 1:
        raise ValueError("n_repeats must be at least 1")
    rng = random.Random(seed)
    order = list(conditions) * n_repeats
    rng.shuffle(order)
    return tuple(order)


def _group_means(labels: list[str], values: list[float]
                 ) -> dict[str, float]:
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for lab, v in zip(labels, values):
        sums[lab] = sums.get(lab, 0.0) + v
        counts[lab] = counts.get(lab, 0) + 1
    return {k: sums[k] / counts[k] for k in sums}


def _spread_statistic(labels: list[str], values: list[float]) -> float:
    """Max absolute deviation of a group mean from the grand mean.

    Chosen over an F statistic because it needs no distributional
    assumption and because the permutation null supplies the reference
    distribution anyway.
    """
    grand = sum(values) / len(values)
    means = _group_means(labels, values)
    return max(abs(m - grand) for m in means.values())


def orientation_null(responses: dict[str, list[float]],
                     *,
                     seed: int,
                     n_permutations: int = 2000) -> dict:
    """Permutation test over orientation labels.

    ``responses`` maps an orientation condition to the responses
    measured in it. The labels are shuffled ``n_permutations`` times and
    the spread statistic recomputed; the p-value is the fraction of
    shuffles reaching the observed spread. Under no true orientation
    effect this is approximately uniform on (0, 1], which is the
    property that makes it a null rather than a formality.

    The ``(1 + count) / (1 + n)`` form is used deliberately: it can
    never return exactly zero, because a finite permutation test cannot
    license "p = 0".
    """
    if len(responses) < 2:
        raise ValueError(
            "an orientation null needs at least two conditions; one "
            "condition compared to itself tests nothing")
    if n_permutations < 1:
        raise ValueError("n_permutations must be at least 1")

    labels: list[str] = []
    values: list[float] = []
    for cond, vals in responses.items():
        if not vals:
            raise ValueError(f"condition {cond!r} has no responses")
        labels.extend([cond] * len(vals))
        values.extend(float(v) for v in vals)

    observed = _spread_statistic(labels, values)

    rng = random.Random(seed)
    shuffled = list(labels)
    at_least = 0
    null: list[float] = []
    for _ in range(n_permutations):
        rng.shuffle(shuffled)
        s = _spread_statistic(shuffled, values)
        null.append(s)
        if s >= observed:
            at_least += 1

    p = (1.0 + at_least) / (1.0 + n_permutations)
    return {
        "test": "orientation_label_permutation",
        "conditions": tuple(responses),
        "n_observations": len(values),
        "n_permutations": n_permutations,
        "seed": seed,
        "statistic": observed,
        "null_mean": sum(null) / len(null),
        "null_max": max(null),
        "p": p,
        "group_means": _group_means(labels, values),
        "evidence_class": "ORDINARY_CHANNEL_RESULT",
        "note": (
            "this tests the orientation labels only. It does not "
            "control presentation order; use "
            "randomized_presentation_order() when acquiring, or the "
            "drift confound remains inside both the statistic and the "
            "null"),
    }


# --------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------

@dataclass(frozen=True)
class EnvironmentalControl:
    """One environmental variable, how it is held and how it is logged.

    A variable that is neither controlled nor recorded is a variable
    that will be blamed after the fact, when it is too late to check.
    """

    variable: str
    unit: str
    #: How the variable is held during a run.
    control_method: str
    #: How it is recorded, at what rate.
    logging_method: str
    #: Effects it could mimic if uncontrolled.
    mimics: tuple[str, ...]
    #: Ordinary channels (r6.ORDINARY_CHANNELS) it enters through.
    ordinary_channels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for c in self.ordinary_channels:
            if c not in ORDINARY_CHANNELS:
                raise ValueError(
                    f"{self.variable}: {c!r} is not one of the "
                    f"{len(ORDINARY_CHANNELS)} ordinary channels")
        if not self.mimics:
            raise ValueError(
                f"{self.variable}: an environmental variable that "
                f"mimics nothing needs no control entry")


ENVIRONMENTAL_CONTROLS: tuple[EnvironmentalControl, ...] = (
    EnvironmentalControl(
        variable="temperature",
        unit="K",
        control_method=(
            "enclosure with thermal mass; warm-up period before the "
            "first condition; no condition acquired during transients"),
        logging_method=(
            "calibrated sensors at specimen, mount and amplifier, "
            "logged at >= 1 Hz with the run clock"),
        mimics=(
            "apparent orientation dependence, when orientation order "
            "correlates with time",
            "drift in payload relaxation rate",
            "resonant frequency shift via elastic constants",
            "pyroelectric charge on the collector",
        ),
        ordinary_channels=("thermal_state", "crystal_charge",
                           "displacement_and_strain"),
    ),
    EnvironmentalControl(
        variable="humidity",
        unit="%RH",
        control_method=(
            "enclosure with desiccant or humidity control; recorded "
            "setpoint per run"),
        logging_method="calibrated hygrometer logged with the run clock",
        mimics=(
            "surface conduction changing apparent charge decay",
            "electrostatic accumulation and discharge events",
            "acoustic damping change",
        ),
        ordinary_channels=(
            "electrostatic_ion_ozone_humidity_airflow",
            "collector_charge", "sound_and_ultrasound"),
    ),
    EnvironmentalControl(
        variable="line_voltage",
        unit="V",
        control_method=(
            "regulated supply; drive and instrumentation on separate "
            "circuits; isolation transformer"),
        logging_method="mains voltage and drive rail logged per run",
        mimics=(
            "amplitude drift read as a specimen effect",
            "mains-harmonic features at 50/60 Hz and multiples",
            "apparent day/night effects tracking building load",
        ),
        ordinary_channels=("drive_voltage", "drive_current",
                           "environmental_and_instrumentation_crosstalk"),
    ),
    EnvironmentalControl(
        variable="vibration",
        unit="m/s^2",
        control_method=(
            "isolated table; specimen decoupled from pumps, fans and "
            "footfall; no condition acquired during building activity"),
        logging_method="triaxial accelerometer logged with the run clock",
        mimics=(
            "spurious mechanical resonance mistaken for a driven mode",
            "cable microphonics on high-impedance inputs",
            "apparent orientation dependence via mount stiffness "
            "changing with mounting angle",
        ),
        ordinary_channels=("displacement_and_strain",
                           "sound_and_ultrasound", "force_and_torque"),
    ),
    EnvironmentalControl(
        variable="electromagnetic_interference",
        unit="V/m and A/m",
        control_method=(
            "shielded enclosure; single-point ground; twisted and "
            "shielded leads; drive and sense separated"),
        logging_method=(
            "broadband field probe and a spectrum record per run, "
            "including a drive-off baseline"),
        mimics=(
            "direct drive crosstalk read as specimen response",
            "ground-loop signals synchronous with the drive",
            "radio and switching-supply pickup at fixed frequencies",
        ),
        ordinary_channels=(
            "electric_field", "magnetic_field",
            "environmental_and_instrumentation_crosstalk"),
    ),
    EnvironmentalControl(
        variable="operator_presence",
        unit="categorical",
        control_method=(
            "operator outside the enclosure during acquisition; fixed "
            "position when present; presence recorded as a covariate"),
        logging_method="presence and position logged per condition",
        mimics=(
            "body capacitance and thermal load coupling to the "
            "collector",
            "expectancy effects on setup, on which runs are kept and "
            "on where analysis stops",
            "airflow and humidity change near the specimen",
        ),
        ordinary_channels=(
            "collector_charge", "thermal_state",
            "electrostatic_ion_ozone_humidity_airflow"),
    ),
)


def environmental_registry() -> dict[str, EnvironmentalControl]:
    return {e.variable: e for e in ENVIRONMENTAL_CONTROLS}


def confound_matrix() -> dict[str, dict]:
    """Which environmental variable could mimic which claimed effect.

    Read it in the direction that hurts: for any claimed effect, this
    says what else produces it. That is the only direction in which a
    confound table is useful.
    """
    by_effect: dict[str, list[str]] = {}
    for e in ENVIRONMENTAL_CONTROLS:
        for m in e.mimics:
            by_effect.setdefault(m, []).append(e.variable)
    return {
        "by_variable": {
            e.variable: {
                "mimics": list(e.mimics),
                "ordinary_channels": list(e.ordinary_channels),
                "control_method": e.control_method,
                "logging_method": e.logging_method,
            }
            for e in ENVIRONMENTAL_CONTROLS
        },
        "by_effect": {k: sorted(v) for k, v in by_effect.items()},
        "note": (
            "every entry here is an alternative explanation that "
            "survives if the variable is unlogged. An unlogged variable "
            "cannot be excluded after the run, only argued about"),
    }


# --------------------------------------------------------------------
# Blinding
# --------------------------------------------------------------------

#: The blinding elements a certified design must carry.
REQUIRED_BLINDING = (
    "specimen_identity",
    "orientation",
    "drive_state",
    "analysis_preregistered",
    "randomized_order",
    "independent_decoding",
)


def blinding_protocol() -> dict:
    """The blinding R6 requires before any result is reportable.

    Blinding is not a courtesy to sceptics. Left-handed and right-handed
    quartz look identical; whether the operator *believes* they are
    looking at the special one is the single largest uncontrolled
    variable in an experiment of this kind, and it acts through a
    hundred small legitimate-feeling decisions about which runs to
    repeat and when to stop.
    """
    return {
        "elements": {
            "specimen_identity": {
                "requirement": (
                    "specimens are relabelled with opaque codes by "
                    "someone not running the apparatus; handedness, "
                    "material and the empty mount are indistinguishable "
                    "to the operator"),
                "why": (
                    "the enantiomers and the blanks are visually and "
                    "mechanically similar; expectation would otherwise "
                    "select which runs are kept"),
            },
            "orientation": {
                "requirement": (
                    "the mounting angle for each trial is issued from a "
                    "sealed randomization schedule; the operator sets "
                    "the fixture to a coded index, not to a named "
                    "condition"),
                "why": (
                    "the operator must not know which trial is the "
                    "'aligned' one the claim predicts"),
            },
            "drive_state": {
                "requirement": (
                    "drive on and sham drive are switched by the "
                    "schedule, not by the operator; the sham must match "
                    "the real drive in every observable the operator can "
                    "perceive, including audible tone, heat and "
                    "indicator state"),
                "why": (
                    "a sham that is detectable is not a sham; "
                    "'sham_drive' is one of the eighteen ordinary "
                    "channels for this reason"),
            },
            "analysis_preregistered": {
                "requirement": (
                    "the statistic, the exclusion rules, the stopping "
                    "rule and the null construction are written down, "
                    "hashed and timestamped before the first trial"),
                "why": (
                    "the v4.6 lesson: an analysis chosen after seeing "
                    "the data has an unbounded and unreportable "
                    "multiple-comparison cost"),
            },
            "randomized_order": {
                "requirement": (
                    "the presentation order of specimen, orientation and "
                    "drive state is randomized from a recorded seed; see "
                    "randomized_presentation_order()"),
                "why": (
                    "time-correlated drift aliases into any fixed "
                    "ordering"),
            },
            "independent_decoding": {
                "requirement": (
                    "the code-to-condition mapping is held by someone "
                    "who did not run the apparatus and is not "
                    "disclosed until the preregistered analysis has "
                    "been run on the coded data"),
                "why": (
                    "self-decoding reintroduces every bias the blind "
                    "removed, at the last possible moment"),
            },
        },
        "required": list(REQUIRED_BLINDING),
        "status": "DESIGN_ONLY",
        "note": (
            "no blinded run has been performed. This describes what "
            "would be required, not what was done"),
    }


# --------------------------------------------------------------------
# Completeness
# --------------------------------------------------------------------

#: Design requirements without which no result may be reported.
REQUIRED_DESIGN_ELEMENTS = (
    "empty_mount_control",
    "sham_drive",
    "randomized_order",
    "blinding",
)


def control_completeness(design: dict) -> dict:
    """Refuse to certify a design that is missing a required control.

    ``design`` is a mapping with:

        materials        iterable of material ids
        sham_drive       bool
        randomized_order bool
        blinding         iterable of blinding element names

    Returns a report naming everything that is missing. It does not
    raise: the caller is entitled to see all the gaps at once, and a
    partial design is a normal state during planning. What it will not
    do is return ``certified`` while a gap exists.
    """
    if not isinstance(design, dict):
        raise TypeError("design must be a mapping")

    missing: list[str] = []
    detail: dict[str, str] = {}

    registry = material_registry()
    materials = tuple(design.get("materials") or ())
    unknown = tuple(m for m in materials if m not in registry)

    mount = empty_mount()
    if mount.material_id not in materials:
        missing.append("empty_mount_control")
        detail["empty_mount_control"] = (
            f"the design does not include {mount.material_id!r}. "
            f"Without the no-specimen condition, every reported "
            f"specimen response also contains the apparatus response "
            f"and the two cannot be separated afterwards")

    if not design.get("sham_drive"):
        missing.append("sham_drive")
        detail["sham_drive"] = (
            "no sham-drive condition. 'sham_drive' is one of the "
            "eighteen ordinary channels; without it, drive crosstalk "
            "and operator expectation are unbounded")

    if not design.get("randomized_order"):
        missing.append("randomized_order")
        detail["randomized_order"] = (
            "presentation order is not randomized, so thermal and "
            "instrumental drift are confounded with condition")

    blinding = tuple(design.get("blinding") or ())
    missing_blinding = tuple(b for b in REQUIRED_BLINDING
                             if b not in blinding)
    if missing_blinding:
        missing.append("blinding")
        detail["blinding"] = (
            "blinding incomplete; missing "
            + ", ".join(missing_blinding))

    missing_materials = tuple(
        m.material_id for m in MATERIAL_CONTROLS
        if not m.is_specimen and m.material_id not in materials)

    return {
        "certified": not missing,
        "status": ("DESIGN_CONTROLLED" if not missing
                   else "DESIGN_REFUSED_INCOMPLETE_CONTROLS"),
        "missing": missing,
        "missing_detail": detail,
        "missing_blinding": list(missing_blinding),
        "missing_controls": list(missing_materials),
        "unknown_materials": list(unknown),
        "required": list(REQUIRED_DESIGN_ELEMENTS),
        "note": (
            "certification here means the design carries its controls. "
            "It is not a statement about any result, and no run has "
            "been performed"),
    }


def refuse_uncontrolled_report(design: dict, claim: str = ""):
    """Always refuses when the design is incomplete.

    The companion to :func:`control_completeness` for callers that want
    a hard stop rather than a report.
    """
    rep = control_completeness(design)
    if rep["certified"]:
        return rep
    raise ControlRefused(
        f"refusing to report {claim or 'a result'} from a design "
        f"missing: {', '.join(rep['missing'])}. "
        f"{rep['missing_detail'].get(rep['missing'][0], '')}")


def control_records() -> list[dict]:
    """Flat records for the canonical store / workbook."""
    return [m.as_record() for m in MATERIAL_CONTROLS]
