"""R11 — planetary orbital levels versus atomic shells, and the null that eats them.

The proposed analogy is old and visually seductive: planets sit at
discrete radii around a star, electrons sit at discrete levels around a
nucleus, therefore (the argument goes) the two are the same law at
different scales. This module tests that analogy **without assuming it
is real**, and the result is that it does not survive its own control.

**Why an atomic orbital is not a planetary track.**
An atomic orbital is a *stationary state of a quantum field problem*:
a normalisable solution of the Schroedinger (or Dirac) equation in a
Coulomb potential, indexed by integers ``n, l, m`` that come out of
boundary conditions and single-valuedness, not out of history. The
electron has no track. It has a probability amplitude whose modulus
squared is a smeared cloud; ``l`` and ``m`` carry angular momentum
quantisation in units of hbar; the Pauli principle limits occupancy;
and the characteristic radius of a hydrogenic state scales as
``n**2 / Z`` because that is what the Coulomb eigenvalue problem
returns. Discreteness there is *forced*: intermediate ``n`` do not
exist.

A planet or a moon is a classical two-body-plus-perturbations object.
Its semi-major axis is a continuous constant of motion which could take
any value; the value it actually has is an accident of accretion,
angular-momentum transport in a disc, gas- and tide-driven migration,
resonance capture and escape, scattering, and (for satellites) tidal
evolution and collisional history. Nothing quantises it. There is no
``hbar``, no exclusion principle, no eigenvalue condition, and no
integer that is anything more than a label we assign after sorting the
bodies by distance. Intermediate orbits are perfectly legal and are
occupied wherever material survived.

So a resemblance between the two pictures is a resemblance between two
*sorted lists of increasing numbers*. That is not a shared physics. It
is not even a coincidence yet, because nobody has shown that the
sorted list is unusual. Which is what this module does.

**The trap.** To "fit" ``N`` sorted radii to a law you may choose the
functional family (five here), its free parameters (one to three
continuous, plus a whole discrete chain in the resonance model), the
index offset, and the normalising length. With that much freedom a
handful of sorted radii fits *something* almost always. The only
quantity that can be evidence is a residual smaller than **randomly
drawn sorted radii** achieve under the *same* search. That is the
``random_order_statistic`` control, and on the eight-planet set it is
competitive with the "meaningful" models. The headline is therefore a
negative: ``ORBITAL_ATOMIC_SCALING_UNESTABLISHED``.

**Normalisation discipline.** Radii are divided by a *declared* scale
for the whole system (primary body radius, Hill radius, Roche limit,
synchronous orbit). Re-optimising the normalisation separately per
target until each desired match appears is the single easiest way to
manufacture this result, and :func:`refuse_per_target_normalization`
raises rather than allow it.

**Nothing is measured here.** Every number is a published semi-major
axis or a published body radius, and every operation on them is
arithmetic. ``PHYSICAL_VALIDATION_NOT_CLAIMED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

#: The standing result of this module.
VERDICT_UNESTABLISHED = "ORBITAL_ATOMIC_SCALING_UNESTABLISHED"

EVIDENCE_CLASS = "DERIVED_MATHEMATICS"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Status for a model that cannot be evaluated because the inputs it
#: needs are not in this repository (and are not invented here).
BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


class ScalingError(ValueError):
    """Raised when a scaling claim exceeds what the arithmetic licenses."""


# --- declared normalisation --------------------------------------------

class ScaleKind(Enum):
    """The declared lengths a system may be normalised by.

    Exactly one is in force for a system at a time, it is declared up
    front, and it applies to every body in that system.
    """

    PRIMARY_BODY_RADIUS = "PRIMARY_BODY_RADIUS"
    HILL_RADIUS = "HILL_RADIUS"
    ROCHE_LIMIT = "ROCHE_LIMIT"
    SYNCHRONOUS_ORBIT = "SYNCHRONOUS_ORBIT"


@dataclass(frozen=True)
class NormalizationScale:
    """A declared length used to make radii dimensionless."""

    kind: ScaleKind
    value: float
    units: str
    basis: str
    approximate: bool = True

    def __post_init__(self) -> None:
        if not (self.value > 0) or not math.isfinite(self.value):
            raise ScalingError("a normalisation scale must be finite and > 0")


# --- the systems --------------------------------------------------------

@dataclass(frozen=True)
class OrbitalSystem:
    """One primary and its bodies, sorted outward, with a declared scale."""

    system_id: str
    primary: str
    units: str
    bodies: tuple[str, ...]
    semi_major_axis: tuple[float, ...]
    scale: NormalizationScale
    scales_available: tuple[NormalizationScale, ...] = ()
    source_note: str = "published semi-major axes"

    def __post_init__(self) -> None:
        if len(self.bodies) != len(self.semi_major_axis):
            raise ScalingError("bodies and semi-major axes must line up")
        if len(self.bodies) < 3:
            raise ScalingError("fewer than three bodies cannot test a law")
        a = np.asarray(self.semi_major_axis, float)
        if not np.all(np.isfinite(a)) or not np.all(a > 0):
            raise ScalingError("semi-major axes must be finite and > 0")
        if not np.all(np.diff(a) > 0):
            raise ScalingError("bodies must be listed strictly outward")
        if self.scale.units != self.units:
            raise ScalingError(
                f"scale is in {self.scale.units} but the system is in "
                f"{self.units}; a normalisation may not change units "
                f"silently")

    @property
    def n(self) -> int:
        return len(self.bodies)

    def index(self) -> np.ndarray:
        """The integer label 1..N. A label from sorting, not a quantum number."""
        return np.arange(1, self.n + 1, dtype=float)

    def normalized(self) -> np.ndarray:
        """Radii divided by the system's one declared scale."""
        return np.asarray(self.semi_major_axis, float) / self.scale.value


