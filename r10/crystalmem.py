"""R10.6 — a fading-memory crystal shift register, as hypothesis only.

The source material proposes that a crystal can *store* something: that a
write stimulus leaves a trace which can be read back later. This module
gives that proposal a typed, arithmetic body so it can be reasoned about
and, above all, argued with. It is a **hypothesis**, not a measurement.
No specimen has been written to, driven, or read; the status of every
claim here is ``BENCH_TEST_REQUIRED``.

The model is a *fading* memory. A state written at ``t = 0`` decays as
``exp(-t / tau)``; a stored bit is recoverable only while its amplitude
stays above a read threshold, so it has a finite retention window
``t_max = tau * ln(A0 / threshold)``. Strung into an N-stage shift
register, a value both decays with age and *disperses* (spreads) as it
propagates, so only a bounded number of stages stay readable.

**The firewall is the point of the module.** A trace that decays and
disperses is *exactly* what ordinary material relaxation looks like:
acoustic ringdown, thermal relaxation, trapped-charge decay all produce
a decaying envelope. So a decaying echo is **not** evidence of stored
information. With equal time constants the memory envelope and a passive
relaxation envelope are point-for-point identical -- the decay curve
alone carries zero bits about whether anything was stored. What would
distinguish a memory is *ordered delayed readout*: the written pattern
returning in the correct order after a controlled delay, which a passive
ringdown cannot do because it carries no pattern.
:func:`refuse_memory_claim_without_delayed_readout` enforces this, and
:func:`null_model_report` shows the two models collapsing onto one curve.

A genuine memory is also destructive to read and therefore needs a
refresh: :func:`destructive_read` consumes the stored state, and without
a :func:`refresh` the data is gone on the next read. A read that does not
consume, or that persists without a rewrite, is a transient echo, not a
register cell.

Nothing here is measured. ``measured_here: nothing``;
``PHYSICAL_VALIDATION_NOT_CLAIMED``. The decay-time constant ``tau``, the
stage latency, and the dispersion length are *model parameters supplied
to the hypothesis*, not device figures characterised on a bench.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

# --- claim discipline: statuses come from the contract ----------------

#: Statuses this module uses, quoted verbatim from
#: ``01_GOVERNANCE/CLAIM_STATUS_CONTRACT.md``. Kept as a constant so a
#: test can assert that nothing here invents a status outside the
#: contract's vocabulary.
CONTRACT_STATUSES = (
    "PHYSICAL_HYPOTHESIS",
    "BENCH_TEST_REQUIRED",
)

#: The whole module sits at this status. Nothing is measured, so nothing
#: can be MEASURED, REPLICATED, or UNEXPLAINED_BY_DECLARED_BUDGET.
CLAIM_STATUS = "BENCH_TEST_REQUIRED"
EVIDENCE_CLASS = "PHYSICAL_HYPOTHESIS"
HARDWARE_STATUS = "DEFERRED — no specimen has been written, driven, or read"
MEASURED_HERE = "nothing"
VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

# --- amplitude constants ----------------------------------------------

#: Write amplitude, normalised. Dimensionless by construction: every
#: amplitude in this module is a fraction of the write amplitude.
DEFAULT_A0 = 1.0

#: Read threshold as an *exact* rational: a stored amplitude at or below
#: 1% of the write amplitude is treated as unreadable. This is a chosen
#: convention, not a measured device figure -- a real detector's noise
#: floor would set it, and no detector has been built. It is exact so
#: that stage counts and window comparisons stay exact wherever the
#: transcendental decay does not force a float.
READ_THRESHOLD = Fraction(1, 100)


class MemoryClaimRefused(RuntimeError):
    """Raised when a memory claim is asserted without ordered readout."""


class SchemaViolation(ValueError):
    """Raised when a CrystalMemory record breaks a load-bearing rule."""


# --- 1. the fading retention model ------------------------------------

def retention_amplitude(t_s: float, tau_s: float,
                        a0: float = DEFAULT_A0) -> float:
    """Amplitude of a state written at ``t=0``, after ``t_s`` seconds.

    ``A(t) = A0 * exp(-t / tau)``. Float, because the decay is
    transcendental; there is nothing exact to preserve here.
    """
    if tau_s <= 0:
        raise ValueError("tau must be positive")
    if t_s < 0:
        raise ValueError("elapsed time cannot be negative")
    if a0 <= 0:
        raise ValueError("write amplitude must be positive")
    return a0 * math.exp(-t_s / tau_s)


def retention_window(tau_s: float, a0: float = DEFAULT_A0,
                     threshold: Fraction = READ_THRESHOLD) -> float:
    """Longest delay at which a written state is still readable.

    Solving ``A0 * exp(-t / tau) = threshold`` gives
    ``t_max = tau * ln(A0 / threshold)``. At exactly ``t_max`` the
    amplitude equals the threshold; a bit is recoverable strictly
    *before* that.
    """
    if tau_s <= 0:
        raise ValueError("tau must be positive")
    thr = float(threshold)
    if a0 <= thr:
        raise ValueError(
            "write amplitude is already at or below the read threshold; "
            "there is no retention window to speak of")
    return tau_s * math.log(a0 / thr)


def recoverable(t_s: float, tau_s: float, a0: float = DEFAULT_A0,
                threshold: Fraction = READ_THRESHOLD) -> bool:
    """Is a state written at ``t=0`` still above threshold at ``t_s``?"""
    return retention_amplitude(t_s, tau_s, a0) > float(threshold)


# --- 2. destructive read and the refresh it forces --------------------

@dataclass(frozen=True)
class StoredBit:
    """One bit held as a decaying amplitude."""

    amplitude: float
    written_value: int          # 0 or 1
    age_s: float

    def __post_init__(self) -> None:
        if self.written_value not in (0, 1):
            raise ValueError("written_value must be 0 or 1")
        if self.amplitude < 0:
            raise ValueError("amplitude cannot be negative")
        if self.age_s < 0:
            raise ValueError("age cannot be negative")


@dataclass(frozen=True)
class ReadResult:
    """What a destructive read returns, and what it leaves behind."""

    recovered: bool
    value: int | None
    residual: StoredBit         # the consumed cell: amplitude driven to 0


def write_bit(value: int, a0: float = DEFAULT_A0) -> StoredBit:
    """Write a bit at full amplitude, age zero."""
    return StoredBit(a0, value, 0.0)


def age_bit(bit: StoredBit, tau_s: float, dt_s: float) -> StoredBit:
    """Advance a stored bit by ``dt_s`` seconds of fading."""
    if dt_s < 0:
        raise ValueError("cannot age backwards")
    factor = retention_amplitude(dt_s, tau_s, 1.0)
    return StoredBit(bit.amplitude * factor, bit.written_value,
                     bit.age_s + dt_s)


def destructive_read(bit: StoredBit,
                     threshold: Fraction = READ_THRESHOLD) -> ReadResult:
    """Read a cell, consuming its stored state.

    This is what makes the cell a *memory* rather than a passive echo:
    the read collapses the amplitude to zero. Whatever was there is now
    gone from the cell, and only a refresh puts it back. A read that
    left the amplitude standing would be a measurement of an ongoing
    ringdown, not a register readout.
    """
    thr = float(threshold)
    recovered = bit.amplitude > thr
    value = bit.written_value if recovered else None
    residual = StoredBit(0.0, bit.written_value, bit.age_s)
    return ReadResult(recovered, value, residual)


def refresh(bit: StoredBit, a0: float = DEFAULT_A0) -> StoredBit:
    """Rewrite a cell's value at full amplitude (the refresh cycle)."""
    return StoredBit(a0, bit.written_value, 0.0)


