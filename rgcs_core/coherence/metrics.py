"""Coherence metrics COH-M1..M11 — exact ports of the normative reference
implementations in tools/generate_golden_coherence.py
(docs/COHERENCE_METRICS.md; frozen by Sub-Agent 03).

Units: time in s, sample rate fs in Hz, phases in rad, coherence and PLV
dimensionless in [0, 1]. Complex baseband signal z = I + iQ in the
declared campaign observable unit X.

The autocorrelation coherence (COH-M5) is adapted from KOS-07 (Koster et
al. 2026, Methods equation) as an Established signal-processing
definition; substitution map: their z(t) = I + iQ -> ours; their 100 ns
window at GHz carriers -> window parameter w chosen per apparatus (same
~tens-of-carrier-cycles compromise). Amplitude and coherence are ALWAYS
separate quantities (KOS-03); a report of a bare coherence number without
(w, baseline) is non-compliant.
"""

from __future__ import annotations

import math

import numpy as np

from ..provenance import classified

__all__ = ["DEFAULT_WINDOW_S", "DEFAULT_HOP_S", "analytic_signal",
           "instantaneous_phase", "instantaneous_frequency",
           "circular_mean", "circular_resultant", "circular_variance",
           "rayleigh_test", "coherence_window", "coherence_series",
           "noise_baseline_theory", "phase_linearity",
           "amplitude_normalized_coherence", "band_power_fraction",
           "coherence_onset_time", "coherence_decay_time",
           "phase_locking_value", "initial_phase_estimate"]

#: Default analysis window / hop (declared analysis parameters; the golden
#: datasets use w = 2 ms, hop = 0.5 ms at fs = 100 kHz, f0 = 5 kHz).
DEFAULT_WINDOW_S = 2.0e-3
DEFAULT_HOP_S = 0.5e-3


@classified("Established", sources=("KOS-05",),
            note="COH-M1b: FFT Hilbert transform")