_SUN_RADIUS_AU = 0.00465047        # solar equatorial radius in AU
_JUPITER_RADIUS_KM = 71492.0       # equatorial
_SATURN_RADIUS_KM = 60268.0        # equatorial

SOLAR_SCALES = (
    NormalizationScale(ScaleKind.PRIMARY_BODY_RADIUS, _SUN_RADIUS_AU, "AU",
                       "solar equatorial radius", approximate=False),
    NormalizationScale(ScaleKind.SYNCHRONOUS_ORBIT, 0.168, "AU",
                       "co-rotation radius for a ~25.4 d equatorial period"),
    NormalizationScale(ScaleKind.ROCHE_LIMIT, 0.0088, "AU",
                       "rigid-body Roche limit for a 3000 kg/m^3 body"),
)

JOVIAN_SCALES = (
    NormalizationScale(ScaleKind.PRIMARY_BODY_RADIUS, _JUPITER_RADIUS_KM,
                       "km", "Jovian equatorial radius", approximate=False),
    NormalizationScale(ScaleKind.SYNCHRONOUS_ORBIT, 1.6e5, "km",
                       "co-rotation radius for a ~9.925 h period"),
    NormalizationScale(ScaleKind.ROCHE_LIMIT, 1.33e5, "km",
                       "rigid-body Roche limit for a 3000 kg/m^3 body"),
    NormalizationScale(ScaleKind.HILL_RADIUS, 5.3e7, "km",
                       "Hill radius against solar tide"),
)

SATURNIAN_SCALES = (
    NormalizationScale(ScaleKind.PRIMARY_BODY_RADIUS, _SATURN_RADIUS_KM,
                       "km", "Saturnian equatorial radius",
                       approximate=False),
    NormalizationScale(ScaleKind.SYNCHRONOUS_ORBIT, 1.12e5, "km",
                       "co-rotation radius for a ~10.55 h period"),
    NormalizationScale(ScaleKind.ROCHE_LIMIT, 8.9e4, "km",
                       "rigid-body Roche limit for a 3000 kg/m^3 body"),
    NormalizationScale(ScaleKind.HILL_RADIUS, 6.5e7, "km",
                       "Hill radius against solar tide"),
)

#: Solar System planets, semi-major axes in AU (published values).
SOLAR_SYSTEM = OrbitalSystem(
    "solar_planets", "Sun", "AU",
    ("Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus",
     "Neptune"),
    (0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069),
    SOLAR_SCALES[0], SOLAR_SCALES,
    "published semi-major axes in AU; the asteroid belt and all "
    "dwarf planets are deliberately excluded, and that exclusion is "
    "itself a degree of freedom",
)

#: The four Galilean satellites, semi-major axes in km.
JOVIAN_GALILEAN = OrbitalSystem(
    "jovian_galilean", "Jupiter", "km",
    ("Io", "Europa", "Ganymede", "Callisto"),
    (421700.0, 671034.0, 1070412.0, 1882709.0),
    JOVIAN_SCALES[0], JOVIAN_SCALES,
    "published semi-major axes in km; the inner three are in a genuine "
    "Laplace resonance, which is dynamics, not shell structure",
)

#: Major Saturnian satellites, semi-major axes in km.
SATURNIAN_MAJOR = OrbitalSystem(
    "saturnian_major", "Saturn", "km",
    ("Mimas", "Enceladus", "Tethys", "Dione", "Rhea", "Titan", "Iapetus"),
    (185539.0, 237948.0, 294619.0, 377396.0, 527108.0, 1221870.0,
     3560820.0),
    SATURNIAN_SCALES[0], SATURNIAN_SCALES,
    "published semi-major axes in km; Hyperion and the small irregulars "
    "are excluded, another free choice",
)

