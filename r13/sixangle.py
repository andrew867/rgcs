"""P23 — the six-detector angle ring: planar angular sampling, and the
refusal to read a flat ring as three-dimensional isotropic emission.

A ring of six detectors at 60-degree spacing sits in ONE plane and reads
a synthetic angular emission pattern at six azimuths (0, 60, 120, 180,
240, 300 degrees). That is all it does. The load-bearing governance rule
of this module -- the fifth of the R13 forbidden promotions -- is that

    planar angular uniformity is NOT three-dimensional isotropic emission.

Six coplanar detectors sample the azimuthal circle and nothing else. The
polar directions above and below the plane are never looked at. A pattern
that reads perfectly flat around the ring has demonstrated *azimuthal*
uniformity in one plane; it has said nothing whatever about the
out-of-plane directions, and so it cannot be promoted to 3-D isotropy.
:func:`refuse_planar_uniformity_as_isotropy` raises on any attempt to make
that jump, uniform samples or not.

Two facts make "the ring looks uniform" a *weak* observation even inside
its own plane.

**It is a coefficient of variation, not a measurement.** :func:`planar_
uniformity` returns the coefficient of variation of the six readings: a
constant pattern gives CV = 0 (flat), a ``cos(theta)`` dipole -- whose six
readings sum to zero around the ring -- gives an unbounded CV (as
non-uniform as it gets). Both directions are exercised, and neither number
is a bench reading of anything.

**Six samples alias.** By the sampling theorem on the circle, six equally
spaced detectors resolve angular harmonics only up to order three
(``n // 2``). An order-six harmonic ``cos(6 theta)`` evaluated at the six
azimuths is ``cos(k * 360 deg) = 1`` at every detector: it is
indistinguishable from a uniform (order-zero) pattern.
:func:`aliased_order` folds any order into ``[0, n/2]`` and shows order six
aliasing to zero. So "the ring looks uniform" can be a genuinely uniform
source, or a highly structured order-six source the ring simply cannot
see. That ambiguity is exactly why planar flatness is thin evidence.

Nothing here is measured. The pattern is a caller-supplied function
evaluated in software; no emitter was driven, no detector was exposed, and
no angular power was read. :func:`refuse_ring_as_measured` refuses to call
the samples a measurement. The standing verdict is
``SIX_ANGLE_RING_PLANAR_NOT_ISOTROPIC``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r13.claimtypes import ClaimClass


class SixAngleError(RuntimeError):
    """Raised when the planar ring is asked to over-claim.

    Covers a malformed ring or sample vector, an unevaluable pattern
    function, and -- load-bearing -- any attempt to read planar angular
    uniformity as three-dimensional isotropy or to call synthetic angular
    samples a measurement.
    """


CLAIM_CLASS = ClaimClass.ANALYTIC_MODEL.name
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "SIX_ANGLE_RING_PLANAR_NOT_ISOTROPIC"

#: The pack's ring: six detectors, 60-degree spacing, one plane.
RING_N = 6
RING_SPACING_DEG = 360.0 / RING_N


# --- the ring ----------------------------------------------------------

@dataclass(frozen=True)
class AngleRing:
    """A ring of ``n`` detectors at equal spacing, all in ONE plane.

    The default is the P23 six-detector ring at 60-degree spacing. The
    ``plane`` label is carried only to make explicit that every detector
    shares it: the ring has no extent in the out-of-plane (polar)
    direction, which is the whole point of :func:`refuse_planar_
    uniformity_as_isotropy`.
    """

    n: int = RING_N
    plane: str = "XY"

    def __post_init__(self) -> None:
        if isinstance(self.n, bool) or not isinstance(self.n, int):
            raise SixAngleError("detector count must be an integer")
        if self.n < 3:
            raise SixAngleError(
                f"a ring needs at least 3 detectors; got {self.n}")

    @property
    def spacing_deg(self) -> float:
        return 360.0 / self.n

    @property
    def nyquist_order(self) -> int:
        """Highest angular harmonic ``n`` equal samples can resolve."""
        return self.n // 2

    def angles_deg(self) -> np.ndarray:
        """The detector azimuths in degrees: 0, spacing, 2*spacing, ..."""
        return np.arange(self.n, dtype=float) * self.spacing_deg

    def angles_rad(self) -> np.ndarray:
        return np.radians(self.angles_deg())

    def sample_pattern(self, pattern_func) -> np.ndarray:
        """Evaluate a synthetic angular pattern at the ``n`` azimuths.

        ``pattern_func`` maps an angle in RADIANS to a scalar reading.
        The result is a length-``n`` vector of readings around the ring
        and nothing more -- it carries no information about any direction
        off the plane.
        """
        if not callable(pattern_func):
            raise SixAngleError("pattern_func must be callable")
        out = np.empty(self.n, dtype=float)
        for i, a in enumerate(self.angles_rad()):
            try:
                out[i] = float(pattern_func(float(a)))
            except SixAngleError:
                raise
            except Exception as exc:               # noqa: BLE001
                raise SixAngleError(
                    f"pattern_func failed at angle {math.degrees(a):.1f} "
                    f"deg: {exc}") from exc
        return out


# --- uniformity, as a coefficient of variation -------------------------

def planar_uniformity(samples, *, tol: float = 1e-9) -> dict:
    """Coefficient of variation of the readings around the ring.

    A uniform planar source gives CV ~ 0 (``uniform`` is True). A pattern
    whose readings sum to zero around the ring -- a ``cos(theta)`` dipole
    is the canonical case -- has a mean of zero and an unbounded CV, and
    is reported as maximally non-uniform. The number is a property of the
    six coplanar readings ONLY; a small CV is azimuthal flatness in one
    plane, never a statement about the out-of-plane directions.
    """
    v = np.asarray(samples, dtype=float)
    if v.ndim != 1 or v.size < 3:
        raise SixAngleError(
            "planar_uniformity needs a 1-D vector of at least 3 readings")
    mean = float(v.mean())
    std = float(v.std())                            # population std
    scale = float(np.max(np.abs(v))) + 1e-300
    if abs(mean) <= 1e-12 * scale:
        cv = float("inf")                           # zero-mean ring: no scale
    else:
        cv = std / abs(mean)
    return {
        "n": int(v.size),
        "mean": mean,
        "std": std,
        "coefficient_of_variation": cv,
        "uniform": bool(cv <= tol),
        "samples_in_one_plane": True,
        "claim_class": CLAIM_CLASS,
        "note": (
            "coefficient of variation across coplanar detectors only; a "
            "small value is azimuthal flatness in one plane, not 3-D "
            "isotropy"),
    }


# --- angular aliasing on the circle ------------------------------------

def resolvable_orders(n: int = RING_N) -> tuple[int, ...]:
    """Angular harmonic orders ``n`` equal samples can resolve: 0..n/2."""
    if n < 3:
        raise SixAngleError("a ring needs at least 3 detectors")
    return tuple(range(0, n // 2 + 1))


def aliased_order(m: int, n: int = RING_N) -> int:
    """Apparent angular order after sampling at ``n`` equal azimuths.

    Sampling folds a harmonic of order ``m`` into ``[0, n/2]`` (the
    Nyquist band on the circle). Every multiple of ``n`` -- in particular
    order ``n`` itself -- aliases to 0, i.e. to a uniform pattern. For the
    six-detector ring, ``aliased_order(6) == 0``: an order-six source is
    indistinguishable from a flat one.
    """
    if isinstance(m, bool) or not isinstance(m, int) or m < 0:
        raise SixAngleError("angular order must be a non-negative integer")
    if n < 3:
        raise SixAngleError("a ring needs at least 3 detectors")
    r = m % n
    if r > n // 2:
        r = n - r
    return int(r)


def angular_harmonic_amplitudes(samples) -> np.ndarray:
    """Amplitudes of angular harmonics 0..n/2 in the ring readings.

    A real DFT of the ring, normalised by ``n``. The array index is the
    harmonic order. Because the ring can only resolve up to ``n // 2``,
    any higher-order structure in the true pattern has already aliased
    down into these bins before this is computed.
    """
    v = np.asarray(samples, dtype=float)
    if v.ndim != 1 or v.size < 3:
        raise SixAngleError(
            "angular_harmonic_amplitudes needs at least 3 readings")
    return np.abs(np.fft.rfft(v)) / v.size


# --- the load-bearing refusals -----------------------------------------

def refuse_planar_uniformity_as_isotropy(samples=None) -> None:
    """Refuse to read planar angular uniformity as 3-D isotropy.

    This is the fifth forbidden promotion. Six detectors on one ring
    sample the azimuthal circle in a single plane and never look at the
    polar (out-of-plane) directions. However flat the readings are, they
    are evidence of azimuthal uniformity in that plane and of nothing
    above or below it, so no claim of three-dimensional isotropic
    emission can be drawn from them. Always raises.
    """
    detail = ""
    if samples is not None:
        u = planar_uniformity(samples)
        detail = (f" (the six readings have CV "
                  f"{u['coefficient_of_variation']!r}, but that is a "
                  f"one-plane number)")
    raise SixAngleError(
        "refused: a uniform reading around six coplanar detectors is "
        "PLANAR angular uniformity, not three-dimensional isotropic "
        "emission" + detail + ". The ring lies in one plane and samples "
        "only azimuthal directions; the polar, out-of-plane directions "
        "are never measured, so isotropy in 3-D cannot be inferred from "
        "any pattern of these six samples.")


def refuse_ring_as_measured(samples=None) -> None:
    """Refuse to call synthetic angular samples a measured pattern.

    The readings are values of a caller-supplied function evaluated in
    software. No emitter was driven, no detector was exposed to a field,
    and no angular power was recorded. Always raises.
    """
    n = None if samples is None else int(np.asarray(samples).size)
    raise SixAngleError(
        f"refused: {'these' if n is None else f'these {n}'} values are a "
        "synthetic angular pattern evaluated in software, not readings "
        "from real detectors. No emission was produced, no detector was "
        "exposed, and no angular power was measured; the ring is an "
        "ANALYTIC_MODEL, not a bench result.")


# --- report ------------------------------------------------------------

def sixangle_report() -> dict:
    ring = AngleRing()
    const = ring.sample_pattern(lambda th: 1.0)
    dipole = ring.sample_pattern(lambda th: math.cos(th))
    order6 = ring.sample_pattern(lambda th: math.cos(6.0 * th))
    return {
        "what_this_is": (
            "a six-detector angle ring at 60-degree spacing that samples "
            "a synthetic angular emission pattern in ONE plane, with a "
            "planar-uniformity metric, an angular-aliasing analysis, and "
            "the refusal to read planar uniformity as 3-D isotropy"),
        "ring_n": ring.n,
        "spacing_deg": ring.spacing_deg,
        "plane": ring.plane,
        "angles_deg": [float(a) for a in ring.angles_deg()],
        "nyquist_order": ring.nyquist_order,
        "resolvable_orders": list(resolvable_orders()),
        "order_6_aliases_to": aliased_order(6),
        "order_6_reads_as_uniform": bool(
            planar_uniformity(order6)["uniform"]),
        "constant_uniformity": planar_uniformity(const),
        "dipole_uniformity": planar_uniformity(dipole),
        "refusals": [
            "refuse_planar_uniformity_as_isotropy",
            "refuse_ring_as_measured",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say the source is isotropic. Six detectors on one "
            "ring sample only the azimuthal circle in a single plane; the "
            "polar, OUT-OF-PLANE directions are never sampled, so planar "
            "angular uniformity is not three-dimensional isotropic "
            "emission and may not be promoted to it. It does not say the "
            "readings were measured -- the pattern is a function evaluated "
            "in software, no emitter or detector exists, and nothing was "
            "exposed. And it does not say a flat-looking ring is "
            "structureless: with six samples an order-six harmonic aliases "
            "to order zero, so 'looks uniform' can equally be a source the "
            "ring cannot resolve."),
        "verdict": VERDICT,
    }
