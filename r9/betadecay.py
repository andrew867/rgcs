"""P05 — neutron beta decay and the "omitted antineutrino" ledger.

The source material treats the antineutrino in neutron beta decay as
something that can be left out of the account. This module works out
exactly what its omission would cost, and the answer is decisive:

    The antineutrino is not an optional bookkeeping term. Omitting it
    turns a three-body decay into a two-body decay, which makes the
    electron **monoenergetic**. The electron spectrum is measured and
    it is **continuous**. That discrepancy is the historical reason
    Pauli postulated the neutrino in 1930, and it remains the cleanest
    single argument.

So the omission is not a modelling convenience with a free parameter.
It is a claim about the shape of a spectrum that has been measured
since the 1910s, and it is excluded.

Four conservation laws each independently require the third body:
energy, momentum, angular momentum, and lepton number. Any one of
them is sufficient. All values are CODATA/PDG literature; nothing
here is measured by this project.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

# --- literature masses, MeV/c^2 (CODATA 2018 / PDG) -------------------

M_NEUTRON = 939.565_420_52
M_PROTON = 938.272_088_16
M_ELECTRON = 0.510_998_950

#: Neutron mean lifetime, seconds. Included because the "beam vs
#: bottle" discrepancy is a live experimental issue and a reader
#: should not think this number is settled to arbitrary precision.
NEUTRON_LIFETIME_S = 878.4
NEUTRON_LIFETIME_NOTE = (
    "beam and bottle methods disagree by roughly 4 seconds (~4 sigma); "
    "this is an open experimental question, not a settled constant")

#: Conservation laws that independently require a third body.
CONSERVATION_LAWS = (
    "ENERGY",
    "MOMENTUM",
    "ANGULAR_MOMENTUM",
    "LEPTON_NUMBER",
)


class ConservationViolation(RuntimeError):
    """Raised when a decay account fails a conservation law."""


# --- the ledger --------------------------------------------------------

def q_value_mev() -> float:
    """Q = m_n - m_p - m_e, the energy shared by the decay products."""
    return M_NEUTRON - M_PROTON - M_ELECTRON


@dataclass(frozen=True)
class DecayAccount:
    """A candidate account of neutron beta decay."""

    label: str
    products: tuple[str, ...]
    includes_antineutrino: bool

    @property
    def n_bodies(self) -> int:
        return len(self.products)

    def as_record(self) -> dict:
        d = asdict(self)
        d["products"] = list(self.products)
        d["n_bodies"] = self.n_bodies
        return d


STANDARD = DecayAccount(
    "n -> p + e- + nu_e-bar", ("proton", "electron", "antineutrino"),
    True)

OMITTED = DecayAccount(
    "n -> p + e- (antineutrino omitted)", ("proton", "electron"),
    False)


def spectrum_prediction(account: DecayAccount) -> dict:
    """What electron spectrum does this account predict?

    This is the discriminating observable, and it is not subtle: a
    two-body decay fixes the electron energy exactly, a three-body
    decay spreads it continuously.
    """
    q = q_value_mev()
    if account.n_bodies == 2:
        # Two-body: energies fixed by kinematics alone.
        # Non-relativistic recoil approximation is ample here since
        # the qualitative point is monoenergetic vs continuous.
        e_electron = q * (1.0 - q / (2.0 * M_PROTON))
        return {
            "account": account.label,
            "shape": "MONOENERGETIC",
            "electron_energy_mev": e_electron,
            "spread_mev": 0.0,
            "matches_observation": False,
            "note": ("a two-body decay fixes the electron energy "
                     "exactly; the measured spectrum is continuous, so "
                     "this account is experimentally excluded"),
        }
    return {
        "account": account.label,
        "shape": "CONTINUOUS",
        "electron_energy_mev": None,
        "endpoint_mev": q,
        "spread_mev": q,
        "matches_observation": True,
        "note": ("a three-body decay shares Q continuously between "
                 "the electron and the antineutrino, giving a "
                 "spectrum from 0 to the endpoint; this is what is "
                 "measured"),
    }


def conservation_audit(account: DecayAccount) -> dict:
    """Which conservation laws does this account satisfy?"""
    failures = []
    if not account.includes_antineutrino:
        failures.append({
            "law": "ENERGY",
            "why": ("without a third body the electron energy is "
                    "fixed; the observed continuous spectrum then has "
                    "missing energy with nowhere to go"),
        })
        failures.append({
            "law": "MOMENTUM",
            "why": ("two-body kinematics fix the proton and electron "
                    "momenta back to back; observed momenta are not "
                    "collinear"),
        })
        failures.append({
            "law": "ANGULAR_MOMENTUM",
            "why": ("neutron, proton and electron are each spin-1/2; "
                    "1/2 -> 1/2 + 1/2 cannot balance without a fourth "
                    "half-integer spin"),
        })
        failures.append({
            "law": "LEPTON_NUMBER",
            "why": ("L = 0 before, L = +1 after (the electron) unless "
                    "an antilepton carries L = -1"),
        })
    return {
        "account": account.label,
        "laws_checked": list(CONSERVATION_LAWS),
        "failures": failures,
        "conserves": not failures,
        "verdict": ("CONSERVING" if not failures
                    else "VIOLATES_CONSERVATION"),
        "note": ("each failure is independently sufficient to exclude "
                 "the account; they are not four ways of saying one "
                 "thing" if failures else
                 "all four conservation laws are satisfied"),
    }


def omitted_antineutrino_ledger() -> dict:
    """The P05 headline: what the omission would actually cost."""
    std = conservation_audit(STANDARD)
    omt = conservation_audit(OMITTED)
    return {
        "q_value_mev": q_value_mev(),
        "q_value_note": "literature value 0.782 MeV",
        "neutron_lifetime_s": NEUTRON_LIFETIME_S,
        "neutron_lifetime_caveat": NEUTRON_LIFETIME_NOTE,
        "standard_account": std,
        "omitted_account": omt,
        "standard_spectrum": spectrum_prediction(STANDARD),
        "omitted_spectrum": spectrum_prediction(OMITTED),
        "discriminating_observable": (
            "the shape of the electron energy spectrum: monoenergetic "
            "if the antineutrino is absent, continuous if present"),
        "historical_note": (
            "this is precisely the discrepancy that led Pauli to "
            "postulate the neutrino in 1930, before any neutrino was "
            "detected. The spectrum had been known to be continuous "
            "since the 1910s."),
        "verdict": (
            "The antineutrino cannot be omitted. Its omission is not a "
            "simplification with a free parameter; it is a prediction "
            "that the electron spectrum is a line, and the spectrum is "
            "measured to be continuous. Four independent conservation "
            "laws each exclude the omitted account on their own."),
        "what_this_does_not_say": (
            "It does not say the antineutrino is well understood. "
            "Neutrino masses, the mass ordering, whether neutrinos are "
            "Majorana, and the beam-versus-bottle lifetime discrepancy "
            "are all genuinely open. 'Required by conservation' and "
            "'fully characterised' are different statements."),
    }


def refuse_omission(account: DecayAccount) -> None:
    """Refuse to proceed on an account that violates conservation."""
    audit = conservation_audit(account)
    if not audit["conserves"]:
        laws = ", ".join(f["law"] for f in audit["failures"])
        raise ConservationViolation(
            f"{account.label} violates {laws}. The antineutrino is "
            f"required by each of these independently; omitting it "
            f"predicts a monoenergetic electron, and the measured "
            f"spectrum is continuous.")
