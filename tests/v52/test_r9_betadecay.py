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


def test_omitted_account_violates_all_four_laws():
    """Each is independently sufficient; they are not one argument
    restated four ways."""
    a = B.conservation_audit(B.OMITTED)
    assert not a["conserves"]
    assert {f["law"] for f in a["failures"]} == set(B.CONSERVATION_LAWS)
    assert "not four ways of saying one thing" in a["note"]


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


def test_historical_note_credits_pauli_1930():
    L = B.omitted_antineutrino_ledger()
    assert "Pauli" in L["historical_note"]
    assert "1930" in L["historical_note"]


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