def refresh_required(destructive: bool) -> bool:
    """A destructive read forces a refresh to persist. That is the rule.

    Returns whether a refresh is required given the read's destructiveness.
    A non-destructive read would not need one -- but then the cell is not
    consumed, and a persistent uncleared response is the signature of a
    passive relaxation, not a memory.
    """
    return bool(destructive)


# --- 3. the shift register: decay plus dispersion ---------------------

@dataclass(frozen=True)
class ShiftRegister:
    """An N-stage fading shift register.

    Every parameter is a *model input*, not a measured device figure.
    A written value shifts one stage per clock; by the time it has
    reached stage ``k`` it has aged ``k * stage_latency_s`` and its peak
    has been lowered both by decay and by dispersion.
    """

    n_stages: int               # exact stage count
    stage_latency_s: float      # clock period per stage (model input)
    tau_s: float                # decay constant (model input, unmeasured)
    dispersion_stages: float    # spreading length in stages; inf = none
    a0: float = DEFAULT_A0
    threshold: Fraction = READ_THRESHOLD

    def __post_init__(self) -> None:
        if not isinstance(self.n_stages, int) or self.n_stages < 1:
            raise ValueError("n_stages must be a positive integer")
        if self.stage_latency_s <= 0:
            raise ValueError("stage latency must be positive")
        if self.tau_s <= 0:
            raise ValueError("tau must be positive")
        if self.dispersion_stages <= 0:
            raise ValueError("dispersion length must be positive (inf = none)")
        if self.a0 <= 0:
            raise ValueError("write amplitude must be positive")