SYSTEMS: dict[str, OrbitalSystem] = {
    s.system_id: s for s in (SOLAR_SYSTEM, JOVIAN_GALILEAN, SATURNIAN_MAJOR)
}


def renormalize(system: OrbitalSystem, kind: ScaleKind) -> OrbitalSystem:
    """Switch a system to another *declared* scale, for the whole system.

    Legal because it is one declaration applied to every body. What is
    not legal is a different scale per body or per desired match; see
    :func:`refuse_per_target_normalization`.
    """
    for sc in system.scales_available:
        if sc.kind is kind:
            return OrbitalSystem(
                system.system_id, system.primary, system.units,
                system.bodies, system.semi_major_axis, sc,
                system.scales_available, system.source_note)
    raise ScalingError(
        f"{kind.value} is not declared for {system.system_id}; inventing "
        f"a scale to make a fit work is the thing this module refuses")


def refuse_per_target_normalization(system: OrbitalSystem,
                                    per_body_scales) -> None:
    """Per-target normalisation is refused, always.

    Choosing a different normalising length for each body (or re-tuning
    it until a particular match appears) gives one free parameter per
    data point. Any target sequence can then be hit exactly, so the fit
    carries no information at all.
    """
    raise ScalingError(
        f"refusing {len(per_body_scales)} separate normalisations for "
        f"{system.system_id}. The scale is declared once for the whole "
        f"system; re-optimising it per target is one free parameter per "
        f"body, which fits any sequence exactly and therefore measures "
        f"nothing. Use renormalize() to change the declared scale for "
        f"every body at once.")


def refuse_shared_physics_from_fit(model: str, rms_log_error: float,
                                   system_id: str = "") -> None:
    """A good fit is refused as evidence of shared physics, always.

    Hydrogenic radii come from an eigenvalue condition in a Coulomb
    potential. Orbital radii come from accretion, migration, resonance
    and survival. A small residual between two sorted lists does not
    connect those mechanisms, and no residual value is small enough to.
    """
    where = f" on {system_id}" if system_id else ""
    raise ScalingError(
        f"refusing to read shared physics from a fit: {model!r} reaches "
        f"rms log error {rms_log_error:.4g}{where}, and a good fit is "
        f"not evidence of shared physics. Random sorted radii fit these "
        f"same families about as well (see random_null_comparison), an "
        f"orbital radius is a continuous constant of motion with no "
        f"eigenvalue condition behind it, and no hbar, exclusion "
        f"principle or boundary condition appears anywhere in celestial "
        f"mechanics. Establishing a shared law needs a mechanism and an "
        f"out-of-sample prediction, not a residual.")


# --- the error metric ---------------------------------------------------

def rms_log_error(observed, predicted) -> float:
    """Root-mean-square residual in natural log space (scale free).

    Log space is the only fair metric here: the radii span two decades,
    so a linear residual is a report on Neptune and nothing else.
    """
    o = np.asarray(observed, float)
    p = np.asarray(predicted, float)
    if o.shape != p.shape:
        raise ScalingError("observed and predicted must be the same shape")
    if np.any(o <= 0) or not np.all(np.isfinite(o)):
        raise ScalingError("observed radii must be finite and > 0")
    if np.any(~np.isfinite(p)) or np.any(p <= 0):
        return float("inf")
    return float(np.sqrt(np.mean((np.log(p) - np.log(o)) ** 2)))


@dataclass(frozen=True)
class ModelFit:
    """One model fitted to one sorted radius list."""

    model: str
    params: dict
    rms_log_error: float
    n_params: int
    n_points: int
    status: str = "FIT"
    note: str = ""

    @property
    def aic(self) -> float:
        """Small-sample-ish AIC on the log residuals, floored at zero error.

        The floor matters: two models can both fit generated data to
        machine precision, and then the parsimony term is the only
        honest tie-break.
        """
        if not math.isfinite(self.rms_log_error):
            return float("inf")
        mse = max(self.rms_log_error ** 2, 1e-24)
        return self.n_points * math.log(mse) + 2 * self.n_params


# --- the comparative models --------------------------------------------

def _check_radii(radii) -> np.ndarray:
    r = np.asarray(radii, float)
    if r.ndim != 1 or r.size < 3:
        raise ScalingError("need a 1-D list of at least three radii")
    if not np.all(np.isfinite(r)) or np.any(r <= 0):
        raise ScalingError("radii must be finite and > 0")
    if not np.all(np.diff(r) > 0):
        raise ScalingError("radii must be sorted strictly outward")
    return r


