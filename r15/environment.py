"""P03 -- the environmental ledger: the nuisance variables, kept honestly.

Every measurement happens in a room, and the room moves. Temperature drifts,
the mains sags, a truck goes past and the bench rings, an unshielded supply
sprays RF across the band of interest. None of that is the specimen, and all
of it lands in the data. The environmental ledger is the record that lets a
later analysis tell the two apart: for every run it carries, per channel, the
ambient condition as a **time-series** with units, an uncertainty, and a hash,
aligned to the experiment clock.

**Nine nuisance channels.** Temperature, humidity, pressure, vibration,
acoustic background, line (mains) voltage, EMI/RF background, magnetic field,
and operator actions. Each is an :class:`EnvChannel`: a kind, a source, a
timestamp vector (**passed in**, never read from the wall clock), a value
vector, its units, a one-sigma uncertainty, and a content hash so the trace
cannot be silently edited.

**Four modes, kept distinct.** ``REAL`` (live sensor acquisition), ``REPLAY``
(a recorded trace re-played), ``SYNTHETIC`` (a deterministic simulator), and
``FAULT_INJECTION`` (a deliberately corrupted trace, for testing the guards).
In this software-only repository ``REAL`` is :data:`BLOCKED_MISSING_INPUT`:
no sensor was operated, so a live ledger cannot be formed. Every channel this
module builds is a ``SYNTHETIC_OBSERVATION`` and never a physical measurement.

**Four sources, ranked by authority.** A live ``SENSOR`` trace outranks a
``REPLAY``, which outranks a ``SYNTHETIC`` trace, which outranks a ``MANUAL``
declaration. A manual note that "the lab was about 21 C" is a ``SOURCE_CLAIM``,
not a measurement, and :func:`refuse_manual_as_sensor` refuses to let it stand
in for a sensor trace.

**Clock alignment.** :func:`clock_offset_seconds` and :func:`is_clock_aligned`
check a trace against the experiment clock origin, and :func:`trace_lag_samples`
reuses :func:`r13.daq.cross_correlation_lag` to recover the relative lag
between two traces. A misalignment left uncorrected is a phantom timing that a
later correlation reads as physics.

**Missing-data policy by protocol.** A protocol declares which channels are
required; :func:`check_completeness` applies one of three policies --
``INVALIDATE`` (a missing required channel invalidates the run),
``DEGRADE`` (proceed but cap the evidence), ``ALLOW_MANUAL`` (a manual
declaration may substitute, at its lower authority).

**Drift and nuisance-correlation diagnostics.** :func:`drift_rate` fits a
linear drift in units per second, and :func:`nuisance_correlation` reports the
Pearson correlation between an env channel and a candidate signal -- the first
thing to check before any feature is called intrinsic.

**The error budget.** :func:`build_error_budget` decomposes a quantity's
uncertainty into eleven components -- instrument resolution, calibration,
clock, environment, fixture repeatability, specimen geometry, orientation,
numerical method, DSP, operator, model residual -- and combines them in
quadrature. The environmental channels feed the ``environment`` component via
:func:`environment_component`. **A residual below the combined uncertainty is
not anomalous**: :func:`is_within_budget` states it and
:func:`refuse_subbudget_as_anomaly` refuses the promotion.

Nothing here is measured. The strongest class this module reaches is a
deterministic ``SYNTHETIC_OBSERVATION`` (evidence ``E2``); the verdict is
``R15_ENVIRONMENTAL_LEDGER_SYNTHETIC_NO_MEASUREMENT``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13.daq import cross_correlation_lag
from r15.claims import (
    ClaimClass,
    EvidenceBindings,
    EvidenceLevel,
    evidence_cap,
)

# --- verdict and claim vocabulary -----------------------------------------

#: The standing verdict for this module.
VERDICT = "R15_ENVIRONMENTAL_LEDGER_SYNTHETIC_NO_MEASUREMENT"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

#: The strongest evidence a deterministic synthetic trace reaches.
MAX_ENV_EVIDENCE = EvidenceLevel.E2

#: Method label recorded in the error budget.
QUADRATURE = "quadrature_sum_rss"


class EnvLedgerError(RuntimeError):
    """Raised on a malformed channel, an illegal promotion, or a refusal.

    Covers the structural guards (mismatched trace lengths, a negative
    uncertainty, a hash that does not verify) and the load-bearing refusals
    :func:`refuse_subbudget_as_anomaly`, :func:`refuse_manual_as_sensor`, and
    :func:`refuse_synthetic_env_as_measured`.
    """


# --- the vocabulary -------------------------------------------------------

class EnvChannelKind(Enum):
    """A nuisance variable the ledger can carry as a time-series channel."""

    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    ACOUSTIC = "acoustic"
    LINE_VOLTAGE = "line_voltage"
    EMI_RF = "emi_rf"
    MAGNETIC_FIELD = "magnetic_field"
    OPERATOR_ACTION = "operator_action"


class EnvMode(Enum):
    """How a ledger's traces were obtained. The four are kept distinct."""

    REAL = "real"                       # live sensor acquisition (blocked here)
    REPLAY = "replay"                   # a recorded trace re-played
    SYNTHETIC = "synthetic"             # a deterministic simulator
    FAULT_INJECTION = "fault_injection"  # a deliberately corrupted trace


