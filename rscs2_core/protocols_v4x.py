"""Experimental campaign protocols E01-E09 (Agents E01-E09; coverage
E001-E027, W001-W017, H001-H017; gates G21-G30).

Every campaign is a typed ExperimentProtocolRecord with apparatus,
channels, control matrix, randomization/blinding, analysis plan,
preregistration, and a SAFETY-GATE evaluation. No hardware is
operated: engineering-safe campaigns stop at
PROTOCOL_READY_HARDWARE_REQUIRED; human-subject campaigns stop at
ETHICS_APPROVAL_REQUIRED. The synthetic DAQ analysis pipeline is
validated on planted fixtures (G29); synthetic data can never be
relabeled measured (D01 rule, tested)."""

from __future__ import annotations

import math

import numpy as np

from .research_records import make_record, safety_gate

CHANNELS = ["E011 magnetometer-3ax", "E012 e-field/electrometer",
            "E013 capacitance/impedance", "E014 mic+contact-mic",
            "E015 accelerometer", "E016 laser vibrometer",
            "E017 env(I,V,B,T,RH,SPL)"]

CORE_CONTROLS = ["E018 grounded/ungrounded + glove + no-contact + "
                 "automated", "E019 fixed nonmetal jig",
                 "E020 dummy coil / resistor / no-crystal / rotated "
                 "crystal / metal bracket", "E021 cheap quartz before "
                 "precision crystal", "E022 repeated days + blind "
                 "labels", "E023 simultaneous acoustic + electrical "
                 "pickup", "E026 north/orientation logging",
                 "E027 contact force + mounting pressure logging"]


def _protocol(rid, title, kind, status, extras, limits,
              controls=None, **kw):
    gate = safety_gate({"campaign_kind": kind,
                        "declared_limits": limits, **extras})
    declared = gate["required_status"] if gate["passed"] or \
        gate["required_status"] == "ETHICS_APPROVAL_REQUIRED" else \
        "BLOCKED_SAFETY"
    assert declared == status, (rid, declared, status)
    return make_record(
        "ExperimentProtocolRecord", rid, title, "experimental",
        status, ["ENG"], campaign_kind=kind,
        declared_limits=limits, safety_gate=gate,
        channels=CHANNELS, controls=(controls or CORE_CONTROLS),
        randomization="seeded label shuffle (blind_labels)",
        blinding="condition labels separated from analysis until "
                 "lock", preregistration_id=f"PREREG-{rid}",
        analysis_plan="FFT peak + Q + ring-down via "
                      "analyze_ring_down; control subtraction "
                      "against the C07 ordinary-artifact budget; "
                      "look-elsewhere model for any frequency match",
        **kw)


