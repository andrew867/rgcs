"""Job worker functions. Executed in a separate *process* (spawn context);
they must stay importable module-level callables, must not touch Qt, and
communicate only through the JobContext.

Contract: ``worker(params: dict, ctx: JobContext) -> dict`` (JSON-able).
"""
from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Any

import numpy as np


class JobContext:
    """Passed to workers; wraps the IPC queue (progress + log messages)."""

    def __init__(self, queue, job_id: str):
        self._queue = queue
        self.job_id = job_id

    def progress(self, fraction: float) -> None:
        self._queue.put((self.job_id, "progress", float(fraction)))

    def log(self, message: str) -> None:
        self._queue.put((self.job_id, "log", str(message)))


def trivial_job(params: dict[str, Any], ctx: JobContext) -> dict[str, Any]:
    """Deterministic quick job used by smoke tests and the job-queue demo."""
    steps = int(params.get("steps", 5))
    delay_s = float(params.get("delay_s", 0.0))
    total = 0
    for i in range(steps):
        total += i
        if delay_s:
            time.sleep(delay_s)
        ctx.progress((i + 1) / steps)
        ctx.log(f"step {i + 1}/{steps}")
    return {"kind": "trivial", "steps": steps, "sum": total}


def failing_job(params: dict[str, Any], ctx: JobContext) -> dict[str, Any]:
    """Always raises; exercises the error-preserved-as-artifact path."""
    ctx.log("about to fail (intentional)")
    raise ValueError(params.get("message", "intentional failure"))


def _load_timeseries_csv(path: str) -> dict[str, np.ndarray]:
    """Load a CSV with a header row; returns column-name -> float array.

    Raises ValueError with a user-facing message for every malformed-input
    case (empty file, header-only, binary content, ragged/non-numeric
    rows, non-finite samples) — QA-D-06/13."""
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            try:
                header = next(reader)
            except StopIteration:
                raise ValueError(f"CSV file is empty: {path}") from None
            rows = []
            for lineno, row in enumerate(reader, start=2):
                if not row:
                    continue
                if len(row) != len(header):
                    raise ValueError(
                        f"CSV row {lineno} has {len(row)} fields, expected "
                        f"{len(header)} (columns: {', '.join(header)}): "
                        f"{path}")
                try:
                    rows.append([float(v) for v in row])
                except ValueError:
                    raise ValueError(
                        f"CSV row {lineno} contains a non-numeric value: "
                        f"{path}") from None
    except UnicodeDecodeError:
        raise ValueError(
            f"file is not a text CSV (binary or wrong encoding): "
            f"{path}") from None
    if not rows:
        raise ValueError(f"CSV has a header but no data rows: {path}")
    data = np.asarray(rows, dtype=float)
    if not np.all(np.isfinite(data)):
        bad = int(np.count_nonzero(~np.isfinite(data)))
        raise ValueError(
            f"CSV contains {bad} non-finite value(s) (NaN/inf); "
            f"clean the record before analysis: {path}")
    return {name: data[:, i] for i, name in enumerate(header)}


