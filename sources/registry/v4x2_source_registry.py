"""B01: the five 2026 papers as typed source records with hashes,
claim cards, allowed/forbidden transfers, and the transfer firewall
(coverage B009-B016).

The PDFs live under gitignored internal-docs/ (LOCAL_ANALYSIS_ONLY,
never redistributed); the registry commits hashes and derived claim
cards only. Every record separates measurement / model / inference /
speculation, and the firewall test rejects direct quartz claims."""

from __future__ import annotations

LOCAL_DIR = "internal-docs/plans-v4/references"

SOURCES = {
 "SRC-V4X2-01": {
    "title": "Exchange-mediated spin-electric control of single "
             "molecules on surfaces",
    "doi": "10.1038/s41567-026-03353-w",
    "file": "s41567-026-03353-w.pdf",
    "sha256_prefix": "019435a03b3c5e9d",
    "size_bytes": 3672570,
    "publication_state": "published",
    "system": "FePc and Fe-FePc on MgO/Ag(001)",
    "apparatus": "ESR-STM with spin-polarized tip",
    "conditions": {"temperature_k": [0.05, 1.0],
                   "environment": "UHV, cryogenic STM"},
    "claim_card": {
        "measurement": ["bias-dependent spin-resonance shifts, "
                        "relative shifts approaching tens of percent "
                        "near orbital thresholds",
                        "all-electrical Rabi detuning in a coupled "
                        "molecular-spin pair"],
        "model": ["exchange field follows orbital occupation "
                  "(nonlinear near threshold)"],
        "inference": ["local electrical control of individual spins "
                      "in a pair"],
        "speculation": [],
        "limitations": ["millikelvin temperatures; single molecules; "
                        "STM junction geometry"]},
    "allowed_transfers": ["two-level detuning mathematics",
                          "tunability-vs-linewidth bookkeeping"],
    "forbidden_transfers": ["alpha quartz", "room temperature",
                            "macroscopic resonators"],
    "equations": [
        {"id": "EQ-V4X2-01a", "eq": "J(V) = J0 * sigma((V-Vth)/w)",
         "provenance": "main text, exchange-field bias dependence",
         "implemented": "refmodels/spin_electric.py:"
                        "exchange_field_mev"},
        {"id": "EQ-V4X2-01b",
         "eq": "Omega_eff = sqrt(Omega^2 + delta^2)",
         "provenance": "standard two-level result used by the paper",
         "implemented": "refmodels/spin_electric.py:rabi_detuning"}],
 },
 "SRC-V4X2-02": {
    "title": "Non-equilibrium correlated electron dynamics in "
             "triangular molecular assemblies",
    "doi": "10.1038/s41467-026-75051-3",
    "file": "s41467-026-75051-3_reference.pdf",
    "sha256_prefix": "7e1df086615c6bac",
    "size_bytes": 6178632,
    "publication_state": "article in press (unedited manuscript in "
                         "the supplied file)",
    "system": "TBTAP trimers and hexamers on Pb(111)",
    "apparatus": "STM",
    "conditions": {"temperature_k": [4.0, 8.0],
                   "environment": "UHV STM"},
    "claim_card": {
        "measurement": ["charging-ring and conductance features",
                        "negative differential conductance",
                        "chiral spatial response"],
        "model": ["three-impurity Anderson model + Pauli master "
                  "equation"],
        "inference": ["many features arise from INTERNAL CHARGE "
                      "REARRANGEMENT without changing total cluster "
                      "charge"],
        "speculation": [],
        "limitations": ["in-press manuscript; final version may "
                        "differ (drift guard below)"]},
    "allowed_transfers": ["master-equation bookkeeping",
                          "total-change vs redistribution vs "
                          "trapping vs transfer-function "
                          "classification"],
    "forbidden_transfers": ["charging physics to PCB or quartz"],
    "equations": [
        {"id": "EQ-V4X2-02a",
         "eq": "E(n) = sum eps_i n_i + V sum_{i<j} n_i n_j",
         "provenance": "three-impurity Anderson Hamiltonian "
                       "(diagonal part)",
         "implemented": "refmodels/triangular_transport.py:"
                        "state_energy"},
        {"id": "EQ-V4X2-02b",
         "eq": "Pauli master equation with Fermi-factor rates",
         "provenance": "transport model section",
         "implemented": "refmodels/triangular_transport.py:rates"}],
 },
 "SRC-V4X2-03": {
    "title": "Realization of strongly correlated 2D honeycomb boron",
    "doi": "10.1126/sciadv.aee3116",
    "file": "sciadv.aee3116.pdf",
    "sha256_prefix": "b8e387558cb0a0f0",
    "size_bytes": 3778955,
    "publication_state": "published",
    "system": "expanded honeycomb boron surface state in LaRh3B2",
    "apparatus": "ARPES + STM, DFT and tight binding support",
    "conditions": {"temperature_k": [4.0, 30.0]},
    "claim_card": {
        "measurement": ["strongly narrowed boron-derived band",
                        "extended saddle point pinned near E_F",
                        "QPI consistent with C6-to-C2 breaking"],
        "model": ["tight binding with expansion-reduced hopping"],
        "inference": ["nematicity consistent with the QPI "
                      "anisotropy"],
        "speculation": ["proximity to correlated phases"],
        "limitations": ["surface state; specific material"]},
    "allowed_transfers": ["lattice/DOS/symmetry mathematics",
                          "spacing-tunes-bandwidth design "
                          "principle"],
    "forbidden_transfers": ["electronic nematicity in PCB "
                            "resonators or quartz"],
    "equations": [
        {"id": "EQ-V4X2-03a",
         "eq": "E(k) = +/-|t1 e^{ik d1} + t2 e^{ik d2} "
               "+ t3 e^{ik d3}|",
         "provenance": "honeycomb NN tight binding",
         "implemented": "refmodels/honeycomb_vhs.py:band_energies"}],
 },
 "SRC-V4X2-04": {
    "title": "Geometric bookkeeping guide to Feynman-integral "
             "reduction and epsilon-factorized differential "
             "equations",
    "doi": "10.1103/pyt8-d7rt",
    "file": "pyt8-d7rt.pdf",
    "sha256_prefix": "473ab08fd766fe38",
    "size_bytes": 360933,
    "publication_state": "published",
    "system": "dimensionally regulated Feynman-integral families",
    "apparatus": "n/a (mathematical methods)",
    "conditions": {},
    "claim_card": {
        "measurement": [],
        "model": ["filtration ordering + prefactor selection "
                  "produce structured, epsilon-factorized systems"],
        "inference": ["large expression-size reductions in some "
                      "examples"],
        "speculation": ["that the proposed order ALWAYS yields the "
                        "compatible structure — the paper itself "
                        "marks this conjectural, and this registry "
                        "preserves the caveat"],
        "limitations": ["conjectural generality"]},
    "allowed_transfers": ["basis-selection / filtration / "
                          "nuisance-separation WORKFLOW"],
    "forbidden_transfers": ["Feynman-integral results", "QFT claims "
                            "of any kind"],
    "equations": [
        {"id": "EQ-V4X2-04a",
         "eq": "A(eps) similar to L0 + eps L1 (factorized form)",
         "provenance": "epsilon-factorization target form",
         "implemented": "refmodels/filtration_solver.py:"
                        "eps_factorization_check"}],
 },
 "SRC-V4X2-05": {
    "title": "White-beam spin-echo interferometer for neutron "
             "orbital angular momentum generation",
    "doi": "10.1063/5.0321755",
    "file": "065211_1_5.0321755.pdf",
    "sha256_prefix": "32f952347682a67e",
    "size_bytes": 7968886,
    "publication_state": "published",
    "system": "CANISIUS broadband spin-echo interferometer",
    "apparatus": "white-beam neutron spin-echo",
    "conditions": {"beam": "white (broadband) neutrons"},
    "claim_card": {
        "measurement": ["composite neutron wavefunctions with "
                        "selected angular-mode content",
                        "spin-echo scale calibrated against a known "
                        "nanoporous sample and a second instrument "
                        "after deviating from ideal prediction"],
        "model": ["incomplete transverse recombination + controlled "
                  "phase -> mode-parity selection; residual "
                  "separation vs coherence controls the mode "
                  "distribution"],
        "inference": [],
        "speculation": [],
        "limitations": ["instrument-specific calibration correction "
                        "was required — the calibration lesson "
                        "transfers, the numbers do not"]},
    "allowed_transfers": ["coherent-sum and azimuthal "
                          "mode-decomposition mathematics"],
    "forbidden_transfers": ["neutron physics", "OAM-beam claims for "
                            "resonators"],
    "equations": [
        {"id": "EQ-V4X2-05a",
         "eq": "psi = g(r-d/2) + e^{i phi} g(r+d/2)",
         "provenance": "composite-state construction",
         "implemented": "resonator_platform/composite_modes.py:"
                        "displaced_gaussian_pair"},
        {"id": "EQ-V4X2-05b",
         "eq": "c_m = <e^{i m phi}|psi>",
         "provenance": "azimuthal decomposition",
         "implemented": "resonator_platform/composite_modes.py:"
                        "azimuthal_content"}],
 },
}


