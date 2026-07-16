"""Agent Q1: independent adversarial attacks on the integrated
candidate — attacks the IMPLEMENTATION, not the implementers' fixtures.
Each attack either must be repelled or exposes a defect to fix."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core.multiphysics import (CouplingEdge, CouplingGraph,
                                     get_material, make_result)
from rscs2_core.multiphysics.coupling import CouplingRejected


def test_attack_nan_and_inf_inputs_do_not_leak():
    """NaN fluence / inf coupling must not produce NaN 'alignments'
    that read like results."""
    from rscs2_core.refmodels import iome_linipo4 as io
    k = np.array([0.0, 1.0, 0.0])
    with pytest.raises(ValueError):
        io.write_domains("reference.linipo4", k, 1.0,
                         float("nan"), 2.0)
    with pytest.raises(ValueError):
        io.write_domains("reference.linipo4", k, 1.0, 1.0,
                         float("inf"))
    with pytest.raises(ValueError):
        io.write_domains("reference.linipo4", k, float("nan"),
                         1.0, 2.0)


def test_attack_capability_laundering_via_lying_edge():
    """A forged edge that smuggles an IOME/magnon operator under a
    capability quartz DOES have must be rejected (operator floor)."""
    q = get_material("material.alpha_quartz")
    g = CouplingGraph(q)
    with pytest.raises(CouplingRejected, match="operator .* requires"):
        g.add_edge(CouplingEdge(
            "optical", "domain", "op.iome_writing", "J", "toroidal",
            "elasticity_isotropic",       # lying requirement
            "REDUCED_ORDER_VALIDATED"))
    with pytest.raises(CouplingRejected, match="operator .* requires"):
        g.add_edge(CouplingEdge(
            "spin", "spin", "op.magnon_block", "Hz", "diag",
            "piezoelectric", "REDUCED_ORDER_VALIDATED"))
    # honest elasticity operator under the same capability is fine
    g.add_edge(CouplingEdge(
        "mechanical", "mechanical", "op.elastic_stiffness", "Pa",
        "sym", "elasticity_isotropic", "CORE_VALIDATED"))


def test_attack_classification_case_and_alias_tricks():
    with pytest.raises(ValueError):
        make_result("m", "material.alpha_quartz", "core_validated",
                    ["EST"], 1.0, {})
    with pytest.raises(ValueError):
        make_result("m", "material.alpha_quartz", "CORE_VALIDATED",
                    ["ESTABLISHED"], 1.0, {})
    q = get_material("material.alpha_quartz")
    with pytest.raises(KeyError):
        q.capability("magnonModes")           # camelCase alias


def test_attack_extreme_parameters_bounded():
    from rscs2_core.refmodels.metacrystal import (MetaAtomGeometry,
                                                  transfer_g2)
    geo = MetaAtomGeometry(100.0, 16, 0.0, "ring", 1.0)
    out = transfer_g2("reference.metacrystal", 1e6, geo)
    assert math.isfinite(out["value"]["g2_out"])
    from rscs2_core.refmodels.iome_linipo4 import written_alignment
    for law in ("tanh", "logistic", "linear_clip"):
        assert -1.0 <= written_alignment(1e9, law) <= 1.0


def test_attack_verdict_determinism_and_no_status_injection():
    from rscs2_core.eye import EyeConsensusResult
    with pytest.raises(ValueError, match="not allowed"):
        EyeConsensusResult("TOTALLY_STABLE_TRUST_ME", [], [], {}, {})


def test_attack_frozen_history_and_restricted_sources():
    import subprocess
    from pathlib import Path
    from rscs2_core import provenance_v4 as pv
    repo = Path(pv.__file__).resolve().parents[1]
    out = subprocess.run(["git", "diff", "--stat", "715486b", "HEAD",
                          "--", "archive/v2.0.0"],
                         capture_output=True, text=True, cwd=repo)
    assert out.stdout.strip() == ""
    staged = list((repo / "proof_bundle_110mm").rglob("*.pdf"))
    assert pv.release_filter(staged) == []


def test_attack_separation_never_rounded_by_any_path():
    """Regression re-check from an independent angle: feed the
    comparison helper the exact historical numbers."""
    from rscs2_core.eye import node_coincidence_comparison
    out = node_coincidence_comparison(
        np.array([-0.29476922, -0.20489281, 102.23976226]),
        np.array([[-0.44658144, 0.77350175, 106.01843443]]),
        3.0764499, 3.0764499, 3.0764499, 0.3533080, 0.0317713)
    assert out["separation_mm"] == pytest.approx(3.9062343, abs=1e-6)
    assert out["classification"] == \
        "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE"
    # with tight (refined-mesh-scale) localization the SAME numbers
    # become DISTINCT — the classification tracks uncertainty, not a
    # fixed radius
    tight = node_coincidence_comparison(
        np.array([-0.29476922, -0.20489281, 102.23976226]),
        np.array([[-0.44658144, 0.77350175, 106.01843443]]),
        1.2, 1.2, 1.2, 0.35, 0.03)
    assert tight["classification"] in (
        "NEAR_CONVENTIONAL_NODE_BUT_DISTINCT",
        "DISTINCT_FROM_CONVENTIONAL_NODE")
