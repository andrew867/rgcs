"""P12 — phase ranging and recursive addressing.

Carrier phase gives range to a fraction of a wavelength and gives the
integer cycle count not at all. That single sentence is the whole
subject: the measurement is precise and ambiguous at the same time,
and everything else here is bookkeeping about the ambiguity.

    rho = (N + phi) * lambda

with ``phi`` the measured fractional cycle in [0, 1) and ``N`` an
unknown non-negative integer. ``N`` is not small, not zero by default,
and not recoverable from a single carrier at a single epoch. A module
that quietly sets ``N = 0`` reports a range that is wrong by an
arbitrary multiple of the wavelength while looking as precise as one
that is right.

Two honest disclosures, stated here rather than buried:

1. The dual-wavelength thinning in :func:`dual_wavelength_thinning` is
   the **standard GNSS wide-lane technique**. It is textbook, it is
   decades old, and RGCS did not invent it. See the notes on that
   function.
2. Recursive addressing (:func:`recursive_address_to_range`) buys
   *address* precision without buying *physical* precision. Past a
   computable depth, extra key levels name a smaller cell than the
   transform chain can locate, and the additional digits are
   decoration. :func:`recursive_address_to_range` reports that depth
   rather than letting the caller assume it is infinite.

Nothing here is a measurement. No carrier has been transmitted, no
phase recorded, no ambiguity resolved against real data. Every value
is arithmetic over declared inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from r6.mailbox import KEY_RADIX, KeyPath

EVIDENCE_CLASS = "SYNTHETIC_MODEL"
DERIVED = "DERIVED_ARITHMETIC"

NO_MEASUREMENT = (
    "No measurement has been taken. RGCS owns no transmitter, no "
    "receiver and no phase meter. No carrier has been radiated, no "
    "phase observed, and no ambiguity resolved against data. This "
    "module computes over declared inputs only.")

#: Speed of light in vacuum, exact by definition of the metre.
C = 299_792_458.0


class RangeRefused(RuntimeError):
    """Raised when a range claim is not supportable."""


def _stamp(record: dict, evidence_class: str = DERIVED) -> dict:
    record["evidence_class"] = evidence_class
    record["no_measurement_statement"] = NO_MEASUREMENT
    return record


def wavelength_from_frequency(frequency_hz: float, *,
                              propagation_speed_m_s: float = C) -> float:
    """lambda = v / f.

    ``propagation_speed_m_s`` is exposed because it is a declared
    property of the medium, not a constant. In coax or fibre the
    velocity factor is 0.6 to 0.7 of c, and using c there produces a
    range error of thirty to forty percent — larger than any of the
    effects this module is otherwise concerned with.
    """
    if frequency_hz <= 0:
        raise ValueError("frequency must be positive")
    if propagation_speed_m_s <= 0:
        raise ValueError("propagation speed must be positive")
    return propagation_speed_m_s / frequency_hz


# --------------------------------------------------------------------
# 1. Range from carrier phase
# --------------------------------------------------------------------

def range_from_phase(phase_cycles: float, wavelength_m: float,
                     ambiguity_n: int, *,
                     path_factor: float = 1.0) -> dict:
    """rho = (N + phi) * lambda / path_factor.

    ``phase_cycles`` is the *fractional* cycle in [0, 1). Values
    outside that range are refused rather than wrapped, because a
    caller passing 1.5 has either already added part of the integer or
    has not wrapped a raw phase, and guessing which one silently
    produces a range that is wrong by a wavelength.

    ``ambiguity_n`` must be supplied. There is no default. The whole
    point of this function is that ``N`` comes from somewhere else —
    a code measurement, a known baseline, a wide-lane combination, or
    an integer-search algorithm — and the caller must say where.

    ``path_factor`` is 1 for a one-way link and 2 for a round trip,
    where the observed phase accumulates over twice the geometric
    range.
    """
    if not 0.0 <= phase_cycles < 1.0:
        raise ValueError(
            f"phase_cycles must be a wrapped fraction in [0, 1), got "
            f"{phase_cycles}. Do not fold integer cycles into the "
            f"fraction; pass them as ambiguity_n")
    if wavelength_m <= 0:
        raise ValueError("wavelength must be positive")
    if not isinstance(ambiguity_n, int) or isinstance(ambiguity_n, bool):
        raise TypeError("the cycle ambiguity N must be an integer")
    if ambiguity_n < 0:
        raise ValueError("a negative cycle count implies negative range")
    if path_factor <= 0:
        raise ValueError("path factor must be positive")

    rho = (ambiguity_n + phase_cycles) * wavelength_m / path_factor
    return _stamp({
        "phase_cycles": phase_cycles,
        "wavelength_m": wavelength_m,
        "ambiguity_n": ambiguity_n,
        "path_factor": path_factor,
        "range_m": rho,
        "fractional_part_m": phase_cycles * wavelength_m / path_factor,
        "integer_part_m": ambiguity_n * wavelength_m / path_factor,
        "range_step_per_cycle_m": wavelength_m / path_factor,
        "ambiguity_source": "SUPPLIED_BY_CALLER",
        "statement": (
            "N is NOT determined by this measurement. A single carrier "
            "phase observation at a single epoch constrains the range "
            "only modulo one wavelength. The value returned is "
            "conditional on the supplied N being correct; if N is "
            "wrong by k, the range is wrong by "
            f"k * {wavelength_m / path_factor:.6g} m, and nothing in "
            "the phase observation reveals that it is wrong."),
        "what_would_resolve_it": (
            "an independent range estimate better than half a "
            "wavelength (typically a code/pseudorange measurement), a "
            "second carrier giving a longer effective wavelength (see "
            "dual_wavelength_thinning), motion over a known baseline, "
            "or an integer least-squares search over multiple epochs "
            "and satellites (LAMBDA)."),
    })


# --------------------------------------------------------------------
# 2. Ambiguity set
# --------------------------------------------------------------------

def ambiguity_set(wavelength_m: float, window_m: float) -> dict:
    """How many integer cycle candidates a range window admits.

    Structurally the same audit as
    :func:`r3.root_space.zero_residual_aliases`, and for the same
    reason: a wrapped observable admits one candidate per cycle across
    the search window, and picking one of them — the first, the
    nearest, the tidiest — is a choice, not a measurement.

    The count is ``floor(window / lambda) + 1``: the endpoints are
    both candidates.
    """
    if wavelength_m <= 0:
        raise ValueError("wavelength must be positive")
    if window_m < 0:
        raise ValueError("search window cannot be negative")

    n = int(window_m / wavelength_m)
    candidates = n + 1
    return _stamp({
        "wavelength_m": wavelength_m,
        "search_window_m": window_m,
        "candidates": candidates,
        "spacing_m": wavelength_m,
        "resolved": candidates == 1,
        "status": ("AMBIGUITY_UNRESOLVED" if candidates > 1
                   else "AMBIGUITY_BOUNDED_BY_WINDOW"),
        "statement": (
            "each candidate reproduces the observed phase exactly. "
            "They are not ranked by the phase observation and cannot "
            "be; distinguishing them requires information the carrier "
            "does not carry. A single surviving candidate means the "
            "window was already smaller than a wavelength, which is "
            "an assumption about the geometry, not a result of the "
            "measurement."),
    })


# --------------------------------------------------------------------
# 3. Dual-wavelength thinning
# --------------------------------------------------------------------

def dual_wavelength_thinning(l1: float, l2: float,
                             window_m: float) -> dict:
    """Wide-lane reduction of the candidate set. NOT NOVEL.

    **This is the standard GNSS wide-lane technique and RGCS did not
    invent it.** Two carriers of nearby wavelength are differenced to
    form a beat (wide-lane) wavelength

        lambda_wl = l1 * l2 / |l1 - l2|

    which is much longer than either, so the wide-lane ambiguity can
    be resolved over a range window where neither individual ambiguity
    could be. It has been standard practice in satellite geodesy since
    the mid-1980s — Wuebbena (1985) and Melbourne (1985) independently
    published the combination that carries their names, and the
    integer least-squares treatment (Teunissen's LAMBDA method, 1995)
    is in every GNSS textbook, e.g. Hofmann-Wellenhof, Lichtenegger &
    Wasle, *GNSS* (Springer, 2008), and Misra & Enge, *Global
    Positioning System* (2nd ed., 2006).

    It is included here because the RGCS phase-ranging lane needs it
    and because reimplementing a textbook method without saying so is
    how a repository accidentally claims a fifty-year-old result. The
    honest framing: this function is a correct implementation of prior
    art, and the prior art is load-bearing.

    The trade the textbooks also state, and which is easy to omit
    because it spoils the story: the wide-lane combination amplifies
    measurement noise. The ambiguity gets easier to fix and the
    resulting range gets noisier, roughly in proportion to the
    wavelength gain. It buys resolvability with precision.
    """
    if l1 <= 0 or l2 <= 0:
        raise ValueError("wavelengths must be positive")
    if window_m < 0:
        raise ValueError("search window cannot be negative")
    if l1 == l2:
        raise RangeRefused(
            "identical wavelengths form no beat and cannot thin each "
            "other's ambiguity set; the combination is degenerate")

    beat = l1 * l2 / abs(l1 - l2)
    before_1 = ambiguity_set(l1, window_m)["candidates"]
    before_2 = ambiguity_set(l2, window_m)["candidates"]
    after = ambiguity_set(beat, window_m)["candidates"]
    smaller = min(l1, l2)
    noise_gain = beat / smaller

    return _stamp({
        "l1_m": l1,
        "l2_m": l2,
        "beat_wavelength_m": beat,
        "search_window_m": window_m,
        "candidates_l1": before_1,
        "candidates_l2": before_2,
        "surviving_candidates": after,
        "thinning_factor": (before_1 / after) if after else float("inf"),
        "resolved_within_window": after == 1,
        "wavelength_gain": beat / smaller,
        "noise_amplification": noise_gain,
        "prior_art": (
            "standard GNSS wide-lane / Melbourne-Wuebbena combination "
            "(Wuebbena 1985; Melbourne 1985), with integer "
            "least-squares resolution per Teunissen's LAMBDA method "
            "(1995). Textbook material, not an RGCS contribution."),
        "novelty": "NONE_TEXTBOOK_PRIOR_ART",
        "tradeoff": (
            f"the wide-lane wavelength is {noise_gain:.4g}x the "
            f"shorter carrier, so the ambiguity is that much easier "
            f"to fix and the resulting range is roughly that much "
            f"noisier. Wide-laning is normally used to bootstrap the "
            f"narrow-lane ambiguity, not as the final range."),
        "statement": (
            "thinning reduces the candidate count. It does not by "
            "itself select a candidate, and a surviving count above 1 "
            "means the range remains ambiguous."),
    })


# --------------------------------------------------------------------
# 4. Recursive address to range interval
# --------------------------------------------------------------------

@dataclass(frozen=True)
class RangeInterval:
    """A physical interval named by a recursive address."""

    start_m: float
    width_m: float
    depth: int
    uncertainty_m: float

    @property
    def end_m(self) -> float:
        return self.start_m + self.width_m

    @property
    def centre_m(self) -> float:
        return self.start_m + self.width_m / 2.0

    def as_record(self) -> dict:
        d = asdict(self)
        d["end_m"] = self.end_m
        d["centre_m"] = self.centre_m
        return _stamp(d)


def recursive_address_to_range(key_path: KeyPath, cell_size_m: float, *,
                               per_level_uncertainty_frac: float = 1e-3,
                               radix: int = KEY_RADIX) -> dict:
    """Map an :class:`r6.mailbox.KeyPath` onto a physical range interval.

    Each level subdivides its parent cell into ``radix`` parts, so a
    path of depth L names an interval of width
    ``cell_size_m / radix**L`` whose start is the accumulated offset

        sum_i k_i * cell_size_m / radix**i.

    Uncertainty accumulates *down* the chain rather than shrinking with
    it. Every level introduces a referencing error — the parent cell's
    own origin is only known to some fraction of its size — and those
    errors add in quadrature. Because the coarsest level has the
    largest cell, it dominates the sum, and the total uncertainty is
    essentially fixed by level one no matter how deep the path goes.

    The consequence is the useful output of this function. Beyond
    ``useful_depth`` the named cell is narrower than the uncertainty
    with which it can be located, so the extra key levels are exact
    arithmetic about a position nobody can find. The address gets more
    precise; the range does not. Reporting a depth-8 address as a
    depth-8 physical position is the error this function exists to
    make visible.
    """
    if not isinstance(key_path, KeyPath):
        raise TypeError("key_path must be an r6.mailbox.KeyPath")
    if cell_size_m <= 0:
        raise ValueError("root cell size must be positive")
    if radix < 2:
        raise ValueError("radix must be at least 2")
    if per_level_uncertainty_frac < 0:
        raise ValueError("per-level uncertainty fraction cannot be "
                         "negative")

    start = 0.0
    var = 0.0
    levels = []
    for i, k in enumerate(key_path.keys, start=1):
        parent_width = cell_size_m / radix ** (i - 1)
        cell_width = cell_size_m / radix ** i
        start += k * cell_width
        sigma_i = per_level_uncertainty_frac * parent_width
        var += sigma_i * sigma_i
        levels.append({
            "level": i,
            "key": k,
            "parent_cell_width_m": parent_width,
            "cell_width_m": cell_width,
            "offset_m": k * cell_width,
            "level_uncertainty_m": sigma_i,
            "cumulative_uncertainty_m": math.sqrt(var),
        })

    depth = key_path.depth
    width = cell_size_m / radix ** depth
    sigma = math.sqrt(var)

    # deepest level whose cell is still wider than the accumulated
    # uncertainty: below that, address precision is decoration
    useful = 0
    for lv in levels:
        if lv["cell_width_m"] >= lv["cumulative_uncertainty_m"]:
            useful = lv["level"]
        else:
            break

    interval = RangeInterval(start_m=start, width_m=width, depth=depth,
                             uncertainty_m=sigma)

    return _stamp({
        "key_path": str(key_path),
        "depth": depth,
        "radix": radix,
        "root_cell_size_m": cell_size_m,
        "interval": interval.as_record(),
        "start_m": start,
        "width_m": width,
        "centre_m": interval.centre_m,
        "uncertainty_m": sigma,
        "levels": levels,
        "dominant_level": 1 if levels else None,
        "useful_depth": useful,
        "depth_beyond_useful": max(0, depth - useful),
        "address_finer_than_physics": width < sigma,
        "statement": (
            f"the address names an interval {width:.6g} m wide, "
            f"located to {sigma:.6g} m. "
            + ("The address is finer than the position is known, so "
               "levels beyond "
               f"{useful} add naming precision and no physical "
               "precision."
               if width < sigma else
               "The interval remains wider than the accumulated "
               "uncertainty, so every level is physically "
               "meaningful.")),
        "accumulation_note": (
            "uncertainty adds in quadrature down the chain and is "
            "dominated by the coarsest level, because that level has "
            "the largest cell. Descending the tree cannot recover "
            "precision the root never had."),
    })


# --------------------------------------------------------------------
# 5. Refusal
# --------------------------------------------------------------------

def refuse_range_without_ambiguity_resolution(
        wavelength_m: float | None = None,
        window_m: float | None = None,
        surviving_candidates: int | None = None):
    """Refuse a range claim while the integer ambiguity is open.

    Call with the surviving candidate count, or with a wavelength and
    window so the count can be computed. Raises unless exactly one
    candidate survives.
    """
    if surviving_candidates is None:
        if wavelength_m is None or window_m is None:
            raise RangeRefused(
                "the cycle ambiguity N is unresolved and no evidence "
                "was offered for resolving it. A carrier phase "
                "observation determines the range only modulo one "
                "wavelength; a range reported without stating how N "
                "was fixed is not a range.")
        surviving_candidates = ambiguity_set(
            wavelength_m, window_m)["candidates"]

    if surviving_candidates != 1:
        raise RangeRefused(
            f"{surviving_candidates} integer cycle candidates survive "
            f"the search window; each reproduces the observed phase "
            f"exactly and the observation does not rank them. No "
            f"range may be reported until the ambiguity is fixed by "
            f"independent information, and the method used must be "
            f"stated alongside the result.")

    return _stamp({
        "surviving_candidates": 1,
        "status": "AMBIGUITY_RESOLVED_WITHIN_WINDOW",
        "caveat": (
            "resolution here means the search window admits one "
            "candidate. That is a statement about the declared window, "
            "which is an assumption about the geometry and must be "
            "justified independently of the phase observation."),
    })
