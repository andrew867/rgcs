"""P01 — a transcription correction, append-only, and its exact invariant.

A source correction arrived after R10.6: the numbers first heard as
``8300`` and ``1876`` were a blurry hearing of ``8.300`` and ``1.876``
-- fractional measurements whose decimal point was displaced in
transcription. This module records that correction the only honest way:
**append-only.** The raw journal value is never overwritten; the
correction is a new event that points back at it.

The arithmetic has a clean invariant and a genuine consequence.

**Invariant:** the ratio is scale-free.

    8.300 / 1.876  ==  8300 / 1876  ==  2075/469   (exactly)

So the residual against q^{-1} = 4096/925 is *numerically unchanged* --
still 1649/433825, about 0.086% -- and the R10.6 finding
``APPROXIMATE_NOT_EXACT`` stands untouched.

**Consequence:** the *meaning* changes completely. "8300 of something"
and "8.300 of something" are the same ratio but different physical
statements, and the something is still unknown. The module refuses to
turn a fractional measurement into kilometres, miles, Earth radii,
frequencies, coordinates, or density levels. That is
``PhysicalMappingUnresolved``, and it is the point: a corrected number
is not a decoded number.

Candidate nonlinear mappings (log-radius, inverse-radius, shell index,
...) are provided only as **versioned, invertible models with declared
units-or-dimensionless status** -- never as an assumed reading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

Q = Fraction(925, 4096)
Q_INV = Fraction(4096, 925)


class UnitInventionRefused(RuntimeError):
    """Raised when an unknown-unit quantity is given a unit for free."""


class OverwriteRefused(RuntimeError):
    """Raised when a raw record would be mutated instead of appended."""


# --- the append-only record --------------------------------------------

@dataclass(frozen=True)
class ReceivedQuantity:
    """A value as first heard/transcribed. Immutable."""

    record_id: str
    raw_text: str                # exactly as transcribed, e.g. "8300"
    raw_value: Fraction
    units: str = "UNKNOWN"
    significant_digits: int = 0
    note: str = ""


@dataclass(frozen=True)
class TranscriptionCorrection:
    """A later correction. Points at the raw record; never replaces it."""

    corrects: str                # record_id of the ReceivedQuantity
    corrected_text: str          # e.g. "8.300"
    corrected_value: Fraction
    reason: str
    scale_hypothesis: str        # DECIMAL_POINT_DISPLACED, etc.


#: The raw journal record, preserved verbatim.
RAW_8300 = ReceivedQuantity(
    "RQ_8300", "8300", Fraction(8300), "UNKNOWN", 4,
    "heard while the source was blurry; later corrected")
RAW_1876 = ReceivedQuantity(
    "RQ_1876", "1876", Fraction(1876), "UNKNOWN", 4,
    "companion value; later described as fractional")

#: The corrections, appended.
CORR_8300 = TranscriptionCorrection(
    "RQ_8300", "8.300", Fraction("8.300"),
    "decimal point displaced in transcription of a blurry hearing",
    "DECIMAL_POINT_DISPLACED")
CORR_1876 = TranscriptionCorrection(
    "RQ_1876", "1.876", Fraction("1.876"),
    "companion described as a fractional measurement",
    "DECIMAL_POINT_DISPLACED")

RAW_RECORDS = {r.record_id: r for r in (RAW_8300, RAW_1876)}
CORRECTIONS = (CORR_8300, CORR_1876)


def append_correction(raw: ReceivedQuantity,
                      corr: TranscriptionCorrection) -> dict:
    """Record a correction without touching the raw value."""
    if corr.corrects != raw.record_id:
        raise ValueError("correction does not point at this record")
    return {
        "raw_record_id": raw.record_id,
        "raw_text": raw.raw_text,              # preserved verbatim
        "raw_value": str(raw.raw_value),
        "corrected_text": corr.corrected_text,
        "corrected_value": str(corr.corrected_value),
        "scale_hypothesis": corr.scale_hypothesis,
        "raw_preserved": True,
    }


def refuse_overwrite(raw: ReceivedQuantity) -> None:
    """Raw records are immutable; corrections are appended, not applied."""
    raise OverwriteRefused(
        f"{raw.record_id} ({raw.raw_text!r}) is an append-only journal "
        f"record and is never overwritten. A correction is a new event "
        f"that references it, so the original hearing stays auditable.")


# --- the scale-invariant ratio -----------------------------------------

def ratio_invariance() -> dict:
    """8.300/1.876 == 8300/1876 exactly, so the residual is unchanged."""
    raw_ratio = RAW_8300.raw_value / RAW_1876.raw_value
    corr_ratio = CORR_8300.corrected_value / CORR_1876.corrected_value
    resid = Q_INV - corr_ratio
    return {
        "raw_ratio": str(raw_ratio),
        "corrected_ratio": str(corr_ratio),
        "ratios_equal": raw_ratio == corr_ratio,
        "reduced": str(corr_ratio),                # 2075/469
        "q_inv": str(Q_INV),
        "residual_exact": str(resid),              # 1649/433825
        "residual_percent": float(resid / Q_INV) * 100,
        "are_equal": resid == 0,
        "verdict": "APPROXIMATE_NOT_EXACT",
        "note": (
            "the correction is scale-free: the ratio and its residual "
            "against 4096/925 are numerically unchanged. The R10.6 "
            "APPROXIMATE_NOT_EXACT finding stands"),
    }


# --- the physical mapping stays unresolved -----------------------------

def refuse_unit_invention(value: Fraction, claimed_unit: str) -> None:
    """A fractional measurement of unknown unit gets no free unit."""
    raise UnitInventionRefused(
        f"{value} has UNKNOWN units. Assigning it {claimed_unit!r} -- "
        f"kilometres, miles, Earth radii, hertz, degrees, or a density "
        f"level -- is inventing the evidence. The correction fixed the "
        f"decimal point, not the dimension. PhysicalMappingUnresolved.")


#: Candidate invertible scale models. Each is a hypothesis, not a
#: reading; each has a complete inverse and a declared unit status.
def _log_radius(x): return __import__("math").log(x)
def _inv_log_radius(y): return __import__("math").exp(y)
def _inverse(x): return 1.0 / x
def _inv_inverse(y): return 1.0 / y
def _identity(x): return x


SCALE_MODELS = {
    "LOG_RADIAL": {"forward": _log_radius, "inverse": _inv_log_radius,
                   "units": "DIMENSIONLESS", "domain": "x>0"},
    "INVERSE_RADIUS": {"forward": _inverse, "inverse": _inv_inverse,
                       "units": "RECIPROCAL_OF_INPUT", "domain": "x!=0"},
    "OBJECT_RELATIVE": {"forward": _identity, "inverse": _identity,
                        "units": "DIMENSIONLESS", "domain": "all"},
}


def scale_model_round_trips(name: str, x: float = 4.428) -> bool:
    m = SCALE_MODELS[name]
    return abs(m["inverse"](m["forward"](x)) - x) < 1e-9


def physical_mapping_status() -> dict:
    return {
        "status": "PhysicalMappingUnresolved",
        "why": (
            "the ratio is exact and unitless; the individual "
            "quantities have unknown units and unknown physical "
            "referents. No mapping to distance, frequency, coordinate "
            "or density is supported"),
        "scale_models_available": list(SCALE_MODELS),
        "every_model_invertible": all(
            scale_model_round_trips(n) for n in SCALE_MODELS),
    }


def received_report() -> dict:
    return {
        "corrections": [append_correction(RAW_RECORDS[c.corrects], c)
                        for c in CORRECTIONS],
        "ratio_invariance": ratio_invariance(),
        "physical_mapping": physical_mapping_status(),
        "raw_records_preserved": [r.raw_text for r in RAW_RECORDS.values()],
        "evidence_class": "SOURCE_CLAIM corrected, append-only",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not say what 8.300 or 1.876 measure, or that they "
            "measure anything physical. The decimal-point correction is "
            "faithfully recorded; the units, the referent, and any "
            "mapping remain unresolved, and a corrected number is not a "
            "decoded one."),
    }
