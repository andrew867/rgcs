"""RGCS v4.9 R6 — Dynamic Helicity, Quartz Magnetochiral Response,
Metric-Indexed Witness Memory, Recursive Barycentric Mailbox Routing,
Information-Carrier Transduction, and Planetary Grid Audit.

    Source wording is preserved.
    Ordinary mechanisms are modeled first.
    Every reversal is measured.
    Every headline has a null.
    Residual is not ontology.

The central R6 correction (00_START_HERE, core/11):

    A decaying memory is not automatically a spacetime sensor.

Memory relaxation arises from temperature, magnetic and electric
fields, strain, radiation, chemical change, read disturb, device
aging, clock drift and calibration loss. A module becomes a
relativistic witness only when it contains an independently
characterized clock-like transition or oscillator, records
environmental nuisance channels, preserves calibration and
cryptographic provenance, and is compared against another reference
through a declared worldline and transfer path.

Extends cspc/ (units, nulls), pmwr/ (phase authority), r3/ (root
space, atlas), r4/ (exact address, codec, platforms). Nothing here is
physical evidence: no coil has been wound, no crystal driven, no spin
written, no clock compared.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0.0"
PROGRAMME_ID = "RGCS-V4.9-R6"

#: Clock/metrology promotion ladder (core/11). Terminates below any
#: state that would claim direct access to spacetime structure.
WITNESS_CLASSES = (
    "CLOCK_MODEL",
    "CLOCK_CALIBRATED",
    "CLOCK_COMPARISON",
    "PROPER_TIME_MODEL_FIT",
    "RELATIVISTIC_SHIFT_CONSISTENT",
    "INDEPENDENTLY_REPLICATED_METROLOGY",
)

#: Nuisance channels a witness comparison must record (core/11). A
#: comparison that omits any of these cannot be promoted past
#: CLOCK_COMPARISON.
NUISANCE_CHANNELS = (
    "clock_instability",
    "temperature",
    "magnetic_field",
    "electric_field",
    "acceleration",
    "vibration",
    "strain",
    "radiation",
    "optical_path",
    "electronic_latency",
    "transfer_link_phase",
    "readout_back_action",
    "device_aging",
)

#: Navigation observability statuses (core/14). The last is terminal:
#: nothing promotes out of it inside R6.
NAVIGATION_STATUSES = (
    "DEAD_RECKONING",
    "MAP_AIDED_NAVIGATION",
    "CLOCK_AIDED_GEODESY",
    "GRAVITY_GRADIENT_AIDED",
    "CELESTIAL_AIDED",
    "POSITION_BOUNDED",
    "POSITION_UNOBSERVABLE",
    "SOVEREIGN_NAVIGATION_UNSUPPORTED",
)

#: Phryll promotion ladder (core/07). Unchanged from v4.7: there is no
#: PHRYLL_DETECTED state and adding one is a test failure.
PHRYLL_CLASSES = (
    "SOURCE_CLAIM",
    "OPERATIONAL_HYPOTHESIS",
    "ORDINARY_CHANNEL_RESULT",
    "UNEXPLAINED_INSTRUMENT_RESIDUAL",
    "REPLICATED_ANOMALY",
    "CANDIDATE_NEW_MECHANISM",
)

#: The eighteen ordinary channels that must be bounded before any
#: residual may be registered at all (core/07).
ORDINARY_CHANNELS = (
    "drive_voltage",
    "drive_current",
    "impedance_and_mutual_inductance",
    "electric_field",
    "magnetic_field",
    "crystal_charge",
    "displacement_and_strain",
    "sound_and_ultrasound",
    "optical",
    "thermal_state",
    "electrostatic_ion_ozone_humidity_airflow",
    "force_and_torque",
    "collector_charge",
    "oscillator_phase_and_frequency",
    "radiation",
    "chemistry_material_change",
    "environmental_and_instrumentation_crosstalk",
    "sham_drive",
)

#: Protocol maturity ladder (core/15). Authority follows adoption and
#: governance; it is never asserted by authorship.
PROTOCOL_MATURITY = (
    "EXPERIMENTAL_SCHEMA",
    "DRAFT_PROTOCOL",
    "REFERENCE_IMPLEMENTATION",
    "SECOND_INDEPENDENT_IMPLEMENTATION",
    "INTEROPERABILITY_DEMONSTRATED",
    "SECURITY_REVIEWED",
    "OPEN_GOVERNANCE",
    "CANDIDATE_STANDARD",
    "ADOPTED_STANDARD",
)

#: State names that must never exist anywhere in R6. Enforced by
#: tests/v49/test_r6_claim_language.py against the whole package.
FORBIDDEN_STATES = (
    "SPACETIME_FABRIC_DIRECTLY_READ",
    "PHRYLL_DETECTED",
    "METRIC_ACTUATED",
    "PORTAL_OPEN",
    "SOVEREIGN_NAVIGATION_ACHIEVED",
    "ADOPTED_STANDARD_BY_AUTHORSHIP",
    "CAUSAL_HISTORY_COMPLETE",
)

#: Tempting identifications R6 refuses, with the reason. Extends the
#: r3 FORBIDDEN_COLLAPSES table into the witness/mailbox domain.
FORBIDDEN_COLLAPSES = {
    "DECAY_IS_PROPER_TIME":
        "payload relaxation has at least twelve ordinary causes; the "
        "metric contribution is identifiable only after all of them "
        "are measured and bounded (core/11)",
    "CONFIDENCE_IS_A_CLOCK":
        "posterior confidence is a decoder statistic, not a phase "
        "accumulated by a characterized oscillator",
    "ADDRESS_IS_A_CHANNEL":
        "a barycentric key path names a destination; naming a "
        "destination establishes no coupling to it (core/12)",
    "ROOT_CERTIFICATE_RESTORES_INFORMATION":
        "a prior may regularize reconstruction; it cannot restore "
        "information the physical channel destroyed",
    "LOCAL_FIELD_IS_GLOBAL_POSITION":
        "a local scalar clock rate or uniform gravitational field "
        "does not uniquely identify global position (core/14)",
    "PUBLICATION_IS_STANDARDIZATION":
        "authority follows adoption, interoperability and governance, "
        "not authorship (core/15)",
    "RESIDUAL_IS_ONTOLOGY":
        "an unexplained instrument residual names a measurement that "
        "is not yet understood, not a substance",
}

#: Claims R6 refuses to test at all (core/09). Present so that the
#: refusal is inspectable data rather than an absence.
BIOLOGICAL_REFUSALS = (
    "dna_repair",
    "hydrogen_bonds_and_chromosomes",
    "regeneration",
    "reduced_food_requirements",
    "chakras",
    "gamma_brainwaves",
    "bodily_phryll_harvesting",
    "water_programming",
    "disease_treatment",
)

BIOLOGICAL_REFUSAL_REASON = (
    "R6 does not test biological or medical claims. No human or "
    "animal exposure, treatment, diagnosis or therapeutic "
    "recommendation is permitted. A future biological lane requires "
    "an independent medical/ethics programme, conventional "
    "mechanistic rationale, safety review, preregistration and "
    "institutional oversight (core/09)."
)

__all__ = [
    "SCHEMA_VERSION",
    "PROGRAMME_ID",
    "WITNESS_CLASSES",
    "NUISANCE_CHANNELS",
    "NAVIGATION_STATUSES",
    "PHRYLL_CLASSES",
    "ORDINARY_CHANNELS",
    "PROTOCOL_MATURITY",
    "FORBIDDEN_STATES",
    "FORBIDDEN_COLLAPSES",
    "BIOLOGICAL_REFUSALS",
    "BIOLOGICAL_REFUSAL_REASON",
]
