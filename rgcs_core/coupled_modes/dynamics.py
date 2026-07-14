"""Complex modal dynamics: Stuart-Landau form (RGCS-M.46..M.49).

Units: z_n in the declared campaign observable unit X; omega_n in rad/s;
gain/damping/coupling rates in 1/s; time in s.

The COMPLEX form RGCS-M.46 is integrated directly (the polar form is
singular at A -> 0 and is exactly equivalent otherwise):

    dz_n/dt = (G_n - gamma_n + i omega_n) z_n
              - sum_m beta_nm |z_m|^2 z_n + sum_m K_nm z_m

Classification: Hypothesis (H-09) as a physical model of RGCS crystals;
the mathematical structure (slowly-varying envelope / phase reduction of
weakly coupled, weakly nonlinear oscillators) is Established. Randomness
is seeded and reproducible (Euler-Maruyama with numpy default_rng).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..provenance import classified, classification_string

__all__ = ["integrate_stuart_landau", "stuart_landau_pair"]


@classified("Hypothesis", registry=("RGCS-M.46", "RGCS-M.49"),
            note="H-09 as RGCS physics; Established envelope math; complex "
                 "canonical form integrated (polar form singular at A -> 0)")
def integrate_stuart_landau(omega_rad_s: np.ndarray | list[float],
                            gain_s: np.ndarray | list[float],
                            damping_s: np.ndarray | list[float],
                            beta: np.ndarray | list[list[float]],
                            coupling_k_s: np.ndarray | list[list[float]],
                            z0: np.ndarray | list[complex],
                            fs_hz: float, n_samples: int,
                            noise: float = 0.0,
                            seed: int | None = None) -> dict[str, Any]:
    """Integrate the complex modal dynamics RGCS-M.46 by Euler-Maruyama.

    omega_rad_s: modal angular frequencies (rad/s), shape (M,).
    gain_s:      linear drive gain rates G_n (1/s), shape (M,).
    damping_s:   amplitude damping rates gamma_n = omega_n/(2 Q_n) (1/s,
                 RGCS-M.49), shape (M,).
    beta:        saturation coefficients beta_nm (1/(s X^2)), shape (M, M).
    coupling_k_s: symmetric (possibly complex) coupling rates K_nm
                 (rad/s), zero diagonal. Consistency with a
                 frequency-domain half-splitting g (Hz) requires the
                 anti-Hermitian form K_nm = i * 2*pi*g_nm (RGCS-M.46 /
                 QA-D-04): that choice gives spectral peaks at f0 +/- g
                 for a degenerate pair. Real-symmetric K instead splits
                 growth rates, not frequencies.
    z0:          initial complex amplitudes, shape (M,).
    noise:       additive complex white-noise strength (X/sqrt(s)); 0 gives
                 a fully deterministic trajectory.
    seed:        REQUIRED when noise > 0 (reproducible randomness).

    Returns t_s (s) and z, shape (n_samples, M) complex.
    Amplitude |z_n| and phase arg(z_n) are carried together and reported
    separately (KOS-03 lesson)."""
    omega = np.asarray(omega_rad_s, dtype=float)
    g = np.asarray(gain_s, dtype=float)
    gam = np.asarray(damping_s, dtype=float)
    b = np.asarray(beta, dtype=float)
    k = np.asarray(coupling_k_s, dtype=complex)
    z_init = np.asarray(z0, dtype=complex)
    m = omega.size
    for name, arr, shape in (("gain_s", g, (m,)), ("damping_s", gam, (m,)),
                             ("beta", b, (m, m)),
                             ("coupling_k_s", k, (m, m)),
                             ("z0", z_init, (m,))):
        if arr.shape != shape:
            raise ValueError(f"{name} must have shape {shape}")
    if not np.allclose(k, k.T, atol=1e-12):
        raise ValueError("coupling_k_s must be symmetric")
    if not (math.isfinite(fs_hz) and fs_hz > 0):
        raise ValueError("fs_hz must be positive")
    if n_samples < 2:
        raise ValueError("n_samples must be >= 2")
    if noise < 0:
        raise ValueError("noise must be >= 0")
    if noise > 0 and seed is None:
        raise ValueError("seed is required when noise > 0 "
                         "(reproducible randomness)")

    rng = np.random.default_rng(seed)
    dt = 1.0 / fs_hz
    sq = math.sqrt(dt)
    # Exponential integrating factor for the stiff linear part (exact for
    # the rotation/decay); explicit Euler-Maruyama for the nonlinear,
    # coupling, and noise terms. Plain Euler is unstable for omega*dt of
    # order 1e-2 over many samples.
    lin_prop = np.exp((g - gam + 1j * omega) * dt)
    z = np.empty((n_samples, m), dtype=complex)
    z[0] = z_init
    for i in range(1, n_samples):
        zp = z[i - 1]
        amp2 = np.abs(zp) ** 2
        step = lin_prop * zp + dt * (-(b @ amp2) * zp + k @ zp)
        if noise > 0:
            xi = (rng.standard_normal(m) + 1j * rng.standard_normal(m)) \
                / math.sqrt(2.0)
            step = step + noise * sq * xi
        z[i] = step
    return {
        "t_s": np.arange(n_samples) * dt,
        "z": z,
        "amplitude": np.abs(z),
        "phase_rad": np.angle(z),
        "classification": classification_string(integrate_stuart_landau),
    }


@classified("Derived", note="synthetic-data generator matching "
                            "tools/generate_golden_coherence.py exactly; "
                            "Hypothesis (DC-H2) as an RGCS physical model")
def stuart_landau_pair(rng: np.random.Generator, n: int, fs: float,
                       f1: float, f2: float, mu: float, coupling_k: float,
                       noise: float, a0: complex, b0: complex
                       ) -> tuple[np.ndarray, np.ndarray]:
    """Two diffusively coupled Stuart-Landau oscillators (Euler-Maruyama),
    an EXACT port of the golden-dataset generator:

        da/dt = (mu + i 2 pi f1) a - |a|^2 a + K (b - a) + noise xi_a
        db/dt = (mu + i 2 pi f2) b - |b|^2 b + K (a - b) + noise xi_b

    Phase reduction locks the pair when K >= K_c = pi |f1 - f2|."""
    dt = 1.0 / fs
    a = np.empty(n, complex)
    b = np.empty(n, complex)
    a[0], b[0] = a0, b0
    sq = math.sqrt(dt)
    for i in range(1, n):
        xa = (rng.standard_normal() + 1j * rng.standard_normal()) \
            / math.sqrt(2)
        xb = (rng.standard_normal() + 1j * rng.standard_normal()) \
            / math.sqrt(2)
        ap, bp = a[i - 1], b[i - 1]
        da = ((mu + 1j * 2 * np.pi * f1) * ap - (abs(ap) ** 2) * ap
              + coupling_k * (bp - ap))
        db = ((mu + 1j * 2 * np.pi * f2) * bp - (abs(bp) ** 2) * bp
              + coupling_k * (ap - bp))
        a[i] = ap + da * dt + noise * sq * xa
        b[i] = bp + db * dt + noise * sq * xb
    return a, b
