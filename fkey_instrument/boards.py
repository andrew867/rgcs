"""CYD board variant discovery and profiles (Agent A14) and signal
backends with exact timing arithmetic (Agent A16).

"ESP32 CYD" is not a pin map. Until a concrete variant is verified
(photo checklist + self-test), the profile is UNKNOWN and OUTPUT IS
DISABLED — no build guide may name an output pin (A14 gate)."""

from __future__ import annotations

from fractions import Fraction


class BoardError(RuntimeError):
    pass


# Known CYD family variants, from community documentation. These are
# CANDIDATE profiles: 'verified: False' until the physical board's
# self-test confirms chip/display/touch IDs. Pin data provenance:
# community CYD documentation (witnessyourself/esp32-smartdisplay
# ecosystems); to be verified against the physical board.
BOARD_PROFILES = {
    "ESP32-2432S028R": {
        "display": {"driver": "ILI9341", "bus": "SPI",
                    "pins": {"MOSI": 13, "CLK": 14, "CS": 15,
                             "DC": 2, "BL": 21}},
        "touch": {"driver": "XPT2046",
                  "pins": {"MOSI": 32, "MISO": 39, "CLK": 25,
                           "CS": 33, "IRQ": 36}},
        "sd": {"pins": {"MOSI": 23, "MISO": 19, "CLK": 18,
                        "CS": 5}},
        "rgb_led": {"pins": {"R": 4, "G": 16, "B": 17}},
        "ldr": {"pin": 34},
        "speaker": {"pin": 26},
        "boot_strap_pins": [0, 2, 5, 12, 15],
        "input_only_pins": [34, 35, 36, 39],
        "candidate_output_pins": [22, 27],
        "candidate_adc_pins": [35],
        "verified": False,
    },
    "ESP32-2432S024C": {
        "display": {"driver": "ILI9341", "bus": "SPI",
                    "pins": {"MOSI": 13, "CLK": 14, "CS": 15,
                             "DC": 2, "BL": 27}},
        "touch": {"driver": "CST820-I2C",
                  "pins": {"SDA": 33, "SCL": 32}},
        "sd": {"pins": {"MOSI": 23, "MISO": 19, "CLK": 18,
                        "CS": 5}},
        "rgb_led": {"pins": {"R": 4, "G": 16, "B": 17}},
        "ldr": {"pin": 34},
        "speaker": {"pin": 26},
        "boot_strap_pins": [0, 2, 5, 12, 15],
        "input_only_pins": [34, 35, 36, 39],
        "candidate_output_pins": [22, 21],
        "candidate_adc_pins": [35],
        "verified": False,
    },
    "SIMULATOR": {
        "display": None, "touch": None, "sd": None,
        "rgb_led": None, "ldr": None, "speaker": None,
        "boot_strap_pins": [], "input_only_pins": [],
        "candidate_output_pins": ["SIM_OUT"],
        "candidate_adc_pins": ["SIM_ADC"],
        "verified": True,          # by definition: no hardware
        "simulated": True,
    },
    "UNKNOWN": {
        "verified": False,
        "output_state": "OUTPUT_DISABLED",
        "note": "unknown board revision means OUTPUT_DISABLED "
                "(A14 gate); run the questionnaire + self-test",
    },
}


def board_profile(name: str) -> dict:
    if name not in BOARD_PROFILES:
        raise BoardError(f"unknown board {name!r}; register it "
                         "through the questionnaire, never guess "
                         "pins")
    import json
    return json.loads(json.dumps(BOARD_PROFILES[name]))


def pin_conflicts(profile_name: str, requested_pins: list) -> dict:
    """Static pin-collision detection (A14 task 8): output on a pin
    already used by display/touch/SD/LED, an input-only pin, or a
    boot-strap pin is a conflict."""
    p = board_profile(profile_name)
    if p.get("output_state") == "OUTPUT_DISABLED":
        return {"allowed": [], "conflicts": requested_pins,
                "reason": "board unknown -> OUTPUT_DISABLED"}
    used = set()
    for sub in ("display", "touch", "sd", "rgb_led"):
        block = p.get(sub) or {}
        for v in (block.get("pins") or {}).values():
            used.add(v)
    for extra in ("ldr", "speaker"):
        if p.get(extra):
            used.add(p[extra]["pin"])
    conflicts, allowed = [], []
    for pin in requested_pins:
        if pin in used:
            conflicts.append({"pin": pin, "reason": "used by board "
                              "peripheral"})
        elif pin in p.get("input_only_pins", []):
            conflicts.append({"pin": pin, "reason": "input-only "
                              "GPIO"})
        elif pin in p.get("boot_strap_pins", []):
            conflicts.append({"pin": pin, "reason": "boot-strap pin: "
                              "driving it can prevent boot or "
                              "change boot mode"})
        else:
            allowed.append(pin)
    return {"allowed": allowed, "conflicts": conflicts}


def questionnaire() -> dict:
    """A14 task 2: what a human must record before a profile is
    verified."""
    return {"photos": ["front with display on", "back silkscreen",
                       "USB connector area", "any daughter boards"],
            "record": ["exact silkscreen model string",
                       "display size and touch type "
                       "(resistive pen vs capacitive)",
                       "USB chip marking", "flash/PSRAM from "
                       "esptool flash_id",
                       "self-test output (chip, display ID, "
                       "touch ID, SD present)"],
            "rule": "a profile becomes verified=True only when the "
                    "self-test report matches it"}


# --- A16: signal backends with exact realized-frequency math -------------------

APB_CLK_HZ = 80_000_000


