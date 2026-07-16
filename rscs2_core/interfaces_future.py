"""Future microscopic interfaces I001-I011 (Agent C13; gate G15).

Typed INTERFACE_ONLY registry: every intentionally deferred
microscopic capability has a declared contract and a request path
that NEVER emits a numeric result."""

from __future__ import annotations

INTERFACES = {
    "I001": ("DFT", "ground-state electronic structure"),
    "I002": ("Bethe-Salpeter", "excitonic optical response"),
    "I003": ("ab-initio spin dynamics", "microscopic spin evolution"),
    "I004": ("microscopic proton tunnelling",
             "double-well quantum dynamics"),
    "I005": ("microscopic plasmonics", "near-field EM at atomic "
             "scale"),
    "I006": ("QFT/QED", "field-theoretic processes"),
    "I007": ("nonclassical photon generation",
             "quantum-statistical light sources"),
    "I008": ("full quantum transduction",
             "coherent microwave-optical conversion"),
    "I009": ("quantum-computing simulators",
             "circuit/annealing simulation"),
    "I010": ("full fluid chemistry", "aqueous speciation/kinetics"),
    "I011": ("complete microscopic consciousness theory",
             "no such validated theory exists anywhere"),
}


class FutureInterfaceError(RuntimeError):
    pass


def interface_record(iid: str) -> dict:
    if iid not in INTERFACES:
        raise KeyError(f"unknown interface id {iid}")
    name, scope = INTERFACES[iid]
    return {"interface_id": iid, "name": name, "scope": scope,
            "classification": "INTERFACE_ONLY",
            "evidence_tags": ["ENG"], "value": None,
            "contract": {"inputs": "typed problem description",
                         "outputs": "typed result envelope",
                         "status": "NO SOLVER IMPLEMENTED"},
            "note": "deferred by design; a request cannot produce a "
                    "number (gate G15)"}


def request_computation(iid: str, *_args, **_kw):
    """The only executable path: refuses with an honest error."""
    rec = interface_record(iid)
    raise FutureInterfaceError(
        f"{rec['name']} ({iid}) is INTERFACE_ONLY: no solver is "
        "implemented; no fake result will be fabricated")