def fit_hydrogenic(radii) -> ModelFit:
    """``r = A * n**2`` -- the hydrogenic form, one free parameter.

    This is the shape the analogy actually predicts: the characteristic
    radius of a hydrogenic state goes as ``n**2 / Z``. Only the overall
    scale is free, so it is the most falsifiable model here.
    """
    r = _check_radii(radii)
    n = np.arange(1, r.size + 1, dtype=float)
    log_a = float(np.mean(np.log(r) - 2.0 * np.log(n)))
    params = {"A": math.exp(log_a), "exponent": 2.0}
    pred = predict("hydrogenic", params, r.size)
    return ModelFit("hydrogenic", params, rms_log_error(r, pred), 1, r.size,
                    note="r = A n^2, the shape n^2/Z would imply")


def fit_geometric(radii) -> ModelFit:
    """``r = A * k**n`` -- a geometric progression, two free parameters."""
    r = _check_radii(radii)
    n = np.arange(1, r.size + 1, dtype=float)
    slope, intercept = np.polyfit(n, np.log(r), 1)
    params = {"A": math.exp(float(intercept)), "k": math.exp(float(slope))}
    pred = predict("geometric", params, r.size)
    return ModelFit("geometric", params, rms_log_error(r, pred), 2, r.size,
                    note="r = A k^n, constant ratio between neighbours")


def fit_power_law(radii) -> ModelFit:
    """``r = A * n**p`` with ``p`` fitted -- the hydrogenic form relaxed.

    The fitted ``p`` is the interesting number: if the analogy were a
    law, ``p`` would come out near 2 in *every* system. It does not.
    """
    r = _check_radii(radii)
    n = np.arange(1, r.size + 1, dtype=float)
    slope, intercept = np.polyfit(np.log(n), np.log(r), 1)
    params = {"A": math.exp(float(intercept)), "p": float(slope)}
    pred = predict("power_law", params, r.size)
    return ModelFit("power_law", params, rms_log_error(r, pred), 2, r.size,
                    note="r = A n^p, p fitted rather than assumed")


def fit_titius_bode(radii, *, c_grid: int = 60, a_grid: int = 12,
                    b_grid: int = 31) -> ModelFit:
    """``r = a + b * c**n`` -- the Titius-Bode-like exponential, 3 free.

    Fitted by a grid over ``(a, c)`` with a log-spaced sweep in ``b``,
    scored in log space so the inner bodies count as much as the outer
    ones. Three parameters on a handful of points is most of the story.
    """
    r = _check_radii(radii)
    n = np.arange(1, r.size + 1, dtype=float)
    log_r = np.log(r)
    c_vals = np.linspace(1.05, 4.0, c_grid)
    a_vals = np.linspace(0.0, 0.95 * float(r[0]), a_grid)
    f_vals = np.exp(np.linspace(math.log(0.2), math.log(5.0), b_grid))

    base = c_vals[:, None] ** n[None, :]                    # (C, N)
    b0 = (r[-1] - a_vals[None, :]) / base[:, -1][:, None]    # (C, A)
    b = b0[:, :, None] * f_vals[None, None, :]               # (C, A, B)
    pred = (a_vals[None, :, None, None]
            + b[:, :, :, None] * base[:, None, None, :])     # (C, A, B, N)
    with np.errstate(invalid="ignore", divide="ignore"):
        lp = np.where(pred > 0, np.log(np.where(pred > 0, pred, 1.0)),
                      np.nan)
        err = np.sqrt(np.mean((lp - log_r) ** 2, axis=-1))
    err = np.where(np.isfinite(err), err, np.inf)
    ci, ai, bi = np.unravel_index(int(np.argmin(err)), err.shape)
    params = {"a": float(a_vals[ai]), "b": float(b[ci, ai, bi]),
              "c": float(c_vals[ci])}
    fitted = predict("titius_bode", params, r.size)
    return ModelFit("titius_bode", params, rms_log_error(r, fitted), 3,
                    r.size, note="r = a + b c^n, the Titius-Bode family")


#: Small-integer period commensurabilities the resonance chain may use.
RESONANCE_RATIOS: tuple[tuple[int, int], ...] = (
    (2, 1), (3, 2), (4, 3), (5, 4), (5, 3), (5, 2), (3, 1), (7, 3),
    (7, 4), (7, 5), (8, 3), (8, 5), (9, 4), (9, 5), (4, 1),
)


