#!/usr/bin/env python3
"""Generate small SYNTHETIC sample datasets for two protocol branches.

Branches covered:
  1. modal_survey  - tap response, 3 real channels (mic, accelerometer, force)
  2. opposed_coil  - single-shot baseband I/Q record around a 4096 Hz LO with
                     a half-spacing (46/23/92) drive envelope and post-drive
                     ringdown (acquisition extends 4.43x past drive-off)

Everything is seeded and reproducible. The data are simulation products for
pipeline/schema testing ONLY (provenance.synthetic = true); they carry no
evidential weight and must never appear in results. Golden-value coherence
datasets live in experiments/sample_data/golden_coherence/ (Agent 03, do not
touch).

Run:  python3 experiments/sample_data/make_samples.py
Then: python3 experiments/schemas/validate.py
"""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20260714
SCHEMA_VERSION = "1.0.0"
PROTOCOL_VERSION = "1.0.0"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, header: list, arrays: list) -> None:
    data = np.column_stack(arrays)
    np.savetxt(path, data, delimiter=",", fmt="%.6e",
               header=",".join(header), comments="")


# ---------------------------------------------------------------- branch 1
def make_modal_survey():
    rng = np.random.default_rng(SEED)
    fs = 32768.0
    n = 8192                      # 0.25 s
    t = np.arange(n) / fs
    t_tap = 0.005

    # Three decaying modes below Nyquist. 10042.677 Hz is the compact-term
    # golden value (G-06) used purely as a recognizable synthetic frequency.
    modes = [           # (f_hz, amp, tau_s) -> tau = Q/(pi f)
        (4096.0, 1.00, 0.060),
        (10042.677, 0.45, 0.035),
        (12288.0, 0.25, 0.020),
    ]
    resp = np.zeros(n)
    for f_hz, amp, tau in modes:
        phase = rng.uniform(0, 2 * np.pi)
        env = np.where(t >= t_tap, np.exp(-(t - t_tap) / tau), 0.0)
        resp += amp * env * np.sin(2 * np.pi * f_hz * (t - t_tap) + phase)

    mic = resp + 0.01 * rng.standard_normal(n)
    accel = 0.7 * resp + 0.02 * rng.standard_normal(n)
    force = np.where((t >= t_tap) & (t < t_tap + 0.0008),
                     5.0 * np.sin(np.pi * (t - t_tap) / 0.0008) ** 2, 0.0)
    force += 0.002 * rng.standard_normal(n)

    csv = HERE / "modal_survey_response.csv"
    write_csv(csv, ["t_s", "mic_v", "accel_m_s2", "force_n"],
              [t, mic, accel, force])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "RUN-SAMPLE-MODAL-0001",
        "session_id": "SES-SAMPLE-SYNTH",
        "protocol_branch": "modal_survey",
        "protocol_version": PROTOCOL_VERSION,
        "hypothesis_ids": ["H-01", "H-01a", "H-09"],
        "timestamp": "2026-07-14T12:00:00Z",
        "operator_id": "OP-SYNTH",
        "control_role": "active",
        "randomization": {"seed": SEED, "scheme": "synthetic - single deterministic shot", "blinded": False},
        "specimen": {
            "specimen_id": "SP-SYNTH-Q154",
            "specimen_type": "quartz_crystal",
            "material": {"name": "alpha-quartz", "density_g_cm3": 2.65, "density_source": "handbook (synthetic record)"},
            "geometry": {
                "length_mm": 154.05, "diameter_wide_mm": 34.0, "diameter_narrow_mm": 25.0,
                "diameter_mode": "across_vertices", "facet_count": 6,
                "angle_female_deg": 51.843, "angle_male_deg": 60.0, "angle_mode": "face_slope",
            },
            "mass_measured_g": 154.0,
            "provenance": {
                "origin": "SYNTHETIC specimen record (no physical object)",
                "classification_note": "synthetic; mode frequencies planted at 4096 / 10042.677 / 12288 Hz",
            },
        },
        "drive_config": {
            "drive_id": "DRV-SAMPLE-TAP",
            "branch": "modal_survey",
            "drive_type": "impulse_tap",
            "placement": {"drive_x_mm": 77.0, "note": "synthetic tap at t = 5 ms"},
            "timing": {"session_duration_s": 0.25, "drive_off_time_s": 0.0058},
            "reference_clock": {"shared": True, "source": "synthetic common timebase"},
            "source_claim_refs": ["RG-01"],
        },
        "acquisition": {
            "acquisition_id": "ACQ-SAMPLE-MODAL",
            "sample_rate_hz": fs, "duration_s": n / fs, "n_samples": n,
            "single_shot": True,
            "n_runs": 1,
            "post_drive": {"drive_off_time_s": 0.0058, "post_drive_ratio": round((n / fs - 0.0058) / 0.0058, 2)},
            "channels": [
                {"channel_id": "CH1", "sensor_type": "contact_mic", "units": "V",
                 "position_xyz_mm": [40.0, 18.0, 0.0], "aperture_mm": 6.0, "calibration_ref": "SYNTH"},
                {"channel_id": "CH2", "sensor_type": "accelerometer", "units": "m/s2",
                 "position_xyz_mm": [120.0, 18.0, 0.0], "aperture_mm": 8.0, "calibration_ref": "SYNTH",
                 "sensor_mass_g": 0.8},
                {"channel_id": "CH3", "sensor_type": "force", "units": "N",
                 "position_xyz_mm": [77.0, -20.0, 0.0], "calibration_ref": "SYNTH"},
            ],
            "artifact_register_ref": "synthetic - not applicable",
            "notes": "n_runs = 1 sample shot; real campaigns follow EXPERIMENT_PROTOCOL.md repeat counts.",
        },
        "environment": {
            "bench_id": "BENCH-SYNTH",
            "timestamp_start": "2026-07-14T12:00:00Z",
            "temperature_c_start": 21.0,
            "notes": "synthetic environment record",
        },
        "timeseries": [{
            "file": "modal_survey_response.csv",
            "format": "csv",
            "sha256": sha256_of(csv),
            "channel_ids": ["CH1", "CH2", "CH3"],
            "run_index": 0,
            "sample_rate_hz": fs,
            "t0_s": 0.0,
            "n_rows": n,
            "columns": [
                {"name": "t_s", "units": "s", "description": "time from acquisition start"},
                {"name": "mic_v", "units": "V", "channel_id": "CH1", "description": "contact mic"},
                {"name": "accel_m_s2", "units": "m/s2", "channel_id": "CH2", "description": "accelerometer"},
                {"name": "force_n", "units": "N", "channel_id": "CH3", "description": "tap force"},
            ],
        }],
        "provenance": {
            "software": {"numpy": np.__version__, "generator": "make_samples.py"},
            "generator_script": "experiments/sample_data/make_samples.py",
            "generator_seed": SEED,
            "synthetic": True,
        },
        "classification_note": "SYNTHETIC pipeline-test data; carries no evidential weight.",
        "notes": "Planted modes: 4096 Hz (tau 60 ms), 10042.677 Hz (tau 35 ms), 12288 Hz (tau 20 ms); tap at 5 ms.",
    }
    (HERE / "modal_survey_run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return csv


# ---------------------------------------------------------------- branch 2
def make_opposed_coil():
    rng = np.random.default_rng(SEED + 1)
    fs = 8192.0
    dur = 2.0
    n = int(fs * dur)             # 16384
    t = np.arange(n) / fs

    # Half-spacing envelope (RG-12): 4 x (46 ms ON + 23 ms spacing) + 92 ms
    # pause = 368 ms macrocycle; drive off at 0.368 s; post-drive ratio 4.43.
    drive_off = 0.368
    on = np.zeros(n, dtype=bool)
    for k in range(4):
        t0 = k * (0.046 + 0.023)
        on |= (t >= t0) & (t < t0 + 0.046)

    # Baseband response at +12 Hz offset from the 4096 Hz LO. Amplitude grows
    # while ON bursts feed the mode (gain 30 /s), decays at 1/tau otherwise.
    tau = 0.30
    amp = np.zeros(n)
    a = 0.0
    dt = 1 / fs
    for i in range(n):
        a += dt * ((30.0 * (0.01 + a) if on[i] else 0.0) - a / tau)
        amp[i] = a
    phase0 = rng.uniform(0, 2 * np.pi)          # spontaneous per-shot phase
    z = amp * np.exp(1j * (2 * np.pi * 12.0 * t + phase0))
    z += 0.004 * (rng.standard_normal(n) + 1j * rng.standard_normal(n))

    # Drive-current proxy (shunt voltage): square bursts + switching noise.
    shunt = 0.3 * on.astype(float) + 0.003 * rng.standard_normal(n)

    csv = HERE / "opposed_coil_iq.csv"
    write_csv(csv, ["t_s", "z_i_v", "z_q_v", "shunt_v"],
              [t, z.real, z.imag, shunt])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "RUN-SAMPLE-COIL-0001",
        "session_id": "SES-SAMPLE-SYNTH",
        "protocol_branch": "opposed_coil",
        "protocol_version": PROTOCOL_VERSION,
        "hypothesis_ids": ["H-12", "H-14"],
        "timestamp": "2026-07-14T12:05:00Z",
        "operator_id": "OP-SYNTH",
        "control_role": "active",
        "randomization": {"seed": SEED + 1, "scheme": "synthetic - single deterministic shot", "blinded": False},
        "specimen": {
            "specimen_id": "SP-SYNTH-Q154",
            "specimen_type": "quartz_crystal",
            "material": {"name": "alpha-quartz", "density_g_cm3": 2.65, "density_source": "handbook (synthetic record)"},
            "geometry": {
                "length_mm": 154.05, "diameter_wide_mm": 34.0, "diameter_narrow_mm": 25.0,
                "diameter_mode": "across_vertices", "facet_count": 6,
                "angle_female_deg": 51.843, "angle_male_deg": 60.0, "angle_mode": "face_slope",
            },
            "mass_measured_g": 154.0,
            "provenance": {
                "origin": "SYNTHETIC specimen record (no physical object)",
                "classification_note": "synthetic",
            },
        },
        "drive_config": {
            "drive_id": "DRV-SAMPLE-COIL",
            "branch": "opposed_coil",
            "drive_type": "opposed_coil_pulse",
            "carrier": {"frequency_hz": 4096, "waveform": "square", "phase_between_outputs_deg": 180,
                        "clock_source": "synthetic common timebase"},
            "pulse": {"width_us": 1.3, "voltage_v": 60, "peak_current_a": 3},
            "envelope": {"family": "half_spacing_46_23_92", "on_ms": 46, "spacing_ms": 23,
                         "final_pause_ms": 92, "bursts_per_group": 4,
                         "exact_total_cycles": 1508, "exact_allocation": "754 ON + 377 spacing + 377 pause"},
            "coil": {"turns_copper": 40, "turns_silver": 40, "wire_diameter_mm": 0.33,
                     "wire_spacing_mm": 0.66, "inferred_inductance_uh": 26,
                     "stored_energy_per_pulse_uj": 117},
            "timing": {"session_duration_s": drive_off, "drive_off_time_s": drive_off},
            "reference_clock": {"shared": True, "source": "synthetic common timebase",
                                "generator_phase_priming_note": "constant phase offset each run (simulated)"},
            "source_claim_refs": ["RG-12", "RG-14", "G-12", "G-13"],
        },
        "acquisition": {
            "acquisition_id": "ACQ-SAMPLE-COIL",
            "sample_rate_hz": fs, "duration_s": dur, "n_samples": n,
            "single_shot": True,
            "n_runs": 1,
            "post_drive": {"drive_off_time_s": drive_off,
                           "post_drive_ratio": round((dur - drive_off) / drive_off, 2)},
            "iq": {"enabled": True, "lo_frequency_hz": 4096,
                   "lo_derivation": "same synthetic timebase as drive carrier",
                   "demodulation": "digital_heterodyne", "shared_reference": True,
                   "reference_source": "synthetic common timebase"},
            "channels": [
                {"channel_id": "CH1", "sensor_type": "contact_mic", "units": "V",
                 "position_xyz_mm": [77.0, 18.0, 0.0], "aperture_mm": 6.0, "calibration_ref": "SYNTH"},
                {"channel_id": "CH2", "sensor_type": "current_shunt", "units": "V",
                 "position_xyz_mm": [0.0, -40.0, 0.0], "calibration_ref": "SYNTH"},
            ],
            "artifact_register_ref": "synthetic - not applicable",
            "notes": "n_runs = 1 sample shot; coherence/ensemble claims need >= 100 runs.",
        },
        "environment": {
            "bench_id": "BENCH-SYNTH",
            "timestamp_start": "2026-07-14T12:05:00Z",
            "temperature_c_start": 21.0,
            "instrument_phase_drift_deg": 0.0,
            "notes": "synthetic environment record",
        },
        "timeseries": [{
            "file": "opposed_coil_iq.csv",
            "format": "csv",
            "sha256": sha256_of(csv),
            "channel_ids": ["CH1", "CH2"],
            "run_index": 0,
            "sample_rate_hz": fs,
            "t0_s": 0.0,
            "n_rows": n,
            "columns": [
                {"name": "t_s", "units": "s", "description": "time from acquisition start"},
                {"name": "z_i_v", "units": "V", "channel_id": "CH1", "description": "in-phase z_I (baseband, LO 4096 Hz)"},
                {"name": "z_q_v", "units": "V", "channel_id": "CH1", "description": "quadrature z_Q"},
                {"name": "shunt_v", "units": "V", "channel_id": "CH2", "description": "coil current shunt"},
            ],
        }],
        "provenance": {
            "software": {"numpy": np.__version__, "generator": "make_samples.py"},
            "generator_script": "experiments/sample_data/make_samples.py",
            "generator_seed": SEED + 1,
            "synthetic": True,
        },
        "classification_note": "SYNTHETIC pipeline-test data; carries no evidential weight.",
        "notes": "Response planted at LO + 12 Hz with random per-shot phase; ringdown tau = 0.30 s after drive-off at 0.368 s.",
    }
    (HERE / "opposed_coil_run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return csv


if __name__ == "__main__":
    for f in (make_modal_survey(), make_opposed_coil()):
        print(f"wrote {f.name}: {f.stat().st_size} bytes, sha256 {sha256_of(f)[:16]}...")
    print("wrote modal_survey_run_manifest.json, opposed_coil_run_manifest.json")