class EnvSource(Enum):
    """Where one channel's samples came from. Ranks channel authority."""

    SENSOR = "sensor"
    REPLAY = "replay"
    SYNTHETIC = "synthetic"
    MANUAL = "manual"


#: Source authority: a live sensor trace outranks a replay, which outranks a
#: synthetic trace, which outranks a manual declaration.
SOURCE_AUTHORITY: dict[EnvSource, int] = {
    EnvSource.SENSOR: 3,
    EnvSource.REPLAY: 2,
    EnvSource.SYNTHETIC: 1,
    EnvSource.MANUAL: 0,
}

#: The claim class each source can support in this software-only environment.
#: No sensor was operated, so even a channel *labelled* SENSOR is honestly a
#: synthetic observation until real artifacts exist; a manual note is a
#: declared source claim.
SOURCE_CLAIM_CLASS: dict[EnvSource, ClaimClass] = {
    EnvSource.SENSOR: ClaimClass.SYNTHETIC_OBSERVATION,
    EnvSource.REPLAY: ClaimClass.SYNTHETIC_OBSERVATION,
    EnvSource.SYNTHETIC: ClaimClass.SYNTHETIC_OBSERVATION,
    EnvSource.MANUAL: ClaimClass.SOURCE_CLAIM,
}

#: Conventional units for each channel kind.
CHANNEL_UNITS: dict[EnvChannelKind, str] = {
    EnvChannelKind.TEMPERATURE: "K",
    EnvChannelKind.HUMIDITY: "%RH",
    EnvChannelKind.PRESSURE: "Pa",
    EnvChannelKind.VIBRATION: "m/s^2",
    EnvChannelKind.ACOUSTIC: "Pa",
    EnvChannelKind.LINE_VOLTAGE: "V",
    EnvChannelKind.EMI_RF: "V/m",
    EnvChannelKind.MAGNETIC_FIELD: "T",
    EnvChannelKind.OPERATOR_ACTION: "event",
}

#: The channels a protocol requires by default: the seven core measurement
#: nuisances. Magnetic field and operator actions are optional context.
DEFAULT_REQUIRED_KINDS: frozenset[EnvChannelKind] = frozenset({
    EnvChannelKind.TEMPERATURE,
    EnvChannelKind.HUMIDITY,
    EnvChannelKind.PRESSURE,
    EnvChannelKind.VIBRATION,
    EnvChannelKind.ACOUSTIC,
    EnvChannelKind.LINE_VOLTAGE,
    EnvChannelKind.EMI_RF,
})


def source_authority(source: EnvSource) -> int:
    """The authority rank of a source; higher outranks lower."""
    if not isinstance(source, EnvSource):
        raise EnvLedgerError("source must be an EnvSource")
    return SOURCE_AUTHORITY[source]


# --- one environmental channel --------------------------------------------

def _hash_series(kind: EnvChannelKind, units: str, uncertainty: float,
                 t: np.ndarray, values: np.ndarray) -> str:
    """A content hash over a channel's identity and its samples.

    Deterministic in the samples, so editing a trace changes the hash and the
    edit cannot pass silently.
    """
    h = hashlib.sha256()
    h.update(kind.value.encode("utf-8"))
    h.update(b"\x00")
    h.update(units.encode("utf-8"))
    h.update(b"\x00")
    h.update(np.float64(uncertainty).tobytes())
    h.update(np.ascontiguousarray(t, dtype=np.float64).tobytes())
    h.update(np.ascontiguousarray(values, dtype=np.float64).tobytes())
    return h.hexdigest()