def fit_resonance_chain(radii) -> ModelFit:
    """Successive period ratios snapped to small-integer commensurabilities.

    Kepler's third law gives ``P ~ r**1.5`` about a common primary, so
    each step's period ratio is read off the radii and replaced by the
    nearest allowed small-integer ratio. This is real dynamics -- the
    Galilean Laplace resonance is genuine -- but note the cost: one
    discrete choice per step is ``N-1`` extra degrees of freedom, which
    is why the AIC penalty here is heavy and why a good residual from
    this model is worth the least of any model in the suite.
    """
    r = _check_radii(radii)
    obs_period_ratio = (r[1:] / r[:-1]) ** 1.5
    chosen: list[tuple[int, int]] = []
    for pr in obs_period_ratio:
        target = math.log(float(pr))
        best = min(RESONANCE_RATIOS,
                   key=lambda ab: abs(math.log(ab[0] / ab[1]) - target))
        chosen.append(best)
    params = {"A": 1.0, "ratios": tuple(chosen)}
    rel = predict("resonance_chain", {"A": 1.0, "ratios": tuple(chosen)},
                  r.size)
    log_a = float(np.mean(np.log(r) - np.log(rel)))
    params["A"] = math.exp(log_a)
    pred = predict("resonance_chain", params, r.size)
    return ModelFit("resonance_chain", params, rms_log_error(r, pred),
                    1 + len(chosen), r.size,
                    note="period ratios snapped to small integers; one "
                         "discrete choice per step")


def formation_informed_model(system: OrbitalSystem | None = None) -> ModelFit:
    """The model that would actually explain anything -- and cannot run here.

    A formation-informed prediction needs the protoplanetary or
    circumplanetary disc surface-density profile, the gas dissipation
    timescale, the migration and resonance-capture history, and the
    collisional record. None of that is in this repository, and none of
    it is invented here. ``BLOCKED_MISSING_DATA`` is the honest state.
    """
    n = system.n if system is not None else 0
    return ModelFit(
        "formation_informed", {}, float("nan"), 0, n,
        status=BLOCKED_MISSING_DATA,
        note="requires disc surface density, gas dissipation timescale, "
             "migration and resonance-capture history, and the "
             "collisional record; none are present, so no number is "
             "produced and none is guessed")


#: The models that can be fitted to a bare radius list.
FITTERS = {
    "hydrogenic": fit_hydrogenic,
    "geometric": fit_geometric,
    "power_law": fit_power_law,
    "titius_bode": fit_titius_bode,
    "resonance_chain": fit_resonance_chain,
}

#: Structured (non-control, non-blocked) model names.
STRUCTURED_MODELS: tuple[str, ...] = tuple(FITTERS)

#: The control.
NULL_MODEL = "random_order_statistic"

#: Declared but unrunnable.
BLOCKED_MODELS: tuple[str, ...] = ("formation_informed",)


def predict(model: str, params: dict, n_points: int) -> np.ndarray:
    """Apply already-fitted parameters to an index run of ``n_points``.

    This is what makes an out-of-sample number possible: the parameters
    are frozen from one system and pushed onto another.
    """
    if n_points < 1:
        raise ScalingError("n_points must be >= 1")
    n = np.arange(1, n_points + 1, dtype=float)
    if model == "hydrogenic":
        return float(params["A"]) * n ** float(params.get("exponent", 2.0))
    if model == "geometric":
        return float(params["A"]) * float(params["k"]) ** n
    if model == "power_law":
        return float(params["A"]) * n ** float(params["p"])
    if model == "titius_bode":
        return (float(params["a"])
                + float(params["b"]) * float(params["c"]) ** n)
    if model == "resonance_chain":
        ratios = tuple(params["ratios"])
        if n_points - 1 > len(ratios):
            raise ScalingError(
                f"the fitted resonance chain has {len(ratios)} steps and "
                f"cannot be extended to {n_points} bodies; extending it "
                f"would mean choosing new ratios on the evaluation set, "
                f"which is not an out-of-sample prediction")
        steps = np.array([(a / b) ** (2.0 / 3.0)
                          for a, b in ratios[:n_points - 1]], float)
        rel = np.concatenate([[1.0], np.cumprod(steps)]) if steps.size \
            else np.array([1.0])
        return float(params["A"]) * rel
    raise ScalingError(f"unknown model {model!r}")


# --- the control: random order statistics ------------------------------

def random_sorted_radii(n: int, r_min: float, r_max: float, rng, *,
                        pin_endpoints: bool = True) -> np.ndarray:
    """``n`` sorted log-uniform draws spanning the same range.

    This is the matched null: same count, same dynamic range, no
    structure whatsoever. With ``pin_endpoints`` the extremes are held
    at the observed ones and only the interior is random, which is the
    tighter (harder to beat) version of the control.
    """
    if n < 3 or not (0 < r_min < r_max):
        raise ScalingError("need n >= 3 and 0 < r_min < r_max")
    lo, hi = math.log(r_min), math.log(r_max)
    if pin_endpoints:
        interior = np.sort(rng.uniform(lo, hi, size=n - 2))
        draws = np.concatenate([[lo], interior, [hi]])
    else:
        draws = np.sort(rng.uniform(lo, hi, size=n))
    out = np.exp(draws)
    # a tie would break the strictly-increasing invariant
    return np.maximum.accumulate(out * (1.0 + 1e-12 * np.arange(n)))


