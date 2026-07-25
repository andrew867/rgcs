"""P30 -- the laser-trim planning simulator: plan mass-removal, never fire.

This is the laser-trim *planning* lane of the R15 platform. It fires no
laser, cuts no copper, and reads no frequency. What it *does* is stand up,
in software, the full apparatus a frequency-trim of a resonator would need
-- a mass-to-frequency model (the Sauerbrey relation ``Delta f = -C_f *
Delta m`` from :mod:`r13.qcmstack`), a geometry of trimmable features
(copper islands, tabs, rings, perforations and coupons), a separation of
mass, trace and substrate removal, a laser safety envelope (a per-pulse
energy cap and keep-out zones around electrodes and mounts), and a
closed-loop *measure-predict-trim-verify* planner that converges a synthetic
resonator to a target frequency -- and it keeps strict track of what could
be planned versus what was actually done to hardware, which is nothing.

**Ablation is irreversible; the plan approaches from the safe side.** Laser
ablation removes mass and cannot add it back. Per Sauerbrey, removing mass
*raises* the frequency, monotonically, and there is no undo: a step taken
is a step that cannot be reversed. So the planner is deliberately timid --
each iteration closes only a fraction of the remaining gap, so the frequency
climbs toward the target *from below* and never crosses it. A plan whose
predicted trajectory overshoots the target is rejected outright by
:func:`assert_plan_no_overshoot` / :func:`refuse_overshoot_plan`, because an
overshoot on an irreversible edit is unrecoverable.

**One planner interface, four honest modes.** ``SYNTHETIC`` plans and
verifies against a seeded synthetic resonator and emits *no physical
command*. ``REPLAY`` re-reads a stored plan's predicted states and issues
nothing new. ``FAULT_INJECTION`` perturbs the model sensitivity to exercise
the predictor's uncertainty, still emitting no command. ``REAL`` is an
interface only: there is no laser trimmer in this repository, so a real
trim acquires and does *nothing* -- it raises :class:`NoLaserHardwareError`
and offers a ``blocked_receipt`` whose physical run is
``BLOCKED_MISSING_INPUT``.

**The load-bearing line.** A converged trim plan here is a
``MODEL_PREDICTION`` over a synthetic resonator -- a plan, never an executed
trim. No laser was fired and no copper was removed, so
:func:`refuse_plan_as_executed_trim` draws that line and the REAL trimmer
fires nothing. Substrate (FR-4) cutting is never a default: a site that
asks to cut substrate is refused unless the envelope explicitly authorises
it.

This module extends the R10-R13 authorities -- it reuses
:func:`r13.qcmstack.sauerbrey_delta_f` and
:func:`r13.qcmstack.sauerbrey_constant` for the mass/frequency model,
:func:`r10.microcrystal.make_13mhz_resonator` for the synthetic resonator it
trims, and :func:`r13.apparatus.refuse_design_as_measurement` for the
unbuilt-hardware refusal -- and it is typed against the R15 claim taxonomy
in :mod:`r15.claims`.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r15 import claims
from r13.qcmstack import (BVDResonator, DEFAULT_RESONATOR, sauerbrey_delta_f,
                          sauerbrey_constant)
from r13 import apparatus as _apparatus
from r10.microcrystal import Resonator, make_13mhz_resonator


# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "LASER_TRIM_PLANNER_TYPED_NO_LASER_PLAN_ONLY_NO_OVERSHOOT"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
#: A real trim needs a built laser trimmer, which does not exist here.
PHYSICAL_RUN = "BLOCKED_MISSING_INPUT"

#: The no-undo warning surfaced on every plan and report.
IRREVERSIBLE_WARNING = (
    "laser ablation is IRREVERSIBLE: mass removed cannot be added back and a "
    "trim step cannot be undone. Plan conservatively and approach the target "
    "from the safe side (frequency climbs from below); never overshoot.")

#: A converged trim plan is a model prediction over a synthetic resonator.
PLAN_CLAIM_CLASS = claims.ClaimClass.MODEL_PREDICTION
#: The simulated measure-predict-trim-verify loop is a synthetic observation.
LOOP_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: The class of the planner machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED


class TrimPlannerError(RuntimeError):
    """Raised on any planner refusal or structural guard.

    Covers the guards (a non-finite value, no trimmable site, an empty plan)
    and is the base of :class:`NoLaserHardwareError`,
    :class:`OvershootError`, :class:`KeepOutViolation`,
    :class:`SubstrateCutRefused` and :class:`UnreachableTargetError`.
    """


class NoLaserHardwareError(TrimPlannerError):
    """Raised when a REAL trimmer is asked to fire.

    There is no laser trimmer, positioning stage, or resonator here, so a
    real trim removes nothing. The command is BLOCKED at the hardware-access
    boundary and the physical run is BLOCKED_MISSING_INPUT.
    """


class OvershootError(TrimPlannerError):
    """Raised when a plan's predicted trajectory crosses the target.

    An overshoot on an irreversible ablation edit is unrecoverable, so a plan
    that overshoots is rejected rather than clamped.
    """


class KeepOutViolation(TrimPlannerError):
    """Raised when a trim site falls inside a keep-out zone.

    Keep-out zones guard electrodes and mounts; a pulse there would damage
    the part, so any site inside one is refused.
    """


class SubstrateCutRefused(TrimPlannerError):
    """Raised when a site asks to cut substrate without authority.

    Substrate (FR-4) removal is never a default: it is refused unless the
    envelope explicitly authorises it.
    """


class UnreachableTargetError(TrimPlannerError):
    """Raised when the target cannot be reached by removing mass.

    Ablation only *raises* frequency (it removes mass); a target below the
    current frequency would need mass *added*, which ablation cannot do.
    """


# --- small guards --------------------------------------------------------

def _finite(value: object, what: str) -> float:
    try:
        x = float(value)                              # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise TrimPlannerError(f"cannot read {value!r} as {what}") from None
    if not math.isfinite(x):
        raise TrimPlannerError(f"{what} must be finite, got {value!r}")
    return x


def _positive(value: object, what: str) -> float:
    x = _finite(value, what)
    if x <= 0.0:
        raise TrimPlannerError(f"{what} must be positive, got {x!r}")
    return x


def _nonneg(value: object, what: str) -> float:
    x = _finite(value, what)
    if x < 0.0:
        raise TrimPlannerError(f"{what} must be non-negative, got {x!r}")
    return x


# --- (1) the trimmable geometry: features, removal type, keep-out --------

class FeatureType(Enum):
    """The trimmable features a tuning edit can touch."""

    ISLAND = "island"
    TAB = "tab"
    RING = "ring"
    PERFORATION = "perforation"
    COUPON = "coupon"


class RemovalType(Enum):
    """What a pulse removes. Mass tuning is the default; the others are not.

    ``MASS`` removes electrode/copper mass -- the tuning mechanism modelled by
    Sauerbrey. ``TRACE`` cuts a conductor trace (an electrical edit).
    ``SUBSTRATE`` cuts the dielectric (FR-4); it is never a default and is
    refused unless the safety envelope authorises it.
    """

    MASS = "mass"
    TRACE = "trace"
    SUBSTRATE = "substrate"


class FreqDirection(Enum):
    """The direction a trim moves the frequency. Mass removal raises it."""

    RAISE = "raise"
    LOWER = "lower"


@dataclass(frozen=True)
class KeepOutZone:
    """A circular keep-out region (mm) around an electrode or a mount.

    A pulse inside the zone would damage the part; :meth:`contains` flags a
    site that falls within ``radius_mm`` of the centre.
    """

    name: str
    cx_mm: float
    cy_mm: float
    radius_mm: float

    def __post_init__(self) -> None:
        if not str(self.name):
            raise TrimPlannerError("a keep-out zone needs a name")
        _finite(self.cx_mm, "the keep-out centre x")
        _finite(self.cy_mm, "the keep-out centre y")
        _positive(self.radius_mm, "the keep-out radius")

    def contains(self, x_mm: float, y_mm: float) -> bool:
        dx = _finite(x_mm, "the site x") - self.cx_mm
        dy = _finite(y_mm, "the site y") - self.cy_mm
        return math.hypot(dx, dy) <= self.radius_mm


@dataclass(frozen=True)
class TrimSite:
    """A candidate location for a tuning edit on the part (mm).

    ``group`` labels a symmetry set: sites sharing a group are trimmed in
    equal amounts so a symmetric edit stays balanced. ``removal`` defaults to
    ``MASS`` -- the only removal type a default plan performs.
    """

    site_id: str
    feature: FeatureType
    x_mm: float
    y_mm: float
    removal: RemovalType = RemovalType.MASS
    group: str = "default"

    def __post_init__(self) -> None:
        if not str(self.site_id):
            raise TrimPlannerError("a trim site needs a site_id")
        if not isinstance(self.feature, FeatureType):
            raise TrimPlannerError("feature must be a FeatureType")
        if not isinstance(self.removal, RemovalType):
            raise TrimPlannerError("removal must be a RemovalType")
        _finite(self.x_mm, "the site x")
        _finite(self.y_mm, "the site y")


def symmetric_ring_sites(n: int, *, radius_mm: float = 3.0,
                         feature: FeatureType = FeatureType.RING,
                         group: str = "ring",
                         site_prefix: str = "s") -> tuple[TrimSite, ...]:
    """``n`` trim sites placed symmetrically on a ring, one symmetry group.

    A deterministic synthetic geometry: ``n`` equally-spaced sites at
    ``radius_mm`` from the origin, all in one symmetry ``group`` so a
    symmetric plan removes equal mass from each.
    """
    if int(n) < 1:
        raise TrimPlannerError("a ring needs at least one site")
    r = _positive(radius_mm, "the ring radius")
    sites = []
    for i in range(int(n)):
        theta = 2.0 * math.pi * i / int(n)
        sites.append(TrimSite(
            site_id=f"{site_prefix}{i}", feature=feature,
            x_mm=r * math.cos(theta), y_mm=r * math.sin(theta), group=group))
    return tuple(sites)


# --- (2) the laser safety envelope ---------------------------------------

@dataclass(frozen=True)
class LaserSafetyEnvelope:
    """The declared design bounds a trim plan is kept within.

    A bound, not a clearance: keeping a plan inside the envelope is a design
    discipline and does not authorise firing anything, because there is no
    laser. ``max_energy_per_pulse_j`` caps the per-pulse energy;
    ``ablation_yield_kg_per_j`` is the modelled mass removed per joule (a
    declared placeholder, not a measured yield); ``keep_out_zones`` guard
    electrodes and mounts; ``allow_substrate_removal`` is ``False`` so
    FR-4 cutting is never a default.
    """

    max_energy_per_pulse_j: float = 100.0e-6
    ablation_yield_kg_per_j: float = 1.0e-6
    max_total_removal_kg: float = 1.0e-8
    keep_out_zones: tuple[KeepOutZone, ...] = ()
    allow_substrate_removal: bool = False

    def __post_init__(self) -> None:
        _positive(self.max_energy_per_pulse_j, "the max energy per pulse")
        _positive(self.ablation_yield_kg_per_j, "the ablation yield")
        _positive(self.max_total_removal_kg, "the max total removal")
        for z in self.keep_out_zones:
            if not isinstance(z, KeepOutZone):
                raise TrimPlannerError("keep_out_zones must be KeepOutZones")

    @property
    def max_mass_per_pulse_kg(self) -> float:
        """The most mass one pulse may remove, ``energy_cap * yield``."""
        return self.max_energy_per_pulse_j * self.ablation_yield_kg_per_j

    def energy_for_mass_j(self, removed_kg: float) -> float:
        """The pulse energy a modelled mass removal implies."""
        return _nonneg(removed_kg, "the removed mass") \
            / self.ablation_yield_kg_per_j

    def pulses_for_mass(self, removed_kg: float) -> int:
        """Pulses needed to remove ``removed_kg`` within the per-pulse cap."""
        m = _nonneg(removed_kg, "the removed mass")
        if m == 0.0:
            return 0
        return int(math.ceil(m / self.max_mass_per_pulse_kg))

    def violated_zone(self, site: TrimSite) -> KeepOutZone | None:
        """The first keep-out zone a site falls inside, or ``None``."""
        for z in self.keep_out_zones:
            if z.contains(site.x_mm, site.y_mm):
                return z
        return None

    def check_site(self, site: TrimSite) -> None:
        """Refuse a site inside a keep-out zone or an unauthorised FR-4 cut."""
        if not isinstance(site, TrimSite):
            raise TrimPlannerError("check_site needs a TrimSite")
        if site.removal is RemovalType.SUBSTRATE \
                and not self.allow_substrate_removal:
            raise SubstrateCutRefused(
                f"refused: site {site.site_id!r} asks to cut SUBSTRATE (FR-4), "
                f"which is not a default trim. Substrate removal is authorised "
                f"only when the envelope sets allow_substrate_removal=True; "
                f"the default plan removes MASS only. {VERDICT}")
        zone = self.violated_zone(site)
        if zone is not None:
            raise KeepOutViolation(
                f"refused: site {site.site_id!r} at "
                f"({site.x_mm:.3f}, {site.y_mm:.3f}) mm falls inside keep-out "
                f"zone {zone.name!r} (r={zone.radius_mm} mm around its "
                f"electrode/mount); a pulse there would damage the part. "
                f"{VERDICT}")

    def as_dict(self) -> dict:
        return {
            "max_energy_per_pulse_j": self.max_energy_per_pulse_j,
            "ablation_yield_kg_per_j": self.ablation_yield_kg_per_j,
            "max_mass_per_pulse_kg": self.max_mass_per_pulse_kg,
            "max_total_removal_kg": self.max_total_removal_kg,
            "keep_out_zones": [z.name for z in self.keep_out_zones],
            "allow_substrate_removal": self.allow_substrate_removal,
            "note": ("declared design bounds; NOT a clearance to fire "
                     "anything -- there is no laser"),
        }


#: The default envelope: a modest per-pulse cap, no substrate cutting.
DEFAULT_ENVELOPE = LaserSafetyEnvelope()


# --- (3) the mass-to-frequency model (Sauerbrey) -------------------------

@dataclass(frozen=True)
class TrimModel:
    """The mass/frequency model a trim plan predicts through.

    Wraps the Sauerbrey sensitivity ``C_f`` (Hz per kg) from
    :mod:`r13.qcmstack`. Removing mass (a positive ``removed_kg``) gives
    ``Delta m < 0`` and, by ``Delta f = -C_f * Delta m``, a positive
    ``Delta f``: ablation *raises* the frequency, monotonically.
    ``rel_uncertainty`` is a declared one-sigma fractional uncertainty on the
    sensitivity, not a measured error.
    """

    Cf: float
    rel_uncertainty: float = 0.05

    def __post_init__(self) -> None:
        _positive(self.Cf, "the Sauerbrey mass sensitivity Cf")
        _nonneg(self.rel_uncertainty, "the relative uncertainty")

    @classmethod
    def from_frequency(cls, f0_hz: float, *, area_m2: float = 1.0e-4,
                       rel_uncertainty: float = 0.05) -> "TrimModel":
        """Build the model from a fundamental via ``sauerbrey_constant``."""
        cf = sauerbrey_constant(_positive(f0_hz, "the fundamental f0"),
                                area_m2=area_m2)
        return cls(Cf=cf, rel_uncertainty=rel_uncertainty)

    def delta_f_for_removed_mass(self, removed_kg: float) -> float:
        """Predicted frequency shift for removing ``removed_kg`` (>= 0).

        ``Delta f = -C_f * Delta m`` with ``Delta m = -removed_kg`` gives
        ``+C_f * removed_kg`` -- a raise.
        """
        m = _nonneg(removed_kg, "the removed mass")
        return sauerbrey_delta_f(-m, self.Cf)

    def removed_mass_for_delta_f(self, delta_f_hz: float) -> float:
        """Mass to remove to raise the frequency by ``delta_f_hz`` (>= 0)."""
        df = _nonneg(delta_f_hz, "the frequency raise")
        return df / self.Cf


def predict_frequency_change(model: TrimModel, removed_kg: float) -> dict:
    """Predict the direction, size and uncertainty of a frequency change.

    Returns the direction (``RAISE`` for a mass removal), the nominal
    ``Delta f``, and a one-sigma band from the model's relative uncertainty.
    A model prediction, never a measurement.
    """
    if not isinstance(model, TrimModel):
        raise TrimPlannerError("predict_frequency_change needs a TrimModel")
    df = model.delta_f_for_removed_mass(removed_kg)
    sigma = abs(df) * model.rel_uncertainty
    return {
        "direction": FreqDirection.RAISE.value,
        "delta_f_hz": df,
        "sigma_hz": sigma,
        "delta_f_lo_hz": df - sigma,
        "delta_f_hi_hz": df + sigma,
        "claim_class": PLAN_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": ("a model prediction from Sauerbrey Delta f = -Cf*Delta m; "
                 "no laser fired, no frequency read"),
    }


# --- (4) the trim plan: steps, overshoot guard, serialization ------------

@dataclass(frozen=True)
class TrimStep:
    """One planned edit: remove ``removed_kg`` at one site, predicted only.

    ``f_before_hz`` and ``f_after_hz`` are the model's predicted frequencies
    around the step; ``n_pulses`` and ``energy_j`` are what the envelope
    implies. Nothing here was fired.
    """

    index: int
    iteration: int
    site_id: str
    feature: FeatureType
    removal: RemovalType
    removed_kg: float
    n_pulses: int
    energy_j: float
    f_before_hz: float
    f_after_hz: float

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "iteration": self.iteration,
            "site_id": self.site_id,
            "feature": self.feature.value,
            "removal": self.removal.value,
            "removed_kg": self.removed_kg,
            "n_pulses": self.n_pulses,
            "energy_j": self.energy_j,
            "f_before_hz": self.f_before_hz,
            "f_after_hz": self.f_after_hz,
        }


def plan_overshoots(steps, f_target_hz: float, tolerance_hz: float,
                    direction: FreqDirection = FreqDirection.RAISE) -> bool:
    """Whether any step's predicted frequency crosses the target.

    For a ``RAISE`` trim, overshoot means a predicted ``f_after`` beyond
    ``f_target + tolerance`` -- past the far edge of the tolerance band, on
    the irreversible side.
    """
    tol = _nonneg(tolerance_hz, "the tolerance")
    ft = _finite(f_target_hz, "the target frequency")
    for s in steps:
        fa = _finite(s.f_after_hz, "a step f_after")
        if direction is FreqDirection.RAISE and fa > ft + tol:
            return True
        if direction is FreqDirection.LOWER and fa < ft - tol:
            return True
    return False


def assert_plan_no_overshoot(steps, f_target_hz: float, tolerance_hz: float,
                             direction: FreqDirection = FreqDirection.RAISE
                             ) -> None:
    """Raise :class:`OvershootError` if a plan overshoots the target."""
    if plan_overshoots(steps, f_target_hz, tolerance_hz, direction):
        raise OvershootError(
            f"refused: this plan's predicted trajectory overshoots the target "
            f"{f_target_hz} Hz beyond its tolerance {tolerance_hz} Hz. "
            f"Ablation is IRREVERSIBLE, so an overshoot is unrecoverable and "
            f"the plan is rejected: approach the target from the safe side "
            f"and close only a fraction of the gap per step. {VERDICT}")


@dataclass(frozen=True)
class TrimPlan:
    """A predicted trim plan: an ordered list of steps, never executed.

    ``claim_class`` is capped at ``MODEL_PREDICTION`` and can never be a
    measurement class; ``executed`` is always ``False`` -- a plan is a
    prediction, not a fired trim. The plan is checked for overshoot at
    construction: an overshooting plan cannot be built.
    """

    resonator_id: str
    f_start_hz: float
    f_target_hz: float
    tolerance_hz: float
    steps: tuple[TrimStep, ...]
    converged: bool
    f_final_hz: float
    direction: FreqDirection = FreqDirection.RAISE
    envelope: LaserSafetyEnvelope = DEFAULT_ENVELOPE
    claim_class: claims.ClaimClass = PLAN_CLAIM_CLASS
    executed: bool = False

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            claims.refuse_model_as_measurement()
        if self.executed:
            raise TrimPlannerError(
                "a TrimPlan is a prediction; it is never marked executed")
        assert_plan_no_overshoot(self.steps, self.f_target_hz,
                                 self.tolerance_hz, self.direction)

    def total_removed_kg(self) -> float:
        return float(sum(s.removed_kg for s in self.steps))

    def total_pulses(self) -> int:
        return int(sum(s.n_pulses for s in self.steps))

    def per_site_removed_kg(self) -> dict:
        """Cumulative modelled mass removed at each site."""
        out: dict[str, float] = {}
        for s in self.steps:
            out[s.site_id] = out.get(s.site_id, 0.0) + s.removed_kg
        return out

    def residual_hz(self) -> float:
        """Predicted signed distance still to the target (target - final)."""
        return self.f_target_hz - self.f_final_hz

    def digest(self) -> str:
        """A deterministic hash of the plan for canonical comparison."""
        parts = [f"{self.resonator_id}|{self.f_start_hz!r}|"
                 f"{self.f_target_hz!r}|{self.tolerance_hz!r}|"
                 f"{self.direction.value}"]
        for s in self.steps:
            parts.append(f"{s.index}:{s.site_id}:{s.removed_kg!r}:"
                         f"{s.f_after_hz!r}")
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()

    def as_dict(self) -> dict:
        return {
            "resonator_id": self.resonator_id,
            "f_start_hz": self.f_start_hz,
            "f_target_hz": self.f_target_hz,
            "tolerance_hz": self.tolerance_hz,
            "direction": self.direction.value,
            "n_steps": len(self.steps),
            "total_pulses": self.total_pulses(),
            "total_removed_kg": self.total_removed_kg(),
            "converged": bool(self.converged),
            "f_final_hz": self.f_final_hz,
            "residual_hz": self.residual_hz(),
            "overshoot": plan_overshoots(self.steps, self.f_target_hz,
                                         self.tolerance_hz, self.direction),
            "steps": [s.as_dict() for s in self.steps],
            "envelope": self.envelope.as_dict(),
            "plan_sha256": self.digest(),
            "executed": self.executed,
            "irreversible_warning": IRREVERSIBLE_WARNING,
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- (5) the planner ------------------------------------------------------

def plan_trim(f_start_hz: float, f_target_hz: float, model: TrimModel, *,
              sites, tolerance_hz: float = 1.0, safety_fraction: float = 0.5,
              max_iterations: int = 200, envelope: LaserSafetyEnvelope = None,
              resonator_id: str = "synthetic") -> TrimPlan:
    """Plan a mass-removal trim that converges to the target from below.

    Removes mass symmetrically across the ``MASS`` sites in equal amounts,
    closing only ``safety_fraction`` of the remaining gap each iteration so
    the predicted frequency climbs toward the target and never overshoots.
    Every site is checked against the safety envelope (keep-out zones,
    substrate authority) before any step is planned. The result is a
    ``MODEL_PREDICTION`` -- a plan, not a fired trim.
    """
    if not isinstance(model, TrimModel):
        raise TrimPlannerError("plan_trim needs a TrimModel")
    env = envelope if envelope is not None else DEFAULT_ENVELOPE
    f0 = _positive(f_start_hz, "the start frequency")
    ft = _positive(f_target_hz, "the target frequency")
    tol = _positive(tolerance_hz, "the tolerance")
    frac = _finite(safety_fraction, "the safety fraction")
    if not (0.0 < frac < 1.0):
        raise TrimPlannerError(
            "the safety fraction must lie strictly in (0, 1): each iteration "
            "closes only a fraction of the gap so the plan never overshoots")

    site_list = list(sites)
    if not site_list:
        raise TrimPlannerError("plan_trim needs at least one trim site")
    # validate every site against the envelope up front
    for s in site_list:
        if not isinstance(s, TrimSite):
            raise TrimPlannerError("every site must be a TrimSite")
        env.check_site(s)
    mass_sites = [s for s in site_list if s.removal is RemovalType.MASS]
    if not mass_sites:
        raise TrimPlannerError(
            "no MASS trim site available; mass removal is the tuning "
            "mechanism and substrate/trace cuts do not tune the frequency")

    # a target below the start cannot be reached by removing mass
    if ft < f0 - tol:
        raise UnreachableTargetError(
            f"refused: target {ft} Hz is below the start {f0} Hz. Ablation "
            f"only REMOVES mass, which RAISES the frequency; reaching a lower "
            f"target would need mass ADDED, which ablation cannot do. Approach "
            f"the target from the safe side (start below it). {VERDICT}")

    steps: list[TrimStep] = []
    f = f0
    total_removed = 0.0
    it = 0
    while (ft - f) > tol and it < max_iterations:
        remaining = ft - f
        close_hz = frac * remaining            # raise to plan this iteration
        total_mass = model.removed_mass_for_delta_f(close_hz)
        per_site = total_mass / len(mass_sites)
        if per_site <= 0.0:
            break
        for site in mass_sites:
            f_before = f
            n_pulses = env.pulses_for_mass(per_site)
            energy = env.energy_for_mass_j(per_site)
            df = model.delta_f_for_removed_mass(per_site)
            f_after = f_before + df
            steps.append(TrimStep(
                index=len(steps), iteration=it, site_id=site.site_id,
                feature=site.feature, removal=site.removal,
                removed_kg=per_site, n_pulses=n_pulses, energy_j=energy,
                f_before_hz=f_before, f_after_hz=f_after))
            f = f_after
            total_removed += per_site
        it += 1
        if total_removed > env.max_total_removal_kg:
            raise TrimPlannerError(
                f"refused: the plan's total removal {total_removed:.3e} kg "
                f"exceeds the envelope cap {env.max_total_removal_kg:.3e} kg; "
                f"the target is too far for this envelope. {VERDICT}")

    converged = abs(ft - f) <= tol
    return TrimPlan(
        resonator_id=str(resonator_id), f_start_hz=f0, f_target_hz=ft,
        tolerance_hz=tol, steps=tuple(steps), converged=converged,
        f_final_hz=f, direction=FreqDirection.RAISE, envelope=env)


def mass_imbalance_kg(plan: TrimPlan) -> float:
    """The worst per-site removal spread within a symmetry set.

    Zero for a symmetric plan: every mass site receives equal cumulative
    removal, so the max-minus-min over the sites is zero.
    """
    if not isinstance(plan, TrimPlan):
        raise TrimPlannerError("mass_imbalance_kg needs a TrimPlan")
    per_site = plan.per_site_removed_kg()
    if not per_site:
        return 0.0
    vals = list(per_site.values())
    return float(max(vals) - min(vals))


# --- (6) the measure-predict-trim-verify loop ----------------------------

def default_synthetic_resonator() -> Resonator:
    """The synthetic 13 MHz microcrystal the loop trims (from R10)."""
    return make_13mhz_resonator("P30_trim_target")


def simulate_trim_loop(*, detune_hz: float = 500.0, tolerance_hz: float = 1.0,
                       safety_fraction: float = 0.5,
                       resonator: Resonator = None,
                       sites=None, envelope: LaserSafetyEnvelope = None,
                       seed: int = 0) -> dict:
    """Run a synthetic measure-predict-trim-verify loop to a target.

    Plants a synthetic resonator detuned ``detune_hz`` *below* its nominal
    frequency (over-massed), then plans and simulates the trim that raises it
    back to nominal within ``tolerance_hz``, approaching from below. The
    convergence is a ``SYNTHETIC_OBSERVATION`` over a simulated resonator --
    no laser fired, no frequency read. Deterministic under ``seed``.
    """
    res = resonator if resonator is not None else default_synthetic_resonator()
    f_target = float(res.fs)
    f_start = f_target - _positive(detune_hz, "the detune")
    model = TrimModel.from_frequency(f_target)
    site_tuple = sites if sites is not None else symmetric_ring_sites(4)
    plan = plan_trim(f_start, f_target, model, sites=site_tuple,
                     tolerance_hz=tolerance_hz, safety_fraction=safety_fraction,
                     envelope=envelope, resonator_id=res.resonator_id)
    return {
        "seed": int(seed),
        "resonator_id": res.resonator_id,
        "f_target_hz": f_target,
        "f_start_hz": f_start,
        "f_final_hz": plan.f_final_hz,
        "tolerance_hz": float(tolerance_hz),
        "residual_hz": plan.residual_hz(),
        "converged": bool(plan.converged),
        "overshoot": plan_overshoots(plan.steps, f_target, tolerance_hz),
        "n_iterations": (plan.steps[-1].iteration + 1) if plan.steps else 0,
        "n_steps": len(plan.steps),
        "total_removed_kg": plan.total_removed_kg(),
        "mass_imbalance_kg": mass_imbalance_kg(plan),
        "plan_sha256": plan.digest(),
        "claim_class": LOOP_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "irreversible_warning": IRREVERSIBLE_WARNING,
        "note": ("a synthetic resonator converged to a target frequency by a "
                 "planned trim; nothing was fired and no frequency was read"),
    }


# --- (7) the four planner modes behind one executor ----------------------

class TrimMode(Enum):
    """The four modes behind the one trim-executor interface."""

    REAL = "REAL"
    SYNTHETIC = "SYNTHETIC"
    REPLAY = "REPLAY"
    FAULT_INJECTION = "FAULT_INJECTION"


class TrimExecutor:
    """The one trim-executor interface. Not fired directly."""

    def __init__(self, mode: TrimMode) -> None:
        self.mode = mode

    def run(self, plan: TrimPlan) -> dict:
        raise NotImplementedError


class RealLaserTrimmer(TrimExecutor):
    """A real trim executor with no laser behind it.

    Running a trim removes nothing: it raises :class:`NoLaserHardwareError`.
    It offers :meth:`blocked_receipt` so callers record the honest
    BLOCKED_MISSING_INPUT state instead of a fabricated trim.
    """

    def __init__(self, trimmer_id: str = "real_laser_trimmer") -> None:
        super().__init__(TrimMode.REAL)
        self.trimmer_id = str(trimmer_id)

    def run(self, plan: TrimPlan) -> dict:
        # borrow the R13 apparatus refusal: the trim head is an unbuilt design
        try:
            _apparatus.refuse_design_as_measurement(
                claim="the laser trimmer produced a physical trim",
                quantity="a resonator frequency")
        except _apparatus.ApparatusError as exc:
            raise NoLaserHardwareError(
                f"refused: {self.trimmer_id} is a REAL trimmer and no laser, "
                f"positioning stage or resonator exists in this repository, so "
                f"it fires NOTHING and removes NO mass. The trim is BLOCKED at "
                f"the hardware-access boundary, not faked. A physical trim is "
                f"{PHYSICAL_RUN}. {exc} {PHYSICAL_VALIDATION}. {VERDICT}"
            ) from exc

    def blocked_receipt(self) -> dict:
        """The honest BLOCKED / BLOCKED_MISSING_INPUT receipt for a real trim."""
        return {
            "trimmer_id": self.trimmer_id,
            "mode": self.mode.value,
            "status": "BLOCKED",
            "reason": ("no laser trimmer, positioning stage or resonator "
                       "present; fires nothing, removes no mass"),
            "fired": False,
            "physical_commands_emitted": 0,
            "n_pulses": 0,
            "claim_class": PHYSICAL_RUN,
            "physical_run": PHYSICAL_RUN,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "irreversible_warning": IRREVERSIBLE_WARNING,
        }


class SyntheticTrimSimulator(TrimExecutor):
    """A dry-run simulator: verifies a plan and emits no physical command."""

    def __init__(self, simulator_id: str = "synthetic_trim_simulator") -> None:
        super().__init__(TrimMode.SYNTHETIC)
        self.simulator_id = str(simulator_id)

    def run(self, plan: TrimPlan) -> dict:
        if not isinstance(plan, TrimPlan):
            raise TrimPlannerError("run needs a TrimPlan")
        # re-verify the plan against its own overshoot guard, dry-run only
        assert_plan_no_overshoot(plan.steps, plan.f_target_hz,
                                 plan.tolerance_hz, plan.direction)
        return {
            "simulator_id": self.simulator_id,
            "mode": self.mode.value,
            "dry_run": True,
            "physical_commands_emitted": 0,
            "fired": False,
            "n_steps_verified": len(plan.steps),
            "predicted_f_final_hz": plan.f_final_hz,
            "converged": bool(plan.converged),
            "plan_sha256": plan.digest(),
            "claim_class": LOOP_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "note": ("a dry-run verification of a plan; NO physical command "
                     "was emitted and no laser was fired"),
        }


class ReplayTrimExecutor(TrimExecutor):
    """Replays a stored plan's predicted states; emits nothing new."""

    def __init__(self, executor_id: str = "replay_trim_executor") -> None:
        super().__init__(TrimMode.REPLAY)
        self.executor_id = str(executor_id)

    def run(self, plan: TrimPlan) -> dict:
        if not isinstance(plan, TrimPlan):
            raise TrimPlannerError("run needs a TrimPlan")
        return {
            "executor_id": self.executor_id,
            "mode": self.mode.value,
            "physical_commands_emitted": 0,
            "fired": False,
            "replayed_f_final_hz": plan.f_final_hz,
            "plan_sha256": plan.digest(),
            "claim_class": LOOP_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "note": "replays a stored plan; reads back predictions, fires nothing",
        }


