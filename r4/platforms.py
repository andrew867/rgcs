"""A35-A41 — the physical four-state platform registry and decision
matrix.

Nothing in this module is a measurement. Each entry records what the
published literature supports for that platform, what this programme
would still have to qualify, and which stop-matrix gates are open.

The three refusals that matter:

- **Four spin-1/2 directions are not four states.** Tetrahedral
  directions overlap at -1/3; a spin-1/2 has a two-dimensional Hilbert
  space and holds one qubit, not two bits.
- **Quartz is BLOCKED** (R36). No identified spin-active defect with a
  demonstrated write/read/reset chain exists in this programme's
  specimen, so the platform cannot be selected however attractive the
  source narrative is.
- **Classical four-domain devices are not coherent spin memory.** They
  can carry quaternary symbols perfectly well, and that is a different
  claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import (PHYSICAL_GATES, ClaimBoundaryError, PhysicalGateBlocked,
               validate_four_state_type)


@dataclass(frozen=True)
class Platform:
    id: str
    four_state_type: str
    native_levels: int
    orthogonal_states: bool
    coherent: bool
    typical_temperature_K: str
    literature_status: str
    open_gates: tuple
    limitations: str
    selectable: bool

    def __post_init__(self):
        validate_four_state_type(self.four_state_type)
        for g in self.open_gates:
            if g not in PHYSICAL_GATES.values():
                raise ClaimBoundaryError(
                    f"{g!r} is not a stop-matrix status")


REGISTRY = {
    "SIC_V_SI_SPIN_3_2": Platform(
        id="SIC_V_SI_SPIN_3_2",
        four_state_type="SPIN_THREE_HALVES",
        native_levels=4, orthogonal_states=True, coherent=True,
        typical_temperature_K="4-300 (defect and readout dependent)",
        literature_status=(
            "silicon vacancy in 4H-SiC is an established spin-3/2 "
            "system with optical initialization and ODMR readout "
            "reported in the literature"),
        open_gates=("READOUT_DEGENERATE", "RETENTION_UNMEASURED",
                    "CROSSTALK_UNBOUNDED", "CALIBRATION_INCOMPLETE"),
        limitations=(
            "full four-level discrimination is nontrivial: optical "
            "readout commonly distinguishes |m_s|=1/2 from |m_s|=3/2 "
            "PAIRS rather than all four levels, so sign resolution "
            "needs extra control; spectator transitions and strain "
            "inhomogeneity matter"),
        selectable=True),
    "DIAMOND_NV_PLUS_N15": Platform(
        id="DIAMOND_NV_PLUS_N15",
        four_state_type="TWO_COUPLED_SPIN_HALF",
        native_levels=4, orthogonal_states=True, coherent=True,
        typical_temperature_K="300",
        literature_status=(
            "NV electron spin coupled to a 15N nuclear spin gives four "
            "orthogonal product states with well-developed control"),
        open_gates=("RETENTION_UNMEASURED", "CROSSTALK_UNBOUNDED",
                    "CALIBRATION_INCOMPLETE"),
        limitations=(
            "four states come from TWO spins, not one four-level "
            "system; addressing density is limited by optical "
            "diffraction unless super-resolution is used"),
        selectable=True),
    "CLASSICAL_FOUR_DOMAIN": Platform(
        id="CLASSICAL_FOUR_DOMAIN",
        four_state_type="FOUR_CLASSICAL_DOMAINS",
        native_levels=4, orthogonal_states=True, coherent=False,
        typical_temperature_K="300",
        literature_status=(
            "multilevel resistive/magnetic cells with four stable "
            "states are ordinary engineering"),
        open_gates=("RETENTION_UNMEASURED",),
        limitations=(
            "NOT coherent spin memory. Perfectly good for quaternary "
            "symbol storage; it tests the codec, not the spin "
            "hypothesis"),
        selectable=True),
    "SPIN_HALF_TETRAHEDRAL": Platform(
        id="SPIN_HALF_TETRAHEDRAL",
        four_state_type="SPIN_HALF_FOUR_DIRECTIONS",
        native_levels=2, orthogonal_states=False, coherent=True,
        typical_temperature_K="n/a",
        literature_status=(
            "four tetrahedral Bloch directions form a SIC-POVM frame; "
            "informationally complete for measurement"),
        open_gates=("FOUR_STATE_MANIFOLD_UNPROVEN",
                    "READOUT_DEGENERATE"),
        limitations=(
            "REFUSED as memory: a spin-1/2 has a 2-dimensional Hilbert "
            "space. Four non-orthogonal directions (overlap -1/3) "
            "cannot be deterministically distinguished, so they do not "
            "store two bits"),
        selectable=False),
    "QUARTZ_DEFECT": Platform(
        id="QUARTZ_DEFECT",
        four_state_type="QUARTZ_DEFECT_PLATFORM",
        native_levels=0, orthogonal_states=False, coherent=False,
        typical_temperature_K="unknown",
        literature_status=(
            "alpha-quartz hosts paramagnetic defect centres (e.g. E' "
            "and Al-hole centres) studied by EPR; none is qualified "
            "here as an addressable four-level memory"),
        open_gates=tuple(PHYSICAL_GATES.values()),
        limitations=(
            "BLOCKED: no identified defect with a demonstrated "
            "write/read/reset chain in this programme's specimen. The "
            "source narrative motivates the lane; it does not qualify "
            "the platform"),
        selectable=False),
}


def select_platform(pid: str) -> Platform:
    """Selection refuses blocked platforms, with the reason."""
    if pid not in REGISTRY:
        raise ClaimBoundaryError(f"unknown platform {pid!r}")
    p = REGISTRY[pid]
    if not p.selectable:
        raise PhysicalGateBlocked(
            f"{pid} is not selectable: {p.limitations}")
    return p


def decision_matrix() -> dict:
    """A40: rank selectable platforms on what this programme actually
    needs, and record the sensitivity of the ranking (A37)."""
    rows = []
    for p in REGISTRY.values():
        score = 0
        if p.selectable:
            score += 2
        if p.orthogonal_states:
            score += 2
        if p.native_levels >= 4:
            score += 1
        if p.coherent:
            score += 1
        score -= len(p.open_gates) * 0.5
        rows.append({"platform": p.id, "score": score,
                     "selectable": p.selectable,
                     "coherent": p.coherent,
                     "open_gates": len(p.open_gates)})
    rows.sort(key=lambda r: -r["score"])
    top = rows[0]["platform"]
    # sensitivity: does dropping the coherence requirement change the top?
    alt = sorted(rows, key=lambda r: -(r["score"] -
                                       (1 if REGISTRY[r["platform"]].coherent
                                        else 0)))
    return {
        "ranking": rows,
        "recommended_for_coherent_spin_memory": top,
        "recommended_if_coherence_not_required":
            alt[0]["platform"],
        "sensitivity_note":
            "the ranking is sensitive to whether coherence is "
            "required: a classical four-domain cell is the easiest "
            "quaternary carrier but tests the CODEC only, not the "
            "spin hypothesis",
        "quartz_status": "BLOCKED",
        "physical_status": "UNTESTED — no platform has been operated",
        "evidence_class": "ANALYTIC_MODEL",
    }


def stop_matrix_report(pid: str) -> dict:
    """Which gates block this platform right now (core/13)."""
    p = REGISTRY[pid]
    return {"platform": pid,
            "open_gates": list(p.open_gates),
            "n_open": len(p.open_gates),
            "may_continue_in_simulation": True,
            "may_emit_physical_verdict": False,
            "note": "the programme may continue in simulation when a "
                    "physical gate is blocked; it may not synthesize a "
                    "physical verdict"}