def _best_structured(radii) -> ModelFit:
    """AIC-best structured fit -- the same search applied to everything."""
    fits = [f(radii) for f in FITTERS.values()]
    return min(fits, key=lambda f: f.aic)


def _null_best_errors(radii, *, trials: int, seed: int,
                      pin_endpoints: bool) -> np.ndarray:
    r = _check_radii(radii)
    rng = np.random.default_rng(seed)
    out = np.empty(trials, float)
    for i in range(trials):
        draw = random_sorted_radii(r.size, float(r[0]), float(r[-1]), rng,
                                   pin_endpoints=pin_endpoints)
        out[i] = _best_structured(draw).rms_log_error
    return out


def null_order_statistic(radii, *, trials: int = 200, seed: int = 20260723,
                         pin_endpoints: bool = True) -> ModelFit:
    """The control as a pseudo-model: how well sorted noise gets fitted.

    Its "error" is the median best-fit error the *same* model search
    reaches on random sorted radii of the same count and range. It is
    never selected as an explanation -- it is the bar the explanations
    have to clear.
    """
    r = _check_radii(radii)
    errs = _null_best_errors(r, trials=trials, seed=seed,
                             pin_endpoints=pin_endpoints)
    params = {"trials": trials, "pin_endpoints": pin_endpoints,
              "median": float(np.median(errs)),
              "q10": float(np.quantile(errs, 0.10)),
              "q90": float(np.quantile(errs, 0.90))}
    return ModelFit(NULL_MODEL, params, float(np.median(errs)), 2, r.size,
                    status="CONTROL",
                    note="median best-fit error of the same model search "
                         "on sorted log-uniform draws of the same size "
                         "and range")


def fit_models(radii, *, include_null: bool = True, null_trials: int = 200,
               seed: int = 20260723,
               system: OrbitalSystem | None = None) -> dict[str, ModelFit]:
    """Fit every comparative model and return per-model in-sample error."""
    r = _check_radii(radii)
    out: dict[str, ModelFit] = {name: fn(r) for name, fn in FITTERS.items()}
    if include_null:
        out[NULL_MODEL] = null_order_statistic(r, trials=null_trials,
                                               seed=seed)
    out["formation_informed"] = formation_informed_model(system)
    return out


def fit_system_models(system: OrbitalSystem, **kw) -> dict[str, ModelFit]:
    """Fit every model to a system's normalised radii."""
    return fit_models(system.normalized(), system=system, **kw)


def best_model(fits: dict[str, ModelFit]) -> ModelFit:
    """AIC-best explanatory model. The control and blocked models cannot win."""
    usable = [f for f in fits.values() if f.status == "FIT"]
    if not usable:
        raise ScalingError("no fitted model to select from")
    return min(usable, key=lambda f: f.aic)


def random_null_comparison(radii, *, trials: int = 200, seed: int = 20260723,
                           pin_endpoints: bool = True,
                           alpha: float = 0.05) -> dict:
    """Does the real system beat sorted noise under the same search?

    The observed statistic is the best (AIC-selected) in-sample error;
    the null distribution is the same statistic on random sorted radii
    of the same count and range. ``p`` is the fraction of null draws
    fitting at least as tightly, with the ``+1`` correction.
    """
    r = _check_radii(radii)
    observed = _best_structured(r)
    errs = _null_best_errors(r, trials=trials, seed=seed,
                             pin_endpoints=pin_endpoints)
    at_least_as_good = int(np.sum(errs <= observed.rms_log_error))
    p = (at_least_as_good + 1) / (trials + 1)
    median = float(np.median(errs))
    return {
        "n_bodies": int(r.size),
        "observed_model": observed.model,
        "observed_rms_log_error": observed.rms_log_error,
        "null_median_rms_log_error": median,
        "null_q10_rms_log_error": float(np.quantile(errs, 0.10)),
        "null_trials": trials,
        "pin_endpoints": pin_endpoints,
        "p_value": p,
        "null_competitive": bool(p > alpha),
        "null_error_ratio": (median / observed.rms_log_error
                             if observed.rms_log_error > 0 else float("inf")),
        "verdict": ("NO_BETTER_THAN_CHANCE" if p > alpha
                    else "TIGHTER_THAN_CHANCE"),
        "note": (
            "a small residual alone is meaningless: sorted random radii "
            "of the same count and range get fitted about this well by "
            "the same five families. Only a residual the control rarely "
            "reaches would be evidence"),
        "look_elsewhere_paid": True,
    }


