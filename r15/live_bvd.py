"""P28 — live (streaming) impedance and incremental Butterworth-Van Dyke fitting.

This is the *live-fit* layer of the R15 electrical stack. It measures
nothing. What it does is stand up, in software, the machinery a live
resonator sweep would need: an impedance **stream** that delivers complex
samples one at a time, an **incremental** BVD fitter that re-estimates
``f_s, f_p, Q`` and the motional ``R, L, C`` with the static ``C0`` as the
stream fills in, a running convergence and uncertainty tracker that says
whether the fit is *settling* or *stable*, robust rejection of streaming
faults (dropouts and outlier spikes), a base-vs-extended model selection
that penalises over-parameterisation, and identifiability / multimodal
diagnostics that stop a poorly constrained fit from advancing a claim.

**The load-bearing line.** A live fit here converges to the parameters this
module *planted* in a synthetic impedance stream. No crystal was cut,
electroded, mounted or swept and no analyzer streamed anything, so a live
fit is a :class:`~r15.claims.ClaimClass.SYNTHETIC_OBSERVATION`, never a
measured device, and an *unconverged* fit is not a result at all.
:func:`refuse_live_synthetic_as_measured`, :func:`refuse_unconverged_as_result`
and :func:`refuse_poorly_identified` draw those lines, and a REAL stream
delivers nothing.

**Four honest stream modes.** ``REAL_STREAM`` is an interface only and
raises :class:`NoLiveHardwareError`; ``SYNTHETIC_STREAM`` progressively
samples a planted :class:`~r13.qcmstack.BVDResonator`; ``REPLAY_STREAM``
re-emits a recorded synthetic stream; ``FAULT_INJECTION_STREAM`` wraps a
synthetic stream and deterministically injects dropouts and outlier spikes
so the robust fitter can be exercised against known faults.

This module extends the R13 measurement stack -- it reuses
:func:`r13.qcmstack.fit_bvd` and :class:`r13.qcmstack.BVDResonator` for the
BVD fit and equivalent circuit -- and the R15 electrical lane
(:mod:`r15.electrical`) for the synthetic impedance sweep, the electrical
error budget and the observation record. It is typed against the R15 claim
taxonomy in :mod:`r15.claims`. It hard-imports no sibling R15 phase module
other than the electrical lane it builds on.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

import numpy as np

from r15 import claims
from r15 import electrical as E
from r13.qcmstack import BVDResonator, fit_bvd

# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "LIVE_BVD_TYPED_NO_DEVICE_SYNTHETIC_STREAM_CONVERGED"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
#: A real streaming sweep has been designed but not run.
PHYSICAL_RUN = "PREREGISTERED_NOT_RUN"

#: The ceiling for a live fit to a synthetic stream: a synthetic
#: observation, never a measurement.
FIT_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: The class of the streaming/fitting machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED


class LiveBVDError(RuntimeError):
    """Raised on any live-BVD refusal or structural guard."""


class NoLiveHardwareError(LiveBVDError):
    """Raised when a REAL_STREAM is asked to deliver samples.

    There is no impedance analyzer or crystal here, so a real stream
    delivers nothing. The stream is BLOCKED at the hardware-access boundary
    and the physical run is PREREGISTERED_NOT_RUN.
    """


class NotConvergedError(LiveBVDError):
    """Raised when an unconverged (or poorly identified) live fit is read as
    a result."""


def _finite(value: object, what: str) -> float:
    try:
        x = float(value)                              # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise LiveBVDError(f"cannot read {value!r} as {what}") from None
    if not math.isfinite(x):
        raise LiveBVDError(f"{what} must be finite, got {value!r}")
    return x


def _positive(value: object, what: str) -> float:
    x = _finite(value, what)
    if x <= 0.0:
        raise LiveBVDError(f"{what} must be positive, got {x!r}")
    return x


# --- (1) the impedance stream and its four modes -------------------------

class StreamMode(Enum):
    """The four modes behind the one impedance-stream interface."""

    REAL_STREAM = "REAL_STREAM"
    SYNTHETIC_STREAM = "SYNTHETIC_STREAM"
    REPLAY_STREAM = "REPLAY_STREAM"
    FAULT_INJECTION_STREAM = "FAULT_INJECTION_STREAM"


def _progressive_order(n: int) -> list[int]:
    """A progressive (coarse-to-fine) visiting order over ``range(n)``.

    A live sweep refines its coverage over time: it first spans the whole
    band coarsely, then fills in denser and denser detail. This returns the
    endpoints first, then recursively the midpoints, so a fit becomes
    possible early (from a coarse sweep) and converges as density grows.
    Deterministic; a permutation of ``range(n)``.
    """
    if n <= 0:
        raise LiveBVDError("a stream needs at least one point")
    if n == 1:
        return [0]
    order = [0, n - 1]
    seen = {0, n - 1}
    q: deque[tuple[int, int]] = deque([(0, n - 1)])
    while q:
        lo, hi = q.popleft()
        mid = (lo + hi) // 2
        if lo < mid < hi and mid not in seen:
            seen.add(mid)
            order.append(mid)
            q.append((lo, mid))
            q.append((mid, hi))
    for i in range(n):
        if i not in seen:
            seen.add(i)
            order.append(i)
    return order


class ImpedanceStream:
    """Base of the one live impedance-stream interface. Not used directly."""

    def __init__(self, stream_id: str, mode: StreamMode) -> None:
        self.stream_id = str(stream_id)
        self.mode = mode

    def samples(self) -> Iterator[tuple[float, complex]]:
        raise NotImplementedError

    def as_list(self) -> list[tuple[float, complex]]:
        return list(self.samples())


class RealImpedanceStream(ImpedanceStream):
    """A real live stream with no analyzer behind it.

    Delivering a sample acquires nothing: it raises
    :class:`NoLiveHardwareError`. The stream offers :meth:`blocked_receipt`
    so callers record the honest PREREGISTERED_NOT_RUN state.
    """

    def __init__(self, stream_id: str = "real_impedance_stream") -> None:
        super().__init__(stream_id, StreamMode.REAL_STREAM)

    def samples(self) -> Iterator[tuple[float, complex]]:
        raise NoLiveHardwareError(
            f"refused: {self.stream_id} is a REAL_STREAM and no impedance "
            f"analyzer or crystal exists in this repository, so it delivers "
            f"NOTHING. The stream is BLOCKED at the hardware-access boundary, "
            f"not faked. A physical stream is {PHYSICAL_RUN}; the live BVD "
            f"parameters are BLOCKED_MISSING_INPUT pending a built, "
            f"calibrated instrument. {PHYSICAL_VALIDATION}. {VERDICT}")

    def blocked_receipt(self) -> dict:
        """The honest BLOCKED / PREREGISTERED_NOT_RUN receipt for a real stream."""
        return {
            "stream_id": self.stream_id,
            "mode": self.mode.value,
            "status": "BLOCKED",
            "reason": ("no impedance analyzer or crystal present; the live "
                       "stream delivers nothing"),
            "acquired": False,
            "n_samples": 0,
            "claim_class": "BLOCKED_MISSING_INPUT",
            "physical_run": PHYSICAL_RUN,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class SyntheticImpedanceStream(ImpedanceStream):
    """A deterministic synthetic impedance stream from a planted resonator.

    Builds a full complex sweep with :func:`r15.electrical.synthetic_electrical_sweep`
    and emits it one sample at a time in a progressive (coarse-to-fine)
    order. Same seed => identical stream. Each sample is a
    ``SYNTHETIC_OBSERVATION``; nothing is streamed from a device.
    """

    def __init__(self, resonator: BVDResonator = E.DEFAULT_RESONATOR, *,
                 stream_id: str = "synthetic_impedance_stream",
                 n: int = 8001, seed: int = 0, noise: float = 0.0,
                 fixture: "E.FixtureModel | None" = None,
                 progressive: bool = True) -> None:
        super().__init__(stream_id, StreamMode.SYNTHETIC_STREAM)
        if not isinstance(resonator, BVDResonator):
            raise LiveBVDError("SyntheticImpedanceStream needs a BVDResonator")
        data = E.synthetic_electrical_sweep(resonator, fixture=fixture,
                                            n=int(n), seed=int(seed),
                                            noise=float(noise))
        self.resonator = resonator
        self.seed = int(seed)
        self._freqs = np.asarray(data["freqs_hz"], dtype=float)
        self._Z = np.asarray(data["Z"], dtype=complex)
        self._true = {
            "R": data["true_R"], "L": data["true_L"], "C": data["true_C"],
            "C0": data["true_C0"], "f_s_hz": data["true_f_s"],
            "f_p_hz": data["true_f_p"], "Q": data["true_Q"],
        }
        self._order = (_progressive_order(self._freqs.size) if progressive
                       else list(range(self._freqs.size)))

    def samples(self) -> Iterator[tuple[float, complex]]:
        for i in self._order:
            yield float(self._freqs[i]), complex(self._Z[i])

    def planted(self) -> dict:
        """The planted BVD parameters a live fit should converge to."""
        return dict(self._true)


class ReplayImpedanceStream(ImpedanceStream):
    """Re-emits a recorded (synthetic) stream sample-for-sample.

    It reads back what was stored and streams nothing new; each sample is a
    ``SYNTHETIC_OBSERVATION`` of a recorded artifact.
    """

    def __init__(self, recorded: list[tuple[float, complex]], *,
                 stream_id: str = "replay_impedance_stream") -> None:
        super().__init__(stream_id, StreamMode.REPLAY_STREAM)
        self._recorded = [(float(f), complex(z)) for f, z in recorded]
        if not self._recorded:
            raise LiveBVDError("a replay stream needs a recorded stream")

    def samples(self) -> Iterator[tuple[float, complex]]:
        for f, z in self._recorded:
            yield f, z


class StreamFault(Enum):
    """The two ordinary *streaming* faults this layer injects and rejects."""

    DROPOUT = "dropout"        # a sample is lost (delivered non-finite)
    OUTLIER_SPIKE = "outlier_spike"   # a sample's magnitude spikes


class FaultInjectionImpedanceStream(ImpedanceStream):
    """Wraps a synthetic stream and injects dropouts and outlier spikes.

    Deterministic under ``seed``: dropouts deliver a non-finite sample (a
    lost packet), outlier spikes multiply a sample's complex value by
    ``spike_gain`` so its magnitude is locally anomalous. The robust fitter
    must reject both without letting one bad sample wreck the fit.
    """

    def __init__(self, inner: SyntheticImpedanceStream, *,
                 outlier_fraction: float = 0.01, spike_gain: float = 50.0,
                 dropout_fraction: float = 0.0, seed: int = 0,
                 stream_id: str = "fault_impedance_stream") -> None:
        super().__init__(stream_id, StreamMode.FAULT_INJECTION_STREAM)
        if not isinstance(inner, SyntheticImpedanceStream):
            raise LiveBVDError(
                "FaultInjectionImpedanceStream wraps a SyntheticImpedanceStream")
        if not 0.0 <= outlier_fraction < 0.5:
            raise LiveBVDError("outlier_fraction must be in [0, 0.5)")
        if not 0.0 <= dropout_fraction < 0.5:
            raise LiveBVDError("dropout_fraction must be in [0, 0.5)")
        if abs(float(spike_gain)) <= 1.0:
            raise LiveBVDError("spike_gain must have magnitude > 1 to spike")
        base = inner.as_list()
        n = len(base)
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), 0x0F]))
        k_out = int(round(float(outlier_fraction) * n))
        k_drop = int(round(float(dropout_fraction) * n))
        chosen = rng.choice(n, size=min(k_out + k_drop, n), replace=False)
        out_idx = set(int(i) for i in chosen[:k_out])
        drop_idx = set(int(i) for i in chosen[k_out:k_out + k_drop])
        samples: list[tuple[float, complex]] = []
        for i, (f, z) in enumerate(base):
            if i in drop_idx:
                samples.append((f, complex(math.nan, math.nan)))
            elif i in out_idx:
                samples.append((f, z * float(spike_gain)))
            else:
                samples.append((f, z))
        self._samples = samples
        self.inner = inner
        self.n_outliers = len(out_idx)
        self.n_dropouts = len(drop_idx)
        self.faults = tuple(
            f for f, k in ((StreamFault.OUTLIER_SPIKE, k_out),
                           (StreamFault.DROPOUT, k_drop)) if k > 0)

    def samples(self) -> Iterator[tuple[float, complex]]:
        for f, z in self._samples:
            yield f, z

    def planted(self) -> dict:
        return self.inner.planted()


# --- (2) the incremental fit estimate and convergence state --------------

@dataclass(frozen=True)
class FitEstimate:
    """One incremental BVD estimate over the accepted stream so far.

    Recovered from a synthetic stream, so it is a ``SYNTHETIC_OBSERVATION``,
    never a measured device.
    """

    f_s_hz: float
    f_p_hz: float
    Q: float
    R: float
    L: float
    C: float
    C0: float
    fwhm_hz: float
    n_points: int
    residual_rms: float
    relative_uncertainty: float
    claim_class: claims.ClaimClass = FIT_CLAIM_CLASS

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            claims.refuse_synthetic_as_physical()

    def as_dict(self) -> dict:
        return {
            "f_s_hz": float(self.f_s_hz),
            "f_p_hz": float(self.f_p_hz),
            "Q": float(self.Q),
            "R": float(self.R),
            "L": float(self.L),
            "C": float(self.C),
            "C0": float(self.C0),
            "fwhm_hz": float(self.fwhm_hz),
            "n_points": int(self.n_points),
            "residual_rms": float(self.residual_rms),
            "relative_uncertainty": float(self.relative_uncertainty),
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


@dataclass(frozen=True)
class ConvergenceState:
    """Whether the running fit is settling or stable.

    ``converged`` is true only once the key parameters have stopped moving
    (relative change below ``tolerance`` over ``window`` consecutive
    updates) *and* the fit is identifiable. ``settling`` means an estimate
    exists but is still moving.
    """

    converged: bool
    settling: bool
    identifiable: bool
    n_updates: int
    relative_change: float
    tolerance: float
    window: int

    def as_dict(self) -> dict:
        return {
            "converged": bool(self.converged),
            "settling": bool(self.settling),
            "identifiable": bool(self.identifiable),
            "n_updates": int(self.n_updates),
            "relative_change": (None if not math.isfinite(self.relative_change)
                                else float(self.relative_change)),
            "tolerance": float(self.tolerance),
            "window": int(self.window),
        }


_UNSTARTED = ConvergenceState(
    converged=False, settling=False, identifiable=False, n_updates=0,
    relative_change=math.inf, tolerance=0.0, window=0)


# --- (3) robust streaming outlier rejection (Hampel) ---------------------

def hampel_mask(values, window: int = 7, k: float = 6.0) -> np.ndarray:
    """A boolean *keep* mask: ``True`` for inliers, ``False`` for spikes.

    A Hampel filter over frequency-sorted magnitudes: each point is compared
    to the local median of a window of radius ``window``; a deviation beyond
    ``k`` local (MAD-scaled) standard deviations is an isolated spike and is
    rejected. A smooth resonance -- a cluster of many elevated points -- is
    kept; a single anomalous sample is not.
    """
    x = np.asarray(values, dtype=float)
    n = x.size
    keep = np.ones(n, dtype=bool)
    if n == 0:
        return keep
    w = max(1, int(window))
    kk = _positive(k, "the Hampel k")
    for i in range(n):
        lo = max(0, i - w)
        hi = min(n, i + w + 1)
        win = x[lo:hi]
        med = float(np.median(win))
        mad = 1.4826 * float(np.median(np.abs(win - med)))
        dev = abs(float(x[i]) - med)
        eps = 1e-9 * (abs(med) + 1e-30)
        if dev > eps and dev > kk * mad:
            keep[i] = False
    return keep


# --- (4) identifiability and multimodal diagnostics ----------------------

def detect_multimodal(freqs, Z, *, rel_height: float = 0.5,
                      min_separation_frac: float = 0.01) -> dict:
    """Detect a multimodal conductance spectrum (more than one resonance).

    The motional conductance ``G = Re(1/Z)`` peaks at each resonance. If a
    second peak reaches ``rel_height`` of the tallest and is separated from
    it by more than ``min_separation_frac`` of the span, the spectrum is
    multimodal and a single-BVD fit is not well posed.
    """
    f = np.asarray(freqs, dtype=float)
    z = np.asarray(Z, dtype=complex)
    if f.shape != z.shape or f.ndim != 1 or f.size < 8:
        raise LiveBVDError("detect_multimodal needs matching 1-D arrays >= 8")
    order = np.argsort(f)
    f = f[order]
    g = np.real(1.0 / z[order])
    peaks = [i for i in range(1, f.size - 1)
             if g[i] > g[i - 1] and g[i] >= g[i + 1]]
    if not peaks:
        return {"multimodal": False, "n_peaks": 0, "peak_freqs_hz": []}
    peaks.sort(key=lambda i: g[i], reverse=True)
    top = peaks[0]
    g_top = float(g[top])
    span = float(f[-1] - f[0]) or 1.0
    modes = [top]
    for i in peaks[1:]:
        if g[i] < rel_height * g_top:
            break
        if all(abs(f[i] - f[j]) > min_separation_frac * span for j in modes):
            modes.append(i)
    modes.sort()
    return {
        "multimodal": bool(len(modes) > 1),
        "n_peaks": len(modes),
        "peak_freqs_hz": [float(f[i]) for i in modes],
    }


def identifiability(freqs, Z, estimate: FitEstimate, *,
                    min_points_across_fwhm: int = 5,
                    min_off_resonance: int = 4) -> dict:
    """Whether a BVD fit is well constrained by the accepted samples.

    ``f_s`` and ``Q`` are only identifiable if the resonance is resolved by
    several samples across its FWHM; ``C0`` needs off-resonance samples; and
    a multimodal spectrum is not a single BVD. A fit that fails any of these
    is *poorly identified* and cannot advance a claim.
    """
    f = np.asarray(freqs, dtype=float)
    z = np.asarray(Z, dtype=complex)
    fwhm = float(estimate.fwhm_hz)
    f_s = float(estimate.f_s_hz)
    across = int(np.count_nonzero(np.abs(f - f_s) <= 0.5 * fwhm))
    off = int(np.count_nonzero(np.abs(f - f_s) > 10.0 * fwhm))
    mm = detect_multimodal(f, z) if f.size >= 8 else {"multimodal": False}
    ident = (across >= min_points_across_fwhm and off >= min_off_resonance
             and not mm["multimodal"])
    return {
        "identifiable": bool(ident),
        "points_across_fwhm": across,
        "off_resonance_points": off,
        "multimodal": bool(mm["multimodal"]),
    }


# --- (5) base vs extended model selection --------------------------------

def _bvd_admittance(params: dict, freqs: np.ndarray) -> np.ndarray:
    """The BVD admittance ``Y = 1/Z`` for ``R, L, C, C0`` over ``freqs``."""
    res = BVDResonator(R=params["R"], L=params["L"], C=params["C"],
                       C0=params["C0"])
    return 1.0 / res.impedance(freqs)


def select_model(freqs, Z) -> dict:
    """Select between the base BVD and an extended (BVD + leakage) model.

    The extended model adds one free parameter -- a static leakage
    conductance ``G0`` in parallel with ``C0`` -- so it can only fit the data
    at least as well as the base model. A Bayesian information criterion
    ``BIC = n ln(RSS/n) + k ln n`` penalises the extra parameter, so on data
    that is truly a plain BVD the base model is selected: over-parameterisation
    does not win.
    """
    f = np.asarray(freqs, dtype=float)
    z = np.asarray(Z, dtype=complex)
    if f.shape != z.shape or f.ndim != 1 or f.size < 64:
        raise LiveBVDError("select_model needs matching 1-D arrays >= 64")
    fit = fit_bvd(f, z)
    y_data = 1.0 / z
    y_base = _bvd_admittance(fit, f)
    n = f.size
    rss_base = float(np.sum(np.abs(y_data - y_base) ** 2))
    # extended: add the best real leakage conductance G0 (linear in Y)
    g0 = float(np.mean(np.real(y_data - y_base)))
    y_ext = y_base + g0
    rss_ext = float(np.sum(np.abs(y_data - y_ext) ** 2))
    k_base, k_ext = 4, 5
    tiny = 1e-300

    def _bic(rss: float, k: int) -> float:
        return n * math.log(max(rss, tiny) / n) + k * math.log(n)

    bic_base = _bic(rss_base, k_base)
    bic_ext = _bic(rss_ext, k_ext)
    selected = "BVD" if bic_base <= bic_ext else "BVD_EXTENDED"
    return {
        "selected": selected,
        "bic_bvd": bic_base,
        "bic_bvd_extended": bic_ext,
        "rss_bvd": rss_base,
        "rss_bvd_extended": rss_ext,
        "leakage_conductance_g0": g0,
        "n_points": n,
        "claim_class": FIT_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "note": ("model selection over a SYNTHETIC stream; the extended "
                 "model's extra parameter is BIC-penalised, so a plain BVD "
                 "is not over-fit"),
    }


# --- (6) the live, incremental BVD fitter --------------------------------

class LiveBVDFitter:
    """An incremental BVD fitter over a live impedance stream.

    Samples are pushed one at a time. Non-finite or zero samples are counted
    as dropouts and dropped; the remainder are frequency-sorted and passed
    through a Hampel filter that rejects outlier spikes; the surviving
    inliers are fit with :func:`r13.qcmstack.fit_bvd`. The fit is re-run as
    the stream fills in, and a running convergence tracker reports whether it
    is *settling* or *stable*. Every estimate is a ``SYNTHETIC_OBSERVATION``.
    """

    def __init__(self, *, min_points: int = 256, refit_interval: int = 256,
                 hampel_window: int = 7, hampel_k: float = 6.0,
                 convergence_tol: float = 1e-3, convergence_window: int = 2,
                 budget_id: str = "P28_live_bvd") -> None:
        self.min_points = max(64, int(min_points))
        self.refit_interval = max(1, int(refit_interval))
        self.hampel_window = max(1, int(hampel_window))
        self.hampel_k = _positive(hampel_k, "hampel_k")
        self.convergence_tol = _positive(convergence_tol, "convergence_tol")
        self.convergence_window = max(1, int(convergence_window))
        self.budget_id = str(budget_id)
        self._freqs: list[float] = []
        self._Z: list[complex] = []
        self._n_pushed = 0
        self._n_dropout = 0
        self._n_rejected = 0
        self._since_refit = 0
        self._estimate: FitEstimate | None = None
        self._ident: dict | None = None
        self._fs_history: list[float] = []
        self._rel_changes: list[float] = []
        self._n_updates = 0

    # -- ingestion --------------------------------------------------------

    def push(self, freq: float, Z: complex) -> None:
        """Push one live sample; refit when enough new samples accumulate."""
        self._n_pushed += 1
        try:
            f = float(freq)
            z = complex(Z)
        except (TypeError, ValueError):
            self._n_dropout += 1
            return
        if not (math.isfinite(f) and math.isfinite(z.real)
                and math.isfinite(z.imag)) or z == 0:
            self._n_dropout += 1
            return
        self._freqs.append(f)
        self._Z.append(z)
        self._since_refit += 1
        if (len(self._freqs) >= self.min_points
                and self._since_refit >= self.refit_interval):
            self._since_refit = 0
            self._try_refit()

    def run(self, stream: ImpedanceStream) -> "LiveBVDFitter":
        """Push an entire stream, then run a final refit. Returns self."""
        for f, z in stream.samples():
            self.push(f, z)
        self._try_refit()
        return self

    # -- the incremental refit -------------------------------------------

    def _try_refit(self) -> None:
        if len(self._freqs) < 64:
            return
        f = np.asarray(self._freqs, dtype=float)
        z = np.asarray(self._Z, dtype=complex)
        order = np.argsort(f)
        f, z = f[order], z[order]
        keep = hampel_mask(np.abs(z), self.hampel_window, self.hampel_k)
        self._n_rejected = int(np.count_nonzero(~keep))
        ff, zz = f[keep], z[keep]
        if ff.size < 64:
            return
        try:
            fit = fit_bvd(ff, zz)
        except Exception:
            # not yet fittable (e.g. the peak is not resolved): still settling
            return
        res = BVDResonator(R=fit["R"], L=fit["L"], C=fit["C"], C0=fit["C0"])
        resid = zz - res.impedance(ff)
        rms = float(np.sqrt(np.mean(np.abs(resid) ** 2)))
        self._n_updates += 1
        f_s = float(fit["f_s_hz"])
        if self._fs_history:
            rel = abs(f_s - self._fs_history[-1]) / (abs(f_s) or 1.0)
        else:
            rel = math.inf
        self._fs_history.append(f_s)
        self._rel_changes.append(rel)
        rel_unc = self._running_uncertainty()
        self._estimate = FitEstimate(
            f_s_hz=f_s, f_p_hz=float(fit["f_p_hz"]), Q=float(fit["Q"]),
            R=float(fit["R"]), L=float(fit["L"]), C=float(fit["C"]),
            C0=float(fit["C0"]), fwhm_hz=float(fit["fwhm_hz"]),
            n_points=int(ff.size), residual_rms=rms,
            relative_uncertainty=rel_unc)
        self._ident = identifiability(ff, zz, self._estimate)

    def _running_uncertainty(self) -> float:
        """A running relative uncertainty on ``f_s``.

        Combines the modelled electrical error budget (in quadrature) with
        the observed run-to-run scatter of ``f_s`` over the recent window.
        A modelled/observed dispersion, not a measured uncertainty.
        """
        budget = E.electrical_error_budget(self.budget_id)
        base = float(budget["combined_uncertainty"])
        recent = self._fs_history[-(self.convergence_window + 1):]
        if len(recent) >= 2:
            arr = np.asarray(recent, dtype=float)
            scatter = float(np.std(arr) / (abs(np.mean(arr)) or 1.0))
        else:
            scatter = 0.0
        return math.sqrt(base * base + scatter * scatter)

    # -- state ------------------------------------------------------------

    @property
    def estimate(self) -> FitEstimate | None:
        return self._estimate

    @property
    def n_rejected(self) -> int:
        return self._n_rejected

    @property
    def n_dropout(self) -> int:
        return self._n_dropout

    @property
    def n_pushed(self) -> int:
        return self._n_pushed

    @property
    def convergence(self) -> ConvergenceState:
        if self._estimate is None:
            return _UNSTARTED
        window = self.convergence_window
        trailing = self._rel_changes[-window:]
        stable = (len(trailing) >= window
                  and all(r < self.convergence_tol for r in trailing))
        ident = bool(self._ident and self._ident["identifiable"])
        converged = bool(stable and ident)
        return ConvergenceState(
            converged=converged, settling=not converged, identifiable=ident,
            n_updates=self._n_updates,
            relative_change=self._rel_changes[-1] if self._rel_changes
            else math.inf,
            tolerance=self.convergence_tol, window=window)

    # -- the result / fit receipt ----------------------------------------

    def result(self) -> dict:
        """The converged live-fit receipt; refuses an unconverged fit.

        Raises :class:`NotConvergedError` if no estimate exists, if the fit
        is still settling, or if it is poorly identified: an unconverged or
        poorly identified live fit is not a result.
        """
        conv = self.convergence
        if self._estimate is None:
            raise NotConvergedError(
                "refused: no live BVD estimate exists yet; the stream has not "
                "delivered enough inliers to resolve a resonance. An absent "
                f"fit is not a result. {PHYSICAL_VALIDATION}. {VERDICT}")
        if not conv.converged:
            reason = ("still settling" if conv.identifiable
                      else "poorly identified")
            raise NotConvergedError(
                f"refused: the live BVD fit is {reason} "
                f"(relative_change={conv.relative_change:g}, "
                f"tol={self.convergence_tol:g}, "
                f"identifiable={conv.identifiable}); an unconverged or poorly "
                f"identified fit is not a result and cannot advance a claim. "
                f"{PHYSICAL_VALIDATION}. {VERDICT}")
        return self.fit_receipt()

    def fit_receipt(self) -> dict:
        """A structured live-fit receipt with estimate, convergence and residuals."""
        est = self._estimate
        conv = self.convergence
        return {
            "fit_id": "P28_live_bvd_fit",
            "estimate": est.as_dict() if est else None,
            "convergence": conv.as_dict(),
            "identifiability": dict(self._ident) if self._ident else None,
            "counts": {
                "n_pushed": self._n_pushed,
                "n_dropout": self._n_dropout,
                "n_rejected_outliers": self._n_rejected,
                "n_accepted": est.n_points if est else 0,
                "n_updates": self._n_updates,
            },
            "residual_rms": est.residual_rms if est else None,
            "claim_class": FIT_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "note": ("a live fit to a SYNTHETIC impedance stream planted in "
                     "this module; not a measurement of any crystal"),
        }

    def observation_record(self, *, observation_id: str = "P28_obs_f_s",
                           run_id: str = "P28_live_run") -> dict:
        """A schema-shaped observation record for the live series resonance.

        Reuses :func:`r15.electrical.observation_record`. The value is
        recovered from a synthetic stream, so it is a
        ``SYNTHETIC_OBSERVATION``, not a measurement.
        """
        if self._estimate is None:
            raise NotConvergedError(
                "refused: no live estimate to record; nothing has converged")
        rec = E.observation_record({"f_s_hz": self._estimate.f_s_hz},
                                   observation_id=observation_id,
                                   run_id=run_id)
        rec["analysis_version"] = "r15.live_bvd.LiveBVDFitter/1"
        rec["source_artifacts"] = ["synthetic_impedance_stream(seed)"]
        return rec


# --- (7) the load-bearing refusals ---------------------------------------

def refuse_unconverged_as_result(
        detail: str = "an unconverged live BVD fit") -> None:
    """Refuse an unconverged (or poorly identified) live fit as a result.

    A live fit is only a result once it has stopped moving *and* is
    identifiable. A settling or poorly identified fit is provisional; reading
    it as a settled result is refused.
    """
    raise NotConvergedError(
        f"refused: {detail!r} is provisional -- the running fit has not "
        f"converged (its parameters are still moving or the resonance is not "
        f"resolved). It is a settling {FIT_CLAIM_CLASS.value}, not a result, "
        f"and cannot advance a claim. {PHYSICAL_VALIDATION}. {VERDICT}")


def refuse_poorly_identified(
        detail: str = "a poorly identified live BVD fit") -> None:
    """Refuse a poorly identified fit as advancing a claim. Always raises."""
    raise NotConvergedError(
        f"refused: {detail!r} is poorly identified -- too few samples across "
        f"the resonance, too few off-resonance samples, or a multimodal "
        f"spectrum. A fit that is not constrained by the data cannot advance "
        f"a claim. {PHYSICAL_VALIDATION}. {VERDICT}")


def refuse_live_synthetic_as_measured(
        quantity: str = "a live-fitted BVD parameter") -> None:
    """Refuse a live synthetic fit read as a measured device. Always raises.

    A live fit converges to the parameters this module *planted* in a
    synthetic stream. No crystal, impedance analyzer or streaming acquisition
    exists here, so the live ``R, L, C, C0, f_s, f_p, Q`` describe a model,
    not a device. Delegates to the governance core so the refusal is the
    canonical one.
    """
    try:
        claims.refuse_synthetic_as_physical()
    except claims.ClaimError as exc:
        raise LiveBVDError(
            f"refused: {quantity!r} is recovered from a live SYNTHETIC "
            f"impedance stream planted in this module, not streamed from a "
            f"device. {exc} A measured device's live BVD parameters are "
            f"{PHYSICAL_RUN} / BLOCKED_MISSING_INPUT. {PHYSICAL_VALIDATION}. "
            f"{VERDICT}") from exc


# --- (8) the report ------------------------------------------------------

def live_bvd_report() -> dict:
    """The standing statement of what the live-BVD layer is and is not."""
    return {
        "what_this_is": (
            "the R15 live (streaming) impedance and incremental "
            "Butterworth-Van Dyke fitting layer: an impedance stream with "
            "four modes (real/synthetic/replay/fault-injection), an "
            "incremental BVD fitter that re-estimates f_s, f_p, Q and the "
            "motional R, L, C with the static C0 as the stream fills in, a "
            "running convergence and uncertainty tracker (settling vs "
            "stable), robust Hampel rejection of dropouts and outlier spikes, "
            "a base-vs-extended model selection that penalises "
            "over-parameterisation, and identifiability / multimodal "
            "diagnostics"),
        "stream_modes": [m.value for m in StreamMode],
        "stream_faults": [f.value for f in StreamFault],
        "reuses": [
            "r13.qcmstack.fit_bvd / BVDResonator (BVD fit + equivalent circuit)",
            "r15.electrical.synthetic_electrical_sweep / electrical_error_budget "
            "/ observation_record (synthetic sweep, budget, record)",
            "r15.claims (claim taxonomy and forbidden promotions)",
        ],
        "refusals": [
            "REAL_STREAM.samples raises NoLiveHardwareError (delivers nothing; "
            "PREREGISTERED_NOT_RUN)",
            "LiveBVDFitter.result refuses an unconverged or poorly identified "
            "fit (NotConvergedError)",
            "refuse_unconverged_as_result",
            "refuse_poorly_identified",
            "refuse_live_synthetic_as_measured",
        ],
        "fit_claim_class": FIT_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "physical_run": PHYSICAL_RUN,
        "hardware_status": (
            "no impedance analyzer or crystal exists here; a REAL_STREAM is "
            "BLOCKED and delivers nothing"),
        "what_would_change_this": (
            "a physical crystal streamed on a calibrated impedance analyzer, "
            "its raw complex samples captured live with a clock binding and an "
            "environment log, each with its uncertainty and its null -- none "
            "of which exists in this repository"),
        "what_this_does_not_say": (
            "It does not say any crystal was measured. A synthetic stream is "
            "simulator output and a live BVD fit converges to parameters this "
            "module PLANTED; a REAL_STREAM delivers nothing, an unconverged "
            "fit is not a result, and a SYNTHETIC_OBSERVATION is never a "
            "PHYSICAL_MEASUREMENT. PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "PHYSICAL_RUN",
    "FIT_CLAIM_CLASS", "SOFTWARE_CLAIM_CLASS",
    "LiveBVDError", "NoLiveHardwareError", "NotConvergedError",
    "StreamMode", "StreamFault", "ImpedanceStream", "RealImpedanceStream",
    "SyntheticImpedanceStream", "ReplayImpedanceStream",
    "FaultInjectionImpedanceStream",
    "FitEstimate", "ConvergenceState", "hampel_mask", "detect_multimodal",
    "identifiability", "select_model", "LiveBVDFitter",
    "refuse_unconverged_as_result", "refuse_poorly_identified",
    "refuse_live_synthetic_as_measured", "live_bvd_report",
]
