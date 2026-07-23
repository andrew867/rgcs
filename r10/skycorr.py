"""P17 — sky-event / collective-observation correlation, and why a
coincidence in time is never an identification.

R10.7's :mod:`r10.skytrack` already refuses to identify a single
observation without a catalog match. This module extends that refusal to
the *collective* case: given a set of anonymized observation windows
(rough times, optionally rough directions) and a catalog of ordinary
events (satellite passes, launches, meteor showers, aircraft), it asks
whether the observations line up with the events more than chance would
produce -- and it reports that alignment **as a correlation only**.

The load-bearing rule is a refusal:

    a temporal (or even temporal-plus-angular) coincidence between an
    observation window and a catalog event is a *correlation*, not an
    *identification*. Two events sharing a clock reading do not thereby
    share a cause.

So :func:`correlate` returns matches but the verdict stays
``UNIDENTIFIED_CORRELATION_ONLY``, and
:func:`refuse_identity_from_correlation` raises rather than let a match
be read as "identified".

The statistics are held to the project's null+power discipline:

* **NULL (control).** :func:`time_shuffled_null` redraws the catalog
  event times at random over the observation span and rebuilds the
  distribution of match counts. If the real events are unrelated to the
  windows, the observed count sits inside that null and ``p`` is *not*
  small -- a coincidence rate is not evidence.
* **POWER.** Plant a catalog event that truly falls inside a window and
  the observed match count climbs above the null, so ``p`` becomes
  small. Both directions are required, or the pipeline proves nothing.
* **MULTIPLICITY.** Searching many catalog events for a hit inflates the
  chance of *some* hit; :func:`multiplicity_correct` applies the
  Bonferroni penalty for the number of events searched.

No location, no personal data, and no specific observation live here.
The module operates on anonymized windows only; any real sky observation,
its place, and its context stay in the private journal and never enter
this repository. No physical measurement is performed:
``PHYSICAL_VALIDATION_NOT_CLAIMED``.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import numpy as np

# Reused, not modified: the single-observation engine that already
# refuses identity without a catalog match. Correlation cannot upgrade
# its verdict, and this import keeps the two engines consistent.
from r10.skytrack import Kinematics, assess_observation


class SkyCorrError(ValueError):
    """Raised when a correlation is asked to become an identification,
    or on malformed correlation input."""


class EventKind(enum.Enum):
    """The ordinary catalog categories. UNKNOWN is not exotic; it is
    merely uncatalogued."""

    SATELLITE = "SATELLITE"
    LAUNCH = "LAUNCH"
    METEOR_SHOWER = "METEOR_SHOWER"
    AIRCRAFT = "AIRCRAFT"
    UNKNOWN = "UNKNOWN"


# --- anonymized inputs -------------------------------------------------

@dataclass(frozen=True)
class ObsWindow:
    """An anonymized observation window: rough times, optional rough
    direction. Deliberately holds NO location and NO personal data."""

    start_utc_s: float
    end_utc_s: float
    approx_azimuth_deg: float | None = None
    approx_elevation_deg: float | None = None

    def __post_init__(self) -> None:
        if self.end_utc_s < self.start_utc_s:
            raise SkyCorrError("observation window ends before it starts")

    @property
    def duration_s(self) -> float:
        return self.end_utc_s - self.start_utc_s

    @property
    def has_direction(self) -> bool:
        return (self.approx_azimuth_deg is not None
                and self.approx_elevation_deg is not None)


@dataclass(frozen=True)
class CatalogEvent:
    """An ordinary catalog event. Point in time, optional direction."""

    event_id: str
    time_utc_s: float
    kind: EventKind = EventKind.UNKNOWN
    azimuth_deg: float | None = None
    elevation_deg: float | None = None

    @property
    def has_direction(self) -> bool:
        return self.azimuth_deg is not None and self.elevation_deg is not None


@dataclass(frozen=True)
class Match:
    """A window/event coincidence. A correlation, never an identity."""

    window_index: int
    event_id: str
    kind: EventKind
    dt_s: float                      # signed gap to nearest window edge
    angular_sep_deg: float | None    # None when either lacks a direction
    identity_claimed: bool = False   # structurally always False


# --- the coincidence tests ---------------------------------------------

def _edge_gap_s(window: ObsWindow, event: CatalogEvent) -> float:
    """Seconds from the event time to the nearest window edge; 0 if the
    event falls inside the window."""
    if event.time_utc_s < window.start_utc_s:
        return event.time_utc_s - window.start_utc_s      # negative
    if event.time_utc_s > window.end_utc_s:
        return event.time_utc_s - window.end_utc_s        # positive
    return 0.0


def temporal_match(window: ObsWindow, event: CatalogEvent,
                   tol_s: float) -> bool:
    """True if the event time falls within ``tol_s`` of the window
    (inside, or within tol of either edge)."""
    if tol_s < 0:
        raise SkyCorrError("temporal tolerance must be non-negative")
    return abs(_edge_gap_s(window, event)) <= tol_s


def angular_separation_deg(az1: float, el1: float,
                           az2: float, el2: float) -> float:
    """Great-circle separation between two (azimuth, elevation) points,
    in degrees. Az is treated as longitude, el as latitude."""
    a1, e1, a2, e2 = np.radians([az1, el1, az2, el2])
    cos_sep = (np.sin(e1) * np.sin(e2)
               + np.cos(e1) * np.cos(e2) * np.cos(a1 - a2))
    return float(np.degrees(np.arccos(np.clip(cos_sep, -1.0, 1.0))))


def angular_match(window: ObsWindow, event: CatalogEvent,
                  ang_tol_deg: float) -> bool | None:
    """Angular coincidence check.

    Returns ``None`` when either side lacks a direction (no angular
    constraint applies), otherwise True/False against ``ang_tol_deg``.
    """
    if not (window.has_direction and event.has_direction):
        return None
    sep = angular_separation_deg(
        window.approx_azimuth_deg, window.approx_elevation_deg,
        event.azimuth_deg, event.elevation_deg)
    return sep <= ang_tol_deg


def _is_match(window: ObsWindow, event: CatalogEvent, tol_s: float,
              ang_tol_deg: float) -> bool:
    """A pair matches if it is a temporal coincidence AND, when both
    sides carry a direction, an angular coincidence too."""
    if not temporal_match(window, event, tol_s):
        return False
    ang = angular_match(window, event, ang_tol_deg)
    return ang is not False        # None (no angle) or True both pass


# --- correlation (returns matches; never identifies) -------------------

def correlate(windows, catalog, tol_s: float,
              ang_tol_deg: float = 5.0) -> dict:
    """Correlate observation windows against the catalog.

    Returns the matches and a match count, but the verdict is fixed at
    ``UNIDENTIFIED_CORRELATION_ONLY`` -- the matches are coincidences,
    not identifications, no matter how many there are.
    """
    matches: list[Match] = []
    for wi, w in enumerate(windows):
        for e in catalog:
            if _is_match(w, e, tol_s, ang_tol_deg):
                ang = angular_match(w, e, ang_tol_deg)
                sep = (None if ang is None else angular_separation_deg(
                    w.approx_azimuth_deg, w.approx_elevation_deg,
                    e.azimuth_deg, e.elevation_deg))
                matches.append(Match(
                    window_index=wi, event_id=e.event_id, kind=e.kind,
                    dt_s=_edge_gap_s(w, e), angular_sep_deg=sep))
    return {
        "verdict": "UNIDENTIFIED_CORRELATION_ONLY",
        "match_count": len(matches),
        "matches": matches,
        "n_windows": len(windows),
        "n_catalog_events": len(catalog),
        "identity_claimed": False,
        "note": (
            "matches are temporal (and where available angular) "
            "coincidences; a shared clock reading is not a shared cause, "
            "so nothing here is identified"),
    }


def refuse_identity_from_correlation(match: Match | dict) -> None:
    """A coincidence is not an identification. Always raises."""
    ref = match.event_id if isinstance(match, Match) else match.get(
        "event_id", "?")
    raise SkyCorrError(
        f"a correlation with catalog event {ref!r} is a coincidence in "
        f"time (and possibly direction), not an identification. Matching "
        f"a window to an ordinary event does not identify the "
        f"observation as that event, and matching nothing does not make "
        f"it exotic. The honest status stays "
        f"UNIDENTIFIED_CORRELATION_ONLY.")


# --- null + power ------------------------------------------------------

def _count_matches(windows, catalog, tol_s: float,
                   ang_tol_deg: float) -> int:
    return sum(1 for w in windows for e in catalog
               if _is_match(w, e, tol_s, ang_tol_deg))


def _span(windows) -> tuple[float, float]:
    starts = [w.start_utc_s for w in windows]
    ends = [w.end_utc_s for w in windows]
    return min(starts), max(ends)


def time_shuffled_null(windows, catalog, tol_s: float, *,
                       ang_tol_deg: float = 5.0, trials: int = 2000,
                       margin_s: float = 0.0, seed: int = 20260723) -> dict:
    """Redraw catalog event times at random over the observation span and
    rebuild the null distribution of match counts.

    Random, unrelated event times reproduce the coincidence rate the
    geometry alone produces, so the observed count sits inside the null
    and ``p`` is *not* small. A genuine excess (see the power test) pushes
    the observed count into the tail and ``p`` drops.

    The event *directions* are preserved; only the times are shuffled, so
    any angular constraint applies identically to observed and null.
    """
    if not windows or not catalog:
        raise SkyCorrError("need at least one window and one event")
    rng = np.random.default_rng(seed)
    lo, hi = _span(windows)
    lo -= margin_s
    hi += margin_s
    observed = _count_matches(windows, catalog, tol_s, ang_tol_deg)
    counts = np.empty(trials, dtype=int)
    for t in range(trials):
        times = rng.uniform(lo, hi, size=len(catalog))
        shuffled = [
            CatalogEvent(e.event_id, float(ts), e.kind,
                         e.azimuth_deg, e.elevation_deg)
            for e, ts in zip(catalog, times)]
        counts[t] = _count_matches(windows, shuffled, tol_s, ang_tol_deg)
    at_least = int(np.sum(counts >= observed))
    p = (at_least + 1) / (trials + 1)
    return {
        "observed_match_count": observed,
        "null_mean": float(counts.mean()),
        "null_max": int(counts.max()),
        "p_value": p,
        "trials": trials,
        "exceeds_null": bool(p < 0.05),
        "verdict": "UNIDENTIFIED_CORRELATION_ONLY",
        "note": ("a small p means the observations coincide with the "
                 "catalog more than chance; it still does NOT identify "
                 "them as those events"),
    }


def multiplicity_correct(p_value: float, n_events_searched: int) -> dict:
    """Bonferroni penalty for searching many catalog events for a hit."""
    if n_events_searched < 1:
        raise SkyCorrError("must have searched at least one event")
    if not 0.0 <= p_value <= 1.0:
        raise SkyCorrError("p_value must lie in [0, 1]")
    corrected = min(1.0, p_value * n_events_searched)
    return {
        "raw_p": p_value,
        "n_events_searched": n_events_searched,
        "corrected_p": corrected,
        "survives_at_0_05": bool(corrected < 0.05),
        "note": ("searching N events for a coincidence gives N chances "
                 "for a false hit; the raw p is corrected accordingly"),
    }


# --- consistency with the single-observation engine --------------------

def kinematic_context(k: Kinematics) -> dict:
    """Fold in R10.7's single-observation verdict, and state plainly that
    a correlation does not upgrade it.

    The skytrack engine already returns ``UNIDENTIFIED_OBSERVATION`` /
    ``INSUFFICIENT_GEOMETRY`` and never ``IDENTIFIED``; a temporal match
    found here cannot promote that verdict.
    """
    single = assess_observation(k)
    return {
        "skytrack_verdict": single["verdict"],
        "correlation_verdict": "UNIDENTIFIED_CORRELATION_ONLY",
        "correlation_upgrades_identity": False,
        "note": ("kinematics rank ordinary candidates and a correlation "
                 "adds a coincident catalog event; neither identifies the "
                 "observation, and the two engines agree on the refusal"),
    }


def skycorr_report() -> dict:
    return {
        "verdict": "UNIDENTIFIED_CORRELATION_ONLY",
        "event_kinds": [k.value for k in EventKind],
        "tests_provided": ["temporal_match", "angular_match", "correlate",
                           "time_shuffled_null", "multiplicity_correct"],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "holds_specific_observation": False,
        "what_this_does_not_say": (
            "It does not identify any observation, and it holds no "
            "specific observation, location, or personal record. It "
            "correlates anonymized windows against ordinary catalog "
            "events and reports the alignment as a coincidence rate "
            "only -- a temporal or angular match is never an "
            "identification, and the absence of a match never makes an "
            "observation exotic. No physical measurement is performed."),
    }