# --- the honest number: out of sample ----------------------------------

def out_of_sample_error(fit_system: OrbitalSystem,
                        eval_system: OrbitalSystem) -> dict:
    """Fit on one system, evaluate on an independent one. No refitting.

    Each system is an independent holdout for the others. If there were
    a universal orbital-to-shell mapping, parameters learned on the
    planets would transfer to a satellite system. The strict number
    keeps every parameter frozen; the ``shape_only`` number is the most
    generous transfer possible, re-fitting the single multiplicative
    scale (a log-space offset) and nothing else.
    """
    if fit_system.system_id == eval_system.system_id:
        raise ScalingError(
            "a system is not a holdout for itself; evaluate on a "
            "different system")
    fit_r = fit_system.normalized()
    eval_r = eval_system.normalized()
    in_fits = {name: fn(fit_r) for name, fn in FITTERS.items()}
    per_model: dict[str, dict] = {}
    for name, fit in in_fits.items():
        try:
            pred = predict(name, fit.params, eval_system.n)
        except ScalingError as exc:
            per_model[name] = {
                "in_sample_rms_log_error": fit.rms_log_error,
                "out_of_sample_rms_log_error": float("inf"),
                "shape_only_rms_log_error": float("inf"),
                "transferable": False,
                "why_not": str(exc),
            }
            continue
        strict = rms_log_error(eval_r, pred)
        if np.all(pred > 0):
            offset = float(np.mean(np.log(eval_r) - np.log(pred)))
            shape = rms_log_error(eval_r, pred * math.exp(offset))
        else:
            shape = float("inf")
        per_model[name] = {
            "in_sample_rms_log_error": fit.rms_log_error,
            "out_of_sample_rms_log_error": strict,
            "shape_only_rms_log_error": shape,
            "transferable": True,
        }
    chosen = best_model(in_fits)
    head = per_model[chosen.model]
    in_err = head["in_sample_rms_log_error"]
    out_err = head["out_of_sample_rms_log_error"]
    ratio = out_err / in_err if in_err > 0 else float("inf")
    return {
        "fit_system": fit_system.system_id,
        "eval_system": eval_system.system_id,
        "fit_scale": fit_system.scale.kind.value,
        "eval_scale": eval_system.scale.kind.value,
        "selected_model": chosen.model,
        "in_sample_rms_log_error": in_err,
        "out_of_sample_rms_log_error": out_err,
        "shape_only_rms_log_error": head["shape_only_rms_log_error"],
        "degradation_factor": ratio,
        "per_model": per_model,
        "verdict": ("NO_UNIVERSAL_MAPPING" if ratio > 2.0
                    else "TRANSFER_NOT_EXCLUDED"),
        "note": (
            "the in-sample number is what a fit advertises; this is the "
            "number that decides whether anything was learned. Both "
            "systems are normalised by their own declared scale, so the "
            "comparison is dimensionless on both sides"),
        "shape_only_caveat": (
            "the shape-only number can come out *below* the in-sample "
            "number when the evaluation system has fewer and smoother "
            "bodies. That is not transfer succeeding; it is a reminder "
            "that a four-point fit is easy, which is the same warning "
            "the random control gives"),
    }


def fitted_exponents() -> dict:
    """The fitted power-law exponent per system -- a law would repeat itself."""
    out = {}
    for sid, sysm in SYSTEMS.items():
        out[sid] = {
            "p": fit_power_law(sysm.normalized()).params["p"],
            "n_bodies": sysm.n,
            "scale": sysm.scale.kind.value,
        }
    ps = [v["p"] for v in out.values()]
    out["spread"] = float(max(ps) - min(ps))
    out["universal"] = bool(out["spread"] < 0.2)
    out["note"] = (
        "a hydrogenic mapping predicts p = 2 in every system. The fitted "
        "exponents disagree with each other by more than they disagree "
        "with 2, so there is no single exponent to call universal")
    return out


# --- look elsewhere -----------------------------------------------------

