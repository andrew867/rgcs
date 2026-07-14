"""rgcs_core.harmonics — axial half-wave estimates and the 4096 ladder
with mandatory wave-speed uncertainty (RGCS-M.8..M.12, closes D-05).

Units: lengths in mm, wave speed in m/s (the mm -> m conversion appears
exactly once per function), frequencies in Hz. Every frequency/length
output is an :class:`~rgcs_core.uncertainty.UncertainValue`; harmonic
classification is SET-VALUED (RGCS-M.12).

Interpretation rule (RGCS-M.11): with u_v = 0.05, a 0.03% "match" is
~170x smaller than the systematic band; such matches are
Derived-from-Hypothesis arithmetic, never confirmation (D-04).
"""

from __future__ import annotations

import math
from typing import Any

from ..provenance import classified, classification_string
from ..uncertainty import UncertainValue, default_wave_speed

__all__ = ["DEFAULT_BASE_FREQUENCY_HZ", "axial_half_wave",
           "ladder_length_mm", "harmonic_classification"]

#: Ladder base frequency f_0. Source claim (JH corpus, RG-01).
DEFAULT_BASE_FREQUENCY_HZ = 4096.0


def _as_uncertain(v: UncertainValue | float | None) -> UncertainValue:
    if v is None:
        return default_wave_speed()
    if isinstance(v, UncertainValue):
        return v
    return UncertainValue(float(v), 0.0)


@classified("Derived", registry=("RGCS-M.8", "RGCS-M.10", "RGCS-M.11"),
            sources=("RG-01",),
            note="formula Established; applicability to a faceted tapered "
                 "crystal is Hypothesis H-01a (assumption A-01)")
def axial_half_wave(length_mm: float,
                    wave_speed: UncertainValue | float | None = None
                    ) -> UncertainValue:
    """Axial half-wave frequency estimate f_ax = v_L/(2 L) (RGCS-M.8),
    L converted mm -> m exactly once here. Returns an UncertainValue with
    u(f)/f = u_v (RGCS-M.11)."""
    if not (math.isfinite(length_mm) and length_mm > 0):
        raise ValueError("length_mm must be positive")
    v = _as_uncertain(wave_speed)
    if v.mean <= 0:
        raise ValueError("wave speed must be positive")
    length_m = length_mm / 1000.0          # the single mm -> m conversion
    return UncertainValue(v.mean / (2.0 * length_m), v.u_rel)


@classified("Derived", registry=("RGCS-M.9", "RGCS-M.11"), sources=("RG-01",),
            note="f_0 = 4096 Hz is Source claim; output is an interval")
def ladder_length_mm(harmonic_index: int,
                     base_frequency_hz: float = DEFAULT_BASE_FREQUENCY_HZ,
                     wave_speed: UncertainValue | float | None = None
                     ) -> UncertainValue:
    """Ideal ladder length L_N = v_L/(2 N f_0), returned in mm
    (m -> mm conversion exactly once here). Golden: ladder constant
    770.263671875 mm (G-01); L_5 = 154.052734375 mm (G-02)."""
    if harmonic_index < 1:
        raise ValueError("harmonic_index must be >= 1")
    if not (math.isfinite(base_frequency_hz) and base_frequency_hz > 0):
        raise ValueError("base_frequency_hz must be positive")
    v = _as_uncertain(wave_speed)
    if v.mean <= 0:
        raise ValueError("wave speed must be positive")
    length_m = v.mean / (2.0 * harmonic_index * base_frequency_hz)
    return UncertainValue(length_m * 1000.0, v.u_rel)  # single m -> mm

@classified("Derived", registry=("RGCS-M.12",), sources=("RG-01", "RG-02",
                                                         "RG-03"),
            note="SET-VALUED classification; |set| > 1 means the harmonic "
                 "class is ambiguous at the declared u_v")
def harmonic_classification(length_mm: float,
                            base_frequency_hz: float =
                            DEFAULT_BASE_FREQUENCY_HZ,
                            wave_speed: UncertainValue | float | None = None
                            ) -> dict[str, Any]:
    """Set-valued harmonic classification (RGCS-M.12):
    N_eff = f_ax/f_0; the class set contains every N' whose bin
    [(N'-1/2) f_0, (N'+1/2) f_0] intersects the 1-sigma band
    [f_ax (1-u_v), f_ax (1+u_v)]. Golden: 116 mm at u_v = 0.05 -> {6, 7}."""
    f_ax = axial_half_wave(length_mm, wave_speed)
    n_eff = f_ax.mean / base_frequency_hz
    n_round = max(1, round(n_eff))
    lo, hi = f_ax.interval()
    n_min = max(1, math.ceil(lo / base_frequency_hz - 0.5))
    n_max = math.floor(hi / base_frequency_hz + 0.5)
    class_set = [n for n in range(n_min, n_max + 1)
                 if (max(lo, (n - 0.5) * base_frequency_hz)
                     <= min(hi, (n + 0.5) * base_frequency_hz))]
    target = n_round * base_frequency_hz
    ideal = ladder_length_mm(n_round, base_frequency_hz, wave_speed)
    return {
        "axial_frequency_hz": f_ax.to_dict(),
        "n_eff": n_eff,
        "nearest_harmonic": n_round,
        "harmonic_class_set": class_set,
        "ambiguous": len(class_set) != 1,
        "target_frequency_hz": target,
        "frequency_error_hz": f_ax.mean - target,
        "frequency_error_fraction": f_ax.mean / target - 1.0,
        "ideal_length_mm": ideal.to_dict(),
        "length_error_fraction": length_mm / ideal.mean - 1.0,
        "interpretation_rule": "matches within the u_v band are "
                               "Derived-from-Hypothesis arithmetic, never "
                               "confirmation (RGCS-M.11, D-04)",
        "classification": classification_string(harmonic_classification),
    }
