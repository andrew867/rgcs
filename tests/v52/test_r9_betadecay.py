"""P05 — the omitted-antineutrino ledger."""

from __future__ import annotations

import pytest

from r9 import betadecay as B


def test_q_value_matches_literature():
    """Q = m_n - m_p - m_e = 0.782 MeV."""
    assert B.q_value_mev() == pytest.approx(0.782, abs=0.001)


def test_masses_are_literature_values():
    assert B.M_NEUTRON > B.M_PROTON > B.M_ELECTRON
    assert B.M_NEUTRON - B.M_PROTON == pytest.approx(1.293, abs=0.001)


def test_standard_account_conserves():
    a = B.conservation_audit(B.STANDARD)
    assert a["conserves"]
    assert a["verdict"] == "CONSERVING"
    assert a["failures"] == []


def test_omitted_account_fails_all_four_checks():
    a = B.conservation_audit(B.OMITTED)
    assert not a["conserves"]
    assert {f["law"] for f in a["failures"]} == set(B.CONSERVATION_LAWS)


def test_the_four_checks_are_not_four_independent_arguments():
    """R9-D-012. The module claimed four independent conservation
    laws. Energy and momentum are the same empirical argument twice --
    a two-body decay conserves both perfectly and simply predicts the
    wrong electron energy. The honest count is two.
    """
    a = B.conservation_audit(B.OMITTED)
    assert a["independent_argument_count"] == 2
    assert B.ARGUMENT_KINDS["ENERGY"] == "EMPIRICAL"
    assert B.ARGUMENT_KINDS["MOMENTUM"] == "EMPIRICAL"
    assert B.ARGUMENT_KINDS["ANGULAR_MOMENTUM"] == "A_PRIORI"
    assert "circular" in B.ARGUMENT_KINDS["LEPTON_NUMBER"].lower()


def test_lepton_number_circularity_is_admitted():
    assert "close to circular" in B.INDEPENDENCE_NOTE
    assert "ONE decisive empirical argument" in B.INDEPENDENCE_NOTE


def test_incoherent_accounts_are_refused():
    """R9-D-013. n_bodies and includes_antineutrino were independent
    fields with no cross-check, so a two-body decay claiming an
    antineutrino was reported CONSERVING."""
    bogus = B.DecayAccount("two bodies, claims a neutrino",
                           ("proton", "electron"), True)
    with pytest.raises(B.ConservationViolation) as e:
        B.conservation_audit(bogus)
    assert "incoherent account" in str(e.value)

    stub = B.DecayAccount("n -> p only", ("proton",), True)
    with pytest.raises(B.ConservationViolation):
        B.conservation_audit(stub)


def test_two_body_decay_predicts_a_monoenergetic_electron():
    s = B.spectrum_prediction(B.OMITTED)
    assert s["shape"] == "MONOENERGETIC"
    assert s["spread_mev"] == 0.0
    assert not s["matches_observation"]


def test_three_body_decay_predicts_a_continuous_spectrum():
    s = B.spectrum_prediction(B.STANDARD)
    assert s["shape"] == "CONTINUOUS"
    assert s["matches_observation"]
    assert s["endpoint_mev"] == pytest.approx(B.q_value_mev())


def test_the_spectrum_is_the_discriminating_observable():
    L = B.omitted_antineutrino_ledger()
    assert "shape of the electron energy spectrum" in \
        L["discriminating_observable"]
    assert L["standard_spectrum"]["shape"] != \
        L["omitted_spectrum"]["shape"]


def test_two_body_electron_energy_is_near_q():
    """Recoil is small: the proton is ~1800x the electron mass."""
    s = B.spectrum_prediction(B.OMITTED)
    assert 0.99 * B.q_value_mev() < s["electron_energy_mev"] \
        <= B.q_value_mev()


def test_omission_is_refused():
    with pytest.raises(B.ConservationViolation) as e:
        B.refuse_omission(B.OMITTED)
    msg = str(e.value)
    assert "LEPTON_NUMBER" in msg
    assert "measured" in msg and "continuous" in msg


def test_standard_account_is_not_refused():
    B.refuse_omission(B.STANDARD)      # must not raise


def test_verdict_says_omission_is_not_a_free_parameter():
    L = B.omitted_antineutrino_ledger()
    assert "cannot be omitted" in L["verdict"]
    assert "free parameter" in L["verdict"]


def test_historical_note_gives_the_full_sequence():
    """Not just Pauli: Chadwick measured it, and Ellis & Wooster
    proved the continuum was not an instrumental artefact -- which is
    the step that made the crisis inescapable."""
    n = B.omitted_antineutrino_ledger()["historical_note"]
    for name in ("Chadwick", "Ellis", "Wooster", "Pauli", "Fermi"):
        assert name in n
    assert "1914" in n and "1930" in n and "1934" in n


def test_pauli_and_fermi_are_not_conflated():
    """Pauli's particle was a nuclear constituent; 'created at decay'
    is Fermi's 1934 reinterpretation."""
    p = B.omitted_antineutrino_ledger()["historical_precision"]
    assert "nuclear constituent" in p
    assert "Fermi's 1934 reinterpretation" in p


def test_references_are_carried():
    refs = B.omitted_antineutrino_ledger()["references"]
    assert len(refs) == 4
    assert all(isinstance(r, str) and r for r in refs)


def test_the_caveat_does_not_overclaim_neutrino_knowledge():
    """'Required by conservation' is not 'fully characterised'."""
    L = B.omitted_antineutrino_ledger()
    c = L["what_this_does_not_say"]
    assert "Majorana" in c
    assert "genuinely open" in c


def test_lifetime_carries_the_beam_bottle_caveat():
    L = B.omitted_antineutrino_ledger()
    assert "beam" in L["neutron_lifetime_caveat"]
    assert "not a settled constant" in L["neutron_lifetime_caveat"]


def test_account_body_count():
    assert B.STANDARD.n_bodies == 3
    assert B.OMITTED.n_bodies == 2