def stage_fidelity(reg: ShiftRegister, k: int) -> float:
    """Peak amplitude of a value once it has reached stage ``k``.

    Two independent losses multiply:

    * decay with age: ``exp(-k * stage_latency / tau)``;
    * dispersion of an initially sharp pulse, whose peak falls as
      ``1 / sqrt(1 + k / dispersion_stages)`` -- the standard peak
      attenuation of a spreading (Gaussian-broadening) pulse. With
      ``dispersion_stages = inf`` this factor is exactly 1 and only
      decay remains.

    Strictly decreasing in ``k``, so the readable stages are a prefix.
    """
    if not 0 <= k <= reg.n_stages:
        raise ValueError(f"stage {k} outside 0..{reg.n_stages}")
    decay = math.exp(-k * reg.stage_latency_s / reg.tau_s)
    dispersion = 1.0 / math.sqrt(1.0 + k / reg.dispersion_stages)
    return reg.a0 * decay * dispersion


def last_readable_stage(reg: ShiftRegister) -> int:
    """Highest stage index whose fidelity still exceeds the threshold.

    Stage 0 is the freshly written value (fidelity ``a0``). Because
    fidelity is strictly decreasing, a linear scan finds the boundary
    exactly. Returns -1 only if even stage 0 is unreadable, which cannot
    happen while ``a0 > threshold`` but is handled rather than assumed.
    """
    thr = float(reg.threshold)
    k = 0
    while k <= reg.n_stages and stage_fidelity(reg, k) > thr:
        k += 1
    return k - 1


def readable_stage_count(reg: ShiftRegister) -> int:
    """Number of stages (including stage 0) that stay above threshold."""
    return last_readable_stage(reg) + 1


# --- 4. the firewall: memory versus ordinary relaxation ---------------

def memory_amplitude(t_s: float, tau_s: float,
                     a0: float = DEFAULT_A0) -> float:
    """Envelope predicted by the *memory* hypothesis: A0 exp(-t/tau)."""
    return retention_amplitude(t_s, tau_s, a0)


def ordinary_relaxation_amplitude(t_s: float, tau_relax_s: float,
                                  a0: float = DEFAULT_A0) -> float:
    """Envelope predicted by an *ordinary relaxation* null.

    An acoustic ringdown, a thermal relaxation, a trapped-charge decay:
    all of them relax as ``A0 exp(-t / tau_relax)``. It is the *same
    functional form* as the memory envelope. That identity is the whole
    problem, and this function exists to make it explicit rather than
    hide it.
    """
    return retention_amplitude(t_s, tau_relax_s, a0)


def decay_curves_indistinguishable(tau_s: float, times_s,
                                   a0: float = DEFAULT_A0,
                                   tol: float = 1e-12) -> dict:
    """Sample both envelopes and show the decay curve settles nothing.

    With the relaxation time constant equal to the memory time constant
    the two envelopes are point-for-point identical. A fit to the decay
    curve therefore cannot prefer the memory hypothesis over the null:
    the maximum absolute difference is zero to machine precision.
    """
    times = list(times_s)
    if not times:
        raise ValueError("need at least one sample time")
    mem = [memory_amplitude(t, tau_s, a0) for t in times]
    null = [ordinary_relaxation_amplitude(t, tau_s, a0) for t in times]
    max_abs_diff = max(abs(m - n) for m, n in zip(mem, null))
    return {
        "tau_s": tau_s,
        "tau_relax_s": tau_s,
        "n_samples": len(times),
        "max_abs_diff": max_abs_diff,
        "indistinguishable": max_abs_diff <= tol,
        "what_this_shows": (
            "with equal time constants the memory envelope and the "
            "ordinary-relaxation envelope are the same curve. Fitting a "
            "decay to data cannot tell them apart."),
        "what_this_does_not_show": (
            "it does not show the specimen stores nothing -- it shows "
            "that the decay curve alone is silent on the question. The "
            "question is settled only by ordered delayed readout, which "
            "the envelope does not carry."),
    }