@dataclass(frozen=True)
class EnvChannel:
    """One nuisance variable as a time-series, aligned and hashed.

    Build with :meth:`from_series`, which computes the hash. The timestamps
    ``t`` are supplied by the caller (the experiment clock), never taken from
    the wall clock, so the record is deterministic and replayable.
    """

    kind: EnvChannelKind
    source: EnvSource
    t: np.ndarray
    values: np.ndarray
    units: str
    uncertainty: float
    sample_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EnvChannelKind):
            raise EnvLedgerError("kind must be an EnvChannelKind")
        if not isinstance(self.source, EnvSource):
            raise EnvLedgerError("source must be an EnvSource")
        t = np.asarray(self.t, dtype=float)
        v = np.asarray(self.values, dtype=float)
        if t.ndim != 1 or v.ndim != 1:
            raise EnvLedgerError(
                f"{self.kind.value}: a channel is a 1-D time-series")
        if t.shape != v.shape:
            raise EnvLedgerError(
                f"{self.kind.value}: t and values must have one sample each "
                f"({t.shape} vs {v.shape})")
        if t.size < 1:
            raise EnvLedgerError(
                f"{self.kind.value}: a channel needs at least one sample")
        if t.size >= 2 and np.any(np.diff(t) <= 0.0):
            raise EnvLedgerError(
                f"{self.kind.value}: timestamps must be strictly increasing")
        if not self.units:
            raise EnvLedgerError(
                f"{self.kind.value}: a channel without units is not a channel")
        if float(self.uncertainty) < 0.0:
            raise EnvLedgerError(
                f"{self.kind.value}: uncertainty cannot be negative")

    @classmethod
    def from_series(cls, kind: EnvChannelKind, t, values, *,
                    source: EnvSource = EnvSource.SYNTHETIC,
                    units: str | None = None,
                    uncertainty: float = 0.0) -> "EnvChannel":
        """Build a channel and stamp its content hash."""
        t_arr = np.asarray(t, dtype=float)
        v_arr = np.asarray(values, dtype=float)
        u = CHANNEL_UNITS[kind] if units is None else str(units)
        digest = _hash_series(kind, u, float(uncertainty), t_arr, v_arr)
        return cls(kind=kind, source=source, t=t_arr, values=v_arr,
                   units=u, uncertainty=float(uncertainty), sample_hash=digest)

    @property
    def n(self) -> int:
        return int(np.asarray(self.values).size)

    @property
    def t0(self) -> float:
        return float(np.asarray(self.t)[0])

    @property
    def authority(self) -> int:
        return source_authority(self.source)

    @property
    def claim_class(self) -> ClaimClass:
        return SOURCE_CLAIM_CLASS[self.source]

    def verify_hash(self) -> bool:
        """Recompute the hash and check it matches the stored one."""
        return _hash_series(self.kind, self.units, self.uncertainty,
                            np.asarray(self.t, dtype=float),
                            np.asarray(self.values, dtype=float)) == \
            self.sample_hash

    def as_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "source": self.source.value,
            "units": self.units,
            "uncertainty": self.uncertainty,
            "n_samples": self.n,
            "t0": self.t0,
            "authority": self.authority,
            "claim_class": self.claim_class.value,
            "sample_hash": self.sample_hash,
        }


# --- synthetic channels, deterministic under a seed -----------------------

def synthetic_channel(kind: EnvChannelKind, t, *, seed: int,
                      mean: float = 0.0, noise: float = 0.0,
                      drift_rate: float = 0.0,
                      uncertainty: float = 0.0,
                      source: EnvSource = EnvSource.SYNTHETIC) -> EnvChannel:
    """A deterministic synthetic nuisance channel on the supplied clock.

    ``values = mean + drift_rate*(t - t[0]) + noise * N(0,1)`` where the noise
    is drawn from a seeded generator, so the same ``seed`` and ``t`` reproduce
    the trace byte-for-byte -- and therefore the same hash.
    """
    t_arr = np.asarray(t, dtype=float)
    if t_arr.size < 1:
        raise EnvLedgerError(f"{kind.value}: need at least one timestamp")
    rng = np.random.default_rng(int(seed))
    ramp = float(drift_rate) * (t_arr - t_arr[0])
    fluct = float(noise) * rng.standard_normal(t_arr.size)
    values = float(mean) + ramp + fluct
    return EnvChannel.from_series(kind, t_arr, values, source=source,
                                  uncertainty=uncertainty)