def look_elsewhere_correction(n_models: int, n_systems: int, *,
                              p_value: float = 0.05,
                              alpha: float = 0.05) -> dict:
    """Bonferroni correction for the whole search that was actually run.

    Every model tried on every system is a look, and the reported
    significance has to pay for all of them. Both the corrected p and
    the corrected threshold move against the claim as the search grows.
    """
    if n_models < 1 or n_systems < 1:
        raise ScalingError("n_models and n_systems must be >= 1")
    if not (0.0 <= p_value <= 1.0) or not (0.0 < alpha < 1.0):
        raise ScalingError("p_value must be in [0,1] and alpha in (0,1)")
    trials = int(n_models) * int(n_systems)
    corrected_p = min(1.0, p_value * trials)
    corrected_alpha = alpha / trials
    return {
        "n_models": int(n_models),
        "n_systems": int(n_systems),
        "effective_trials": trials,
        "raw_p_value": float(p_value),
        "corrected_p_value": float(corrected_p),
        "alpha": float(alpha),
        "corrected_alpha": float(corrected_alpha),
        "significant_after_correction": bool(p_value <= corrected_alpha),
        "method": "BONFERRONI",
        "note": (
            "the normalisation choice, the index offset and the decision "
            "of which bodies count are further looks that this simple "
            "count does not even include, so the correction here is a "
            "lower bound on the penalty owed"),
    }


# --- report -------------------------------------------------------------

def orbitalscaling_report(*, null_trials: int = 120,
                          seed: int = 20260723) -> dict:
    """The standing state of the orbital-versus-atomic scaling question."""
    solar = SOLAR_SYSTEM.normalized()
    fits = fit_models(solar, include_null=False, system=SOLAR_SYSTEM)
    null = random_null_comparison(solar, trials=null_trials, seed=seed)
    per_system_null = {
        sid: random_null_comparison(s.normalized(), trials=null_trials,
                                    seed=seed + i)
        for i, (sid, s) in enumerate(SYSTEMS.items())
    }
    oos = out_of_sample_error(SOLAR_SYSTEM, JOVIAN_GALILEAN)
    lee = look_elsewhere_correction(len(STRUCTURED_MODELS), len(SYSTEMS),
                                    p_value=min(r["p_value"] for r
                                                in per_system_null.values()))
    return {
        "systems": {sid: {"primary": s.primary, "n_bodies": s.n,
                          "units": s.units,
                          "declared_scale": s.scale.kind.value}
                    for sid, s in SYSTEMS.items()},
        "models_compared": list(STRUCTURED_MODELS) + [NULL_MODEL],
        "blocked_models": {m: BLOCKED_MISSING_DATA for m in BLOCKED_MODELS},
        "solar_in_sample_rms_log_error": {
            k: v.rms_log_error for k, v in fits.items()
            if v.status == "FIT"},
        "solar_best_model": best_model(fits).model,
        "random_null": null,
        "per_system_null": {
            sid: {"observed_model": r["observed_model"],
                  "observed_rms_log_error": r["observed_rms_log_error"],
                  "null_median_rms_log_error":
                      r["null_median_rms_log_error"],
                  "p_value": r["p_value"],
                  "verdict": r["verdict"]}
            for sid, r in per_system_null.items()},
        "out_of_sample": oos,
        "fitted_exponents": fitted_exponents(),
        "look_elsewhere": lee,
        "physics_distinction": (
            "a hydrogenic radius scales as n^2/Z because an eigenvalue "
            "problem in a Coulomb potential forces it, with no track and "
            "no intermediate n; an orbital semi-major axis is a "
            "continuous constant of motion set by accretion, migration, "
            "resonance and survival. There is no established universal "
            "mapping between them"),
        "the_trap": (
            "family, parameters, index offset, normalising length and "
            "which bodies count are all free, so a handful of sorted "
            "radii fit something almost always"),
        "the_test": (
            "random_null_comparison runs the identical search on sorted "
            "random radii of the same count and range; out_of_sample_error "
            "freezes the parameters and moves to an independent system"),
        "headline": (
            "on the eight planets the best of five families reaches an "
            "rms log residual the random order-statistic control matches "
            "or beats often enough that the result is "
            "NO_BETTER_THAN_CHANCE; a handful of sorted radii fit "
            "something almost always"),
        "the_one_system_that_beats_chance": (
            "the four Galilean satellites do fit better than the control, "
            "and the reason is known and mundane: Io, Europa and "
            "Ganymede sit in an established Laplace resonance, which is "
            "gravitational dynamics with a mechanism, not shell "
            "structure. It is also the smallest set here, and after the "
            "look-elsewhere correction for every model on every system "
            "it is no longer significant"),
        "refusals": ["refuse_per_target_normalization",
                     "refuse_shared_physics_from_fit"],
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say planetary orbits are quantised, that "
            "planets occupy shells, that a principal quantum number "
            "applies to celestial mechanics, or that any fitted "
            "exponent is a law. It does not claim the Titius-Bode "
            "family is physics. It does not claim the resonance chain "
            "explains anything beyond the resonances that are already "
            "established dynamics. And it does not treat a small "
            "residual as a discovery, because sorted random radii reach "
            "comparable residuals under the same search and the fitted "
            "parameters do not transfer to an independent system."),
        "verdict": VERDICT_UNESTABLISHED,
    }