def read_pattern_memory(pattern) -> list[int]:
    """The memory hypothesis's readout: the written pattern, in order.

    In the model a shift register clocked at the right phases returns the
    stored bits in the order they went in. This is a *model prediction*,
    not a measurement of any specimen.
    """
    bits = [int(b) for b in pattern]
    if any(b not in (0, 1) for b in bits):
        raise ValueError("pattern must be bits (0/1)")
    return bits


def read_pattern_relaxation_null(pattern) -> list[int]:
    """The null's readout: a fixed envelope shape carrying no pattern.

    A passive relaxation has one monotone envelope. Thresholded, it
    reads as ones until the envelope crosses the read threshold once,
    then zeros -- *independently of whatever was written*. That
    independence is the falsifiable content: the null cannot reproduce
    an arbitrary written pattern because it has no way to encode one.
    """
    n = len(list(pattern))
    if n == 0:
        raise ValueError("pattern must be non-empty")
    ones = n // 2                       # a fixed monotone crossing
    return [1] * ones + [0] * (n - ones)


def match_fraction(a, b) -> Fraction:
    """Exact fraction of positions where two equal-length bit lists agree."""
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("length mismatch")
    if not a:
        raise ValueError("empty sequences")
    return Fraction(sum(1 for x, y in zip(a, b) if x == y), len(a))


def ordered_readout_distinguishes(pattern) -> dict:
    """Ordered readout is the observable that separates memory from null.

    In the model the memory readout reproduces the written pattern
    exactly (match 1), while the relaxation null -- carrying no pattern
    -- cannot, unless the pattern happens to equal its fixed monotone
    shape. This is what a bench test would have to demonstrate; it is
    demonstrated here only *in the model*, and measures nothing.
    """
    bits = read_pattern_memory(pattern)
    mem = read_pattern_memory(bits)
    null = read_pattern_relaxation_null(bits)
    return {
        "pattern": bits,
        "memory_readout": mem,
        "null_readout": null,
        "memory_match": match_fraction(bits, mem),
        "null_match": match_fraction(bits, null),
        "null_is_independent_of_pattern": True,
        "envelope_alone_distinguishes": False,
        "what_this_shows": (
            "only ordered readout separates the hypotheses; the memory "
            "model returns the pattern in order, the null cannot."),
        "measured_here": MEASURED_HERE,
    }


def null_model_report(tau_s: float, times_s, pattern) -> dict:
    """The firewall in one object: same envelope, different readout."""
    return {
        "decay_curve": decay_curves_indistinguishable(tau_s, times_s),
        "ordered_readout": ordered_readout_distinguishes(pattern),
        "conclusion": (
            "a decaying resonance is presumed ordinary relaxation. The "
            "decay curve does not distinguish it from a memory; only "
            "ordered delayed readout does, and none has been observed."),
        "status": CLAIM_STATUS,
        "measured_here": MEASURED_HERE,
    }


def refuse_memory_claim_without_delayed_readout() -> None:
    """Refuse to call a decaying response a memory. This is the firewall."""
    raise MemoryClaimRefused(
        "no memory claim is available. A decaying resonance is presumed "
        "ordinary material relaxation -- acoustic ringdown, thermal "
        "relaxation, trapped-charge decay -- until ordered delayed "
        "readout is demonstrated. The decay curve alone cannot tell a "
        "fading memory from a passive ringdown: with equal time "
        "constants the two envelopes are point-for-point identical and "
        "carry zero bits about whether anything was stored. A memory "
        "claim requires the written pattern to return in the correct "
        "order after a controlled delay, distinguishable from an "
        "envelope that carries no pattern, and to survive a destructive "
        "read followed by refresh. No specimen has been written, driven "
        "or read; nothing here is measured.")


# --- 5. named controls, damage thresholds, observables ----------------

@dataclass(frozen=True)
class Control:
    """A control that a bench test would have to have in place."""

    name: str
    description: str
    why: str


