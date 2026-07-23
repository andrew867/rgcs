"""P05 — the 1604 and 1644 cues: a near-miss, its residual, and a null.

Two numeric cues were recorded, spoken digit-by-digit as ``1-6-0-4`` and
``1-6-4-4``. This module tests ONLY preregistered arithmetic relations on
them, keeps every residual exact where the arithmetic is rational, and
assigns NO meaning beyond the arithmetic itself.

The tempting claim is that

    1604  is close to  925 * sqrt(3) = 1602.146997...

a match at about 0.12%. This module reports that residual honestly and
then refuses to let it stand alone, for two reasons.

**It is approximate, not exact.** ``sqrt(3)`` is irrational, so the
comparison is a floating-point near-miss with a nonzero residual, never
an identity. ``refuse_exact_claim`` raises rather than call it one.

**It is no better than chance.** With a preregistered grid of small
``a * sqrt(b)`` expressions and the observed tolerance, a randomly chosen
target in the same range lands *equally close* to some grid expression
essentially always: the look-elsewhere p-value is ~1.0. A search over
enough candidate forms hits any target; that a form was found near 1604
is therefore uninformative. To show the search is not simply blind, a
POWER control plants a target that IS exactly a grid expression
(``30 * sqrt(5)``) and confirms the search recovers it at ~zero
residual. So the machinery can detect a real hit -- it just reports that
1604's hit is not one.

The pair also differs by exactly ``1644 - 1604 = 40`` (integers, exact),
and the module assigns that 40 no meaning. A digit readback such as
``1-6-0-4`` is kept distinct from the integer 1604: a spoken sequence is
not automatically a base-10 quantity with units.

Everything here is arithmetic. Nothing is measured, generated, or driven.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

# --- the cues, exact where they are integers ---------------------------

VALUE_1604 = 1604
VALUE_1644 = 1644

#: 925 * sqrt(3): sqrt(3) is irrational, so this is a float, not exact.
k_root3 = 925 * math.sqrt(3)          # 1602.146997001211...

#: residual of the near-miss, and the two ways to normalise it.
_RESIDUAL_HZ = VALUE_1604 - k_root3    # ~1.853002998788497
#: relative to the target 1604 (the written formula (1604-925*sqrt3)/1604)
OBSERVED_REL_RESIDUAL = _RESIDUAL_HZ / VALUE_1604          # ~0.00115524
#: relative to 925*sqrt(3) itself
OBSERVED_REL_RESIDUAL_VS_ROOT3 = _RESIDUAL_HZ / k_root3    # ~0.00115657


class CueError(RuntimeError):
    """Raised when a cue is given exactness or meaning it has not earned."""


@dataclass(frozen=True)
class NumericCue:
    """A cue as spoken. The digit readback is kept apart from the integer."""

    cue_id: str
    spoken_text: str                 # e.g. "1-6-0-4"
    spoken_digits: tuple[int, ...]   # e.g. (1, 6, 0, 4)
    parsed_value: int                # e.g. 1604 -- an interpretation
    units: str = "UNKNOWN"
    note: str = ""

    def digits_match_value(self) -> bool:
        """Does reading the digits in base 10 reproduce the parsed value?"""
        acc = 0
        for d in self.spoken_digits:
            acc = acc * 10 + d
        return acc == self.parsed_value


CUE_1604 = NumericCue(
    "CUE_1604", "1-6-0-4", (1, 6, 0, 4), VALUE_1604, "UNKNOWN",
    "spoken digit-by-digit; parsed as base-10 only as one interpretation")
CUE_1644 = NumericCue(
    "CUE_1644", "1-6-4-4", (1, 6, 4, 4), VALUE_1644, "UNKNOWN",
    "companion cue; parsed as base-10 only as one interpretation")


# --- the near-miss against 925*sqrt(3), residual shown -----------------

def root3_residual() -> dict:
    """1604 vs 925*sqrt(3): close, not equal, residual shown both ways."""
    return {
        "target": VALUE_1604,
        "k_root3": k_root3,
        "k_root3_is_exact": False,        # sqrt(3) is irrational
        "residual_hz": _RESIDUAL_HZ,
        "relative_residual": OBSERVED_REL_RESIDUAL,
        "relative_residual_percent": OBSERVED_REL_RESIDUAL * 100,
        "relative_residual_vs_root3": OBSERVED_REL_RESIDUAL_VS_ROOT3,
        "relative_residual_vs_root3_percent":
            OBSERVED_REL_RESIDUAL_VS_ROOT3 * 100,
        "are_equal": _RESIDUAL_HZ == 0,
        "verdict": "APPROXIMATE_NOT_EXACT",
        "note": (
            "1604 and 925*sqrt(3) agree to about 0.12% and are not "
            "equal. sqrt(3) is irrational, so there is no rational "
            "residual to reduce to zero and no identity to claim; the "
            "match is a near-miss whose residual must always be shown"),
    }


def refuse_exact_claim(target: int = VALUE_1604) -> None:
    """Refuse to call the 1604 vs 925*sqrt(3) near-miss an identity."""
    raise CueError(
        f"{target} is not equal to 925*sqrt(3) = {k_root3:.9f}. Their "
        f"difference is {_RESIDUAL_HZ:.9f} (about "
        f"{OBSERVED_REL_RESIDUAL * 100:.4f}%). sqrt(3) is irrational, so "
        f"this is an APPROXIMATE_NOT_EXACT near-miss, never an identity, "
        f"and it confers no exactness on anything built from it.")


# --- the difference 1644 - 1604 = 40, meaning withheld -----------------

def difference() -> dict:
    """1644 - 1604 = 40 exactly, and 40 is assigned no meaning."""
    diff = VALUE_1644 - VALUE_1604
    return {
        "a": VALUE_1644,
        "b": VALUE_1604,
        "difference": diff,               # 40, exact integer subtraction
        "is_exact": True,
        "meaning_assigned": False,
        "note": (
            "the two cues differ by exactly 40. That is a fact of integer "
            "subtraction and nothing more: no interval, frequency, index, "
            "count, or code is read from it"),
    }


def refuse_meaning_for_difference(claimed_meaning: str = "an interval") -> None:
    """The difference of 40 is arithmetic only; refuse to interpret it."""
    diff = VALUE_1644 - VALUE_1604
    raise CueError(
        f"{VALUE_1644} - {VALUE_1604} = {diff} is exact integer "
        f"subtraction. Reading it as {claimed_meaning!r} -- an interval, "
        f"a frequency step, a shell index, a count, or a code -- invents "
        f"meaning the arithmetic does not carry. meaning_assigned=False.")


# --- the look-elsewhere null, with a power control ---------------------

#: Preregistered candidate grid: expressions a*sqrt(b). Ranges are fixed
#: in advance so the search cannot be tuned after seeing the result.
GRID_A_MAX = 1500
GRID_B_SET = (2, 3, 5, 6, 7, 10, 11, 13)
#: Preregistered range random targets are drawn from, and the sampler.
SEARCH_LO = 1000
SEARCH_HI = 2000
N_SAMPLES = 2000
SEED = 1604


def _sqrt_b_values() -> dict:
    return {b: math.sqrt(b) for b in GRID_B_SET}


_SQRT_B = _sqrt_b_values()


def best_grid_hit(target: float) -> dict:
    """Closest a*sqrt(b) in the grid to target, by relative residual.

    Only the a nearest to target/sqrt(b) (and its two neighbours) can be
    the closest for each b, so this is exact without scanning the whole
    grid.
    """
    if target <= 0:
        raise CueError("target must be positive")
    best = None
    for b, sb in _SQRT_B.items():
        a0 = round(target / sb)
        for a in (a0 - 1, a0, a0 + 1):
            if a < 1 or a > GRID_A_MAX:
                continue
            value = a * sb
            rel = abs(target - value) / target
            if best is None or rel < best["relative_residual"]:
                best = {"a": a, "b": b, "value": value,
                        "relative_residual": rel}
    if best is None:
        raise CueError("empty grid for target range")
    return best


def lookelsewhere_pvalue(target: float = VALUE_1604,
                         tol_rel: float | None = None,
                         n_samples: int = N_SAMPLES,
                         seed: int = SEED) -> dict:
    """How often does chance land as close to a random target as we did?

    Draw ``n_samples`` random targets from the preregistered range and
    count the fraction for which SOME grid expression falls within
    ``tol_rel`` (default: the observed 1604 vs 925*sqrt(3) residual). A
    large p means the near-miss is no better than chance.
    """
    if tol_rel is None:
        tol_rel = OBSERVED_REL_RESIDUAL
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_samples):
        t = rng.uniform(SEARCH_LO, SEARCH_HI)
        if best_grid_hit(t)["relative_residual"] <= tol_rel:
            hits += 1
    p = hits / n_samples
    return {
        "target": target,
        "tol_rel": tol_rel,
        "n_samples": n_samples,
        "hits": hits,
        "p_value": p,
        "observed_best_hit": best_grid_hit(target),
        "verdict": ("NO_BETTER_THAN_CHANCE" if p > 0.05
                    else "BETTER_THAN_CHANCE"),
        "note": (
            "with a grid this rich, a random target is matched to the "
            "observed tolerance essentially always, so a form found near "
            "1604 carries no evidential weight on its own"),
    }


#: The planted signal for the power control: exactly a grid expression.
PLANT_A, PLANT_B = 30, 5
PLANTED_TARGET = PLANT_A * math.sqrt(PLANT_B)     # 30*sqrt(5) = 67.082...


def power_check() -> dict:
    """Plant an exact grid expression and confirm the search recovers it."""
    hit = best_grid_hit(PLANTED_TARGET)
    detected = hit["relative_residual"] < 1e-12
    return {
        "planted": f"{PLANT_A}*sqrt({PLANT_B})",
        "planted_value": PLANTED_TARGET,
        "recovered": hit,
        "detected": detected,
        "note": (
            "the search finds a planted exact expression at ~zero "
            "residual, so it has the power to detect a real hit; that it "
            "calls 1604's near-miss chance is a finding, not blindness"),
    }


def cue1604_report() -> dict:
    resid = root3_residual()
    lee = lookelsewhere_pvalue()
    return {
        "cues": [
            {"cue_id": CUE_1604.cue_id, "spoken_text": CUE_1604.spoken_text,
             "spoken_digits": list(CUE_1604.spoken_digits),
             "parsed_value": CUE_1604.parsed_value},
            {"cue_id": CUE_1644.cue_id, "spoken_text": CUE_1644.spoken_text,
             "spoken_digits": list(CUE_1644.spoken_digits),
             "parsed_value": CUE_1644.parsed_value},
        ],
        "root3_residual": resid,
        "difference": difference(),
        "lookelsewhere": lee,
        "power": power_check(),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "APPROXIMATE_NOT_EXACT",
        "what_this_does_not_say": (
            "It does not say 1604 equals 925*sqrt(3), that the near-miss "
            "is significant, that the difference of 40 means anything, or "
            "that any of these numbers is physical. The residual is shown, "
            "the look-elsewhere p-value is ~1.0 (no better than chance), "
            "and no meaning is assigned beyond the arithmetic."),
    }
