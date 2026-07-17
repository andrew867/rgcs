"""A23: end-to-end demo campaigns, entirely in simulator mode.

Six demos per the pack; every report carries SYNTHETIC in ids, file
names, and body text. Runs from a fresh clone with no hardware
(A21 gate).

    python tools/v44_demo_campaigns.py
Writes docs/v4/fkey/SYNTHETIC_demo_report.json (+ .md)
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fkey_instrument import contracts, phase_closure as pc  # noqa: E402
from fkey_instrument import plant as pl, relations as rel   # noqa: E402
from fkey_instrument import spectrum as sp                  # noqa: E402
from fkey_instrument.device import SimDevice                # noqa: E402
from fkey_instrument.optimizer import (Bridge,              # noqa: E402
                                       candidate_families,
                                       compile_campaign, optimize)

OUT = ROOT / "docs" / "v4" / "fkey"


def demo1_relation_census() -> dict:
    rels = rel.rank(rel.seed_relations())
    return {"demo": "1 exact relation census (SYNTHETIC)",
            "ranked": [{"inputs": [[str(c), str(f)] for c, f in
                                   r.inputs],
                        "output_hz": str(r.output_hz),
                        "target_hz": str(r.target_hz),
                        "class": r.primary_class,
                        "order": r.order,
                        "exact": r.exact} for r in rels],
            "explanation": rel.seed_explanation()}


def demo2_waveform_distinction() -> dict:
    fs = 1_048_576.0
    out = {}
    for name, wf, f in (("sine_4096", "sine", 4096.0),
                        ("square_4096", "square", 4096.0),
                        ("sine_20480", "sine", 20480.0)):
        x = sp.synthesize(wf, f, fs, 0.02)
        out[name] = sp.fft_lines(x, fs, 4)
    out["key_comparison"] = sp.fifth_harmonic_comparison()
    return {"demo": "2 waveform distinction (SYNTHETIC)", **out}


def demo3_nominal_sweep() -> dict:
    p = pl.CoupledPlant(4300.0, 8.0, 20278.96, 400.0)
    sweep = pl.synthetic_sweep(p, 20100, 20460, n=3001, noise=0.008)
    fit = pl.fit_peak(sweep["f_hz"], sweep["magnitude"])
    boot = pl.bootstrap_q(sweep["f_hz"], sweep["magnitude"])
    return {"demo": "3 nominal specimen sweep (SYNTHETIC)",
            "sweep_id": sweep["id"],
            "fit": {k: v for k, v in fit.items()},
            "q_ci95": boot.get("q_ci95"),
            "note": "pre-arrival plant model; the peak is the "
                    "MODEL's, not a crystal's"}


def demo4_optimizer() -> dict:
    out = optimize()
    dev = SimDevice()
    bridge = Bridge(dev)
    compiled = []
    for fam in out["pareto"][:4]:
        rec = bridge.compile_recipe(fam)
        v = contracts.validate_recipe(rec)
        compiled.append({"family": fam["family"],
                         "recipe_id": rec["recipe_id"],
                         "valid": v["valid"],
                         "hash": contracts.content_hash(rec)[:16]})
    return {"demo": "4 optimizer Pareto + compiled recipes "
                    "(SYNTHETIC)",
            "pareto_families": [c["family"] for c in out["pareto"]],
            "gate_check": out["gate_check"],
            "compiled": compiled}


def demo5_device_simulator() -> dict:
    dev = SimDevice()
    bridge = Bridge(dev)
    fam = [c for c in candidate_families()
           if c["family"] == "clock_square_4096"][0]
    rec = bridge.compile_recipe(fam)
    up = bridge.upload(rec)
    run = bridge.arm_start_run()
    logs = bridge.download_and_verify_logs()
    return {"demo": "5 device simulator end-to-end (SYNTHETIC)",
            "uploaded": up["loaded"], "ran": run["ok"],
            "segments": run.get("result", {}).get("segments"),
            "log_chain_intact": logs["chain"]["intact"],
            "all_events_synthetic": logs["all_synthetic"]}


def demo6_fault_refusal() -> dict:
    results = {}
    # overtemperature
    d1 = SimDevice()
    b1 = Bridge(d1)
    b1.upload(b1.compile_recipe(candidate_families()[0]))
    lease = d1.request_arm()
    d1.start(lease["token"])
    d1.fault("OVERTEMP", "simulated 65C")
    results["overtemp"] = {"state": d1.state,
                           "output_on": d1.output_on}
    # expired arm
    t = [0.0]
    d2 = SimDevice(clock=lambda: t[0])
    b2 = Bridge(d2)
    b2.upload(b2.compile_recipe(candidate_families()[0]))
    lease = d2.request_arm(ttl_s=5.0)
    t[0] = 6.0
    started = d2.start(lease["token"])
    results["arm_expiry"] = {"started": started["started"],
                             "state": d2.state}
    # invalid pin profile
    d3 = SimDevice(profile="ESP32-2432S028R")
    rec = Bridge(d3).compile_recipe(candidate_families()[0])
    rec["device_requirements"]["output_pins"] = [15]
    loaded = d3.load_recipe(rec, contracts.validate_recipe)
    results["pin_conflict"] = {"loaded": loaded["loaded"],
                               "state": d3.state}
    ok = (results["overtemp"]["state"] == "FAULT_LATCHED"
          and not results["overtemp"]["output_on"]
          and not results["arm_expiry"]["started"]
          and not results["pin_conflict"]["loaded"])
    return {"demo": "6 fault refusal (SYNTHETIC)", "all_failed_off":
            ok, **results}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    demos = [demo1_relation_census(), demo2_waveform_distinction(),
             demo3_nominal_sweep(), demo4_optimizer(),
             demo5_device_simulator(), demo6_fault_refusal()]
    report = {"banner": "SYNTHETIC DEMO REPORT — every number in "
                        "this file was produced by simulation; no "
                        "hardware and no crystal exist",
              "synthetic": True, "demos": demos}
    (OUT / "SYNTHETIC_demo_report.json").write_text(
        json.dumps(report, indent=1, default=str) + "\n",
        encoding="utf-8")
    lines = ["# SYNTHETIC demo report (A23)", "",
             "**" + report["banner"] + "**", ""]
    for d in demos:
        lines.append(f"## {d['demo']}")
        lines.append("")
        for k, v in d.items():
            if k == "demo":
                continue
            lines.append(f"- **{k}**: "
                         f"{json.dumps(v, default=str)[:400]}")
        lines.append("")
    (OUT / "SYNTHETIC_demo_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print("demo campaigns complete:",
          all("demo" in d for d in demos))
    print("demo 5 ran:", demos[4]["ran"],
          "| demo 6 all failed off:", demos[5]["all_failed_off"])
    return 0 if demos[4]["ran"] and demos[5]["all_failed_off"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