#: The controls, named but not exercised -- no specimen is driven.
CONTROLS = (
    Control(
        "SECOND_UNTREATED_SPECIMEN",
        "a matched crystal never written to, read on the same "
        "instrument throughout",
        "turns an absolute envelope, which decays for many ordinary "
        "reasons, into a differential one against a passive control"),
    Control(
        "ORDERED_NONTRIVIAL_PATTERN",
        "write a known, non-monotone bit pattern, not a single bit",
        "a single bit or a monotone pattern cannot be told from a "
        "passive envelope; ordered readout needs structure to preserve"),
    Control(
        "BLIND_READ_DELAY",
        "the read delay is set by a third party, not chosen after the "
        "fact",
        "prevents fitting the readout order to the data retrospectively"),
    Control(
        "DESTRUCTIVE_READ_THEN_REFRESH",
        "confirm the read consumes the state and that only a refresh "
        "restores it",
        "a response that persists uncleared is a ringdown, not a "
        "register cell"),
    Control(
        "INSTRUMENT_DRIFT_BASELINE",
        "the readout instrument's own drift characterised against a "
        "reference",
        "instrument drift otherwise mimics a slow fade"),
)


@dataclass(frozen=True)
class DamageThreshold:
    """A named limit past which the specimen is altered or destroyed."""

    name: str
    mechanism: str
    control: str
    source: str


#: Named damage mechanisms. Deliberately carry no numbers: no specimen
#: has been driven, so any figure would be invented. A bench test would
#: measure these before writing.
DAMAGE_THRESHOLDS = (
    DamageThreshold(
        "DRIVE_FRACTURE",
        "acoustic drive above the elastic limit cracks the crystal",
        "cap drive well below the rated level and ramp slowly",
        "standard quartz-resonator drive-level practice"),
    DamageThreshold(
        "SELF_HEATING",
        "dissipated write power heats and detunes the specimen",
        "hold and log temperature; bound the dissipated power",
        "resonator self-heating literature"),
    DamageThreshold(
        "DIELECTRIC_BREAKDOWN",
        "a write field above the dielectric strength punctures the crystal",
        "keep the applied field below the rated dielectric strength",
        "dielectric-strength ratings for the material"),
    DamageThreshold(
        "DEPOLING",
        "temperature past the Curie point erases any poled state",
        "stay well below the material's Curie point",
        "ferroelectric Curie-point data for the material"),
)

#: What a bench test would record. None is recorded here.
OBSERVABLES = (
    "RETENTION_WINDOW_S",
    "READOUT_ORDER_MATCH",
    "DIFFERENTIAL_ENVELOPE_VS_CONTROL",
    "REFRESH_CYCLES_TO_PERSIST",
    "READABLE_STAGE_COUNT",
)


# --- the schema record ------------------------------------------------

@dataclass(frozen=True)
class CrystalMemory:
    """The crystal-memory hypothesis, typed to the schema.

    The load-bearing invariant, enforced in ``__post_init__``: a
    destructive read *requires* a refresh. The schema's rule "a memory
    claim requires ordered delayed readout" is why this record can only
    ever carry the status ``BENCH_TEST_REQUIRED`` -- ordered readout is
    an experiment, not a field.
    """

    memory_id: str
    specimen: str
    state_variable: str
    write_stimulus: str
    transport_equation: str
    retention_model: str
    dispersion_model: str
    read_operator: str
    destructive_read: bool
    refresh_required: bool
    capacity: dict
    fidelity: dict
    latency: dict
    controls: tuple
    damage_thresholds: tuple
    observables: tuple
    status: str = CLAIM_STATUS

    def __post_init__(self) -> None:
        if self.status not in CONTRACT_STATUSES:
            raise SchemaViolation(
                f"status {self.status!r} is not in the claim-status "
                f"contract; allowed here: {CONTRACT_STATUSES}")
        if self.destructive_read and not self.refresh_required:
            raise SchemaViolation(
                "a destructive read consumes the stored state, so a "
                "refresh is required to persist it; destructive_read=True "
                "with refresh_required=False is not a memory, it is a "
                "one-shot echo")


