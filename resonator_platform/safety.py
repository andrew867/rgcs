"""Fabrication, instrument, and process safety (Agent S01).

Machine-readable limits for the processes this programme could touch,
integrated with the trim-control capability gate. The binding rule
from the pack: **no machine action without capability; no FR-4 laser
process without qualified enclosure and extraction; safety rules
cannot be weakened to obtain data.**"""

from __future__ import annotations

PROCESS_LIMITS = {
    "laser_trim": {
        "hazards": ["eye (class 4 beam)", "FR-4 fumes: brominated "
                    "flame retardants + glass fiber — genuinely "
                    "hazardous", "fire"],
        "requirements": ["class-1 enclosure (interlocked)",
                         "fume extraction with filtration rated for "
                         "the material", "fire watch + extinguisher",
                         "laser safety officer sign-off"],
        "hard_refusals": ["FR-4 ablation without qualified "
                          "extraction", "open-beam operation",
                          "PVC-containing boards (chlorine gas)"],
    },
    "cnc_trim": {
        "hazards": ["rotating tooling", "glass-fiber dust",
                    "workpiece ejection"],
        "requirements": ["guarding", "dust extraction + HEPA",
                         "workholding verification"],
        "hard_refusals": ["unguarded operation"],
    },
    "high_voltage": {
        "limits": {"voltage_v": 30.0, "current_a": 3.0,
                   "stored_mj": 5.0},
        "note": "inherited from the S01 v4.2 envelope, unchanged",
    },
    "rf": {"limits": {"eirp_dbm": 0.0},
           "note": "no intentional radiator work in this programme"},
    "ultrasound": {"limits": {"spl_dba": 85.0},
                   "note": "inherited envelope, unchanged"},
    "cryogenic": {"hard_refusals": ["any cryogen handling — no "
                                    "trained personnel or equipment "
                                    "in this programme"]},
    "microfabrication": {"hard_refusals": [
        "all wet-bench chemistry (HF etc.) — cleanroom work is "
        "INTERFACE_ONLY via the foundry handoff (mems.py)"]},
}


class SafetyRefusal(RuntimeError):
    pass


def check_process(process: str, evidence: dict) -> dict:
    """A process is enabled only when every requirement has evidence.
    There is no override parameter, deliberately."""
    if process not in PROCESS_LIMITS:
        raise SafetyRefusal(f"unknown process {process!r}: an "
                            "unlisted process is a refused process")
    spec = PROCESS_LIMITS[process]
    missing = [r for r in spec.get("requirements", [])
               if r not in evidence or not evidence[r]]
    if missing:
        raise SafetyRefusal(
            f"{process} refused; missing evidence for: {missing}")
    return {"process": process, "enabled": True,
            "evidence": {k: bool(v) for k, v in evidence.items()},
            "note": "enabling is per-process and per-session; it "
                    "does not persist"}


def stop_work_record(reason: str, operator: str) -> dict:
    """Anyone can stop work; the record is mandatory and the restart
    requires addressing the reason, not overriding it."""
    return {"record": "STOP_WORK", "reason": reason,
            "operator": operator,
            "restart_requires": "the reason addressed and recorded; "
                                "there is no override path"}
