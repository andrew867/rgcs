"""A01 — source claim ingest and provenance.

The source material motivates hypotheses. It never overrides units,
established physics, controls, or evidence classes. This module
preserves the source's exact wording and dates as ``SOURCE_CLAIM``,
attaches the standing corrections, and makes promotion mechanical
rather than rhetorical: a claim can only rise up the evidence ladder
by presenting the evidence that rung requires.

The corrections are the point. Each records something the source says
that is either wrong as stated or right only under a narrower reading,
so the record carries the correction wherever the claim travels.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import ClaimBoundaryError, EVIDENCE_CLASSES, validate_evidence_class

SOURCE_ID = "SRC-JH-DAN-2024-FRACTAL-4096-001"

#: Dates carried verbatim from the source record.
SOURCE_DATES = ("2024-04-21", "2024-05-30", "2024-07-18", "2024-08-31")

#: Exact source wording, preserved. Do not paraphrase these strings.
SOURCE_CLAIMS = (
    "4096 is described as a fractal core measure of visible-light "
    "frequency.",
    "2.45 GHz is described as the frequency of water.",
    "4096 and 64 are linked to a 64-tetrahedron grid.",
    "0.0356521923094988 is supplied as the fractal relationship "
    "between 2.45 GHz and the scale hierarchy.",
)


@dataclass(frozen=True)
class Correction:
    id: str
    subject: str
    source_says: str
    correction: str
    basis: str


#: Standing corrections (pack data/source_claim.json + core/04).
CORRECTIONS = (
    Correction(
        "CSPC-CORR-001", "water / 2.45 GHz",
        "2.45 GHz is the frequency of water.",
        "2.45 GHz is NOT a unique fundamental resonance of water. It "
        "is an ISM band chosen for regulatory and engineering reasons. "
        "Liquid water's dielectric loss is broad and has no sharp "
        "resonance there; the Debye relaxation peak of bulk water at "
        "room temperature lies near ~20 GHz. Microwave ovens use "
        "2.45 GHz for penetration depth and component economics, not "
        "because it is water's resonance.",
        "dielectric relaxation spectroscopy; ITU ISM band allocation"),
    Correction(
        "CSPC-CORR-002", "units of the fractal relationship",
        "0.0356521923094988 is the fractal relationship between "
        "2.45 GHz and the scale hierarchy.",
        "The recovered quantity retains HERTZ units: it is "
        "2.45e9 Hz / 2^36 = 0.03565219230949878692626953125 Hz, the "
        "least-significant-bit step of a 36-bit accumulator clocked at "
        "2.45 GHz. It is a frequency, not a dimensionless ratio.",
        "cspc.exact.DDS_36BIT_LSB; dimensional audit (cspc.units)"),
    Correction(
        "CSPC-CORR-003", "powers-of-eight level naming",
        "the 11th level is an 11th octave.",
        "An octave is a factor of 2. The 11th powers-of-EIGHT level is "
        "8^11 = 2^33, i.e. thirty-three octaves, not eleven. Calling it "
        "an 11th octave understates the span by 22 octaves.",
        "definition of octave; 8^n = 2^(3n)"),
    Correction(
        "CSPC-CORR-004", "arithmetic vs physics",
        "these relationships connect the domains.",
        "Arithmetic relationships do not establish coupling, energy "
        "transfer, or spacetime travel. An exact ratio between two "
        "numbers is a fact about the numbers.",
        "cspc transfer firewalls ARITHMETIC_TO_SPECTRUM, "
        "SPECTRUM_TO_COUPLING, TEMPORAL_ORDER_TO_TRAVEL"),
    Correction(
        "CSPC-CORR-005", "precision inheritance",
        "the derived value is 0.0356521923094988 (16 digits).",
        "Source precision does not confer measurement precision. The "
        "input 2.45 GHz is nominal, carrying three significant "
        "figures. The quotient is exact ARITHMETIC to any number of "
        "digits, but its empirical significance remains three figures. "
        "Quoting sixteen digits as a physical fact is an overclaim.",
        "transfer firewall SOURCE_PRECISION_TO_MEASUREMENT_PRECISION; "
        "cspc.units.Quantity.precision_audit"),
)


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    dates: tuple
    claims: tuple
    evidence_class: str = "SOURCE_CLAIM"
    scientific_status: str = (
        "preserved as source context; not established physics")
    corrections: tuple = field(default=CORRECTIONS)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "evidence_class": self.evidence_class,
            "dates": list(self.dates),
            "claims": list(self.claims),
            "scientific_status": self.scientific_status,
            "corrections": [
                {"id": c.id, "subject": c.subject,
                 "source_says": c.source_says,
                 "correction": c.correction, "basis": c.basis}
                for c in self.corrections],
            "claim_boundary":
                "SOURCE_CLAIM only. No claim here is a measurement, a "
                "derivation, or evidence of coupling. Corrections "
                "travel with the claims.",
        }


def source_record() -> SourceRecord:
    return SourceRecord(SOURCE_ID, SOURCE_DATES, SOURCE_CLAIMS)


def correction(cid: str) -> Correction:
    for c in CORRECTIONS:
        if c.id == cid:
            return c
    raise KeyError(cid)


#: What each rung of the ladder demands before a claim may occupy it.
PROMOTION_REQUIREMENTS = {
    "DERIVED_ARITHMETIC": "an exact derivation from stated inputs",
    "ANALYTIC_MODEL": "a named equation with declared domain and units",
    "NUMERICAL_SIMULATION": "a specified model, seed, and convergence "
                            "statement",
    "SYNTHETIC_RUN": "a generated dataset explicitly marked SYNTHETIC",
    "BENCH_MEASUREMENT": "a calibrated instrument record with apparatus "
                         "provenance, controls, and uncertainty",
    "REPLICATED_MEASUREMENT": "an independent bench result from a "
                              "separate operator/apparatus",
}


def promote(claim_id: str, from_class: str, to_class: str,
            evidence: str | None = None) -> dict:
    """Move a claim up the ladder — only with the evidence that rung
    requires.

    Refuses silent promotion, which is the failure mode this whole
    programme exists to prevent: a SOURCE_CLAIM becoming a fact because
    it was repeated in enough documents.
    """
    validate_evidence_class(from_class)
    validate_evidence_class(to_class)
    order = list(EVIDENCE_CLASSES)
    if order.index(to_class) <= order.index(from_class):
        raise ClaimBoundaryError(
            f"{to_class} is not a promotion from {from_class}")
    need = PROMOTION_REQUIREMENTS.get(to_class)
    if need and not evidence:
        raise ClaimBoundaryError(
            f"cannot promote {claim_id} to {to_class} without evidence: "
            f"requires {need}")
    return {"claim_id": claim_id, "from": from_class, "to": to_class,
            "evidence": evidence, "requirement": need}


def load_pack_source(path: str | Path) -> dict:
    """Read the pack's source_claim.json and confirm our in-repo record
    preserves it (wording and dates must not drift)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rec = source_record()
    return {
        "pack_source_id": data.get("source_id"),
        "matches_id": data.get("source_id") == rec.source_id,
        "matches_dates": tuple(data.get("dates", ())) == rec.dates,
        "matches_claims": tuple(data.get("claims", ())) == rec.claims,
        "pack_required_corrections": data.get("required_corrections", []),
    }