# --- the ledger -----------------------------------------------------------

@dataclass(frozen=True)
class EnvironmentLedger:
    """The per-run environmental record: a mode, a clock origin, channels."""

    run_id: str
    mode: EnvMode
    clock_t0: float
    channels: tuple[EnvChannel, ...]
    required_kinds: frozenset[EnvChannelKind] = DEFAULT_REQUIRED_KINDS

    def __post_init__(self) -> None:
        if not self.run_id:
            raise EnvLedgerError("a ledger needs a run_id")
        if not isinstance(self.mode, EnvMode):
            raise EnvLedgerError("mode must be an EnvMode")
        object.__setattr__(self, "channels", tuple(self.channels))
        object.__setattr__(self, "required_kinds",
                           frozenset(self.required_kinds))

    def kinds(self) -> frozenset[EnvChannelKind]:
        return frozenset(c.kind for c in self.channels)

    def channels_for(self, kind: EnvChannelKind) -> tuple[EnvChannel, ...]:
        return tuple(c for c in self.channels if c.kind == kind)

    def authoritative(self, kind: EnvChannelKind) -> EnvChannel:
        """The highest-authority channel for a kind (sensor over manual)."""
        candidates = self.channels_for(kind)
        if not candidates:
            raise EnvLedgerError(f"no {kind.value} channel in this ledger")
        return max(candidates, key=lambda c: c.authority)

    def missing_required(self) -> list[EnvChannelKind]:
        present = self.kinds()
        return sorted((k for k in self.required_kinds if k not in present),
                      key=lambda k: k.value)


# --- missing-data policy by protocol --------------------------------------

class MissingDataPolicy(Enum):
    """What a protocol does when a required channel is absent."""

    INVALIDATE = "invalidate"      # a missing required channel voids the run
    DEGRADE = "degrade"            # proceed, but cap the evidence
    ALLOW_MANUAL = "allow_manual"  # a manual declaration may substitute


@dataclass(frozen=True)
class CompletenessResult:
    """The outcome of applying a missing-data policy to a ledger."""

    valid: bool
    missing: tuple[EnvChannelKind, ...]
    manual_substitutions: tuple[EnvChannelKind, ...]
    evidence: EvidenceLevel
    policy: MissingDataPolicy

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "missing": [k.value for k in self.missing],
            "manual_substitutions": [k.value for k in self.manual_substitutions],
            "evidence": self.evidence.name,
            "policy": self.policy.value,
        }


def _env_bindings(complete: bool) -> EvidenceBindings:
    """Bindings for an env-only synthetic ledger: environment bound iff the
    required channels are present. No calibration, specimen or raw artifact
    exists here, so physical evidence is out of reach regardless."""
    return EvidenceBindings(environment=complete, uncertainty=True)


def check_completeness(
        ledger: EnvironmentLedger,
        policy: MissingDataPolicy = MissingDataPolicy.INVALIDATE,
) -> CompletenessResult:
    """Apply a missing-data policy and report validity and an evidence cap.

    A well-formed synthetic ledger with every required channel present tops
    out at :data:`MAX_ENV_EVIDENCE` (a deterministic synthetic observation,
    ``E2``) -- never a physical measurement. A missing required channel is
    treated per policy:

    * ``INVALIDATE`` -- the run is invalid and evidence drops to ``E0``.
    * ``DEGRADE`` -- the run proceeds but evidence is capped to ``E1``.
    * ``ALLOW_MANUAL`` -- a manual declaration for the missing kind counts as
      a substitution (at its lower authority); a kind with neither a trace nor
      a manual note still invalidates.
    """
    if not isinstance(policy, MissingDataPolicy):
        raise EnvLedgerError("policy must be a MissingDataPolicy")
    present = ledger.kinds()
    manual_kinds = frozenset(
        c.kind for c in ledger.channels if c.source == EnvSource.MANUAL)
    missing: list[EnvChannelKind] = []
    substituted: list[EnvChannelKind] = []
    for k in sorted(ledger.required_kinds, key=lambda x: x.value):
        if k in present:
            # a required kind covered only by a manual note is a substitution
            has_trace = any(c.kind == k and c.source != EnvSource.MANUAL
                            for c in ledger.channels)
            if not has_trace and policy == MissingDataPolicy.ALLOW_MANUAL:
                substituted.append(k)
            continue
        missing.append(k)

    if not missing:
        complete = True
        # evidence: a synthetic ledger reaches E2; the cap is honest about the
        # missing physical bindings and never returns a physical level.
        evidence = evidence_cap(_env_bindings(True), MAX_ENV_EVIDENCE)
        valid = True
    else:
        complete = False
        if policy == MissingDataPolicy.INVALIDATE:
            valid, evidence = False, EvidenceLevel.E0
        elif policy == MissingDataPolicy.DEGRADE:
            valid, evidence = True, EvidenceLevel.E1
        else:  # ALLOW_MANUAL: only invalid if a kind has no manual note either
            unresolved = [k for k in missing if k not in manual_kinds]
            valid = not unresolved
            evidence = EvidenceLevel.E1 if valid else EvidenceLevel.E0
    return CompletenessResult(
        valid=valid, missing=tuple(missing),
        manual_substitutions=tuple(substituted),
        evidence=evidence, policy=policy)


