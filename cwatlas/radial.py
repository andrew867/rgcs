"""P29 — Radial shell, altitude, and effective-potential mapping.

This maps a *radial coordinate* to a body-relative shell band (reusing the
shell registry in :mod:`cwatlas.shells`) and an altitude position within that
band, under a **declared radial convention** (a :class:`RadialProfile`). Four
conventions are declared: ``SURFACE``, ``ATMOSPHERE``, ``ORBIT``, and a
dimensionless ``DIMENSIONLESS`` convention. Each is a named, versioned profile;
none is a hidden default.

Two governance facts shape the design:

* **"Effective potential" is a nonliteral label.** It is SOURCE ontology — a
  re-expression of the shell ordinal, at most a ``SOURCE_CLAIM``. It is never a
  physical potential (no energy, no gravity, no field is claimed). Asking to
  treat an effective-potential label as a physical potential is a typed
  refusal.
* **The ``8 <-> 0`` closure stays opt-in.** Resolving a shell-8 mapping back to
  shell 0 goes through :func:`cwatlas.shells.apply_shell_closure`, which is off
  by default (System Contract invariant 8).

The radial <-> (shell, altitude) map is reversible: mapping a radial value to a
``(shell_index, altitude_in_band)`` pair and back reproduces the radial value
within a declared quantization. Band edges are dimensionless source-ontology
band ordinals; a profile's ``band_width`` and ``datum_offset`` are declared
convention constants, not measured physics.

Pure arithmetic. Nothing here measures anything; every input is passed in.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cwatlas import shells
from cwatlas.claims import ClaimClass, ClaimError

#: Round-trip tolerance for radial <-> (shell, altitude), in band ordinals.
RADIAL_ROUND_TRIP_TOL = 1e-9


class RadialError(ValueError):
    """Raised on an invalid, out-of-range, or underdetermined radial input.

    An explicit result state, never a silent guess.
    """


@dataclass(frozen=True)
class RadialProfile:
    """A declared radial convention mapping a radial value to band ordinals.

    A radial value ``r`` (in ``unit``) maps to a dimensionless band ordinal

        ``u = (r - datum_offset) / band_width``

    which must fall in ``[0, SHELL_MAX]``. ``band_width`` and ``datum_offset``
    are *declared* convention constants; they are not measured, and the label
    they carry is nonliteral SOURCE ontology.
    """

    profile_id: str
    version: str
    unit: str
    datum_offset: float
    band_width: float
    claim_class: ClaimClass = ClaimClass.SOURCE_CLAIM

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise RadialError("a radial profile must declare a profile_id.")
        if not self.version:
            raise RadialError("a radial profile must declare a version.")
        if not self.unit:
            raise RadialError("a radial profile must declare a unit.")
        if not math.isfinite(self.band_width) or self.band_width <= 0.0:
            raise RadialError("band_width must be positive and finite.")
        if not math.isfinite(self.datum_offset):
            raise RadialError("datum_offset must be finite.")
        if self.claim_class not in (
            ClaimClass.SOURCE_CLAIM, ClaimClass.MATHEMATICAL_TRANSLATION):
            raise RadialError(
                "a radial convention label is nonliteral SOURCE ontology; it "
                "may only be SOURCE_CLAIM or MATHEMATICAL_TRANSLATION, not "
                f"{self.claim_class.value}.")

    @property
    def profile_key(self) -> str:
        return f"{self.profile_id}@{self.version}"


#: The four declared radial conventions. Band widths / datums are declared
#: source-ontology convention constants (not measured metres of physics).
RADIAL_PROFILES: dict[str, RadialProfile] = {
    "DIMENSIONLESS@1.0.0": RadialProfile(
        "DIMENSIONLESS", "1.0.0", unit="band_ordinal",
        datum_offset=0.0, band_width=1.0),
    "SURFACE@1.0.0": RadialProfile(
        "SURFACE", "1.0.0", unit="m",
        datum_offset=0.0, band_width=1_000.0),
    "ATMOSPHERE@1.0.0": RadialProfile(
        "ATMOSPHERE", "1.0.0", unit="m",
        datum_offset=0.0, band_width=10_000.0),
    "ORBIT@1.0.0": RadialProfile(
        "ORBIT", "1.0.0", unit="m",
        datum_offset=0.0, band_width=100_000.0),
}


#: Nonliteral "effective-potential" labels, one per shell ordinal. These are
#: SOURCE ontology re-expressions of the shell ordinal, NOT physical potentials.
EFFECTIVE_POTENTIAL_LABELS: dict[int, str] = {
    i: f"EFFECTIVE_POTENTIAL_ORDINAL_{i}"
    for i in range(shells.SHELL_MIN, shells.SHELL_MAX + 1)
}


def get_radial_profile(profile_key: str) -> RadialProfile:
    """Look up a declared radial convention, or refuse an unknown key."""
    try:
        return RADIAL_PROFILES[profile_key]
    except (KeyError, TypeError):
        raise RadialError(
            f"unknown radial profile {profile_key!r}; declared conventions "
            f"are {sorted(RADIAL_PROFILES)}.") from None


def effective_potential_label(shell_index: int) -> str:
    """Return the nonliteral effective-potential label for a shell ordinal.

    The label is SOURCE ontology — a re-expression of the shell ordinal — and
    is never a physical potential. See :func:`refuse_effective_potential_as_physical`.
    """
    shells.get_shell(shell_index)  # refuses unknown index
    return EFFECTIVE_POTENTIAL_LABELS[shell_index]


def refuse_effective_potential_as_physical(*_a, **_k) -> None:
    """Treating an effective-potential label as a physical potential is refused."""
    raise ClaimError(
        "refused: 'effective potential' is a NONLITERAL SOURCE-ontology label "
        "(a re-expression of the shell ordinal). It is not a physical "
        "potential: no energy, gravity, or field is measured or claimed. "
        "PHYSICAL_VALIDATION_NOT_CLAIMED.")


@dataclass(frozen=True)
class RadialMapping:
    """A radial coordinate resolved to a shell band and within-band altitude.

    ``band_ordinal`` is the dimensionless ordinal ``(r - datum) / band_width``.
    ``altitude_in_band`` is the position within the resolved shell band, in
    ``[0, 1]`` (and ``0`` for the surface datum, shell 0). The effective-
    potential label is nonliteral SOURCE ontology.
    """

    radial_value: float
    unit: str
    band_ordinal: float
    shell_index: int
    altitude_in_band: float
    body_id: str
    profile_key: str
    effective_potential_label: str
    claim_class: ClaimClass


def _band_ordinal_to_shell(u: float) -> int:
    """Resolve a band ordinal ``u`` in [0, SHELL_MAX] to a shell index.

    ``u == 0`` -> shell 0 (surface datum); ``u`` in ``(n-1, n]`` -> shell ``n``.
    """
    if u == 0.0:
        return shells.SHELL_MIN
    return int(math.ceil(u))


def radial_to_shell(
    profile: RadialProfile, radial_value: float, body_id: str,
) -> RadialMapping:
    """Map a radial coordinate to a shell band and within-band altitude."""
    if not body_id:
        raise RadialError("a radial mapping must declare a body_id.")
    if not math.isfinite(radial_value):
        raise RadialError(f"radial_value must be finite, got {radial_value!r}.")

    u = (radial_value - profile.datum_offset) / profile.band_width
    if not (shells.SHELL_MIN <= u <= shells.SHELL_MAX):
        raise RadialError(
            f"radial_value {radial_value!r} maps to band ordinal {u!r}, "
            f"outside the declared shell range "
            f"[{shells.SHELL_MIN}, {shells.SHELL_MAX}]; refusing to invent a "
            f"shell outside the ontology.")

    shell_index = _band_ordinal_to_shell(u)
    lower_edge = 0.0 if shell_index == 0 else float(shell_index - 1)
    altitude_in_band = u - lower_edge
    # Guard against tiny negative from float error at exact edges.
    if -RADIAL_ROUND_TRIP_TOL < altitude_in_band < 0.0:
        altitude_in_band = 0.0

    return RadialMapping(
        radial_value=float(radial_value),
        unit=profile.unit,
        band_ordinal=float(u),
        shell_index=shell_index,
        altitude_in_band=float(altitude_in_band),
        body_id=body_id,
        profile_key=profile.profile_key,
        effective_potential_label=effective_potential_label(shell_index),
        claim_class=profile.claim_class,
    )


def shell_to_radial(
    profile: RadialProfile, shell_index: int, altitude_in_band: float,
) -> float:
    """Inverse of :func:`radial_to_shell`: reconstruct the radial value.

    ``altitude_in_band`` must be in ``[0, 1]`` (and ``0`` for shell 0).
    """
    shells.get_shell(shell_index)  # refuses unknown index
    if not math.isfinite(altitude_in_band):
        raise RadialError("altitude_in_band must be finite.")
    if shell_index == 0:
        if abs(altitude_in_band) > RADIAL_ROUND_TRIP_TOL:
            raise RadialError(
                "shell 0 is the surface datum; altitude_in_band must be 0.")
        u = 0.0
    else:
        if not (0.0 <= altitude_in_band <= 1.0 + RADIAL_ROUND_TRIP_TOL):
            raise RadialError(
                f"altitude_in_band must be in [0, 1] for shell {shell_index}, "
                f"got {altitude_in_band!r}.")
        u = float(shell_index - 1) + altitude_in_band
    return profile.datum_offset + u * profile.band_width


def resolve_shell_closure(
    mapping: RadialMapping, apply_closure: bool = False,
) -> int:
    """Resolve the mapping's shell under the 8 <-> 0 closure (opt-in, off by default).

    Delegates to :func:`cwatlas.shells.apply_shell_closure`, which refuses a
    shell-8 -> 0 resolution unless ``apply_closure=True`` (invariant 8).
    """
    return shells.apply_shell_closure(mapping.shell_index, apply_closure=apply_closure)


def radial_report() -> dict:
    """P29 declaration receipt. Labels are nonliteral; nothing is measured."""
    return {
        "phase_id": "P29",
        "what_this_is": (
            "a radial coordinate -> (shell band, within-band altitude) mapping "
            "under four declared radial conventions (surface, atmosphere, "
            "orbit, dimensionless), reusing the shell registry; 'effective "
            "potential' is a nonliteral SOURCE-ontology label; the radial <-> "
            "(shell, altitude) map is reversible; the 8 <-> 0 closure stays "
            "opt-in."),
        "claim_class": ClaimClass.SOURCE_CLAIM.value,
        "radial_profiles": {
            k: {
                "unit": p.unit,
                "datum_offset": p.datum_offset,
                "band_width": p.band_width,
                "claim_class": p.claim_class.value,
            }
            for k, p in RADIAL_PROFILES.items()
        },
        "effective_potential_labels": EFFECTIVE_POTENTIAL_LABELS,
        "effective_potential_is_nonliteral": True,
        "round_trip_tolerance_band_ordinal": RADIAL_ROUND_TRIP_TOL,
        "shell_closure_opt_in": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "RADIAL_SHELL_ALTITUDE_REVERSIBLE_EFFECTIVE_POTENTIAL_NONLITERAL",
    }
