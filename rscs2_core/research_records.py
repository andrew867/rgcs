"""Shared research-record schemas + safety gates (Agents D01/S01 of
the master expansion programme; pack 42/43).

One typed factory covers the 25 record kinds with the common-field
contract; kind-specific rules enforce the measurement, frequency, and
consciousness-layer disciplines. Safety limits are machine-readable
and every experiment protocol must pass `safety_gate` before it can be
marked PROTOCOL_READY."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

SCHEMA_VERSION = "rgcs.v4x.record.1"

RECORD_KINDS = (
    "SourceRecord", "EquationRecord", "FrequencyKeyRecord",
    "TimingCandidateRecord", "GeometryMotifRecord", "SpecimenRecord",
    "MaterialCapabilityRecord", "ApparatusRecord", "InstrumentRecord",
    "CalibrationRecord", "SafetyLimitRecord",
    "ExperimentProtocolRecord", "PreregistrationRecord", "RunRecord",
    "RawObservationRecord", "ParticipantRecord", "WaterSampleRecord",
    "ResultEnvelope", "HypothesisRecord", "FalsificationRecord",
    "ConsciousnessLayerRecord", "CoverageLedgerRecord",
    "ProofArtifactRecord", "DefectRecord", "ReleaseManifest")

STATUS_CLASSES = (
    "CORE_VALIDATED", "REDUCED_ORDER_VALIDATED",
    "EXPERIMENTALLY_MEASURED", "EXPERIMENTALLY_NULL",
    "INTERFACE_ONLY", "MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL",
    "CANDIDATE_NEW_COUPLING", "SOURCE_HYPOTHESIS",
    "ENGINEERING_PROTOTYPE", "NOT_APPLICABLE",
    "INSUFFICIENT_RESOLUTION", "INCONCLUSIVE",
    "PROTOCOL_READY_HARDWARE_REQUIRED", "ETHICS_APPROVAL_REQUIRED")

EVIDENCE_TAGS = ("EST", "DER", "MEAS", "HYP", "SRC", "ENG", "NULL")

FREQUENCY_KINDS = ("exact_physical_frequency", "arithmetic_motif",
                   "source_label", "harmonic_relation",
                   "timing_inverse", "dimensionless_ratio",
                   "angle_derived_motif", "non_frequency_value")

CONSCIOUSNESS_LAYERS = ("metaphor", "mathematical_model",
                        "established_cognitive_evidence",
                        "speculative_biological_mechanism",
                        "speculative_external_field_mechanism",
                        "first_person_phenomenology", "private_myth",
                        "engineering_analogy")


class RecordError(ValueError):
    pass


def make_record(kind: str, record_id: str, title: str, lane: str,
                status: str, evidence_tags: list, **fields) -> dict:
    """Typed record factory with the common-field contract and
    kind-specific rules."""
    if kind not in RECORD_KINDS:
        raise RecordError(f"unknown record kind {kind}")
    if status not in STATUS_CLASSES:
        raise RecordError(f"unknown status {status}")
    bad = set(evidence_tags) - set(EVIDENCE_TAGS)
    if bad:
        raise RecordError(f"unknown evidence tags {bad}")
    rec = {
        "schema_version": SCHEMA_VERSION, "kind": kind,
        "record_id": record_id, "title": title, "lane": lane,
        "status": status, "evidence_tags": sorted(evidence_tags),
        "source_ids": fields.pop("source_ids", []),
        "equation_ids": fields.pop("equation_ids", []),
        "units": fields.pop("units", {}),
        "assumptions": fields.pop("assumptions", []),
        "uncertainty": fields.pop("uncertainty", {}),
        "controls": fields.pop("controls", []),
        "failure_conditions": fields.pop("failure_conditions", []),
        "public": fields.pop("public", True),
        "warnings": fields.pop("warnings", []),
    }
    # measurement rules: MEAS requires the full provenance block and
    # synthetic data can never carry MEAS
    if "MEAS" in rec["evidence_tags"]:
        required = ("raw_hash", "instrument", "calibration_id",
                    "protocol_version", "randomization", "blinding",
                    "safety_gate_id")
        missing = [k for k in required if k not in fields]
        if missing:
            raise RecordError(
                f"MEAS record missing {missing} (measurement rules)")
        if fields.get("synthetic"):
            raise RecordError(
                "synthetic data cannot be relabeled measured")
    if fields.get("synthetic") and status == \
            "EXPERIMENTALLY_MEASURED":
        raise RecordError("synthetic data cannot be "
                          "EXPERIMENTALLY_MEASURED")
    # frequency rules
    if kind == "FrequencyKeyRecord":
        fk = fields.get("frequency_kind")
        if fk not in FREQUENCY_KINDS:
            raise RecordError(
                f"FrequencyKeyRecord requires frequency_kind in "
                f"{FREQUENCY_KINDS}, got {fk}")
    # consciousness rules
    if kind == "ConsciousnessLayerRecord":
        layer = fields.get("layer")
        if layer not in CONSCIOUSNESS_LAYERS:
            raise RecordError(f"layer must be one of "
                              f"{CONSCIOUSNESS_LAYERS}")
        if layer in ("metaphor", "private_myth",
                     "first_person_phenomenology") and \
                status not in ("SOURCE_HYPOTHESIS",):
            raise RecordError(
                "metaphor/myth/phenomenology layers are capped at "
                "SOURCE_HYPOTHESIS (no automatic promotion)")
    # hypothesis rules
    if kind in ("HypothesisRecord", "FalsificationRecord"):
        if not fields.get("falsification_condition"):
            raise RecordError(f"{kind} requires a "
                              "falsification_condition")
    rec.update(fields)
    return rec


def dumps(rec: dict) -> str:
    return json.dumps(rec, sort_keys=True, indent=2, default=str)


# --- S01: safety limits and gates ---------------------------------------

#: frozen envelopes (v3 D6/D7) + expansion-programme additions
SAFETY_LIMITS = {
    "electrical": {"max_voltage_v": 30.0, "max_current_a": 3.0,
                   "max_pulse_energy_mj": 5.0,
                   "isolation": "battery or isolation transformer; "
                                "current-limited supply; "
                                "dummy-load-first"},
    "optical": {"max_class": "3R", "max_power_mw": 5.0,
                "interlock_required": True},
    "acoustic": {"max_spl_dba": 85.0,
                 "ultrasound_max_spl_db_re20u": 110.0,
                 "note": "hearing protection above 80 dBA; no "
                         "focused airborne ultrasound at operators"},
    "coil_thermal": {"max_surface_temp_c": 50.0,
                     "max_continuous_current_a": 1.0},
    "human_subjects": {"ethics_approval_required": True,
                       "consent_required": True,
                       "withdrawal_anytime": True,
                       "privacy": "identifiers separated from data; "
                                  "participant records private",
                       "no_medical_claims": True},
    "water_fluids": {"no_ingestion": True,
                     "no_therapeutic_claims": True,
                     "spill_and_electrical_separation": True},
}


def safety_gate(protocol: dict) -> dict:
    """Evaluate a protocol record against the safety contract.
    Returns {passed, blockers, required_status}. Human-subject
    protocols can never pass beyond ETHICS_APPROVAL_REQUIRED here."""
    blockers = []
    kind = protocol.get("campaign_kind", "")
    limits = protocol.get("declared_limits", {})
    if protocol.get("uses_mains_voltage"):
        blockers.append("mains voltage prohibited (electrical "
                        "envelope: <=30 V isolated)")
    if limits.get("voltage_v", 0) > \
            SAFETY_LIMITS["electrical"]["max_voltage_v"]:
        blockers.append("voltage exceeds 30 V envelope")
    if limits.get("current_a", 0) > \
            SAFETY_LIMITS["electrical"]["max_current_a"]:
        blockers.append("current exceeds 3 A envelope")
    if limits.get("spl_dba", 0) > \
            SAFETY_LIMITS["acoustic"]["max_spl_dba"]:
        blockers.append("SPL exceeds 85 dBA envelope")
    if kind in ("human_loading", "operator_state") and not \
            protocol.get("ethics_approval_id"):
        return {"passed": False, "blockers": blockers,
                "required_status": "ETHICS_APPROVAL_REQUIRED",
                "note": "human-subject campaigns are blocked on "
                        "ethics approval regardless of engineering "
                        "safety"}
    if kind == "water" and not protocol.get("no_ingestion_ack"):
        blockers.append("water protocols must acknowledge "
                        "no-ingestion/no-therapeutic-claims")
    passed = not blockers
    return {"passed": passed, "blockers": blockers,
            "required_status": "PROTOCOL_READY_HARDWARE_REQUIRED"
            if passed else "BLOCKED_SAFETY"}
