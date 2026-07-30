from rgcs_lab.lattice import LatticeConfig, hermitian_ring_hamiltonian, simulate


def test_lattice_hamiltonian_is_hermitian_with_phase():
    h = hermitian_ring_hamiltonian(LatticeConfig(directed_phase_rad=0.3))
    assert h.shape == (64, 64)
    assert (abs(h - h.conj().T) < 1e-12).all()


def test_lattice_lossless_norm_drift_is_reported_small():
    rec = simulate(LatticeConfig(steps=20, dt_s=0.001))
    ledger = rec["result"]["energy_ledger"]
    assert rec["status"] == "GREEN"
    assert abs(ledger["numerical_drift"]) < 1e-10
    assert ledger["resonance_gain_label"].startswith("attributed")


def test_lattice_damping_ledger_has_dissipation():
    rec = simulate(LatticeConfig(steps=20, dt_s=0.001, damping_s=0.1))
    ledger = rec["result"]["energy_ledger"]
    assert ledger["dissipated"] > 0.0
    assert ledger["stored"] < ledger["initial"]