def analytic_signal(x: np.ndarray) -> np.ndarray:
    """COH-M1b. Analytic signal z(t) of a real record x via FFT Hilbert
    transform: Z(f) = X(f) * h(f), h = [1, 2...2, 1(only if N even),
    0...0]. Returns a complex array, same length as x."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        raise ValueError("input record must be non-empty")
    if not np.all(np.isfinite(x)):
        raise ValueError("input record contains non-finite samples "
                         "(NaN/inf) (QA-D-13)")
    n = x.size
    big_x = np.fft.fft(x)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0
    return np.fft.ifft(big_x * h)


@classified("Established", note="COH-M2")
def instantaneous_phase(z: np.ndarray) -> np.ndarray:
    """COH-M2. Unwrapped instantaneous phase phi(t) = unwrap(arg z). rad."""
    z = np.asarray(z)
    if z.size == 0:
        raise ValueError("input record must be non-empty")
    return np.unwrap(np.angle(z))


@classified("Derived", note="unified per-run initial-phase estimator "
                            "(QA-D-03): arg z at the first sample, mod 2 pi")
def initial_phase_estimate(z: np.ndarray) -> float:
    """Per-run initial-phase estimator, unified across all analysis
    pipelines (QA-D-03): the instantaneous phase at the first sample,
    phi_0 = arg z(0), returned mod 2 pi in [0, 2 pi).

    This is THE estimator behind every ensemble Rayleigh statistic in the
    project (Fig. 8, Table 8, manuscript body). A circular mean over a
    full analysis window is NOT used: for a rotating carrier the window
    resultant is near zero (the phase sweeps whole cycles), making the
    mean angle noise-dominated."""
    ph = instantaneous_phase(z)
    return float(np.mod(ph[0], 2.0 * np.pi))


@classified("Established", note="COH-M2; meaningful only where |z| is well "
                                "above noise — report alongside amplitude")
def instantaneous_frequency(z: np.ndarray, fs: float) -> np.ndarray:
    """COH-M2. Instantaneous frequency f_inst = (1/2 pi) dphi/dt via
    central differences (np.gradient). Hz. Length preserved."""
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("fs must be positive")
    if np.asarray(z).size < 2:
        raise ValueError("need at least 2 samples for a frequency "
                         "estimate (QA-D-12)")
    return np.gradient(instantaneous_phase(z)) * fs / (2.0 * np.pi)


@classified("Established", note="COH-M3: circular statistics")
def circular_mean(phases: np.ndarray) -> float:
    """COH-M3. Circular mean angle arg(mean exp(i phi)). rad in (-pi, pi]."""
    ph = np.asarray(phases)
    if ph.size == 0:
        raise ValueError("phases must be non-empty")
    return float(np.angle(np.mean(np.exp(1j * ph))))


@classified("Established", note="COH-M3")
def circular_resultant(phases: np.ndarray) -> float:
    """COH-M3. Mean resultant length Rbar = |mean exp(i phi)| in [0, 1]."""
    ph = np.asarray(phases)
    if ph.size == 0:
        raise ValueError("phases must be non-empty")
    return float(np.abs(np.mean(np.exp(1j * ph))))


@classified("Established", note="COH-M3")
def circular_variance(phases: np.ndarray) -> float:
    """COH-M3. Circular variance V = 1 - Rbar in [0, 1]."""
    return 1.0 - circular_resultant(phases)


@classified("Established", registry=("RGCS-M.61",), sources=("KOS-06",),
            note="COH-M4: standard small-sample corrected Rayleigh p "
                 "(Mardia & Jupp 2000); the alpha threshold is a protocol "
                 "parameter, not physics")
def rayleigh_test(phases: np.ndarray) -> dict:
    """COH-M4. Rayleigh test of uniformity for n phases:
    Z = n Rbar^2; p ~= exp(-Z)(1 + (2Z - Z^2)/(4n)
    - (24Z - 132Z^2 + 76Z^3 - 9Z^4)/(288 n^2)).
    Small p rejects uniformity (phase externally imprinted); large p is
    CONSISTENT with uniform (spontaneous-phase pattern, KOS-06)."""
    ph = np.asarray(phases, dtype=float)
    if ph.size == 0:
        raise ValueError("phases must be non-empty")
    n = ph.size
    rbar = circular_resultant(ph)
    z = n * rbar * rbar
    p = math.exp(-z) * (1.0 + (2.0 * z - z * z) / (4.0 * n)
                        - (24.0 * z - 132.0 * z ** 2 + 76.0 * z ** 3
                           - 9.0 * z ** 4) / (288.0 * n * n))
    return {"n": n, "Rbar": rbar, "Z": z, "p": float(min(max(p, 0.0), 1.0))}


@classified("Established", sources=("KOS-07",),
            note="COH-M5: adapted from Koster et al. 2026 Methods equation; "
                 "report triplet (C, w, baseline) — a bare number is "
                 "non-compliant")
def coherence_window(seg: np.ndarray) -> float:
    """COH-M5. Normalized autocorrelation coherence of one complex window
    segment: C = sum_tau |ACF_z(tau)| / (N * sum_n |z_n|^2), the discrete
    form of the KOS-07 normalization against a perfectly coherent dummy
    tone of the same power. Pure tone -> exactly 1; white noise -> small
    positive baseline ~ (2 sqrt(pi)/3)/sqrt(N); amplitude scale cancels."""
    seg = np.asarray(seg, dtype=complex)
    n = seg.size
    power = float(np.sum(np.abs(seg) ** 2))
    if power <= 0.0 or n < 2:
        return 0.0
    acf = np.correlate(seg, seg, mode="full")   # lags -(n-1)..(n-1)
    return float(np.sum(np.abs(acf)) / (n * power))


@classified("Established", sources=("KOS-07",),
            note="COH-M5 sliding form; window-length sensitivity analysis "
                 "is mandatory")
def coherence_series(z: np.ndarray, fs: float,
                     window_s: float = DEFAULT_WINDOW_S,
                     hop_s: float = DEFAULT_HOP_S
                     ) -> tuple[np.ndarray, np.ndarray]:
    """COH-M5. Sliding-window coherence trace C_w(t): coherence_window on
    boxcar segments of length w centred at t, hop hop_s.
    Returns (t_centres, C)."""
    z = np.asarray(z, dtype=complex)
    if z.size == 0:
        raise ValueError("input record must be non-empty")
    if not np.all(np.isfinite(z)):
        raise ValueError("input record contains non-finite samples "
                         "(NaN/inf); clean the record before coherence "
                         "analysis (QA-D-13)")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("fs must be positive")
    if window_s <= 0 or hop_s <= 0:
        raise ValueError("window_s and hop_s must be positive")
    nwin = max(int(round(window_s * fs)), 2)
    nhop = max(int(round(hop_s * fs)), 1)
    if z.size < nwin:
        raise ValueError("record shorter than one analysis window")
    starts = np.arange(0, z.size - nwin + 1, nhop)
    tc = (starts + nwin / 2.0) / fs
    c = np.array([coherence_window(z[s:s + nwin]) for s in starts])
    return tc, c


@classified("Established", sources=("KOS-07",),
            note="finite-window white-noise baseline; window-dependent, "
                 "measured per pipeline and reported with every C value")
def noise_baseline_theory(n_window: int) -> float:
    """Theoretical white-noise coherence baseline b_w ~ (2 sqrt(pi)/3)/
    sqrt(N_w) for the COH-M5 metric (~0.084 for N_w = 200)."""
    if n_window < 2:
        raise ValueError("n_window must be >= 2")
    return (2.0 * math.sqrt(math.pi) / 3.0) / math.sqrt(n_window)


@classified("Derived", note="COH-M6: global, model-based (assumes one tone); "
                            "distinct from the local, model-free COH-M5")
def phase_linearity(z: np.ndarray) -> float:
    """COH-M6. Phase-linearity score PL = |mean exp(i(phi_n - a n - b))|
    in [0, 1], (a, b) the least-squares line through the unwrapped phase.
    1 = perfectly linear phase; phase diffusion -> 0."""
    phi = instantaneous_phase(np.asarray(z, dtype=complex))
    if phi.size < 2:
        raise ValueError("need at least 2 samples")
    n = np.arange(phi.size, dtype=float)
    a, b = np.polyfit(n, phi, 1)
    resid = phi - (a * n + b)
    return float(np.abs(np.mean(np.exp(1j * resid))))


@classified("Derived", sources=("KOS-03", "KOS-10"),
            note="COH-M7: separates phase order from amplitude weighting; "
                 "divergence from plain C flags amplitude transients")
def amplitude_normalized_coherence(z: np.ndarray, fs: float,
                                   window_s: float = DEFAULT_WINDOW_S,
                                   hop_s: float = DEFAULT_HOP_S,
                                   floor: float = 1e-12
                                   ) -> tuple[np.ndarray, np.ndarray]:
    """COH-M7. Coherence series of the unit-magnitude signal
    u(t) = z(t)/max(|z(t)|, floor). Report alongside plain C_w."""
    z = np.asarray(z, dtype=complex)
    u = z / np.maximum(np.abs(z), floor)
    return coherence_series(u, fs, window_s, hop_s)


@classified("Derived", note="COH-M8: a band-power fraction, PROXY only — "
                            "not an occupation number of anything")
def band_power_fraction(z: np.ndarray, fs: float, f0: float,
                        bw: float) -> float:
    """COH-M8. Mode occupancy proxy: fraction of one-record power within
    [f0 - bw/2, f0 + bw/2] over total in [0, fs/2). In [0, 1]."""
    z = np.asarray(z, dtype=complex)
    if z.size == 0:
        raise ValueError("input record must be non-empty")
    spec = np.abs(np.fft.fft(z)) ** 2
    freqs = np.fft.fftfreq(z.size, d=1.0 / fs)
    pos = freqs >= 0.0
    band = pos & (np.abs(freqs - f0) <= bw / 2.0)
    tot = float(np.sum(spec[pos]))
    return float(np.sum(spec[band]) / tot) if tot > 0 else 0.0


@classified("Derived", note="COH-M9: theta_on and hold are protocol "
                            "parameters; resolution = hop")
def coherence_onset_time(tc: np.ndarray, c: np.ndarray, threshold: float,
                         hold: int = 3) -> float:
    """COH-M9. Onset time: earliest window centre where C >= threshold for
    `hold` consecutive windows. NaN if never (JSON callers serialize null)."""
    c = np.asarray(c)
    if hold < 1:
        raise ValueError("hold must be >= 1")
    for i in range(c.size - hold + 1):
        if np.all(c[i:i + hold] >= threshold):
            return float(np.asarray(tc)[i])
    return float("nan")


@classified("Derived", sources=("GAN-09",),
            note="COH-M10: exponential FORM only is the GAN-09 analogy; "
                 "the fitted tau_c is a bench parameter, never imported")
def coherence_decay_time(tc: np.ndarray, c: np.ndarray,
                         baseline: float) -> float:
    """COH-M10. Coherence decay time: exponential-fit tau of (C - baseline)
    on the falling segment from the global max of C to the first window
    with C <= baseline + 0.05 (or the end). NaN if < 3 windows."""
    from .models import fit_exponential_decay
    tc = np.asarray(tc)
    c = np.asarray(c)
    if tc.size == 0 or c.size == 0 or tc.size != c.size:
        raise ValueError("tc and c must be non-empty and equal-length "
                         "(QA-D-12)")
    i0 = int(np.argmax(c))
    below = np.where(c[i0:] <= baseline + 0.05)[0]
    i1 = i0 + int(below[0]) if below.size else c.size
    seg_t, seg_c = tc[i0:i1], c[i0:i1] - baseline
    if seg_t.size < 3:
        return float("nan")
    return fit_exponential_decay(seg_t, np.maximum(seg_c, 1e-9))["tau_s"]


@classified("Established", note="COH-M11: pairwise phase-locking value; "
                                "discard the initial transient before "
                                "averaging")
def phase_locking_value(phi_a: np.ndarray, phi_b: np.ndarray) -> float:
    """COH-M11. PLV = |mean exp(i(phi_a - phi_b))| in [0, 1]."""
    pa = np.asarray(phi_a)
    pb = np.asarray(phi_b)
    if pa.size == 0 or pa.shape != pb.shape:
        raise ValueError("phase arrays must be non-empty and equal-shaped")
    return float(np.abs(np.mean(np.exp(1j * (pa - pb)))))