# --- clock alignment ------------------------------------------------------

def clock_offset_seconds(channel: EnvChannel, expected_t0: float) -> float:
    """Signed offset of a channel's clock origin from the experiment clock."""
    return float(channel.t0 - float(expected_t0))


def is_clock_aligned(channel: EnvChannel, expected_t0: float,
                     tol_s: float) -> bool:
    """Is the channel's origin within ``tol_s`` of the experiment clock?"""
    if float(tol_s) < 0.0:
        raise EnvLedgerError("tolerance cannot be negative")
    return abs(clock_offset_seconds(channel, expected_t0)) <= float(tol_s)


def trace_lag_samples(reference: EnvChannel, channel: EnvChannel) -> int:
    """Integer sample lag of one trace relative to another.

    Reuses :func:`r13.daq.cross_correlation_lag`; a nonzero lag on traces that
    should share the experiment clock is a detected misalignment.
    """
    if reference.n != channel.n:
        raise EnvLedgerError(
            "traces must share a length to be cross-correlated for lag")
    return cross_correlation_lag(np.asarray(reference.values, dtype=float),
                                 np.asarray(channel.values, dtype=float))


def realign_to_clock(channel: EnvChannel, expected_t0: float) -> EnvChannel:
    """Return a copy of the channel whose origin sits at the experiment clock.

    The samples are unchanged; only the timebase is shifted, so the correction
    is explicit and rehashed rather than silent.
    """
    offset = clock_offset_seconds(channel, expected_t0)
    new_t = np.asarray(channel.t, dtype=float) - offset
    return EnvChannel.from_series(channel.kind, new_t, channel.values,
                                  source=channel.source,
                                  units=channel.units,
                                  uncertainty=channel.uncertainty)


# --- drift and nuisance-correlation diagnostics ---------------------------

def drift_rate(channel: EnvChannel) -> float:
    """Least-squares linear drift of a channel, in units per second."""
    t = np.asarray(channel.t, dtype=float)
    v = np.asarray(channel.values, dtype=float)
    if t.size < 2:
        raise EnvLedgerError("need at least two samples to estimate drift")
    slope, _intercept = np.polyfit(t - t[0], v, 1)
    return float(slope)


def nuisance_correlation(channel: EnvChannel, signal) -> float:
    """Pearson correlation of an env channel with a candidate signal.

    A feature that correlates strongly with an environmental channel is a
    nuisance suspect, not an intrinsic effect. Returns a value in [-1, 1];
    ``0.0`` when either series has no variance (nothing to correlate).
    """
    a = np.asarray(channel.values, dtype=float)
    b = np.asarray(signal, dtype=float)
    if a.shape != b.shape:
        raise EnvLedgerError("channel and signal must share a length")
    if a.size < 2:
        raise EnvLedgerError("need at least two samples to correlate")
    if np.std(a) == 0.0 or np.std(b) == 0.0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


# --- the error budget -----------------------------------------------------

