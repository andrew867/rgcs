"""A12-A15 — DDS/NCO mathematics, practical backends, tuning-word and
phase-closure compilation, and the shared-clock uncertainty model.

**A12 abstract reference.** A direct digital synthesiser with an
``N``-bit phase accumulator clocked at ``f_clk`` emits

    f_out = M * f_clk / 2**N          (M = tuning word, integer)

With N = 36 and f_clk = 2.45 GHz the least-significant step is
2.45e9 / 2**36 Hz exactly — the number the source supplied as a
"fractal relationship", which is in fact a frequency resolution
(CSPC-CORR-002). All arithmetic is ``Fraction``; the model is exact.

**A13 practical backends.** 2.45 GHz is not a realizable accumulator
clock for this project's hardware, and the programme explicitly does
not build a 2.45 GHz radiator (A17). Practical NCOs use ordinary
reference clocks (10/25/100/125 MHz). A requested frequency is then
generally NOT representable: the tuning word is an integer, so the
realized frequency differs. Requested, realized, and measured are three
separate fields and are never conflated — realized is computed,
measured stays ``None`` until an instrument reports one.

**A14 phase-closure compiler.** Reuses
``fkey_instrument.phase_closure`` (exact rational closure windows)
rather than re-deriving it.

**A15 shared clock uncertainty.** A reference oscillator has a
fractional frequency offset and drift; both propagate to every tone
derived from it. Because all tones share the clock, their *ratios* are
immune to clock error while their *absolute* values are not — which is
exactly why a phase-closure experiment can be tight even when absolute
calibration is poor.

Nothing here emits or measures anything physical.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from fkey_instrument import phase_closure
from .units import exact

#: Reference clocks the programme treats as realizable, in Hz.
#: The 2**n entries are ordinary "binary" crystals (67.108864 MHz is
#: 2**26, i.e. 32.768 kHz x 2**11) and are stock parts, not exotica.
REALIZABLE_CLOCKS = {
    "XO_10MHZ": Fraction(10_000_000),
    "XO_25MHZ": Fraction(25_000_000),
    "XO_100MHZ": Fraction(100_000_000),
    "XO_125MHZ": Fraction(125_000_000),
    "ESP32_APB_80MHZ": Fraction(80_000_000),
    "XO_BINARY_2POW25": Fraction(2) ** 25,      # 33.554432 MHz
    "XO_BINARY_2POW26": Fraction(2) ** 26,      # 67.108864 MHz
}


def exact_clocks_for(targets, bits: int = 32) -> dict:
    """Which realizable clocks represent EVERY target exactly?

    A practically important result rather than a numerical curiosity:
    the binary target family (4096, 20480, 32768, 40960 ...) is exactly
    representable on a binary reference clock and is NOT exactly
    representable on any decimal one. Exactness is therefore an
    engineering choice of oscillator, not a property of the
    frequencies, and certainly not evidence about nature.
    """
    out = {}
    for name, clk in REALIZABLE_CLOCKS.items():
        ok = True
        for t in targets:
            ratio = exact(t) * Fraction(2) ** bits / clk
            if ratio.denominator != 1:
                ok = False
                break
        out[name] = ok
    return {
        "targets": [str(exact(t)) for t in targets],
        "bits": bits,
        "exact_on": [k for k, v in out.items() if v],
        "inexact_on": [k for k, v in out.items() if not v],
        "recommendation":
            "choose a reference clock in the same arithmetic family as "
            "the targets; a binary target family needs a binary clock",
        "evidence_class": "DERIVED_ARITHMETIC",
    }

#: The abstract model's clock. NOT a hardware target.
ABSTRACT_CLOCK_HZ = Fraction(2_450_000_000)
ABSTRACT_BITS = 36


class DDSError(ValueError):
    pass


@dataclass(frozen=True)
class DDSPlan:
    """A tuning word and everything needed to judge it honestly."""
    requested_hz: Fraction
    realized_hz: Fraction            # exact, from the integer word
    tuning_word: int
    bits: int
    clock_hz: Fraction
    measured_hz: None = None         # only an instrument may fill this

    @property
    def lsb_hz(self) -> Fraction:
        return self.clock_hz / Fraction(2) ** self.bits

    @property
    def error_hz(self) -> Fraction:
        return self.realized_hz - self.requested_hz

    @property
    def relative_error(self) -> Fraction:
        return self.error_hz / self.requested_hz if self.requested_hz \
            else Fraction(0)

    @property
    def exact(self) -> bool:
        return self.realized_hz == self.requested_hz

    def to_dict(self) -> dict:
        return {
            "requested_hz": str(self.requested_hz),
            "realized_hz": str(self.realized_hz),
            "measured_hz": self.measured_hz,
            "tuning_word": self.tuning_word,
            "bits": self.bits,
            "clock_hz": str(self.clock_hz),
            "lsb_hz": str(self.lsb_hz),
            "error_hz": str(self.error_hz),
            "relative_error_ppm": float(self.relative_error) * 1e6,
            "exactly_representable": self.exact,
            "evidence_class": "DERIVED_ARITHMETIC",
            "note": "realized is COMPUTED from the integer tuning "
                    "word; measured stays null until an instrument "
                    "reports one",
        }


def lsb_hz(clock_hz=ABSTRACT_CLOCK_HZ, bits: int = ABSTRACT_BITS
           ) -> Fraction:
    """Frequency resolution of an N-bit accumulator, exactly."""
    return exact(clock_hz) / Fraction(2) ** bits


def tuning_word(target_hz, clock_hz, bits: int) -> int:
    """Nearest integer tuning word (round-half-up on exact rationals)."""
    t, c = exact(target_hz), exact(clock_hz)
    if t <= 0 or c <= 0:
        raise DDSError("frequencies must be positive")
    if t >= c / 2:
        raise DDSError(
            f"target {t} Hz is at or above Nyquist for a {c} Hz clock")
    ratio = t * Fraction(2) ** bits / c
    n = int(ratio)
    return n + 1 if (ratio - n) >= Fraction(1, 2) else n


def plan(target_hz, clock="XO_100MHZ", bits: int = 32) -> DDSPlan:
    """Compile one tone for a practical NCO."""
    c = REALIZABLE_CLOCKS[clock] if isinstance(clock, str) \
        else exact(clock)
    t = exact(target_hz)
    m = tuning_word(t, c, bits)
    realized = Fraction(m) * c / Fraction(2) ** bits
    return DDSPlan(t, realized, m, bits, c)


def abstract_plan(target_hz) -> DDSPlan:
    """A12: the exact 36-bit / 2.45 GHz reference model."""
    return plan(target_hz, ABSTRACT_CLOCK_HZ, ABSTRACT_BITS)


def backend_comparison(target_hz, bits: int = 32) -> dict:
    """Same target across every realizable clock: which is closest, and
    is it exactly representable anywhere?"""
    rows = {}
    for name in REALIZABLE_CLOCKS:
        p = plan(target_hz, name, bits)
        rows[name] = p.to_dict()
    best = min(rows.items(),
               key=lambda kv: abs(float(kv[1]["relative_error_ppm"])))
    return {
        "target_hz": str(exact(target_hz)),
        "bits": bits,
        "backends": rows,
        "best_backend": best[0],
        "any_exact": any(v["exactly_representable"]
                         for v in rows.values()),
        "claim_boundary":
            "quantization arithmetic only; no signal was generated and "
            "no hardware was operated",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


# --- A14 phase-closure compilation --------------------------------------

def compile_recipe(targets, clock="XO_100MHZ", bits: int = 32) -> dict:
    """Compile a multi-tone recipe: tuning words plus the exact window
    in which every REALIZED tone closes an integer number of cycles.

    Closure is computed on realized frequencies, not requested ones —
    using the requested values would report a closure the hardware
    cannot actually deliver.
    """
    plans = [plan(t, clock, bits) for t in targets]
    realized = [p.realized_hz for p in plans]
    window = phase_closure.common_closure_window(realized)
    requested_window = phase_closure.common_closure_window(
        [p.requested_hz for p in plans])
    drift = [phase_closure.closure_drift(p.requested_hz, p.realized_hz,
                                         window["window_s"])
             for p in plans]
    return {
        "clock": clock if isinstance(clock, str) else str(clock),
        "bits": bits,
        "plans": [p.to_dict() for p in plans],
        "closure_window_s_realized": str(window["window_s"]),
        "closure_window_s_requested": str(requested_window["window_s"]),
        "closure_computed_on": "realized frequencies",
        "per_tone_drift": drift,
        "all_exact": all(p.exact for p in plans),
        "evidence_class": "DERIVED_ARITHMETIC",
        "claim_boundary":
            "a closure window is arithmetic about the generator. It "
            "says nothing about whether a specimen responds "
            "(firewall ARITHMETIC_TO_SPECTRUM).",
    }


# --- A15 shared-clock uncertainty ---------------------------------------

@dataclass(frozen=True)
class ClockModel:
    """A shared reference oscillator."""
    nominal_hz: Fraction
    fractional_offset: Fraction      # (f_actual - f_nom)/f_nom
    fractional_drift_per_s: Fraction = Fraction(0)
    label: str = ""

    def actual_hz(self, elapsed_s=0) -> Fraction:
        e = exact(elapsed_s)
        return self.nominal_hz * (1 + self.fractional_offset
                                  + self.fractional_drift_per_s * e)


def shared_clock_uncertainty(targets, clock_model: ClockModel,
                             elapsed_s=1) -> dict:
    """Propagate reference-clock error to derived tones.

    The key structural fact: every tone scales by the SAME factor, so
    ratios between tones are exact regardless of clock error, while
    absolute frequencies inherit it. Phase-closure experiments exploit
    this; absolute-frequency claims cannot.
    """
    k = (1 + clock_model.fractional_offset
         + clock_model.fractional_drift_per_s * exact(elapsed_s))
    rows = []
    for t in targets:
        t = exact(t)
        rows.append({
            "nominal_hz": str(t),
            "actual_hz": str(t * k),
            "absolute_error_hz": str(t * k - t),
            "relative_error_ppm": float(k - 1) * 1e6,
        })
    ratios_exact = True
    if len(targets) >= 2:
        a, b = exact(targets[0]), exact(targets[1])
        ratios_exact = ((a * k) / (b * k)) == (a / b)
    return {
        "clock": clock_model.label or str(clock_model.nominal_hz),
        "elapsed_s": str(exact(elapsed_s)),
        "scale_factor": str(k),
        "tones": rows,
        "ratios_immune_to_clock_error": ratios_exact,
        "note": "all tones share one clock, so their RATIOS are exact "
                "under clock error while ABSOLUTE values are not",
        "evidence_class": "ANALYTIC_MODEL",
    }