class TransferFirewall(RuntimeError):
    pass


QUARTZ_TARGETS = ("quartz", "alpha quartz", "crystal specimen",
                  "wand", "110 mm")


def check_transfer(source_id: str, target: str, what: str) -> dict:
    """The mechanical guard (B012/B015): a transfer is allowed only if
    `what` matches an allowed transfer AND the target is not a
    forbidden system for that source."""
    src = SOURCES[source_id]
    t = target.lower()
    for forbidden in src["forbidden_transfers"]:
        if any(k in t for k in forbidden.lower().split()[:2]) or \
                any(q in t for q in QUARTZ_TARGETS):
            raise TransferFirewall(
                f"{source_id} forbids transfer to {target!r}: "
                f"{src['forbidden_transfers']}")
    allowed = any(a.lower().split()[0] in what.lower()
                  for a in src["allowed_transfers"])
    return {"source": source_id, "target": target, "what": what,
            "allowed": allowed,
            "note": "mathematics may transfer; the physics stays in "
                    "its system"}


def lookup(key: str) -> dict:
    """B014: lookup by source id, DOI, filename, or equation id."""
    if key in SOURCES:
        return SOURCES[key]
    for sid, s in SOURCES.items():
        if s["doi"] == key or s["file"] == key:
            return s
        for eq in s["equations"]:
            if eq["id"] == key:
                return {"source_id": sid, **eq}
    raise KeyError(f"no source or equation matches {key!r}")


def concept_map() -> dict:
    """B016: cross-source concepts WITHOUT asserting a shared physical
    mechanism."""
    return {
        "shared_concepts": {
            "nonlinear parameter tuning": ["SRC-V4X2-01"],
            "collective/internal state vs total state":
                ["SRC-V4X2-02"],
            "geometry reshapes state density": ["SRC-V4X2-03"],
            "basis choice reveals structure": ["SRC-V4X2-04"],
            "phase selects mode content": ["SRC-V4X2-05"],
        },
        "explicit_disclaimer": "these papers do NOT jointly "
                               "establish a single physical "
                               "mechanism; the map is conceptual "
                               "navigation only (B016)",
    }


def drift_guard() -> dict:
    """B015: the in-press paper may change on publication. Public
    docs citing SRC-V4X2-02 must carry the in-press marker until the
    hash of a final version is registered."""
    return {"SRC-V4X2-02": {
        "state": "article in press",
        "action_on_final_publication":
            "register the final PDF hash as a NEW record; never "
            "overwrite this one; re-verify every claim card entry "
            "against the final text"}}