class BudgetComponent(Enum):
    """The eleven uncertainty contributions of a quantitative result."""

    INSTRUMENT_RESOLUTION = "instrument_resolution"
    CALIBRATION = "calibration"
    CLOCK = "clock"
    ENVIRONMENT = "environment"
    FIXTURE_REPEATABILITY = "fixture_repeatability"
    SPECIMEN_GEOMETRY = "specimen_geometry"
    ORIENTATION = "orientation"
    NUMERICAL_METHOD = "numerical_method"
    DSP = "dsp"
    OPERATOR = "operator"
    MODEL_RESIDUAL = "model_residual"


@dataclass(frozen=True)
class ErrorComponent:
    """One line of an error budget: a labelled one-sigma contribution."""

    component: BudgetComponent
    sigma: float
    units: str
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.component, BudgetComponent):
            raise EnvLedgerError("component must be a BudgetComponent")
        if float(self.sigma) < 0.0:
            raise EnvLedgerError(
                f"{self.component.value}: a sigma cannot be negative")
        if not self.units:
            raise EnvLedgerError(
                f"{self.component.value}: a sigma without units is not a "
                f"budget line")

    def as_dict(self) -> dict:
        return {
            "component": self.component.value,
            "sigma": float(self.sigma),
            "units": self.units,
            "note": self.note,
        }


def environment_component(ledger: EnvironmentLedger, *,
                          quantity_units: str = "mixed") -> ErrorComponent:
    """Fold a ledger's channel uncertainties into the ENVIRONMENT budget line.

    Combines the authoritative channels' one-sigma uncertainties in
    quadrature. This is a *model* of the environmental contribution, not a
    measured coupling coefficient; the units are heterogeneous, so the caller
    supplies a label for the reported quantity.
    """
    per_kind = [ledger.authoritative(k).uncertainty for k in ledger.kinds()]
    sigma = float(np.sqrt(np.sum(np.square(np.asarray(per_kind, dtype=float)))))
    return ErrorComponent(
        component=BudgetComponent.ENVIRONMENT, sigma=sigma,
        units=quantity_units,
        note="quadrature sum of authoritative channel uncertainties (model)")


def combine_quadrature(components) -> float:
    """Root-sum-square of the component sigmas -- the combined uncertainty."""
    comps = list(components)
    if not comps:
        raise EnvLedgerError("an error budget needs at least one component")
    sigmas = np.asarray([float(c.sigma) for c in comps], dtype=float)
    return float(np.sqrt(np.sum(np.square(sigmas))))


