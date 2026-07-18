"""A05/A06/A09/A10 — narrative ingest, novelty boundary, and the
frozen evaluation contract.

The operator's intuition note is preserved VERBATIM and hash-pinned:
later work may translate, narrow, or reject it, but may not rewrite it
as a prediction made after results. The evaluation metrics for the
recovery lane are frozen here, before any estimator was tuned against
them, exactly as the v4.6 simplicity metric was.
"""

from __future__ import annotations

import hashlib

#: The operator note, verbatim (source_claims/OPERATOR_LOST_CHANNEL_NOTE).
#: Immutable: the pinned hash below fails the suite if a word changes.
OPERATOR_NOTE = (
    "The crystal is a phase translation device. The ratio is the top "
    "to bottom and the Great Pyramid angle. It brings the Phryll in "
    "from one end and moves it via frequency translation and "
    "excitation from self-oscillations of the crystal induced from "
    "the coils and/or photonic light, or phonons acoustically."
)
OPERATOR_NOTE_STATUS = ("LORE", "HYPOTHESIS_SEED")


def operator_note_fingerprint() -> str:
    return hashlib.sha256(OPERATOR_NOTE.encode("utf-8")).hexdigest()


#: Source-narrative elements (source_claims/PHRYLL_SOURCE_TRANSLATION),
#: each entering as SOURCE_CLAIM with its scientific translation.
SOURCE_ELEMENTS = (
    ("electrical pulses applied to a central crystal",
     "electrode piezoelectric excitation — ordinary"),
    ("top pyramid section near 52 degrees said to harvest output",
     "termination-angle geometry; directionality is a hypothesis "
     "requiring both-orientation tests"),
    ("20 Hz electrode pulses and 4096 Hz crossed-coil configurations",
     "specific drive parameters; candidates, not privileged values"),
    ("crossed coils at 45 or 90 degrees",
     "coil geometry parameter for the excitation lane"),
    ("51.843 degree termination geometry",
     "angle candidate; see pyramid_ratio_audit"),
    ("alleged radiation, water storage, consciousness effects, "
     "levitation, antigravity, and free energy",
     "excluded claims — firewall DEVICE_MIRACLES; not investigable "
     "as stated"),
)

#: The sham-control episode, preserved because it is the programme's
#: single most instructive datum about expectation effects.
SHAM_EPISODE = (
    "The source includes an uncontrolled episode where an effect was "
    "reported before participants noticed output power was not "
    "engaged. Preserved as a crucial expectation and sham-control "
    "warning.")


#: Novelty boundary (A09): what v4.7 adds vs what is textbook. Claiming
#: novelty for textbook material is a credibility bug.
NOVELTY_BOUNDARY = {
    "textbook_not_novel": (
        "phase-locked loops and synchronization state machines",
        "finite-Q ringdown and oscillator holdover",
        "multipath least-squares/sparse channel estimation",
        "multi-wavelength integer-ambiguity resolution",
        "relativistic clock corrections (GPS practice)",
        "acousto-optic sidebands and piezoelectric transduction",
    ),
    "programme_specific": (
        "exact-rational closure-window alias analysis tied to the "
        "dyadic candidate family",
        "dual coprime closure lattices as an ambiguity-breaking "
        "probe design",
        "the evidence-class ladder wiring every estimate to refusal "
        "semantics",
        "the guarded Phryll operationalization with a prohibited "
        "DETECTED state",
    ),
    "evidence_class": "DERIVED_ARITHMETIC",
}

#: Frozen evaluation contract (A10) — fixed BEFORE estimator tuning.
EVALUATION_SPEC = (
    "PMWR-EVAL-v1: recovery quality is judged on (1) refusal "
    "correctness — the gate must refuse all non-identifiable holdout "
    "cases; (2) gain RMSE on identifiable synthetic holdouts at "
    "seeds 41,42,43; (3) alias disclosure — every RECOVERED verdict "
    "must carry its closure alias caveat. Holdout scenarios are the "
    "REFERENCE_SCENARIOS in the pack, evaluated once. Frozen "
    "2026-07-18 before estimator implementation was tuned."
)


def evaluation_fingerprint() -> str:
    return hashlib.sha256(EVALUATION_SPEC.encode("utf-8")).hexdigest()
