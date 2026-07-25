"""P25 — the DDS recipe compiler.

A direct-digital-synthesis (DDS) core turns one reference clock ``f_clk``
into an output tone by advancing a phase accumulator by a *frequency tuning
word* (FTW) each clock cycle. The synthesized frequency is set entirely by
that integer:

    ``FTW = round(f_out / f_clk * 2**N)``  and  ``f_out = FTW / 2**N * f_clk``

with ``N`` the accumulator width. A phase-offset word and an amplitude
(scale-factor) word finish the tuning, and a *ramp / chirp* is nothing but
an ordered sequence of FTW steps. This module compiles a frozen protocol or
a sweep / chirp specification into exactly that: a deterministic ordered
sequence of tuning words -- a **recipe** -- and it does so honestly.

**Three target kinds, and every approximation reports its error.** A target
frequency is *dyadic* (its ratio to the clock is ``m/2**j`` with ``j <= N``,
so the FTW is an exact integer and the quantization error is exactly zero),
*rational* (an exact :class:`~fractions.Fraction` ratio, exact only when the
denominator divides ``2**N``), or *approximate* (any real value, rounded to
the nearest FTW). Every step records both the *requested* and the *realized*
frequency and the residual, and :func:`verify_recipe` checks that every FTW
round-trips (``word -> frequency -> word`` is the identity) and that the
quantization error stays within one half-LSB tolerance.

**Device limits are enforced and out-of-range recipes are refused.** A
:class:`DDSDeviceSpec` carries the Nyquist limit (``f_clk/2``), the maximum
FTW (``2**N - 1``) and the phase / amplitude resolutions. A target at or
above Nyquist, a non-positive frequency, or an out-of-range amplitude is
refused with :class:`DDSDeviceLimitError`; nothing is quietly clamped.

**Multichannel closure can be broken by independent optimization.** Several
channels share one clock. When a set of phase offsets must close around a
loop (``sum of requested phases = 0 (mod 2*pi)``), rounding each channel's
phase word *independently* lets the rounding errors fail to cancel, so the
closure residual is non-zero; a *joint* optimization lets the last channel
absorb the residual and closes exactly. Both paths are compiled and the
contrast is the point.

**Four honest modes, and no promotion.** Behind the emitter sit the four
R15 device modes. ``REAL_DEVICE`` has no DDS hardware behind it, so emitting
a recipe to it acquires *nothing*: it raises :class:`NoDDSHardwareError` and
its receipt is ``PREREGISTERED_NOT_RUN``. ``SYNTHETIC_DEVICE`` renders the
recipe to a deterministic synthetic waveform (a ``SYNTHETIC_OBSERVATION``,
never a measurement). ``REPLAY_DEVICE`` replays a recorded synthetic render.
``FAULT_INJECTION_DEVICE`` injects the ordinary DDS pathologies (FTW
truncation, phase truncation, a dropped step, a word bit-flip, amplitude
clipping) so the quantization and fault budget can be exercised. A phase-
truncation *spur* is a ``KNOWN_ORDINARY_EFFECT`` of finite word length, not
a tone (:func:`refuse_spur_as_signal`).

**Freezing.** :func:`freeze_recipe` seals a recipe with a SHA-256 over its
canonical serialization (reusing :func:`r13.serialize.content_hash`, the one
canonicalisation authority). Any edit after the seal changes the hash, so
:func:`refuse_edit_after_seal` detects a post-seal edit and refuses to run
it under the old commitment.

Nothing here is measured. A compiled recipe is ``SOFTWARE_IMPLEMENTED``; a
rendered waveform is a ``SYNTHETIC_OBSERVATION``; running a recipe on real
DDS hardware is ``PREREGISTERED_NOT_RUN``. The strongest class this module
reaches is a synthetic observation, and :func:`refuse_recipe_as_measured`
blocks reading a compiled recipe or a rendered tone as a measured signal.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

import numpy as np

from r13 import serialize as r13_serialize
from r15 import claims

# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "DDS_RECIPE_COMPILER_SOFTWARE_NO_DDS_HARDWARE"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: A physical DDS run is preregistered, not run: no synthesizer hardware
#: exists in this repository.
PHYSICAL_RUN_STATUS = "PREREGISTERED_NOT_RUN"

#: Stamped on every recipe and rendered observation so a result is
#: reproducible and a change is visible.
ANALYSIS_VERSION = "dds_recipes-1"

#: A compiled recipe and the compiler machinery are software artifacts.
COMPILER_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED
RECIPE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED
#: A rendered waveform is a synthetic observation, never a measurement.
WAVEFORM_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION

#: The maximum rounding error of nearest-FTW quantization, in LSBs. A
#: rounded FTW is never more than half an FTW step from the request.
DEFAULT_FTW_TOLERANCE_LSB = 0.5


class DDSError(RuntimeError):
    """Base of every DDS recipe refusal or structural guard."""


class DDSDeviceLimitError(DDSError):
    """Raised when a target violates a device limit.

    A frequency at or above Nyquist, a non-positive frequency, an FTW past
    the accumulator maximum, or an out-of-range amplitude is refused here --
    the recipe is not quietly clamped to fit.
    """


class NoDDSHardwareError(DDSError):
    """Raised when a REAL_DEVICE emitter is asked to run a recipe.

    There is no DDS hardware in this repository, so emitting a recipe to a
    real device drives NOTHING. The run is BLOCKED at the hardware-access
    boundary and the physical run is PREREGISTERED_NOT_RUN.
    """


class RecipeSealError(DDSError):
    """Raised when an edited recipe is presented as a frozen one."""


# --- the four modes and the fault vocabulary -----------------------------

class DDSMode(Enum):
    """The four emission modes behind the one DDS interface."""

    REAL_DEVICE = "REAL_DEVICE"
    REPLAY_DEVICE = "REPLAY_DEVICE"
    SYNTHETIC_DEVICE = "SYNTHETIC_DEVICE"
    FAULT_INJECTION_DEVICE = "FAULT_INJECTION_DEVICE"


class DDSFaultMode(Enum):
    """The ordinary DDS pathologies a fault-injection emitter can inject.

    ``FTW_TRUNCATION`` and ``PHASE_TRUNCATION`` replace nearest-rounding
    with truncation (a larger, one-sided error and, for phase, a spur);
    ``DROPPED_STEP`` omits one recipe step; ``WORD_BITFLIP`` flips a bit in
    one tuning word; ``AMPLITUDE_CLIP`` clamps the scale-factor words.
    """

    FTW_TRUNCATION = "ftw_truncation"
    PHASE_TRUNCATION = "phase_truncation"
    DROPPED_STEP = "dropped_step"
    WORD_BITFLIP = "word_bitflip"
    AMPLITUDE_CLIP = "amplitude_clip"


class TargetKind(Enum):
    """How a frequency target was specified."""

    DYADIC = "DYADIC"            # ratio m/2**j, j <= N: exact FTW
    RATIONAL = "RATIONAL"        # exact Fraction ratio, exact iff 2**N/den
    APPROXIMATE = "APPROXIMATE"  # any real value, rounded to nearest FTW


# --- the device specification --------------------------------------------

@dataclass(frozen=True)
class DDSDeviceSpec:
    """The declared limits of a DDS core. Every field is a model number.

    ``f_clk`` is the reference clock (Hz); ``ftw_bits`` (``N``) the phase-
    accumulator width; ``phase_bits`` and ``amp_bits`` the phase-offset and
    amplitude word widths. The Nyquist limit, the maximum FTW and the phase
    / amplitude moduli follow from these.
    """

    f_clk: float
    ftw_bits: int = 32
    phase_bits: int = 14
    amp_bits: int = 12
    device_id: str = "dds_core"

    def __post_init__(self) -> None:
        if float(self.f_clk) <= 0.0 or not math.isfinite(float(self.f_clk)):
            raise DDSDeviceLimitError("the reference clock must be positive")
        for name in ("ftw_bits", "phase_bits", "amp_bits"):
            if int(getattr(self, name)) < 1:
                raise DDSDeviceLimitError(f"{name} must be at least 1")

    @property
    def ftw_modulus(self) -> int:
        """``2**N``: the phase-accumulator span."""
        return 1 << int(self.ftw_bits)

    @property
    def max_ftw(self) -> int:
        """``2**N - 1``: the largest representable tuning word."""
        return (1 << int(self.ftw_bits)) - 1

    @property
    def phase_modulus(self) -> int:
        return 1 << int(self.phase_bits)

    @property
    def amp_max(self) -> int:
        return (1 << int(self.amp_bits)) - 1

    @property
    def nyquist(self) -> float:
        """``f_clk / 2``: the highest output frequency a DDS can synthesize."""
        return 0.5 * float(self.f_clk)

    @property
    def freq_lsb(self) -> float:
        """The frequency resolution ``f_clk / 2**N`` -- one FTW step."""
        return float(self.f_clk) / float(self.ftw_modulus)

    def as_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "f_clk": float(self.f_clk),
            "ftw_bits": int(self.ftw_bits),
            "phase_bits": int(self.phase_bits),
            "amp_bits": int(self.amp_bits),
        }


# --- frequency targets ----------------------------------------------------

@dataclass(frozen=True)
class FrequencyTarget:
    """A requested output frequency, with its exact clock ratio if known.

    ``value_hz`` is the requested frequency; ``ratio`` is its exact ratio to
    the clock as a :class:`~fractions.Fraction` when the target is dyadic or
    rational, or ``None`` for a generic approximate target. Build one with
    :meth:`dyadic`, :meth:`rational` or :meth:`approximate` -- never claim a
    kind the ratio does not support.
    """

    value_hz: float
    kind: TargetKind
    ratio: Fraction | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.value_hz)):
            raise DDSDeviceLimitError("a target frequency must be finite")

    @classmethod
    def dyadic(cls, dev: DDSDeviceSpec, numerator: int, power: int,
               label: str = "") -> "FrequencyTarget":
        """A dyadic target ``f_clk * numerator / 2**power`` (``power <= N``).

        Its FTW is the exact integer ``numerator * 2**(N-power)``, so the
        quantization error is exactly zero.
        """
        if int(power) < 0:
            raise DDSDeviceLimitError("a dyadic power must be non-negative")
        if int(power) > int(dev.ftw_bits):
            raise DDSDeviceLimitError(
                f"a dyadic target with power {power} exceeds the {dev.ftw_bits}"
                f"-bit accumulator and is not exactly representable")
        ratio = Fraction(int(numerator), 1 << int(power))
        return cls(value_hz=float(dev.f_clk) * float(ratio),
                   kind=TargetKind.DYADIC, ratio=ratio, label=label)

    @classmethod
    def rational(cls, dev: DDSDeviceSpec, numerator: int, denominator: int,
                 label: str = "") -> "FrequencyTarget":
        """A rational target ``f_clk * numerator / denominator``.

        Exact only when the reduced denominator divides ``2**N``; otherwise
        the FTW is rounded and the step reports the residual.
        """
        ratio = Fraction(int(numerator), int(denominator))
        return cls(value_hz=float(dev.f_clk) * float(ratio),
                   kind=TargetKind.RATIONAL, ratio=ratio, label=label)

    @classmethod
    def approximate(cls, value_hz: float,
                    label: str = "") -> "FrequencyTarget":
        """A generic real target, rounded to the nearest FTW."""
        return cls(value_hz=float(value_hz), kind=TargetKind.APPROXIMATE,
                   ratio=None, label=label)


# --- word <-> quantity conversions ---------------------------------------

def _round_half_up(fr: Fraction) -> int:
    """Round a non-negative :class:`Fraction` to the nearest integer.

    Half rounds up. Exact for exact ratios (no float intermediary), so a
    dyadic ratio lands on its exact integer FTW.
    """
    num, den = fr.numerator, fr.denominator
    q, r = divmod(num, den)
    if 2 * r >= den:
        q += 1
    return q


def frequency_to_ftw(target: FrequencyTarget, dev: DDSDeviceSpec) -> int:
    """The frequency tuning word for a target: ``round(f/f_clk * 2**N)``.

    Uses the exact rational ratio when the target carries one (so a dyadic
    target yields its exact integer FTW), else rounds the real ratio. The
    result is range-checked against Nyquist and the accumulator maximum.
    """
    value = float(target.value_hz)
    if value <= 0.0:
        raise DDSDeviceLimitError(
            f"refused: a DDS synthesizes a positive tone; the target "
            f"{value:g} Hz is not positive. {VERDICT}")
    if value >= dev.nyquist:
        raise DDSDeviceLimitError(
            f"refused: the target {value:g} Hz is at or above the Nyquist "
            f"limit {dev.nyquist:g} Hz (f_clk/2 = {dev.f_clk:g}/2). A DDS "
            f"cannot synthesize a tone at or above half its clock; the "
            f"recipe is out of range and is not clamped. {VERDICT}")
    if target.ratio is not None:
        ftw = _round_half_up(target.ratio * dev.ftw_modulus)
    else:
        ftw = int(round(value / float(dev.f_clk) * dev.ftw_modulus))
    if ftw < 1:
        raise DDSDeviceLimitError(
            f"the target {value:g} Hz rounds to FTW 0 below the frequency "
            f"resolution {dev.freq_lsb:g} Hz")
    if ftw > dev.max_ftw:
        raise DDSDeviceLimitError(
            f"FTW {ftw} exceeds the accumulator maximum {dev.max_ftw} "
            f"(2**{dev.ftw_bits} - 1); target out of range")
    return int(ftw)


def ftw_to_frequency(ftw: int, dev: DDSDeviceSpec) -> float:
    """The synthesized frequency of a tuning word: ``FTW/2**N * f_clk``."""
    return float(ftw) / float(dev.ftw_modulus) * float(dev.f_clk)


def phase_to_word(phase_rad: float, dev: DDSDeviceSpec) -> int:
    """The phase-offset word ``round(phase/(2*pi) * 2**P) mod 2**P``."""
    modulus = dev.phase_modulus
    return int(round(float(phase_rad) / (2.0 * math.pi) * modulus)) % modulus


def word_to_phase(word: int, dev: DDSDeviceSpec) -> float:
    """The phase (radians in ``[0, 2*pi)``) of a phase-offset word."""
    return float(word) / float(dev.phase_modulus) * 2.0 * math.pi


def amplitude_to_word(amplitude: float, dev: DDSDeviceSpec) -> int:
    """The scale-factor word ``round(amplitude * (2**A - 1))``.

    Amplitude is a normalized fraction in ``[0, 1]``; anything outside is a
    device-limit violation, not silently clipped.
    """
    a = float(amplitude)
    if a < 0.0 or a > 1.0:
        raise DDSDeviceLimitError(
            f"a normalized amplitude must lie in [0, 1]; {a:g} is out of "
            f"range")
    return int(round(a * dev.amp_max))


# --- a compiled recipe step ----------------------------------------------

@dataclass(frozen=True)
class RecipeStep:
    """One compiled tuning point: the words, and the requested vs realized
    frequency with its quantization residual.

    ``quantization_error`` is ``realized_frequency - requested_frequency``
    in Hz; it is exactly zero for a dyadic target and bounded by half an
    FTW step otherwise.
    """

    index: int
    ftw: int
    phase_word: int
    amp_word: int
    requested_frequency: float
    realized_frequency: float
    quantization_error: float
    kind: TargetKind
    duration_samples: int = 0
    label: str = ""

    @property
    def is_exact(self) -> bool:
        return self.quantization_error == 0.0

    def as_dict(self) -> dict:
        return {
            "index": int(self.index),
            "ftw": int(self.ftw),
            "phase_word": int(self.phase_word),
            "amp_word": int(self.amp_word),
            "requested_frequency": float(self.requested_frequency),
            "realized_frequency": float(self.realized_frequency),
            "quantization_error": float(self.quantization_error),
            "kind": self.kind.value,
            "duration_samples": int(self.duration_samples),
            "label": self.label,
        }


def compile_step(target: FrequencyTarget, dev: DDSDeviceSpec, index: int = 0,
                 phase_rad: float = 0.0, amplitude: float = 1.0,
                 duration_samples: int = 0) -> RecipeStep:
    """Compile one frequency target into a :class:`RecipeStep`.

    Records both the requested and the realized frequency and their residual
    -- an approximate target always reports a non-zero error, a dyadic
    target reports exactly zero.
    """
    ftw = frequency_to_ftw(target, dev)
    realized = ftw_to_frequency(ftw, dev)
    return RecipeStep(
        index=int(index),
        ftw=ftw,
        phase_word=phase_to_word(phase_rad, dev),
        amp_word=amplitude_to_word(amplitude, dev),
        requested_frequency=float(target.value_hz),
        realized_frequency=float(realized),
        quantization_error=float(realized - float(target.value_hz)),
        kind=target.kind,
        duration_samples=int(duration_samples),
        label=target.label,
    )


# --- a compiled recipe ----------------------------------------------------

@dataclass(frozen=True)
class DDSRecipe:
    """A deterministic ordered sequence of DDS tuning words.

    ``steps`` are the compiled tuning points in order; ``channel`` names the
    synthesizer channel; ``protocol_seal`` optionally carries the seal of
    the frozen R15 protocol this recipe implements, binding the recipe to
    its plan. A recipe is a ``SOFTWARE_IMPLEMENTED`` artifact -- it commands
    nothing until emitted, and emitting it to real hardware is
    PREREGISTERED_NOT_RUN.
    """

    recipe_id: str
    device: DDSDeviceSpec
    steps: tuple
    channel: int = 0
    protocol_seal: str | None = None

    def __post_init__(self) -> None:
        if not str(self.recipe_id).strip():
            raise DDSError("a recipe needs a non-empty recipe_id")
        if not self.steps:
            raise DDSError("a recipe with no steps compiles to nothing")
        for i, s in enumerate(self.steps):
            if not isinstance(s, RecipeStep):
                raise DDSError("every recipe step must be a RecipeStep")
            if s.index != i:
                raise DDSError(
                    f"step indices must be 0..n-1 in order; position {i} "
                    f"carries index {s.index}")

    def max_quantization_error(self) -> float:
        return max(abs(s.quantization_error) for s in self.steps)

    def rms_quantization_error(self) -> float:
        errs = np.array([s.quantization_error for s in self.steps], dtype=float)
        return float(np.sqrt(np.mean(errs * errs)))

    def to_record(self) -> dict:
        """The canonical record the seal is taken over."""
        return {
            "recipe_id": self.recipe_id,
            "analysis_version": ANALYSIS_VERSION,
            "device": self.device.as_dict(),
            "channel": int(self.channel),
            "protocol_seal": self.protocol_seal,
            "steps": [s.as_dict() for s in self.steps],
            "claim_class": RECIPE_CLAIM_CLASS.value,
        }

    def seal(self) -> str:
        """The SHA-256 seal over the canonical record (R13 authority)."""
        return r13_serialize.content_hash(self.to_record())

    def command_plan(self) -> list:
        """The register-write command plan: an ordered list of word writes.

        Each entry is a device-neutral register write (FTW, phase, amplitude
        per step). It commands nothing here; it is the plan an emitter would
        stream to a real core. Deterministic in the recipe.
        """
        plan: list = []
        for s in self.steps:
            plan.append({"channel": int(self.channel), "step": s.index,
                         "register": "FTW", "word": s.ftw})
            plan.append({"channel": int(self.channel), "step": s.index,
                         "register": "PHASE", "word": s.phase_word})
            plan.append({"channel": int(self.channel), "step": s.index,
                         "register": "AMP", "word": s.amp_word})
        return plan


# --- the compilers --------------------------------------------------------

def compile_targets(targets, dev: DDSDeviceSpec, recipe_id: str,
                    channel: int = 0, phase_rad: float = 0.0,
                    amplitude: float = 1.0,
                    protocol_seal: str | None = None) -> DDSRecipe:
    """Compile an ordered iterable of :class:`FrequencyTarget` into a recipe."""
    steps = tuple(
        compile_step(t, dev, index=i, phase_rad=phase_rad, amplitude=amplitude)
        for i, t in enumerate(targets))
    return DDSRecipe(recipe_id=recipe_id, device=dev, steps=steps,
                     channel=int(channel), protocol_seal=protocol_seal)


def compile_sweep(dev: DDSDeviceSpec, f_start: float, f_stop: float,
                  n_points: int, recipe_id: str = "sweep",
                  channel: int = 0, amplitude: float = 1.0,
                  protocol_seal: str | None = None) -> DDSRecipe:
    """Compile a linear frequency sweep into a recipe of approximate targets.

    ``n_points`` frequencies are placed inclusively from ``f_start`` to
    ``f_stop``; each is compiled to its nearest FTW and reports its residual.
    """
    if int(n_points) < 1:
        raise DDSError("a sweep needs at least one point")
    if int(n_points) == 1:
        grid = [float(f_start)]
    else:
        grid = list(np.linspace(float(f_start), float(f_stop),
                                int(n_points)))
    targets = [FrequencyTarget.approximate(f, label=f"sweep[{i}]")
               for i, f in enumerate(grid)]
    return compile_targets(targets, dev, recipe_id, channel=channel,
                           amplitude=amplitude, protocol_seal=protocol_seal)


def compile_chirp(dev: DDSDeviceSpec, f_start: float, f_stop: float,
                  n_steps: int, samples_per_step: int = 1,
                  recipe_id: str = "chirp", channel: int = 0,
                  amplitude: float = 1.0) -> DDSRecipe:
    """Compile a linear FTW ramp (chirp) into equally-spaced tuning words.

    The FTW is stepped linearly from the start to the stop word; each step
    holds for ``samples_per_step`` clock cycles. A chirp is exactly an
    ordered sequence of FTW steps, which is what this returns.
    """
    if int(n_steps) < 2:
        raise DDSError("a chirp needs at least two steps")
    ftw_start = frequency_to_ftw(FrequencyTarget.approximate(f_start), dev)
    ftw_stop = frequency_to_ftw(FrequencyTarget.approximate(f_stop), dev)
    ftw_grid = np.linspace(ftw_start, ftw_stop, int(n_steps))
    steps = []
    for i, ftw_f in enumerate(ftw_grid):
        ftw = int(round(ftw_f))
        if ftw < 1 or ftw > dev.max_ftw:
            raise DDSDeviceLimitError(
                f"chirp step {i} FTW {ftw} is out of range")
        realized = ftw_to_frequency(ftw, dev)
        # the requested frequency for a ramp step is the ideal linear value
        requested = ftw_to_frequency(float(ftw_f), dev)
        steps.append(RecipeStep(
            index=i, ftw=ftw, phase_word=0,
            amp_word=amplitude_to_word(amplitude, dev),
            requested_frequency=float(requested),
            realized_frequency=float(realized),
            quantization_error=float(realized - requested),
            kind=TargetKind.APPROXIMATE,
            duration_samples=int(samples_per_step),
            label=f"chirp[{i}]"))
    return DDSRecipe(recipe_id=recipe_id, device=dev, steps=tuple(steps),
                     channel=int(channel))


def compile_protocol_sweep(sealed, dev: DDSDeviceSpec,
                           recipe_id: str = "protocol_sweep",
                           channel: int = 0) -> DDSRecipe:
    """Compile the SWEEP acquisition of a frozen R15 protocol into a recipe.

    ``sealed`` is an ``r15.protocols.SealedProtocol`` (or a bare
    ``Protocol``). The first ``ACQUIRE`` step carrying a ``SWEEP`` maneuver
    supplies ``f_start``, ``f_stop`` and ``points`` from its setpoints; the
    recipe records the protocol seal so it is bound to its frozen plan. This
    reuses the P07 protocol engine rather than restating a plan format.
    """
    protocol = getattr(sealed, "protocol", sealed)
    seal = getattr(sealed, "seal", None)
    sweep_step = None
    for step in protocol.steps:
        maneuver = getattr(step, "maneuver", None)
        if maneuver is not None and getattr(maneuver, "value", "") == "SWEEP":
            sweep_step = step
            break
    if sweep_step is None:
        raise DDSError(
            "the protocol carries no ACQUIRE SWEEP step to compile into a "
            "DDS recipe")
    setpoints = {sp.name: float(sp.value) for sp in sweep_step.setpoints}
    for name in ("f_start", "f_stop", "points"):
        if name not in setpoints:
            raise DDSError(
                f"the SWEEP step is missing the {name!r} setpoint")
    return compile_sweep(dev, setpoints["f_start"], setpoints["f_stop"],
                         int(round(setpoints["points"])), recipe_id=recipe_id,
                         channel=channel, protocol_seal=seal)


# --- verification: round-trip and quantization tolerance -----------------

def verify_recipe(recipe: DDSRecipe,
                  tolerance_lsb: float = DEFAULT_FTW_TOLERANCE_LSB) -> dict:
    """Verify every FTW round-trips and every residual is within tolerance.

    The round-trip check is ``ftw -> frequency -> ftw`` (recomputing the FTW
    from the realized frequency must return the same word). The tolerance
    check is ``|quantization_error| <= tolerance_lsb * freq_lsb`` -- half an
    FTW step by default, the maximum a nearest-rounding can incur.
    """
    dev = recipe.device
    lsb = dev.freq_lsb
    bound = float(tolerance_lsb) * lsb + 1e-9 * lsb
    roundtrips = True
    within = True
    worst = 0.0
    for s in recipe.steps:
        back = int(round(s.realized_frequency / float(dev.f_clk) *
                         dev.ftw_modulus))
        if back != s.ftw:
            roundtrips = False
        err = abs(s.quantization_error)
        worst = max(worst, err)
        if err > bound:
            within = False
    return {
        "recipe_id": recipe.recipe_id,
        "n_steps": len(recipe.steps),
        "all_ftw_roundtrip": bool(roundtrips),
        "within_tolerance": bool(within),
        "tolerance_lsb": float(tolerance_lsb),
        "freq_lsb": float(lsb),
        "worst_quantization_error": float(worst),
        "max_quantization_error": recipe.max_quantization_error(),
        "rms_quantization_error": recipe.rms_quantization_error(),
        "claim_class": RECIPE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- multichannel phase closure ------------------------------------------

def _wrap_signed(value: int, modulus: int) -> int:
    """Map an integer into ``(-modulus/2, modulus/2]`` (signed residue)."""
    r = int(value) % int(modulus)
    if r > modulus // 2:
        r -= modulus
    return r


def compile_multichannel_phases(requested_phases, dev: DDSDeviceSpec,
                                joint: bool = True) -> dict:
    """Compile per-channel phase words for a set that must close around a loop.

    ``requested_phases`` are the per-channel phase offsets (radians) of a
    loop that ideally closes (``sum = 0 (mod 2*pi)``). With ``joint=True``
    the last channel's word absorbs the accumulated rounding residual so the
    loop closes *exactly*; with ``joint=False`` each channel is rounded
    independently and the residual need not vanish. Returns the words and the
    signed closure residual (in phase-LSBs).
    """
    phases = [float(p) for p in requested_phases]
    if len(phases) < 2:
        raise DDSError("closure needs at least two channels")
    modulus = dev.phase_modulus
    words = [phase_to_word(p, dev) for p in phases]
    if joint:
        # the last channel closes the loop exactly: it is set to the residue
        # that makes the total sum vanish modulo the phase span.
        head = sum(words[:-1]) % modulus
        words[-1] = (-head) % modulus
    residual = _wrap_signed(sum(words), modulus)
    return {
        "requested_phases": phases,
        "phase_words": [int(w) for w in words],
        "realized_phases": [word_to_phase(w, dev) for w in words],
        "closure_residual_lsb": int(residual),
        "closes": bool(residual == 0),
        "mode": "joint" if joint else "independent",
        "claim_class": RECIPE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
    }


def phase_closure_residual(phase_words, dev: DDSDeviceSpec) -> int:
    """The signed phase-closure residual (in LSBs) of a set of phase words."""
    return _wrap_signed(sum(int(w) for w in phase_words), dev.phase_modulus)


# --- freezing: seal and detect edits -------------------------------------

@dataclass(frozen=True)
class SealedRecipe:
    """A recipe frozen at an explicit epoch, plus its seal.

    :meth:`verify` recomputes the seal from the carried recipe and compares:
    the frozen recipe matches; an edited one does not. ``sealed_epoch`` is
    passed in, never read from a clock, so freezing is deterministic.
    """

    recipe: DDSRecipe
    seal: str
    sealed_epoch: int

    def verify(self) -> bool:
        return self.recipe.seal() == self.seal


def freeze_recipe(recipe: DDSRecipe, *, epoch: int) -> SealedRecipe:
    """Seal a recipe before emission; the seal fingerprints the whole plan."""
    return SealedRecipe(recipe=recipe, seal=recipe.seal(),
                        sealed_epoch=int(epoch))


def refuse_edit_after_seal(sealed: SealedRecipe,
                           proposed: DDSRecipe) -> dict:
    """Refuse to present an edited recipe as the frozen one. Raises on edit.

    A recipe is frozen and its seal published. If a tuning word, a step or
    the device is changed and the plan re-presented as the sealed one, the
    edit is detectable: the proposed recipe hashes differently. The edit is
    legal as a NEW recipe under its own seal, and forbidden as a silent
    replacement of the frozen commitment.
    """
    if not isinstance(sealed, SealedRecipe):
        raise DDSError("first argument must be a SealedRecipe")
    if not isinstance(proposed, DDSRecipe):
        raise DDSError("second argument must be a DDSRecipe")
    proposed_seal = proposed.seal()
    if proposed_seal != sealed.seal:
        raise RecipeSealError(
            f"refused: this recipe differs from the frozen one and may not "
            f"be emitted under it. The frozen seal is {sealed.seal}; the "
            f"proposed recipe hashes to {proposed_seal}. A recipe edited "
            f"after sealing is a new recipe and must be frozen afresh under "
            f"its own seal, not run under the previous commitment. {VERDICT}")
    return {"seal": sealed.seal, "proposed_seal": proposed_seal,
            "identical": True}


# --- rendering a recipe to a synthetic waveform --------------------------

@dataclass(frozen=True)
class RenderedWaveform:
    """A deterministic synthetic render of a recipe.

    ``samples`` is the concatenated tone the recipe would drive, sampled at
    ``f_clk``; it is a ``SYNTHETIC_OBSERVATION`` capped below any measurement
    class -- a simulator output, never an instrument reading.
    """

    mode: DDSMode
    samples: np.ndarray
    fs: float
    recipe_id: str
    claim_class: claims.ClaimClass = WAVEFORM_CLAIM_CLASS
    faults: tuple = ()

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            claims.refuse_synthetic_as_physical()

    def digest(self) -> str:
        a = np.ascontiguousarray(self.samples, dtype=float).tobytes()
        return hashlib.sha256(a).hexdigest()


def render_waveform(recipe: DDSRecipe, samples_per_step: int = 64,
                    mode: DDSMode = DDSMode.SYNTHETIC_DEVICE
                    ) -> RenderedWaveform:
    """Render a recipe to a deterministic synthetic waveform (no hardware).

    Each step contributes ``max(step.duration_samples, samples_per_step)``
    samples of ``cos(2*pi * realized_freq * t + phase)`` with continuous
    phase accumulation across steps, at ``f_clk``. Same recipe => identical
    samples. The result is a ``SYNTHETIC_OBSERVATION``.
    """
    dev = recipe.device
    fs = float(dev.f_clk)
    chunks = []
    running_phase = 0.0
    dt = 1.0 / fs
    for s in recipe.steps:
        n = max(int(s.duration_samples), int(samples_per_step))
        if n < 1:
            n = 1
        k = np.arange(n, dtype=float)
        w = 2.0 * math.pi * float(s.realized_frequency)
        offset = word_to_phase(s.phase_word, dev)
        amp = float(s.amp_word) / float(dev.amp_max) if dev.amp_max else 1.0
        chunk = amp * np.cos(w * (k * dt) + running_phase + offset)
        running_phase = (running_phase + w * (n * dt)) % (2.0 * math.pi)
        chunks.append(chunk)
    samples = np.concatenate(chunks) if chunks else np.zeros(0)
    return RenderedWaveform(mode=mode, samples=samples, fs=fs,
                            recipe_id=recipe.recipe_id)


# --- the four emission modes ---------------------------------------------

class DDSEmitter:
    """Base of the one DDS emission interface. Not used directly."""

    mode: DDSMode

    def emit(self, recipe: DDSRecipe) -> RenderedWaveform:
        raise NotImplementedError


class RealDDSEmitter(DDSEmitter):
    """A real DDS interface with no synthesizer hardware behind it.

    Emitting a recipe drives NOTHING: it raises :class:`NoDDSHardwareError`.
    :meth:`blocked_receipt` records the honest PREREGISTERED_NOT_RUN state.
    """

    mode = DDSMode.REAL_DEVICE

    def __init__(self, device_id: str = "real_dds") -> None:
        self.device_id = str(device_id)

    def emit(self, recipe: DDSRecipe) -> RenderedWaveform:
        raise NoDDSHardwareError(
            f"refused: {self.device_id} is a REAL_DEVICE DDS and no "
            f"synthesizer hardware (DDS core, DAC, reconstruction filter, "
            f"reference clock) exists in this repository, so emitting the "
            f"recipe drives NOTHING. The run is BLOCKED at the hardware-"
            f"access boundary. A physical DDS run is {PHYSICAL_RUN_STATUS}. "
            f"{PHYSICAL_VALIDATION}. {VERDICT}")

    def blocked_receipt(self) -> dict:
        return {
            "device_id": self.device_id,
            "mode": self.mode.value,
            "status": "BLOCKED",
            "physical_run": PHYSICAL_RUN_STATUS,
            "reason": ("no DDS hardware present; a recipe emission drives "
                       "nothing. The physical DDS protocol is preregistered "
                       "but not run"),
            "emitted": False,
            "claim_class": "BLOCKED_MISSING_INPUT",
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class SyntheticDDSEmitter(DDSEmitter):
    """Renders a recipe to a deterministic synthetic waveform."""

    mode = DDSMode.SYNTHETIC_DEVICE

    def __init__(self, samples_per_step: int = 64) -> None:
        self.samples_per_step = int(samples_per_step)

    def emit(self, recipe: DDSRecipe) -> RenderedWaveform:
        return render_waveform(recipe, self.samples_per_step,
                               mode=DDSMode.SYNTHETIC_DEVICE)


class ReplayDDSEmitter(DDSEmitter):
    """Replays a previously recorded synthetic render byte-for-byte."""

    mode = DDSMode.REPLAY_DEVICE

    def __init__(self, recorded: RenderedWaveform) -> None:
        if not isinstance(recorded, RenderedWaveform):
            raise DDSError("a replay emitter needs a recorded RenderedWaveform")
        self._recorded = recorded

    def emit(self, recipe: DDSRecipe) -> RenderedWaveform:
        r = self._recorded
        return RenderedWaveform(
            mode=DDSMode.REPLAY_DEVICE,
            samples=np.asarray(r.samples, dtype=float).copy(),
            fs=r.fs, recipe_id=r.recipe_id, faults=r.faults)


class FaultInjectionDDSEmitter(DDSEmitter):
    """Renders a recipe with an ordinary DDS pathology injected.

    Each fault deterministically alters the recipe's words or the rendered
    waveform relative to the clean synthetic render, so the quantization and
    fault budget can be exercised against a known fault.
    """

    mode = DDSMode.FAULT_INJECTION_DEVICE

    def __init__(self, faults, samples_per_step: int = 64,
                 config=None) -> None:
        faults = tuple(faults)
        if not faults:
            raise DDSError(
                "a fault-injection emitter with no faults injects nothing; "
                "supply at least one DDSFaultMode")
        for f in faults:
            if not isinstance(f, DDSFaultMode):
                raise DDSError(f"{f!r} is not a DDSFaultMode")
        self.faults = faults
        self.samples_per_step = int(samples_per_step)
        self.config = dict(config or {})

    def _faulted_steps(self, recipe: DDSRecipe) -> tuple:
        dev = recipe.device
        steps = list(recipe.steps)
        for f in self.faults:
            if f is DDSFaultMode.FTW_TRUNCATION:
                # truncate the FTW toward zero instead of rounding: a larger,
                # one-sided quantization error.
                new = []
                for s in steps:
                    exact = s.requested_frequency / float(dev.f_clk) * \
                        dev.ftw_modulus
                    ftw = max(1, int(math.floor(exact)))
                    realized = ftw_to_frequency(ftw, dev)
                    new.append(RecipeStep(
                        s.index, ftw, s.phase_word, s.amp_word,
                        s.requested_frequency, realized,
                        realized - s.requested_frequency, s.kind,
                        s.duration_samples, s.label))
                steps = new
            elif f is DDSFaultMode.PHASE_TRUNCATION:
                bits = int(self.config.get("phase_trunc_bits", 4))
                mask = ~((1 << bits) - 1)
                steps = [RecipeStep(
                    s.index, s.ftw, s.phase_word & mask, s.amp_word,
                    s.requested_frequency, s.realized_frequency,
                    s.quantization_error, s.kind, s.duration_samples, s.label)
                    for s in steps]
            elif f is DDSFaultMode.DROPPED_STEP:
                if len(steps) > 1:
                    steps = steps[:-1]
            elif f is DDSFaultMode.WORD_BITFLIP:
                bit = int(self.config.get("bitflip_bit", 3))
                s0 = steps[0]
                steps[0] = RecipeStep(
                    s0.index, s0.ftw ^ (1 << bit), s0.phase_word, s0.amp_word,
                    s0.requested_frequency,
                    ftw_to_frequency(s0.ftw ^ (1 << bit), dev),
                    ftw_to_frequency(s0.ftw ^ (1 << bit), dev) -
                    s0.requested_frequency,
                    s0.kind, s0.duration_samples, s0.label)
            elif f is DDSFaultMode.AMPLITUDE_CLIP:
                rail = int(round(float(self.config.get("clip_fraction", 0.5))
                                 * dev.amp_max))
                steps = [RecipeStep(
                    s.index, s.ftw, s.phase_word, min(s.amp_word, rail),
                    s.requested_frequency, s.realized_frequency,
                    s.quantization_error, s.kind, s.duration_samples, s.label)
                    for s in steps]
        # reindex so the faulted recipe is still well-formed
        return tuple(RecipeStep(
            i, s.ftw, s.phase_word, s.amp_word, s.requested_frequency,
            s.realized_frequency, s.quantization_error, s.kind,
            s.duration_samples, s.label) for i, s in enumerate(steps))

    def faulted_recipe(self, recipe: DDSRecipe) -> DDSRecipe:
        return DDSRecipe(recipe_id=recipe.recipe_id + "+fault",
                         device=recipe.device,
                         steps=self._faulted_steps(recipe),
                         channel=recipe.channel)

    def emit(self, recipe: DDSRecipe) -> RenderedWaveform:
        faulted = self.faulted_recipe(recipe)
        rendered = render_waveform(faulted, self.samples_per_step,
                                   mode=DDSMode.FAULT_INJECTION_DEVICE)
        return RenderedWaveform(
            mode=DDSMode.FAULT_INJECTION_DEVICE, samples=rendered.samples,
            fs=rendered.fs, recipe_id=recipe.recipe_id, faults=self.faults)


# --- quantization / fault analysis ---------------------------------------

def quantization_report(recipe: DDSRecipe,
                        tolerance_lsb: float = DEFAULT_FTW_TOLERANCE_LSB
                        ) -> dict:
    """A quantization budget over a recipe: per-kind exactness and residuals.

    Reports how many steps are exact (dyadic), the worst and RMS residual,
    the residual as a fraction of one FTW LSB, and whether every step is
    within tolerance -- the fault-and-quantization analysis the phase prompt
    requires.
    """
    dev = recipe.device
    lsb = dev.freq_lsb
    per_kind: dict = {}
    n_exact = 0
    for s in recipe.steps:
        per_kind.setdefault(s.kind.value, 0)
        per_kind[s.kind.value] += 1
        if s.is_exact:
            n_exact += 1
    verify = verify_recipe(recipe, tolerance_lsb)
    return {
        "recipe_id": recipe.recipe_id,
        "n_steps": len(recipe.steps),
        "n_exact_steps": n_exact,
        "per_kind": per_kind,
        "freq_lsb": float(lsb),
        "max_quantization_error": recipe.max_quantization_error(),
        "rms_quantization_error": recipe.rms_quantization_error(),
        "max_error_in_lsb": (recipe.max_quantization_error() / lsb
                             if lsb > 0 else float("inf")),
        "within_tolerance": verify["within_tolerance"],
        "all_ftw_roundtrip": verify["all_ftw_roundtrip"],
        "analysis_version": ANALYSIS_VERSION,
        "claim_class": RECIPE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- a schema-shaped observation for a rendered tone ---------------------

def waveform_observation(rendered: RenderedWaveform, recipe: DDSRecipe,
                         observation_id: str = "obs_dds_render-1") -> dict:
    """A rendered-tone record matching ``observation_record.schema.json``.

    The value is the recipe's realized first-step frequency, capped at
    ``SYNTHETIC_OBSERVATION``: a synthetic render of a recipe, not a measured
    tone. The uncertainty carries the recipe's worst quantization residual.
    """
    first = recipe.steps[0]
    return {
        "observation_id": observation_id,
        "run_id": recipe.recipe_id,
        "source_artifacts": ["dds_recipe", rendered.digest()],
        "analysis_version": ANALYSIS_VERSION,
        "quantity": "realized_frequency",
        "value": float(first.realized_frequency),
        "units": "Hz",
        "uncertainty": {"type": "quantization",
                        "half_width": float(recipe.max_quantization_error()),
                        "k": 1.0},
        "claim_class": WAVEFORM_CLAIM_CLASS.value,
        "derivation_graph": ["compile_step", "render_waveform"],
    }


# --- the load-bearing refusals -------------------------------------------

def refuse_recipe_as_measured(
        claim: str = "this compiled DDS recipe is a measured signal") -> None:
    """Refuse reading a compiled recipe or render as a measurement. Raises.

    A recipe is an ordered list of tuning words computed from a declared
    clock and target; a render is a simulator output. Neither is a photon,
    a voltage, or any instrument reading of a specimen. Delegates to the
    governance core's model-to-measurement refusal for the canonical text.
    """
    try:
        claims.refuse_model_as_measurement()
    except claims.ClaimError as exc:
        raise DDSError(
            f"refused: {claim!r}. A compiled DDS recipe is a "
            f"SOFTWARE_IMPLEMENTED sequence of tuning words and a rendered "
            f"tone is a SYNTHETIC_OBSERVATION; no synthesizer was operated "
            f"and nothing was acquired. {exc} A physical DDS run is "
            f"{PHYSICAL_RUN_STATUS}. {PHYSICAL_VALIDATION}. {VERDICT}") \
            from exc


def refuse_spur_as_signal(
        claim: str = "a phase-truncation spur is a tone") -> None:
    """Refuse reading a phase-truncation spur as a real tone. Raises.

    Finite phase-word length scatters energy into deterministic spurs at
    predictable offsets -- a ``KNOWN_ORDINARY_EFFECT`` of the DDS, not a
    signal, line or resonance. Delegates to the noise-to-resonance refusal.
    """
    try:
        claims.refuse_noise_as_resonance()
    except claims.ClaimError as exc:
        raise DDSError(
            f"refused: {claim!r}. A DDS phase-truncation spur is a "
            f"KNOWN_ORDINARY_EFFECT of finite word length -- a deterministic "
            f"artifact at a predictable offset -- not a new tone or "
            f"resonance. {exc} {VERDICT}") from exc


# --- report ---------------------------------------------------------------

def _example_device() -> DDSDeviceSpec:
    return DDSDeviceSpec(f_clk=100.0e6, ftw_bits=32, phase_bits=14,
                         amp_bits=12)


def dds_recipes_report() -> dict:
    """The standing statement of what this compiler is and is not."""
    dev = _example_device()
    dyadic = FrequencyTarget.dyadic(dev, 1, 2)          # f_clk/4, exact
    approx = FrequencyTarget.approximate(1_234_567.0)   # generic, rounded
    recipe = compile_targets([dyadic, approx], dev, "report_recipe")
    verify = verify_recipe(recipe)
    joint = compile_multichannel_phases(
        [2 * math.pi / 3, 2 * math.pi / 3, 2 * math.pi / 3], dev, joint=True)
    indep = compile_multichannel_phases(
        [2 * math.pi / 3, 2 * math.pi / 3, 2 * math.pi / 3], dev, joint=False)
    return {
        "what_this_is": (
            "a DDS recipe compiler: it compiles a frozen protocol or a "
            "sweep / chirp specification into a deterministic ordered "
            "sequence of tuning words (FTW = round(f_out/f_clk*2**N), phase "
            "and amplitude words, ramp steps), records requested vs realized "
            "values, verifies FTW round-trips and quantization tolerance, "
            "enforces device limits (Nyquist, max FTW, resolution), jointly "
            "optimizes multichannel phase closure, renders synthetic "
            "waveforms and command plans, and injects fault modes -- behind "
            "one interface with four modes"),
        "ftw_relation": "FTW = round(f_out / f_clk * 2**N)",
        "modes": [m.value for m in DDSMode],
        "fault_modes": [f.value for f in DDSFaultMode],
        "target_kinds": [k.value for k in TargetKind],
        "reuses": ["r13.serialize (canonical seal, content_hash)",
                   "r15.protocols (frozen protocol SWEEP setpoints)",
                   "r15.claims (taxonomy and refusals)"],
        "example_dyadic_exact": recipe.steps[0].is_exact,
        "example_approx_reports_error": recipe.steps[1].quantization_error != 0,
        "example_all_roundtrip": verify["all_ftw_roundtrip"],
        "example_within_tolerance": verify["within_tolerance"],
        "joint_closure_residual_lsb": joint["closure_residual_lsb"],
        "independent_closure_residual_lsb": indep["closure_residual_lsb"],
        "independent_can_break_closure": (indep["closure_residual_lsb"] != 0
                                          and joint["closure_residual_lsb"]
                                          == 0),
        "refusals": [
            "refuse_edit_after_seal (a post-seal edit is detected)",
            "refuse_recipe_as_measured (a recipe/render is not measured)",
            "refuse_spur_as_signal (a phase-truncation spur is not a tone)",
            "DDSDeviceLimitError on out-of-Nyquist / out-of-range targets",
            "RealDDSEmitter.emit raises NoDDSHardwareError (drives nothing)",
        ],
        "recipe_claim_class": RECIPE_CLAIM_CLASS.value,
        "waveform_claim_class": WAVEFORM_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "claim_class": COMPILER_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "physical_run": PHYSICAL_RUN_STATUS,
        "hardware_status": (
            "no DDS hardware exists here; a REAL_DEVICE emission is BLOCKED "
            "and the physical DDS run is PREREGISTERED_NOT_RUN"),
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any tone was synthesized on hardware or "
            "measured. Every tuning word is computed from a declared clock "
            "and target; a compiled recipe is SOFTWARE_IMPLEMENTED and a "
            "rendered waveform is a SYNTHETIC_OBSERVATION. A REAL_DEVICE "
            "emission drives nothing, a target at or above Nyquist is "
            "refused rather than clamped, a post-seal edit is detected, and "
            "a phase-truncation spur is a KNOWN_ORDINARY_EFFECT, never a "
            "signal. PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "PHYSICAL_RUN_STATUS",
    "ANALYSIS_VERSION", "COMPILER_CLAIM_CLASS", "RECIPE_CLAIM_CLASS",
    "WAVEFORM_CLAIM_CLASS", "DEFAULT_FTW_TOLERANCE_LSB",
    "DDSError", "DDSDeviceLimitError", "NoDDSHardwareError", "RecipeSealError",
    "DDSMode", "DDSFaultMode", "TargetKind",
    "DDSDeviceSpec", "FrequencyTarget",
    "frequency_to_ftw", "ftw_to_frequency", "phase_to_word", "word_to_phase",
    "amplitude_to_word",
    "RecipeStep", "compile_step", "DDSRecipe",
    "compile_targets", "compile_sweep", "compile_chirp",
    "compile_protocol_sweep", "verify_recipe",
    "compile_multichannel_phases", "phase_closure_residual",
    "SealedRecipe", "freeze_recipe", "refuse_edit_after_seal",
    "RenderedWaveform", "render_waveform",
    "DDSEmitter", "RealDDSEmitter", "SyntheticDDSEmitter", "ReplayDDSEmitter",
    "FaultInjectionDDSEmitter",
    "quantization_report", "waveform_observation",
    "refuse_recipe_as_measured", "refuse_spur_as_signal",
    "dds_recipes_report",
]