def build_error_budget(budget_id: str, quantity: str, components, *,
                       coverage_factor: float = 2.0) -> dict:
    """Assemble an error budget conforming to ``error_budget.schema.json``.

    The combined uncertainty is the quadrature sum of the component sigmas.
    The ``coverage_factor`` (``k``, default 2) expands it to a coverage
    interval. The budget is a ``MODEL_PREDICTION``: no coupling coefficient
    here was measured.
    """
    comps = list(components)
    if not budget_id:
        raise EnvLedgerError("an error budget needs a budget_id")
    seen = [c.component for c in comps]
    if len(set(seen)) != len(seen):
        raise EnvLedgerError("a budget must not list a component twice")
    combined = combine_quadrature(comps)
    return {
        "budget_id": str(budget_id),
        "quantity": str(quantity),
        "components": [c.as_dict() for c in comps],
        "combination_method": QUADRATURE,
        "combined_uncertainty": combined,
        "coverage_factor": float(coverage_factor),
        "expanded_uncertainty": float(coverage_factor) * combined,
        "claim_class": ClaimClass.MODEL_PREDICTION.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


def is_within_budget(residual: float, combined_sigma: float) -> bool:
    """Is a residual within the combined (quadrature) uncertainty?

    ``True`` means the residual is consistent with the known error sources: it
    is **not** anomalous, and calling it a signal is the promotion
    :func:`refuse_subbudget_as_anomaly` blocks.
    """
    if float(combined_sigma) < 0.0:
        raise EnvLedgerError("the combined sigma cannot be negative")
    return abs(float(residual)) <= float(combined_sigma)


# --- load-bearing refusals ------------------------------------------------

def refuse_subbudget_as_anomaly(
        residual: float, combined_sigma: float,
        claim: str = "an anomaly") -> None:
    """Refuse calling a within-budget residual an anomaly. This ALWAYS raises.

    A residual that does not exceed the combined uncertainty is consistent
    with the instrument, calibration, clock, environment, fixture, specimen,
    orientation, numerical, DSP, operator and model terms already accounted
    for. It is a statement about the error budget, not a discovery.
    """
    within = is_within_budget(residual, combined_sigma)
    raise EnvLedgerError(
        f"refused: calling residual {float(residual):g} {claim!r}. It "
        f"{'does NOT exceed' if within else 'exceeds'} the combined "
        f"quadrature uncertainty {float(combined_sigma):g}. A residual below "
        f"the combined uncertainty is not anomalous: it is consistent with "
        f"the eleven known error sources and is a statement about the budget, "
        f"not a new effect. {VERDICT}.")


def refuse_manual_as_sensor(
        claim: str = "a manual declaration is a sensor trace") -> None:
    """A manual note is not a sensor measurement. This ALWAYS raises.

    A manual declaration ("the lab was about 21 C") is a SOURCE_CLAIM entered
    by hand; it carries the lowest authority in the ledger. Treating it as a
    live sensor trace inflates its standing past what a human note can bear.
    """
    raise EnvLedgerError(
        f"refused: {claim!r}. A manual declaration is a SOURCE_CLAIM with the "
        f"lowest source authority ({SOURCE_AUTHORITY[EnvSource.MANUAL]}); a "
        f"sensor trace has the highest ({SOURCE_AUTHORITY[EnvSource.SENSOR]}). "
        f"A hand-entered note is not an instrument reading of the environment "
        f"and cannot stand in for one. {VERDICT}.")


def refuse_synthetic_env_as_measured(
        claim: str = "these environmental channels are measured") -> None:
    """Synthetic env channels are not measurements. This ALWAYS raises.

    Every channel this module builds is evaluated from a seeded generator on a
    supplied clock -- a SYNTHETIC_OBSERVATION. No thermometer, barometer,
    accelerometer, microphone or field probe was operated, so no environmental
    quantity was measured here. The REAL-mode ledger is BLOCKED_MISSING_INPUT.
    """
    raise EnvLedgerError(
        f"refused: {claim!r}. The channels here are deterministic synthetic "
        f"observations produced from a seeded generator on a supplied clock, "
        f"not instrument readings. No environmental sensor was operated; the "
        f"REAL-mode ledger is {BLOCKED_MISSING_INPUT}. {VERDICT}.")


#: The forbidden promotions this module guards, for the red team.
FORBIDDEN_PROMOTIONS = {
    "subbudget_to_anomaly": refuse_subbudget_as_anomaly,
    "manual_to_sensor": refuse_manual_as_sensor,
    "synthetic_env_to_measured": refuse_synthetic_env_as_measured,
}


# --- a fully-formed synthetic ledger, for tests and demos -----------------

#: Deterministic per-kind parameters (mean, noise, drift, uncertainty) for the
#: demo synthetic ledger. Every value is a model figure, not a measurement.
_SYNTHETIC_PARAMS: dict[EnvChannelKind, tuple[float, float, float, float]] = {
    EnvChannelKind.TEMPERATURE: (295.0, 0.02, 0.0, 0.05),
    EnvChannelKind.HUMIDITY: (45.0, 0.5, 0.0, 1.0),
    EnvChannelKind.PRESSURE: (101325.0, 5.0, 0.0, 10.0),
    EnvChannelKind.VIBRATION: (0.0, 0.01, 0.0, 0.005),
    EnvChannelKind.ACOUSTIC: (0.0, 0.02, 0.0, 0.01),
    EnvChannelKind.LINE_VOLTAGE: (120.0, 0.3, 0.0, 0.5),
    EnvChannelKind.EMI_RF: (0.001, 0.0002, 0.0, 0.0001),
    EnvChannelKind.MAGNETIC_FIELD: (5e-5, 1e-7, 0.0, 5e-8),
    EnvChannelKind.OPERATOR_ACTION: (0.0, 0.0, 0.0, 0.0),
}


def synthetic_ledger(run_id: str, t, *, seed: int,
                     mode: EnvMode = EnvMode.SYNTHETIC,
                     drift_overrides: dict | None = None) -> EnvironmentLedger:
    """Build a full deterministic synthetic ledger over the supplied clock.

    Each channel gets its own sub-seed derived from ``seed`` and the kind, so
    the whole ledger is reproducible byte-for-byte. ``drift_overrides`` maps a
    channel kind to a drift rate (units/second) to inject a known drift.
    """
    overrides = drift_overrides or {}
    t_arr = np.asarray(t, dtype=float)
    channels = []
    for i, (kind, (mean, noise, drift, unc)) in enumerate(
            _SYNTHETIC_PARAMS.items()):
        d = float(overrides.get(kind, drift))
        ch = synthetic_channel(kind, t_arr, seed=int(seed) + i,
                               mean=mean, noise=noise, drift_rate=d,
                               uncertainty=unc, source=EnvSource.SYNTHETIC)
        channels.append(ch)
    return EnvironmentLedger(run_id=run_id, mode=mode, clock_t0=float(t_arr[0]),
                             channels=tuple(channels))


def real_mode_status() -> dict:
    """The REAL-mode ledger as it actually stands here: blocked.

    No environmental sensor was operated in this repository, so a live ledger
    of real ambient conditions cannot be formed. It is BLOCKED_MISSING_INPUT.
    """
    return {
        "mode": EnvMode.REAL.value,
        "status": BLOCKED_MISSING_INPUT,
        "reason": ("no temperature, humidity, pressure, vibration, acoustic, "
                   "mains, RF or magnetic sensor was operated; nothing was "
                   "acquired"),
        "claim_class": BLOCKED_MISSING_INPUT,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- report ---------------------------------------------------------------

def environment_report() -> dict:
    """The standing statement of what this module is and is not."""
    return {
        "what_this_is": (
            "an environmental ledger that records, per run, the ambient "
            "nuisance conditions as time-series channels -- temperature, "
            "humidity, pressure, vibration, acoustic, mains, RF, magnetic "
            "field and operator actions -- each with units, an uncertainty "
            "and a content hash, aligned to the experiment clock, feeding an "
            "eleven-component quadrature error budget"),
        "channels": [k.value for k in EnvChannelKind],
        "modes": [m.value for m in EnvMode],
        "sources_ranked": [s.value for s in
                           sorted(EnvSource, key=source_authority,
                                  reverse=True)],
        "source_authority": {s.value: source_authority(s) for s in EnvSource},
        "required_by_default": sorted(k.value for k in DEFAULT_REQUIRED_KINDS),
        "missing_data_policies": [p.value for p in MissingDataPolicy],
        "budget_components": [c.value for c in BudgetComponent],
        "combination_method": QUADRATURE,
        "budget_note": (
            "a residual below the combined quadrature uncertainty is NOT "
            "anomalous -- is_within_budget states it, "
            "refuse_subbudget_as_anomaly refuses the promotion"),
        "real_mode_status": BLOCKED_MISSING_INPUT,
        "refusals": list(FORBIDDEN_PROMOTIONS),
        "claim_class": ClaimClass.SOFTWARE_IMPLEMENTED.value,
        "synthetic_channel_class": ClaimClass.SYNTHETIC_OBSERVATION.value,
        "max_evidence": MAX_ENV_EVIDENCE.name,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not measure any ambient condition. Every channel is a "
            "deterministic synthetic observation produced from a seeded "
            "generator on a supplied clock; no sensor was operated and the "
            "REAL-mode ledger is BLOCKED_MISSING_INPUT. A manual declaration "
            "is a SOURCE_CLAIM of the lowest authority, never a sensor trace, "
            "and a residual within the combined uncertainty is consistent "
            "with the known error budget, not a new effect. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "BLOCKED_MISSING_INPUT",
    "MAX_ENV_EVIDENCE", "QUADRATURE", "EnvLedgerError",
    "EnvChannelKind", "EnvMode", "EnvSource", "SOURCE_AUTHORITY",
    "SOURCE_CLAIM_CLASS", "CHANNEL_UNITS", "DEFAULT_REQUIRED_KINDS",
    "source_authority", "EnvChannel", "synthetic_channel",
    "EnvironmentLedger", "MissingDataPolicy", "CompletenessResult",
    "check_completeness", "clock_offset_seconds", "is_clock_aligned",
    "trace_lag_samples", "realign_to_clock", "drift_rate",
    "nuisance_correlation", "BudgetComponent", "ErrorComponent",
    "environment_component", "combine_quadrature", "build_error_budget",
    "is_within_budget", "refuse_subbudget_as_anomaly",
    "refuse_manual_as_sensor", "refuse_synthetic_env_as_measured",
    "FORBIDDEN_PROMOTIONS", "synthetic_ledger", "real_mode_status",
    "environment_report",
]
