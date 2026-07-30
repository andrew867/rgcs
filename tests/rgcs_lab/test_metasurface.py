from rgcs_lab.metasurface import MetasurfaceConfig, sweep


def test_metasurface_power_ledger_and_warning():
    rec = sweep(MetasurfaceConfig(points=5))
    ledger = rec["result"]["power_ledger"]
    assert rec["status"] == "YELLOW"
    assert ledger["units"] == "W"
    assert ledger["numerical_residual"] < 1e-12
    assert "does not compute gravity" in rec["warnings"][0]