class FaultInjectionTrimExecutor(TrimExecutor):
    """Perturbs the model sensitivity to exercise the predictor; fires nothing.

    Deterministic under ``seed``: scales the plan's implied ``Cf`` by a
    seeded factor to see how the predicted final frequency would move under a
    mis-estimated sensitivity. Still emits no physical command.
    """

    def __init__(self, model: TrimModel, *,
                 executor_id: str = "fault_trim_executor",
                 sensitivity_error: float = 0.1) -> None:
        super().__init__(TrimMode.FAULT_INJECTION)
        if not isinstance(model, TrimModel):
            raise TrimPlannerError("FaultInjectionTrimExecutor needs a TrimModel")
        self.executor_id = str(executor_id)
        self.model = model
        self.sensitivity_error = _nonneg(sensitivity_error,
                                         "the sensitivity error")

    def run(self, plan: TrimPlan, *, seed: int = 0) -> dict:
        if not isinstance(plan, TrimPlan):
            raise TrimPlannerError("run needs a TrimPlan")
        rng = np.random.default_rng(int(seed))
        factor = 1.0 + self.sensitivity_error * float(rng.standard_normal())
        factor = max(factor, 1e-6)
        # under a mis-estimated Cf, the same removed mass yields a different df
        perturbed_final = plan.f_start_hz + factor * (
            plan.f_final_hz - plan.f_start_hz)
        return {
            "executor_id": self.executor_id,
            "mode": self.mode.value,
            "seed": int(seed),
            "sensitivity_factor": factor,
            "physical_commands_emitted": 0,
            "fired": False,
            "nominal_f_final_hz": plan.f_final_hz,
            "perturbed_f_final_hz": perturbed_final,
            "claim_class": LOOP_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "note": ("a fault-injection run over a mis-estimated sensitivity; "
                     "no physical command emitted"),
        }


