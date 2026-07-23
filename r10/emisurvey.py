"""P10 — a blinded ABAB switched-supply and LED EMI survey framework.

The narrative under test is familiar: someone runs an LED lamp or a
switched-mode supply, *perceives* a change in how well some
communication or sensing "comes through", and concludes the device
*causes* an electromagnetic effect on that channel. This module builds
the honest machine that question needs, and defaults to a
software-only, BLOCKED verdict for one reason: **no spectrum analyzer,
field probe, or EMI receiver is available in this environment, so no
electromagnetic quantity is measured here.** What is built is the
experimental design and its statistics, tested on synthetic data.

Why the framework is blinded and why correlation is not causation
-----------------------------------------------------------------

Three things get conflated in this kind of report, and the whole point
is to keep them apart:

1. ``perceived_communication_quality`` -- a subjective score;
2. ``measured_EMI_environment`` -- what a calibrated instrument would
   read from the field/conducted noise;
3. ``instrument_readout_quality`` -- how clean the *instrument's own*
   readout is, which a switched supply can degrade for mundane reasons
   (ground loops, supply ripple, probe pickup) with no bearing on the
   channel of interest.

A correlation among these three does **not** establish a source or a
mechanism. Perception tracks expectation; a device being ON is visible;
an unblinded analyst scores spectra to match the state they can see.
So the schedule is a blinded ABAB (device-ON = A, device-OFF = B) with
the block states concealed behind a blind code: the analyst scores each
block without knowing whether the device was on. The state is only
revealed with a sealed key, after scoring.

The estimator is a difference in a spectral metric between ON and OFF
blocks, judged against a **permutation null** over the block-label
assignment. With no real ON/OFF difference the p-value is not small
(the control); a planted ON-block excess is recovered with a small
p-value (the power check). Real measured data is declared
``BLOCKED_NO_DATA_SOURCE`` -- honest, not faked -- and any causal
reading of an observed correlation is refused outright.

No private location is ever emitted: ``EmiSurvey`` carries a
``location_private`` field for the operator's own records, and
``public_view`` omits it from every serialization this module produces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class EmiError(RuntimeError):
    """Raised on malformed EMI input or a refused causal claim."""


# --- blinded ABAB schedule ---------------------------------------------

#: Internal true-state tokens. A = device ON, B = device OFF.
STATE_ON = "A"
STATE_OFF = "B"


@dataclass(frozen=True)
class BlindSchedule:
    """A blinded ABAB schedule.

    ``blind_codes`` is what the analyst sees per block -- opaque tokens
    that alternate but do not reveal ON/OFF. ``key`` maps each opaque
    token back to its true state and is meant to stay sealed until
    scoring is complete; it is exposed here only so :func:`reveal` and
    the tests can round-trip it.
    """

    n_blocks: int
    blind_codes: tuple[str, ...]
    key: dict = field(default_factory=dict)


def abab_schedule(n_blocks: int, seed: int = 20260723) -> BlindSchedule:
    """Alternating device-ON (A) / device-OFF (B) blocks, blinded.

    The true states strictly alternate A, B, A, B, .... Each state is
    mapped to a randomly chosen opaque token, so the analyst sees an
    alternating sequence of tokens without knowing which token means
    ON. The sealed :attr:`BlindSchedule.key` reverses the mapping.
    """
    if n_blocks < 2:
        raise EmiError("an ABAB survey needs at least two blocks")
    rng = np.random.default_rng(seed)
    true_states = [STATE_ON if i % 2 == 0 else STATE_OFF
                   for i in range(n_blocks)]
    tokens = ["blk_x", "blk_y"]
    rng.shuffle(tokens)                      # which token conceals ON
    code_for = {STATE_ON: tokens[0], STATE_OFF: tokens[1]}
    blind_codes = tuple(code_for[s] for s in true_states)
    key = {tokens[0]: STATE_ON, tokens[1]: STATE_OFF}
    return BlindSchedule(n_blocks, blind_codes, key)


def reveal(schedule: BlindSchedule, key: dict) -> tuple[str, ...]:
    """Recover the true ON/OFF states from the blind codes and key."""
    try:
        return tuple(key[c] for c in schedule.blind_codes)
    except KeyError as exc:
        raise EmiError(f"blind code {exc} not in the supplied key") from exc


# --- the survey schema --------------------------------------------------

@dataclass
class EmiSurvey:
    """A device-on/off EMI survey record.

    ``location_private`` holds the operator's raw location and is NEVER
    emitted by any public serialization -- see :meth:`public_view`.
    All the spectral / field fields default empty because this
    environment measures none of them.
    """

    survey_id: str
    location_private: str                      # never emitted publicly
    timestamp: str
    devices: tuple[str, ...] = ()
    device_states: tuple[str, ...] = ()
    cables: tuple[str, ...] = ()
    terminations: tuple[str, ...] = ()
    instruments: tuple[str, ...] = ()
    electric_field: tuple[float, ...] = ()
    magnetic_field: tuple[float, ...] = ()
    conducted_noise: tuple[float, ...] = ()
    RF_spectrum: tuple[float, ...] = ()
    mains_spectrum: tuple[float, ...] = ()
    covariates: dict = field(default_factory=dict)
    blind_schedule: BlindSchedule | None = None
    raw_hashes: tuple[str, ...] = ()
    status: str = "BLOCKED_NO_DATA_SOURCE"

    def public_view(self) -> dict:
        """A serialization safe to publish: no private location.

        ``location_private`` and any raw-location covariate are omitted;
        only a coarse public disclosure marker remains.
        """
        cov = {k: v for k, v in self.covariates.items()
               if k not in ("location", "raw_location", "gps", "coordinates")}
        return {
            "survey_id": self.survey_id,
            "location_disclosed": "WITHHELD_PRIVATE",
            "timestamp": self.timestamp,
            "devices": list(self.devices),
            "device_states": list(self.device_states),
            "cables": list(self.cables),
            "terminations": list(self.terminations),
            "instruments": list(self.instruments),
            "n_electric_field": len(self.electric_field),
            "n_magnetic_field": len(self.magnetic_field),
            "n_conducted_noise": len(self.conducted_noise),
            "n_RF_spectrum": len(self.RF_spectrum),
            "n_mains_spectrum": len(self.mains_spectrum),
            "covariates": cov,
            "n_blocks": (self.blind_schedule.n_blocks
                         if self.blind_schedule else 0),
            "raw_hashes": list(self.raw_hashes),
            "status": self.status,
        }


# --- three outcomes that must not be conflated -------------------------

@dataclass(frozen=True)
class SurveyOutcome:
    """Three separate outcomes carried side by side, never merged.

    A correlation among them is not a source and not a mechanism.
    """

    perceived_communication_quality: float
    measured_EMI_environment: float
    instrument_readout_quality: float


def refuse_causal_claim(outcome: SurveyOutcome,
                        claim: str = "device causes the channel effect"
                        ) -> None:
    """Refuse to turn a correlation among the three outcomes into cause.

    Perception, the EMI environment, and the instrument's own readout
    can move together for reasons that have nothing to do with the
    channel of interest (expectation, the device being visibly ON,
    ground loops in the probe). This framework never asserts source or
    mechanism from correlation, so the claim is refused.
    """
    raise EmiError(
        f"refusing the claim {claim!r}: a correlation among perceived "
        f"communication quality, the measured EMI environment, and the "
        f"instrument readout quality does not establish a source or a "
        f"mechanism. Blinding, an independent calibrated instrument, and "
        f"a pre-registered null are required, and no electromagnetic "
        f"quantity is measured here in any case.")


# --- effect estimator, null and power ----------------------------------

def block_effect(metrics, states) -> float:
    """ON-minus-OFF difference in a per-block spectral metric."""
    m = np.asarray(metrics, float)
    s = np.asarray(states, dtype=object)
    if len(m) != len(s):
        raise EmiError("metrics and states differ in length")
    on = m[s == STATE_ON]
    off = m[s == STATE_OFF]
    if len(on) == 0 or len(off) == 0:
        raise EmiError("need at least one ON block and one OFF block")
    return float(on.mean() - off.mean())


def shuffled_label_null(metrics, states, *, trials: int = 2000,
                        seed: int = 20260723) -> dict:
    """Permutation null over the ON/OFF block-label assignment.

    Shuffling which blocks are called ON destroys any real device/metric
    link while preserving the metric values. The two-sided p-value is
    the fraction of shuffles whose absolute effect meets or exceeds the
    observed one. With no real difference the p-value is not small.
    """
    m = np.asarray(metrics, float)
    s = np.asarray(states, dtype=object)
    obs = abs(block_effect(m, s))
    rng = np.random.default_rng(seed)
    at_least = 0
    for _ in range(trials):
        sp = rng.permutation(s)
        if abs(block_effect(m, sp)) >= obs - 1e-12:
            at_least += 1
    p = (at_least + 1) / (trials + 1)
    return {
        "observed_effect": float(block_effect(m, s)),
        "observed_abs_effect": obs,
        "p_value": p,
        "verdict": ("ON_OFF_DIFFERENCE_DETECTED" if p < 0.05
                    else "NO_ON_OFF_DIFFERENCE"),
    }


def planted_effect_power(*, n_blocks: int = 24, excess: float = 3.0,
                         noise: float = 1.0, trials: int = 1000,
                         seed: int = 7) -> dict:
    """Plant a real ON-block excess and show the null recovers it.

    ON blocks are drawn with mean ``excess`` above OFF blocks (both with
    Gaussian ``noise``). A working test returns a small p-value here.
    """
    rng = np.random.default_rng(seed)
    sched = abab_schedule(n_blocks, seed=seed)
    states = reveal(sched, sched.key)
    states = np.array(states, dtype=object)
    metrics = rng.normal(0.0, noise, size=n_blocks)
    metrics[states == STATE_ON] += excess
    res = shuffled_label_null(metrics, states, trials=trials, seed=seed + 1)
    return {
        "planted_excess": excess,
        "p_value": res["p_value"],
        "observed_effect": res["observed_effect"],
        "has_power": bool(res["p_value"] < 0.05),
    }


# --- real measurement is blocked, not faked ----------------------------

REAL_DATA_STATUS = {
    "status": "BLOCKED_NO_DATA_SOURCE",
    "why": ("a real EMI survey needs a spectrum analyzer or EMI "
            "receiver, a calibrated E/H field probe, a LISN for "
            "conducted noise, and a mains monitor -- none of which this "
            "environment has. No field, spectrum, or conducted-noise "
            "value is recorded"),
    "not_faked": ("no measured electromagnetic result is reported, and "
                  "no device is claimed to affect any channel. The "
                  "design, the blinding, the null, and the power check "
                  "are complete and tested on synthetic data"),
}


def emisurvey_report() -> dict:
    return {
        "design": "blinded ABAB device-on/off EMI survey",
        "three_outcomes": ["perceived_communication_quality",
                           "measured_EMI_environment",
                           "instrument_readout_quality"],
        "estimator": "ON-minus-OFF spectral metric vs a permutation null",
        "real_data": REAL_DATA_STATUS,
        "verdict": "EMI_SURVEY_SOFTWARE_ONLY",
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "location_privacy": ("location_private is never emitted; "
                             "public_view withholds it"),
        "what_this_does_not_say": (
            "It does not measure any electromagnetic quantity, and it "
            "does not say a switched supply or LED affects any "
            "communication or sensing channel. A correlation among the "
            "three outcomes is not a source and not a mechanism; a "
            "causal reading is refused. Real measured data is blocked "
            "for want of instruments, not faked."),
    }
