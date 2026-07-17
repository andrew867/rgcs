"""Unified reduced-model playground (Agent Q06) — NEUTRAL GROUND.

This module deliberately lives OUTSIDE rscs2_core and OUTSIDE
consciousness_lane: the playground compares reduced-model MATHEMATICS
across lanes, so it may import from both — but neither lane may
import IT, and its envelopes are structurally unable to carry
evidence (REFERENCE_MATHEMATICS_ONLY, immutable source labels).

History: the first version lived in rscs2_core.refmodels and was
caught by audit gate G51 (quartz module referencing the quarantined
lane). Moving it here preserves the quarantine in both directions
instead of weakening the gate.
"""

from __future__ import annotations

# --- Q06: unified playground ------------------------------------------------

REGISTERED_MODELS = {
    "spin_electric": {"module": "rscs2_core.refmodels.spin_electric",
                      "source_system": "FePc on MgO (mK, STM)",
                      "doi": "10.1038/s41567-026-03353-w"},
    "triangular_transport": {
        "module": "rscs2_core.refmodels.triangular_transport",
        "source_system": "TBTAP on Pb(111) (cryogenic STM)",
        "doi": "10.1038/s41467-026-75051-3"},
    "honeycomb_vhs": {"module": "rscs2_core.refmodels.honeycomb_vhs",
                      "source_system": "boron surface state in "
                                       "LaRh3B2",
                      "doi": "10.1126/sciadv.aee3116"},
    "filtration_solver": {
        "module": "rscs2_core.refmodels.filtration_solver",
        "source_system": "Feynman-integral families (workflow "
                         "analogy only)",
        "doi": "10.1103/pyt8-d7rt"},
    "composite_modes": {
        "module": "resonator_platform.composite_modes",
        "source_system": "CANISIUS neutron spin-echo interferometer",
        "doi": "10.1063/5.0321755"},
    "kuramoto": {"module": "consciousness_lane.reduced_models",
                 "source_system": "abstract oscillator population "
                                  "(quarantined lane)",
                 "doi": None},
}


class PlaygroundError(RuntimeError):
    pass


def run_model(name: str, function: str, /, **kwargs) -> dict:
    """Run a registered reduced model. The result is wrapped with its
    immutable source-system label and an evidence firewall: the
    returned envelope has no writable evidence field, and the label
    cannot be omitted."""
    import importlib
    if name not in REGISTERED_MODELS:
        raise PlaygroundError(f"unregistered model {name}")
    meta = REGISTERED_MODELS[name]
    mod = importlib.import_module(meta["module"])
    fn = getattr(mod, function, None)
    if fn is None:
        raise PlaygroundError(f"{name} has no function {function}")
    result = fn(**kwargs)
    return {
        "model": name,
        "source_system": meta["source_system"],   # immutable label
        "doi": meta["doi"],
        "result": result,
        "evidence_status": "REFERENCE_MATHEMATICS_ONLY",
        "firewall": "playground results cannot be registered as "
                    "evidence for any physical RGCS artifact; "
                    "comparing mathematics is permitted, physical "
                    "identity is not",
    }


def compare(envelopes: list, quantity: str) -> dict:
    """Compare a named quantity across model envelopes. The output
    keeps every source-system label attached to its number, so a
    comparison table cannot silently merge systems."""
    rows = []
    for e in envelopes:
        val = e["result"].get(quantity) if isinstance(e["result"],
                                                      dict) else None
        rows.append({"model": e["model"],
                     "source_system": e["source_system"],
                     quantity: val})
    return {"quantity": quantity, "rows": rows,
            "note": "mathematical comparison only; the systems "
                    "remain physically distinct"}