def build_hypothesis(reg: ShiftRegister,
                     memory_id: str = "R10_6_CRYSTAL_SHIFT_REGISTER"
                     ) -> CrystalMemory:
    """Assemble the schema record, filling the computed fields from ``reg``.

    capacity, fidelity and latency are *derived from the model
    parameters*; nothing in them is measured.
    """
    last = last_readable_stage(reg)
    return CrystalMemory(
        memory_id=memory_id,
        specimen="UNSPECIFIED_CRYSTAL (no specimen selected or driven)",
        state_variable="normalised trace amplitude (fraction of write "
                       "amplitude)",
        write_stimulus="a clocked write pulse setting one bit per stage "
                       "(model; no stimulus applied)",
        transport_equation="one-stage shift per clock; A -> A at the next "
                           "stage",
        retention_model="A(t) = A0 * exp(-t / tau); window t_max = tau * "
                        "ln(A0 / threshold)",
        dispersion_model="peak falls as 1 / sqrt(1 + k / dispersion_stages) "
                         "with stage k",
        read_operator="destructive threshold read: recover the bit if "
                      "amplitude > threshold, then clear the cell",
        destructive_read=True,
        refresh_required=refresh_required(True),
        capacity={
            "readable_stage_count": readable_stage_count(reg),
            "last_readable_stage": last,
            "n_stages": reg.n_stages,
            "bits": readable_stage_count(reg),
            "basis": "MODEL_DERIVED from stage_fidelity vs threshold",
        },
        fidelity={
            "at_stage_0": stage_fidelity(reg, 0),
            "at_last_readable_stage": stage_fidelity(reg, last)
            if last >= 0 else 0.0,
            "read_threshold": float(reg.threshold),
            "basis": "MODEL_DERIVED",
        },
        latency={
            "per_stage_s": reg.stage_latency_s,
            "to_last_readable_stage_s": max(last, 0) * reg.stage_latency_s,
            "full_register_s": reg.n_stages * reg.stage_latency_s,
            "retention_window_s": retention_window(reg.tau_s, reg.a0,
                                                   reg.threshold),
        },
        controls=CONTROLS,
        damage_thresholds=DAMAGE_THRESHOLDS,
        observables=OBSERVABLES,
        status=CLAIM_STATUS,
    )


def crystalmem_report(reg: ShiftRegister) -> dict:
    """One summary of what this module computes and, loudly, disclaims."""
    hyp = build_hypothesis(reg)
    sample_times = [i * reg.stage_latency_s for i in range(reg.n_stages + 1)]
    return {
        "memory_id": hyp.memory_id,
        "capacity": hyp.capacity,
        "fidelity": hyp.fidelity,
        "latency": hyp.latency,
        "retention_window_s": retention_window(reg.tau_s, reg.a0,
                                               reg.threshold),
        "null_model": null_model_report(reg.tau_s, sample_times,
                                        [1, 0, 1, 1, 0, 1]),
        "controls": [c.name for c in hyp.controls],
        "damage_thresholds": [d.name for d in hyp.damage_thresholds],
        "observables": list(hyp.observables),
        "status": CLAIM_STATUS,
        "evidence_class": EVIDENCE_CLASS,
        "hardware_status": HARDWARE_STATUS,
        "measured_here": MEASURED_HERE,
        "validation": VALIDATION,
        "the_firewall": (
            "a decaying, dispersing trace is exactly what ordinary "
            "material relaxation looks like; it is not a memory until "
            "ordered delayed readout is shown. See "
            "refuse_memory_claim_without_delayed_readout()."),
        "what_this_is": (
            "a typed hypothesis for a fading crystal shift register: an "
            "exact retention window, a decay-plus-dispersion fidelity "
            "model, a destructive read that forces a refresh, and a null "
            "that the decay curve cannot beat."),
        "what_this_does_not_say": (
            "it does not say any crystal stores information, that a "
            "retention window has been observed, or that any specimen "
            "has been written to or read. Every number is derived from "
            "supplied model parameters. Nothing has been measured, and "
            "the best status this can carry is BENCH_TEST_REQUIRED."),
    }


# convenience re-export used by build_hypothesis callers who tweak a reg
__all__ = [
    "CLAIM_STATUS", "CONTRACT_STATUSES", "EVIDENCE_CLASS", "HARDWARE_STATUS",
    "MEASURED_HERE", "VALIDATION", "DEFAULT_A0", "READ_THRESHOLD",
    "MemoryClaimRefused", "SchemaViolation",
    "retention_amplitude", "retention_window", "recoverable",
    "StoredBit", "ReadResult", "write_bit", "age_bit", "destructive_read",
    "refresh", "refresh_required",
    "ShiftRegister", "stage_fidelity", "last_readable_stage",
    "readable_stage_count",
    "memory_amplitude", "ordinary_relaxation_amplitude",
    "decay_curves_indistinguishable", "read_pattern_memory",
    "read_pattern_relaxation_null", "match_fraction",
    "ordered_readout_distinguishes", "null_model_report",
    "refuse_memory_claim_without_delayed_readout",
    "Control", "CONTROLS", "DamageThreshold", "DAMAGE_THRESHOLDS",
    "OBSERVABLES", "CrystalMemory", "build_hypothesis", "crystalmem_report",
]