class Backend:
    """Common result contract: requested_hz, calculated realized
    Fraction, quantization error, and a MEASURED field that stays
    None until a real measurement exists (never asserted)."""

    name = "abstract"

    def realize(self, f_requested) -> dict:
        raise NotImplementedError

    def _wrap(self, f_req: Fraction, f_real, detail: dict) -> dict:
        err = None if f_real is None else f_real - f_req
        return {"backend": self.name,
                "requested_hz": f_req,
                "calculated_realized_hz": f_real,
                "measured_realized_hz": None,
                "quantization_error_hz": err,
                "exact": (err == 0) if err is not None else False,
                **detail}


class LedcBackend(Backend):
    """ESP32 LEDC PWM: f = APB / (div * 2^res), div in Q10.8.
    Exact rational arithmetic on the divider."""

    name = "LEDC"

    def realize(self, f_requested, res_bits: int = 10) -> dict:
        from .relations import hz as _hz
        f_req = _hz(f_requested) if not isinstance(f_requested,
                                                  Fraction) \
            else f_requested
        if f_req <= 0:
            raise BoardError("frequency must be positive")
        div_q8 = round(Fraction(APB_CLK_HZ * 256) /
                       (f_req * 2 ** res_bits))
        if div_q8 < 256:
            return self._wrap(f_req, None, {
                "refused": True,
                "reason": f"divider below 1.0 at {res_bits} bits: "
                          "reduce resolution (A16: unsupported "
                          "timing is rejected, not fudged)"})
        f_real = Fraction(APB_CLK_HZ * 256, div_q8 * 2 ** res_bits)
        return self._wrap(f_req, f_real, {
            "res_bits": res_bits, "divider_q10_8": div_q8,
            "divider": Fraction(div_q8, 256)})


class RmtBackend(Backend):
    """RMT: tick-quantized pulse trains. tick = APB/div; a period is
    an integer number of ticks."""

    name = "RMT"

    def realize(self, f_requested, clk_div: int = 1) -> dict:
        from .relations import hz as _hz
        f_req = _hz(f_requested) if not isinstance(f_requested,
                                                  Fraction) \
            else f_requested
        tick_hz = Fraction(APB_CLK_HZ, clk_div)
        ticks = round(tick_hz / f_req)
        if ticks < 2:
            return self._wrap(f_req, None, {
                "refused": True, "reason": "period under 2 ticks"})
        f_real = tick_hz / ticks
        return self._wrap(f_req, f_real, {
            "clk_div": clk_div, "ticks_per_period": ticks})


class DdsBackend(Backend):
    """I2S/DAC DDS: f = fs * dphi / 2^N. Average frequency exact only
    when dphi divides evenly; jitter of one sample otherwise."""

    name = "I2S_DDS"

    def realize(self, f_requested, fs_hz: int = 512_000,
                acc_bits: int = 32) -> dict:
        from .relations import hz as _hz
        f_req = _hz(f_requested) if not isinstance(f_requested,
                                                  Fraction) \
            else f_requested
        dphi = round(f_req * 2 ** acc_bits / fs_hz)
        f_real = Fraction(dphi * fs_hz, 2 ** acc_bits)
        return self._wrap(f_req, f_real, {
            "fs_hz": fs_hz, "acc_bits": acc_bits,
            "phase_increment": dphi,
            "note": "average frequency; per-sample jitter up to one "
                    "sample clock — do not call the setpoint exact "
                    "without measurement"})


class SimulatorBackend(Backend):
    name = "SIMULATOR"

    def realize(self, f_requested) -> dict:
        from .relations import hz as _hz
        f_req = _hz(f_requested) if not isinstance(f_requested,
                                                  Fraction) \
            else f_requested
        return self._wrap(f_req, f_req, {"synthetic": True})


class NullBackend(Backend):
    name = "NULL"

    def realize(self, f_requested) -> dict:
        from .relations import hz as _hz
        f_req = _hz(f_requested) if not isinstance(f_requested,
                                                  Fraction) \
            else f_requested
        return self._wrap(f_req, None, {"output": "disabled"})


BACKENDS = {b.name: b for b in (LedcBackend(), RmtBackend(),
                                DdsBackend(), SimulatorBackend(),
                                NullBackend())}


def capability_report() -> dict:
    """A16: what each backend can and cannot do."""
    return {
        "LEDC": {"kind": "hardware PWM", "waveforms": ["square"],
                 "range_hz": [1, 40_000_000],
                 "duty_control": True, "burst": False},
        "RMT": {"kind": "pulse sequencer",
                "waveforms": ["pulse train", "burst"],
                "range_hz": [1, 1_000_000], "burst": True},
        "I2S_DDS": {"kind": "DAC/DDS", "waveforms": ["arbitrary"],
                    "range_hz": [1, 200_000],
                    "note": "arbitrary waveforms incl. sine; needs "
                            "external DAC or internal 8-bit DAC "
                            "(quality limited)"},
        "SIMULATOR": {"kind": "synthetic", "waveforms": ["any"],
                      "range_hz": [0, 10 ** 9]},
        "NULL": {"kind": "disabled", "waveforms": []},
    }


def timing_report_4096_and_20480() -> dict:
    """A16 specific test: compile both key frequencies on every real
    backend, with divider/phase-increment, quantization error, and
    cumulative drift over a 60 s run."""
    from .phase_closure import closure_drift
    out = {}
    for name in ("LEDC", "RMT", "I2S_DDS"):
        b = BACKENDS[name]
        for f in ("4096", "20480"):
            r = b.realize(f)
            key = f"{name}@{f}Hz"
            if r.get("refused") or r["calculated_realized_hz"] is None:
                out[key] = r
                continue
            drift = closure_drift(f, r["calculated_realized_hz"], 60)
            out[key] = {**{k: str(v) if isinstance(v, Fraction)
                           else v for k, v in r.items()},
                        "cycle_drift_60s":
                            str(drift["cycle_error"])}
    return out