def build_protocols() -> dict:
    P = {}

    def add(rec):
        P[rec["record_id"]] = rec

    add(_protocol(
        "E01", "acoustic campaign: 4096 Hz brushing (3 axes + all 6 "
        "sides), contact + non-contact, forks vs voice-coil/piezo",
        "acoustic", "PROTOCOL_READY_HARDWARE_REQUIRED", {},
        {"spl_dba": 80.0, "voltage_v": 12.0},
        covers=["E001", "E002", "E003", "E004", "F001", "F020",
                "F021", "F022", "F023"]))
    add(_protocol(
        "E02", "electrode pulse campaign: silver electrodes at the "
        "measured compression node; 20/21 Hz comparison; "
        "1496/587/644 node excitation", "electrode_pulse",
        "PROTOCOL_READY_HARDWARE_REQUIRED", {},
        {"voltage_v": 24.0, "current_a": 0.5},
        covers=["E005", "E006", "E007", "F004", "F005", "F006",
                "F024", "F025", "F026"]))
    add(_protocol(
        "E03", "coil and field mapping: crossed coils, 40-turn "
        "modern coil, historical 7-turn scaffold; 3-axis field maps",
        "coil", "PROTOCOL_READY_HARDWARE_REQUIRED", {},
        {"voltage_v": 24.0, "current_a": 1.0},
        covers=["E008", "E009", "E010", "E011"]))
    add(_protocol(
        "E04", "material/specimen comparison: catalog crystals vs "
        "cheap quartz vs polymer/glass controls", "materials",
        "PROTOCOL_READY_HARDWARE_REQUIRED", {},
        {"spl_dba": 80.0},
        covers=["E021", "G015", "G016", "G017", "G018", "G019",
                "G020", "G021", "G022", "G023", "G024", "G026",
                "G029", "G030"]))
    add(_protocol(
        "E05", "water programme: matched blind vessels, sham "
        "exposure, T/gas/pH/conductivity/UV-vis/flow logging, "
        "1-7 passes, historical 7-turn geometry",
        "water", "PROTOCOL_READY_HARDWARE_REQUIRED",
        {"no_ingestion_ack": True}, {"voltage_v": 12.0},
        controls=CORE_CONTROLS + [
            "W001 matched blind vessels", "W002 sham exposure",
            "W010 no-crystal", "W011 raw quartz",
            "W012 polymer+glass", "W013 reversed orientation",
            "W016 contamination/mass-balance/randomized labels"],
        covers=[f"W{i:03d}" for i in range(1, 18)] + ["E010"]))
    add(_protocol(
        "E06", "human loading: grip force, hand capacitance, "
        "contact stiffness/damping, equivalent modal load, "
        "personalized held-target correction", "human_loading",
        "ETHICS_APPROVAL_REQUIRED", {}, {"voltage_v": 0.0},
        covers=[f"H{i:03d}" for i in range(1, 9)] + ["H017"]))
    add(_protocol(
        "E07", "operator-state programme: breathing/imagery/"
        "meditation protocols, optional EEG, HR logging, "
        "40.96 vs 40/41/42 Hz, blinded objective outcomes",
        "operator_state", "ETHICS_APPROVAL_REQUIRED", {},
        {"voltage_v": 0.0},
        covers=["H009", "H010", "H011", "H012", "H013", "H014",
                "H015", "H016", "F008", "F009", "F010", "F011"]))
    add(_protocol(
        "E08", "apparatus integration: full-bench wiring, DAQ "
        "schema, channel calibration chain, phone-app claims "
        "demoted to instrument-limited ENG/HYP", "integration",
        "PROTOCOL_READY_HARDWARE_REQUIRED", {},
        {"voltage_v": 24.0, "current_a": 1.0},
        covers=["E012", "E013", "E014", "E015", "E016", "E017",
                "E024", "E025"]))
    add(_protocol(
        "E09", "staged bench execution: dry-run order, escalation "
        "gates, abort criteria, data lock points", "bench_staging",
        "PROTOCOL_READY_HARDWARE_REQUIRED", {},
        {"voltage_v": 24.0},
        covers=["E018", "E019", "E020", "E022", "E023", "E026",
                "E027"]))
    return P


def coverage_map() -> dict:
    """Ledger-ID -> protocol owner (for the master coverage proof)."""
    out = {}
    for pid, rec in build_protocols().items():
        for cid in rec["covers"]:
            out.setdefault(cid, []).append(pid)
    return out


# --- synthetic DAQ analysis (gate G29) ---------------------------------------

def synth_ring_down(f_hz: float, q: float, fs_hz: float,
                    duration_s: float, noise: float = 0.0,
                    seed: int = 7) -> tuple:
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, duration_s, 1.0 / fs_hz)
    tau = q / (math.pi * f_hz)
    y = np.exp(-t / tau) * np.sin(2 * math.pi * f_hz * t) \
        + noise * rng.standard_normal(len(t))
    return t, y


def analyze_ring_down(t: np.ndarray, y: np.ndarray) -> dict:
    """FFT peak frequency + Q from the amplitude-envelope decay
    (tau fit -> Q = pi f tau). Marked synthetic-safe: carries no
    MEAS tag; the caller supplies provenance."""
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    dt = t[1] - t[0]
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    freqs = np.fft.rfftfreq(len(y), dt)
    f0 = float(freqs[np.argmax(spec[1:]) + 1])
    # envelope via analytic-signal magnitude (Hilbert by FFT)
    Y = np.fft.fft(y)
    h = np.zeros(len(y))
    h[0] = 1
    h[1:(len(y) + 1) // 2] = 2
    env = np.abs(np.fft.ifft(Y * h))
    good = env > 0.05 * env.max()
    # tau from a log-linear fit over the usable envelope
    A = np.vstack([t[good], np.ones(good.sum())]).T
    slope, _ = np.linalg.lstsq(A, np.log(env[good]), rcond=None)[0]
    tau = -1.0 / slope if slope < 0 else float("inf")
    return {"f0_hz": f0, "tau_s": float(tau),
            "q": float(math.pi * f0 * tau),
            "synthetic_validated": True}


def blind_labels(n: int, conditions: list, seed: int) -> dict:
    """Deterministic blinded allocation: opaque labels -> conditions
    kept in a sealed map (analysis sees labels only)."""
    rng = np.random.default_rng(seed)
    alloc = [conditions[i % len(conditions)] for i in range(n)]
    rng.shuffle(alloc)
    labels = [f"SAMPLE-{i:03d}" for i in range(n)]
    return {"labels": labels,
            "sealed_map": dict(zip(labels, alloc)),
            "note": "sealed_map stays with the randomization "
                    "custodian until analysis lock (E022/W016/H015)"}
