"""P12 — recursive barycentric mailbox routing.

A "mailbox address" here is a *name*, built by descending a chain of
nested reference frames and then a chain of tetrahedral cells:

    galactic -> stellar-system barycenter -> star/component barycenter
    -> planetary-system barycenter -> body center -> body-fixed
    -> laboratory -> apparatus -> crystal -> defect site

with a key path K = (K1..KL), each Kl in 0..4095, and a barycentric
coordinate inside the terminal tetrahedron.

The boundary that makes this honest (core/12):

    The mailbox routes information locally through a declared
    protocol. It does not establish nonlocal coupling to the
    celestial destination represented by the address.

Writing "Alpha Centauri" into an address field is naming, not
signalling. :func:`refuse_nonlocal_delivery` enforces that in code.

Two roots are kept deliberately distinct because they are physically
different points that move relative to each other: the visual centre
of the Sun and the solar-system barycentre. Conflating them is a
common and quiet error — the barycentre wanders by more than a solar
radius as Jupiter goes round.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from fractions import Fraction

#: The canonical frame chain, outermost first (core/12).
FRAME_CHAIN = (
    "GALACTIC",
    "STELLAR_SYSTEM_BARYCENTER",
    "STAR_COMPONENT_BARYCENTER",
    "PLANETARY_SYSTEM_BARYCENTER",
    "BODY_CENTER",
    "BODY_FIXED",
    "LABORATORY",
    "APPARATUS",
    "CRYSTAL",
    "DEFECT_SITE",
)

#: The two solar roots. They are not the same point and the transform
#: between them is time dependent.
ROOTS = (
    "SUN_CENTER_VISUAL_ROOT",
    "SOLAR_SYSTEM_BARYCENTER_DYNAMICAL_ROOT",
)

#: Keys are R4 addresses: 4096 = 8^4 = 4^6 = 2^12 per level.
KEY_RADIX = 4096

#: Reasons a destination may be refused (core/12).
REFUSAL_REASONS = (
    "ROOT_MISSING",
    "FRAMES_DO_NOT_COMPOSE",
    "EPOCH_ABSENT",
    "EPOCH_EXPIRED",
    "EPHEMERIS_UNKNOWN",
    "COORDINATE_OUTSIDE_CELL",
    "UNCERTAINTY_EXCEEDS_POLICY",
    "AUTHENTICATION_FAILED",
    "ADDRESS_SEMANTICS_UNDECLARED",
)


class RouteRefused(RuntimeError):
    """Raised when a destination cannot be certified."""

    def __init__(self, reason: str, detail: str = "") -> None:
        if reason not in REFUSAL_REASONS:
            raise ValueError(f"undeclared refusal reason {reason!r}")
        self.reason = reason
        super().__init__(f"{reason}: {detail}" if detail else reason)


# --------------------------------------------------------------------
# Frame graph
# --------------------------------------------------------------------

@dataclass(frozen=True)
class FrameTransform:
    """One edge of the frame graph.

    Every transform carries epoch, time scale, ephemeris/model id,
    units, orientation and uncertainty — none of these are optional,
    because a transform without an epoch is not a transform between
    moving frames, it is a guess.
    """

    from_frame: str
    to_frame: str
    epoch_tt_s: float
    time_scale: str
    ephemeris_id: str
    translation_m: tuple[float, float, float]
    #: Rotation as a unit quaternion (w, x, y, z).
    rotation_quat: tuple[float, float, float, float]
    position_uncertainty_m: float
    units: str = "m"

    def __post_init__(self) -> None:
        if self.from_frame not in FRAME_CHAIN:
            raise ValueError(f"unknown frame {self.from_frame!r}")
        if self.to_frame not in FRAME_CHAIN:
            raise ValueError(f"unknown frame {self.to_frame!r}")
        if self.time_scale not in ("TT", "TAI", "TDB", "UTC", "TCB"):
            raise ValueError(f"undeclared time scale {self.time_scale!r}")
        if self.position_uncertainty_m < 0:
            raise ValueError("uncertainty must be non-negative")
        n = sum(q * q for q in self.rotation_quat) ** 0.5
        if abs(n - 1.0) > 1e-9:
            raise ValueError("rotation quaternion must be normalized")


@dataclass
class FrameGraph:
    """The chain of transforms from a root down to a defect site."""

    root: str
    transforms: list[FrameTransform] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.root not in ROOTS:
            raise ValueError(f"unknown root {self.root!r}")

    def add(self, t: FrameTransform) -> None:
        self.transforms.append(t)

    def composes(self) -> tuple[bool, str]:
        """Whether the chain is contiguous and ordered outermost-in."""
        if not self.transforms:
            return False, "no transforms"
        for a, b in zip(self.transforms, self.transforms[1:]):
            if a.to_frame != b.from_frame:
                return False, (f"{a.to_frame} does not connect to "
                               f"{b.from_frame}")
        idx = [FRAME_CHAIN.index(t.from_frame) for t in self.transforms]
        if idx != sorted(idx):
            return False, "frames are not ordered outermost-first"
        return True, "ok"

    def total_uncertainty_m(self, correlation: float = 0.0) -> float:
        """Accumulated position uncertainty along the chain.

        Quadrature is the ``correlation = 0`` case and it is **not**
        generally the right one. Adding in quadrature assumes the
        links are independent, but a frame chain typically shares an
        ephemeris, a time scale and a calibration across several
        transforms, so their errors are correlated and quadrature
        *understates* the total.

        For a uniform pairwise correlation rho the variance is

            sum_i s_i^2 + rho * sum_{i != j} s_i s_j

        which reduces to quadrature at rho = 0 and to linear addition
        at rho = 1. Callers that know their chain shares an ephemeris
        should pass a positive rho; ``worst_case_uncertainty_m`` gives
        the rho = 1 bound.

        Defect R8-D-002: earlier releases offered only the rho = 0
        form while the certificate carried a covariance field, which
        was internally inconsistent -- the object claimed to track
        correlation and then discarded it.
        """
        if not -1.0 <= correlation <= 1.0:
            raise ValueError("correlation must lie in [-1, 1]")
        s = [t.position_uncertainty_m for t in self.transforms]
        n = len(s)
        if n == 0:
            return 0.0

        # R8-D-005: a uniform correlation matrix is positive
        # semidefinite only for rho >= -1/(n-1). Below that bound the
        # matrix is not a valid covariance and the computed variance
        # goes negative. The previous implementation clamped it to
        # zero, which returned 0.0 m -- i.e. it reported PERFECT
        # knowledge of position for a physically impossible input.
        # That is the most dangerous way this function could fail, so
        # it refuses instead.
        if n > 1:
            psd_floor = -1.0 / (n - 1)
            if correlation < psd_floor - 1e-12:
                raise ValueError(
                    f"uniform correlation {correlation} is not "
                    f"positive semidefinite for {n} links: the bound "
                    f"is rho >= -1/(n-1) = {psd_floor:.6g}. A matrix "
                    f"below it is not a covariance, and the resulting "
                    f"variance is negative.")

        var = sum(x * x for x in s)
        cross = sum(a * b for i, a in enumerate(s)
                    for j, b in enumerate(s) if i != j)
        total = var + correlation * cross
        if total < 0.0:
            raise ValueError(
                "negative accumulated variance; the supplied "
                "correlation does not describe a valid covariance")
        return total ** 0.5

    def worst_case_uncertainty_m(self) -> float:
        """Fully-correlated bound: uncertainties add linearly."""
        return sum(t.position_uncertainty_m for t in self.transforms)

    def epochs_consistent(self, tolerance_s: float = 1.0) -> bool:
        if not self.transforms:
            return False
        e = [t.epoch_tt_s for t in self.transforms]
        return (max(e) - min(e)) <= tolerance_s


def sun_to_barycenter_offset_m(epoch_tt_s: float) -> float:
    """Magnitude of the Sun-centre to barycentre offset.

    Deliberately a *model stub with a declared status*, not a
    computation: producing a number here without a real ephemeris
    would be fabricated data. The physical fact recorded is that the
    offset is of order one solar radius (~7e8 m) and time dependent,
    which is why the two roots are separate.
    """
    raise RouteRefused(
        "EPHEMERIS_UNKNOWN",
        "the Sun-barycentre offset requires a real ephemeris (e.g. a "
        "JPL DE kernel). R6 ships no ephemeris and will not invent "
        "one; the offset is of order a solar radius and varies with "
        "the giant planets' configuration")


# --------------------------------------------------------------------
# Route keys and barycentric coordinates
# --------------------------------------------------------------------

@dataclass(frozen=True)
class KeyPath:
    """K = (K1..KL), each in 0..4095 (R4 exact address radix)."""

    keys: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.keys:
            raise ValueError("a key path needs at least one level")
        for k in self.keys:
            if not isinstance(k, int) or not 0 <= k < KEY_RADIX:
                raise ValueError(
                    f"key {k!r} outside 0..{KEY_RADIX - 1}")

    @property
    def depth(self) -> int:
        return len(self.keys)

    def as_int(self) -> int:
        """The path packed into one integer, exactly (12 bits/level)."""
        v = 0
        for k in self.keys:
            v = (v << 12) | k
        return v

    @classmethod
    def from_int(cls, v: int, depth: int) -> "KeyPath":
        if v < 0:
            raise ValueError("negative key path")
        keys = []
        for _ in range(depth):
            keys.append(v & 0xFFF)
            v >>= 12
        if v:
            raise ValueError("value does not fit the declared depth")
        return cls(tuple(reversed(keys)))

    def __str__(self) -> str:
        return "/".join(str(k) for k in self.keys)


@dataclass(frozen=True)
class Barycentric:
    """A point inside the terminal tetrahedron.

    Stored as exact :class:`Fraction` so that "sums to one" is a fact
    rather than a floating-point aspiration.
    """

    lam: tuple[Fraction, Fraction, Fraction, Fraction]

    def __post_init__(self) -> None:
        if len(self.lam) != 4:
            raise ValueError("a tetrahedron has four barycentric weights")
        if sum(self.lam) != 1:
            raise ValueError(
                f"barycentric weights must sum to exactly 1, got "
                f"{sum(self.lam)}")

    @property
    def inside(self) -> bool:
        return all(0 <= x <= 1 for x in self.lam)

    @classmethod
    def from_ints(cls, a: int, b: int, c: int, d: int) -> "Barycentric":
        tot = a + b + c + d
        if tot == 0:
            raise ValueError("weights must not all be zero")
        return cls(tuple(Fraction(x, tot) for x in (a, b, c, d)))


# --------------------------------------------------------------------
# Destination certificate
# --------------------------------------------------------------------

@dataclass
class DestinationCertificate:
    """Everything required to certify a destination (core/12)."""

    root_id: str
    frame_graph: FrameGraph
    epoch_tt_s: float
    time_scale: str
    ephemeris_or_model: str
    key_path: KeyPath
    local_coordinate: Barycentric
    phase_authority: str
    uncertainty_m: float
    authentication: str | None
    payload_policy: str
    #: What the address *means*. Undeclared semantics is a refusal.
    address_semantics: str | None = None

    def digest(self) -> str:
        blob = json.dumps({
            "root": self.root_id,
            "keys": list(self.key_path.keys),
            "lam": [str(x) for x in self.local_coordinate.lam],
            "epoch": self.epoch_tt_s,
            "scale": self.time_scale,
            "eph": self.ephemeris_or_model,
            "phase": self.phase_authority,
        }, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()


def validate_destination(cert: DestinationCertificate,
                         *,
                         now_tt_s: float,
                         validity_s: float = 86_400.0,
                         uncertainty_policy_m: float = 1e6,
                         known_ephemerides: tuple[str, ...] = (),
                         ) -> dict:
    """Check every refusal condition in core/12.

    Returns a report rather than raising, so a caller can see *all*
    the reasons a destination failed instead of only the first.
    """
    problems: list[str] = []

    if cert.root_id not in ROOTS:
        problems.append("ROOT_MISSING")

    ok, why = cert.frame_graph.composes()
    if not ok:
        problems.append("FRAMES_DO_NOT_COMPOSE")

    if cert.epoch_tt_s is None:
        problems.append("EPOCH_ABSENT")
    elif now_tt_s - cert.epoch_tt_s > validity_s:
        problems.append("EPOCH_EXPIRED")

    if known_ephemerides and \
            cert.ephemeris_or_model not in known_ephemerides:
        problems.append("EPHEMERIS_UNKNOWN")

    if not cert.local_coordinate.inside:
        problems.append("COORDINATE_OUTSIDE_CELL")

    if cert.uncertainty_m > uncertainty_policy_m:
        problems.append("UNCERTAINTY_EXCEEDS_POLICY")

    if not cert.authentication:
        problems.append("AUTHENTICATION_FAILED")

    if not cert.address_semantics:
        problems.append("ADDRESS_SEMANTICS_UNDECLARED")

    return {
        "certificate": cert.digest(),
        "ok": not problems,
        "status": "DESTINATION_CERTIFIED" if not problems
                  else "DESTINATION_REFUSED",
        "refusals": problems,
        "frame_chain_note": why,
        "uncertainty_m": cert.uncertainty_m,
    }


# --------------------------------------------------------------------
# The physical boundary
# --------------------------------------------------------------------

def route_locally(cert: DestinationCertificate, payload_id: str) -> dict:
    """Route a payload to a *local* endpoint named by the address.

    This is the only supported delivery. The address is a name in a
    declared hierarchy; delivery happens over an ordinary local
    protocol to an ordinary local store.
    """
    return {
        "payload_id": payload_id,
        "certificate": cert.digest(),
        "delivered_to": "LOCAL_ENDPOINT",
        "key_path": str(cert.key_path),
        "note": ("the key path names a destination in a declared "
                 "hierarchy; the payload was written locally"),
        "evidence_class": "SYNTHETIC_MODEL",
    }


def refuse_nonlocal_delivery(cert: DestinationCertificate,
                             *args, **kwargs):
    """Always refuses. Naming a destination is not reaching it.

    No mechanism in R6 couples an apparatus to the celestial body a
    key path happens to name. An address field containing a star is a
    string in a database.
    """
    raise RouteRefused(
        "ADDRESS_SEMANTICS_UNDECLARED",
        "the mailbox routes information locally through a declared "
        "protocol and establishes no nonlocal coupling to the "
        "celestial destination represented by the address "
        "(r6 FORBIDDEN_COLLAPSES: ADDRESS_IS_A_CHANNEL). Use "
        "route_locally() for the supported operation")


def laboratory_scale_model(au_m: float = 1.495978707e11,
                           lab_extent_m: float = 1.0) -> dict:
    """The 'laboratory AU' analogy, with its scale factor made explicit.

    The source corpus reasons about celestial structure reproduced at
    bench scale. Recording the ratio is the honest way to hold that
    idea: a 1 m apparatus is ~1.5e-11 of an astronomical unit, and no
    physical law is scale invariant across eleven orders of magnitude.
    The analogy is a naming convenience for nested cells, nothing more.
    """
    ratio = lab_extent_m / au_m
    return {
        "au_m": au_m,
        "lab_extent_m": lab_extent_m,
        "ratio": ratio,
        "orders_of_magnitude": -11 if ratio else 0,
        "status": "ANALOGY_ONLY",
        "note": ("a scale ratio is not a similarity transform; "
                 "gravitational, electromagnetic and quantum scales do "
                 "not co-transform, so bench structure does not model "
                 "celestial structure"),
    }
