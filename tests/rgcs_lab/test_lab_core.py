"""Focused tests for the Recursive Infrastructure Lab hub."""

from __future__ import annotations

import json
import pathlib

import pytest

from rgcs_lab.adapters import coordinate, frames, golay
from rgcs_lab.adapters import services
from rgcs_lab.common.privacy import PrivacyDefaults
from rgcs_lab.common.status import module_catalog
from rgcs_lab.reference import golay as golay_ref
from rgcs_lab.reference import predictions as pred_ref

ROOT = pathlib.Path(__file__).resolve().parents[2]
HUB = ROOT / "static" / "hub"


def test_nine_modules_in_catalog():
    cats = module_catalog()
    assert len(cats) == 9
    assert [c["id"] for c in cats] == [
        "coordinate", "golay", "frames", "memory", "dual_pole",
        "lattice", "metasurface", "predictions", "proofs",
    ]


def test_coordinate_adapter_uses_domain_api():
    result = coordinate.decode(165876523)
    assert result.status.value == "GREEN"
    assert result.result["physical_projection_status"] == "UNDERDETERMINED"
    assert "YELLOW" in " ".join(result.warnings)
    assert result.receipt["receipt_sha256"]


def test_golay_roundtrip_and_flip_ladder():
    for info in (0, 1, 0xA5A, 0xFFF):
        cw = golay_ref.encode12(info)
        got, corr, status, _, _ = golay_ref.decode24(cw)
        assert status == "ok" and got == info and corr == cw
    for flips in range(0, 4):
        demo = golay.demo(flips_per_block=flips, seed=2)
        assert demo.result["exact_round_trip"] is True
        if flips == 0:
            assert demo.result["decoded_blocks"] == demo.result["blocks_in"]
            assert all(s == "ok" for s in demo.result["correction_status"])
        else:
            assert all(s == "corrected" for s in demo.result["correction_status"])
            assert demo.result["decoded_blocks"] == demo.result["blocks_in"]
    hard = golay.demo(flips_per_block=4, seed=2)
    assert any(s == "uncorrectable" for s in hard.result["correction_status"])


def test_frames_roundtrip_example():
    result = frames.example()
    assert result.status.value == "GREEN"
    assert result.result["normalization_error"] < 1e-12
    rt = result.result["round_trip_basis"]
    assert abs(rt["e1"][0] - 1.0) < 1e-9


def test_memory_and_dual_pole():
    mem = services.memory_benchmark("golay transport")
    assert mem.result["top_id"] == "doc-golay"
    good = services.dual_pole_audit({
        "statement": "exact arithmetic decode",
        "claim_class": ["EXACT_ARITHMETIC"],
        "evidence": ["x"],
    })
    assert good.result["critic_bypassed"] is False
    bad = services.dual_pole_audit({
        "statement": "anti-gravity confirmed via torsion resonance",
    })
    assert bad.result["decision"] == "REJECT"
    assert bad.result["attacks"]


def test_lattice_energy_ledger_and_metasurface_conservation():
    lat = services.lattice_run()
    ledger = lat.result["energy_ledger"]
    assert "numerical_drift" in ledger
    assert lat.result["hermitian_residual"] < 1e-10
    meta = services.metasurface_sweep()
    assert meta.status.value == "YELLOW"
    assert meta.result["max_conservation_residual"] < 1e-9
    assert "gravity" in " ".join(meta.warnings).lower() or any(
        "gravity" in w.lower() for w in meta.warnings
    )


def test_prediction_freeze_verify_and_measurement_lock():
    base = {
        "prediction_id": "T-1",
        "hypothesis": "residual may appear",
        "controls": ["unpowered"],
    }
    frozen = pred_ref.freeze_prediction(base)
    assert frozen["status"] == "YELLOW"
    assert pred_ref.verify_prediction(frozen)["match"] is True
    with pytest.raises(ValueError, match="measurement"):
        pred_ref.freeze_prediction({**base, "measurement_started": True})


def test_privacy_defaults_are_local():
    d = PrivacyDefaults()
    assert d.bind_host == "127.0.0.1"
    assert d.telemetry is False
    assert d.outbound_network is False


def test_hub_static_artifacts_exist():
    assert (HUB / "index.html").is_file()
    for mod in module_catalog():
        mid = mod["id"]
        assert (HUB / "modules" / f"{mid}.html").is_file()
        assert (HUB / "fixtures" / f"{mid}.json").is_file()
        assert (HUB / "receipts" / f"{mid}.json").is_file()
    html = (HUB / "index.html").read_text(encoding="utf-8")
    assert "YELLOW" in html
    assert "gravity-modification" in html.lower() or "underdetermined" in html.lower()
    assert "anti-gravity confirmed" not in html.lower()
    assert "antigravity confirmed" not in html.lower()
    # Hub JS must not reimplement Golay/quaternion/solver math.
    js = (HUB / "assets" / "hub.js").read_text(encoding="utf-8")
    for banned in ("encode12", "Hamilton", "da/dt", "syndrome"):
        assert banned not in js


def test_cli_doctor_and_modules(capsys):
    from rgcs_lab.cli import main
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "telemetry=False" in out
    assert main(["modules"]) == 0


def test_cli_refuse_remote_bind():
    from rgcs_lab.cli import main
    assert main(["serve", "--host", "0.0.0.0"]) == 2