# --- (8) the load-bearing refusals ---------------------------------------

def refuse_plan_as_executed_trim(
        claim: str = "a trim plan is an executed physical trim") -> None:
    """Refuse a plan read as an executed trim. Always raises.

    :func:`plan_trim` produces a ``MODEL_PREDICTION`` over a synthetic
    resonator. No laser was fired, no copper removed and no frequency read,
    so the plan is a prediction, not a trim. An executed trim is
    BLOCKED_MISSING_INPUT pending a built, calibrated laser trimmer.
    """
    try:
        claims.refuse_model_as_measurement()
    except claims.ClaimError as exc:
        raise TrimPlannerError(
            f"refused: {claim!r}. {exc} A trim plan is a {PLAN_CLAIM_CLASS.value} "
            f"over a synthetic resonator; no laser was fired and no mass "
            f"removed, so an executed trim is {PHYSICAL_RUN}. "
            f"{PHYSICAL_VALIDATION}. {VERDICT}") from exc


def refuse_overshoot_plan(f_target_hz: float = 0.0, f_after_hz: float = 0.0,
                          tolerance_hz: float = 0.0) -> None:
    """Refuse an overshooting plan. Always raises.

    An overshoot on an irreversible ablation edit cannot be undone, so a plan
    whose predicted frequency crosses the target is rejected outright.
    """
    raise OvershootError(
        f"refused: a predicted f_after {f_after_hz} Hz overshoots the target "
        f"{f_target_hz} Hz beyond tolerance {tolerance_hz} Hz. Laser ablation "
        f"is IRREVERSIBLE; an overshoot is unrecoverable, so the plan is "
        f"rejected. Approach from the safe side and close a fraction of the "
        f"gap per step. {VERDICT}")


