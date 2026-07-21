"""P04/P05/P06/P07 — torus geometry, CW toroidal address, channels, signs.

The source material pictures the universe as a torus with "Source" at a
central zero-point, and information "broadcast outside ordinary time" to
a receiver selected by a CW vector. This module gives the geometry an
honest treatment and puts a hard firewall on the physics.

**A torus is ordinary geometry.** Major radius R, minor radius r, two
angles. Everything about the surface, winding, and addressing is
standard and exact, and none of it is a cosmological claim. Calling the
universe a torus is a picture; the picture's mathematics does not make
it true, any more than drawing the atom as a solar system makes
electrons planets.

**Toroidal electromagnetic fields are not spacetime torsion.** A torus
of current makes a perfectly ordinary magnetic field. "Torsion" in
general relativity is a property of a connection on spacetime. They
share a Latin root and nothing else, and
:func:`refuse_torsion_conflation` says so.

**"Broadcast outside time" gets a causality firewall.** Three channel
models are offered and typed honestly:

* ``CONVENTIONAL_DELAYED`` -- ordinary propagation at or below light
  speed, with a real latency. This is the baseline and it is the only
  one with a mechanism.
* ``SHARED_STATE`` -- a pre-established correlation read locally at both
  ends. Real (this is how entanglement statistics and shared clocks
  work), but it transmits **no information faster than light**, and the
  module enforces that.
* ``NONLOCAL_TRANSFER`` -- instantaneous information transfer. There is
  no known mechanism, it contradicts relativity, and it is pinned
  ``UNSUPPORTED``. :func:`refuse_instantaneous_channel` raises.

Nothing here is measured. No apparatus exists. The CW toroidal address
is a labelling scheme, not a router that reaches anywhere.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction

C_M_PER_S = 299_792_458          # exact, SI definition


class TorsionConflation(TypeError):
    """Raised when toroidal EM is called spacetime torsion."""


class CausalityViolation(RuntimeError):
    """Raised when a channel is claimed to beat light speed."""


# --- P04: ordinary torus geometry --------------------------------------

@dataclass(frozen=True)
class Torus:
    """A standard torus. R > r > 0 for a ring torus."""

    major_radius: float          # R, centre of tube to centre of torus
    minor_radius: float          # r, tube radius

    def __post_init__(self) -> None:
        if self.minor_radius <= 0 or self.major_radius <= 0:
            raise ValueError("radii must be positive")

    @property
    def is_ring_torus(self) -> bool:
        return self.major_radius > self.minor_radius

    def point(self, theta: float, phi: float) -> tuple[float, float, float]:
        """Surface point. theta = around the tube, phi = around the ring."""
        R, r = self.major_radius, self.minor_radius
        x = (R + r * math.cos(theta)) * math.cos(phi)
        y = (R + r * math.cos(theta)) * math.sin(phi)
        z = r * math.sin(theta)
        return (x, y, z)

    @property
    def surface_area(self) -> float:
        return 4 * math.pi ** 2 * self.major_radius * self.minor_radius

    @property
    def volume(self) -> float:
        return 2 * math.pi ** 2 * self.major_radius * self.minor_radius ** 2

    def central_zero_point(self) -> tuple[float, float, float]:
        """The centre of the hole -- the 'Source zero-point' picture.

        It is the origin. It is geometrically distinguished (the centre
        of symmetry) and physically unremarkable: there is nothing
        there, it is a hole.
        """
        return (0.0, 0.0, 0.0)


# --- P05: the CW toroidal address --------------------------------------

@dataclass(frozen=True)
class ToroidalAddress:
    """A hierarchical address: parent domain + toroidal fields + binding.

    Extends the HCM idea (parent scope, refinement, frame, epoch,
    uncertainty) with two toroidal angle fields. It is a label. It is
    not a position until frame and epoch are set, and it routes
    nowhere -- addressing a cell is not reaching it.
    """

    parent_domain: str
    theta_bits: int              # tube-angle refinement
    phi_bits: int                # ring-angle refinement
    theta_index: int
    phi_index: int
    frame: str
    epoch: str
    shell: str
    uncertainty: float

    def __post_init__(self) -> None:
        if not self.frame or not self.epoch:
            raise ValueError("frame and epoch are required for a position")
        if not 0 <= self.theta_index < (1 << self.theta_bits):
            raise ValueError("theta_index out of range")
        if not 0 <= self.phi_index < (1 << self.phi_bits):
            raise ValueError("phi_index out of range")
        if self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")

    @property
    def total_bits(self) -> int:
        return self.theta_bits + self.phi_bits

    def angles(self) -> tuple[float, float]:
        """Cell-centre (theta, phi) in radians."""
        theta = 2 * math.pi * (self.theta_index + 0.5) / (1 << self.theta_bits)
        phi = 2 * math.pi * (self.phi_index + 0.5) / (1 << self.phi_bits)
        return (theta, phi)

    def with_parent(self, outer: str) -> "ToroidalAddress":
        """Prepend a parent domain -- the recursive-scope operation."""
        return ToroidalAddress(
            f"{outer}/{self.parent_domain}", self.theta_bits, self.phi_bits,
            self.theta_index, self.phi_index, self.frame, self.epoch,
            self.shell, self.uncertainty)


# --- P06: channel models, with the causality firewall ------------------

CHANNEL_MODELS = {
    "CONVENTIONAL_DELAYED": {
        "mechanism": "propagation at or below c, finite latency",
        "faster_than_light": False,
        "status": "CONVENTIONAL_REFERENCE",
    },
    "SHARED_STATE": {
        "mechanism": ("pre-established correlation read locally; "
                      "no information crosses faster than light"),
        "faster_than_light": False,
        "status": "CONVENTIONAL_REFERENCE",
    },
    "NONLOCAL_TRANSFER": {
        "mechanism": "none known; contradicts relativity",
        "faster_than_light": True,
        "status": "UNSUPPORTED",
    },
}


def light_delay_seconds(distance_m: float) -> float:
    """The floor on latency for any information channel."""
    if distance_m < 0:
        raise ValueError("distance cannot be negative")
    return distance_m / C_M_PER_S


def assess_channel(model: str, distance_m: float,
                   claimed_latency_s: float) -> dict:
    """Is a claimed latency physically possible over this distance?"""
    if model not in CHANNEL_MODELS:
        raise ValueError(f"unknown channel model {model!r}")
    floor = light_delay_seconds(distance_m)
    spec = CHANNEL_MODELS[model]
    beats_light = claimed_latency_s < floor - 1e-12
    return {
        "model": model,
        "light_delay_floor_s": floor,
        "claimed_latency_s": claimed_latency_s,
        "beats_light_speed": beats_light,
        "status": spec["status"],
        "verdict": ("PHYSICALLY_IMPOSSIBLE" if beats_light
                    else "WITHIN_LIGHT_CONE"),
        "note": (
            "a latency below the light-delay floor would carry "
            "information faster than light and is refused" if beats_light
            else "consistent with ordinary propagation"),
    }


def refuse_instantaneous_channel(distance_m: float) -> None:
    """Instantaneous source broadcast is refused."""
    floor = light_delay_seconds(distance_m)
    raise CausalityViolation(
        f"instantaneous transfer over {distance_m:g} m is refused. The "
        f"light-delay floor is {floor:g} s, and no information channel "
        f"in this framework may beat it. 'Broadcast outside ordinary "
        f"time' has no mechanism, contradicts relativity, and is "
        f"UNSUPPORTED -- a shared pre-established state can look "
        f"instantaneous while transmitting nothing.")


# --- P07: sign conventions, so everything can be reversed --------------

#: Every handedness/direction fixed so a simulation or bench can flip
#: it unambiguously. +1 / -1 only; the physical meaning is named.
SIGN_CONVENTIONS = {
    "EARTH_ROTATION": (+1, "prograde / counterclockwise viewed from "
                           "above the north pole"),
    "EQUATORIAL_CIRCULATION": (+1, "eastward positive"),
    "COIL_ROTATION": (+1, "right-hand rule about the coil axis"),
    "CRYSTAL_AXIAL": (+1, "toward the eye-plane / transverse-generation "
                          "face positive"),
    "HANDEDNESS": (+1, "right-handed coordinate frame"),
}


def reverse_sign(name: str) -> tuple[int, str]:
    """Return the reversed convention -- reversal must be trivial."""
    if name not in SIGN_CONVENTIONS:
        raise ValueError(f"unknown convention {name!r}")
    sign, meaning = SIGN_CONVENTIONS[name]
    return (-sign, meaning)


# --- firewall -----------------------------------------------------------

def refuse_torsion_conflation() -> None:
    raise TorsionConflation(
        "a toroidal current makes an ordinary magnetic field. Spacetime "
        "torsion is a property of a connection in a metric-affine "
        "geometry. The two share a word and nothing physical. A coil is "
        "not a modification of spacetime, and no field this apparatus "
        "could produce curves or twists spacetime measurably.")


def toroid_report() -> dict:
    return {
        "torus_is_ordinary_geometry": True,
        "channels": {k: v["status"] for k, v in CHANNEL_MODELS.items()},
        "only_supported_channels": [
            k for k, v in CHANNEL_MODELS.items()
            if not v["faster_than_light"]],
        "sign_conventions": list(SIGN_CONVENTIONS),
        "firewalls": [
            "toroidal EM field is not spacetime torsion",
            "no information channel beats the light-delay floor",
            "a CW toroidal address is a label, not a router",
            "the central zero-point is a hole, not a source of energy",
        ],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not say the universe is a torus, that Source sits "
            "at a zero-point, that anything is broadcast outside time, "
            "or that a CW address reaches a destination. The torus "
            "geometry is exact and the cosmology is not entailed by it."),
    }
