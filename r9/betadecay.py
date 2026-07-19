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

Four conservation laws are checked -- energy, momentum, angular
momentum, lepton number -- but they are NOT four independent
arguments, and an earlier version of this module wrongly said they
were. Energy and momentum are the same empirical argument twice over
(a two-body decay conserves both and simply predicts the wrong
energy). Angular momentum is genuinely independent. Lepton number is
close to circular here, since it was formulated partly in response to
this decay. See ``INDEPENDENCE_NOTE``.

All values are CODATA/PDG literature; nothing here is measured by
this project.
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


#: The canonical sequence. Nothing in this module is novel; the
#: argument was settled between 1914 and 1934.
HISTORICAL_REFERENCES = (
    ("Chadwick, J. (1914), Verh. Dtsch. Phys. Ges. 16, 383-391 -- "
     "the beta spectrum is continuous, not discrete"),
    ("Ellis, C. D. & Wooster, W. A. (1927) -- calorimetric proof the "
     "continuum is real, not an instrumental artefact"),
    ("Pauli, W., letter of 4 December 1930 ('Liebe Radioaktive Damen "
     "und Herren') -- proposes a neutral spin-1/2 particle"),
    ("Fermi, E. (1934), Z. Phys. 88, 161 -- theory of beta decay; "
     "names the neutrino and treats it as created at decay"),
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
        # Two-body: energies fixed exactly by kinematics.
        #
        # R9-D-014. This used q * (1 - q / (2 m_p)), which assumes the
        # electron momentum is approximately Q. It is not: the
        # electron here is relativistic (T_e / m_e ~ 1.5), so p is
        # 1.187 MeV/c, not 0.782. The proton recoil came out 2.3x too
        # small. The old comment said the non-relativistic
        # approximation was "ample" -- it is ample for the *proton*,
        # but the momentum feeding the proton has to be computed
        # relativistically.
        #
        # Exact: E_e = (M_n^2 + m_e^2 - M_p^2) / (2 M_n)
        e_total = ((M_NEUTRON ** 2 + M_ELECTRON ** 2 - M_PROTON ** 2)
                   / (2.0 * M_NEUTRON))
        e_electron = e_total - M_ELECTRON
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


#: How each argument actually works. R9-D-012: the module used to
#: present all four as "independent conservation laws", which
#: overstates the case, and its own justification strings gave it
#: away -- the energy and momentum entries both appeal to the
#: *observed* spectrum rather than to conservation a priori.
#:
#: Energy is not violated by a two-body decay. A two-body decay
#: conserves energy perfectly; it just predicts a different (fixed)
#: electron energy. What excludes it is that the prediction disagrees
#: with measurement. That is one decisive empirical argument, not two
#: independent conservation arguments.
ARGUMENT_KINDS = {
    "ENERGY": "EMPIRICAL",
    "MOMENTUM": "EMPIRICAL",
    "ANGULAR_MOMENTUM": "A_PRIORI",
    "LEPTON_NUMBER": "A_PRIORI_BUT_PARTLY_CIRCULAR",
}

INDEPENDENCE_NOTE = (
    "These are not four independent arguments. Energy and momentum "
    "are the same empirical argument stated twice: a two-body decay "
    "conserves both perfectly and simply predicts a fixed electron "
    "energy, which measurement contradicts. Angular momentum is a "
    "genuinely independent a priori argument -- spin 1/2 cannot go to "
    "spin 1/2 plus spin 1/2. Lepton number is a priori in form, but "
    "lepton number was formulated partly in response to this very "
    "decay, so leaning on it as independent evidence is close to "
    "circular. The honest count is ONE decisive empirical argument "
    "plus ONE clean spin argument."
)


def conservation_audit(account: DecayAccount) -> dict:
    """Which conservation laws does this account satisfy?

    R9-D-013: this function used to branch on the single boolean
    ``includes_antineutrino``, with no cross-check against
    ``n_bodies``. Incoherent accounts therefore passed -- a two-body
    decay that claimed to include an antineutrino was reported
    CONSERVING and was not refused. The fields are now validated
    against each other before anything else is said.
    """
    expected_bodies = 3 if account.includes_antineutrino else 2
    if account.n_bodies != expected_bodies:
        raise ConservationViolation(
            f"incoherent account {account.label!r}: "
            f"includes_antineutrino={account.includes_antineutrino} "
            f"implies {expected_bodies} bodies, but products list "
            f"{account.n_bodies}. This is not a physical claim to "
            f"audit, it is a bookkeeping error.")

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
        "argument_kinds": dict(ARGUMENT_KINDS),
        "independent_argument_count": 2,
        "note": (INDEPENDENCE_NOTE if failures else
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
            "Chadwick (1914) showed the beta spectrum is continuous. "
            "Ellis & Wooster (1927) settled by calorimetry that the "
            "continuum is real rather than an instrumental or "
            "secondary effect -- this is the step that made the crisis "
            "inescapable. Pauli's letter of 4 December 1930 proposed a "
            "neutral spin-1/2 particle in response. Fermi (1934) gave "
            "the theory and the name."),
        "historical_precision": (
            "Pauli's original particle was a *nuclear constituent*, "
            "not a decay product. The modern 'third body created at "
            "decay' reading is Fermi's 1934 reinterpretation. Saying "
            "'Pauli 1930 requires a third body' flattens that step, so "
            "it is separated here."),
        "references": HISTORICAL_REFERENCES,
        "verdict": (
            "The antineutrino cannot be omitted. Its omission is not a "
            "simplification with a free parameter; it is a prediction "
            "that the electron spectrum is a line, and the spectrum is "
            "measured to be continuous. That measurement is decisive "
            "on its own, and the spin-1/2 counting argument excludes "
            "the omitted account independently of it."),
        "independence": INDEPENDENCE_NOTE,
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
