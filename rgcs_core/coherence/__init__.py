"""rgcs_core.coherence — analytic signal, phase, circular statistics,
autocorrelation coherence, phase linearity, PLV, onset/decay, threshold
detection with bootstrap, spatial phase anisotropy, and decay-law model
comparison (COH-M1..M14; RGCS-M.51..M.56, M.61).

Exact port of the normative reference implementations in
tools/generate_golden_coherence.py (docs/COHERENCE_METRICS.md, frozen).
Expected golden values live in
experiments/sample_data/golden_coherence/manifest.json and are read by
tests, never hard-coded.
"""

from .metrics import (DEFAULT_WINDOW_S, DEFAULT_HOP_S, analytic_signal,
                      instantaneous_phase, instantaneous_frequency,
                      circular_mean, circular_resultant, circular_variance,
                      rayleigh_test, coherence_window, coherence_series,
                      noise_baseline_theory, phase_linearity,
                      amplitude_normalized_coherence, band_power_fraction,
                      coherence_onset_time, coherence_decay_time,
                      phase_locking_value, initial_phase_estimate)
from .anisotropy import (windowed_phase_rates, spatial_phase_anisotropy,
                         phase_rate_shear_scalar, circular_variance_tensor)
from .models import (fit_exponential_decay, model_comparison,
                     threshold_detect_bootstrap)

__all__ = [
    "DEFAULT_WINDOW_S", "DEFAULT_HOP_S", "analytic_signal",
    "instantaneous_phase", "instantaneous_frequency", "circular_mean",
    "circular_resultant", "circular_variance", "rayleigh_test",
    "coherence_window", "coherence_series", "noise_baseline_theory",
    "phase_linearity", "amplitude_normalized_coherence",
    "band_power_fraction", "coherence_onset_time", "coherence_decay_time",
    "phase_locking_value", "initial_phase_estimate", "windowed_phase_rates",
    "spatial_phase_anisotropy", "phase_rate_shear_scalar",
    "circular_variance_tensor", "fit_exponential_decay",
    "model_comparison", "threshold_detect_bootstrap",
]