def coherence_analysis_job(params: dict[str, Any],
                           ctx: JobContext) -> dict[str, Any]:
    """Phase/coherence analysis of one time-series CSV via rgcs_core.coherence.

    params:
        csv_path        path to CSV (columns: t_s plus I/Q pair or one real col)
        signal_column   real signal column (analytic signal via Hilbert), or
        i_column/q_column   complex I/Q pair
        window_s, hop_s coherence window/hop (defaults = golden analysis params)
        max_points      plot decimation cap for stored series (default 4000)

    Callers must report (C, w, baseline) together — all three are returned.
    Output classification: Derived (Established signal-processing metrics
    applied to the given record); carries no evidential weight by itself.
    """
    from rgcs_core import coherence as coh
    from rgcs_core.provenance import MODEL_VERSION, sha256_file

    csv_path = params["csv_path"]
    window_s = float(params.get("window_s", coh.DEFAULT_WINDOW_S))
    hop_s = float(params.get("hop_s", coh.DEFAULT_HOP_S))
    max_points = int(params.get("max_points", 4000))

    ctx.log(f"loading {csv_path}")
    cols = _load_timeseries_csv(csv_path)
    if "t_s" not in cols:
        raise ValueError("CSV must contain a t_s column")
    t = cols["t_s"]
    if len(t) < 8:
        raise ValueError("time series too short")
    fs = float(params.get("fs_hz") or 1.0 / float(np.median(np.diff(t))))
    ctx.progress(0.1)

    i_col = params.get("i_column")
    q_col = params.get("q_column")
    sig_col = params.get("signal_column")
    if i_col and q_col:
        z = cols[i_col] + 1j * cols[q_col]
        source = f"I/Q columns {i_col}/{q_col}"
    else:
        if not sig_col:
            candidates = [c for c in cols if c != "t_s"]
            if not candidates:
                raise ValueError("no signal column found")
            sig_col = candidates[0]
        z = coh.analytic_signal(cols[sig_col])
        source = f"analytic signal of column {sig_col}"
    ctx.log(f"signal: {source}; fs = {fs:.1f} Hz; n = {len(z)}")
    ctx.progress(0.2)

    tc, c_series = coh.coherence_series(z, fs, window_s=window_s, hop_s=hop_s)
    n_window = max(int(round(window_s * fs)), 1)
    baseline = coh.noise_baseline_theory(n_window)
    ctx.progress(0.5)
    ctx.log(f"coherence: {len(c_series)} windows, baseline = {baseline:.4f}")

    phases = coh.instantaneous_phase(z)
    amp = np.abs(z)
    p_lin = coh.phase_linearity(z)
    rayleigh = coh.rayleigh_test(np.angle(np.exp(1j * phases)))
    ctx.progress(0.7)

    onset = coh.coherence_onset_time(tc, c_series, threshold=2.0 * baseline)
    decay = coh.coherence_decay_time(tc, c_series, baseline=baseline)
    ctx.progress(0.85)

    def _decimate(x: np.ndarray) -> list[float]:
        if len(x) <= max_points:
            return [float(v) for v in x]
        idx = np.linspace(0, len(x) - 1, max_points).astype(int)
        return [float(v) for v in x[idx]]

    result = {
        "kind": "coherence_analysis",
        "input": {"csv_path": str(csv_path),
                  "sha256": sha256_file(str(csv_path)),
                  "signal_source": source, "fs_hz": fs,
                  "n_samples": int(len(z))},
        "analysis_params": {"window_s": window_s, "hop_s": hop_s,
                            "n_window": n_window},
        # (C, w, baseline) reported together, per the coherence contract:
        "coherence": {"t_s": _decimate(tc), "c_w": _decimate(c_series),
                      "window_s": window_s, "baseline": float(baseline),
                      "c_max": float(np.max(c_series)),
                      "c_mean": float(np.mean(c_series))},
        "amplitude": {"t_s": _decimate(t), "a": _decimate(amp),
                      "a_rms": float(np.sqrt(np.mean(amp ** 2)))},
        "phase": {"t_s": _decimate(t), "phi_rad": _decimate(phases),
                  "phase_linearity": float(p_lin)},
        "rayleigh": {k: float(v) for k, v in rayleigh.items()},
        "onset_time_s": None if np.isnan(onset) else float(onset),
        "decay_time_s": None if np.isnan(decay) else float(decay),
        "software": {"rgcs_core_model_version": MODEL_VERSION},
        "classification": ("Derived (Established signal-processing metrics; "
                           "this analysis output is not evidence of any "
                           "physical hypothesis by itself)"),
    }
    ctx.progress(1.0)
    ctx.log("done")
    return result


def spectrum_job(params: dict[str, Any], ctx: JobContext) -> dict[str, Any]:
    """Compact-mode spectrum as a background job (also available inline)."""
    from rgcs_core.compact_modes import compact_mode_spectrum

    ctx.log("computing compact-mode spectrum")
    spec = compact_mode_spectrum(
        base_frequency_hz=float(params.get("base_frequency_hz", 0.0)),
        v_chi=params.get("v_chi"),
        compact_radius_mm=params.get("compact_radius_mm"),
        n_max=int(params.get("n_max", 12)),
        parity=params.get("parity", "all"),
        include_zero_mode=bool(params.get("include_zero_mode", True)),
        u_base_frequency_hz=float(params.get("u_base_frequency_hz", 0.0)))
    ctx.progress(1.0)
    return {"kind": "compact_mode_spectrum", "params": dict(params),
            "spectrum": spec}


#: registry of worker callables by dotted name (spawn-safe lookup)
WORKERS = {
    "trivial": trivial_job,
    "failing": failing_job,
    "coherence_analysis": coherence_analysis_job,
    "spectrum": spectrum_job,
}


def run_worker(worker_name: str, params: dict[str, Any], queue,
               job_id: str) -> None:
    """Process entry point (module-level, picklable under spawn)."""
    import traceback
    ctx = JobContext(queue, job_id)
    try:
        fn = WORKERS[worker_name]
        result = fn(params, ctx)
        from rgcs_core.provenance import to_jsonable
        queue.put((job_id, "result", to_jsonable(result)))
    except BaseException:
        queue.put((job_id, "error", traceback.format_exc()))
