"""P03 — a sky-observation reconstruction engine, and why it says
"unidentified" by default.

A night-sky observation is not identified by how striking it was. It is
identified by a *catalog match* under a reconstructed geometry, and that
needs an exact timestamp, an exact location, and an angular path. Without
those, the honest verdict is ``UNIDENTIFIED_OBSERVATION`` or
``INSUFFICIENT_GEOMETRY`` -- not a guess, and certainly not a craft.

This module is the anonymized public engine. It takes the *kinematic
description* of an observation and ranks the ordinary candidates it is
consistent with; it never asserts an identity without a catalog match.
Any specific observation, its location, and its personal context stay in
the private journal and never enter this repository.

The kinematics do discriminate, and the engine is honest about how much:

* a **steady, non-blinking, constant-speed** point that crosses a large
  arc in seconds and makes no sound is *consistent with* a satellite in
  low Earth orbit (a bright pass crosses tens of degrees in a few
  seconds). That makes ``SATELLITE_CANDIDATE`` a leading ordinary
  hypothesis -- but "consistent with" is not "identified", and only a
  satellite-catalog match at the exact time and place confirms it.
* **blinking / navigation lights** shift weight toward ``AIRCRAFT``.
* **stationary or very slow** shifts toward ``ASTRONOMICAL``.

The engine ranks; it does not conclude. Confirmation is a catalog query
that this environment cannot run, so the terminal verdict here is
``PROSPECTIVE_HOLDOUT_REQUIRED`` / ``NO_CATALOG_MATCH`` (not run), never
``IDENTIFIED``.
"""

from __future__ import annotations

from dataclasses import dataclass


class ObservationError(ValueError):
    """Raised on a malformed observation record."""


@dataclass(frozen=True)
class Kinematics:
    """The anonymized kinematic description of an observation."""

    angular_span_deg: float | None      # arc crossed, if estimable
    duration_s: float | None
    steady: bool                        # no blink/shimmer/colour change
    silent: bool
    constant_speed: bool
    brighter_than_stars: bool

    @property
    def angular_speed_deg_s(self) -> float | None:
        if (self.angular_span_deg is None or self.duration_s in (None, 0)):
            return None
        return self.angular_span_deg / self.duration_s

    @property
    def geometry_sufficient(self) -> bool:
        return (self.angular_span_deg is not None
                and self.duration_s is not None)


def rank_ordinary_candidates(k: Kinematics) -> dict:
    """Score the ordinary candidates the kinematics are consistent with.

    Scores are relative plausibility weights, not probabilities, and the
    ranking never becomes an identification.
    """
    scores = {"SATELLITE_CANDIDATE": 0.0, "AIRCRAFT_CANDIDATE": 0.0,
              "ASTRONOMICAL_CANDIDATE": 0.0, "METEOR_CANDIDATE": 0.0}

    # Speed sets which candidates are in play; steadiness/silence breaks
    # ties among them. A deg/s-scale transit is consistent with BOTH a
    # satellite and an aircraft, so the speed credits both and the
    # blink/silence signal decides. A star (near-zero speed) and a meteor
    # (very fast) are distinguished by speed alone.
    sp = k.angular_speed_deg_s
    if sp is not None:
        if sp < 0.1:                                # barely moving
            scores["ASTRONOMICAL_CANDIDATE"] += 3.0
        elif sp > 10:                               # very fast streak
            scores["METEOR_CANDIDATE"] += 3.0
        else:                                       # deg/s scale transit
            scores["SATELLITE_CANDIDATE"] += 2.0    # ambiguous: both
            scores["AIRCRAFT_CANDIDATE"] += 2.0

    # the tie-breakers
    if not k.steady:                                # blinking / nav lights
        scores["AIRCRAFT_CANDIDATE"] += 2.0
    if not k.silent:
        scores["AIRCRAFT_CANDIDATE"] += 1.0
    if k.steady and k.silent and k.constant_speed:  # points to satellite
        scores["SATELLITE_CANDIDATE"] += 2.0
        scores["AIRCRAFT_CANDIDATE"] -= 1.0
    # a meteor is brief; a steady constant-speed light lasting seconds is
    # not a meteor even if fast
    if k.duration_s is not None and k.duration_s > 5 and k.constant_speed:
        scores["METEOR_CANDIDATE"] -= 2.0

    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return {"scores": scores, "leading": ranked[0][0],
            "ranked": [c for c, _ in ranked]}


def assess_observation(k: Kinematics) -> dict:
    """The honest verdict: consistent-with, never identified."""
    if not k.geometry_sufficient:
        return {
            "verdict": "INSUFFICIENT_GEOMETRY",
            "why": ("without an angular span and a duration there is no "
                    "reconstruction; the observation is recorded, not "
                    "identified"),
            "identity_claimed": False,
        }
    ranking = rank_ordinary_candidates(k)
    return {
        "verdict": "UNIDENTIFIED_OBSERVATION",
        "leading_ordinary_candidate": ranking["leading"],
        "ranked_candidates": ranking["ranked"],
        "angular_speed_deg_s": k.angular_speed_deg_s,
        "catalog_match": "NO_CATALOG_MATCH_RUN",
        "to_identify": (
            "an exact UTC timestamp and observer location, then a "
            "satellite/ISS/debris and aircraft-ADS-B catalog query at "
            "that time and place. This environment cannot run it, so "
            "identification is PROSPECTIVE_HOLDOUT_REQUIRED"),
        "identity_claimed": False,
        "note": (
            f"the kinematics are consistent with "
            f"{ranking['leading']} as a leading ordinary hypothesis, "
            f"but consistent-with is not identified, and no exotic "
            f"identity is asserted or excluded"),
    }


def refuse_identity_without_catalog(claimed_identity: str) -> None:
    """No identity -- ordinary or exotic -- without a catalog match."""
    raise ObservationError(
        f"cannot classify the observation as {claimed_identity!r}. "
        f"Identification requires a reconstructed geometry and a catalog "
        f"match at the exact time and place, which has not been run. The "
        f"honest status is UNIDENTIFIED_OBSERVATION -- neither a craft "
        f"nor a debunk, just not yet identified.")


def skytrack_report() -> dict:
    return {
        "default_verdict": "UNIDENTIFIED_OBSERVATION",
        "statuses": ["UNIDENTIFIED_OBSERVATION", "INSUFFICIENT_GEOMETRY",
                     "SATELLITE_CANDIDATE", "AIRCRAFT_CANDIDATE",
                     "ASTRONOMICAL_CANDIDATE", "NO_CATALOG_MATCH",
                     "IDENTIFIED", "UNRESOLVED"],
        "identification_requires": [
            "exact UTC timestamp", "observer location",
            "angular path polyline", "weather/cloud archive",
            "satellite + ISS + debris catalog query",
            "aircraft ADS-B query where coverage exists"],
        "evidence_class": "DERIVED_MATHEMATICS engine over private input",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not classify any specific observation, and it holds "
            "no personal observation record. It ranks ordinary "
            "candidates from kinematics and refuses to identify anything "
            "without a catalog match -- not calling an unknown a craft, "
            "and not calling it nothing either."),
    }
