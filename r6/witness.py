"""P11 — metric-indexed witness memory.

The module the whole R6 correction is about.

A memory record here has five *separate* channels (core/10):

    EXACT ADDRESS AND PROVENANCE     never decays
    APPROXIMATE PROBABILISTIC MEMORY may decay, by design
    CLOCK / PHASE WITNESS            characterized, compared, not decayed
    ENVIRONMENTAL WITNESS            nuisance channels
    OPTICAL READOUT                  how the state was actually observed

The firewall between channels two and three is the point. Payload
relaxation and clock phase are distinct observables that a common
environmental cause can move together. Inferring proper time from
payload confidence is forbidden and is refused in code, not in prose:
see :func:`infer_proper_time_from_payload`.

What this module is *not*: it is not a demonstration. No clock has
been built, no defect has been written or read, no comparison has been
performed. Every number produced here comes from a declared model with
declared parameters.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, asdict

from . import NUISANCE_CHANNELS, WITNESS_CLASSES

#: Caesium-133 ground-state hyperfine transition frequency (Hz). This
#: is a *definition*: the SI second is 9192631770 periods of this
#: transition. Caesium-133 is stable; there is no decay involved. See
#: claim R6-C-101, which records the source's error.
CS133_HYPERFINE_HZ = 9_192_631_770

#: Statuses a record may hold (schemas/metric_indexed_memory_record).
RECORD_STATUSES = (
    "VALID",
    "PAYLOAD_DECAYING",
    "CLOCK_CONFIDENCE_DECAYING",
    "ADDRESS_EXPIRED",
    "TAMPER_EVIDENCE_FAILED",
    "UNIDENTIFIABLE",
    "EXPIRED",
)

#: Ordinary causes of payload relaxation (core/11, amendment). A
#: metric contribution is identifiable only after all of these are
#: measured and bounded. There are twelve; none of them is spacetime.
ORDINARY_DECAY_CAUSES = (
    "intrinsic_relaxation",
    "temperature",
    "magnetic_field",
    "electric_field",
    "strain",
    "radiation",
    "vibration",
    "chemistry",
    "read_disturb",
    "manufacturing_variation",
    "clock_drift",
    "detector_drift",
)


class RefusedError(RuntimeError):
    """Raised when an operation is refused rather than approximated."""


# --------------------------------------------------------------------
# Exact, non-decaying fields
# --------------------------------------------------------------------

@dataclass(frozen=True)
class ExactCore:
    """The part of a record that never decays (core/10).

    Address, source, hash, permissions, custody, calibration IDs and
    transformation receipts are digital and exact. If any of these
    could decay, the record could not be audited after the fact, and
    tamper evidence would be meaningless.
    """

    address: str
    source_hash: str
    permissions: tuple[str, ...]
    chain_of_custody: tuple[str, ...]
    calibration_ids: tuple[str, ...]
    transformation_receipts: tuple[str, ...] = ()

    def digest(self) -> str:
        blob = json.dumps(asdict(self), sort_keys=True, default=list)
        return hashlib.sha256(blob.encode()).hexdigest()


# --------------------------------------------------------------------
# Probabilistic payload with declared decay
# --------------------------------------------------------------------

def _normalize(p: list[float]) -> list[float]:
    s = sum(p)
    if s <= 0:
        raise ValueError("probability vector must have positive mass")
    return [x / s for x in p]


@dataclass
class ProbabilisticPayload:
    """A variable-alphabet payload on the simplex (core/10).

    ``p0`` is the posterior at ``t0``. ``prior`` is where the payload
    relaxes *to* — it must be declared, because "decays to nothing" is
    not a model. ``tau`` is the decay scale and ``beta`` the stretch
    exponent of

        w(t) = exp[-((t - t0)/tau)^beta]
        p(t) = w(t) p0 + (1 - w(t)) prior
    """

    payload_id: str
    p0: list[float]
    prior: list[float]
    t0: float
    tau: float
    beta: float = 1.0
    #: Which ordinary causes have actually been measured for this
    #: payload. Promotion depends on this being complete.
    characterized_causes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.p0) != len(self.prior):
            raise ValueError("p0 and prior must share an alphabet size")
        if len(self.p0) < 2:
            raise ValueError("alphabet must have at least two symbols")
        if self.tau <= 0:
            raise ValueError("tau must be positive")
        if self.beta <= 0:
            raise ValueError("beta must be positive")
        self.p0 = _normalize([float(x) for x in self.p0])
        self.prior = _normalize([float(x) for x in self.prior])

    @property
    def alphabet_size(self) -> int:
        return len(self.p0)

    def weight(self, t: float) -> float:
        """Memory retention w(t) in [0, 1]. Before t0 it is 1."""
        dt = t - self.t0
        if dt <= 0:
            return 1.0
        return math.exp(-((dt / self.tau) ** self.beta))

    def state(self, t: float) -> list[float]:
        w = self.weight(t)
        return [w * a + (1.0 - w) * b
                for a, b in zip(self.p0, self.prior)]

    def entropy_bits(self, t: float) -> float:
        return -sum(x * math.log2(x) for x in self.state(t) if x > 0)

    def informative_bits(self, t: float) -> float:
        """Bits the payload holds *relative to its own prior*.

        This is the KL divergence D(p(t) || prior). It is the honest
        measure of what has not yet been lost: it goes to zero as the
        payload relaxes, whatever the alphabet size.
        """
        return sum(
            x * math.log2(x / q)
            for x, q in zip(self.state(t), self.prior)
            if x > 0 and q > 0
        )

    def fully_characterized(self) -> bool:
        return set(self.characterized_causes) >= set(ORDINARY_DECAY_CAUSES)

    def uncharacterized_causes(self) -> tuple[str, ...]:
        return tuple(c for c in ORDINARY_DECAY_CAUSES
                     if c not in self.characterized_causes)


# --------------------------------------------------------------------
# Clock witness — a separate channel with a real oscillator
# --------------------------------------------------------------------

@dataclass
class ClockWitness:
    """A characterized oscillator, or nothing.

    A witness channel requires a transition or oscillator with a known
    nominal frequency and a measured instability. A payload does not
    become a clock by decaying.

        phi(t) = 2 pi nu0 * proper_time + d_synth + d_transfer
                 + d_env + d_readout
    """

    witness_id: str
    nu0_hz: float
    #: Fractional frequency instability (Allan deviation) at 1 s.
    adev_1s: float
    #: Nuisance channels actually recorded for this witness.
    recorded_channels: tuple[str, ...] = ()
    #: Set once the oscillator has been compared to a reference.
    calibrated_against: str | None = None
    #: True only when a second, independent group reproduced it.
    independently_replicated: bool = False

    def __post_init__(self) -> None:
        if self.nu0_hz <= 0:
            raise ValueError("a clock needs a positive nominal frequency")
        if self.adev_1s <= 0:
            raise ValueError("a clock needs a measured instability")

    def missing_channels(self) -> tuple[str, ...]:
        return tuple(c for c in NUISANCE_CHANNELS
                     if c not in self.recorded_channels)

    def phase_uncertainty_rad(self, averaging_s: float) -> float:
        """Phase uncertainty after averaging, from the Allan deviation.

        sigma_phi ~ 2 pi nu0 * adev(tau) * tau, with white-frequency
        averaging adev(tau) = adev_1s / sqrt(tau).
        """
        if averaging_s <= 0:
            raise ValueError("averaging time must be positive")
        adev_tau = self.adev_1s / math.sqrt(averaging_s)
        return 2.0 * math.pi * self.nu0_hz * adev_tau * averaging_s

    def evidence_class(self) -> str:
        """Where this witness sits on the ladder (core/11).

        Promotion is gated on evidence, not on intent. A witness with
        missing nuisance channels cannot pass CLOCK_COMPARISON however
        good its oscillator is.
        """
        if self.calibrated_against is None:
            return "CLOCK_MODEL"
        if self.missing_channels():
            return "CLOCK_CALIBRATED"
        if self.independently_replicated:
            return "INDEPENDENTLY_REPLICATED_METROLOGY"
        return "CLOCK_COMPARISON"


def caesium_reference(witness_id: str = "CS133-PRIMARY",
                      adev_1s: float = 1e-13) -> ClockWitness:
    """A caesium primary-standard-like witness.

    The frequency is the SI definition. The default instability is a
    plausible commercial caesium beam figure, not a measurement of any
    device the programme owns.
    """
    return ClockWitness(witness_id=witness_id,
                        nu0_hz=float(CS133_HYPERFINE_HZ),
                        adev_1s=adev_1s)


# --------------------------------------------------------------------
# Clock comparison — the only route to a metric statement
# --------------------------------------------------------------------

@dataclass(frozen=True)
class ComparisonResult:
    """Outcome of comparing two witnesses across a transfer link."""

    witness_a: str
    witness_b: str
    #: Measured fractional frequency difference.
    frac_diff: float
    #: Combined uncertainty on that difference.
    frac_uncertainty: float
    #: Fractional shift predicted by the declared metric model.
    predicted_frac: float | None
    evidence_class: str
    status: str
    notes: tuple[str, ...] = ()

    @property
    def consistent(self) -> bool:
        """Whether the measurement agrees with the prediction.

        Deliberately **not** a bare numerical check. A comparison whose
        witnesses are uncalibrated, or whose nuisance channels are
        unrecorded, or whose prediction sits below the combined
        uncertainty, has not tested anything — and must not hand a
        caller a green light by arithmetic coincidence. Agreement is
        reported only from a status that means the prediction was
        actually put at risk.
        """
        if self.predicted_frac is None:
            return False
        if self.status not in ("RELATIVISTIC_SHIFT_CONSISTENT",
                               "MODEL_INCONSISTENT"):
            return False
        return abs(self.frac_diff - self.predicted_frac) <= \
            2.0 * self.frac_uncertainty

    def as_record(self) -> dict:
        d = asdict(self)
        d["notes"] = list(self.notes)
        d["consistent"] = self.consistent
        return d


def gravitational_redshift_frac(delta_height_m: float,
                                g: float = 9.80665,
                                c: float = 299_792_458.0) -> float:
    """Fractional frequency shift for a height difference.

    df/f = g*dh/c^2, the weak-field limit. At dh = 1 m this is
    ~1.09e-16 — measurable by optical clocks, and about three orders
    of magnitude below a good caesium beam. That gap is why the
    platform choice matters and why a decaying payload is nowhere
    near sufficient.
    """
    return g * delta_height_m / (c * c)


def velocity_dilation_frac(speed_ms: float,
                           c: float = 299_792_458.0) -> float:
    """Fractional shift from second-order Doppler, -v^2/(2c^2)."""
    return -(speed_ms ** 2) / (2.0 * c * c)


def compare_witnesses(a: ClockWitness,
                      b: ClockWitness,
                      *,
                      measured_frac_diff: float,
                      averaging_s: float,
                      transfer_link_frac_uncertainty: float,
                      predicted_frac: float | None = None,
                      ) -> ComparisonResult:
    """Compare two witnesses, refusing to overstate the result.

    The comparison is only as good as the *worse* of the two clocks
    and the transfer link. A prediction is only tested if the combined
    uncertainty is small enough to distinguish it from zero.
    """
    notes: list[str] = []
    if a.nu0_hz != b.nu0_hz:
        notes.append(
            "witnesses have different nominal frequencies; the "
            "fractional comparison assumes a declared ratio")

    ua = a.adev_1s / math.sqrt(averaging_s)
    ub = b.adev_1s / math.sqrt(averaging_s)
    combined = math.sqrt(ua ** 2 + ub ** 2
                         + transfer_link_frac_uncertainty ** 2)

    missing = set(a.missing_channels()) | set(b.missing_channels())
    if missing:
        notes.append(
            f"{len(missing)} nuisance channels unrecorded: "
            f"{', '.join(sorted(missing))}")

    cls = "CLOCK_COMPARISON"
    if a.calibrated_against is None or b.calibrated_against is None:
        cls = "CLOCK_MODEL"
        notes.append("at least one witness is uncalibrated")
    elif missing:
        cls = "CLOCK_CALIBRATED"

    status = "COMPARISON_REPORTED"
    if predicted_frac is not None:
        if abs(predicted_frac) < combined:
            status = "PREDICTION_BELOW_RESOLUTION"
            notes.append(
                f"predicted shift {predicted_frac:.3e} is below the "
                f"combined uncertainty {combined:.3e}; this comparison "
                f"cannot test it")
        elif cls in ("CLOCK_COMPARISON",
                     "INDEPENDENTLY_REPLICATED_METROLOGY"):
            ok = abs(measured_frac_diff - predicted_frac) <= 2.0 * combined
            status = ("RELATIVISTIC_SHIFT_CONSISTENT" if ok
                      else "MODEL_INCONSISTENT")
            if ok:
                cls = "RELATIVISTIC_SHIFT_CONSISTENT"
        else:
            status = "PREDICTION_NOT_TESTED_UNCHARACTERIZED"
            notes.append(
                "the prediction is resolvable in principle but the "
                "witnesses are not characterized enough to test it")

    if a.independently_replicated and b.independently_replicated and \
            cls == "RELATIVISTIC_SHIFT_CONSISTENT":
        cls = "INDEPENDENTLY_REPLICATED_METROLOGY"

    assert cls in WITNESS_CLASSES, cls
    return ComparisonResult(
        witness_a=a.witness_id, witness_b=b.witness_id,
        frac_diff=measured_frac_diff, frac_uncertainty=combined,
        predicted_frac=predicted_frac, evidence_class=cls,
        status=status, notes=tuple(notes))


# --------------------------------------------------------------------
# The firewall
# --------------------------------------------------------------------

def infer_proper_time_from_payload(payload: ProbabilisticPayload,
                                   *args, **kwargs):
    """Always refuses. This is the central R6 correction, in code.

    Payload confidence is a decoder statistic. Proper time is phase
    accumulated by a characterized oscillator. There are twelve
    ordinary causes of relaxation and a common environmental cause can
    move both channels together, so even a *correlation* between decay
    and a clock does not license the inference.

    The only supported route to a metric statement is
    :func:`compare_witnesses` on an actual :class:`ClockWitness`.
    """
    raise RefusedError(
        "proper time may not be inferred from payload decay. "
        f"Payload {payload.payload_id!r} has "
        f"{len(payload.uncharacterized_causes())} uncharacterized "
        "ordinary decay causes, and characterizing all twelve would "
        "still not make a payload a clock. Use compare_witnesses() "
        "with a ClockWitness (r6 FORBIDDEN_COLLAPSES: "
        "DECAY_IS_PROPER_TIME).")


def payload_is_a_clock(payload: ProbabilisticPayload) -> bool:
    """Constant ``False``, kept so the answer is inspectable."""
    return False


# --------------------------------------------------------------------
# Bayesian reconstruction with an information bound
# --------------------------------------------------------------------

@dataclass(frozen=True)
class Reconstruction:
    """A bounded reconstruction, or an explicit refusal."""

    payload_id: str
    status: str
    posterior: list[float] | None
    prior: list[float]
    posterior_entropy_bits: float | None
    information_gain_bits: float | None
    effective_observations: float
    refusal_reason: str | None = None

    def as_record(self) -> dict:
        return asdict(self)


def reconstruct(payload: ProbabilisticPayload,
                t: float,
                observations: list[list[float]] | None = None,
                *,
                identifiability_threshold: float = 1e-3,
                root_certificate: str | None = None,
                ) -> Reconstruction:
    """Bayesian reconstruction of a decayed payload.

    New *observations* (likelihood vectors over the alphabet) may
    sharpen the posterior. A ``root_certificate`` may accompany the
    record but contributes **no information**: it is checked for
    presence and then ignored in the arithmetic, because a certificate
    attests to provenance, not to the physical state.

    Refuses with ``UNIDENTIFIABLE`` when the decayed state is
    indistinguishable from the prior and no observation resolves it.
    """
    state = payload.state(t)
    prior = payload.prior
    kl = payload.informative_bits(t)

    obs = observations or []
    post = list(state)
    for like in obs:
        if len(like) != payload.alphabet_size:
            raise ValueError("likelihood has wrong alphabet size")
        if any(x < 0 for x in like):
            raise ValueError("likelihood must be non-negative")
        post = [a * b for a, b in zip(post, like)]
        if sum(post) <= 0:
            return Reconstruction(
                payload_id=payload.payload_id,
                status="UNIDENTIFIABLE",
                posterior=None, prior=prior,
                posterior_entropy_bits=None,
                information_gain_bits=None,
                effective_observations=float(len(obs)),
                refusal_reason=(
                    "an observation assigned zero likelihood to every "
                    "symbol; the posterior is undefined"))
    post = _normalize(post)

    if kl < identifiability_threshold and not obs:
        return Reconstruction(
            payload_id=payload.payload_id,
            status="UNIDENTIFIABLE",
            posterior=None, prior=prior,
            posterior_entropy_bits=None,
            information_gain_bits=None,
            effective_observations=0.0,
            refusal_reason=(
                f"payload has relaxed to within "
                f"{kl:.2e} bits of its prior and no new observation "
                f"was supplied. A root certificate"
                + (" is present but" if root_certificate else " would")
                + " cannot restore information the channel destroyed "
                  "(r6 FORBIDDEN_COLLAPSES: "
                  "ROOT_CERTIFICATE_RESTORES_INFORMATION)."))

    post_entropy = -sum(x * math.log2(x) for x in post if x > 0)
    gain = sum(x * math.log2(x / q)
               for x, q in zip(post, prior) if x > 0 and q > 0)

    status = "RECONSTRUCTED"
    if not obs:
        status = "DECAYED_STATE_REPORTED"
    return Reconstruction(
        payload_id=payload.payload_id,
        status=status,
        posterior=post, prior=prior,
        posterior_entropy_bits=post_entropy,
        information_gain_bits=gain,
        effective_observations=float(len(obs)))


# --------------------------------------------------------------------
# Clock-attested tamper-evident record
# --------------------------------------------------------------------

@dataclass
class WitnessRecord:
    """A memory record binding all five channels (schemas/…)."""

    record_id: str
    exact: ExactCore
    payload: ProbabilisticPayload
    witness: ClockWitness | None
    environmental_record_ids: tuple[str, ...] = ()
    readout_records: list[dict] = field(default_factory=list)
    #: Monotonic counter — must never decrease.
    event_counter: int = 0
    prev_chain_hash: str | None = None

    def chain_hash(self) -> str:
        """Hash over the exact core, counter and previous link."""
        blob = json.dumps({
            "record_id": self.record_id,
            "exact": self.exact.digest(),
            "payload_id": self.payload.payload_id,
            "witness_id": self.witness.witness_id if self.witness else None,
            "counter": self.event_counter,
            "prev": self.prev_chain_hash,
        }, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def status(self, t: float,
               *, payload_floor: float = 0.05,
               clock_floor_rad: float = math.pi) -> str:
        """Current status, evaluated at time ``t``."""
        if self.witness is not None:
            sigma = self.witness.phase_uncertainty_rad(
                max(t - self.payload.t0, 1.0))
            if sigma > clock_floor_rad:
                return "CLOCK_CONFIDENCE_DECAYING"
        if self.payload.informative_bits(t) < payload_floor:
            return "PAYLOAD_DECAYING"
        return "VALID"


def verify_chain(records: list[WitnessRecord]) -> dict:
    """Verify a hash chain and monotonic counter.

    Physical drift is not tamper evidence (core/13); this is. The
    check is entirely cryptographic and entirely about the exact,
    non-decaying fields.
    """
    problems: list[str] = []
    prev_hash: str | None = None
    prev_counter = -1
    for r in records:
        if r.prev_chain_hash != prev_hash:
            problems.append(
                f"{r.record_id}: chain break (expected prev "
                f"{prev_hash}, got {r.prev_chain_hash})")
        if r.event_counter <= prev_counter:
            problems.append(
                f"{r.record_id}: counter not monotonic "
                f"({r.event_counter} after {prev_counter})")
        prev_counter = r.event_counter
        prev_hash = r.chain_hash()
    return {
        "records": len(records),
        "ok": not problems,
        "status": "VALID" if not problems else "TAMPER_EVIDENCE_FAILED",
        "problems": problems,
    }