# --- (9) the report -------------------------------------------------------

def trim_planner_report() -> dict:
    """The standing statement of what the trim planner is and is not."""
    loop = simulate_trim_loop()
    return {
        "what_this_is": (
            "the R15 laser-trim PLANNING simulator: a Sauerbrey mass-to-"
            "frequency model (Delta f = -Cf*Delta m), a geometry of trimmable "
            "features (islands, tabs, rings, perforations, coupons) with "
            "separated mass/trace/substrate removal, a laser safety envelope "
            "(per-pulse energy cap and keep-out zones), and a measure-predict-"
            "trim-verify planner that converges a synthetic resonator to a "
            "target frequency from the safe side without overshoot -- behind "
            "one executor interface with four modes"),
        "modes": [m.value for m in TrimMode],
        "features": [f.value for f in FeatureType],
        "removal_types": [r.value for r in RemovalType],
        "default_removal": RemovalType.MASS.value,
        "convergence_demo": {
            "converged": loop["converged"],
            "residual_hz": loop["residual_hz"],
            "overshoot": loop["overshoot"],
            "mass_imbalance_kg": loop["mass_imbalance_kg"],
        },
        "reuses": [
            "r13.qcmstack.sauerbrey_delta_f / sauerbrey_constant (mass/freq "
            "model)",
            "r10.microcrystal.make_13mhz_resonator (the synthetic resonator "
            "trimmed)",
            "r13.apparatus.refuse_design_as_measurement (unbuilt-hardware "
            "refusal for the REAL trimmer)",
            "r15.claims (claim taxonomy and forbidden promotions)",
        ],
        "refusals": [
            "RealLaserTrimmer.run raises NoLaserHardwareError (fires nothing; "
            "BLOCKED_MISSING_INPUT)",
            "an overshooting plan cannot be constructed (assert_plan_no_"
            "overshoot / refuse_overshoot_plan raise OvershootError)",
            "a site in a keep-out zone is refused (KeepOutViolation)",
            "substrate (FR-4) cutting is refused unless authorised "
            "(SubstrateCutRefused)",
            "a target below the start is unreachable by removing mass "
            "(UnreachableTargetError)",
            "refuse_plan_as_executed_trim (a plan is not a fired trim)",
        ],
        "plan_claim_class": PLAN_CLAIM_CLASS.value,
        "loop_claim_class": LOOP_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "envelope": DEFAULT_ENVELOPE.as_dict(),
        "irreversible_warning": IRREVERSIBLE_WARNING,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "physical_run": PHYSICAL_RUN,
        "hardware_status": (
            "no laser trimmer, positioning stage or resonator exists here; a "
            "REAL trim is BLOCKED and fires nothing"),
        "what_would_change_this": (
            "a built, calibrated laser trimmer over a real resonator on a "
            "positioning stage, with a measured mass sensitivity, a raw "
            "before/after frequency capture, a clock binding and an "
            "environment log -- none of which exists in this repository"),
        "what_this_does_not_say": (
            "It does not say any resonator was trimmed. A plan is a "
            "MODEL_PREDICTION over a SYNTHETIC resonator; no laser was fired, "
            "no copper removed and no frequency read, a REAL trim fires "
            "nothing, and a MODEL_PREDICTION is never a PHYSICAL_MEASUREMENT. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "PHYSICAL_RUN",
    "IRREVERSIBLE_WARNING", "PLAN_CLAIM_CLASS", "LOOP_CLAIM_CLASS",
    "SOFTWARE_CLAIM_CLASS",
    "TrimPlannerError", "NoLaserHardwareError", "OvershootError",
    "KeepOutViolation", "SubstrateCutRefused", "UnreachableTargetError",
    "FeatureType", "RemovalType", "FreqDirection", "KeepOutZone", "TrimSite",
    "symmetric_ring_sites",
    "LaserSafetyEnvelope", "DEFAULT_ENVELOPE",
    "TrimModel", "predict_frequency_change",
    "TrimStep", "plan_overshoots", "assert_plan_no_overshoot", "TrimPlan",
    "plan_trim", "mass_imbalance_kg",
    "default_synthetic_resonator", "simulate_trim_loop",
    "TrimMode", "TrimExecutor", "RealLaserTrimmer", "SyntheticTrimSimulator",
    "ReplayTrimExecutor", "FaultInjectionTrimExecutor",
    "refuse_plan_as_executed_trim", "refuse_overshoot_plan",
    "trim_planner_report",
]
