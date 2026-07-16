"""Agent M2: capability firewall + coupling graph + envelope tests
(gates C1-C5, E5)."""
from __future__ import annotations

import json

import pytest

from rscs2_core.multiphysics import (CAPABILITY_KEYS, CouplingEdge,
                                     CouplingGraph, MATERIALS,
                                     applicability, get_material,
                                     make_result,
                                     not_applicable_result)
from rscs2_core.multiphysics.coupling import CouplingRejected
from rscs2_core.multiphysics.envelope import dumps
from rscs2_core.multiphysics.materials import capability_matrix_markdown


def test_all_sixteen_records_validate_with_full_keys():
    assert len(MATERIALS) == 16
    for m in MATERIALS.values():
        d = m.to_dict()
        assert set(d["capabilities"]) == set(CAPABILITY_KEYS)
        assert d["schema_version"].startswith("rgcs.v4")


def test_quartz_positive_capabilities():
    q = get_material("material.alpha_quartz")
    for k in ("elasticity_anisotropic", "piezoelectric",
              "dielectric_anisotropic", "photoelastic",
              "optical_birefringent"):
        app = applicability(q, k)
        assert app["applicability"] == "APPLICABLE", k
        assert app["classification"] == "CORE_VALIDATED"


def test_quartz_rejects_forbidden_mechanisms():
    """Gate C2/E5: quartz returns NOT_APPLICABLE for every magnetic /
    quantum-material mechanism, with a reason."""
    q = get_material("material.alpha_quartz")
    for k in ("magnetic_order", "magnon_modes", "exciton_frenkel",
              "exciton_magnon_coupling", "ferrotoroidic_order",
              "magnetoelectric_dynamic", "domain_writing",
              "quantum_statistical_response",
              "microscopic_tunnelling_model",
              "directional_optical_response"):
        app = applicability(q, k)
        assert app["applicability"] == "NOT_APPLICABLE", k
        assert app["reason"], k


def test_linipo4_positive_and_mnf2_comparator_shape():
    li = get_material("reference.linipo4")
    assert applicability(li, "ferrotoroidic_order")[
        "applicability"] == "REFERENCE_ONLY"
    assert applicability(li, "domain_writing")[
        "applicability"] == "REFERENCE_ONLY"
    assert li.reference_only
    mn = get_material("reference.mnf2")
    assert applicability(mn, "thermal_domain_selection")[
        "applicability"] == "REFERENCE_ONLY"
    # MnF2 is the polarization/thermal comparator, NOT an IOME material
    assert applicability(mn, "directional_optical_response")[
        "applicability"] == "NOT_APPLICABLE"


def test_unknown_is_not_permission():
    from rscs2_core.multiphysics.capabilities import (
        CapabilityRecord, MaterialCapabilities)
    caps = {k: CapabilityRecord() for k in CAPABILITY_KEYS}
    caps["magnon_modes"] = CapabilityRecord("UNKNOWN",
                                            "NOT_APPLICABLE")
    m = MaterialCapabilities("reference.tmp", "tmp", "test", True,
                             (), "none", "none", {},
                             capabilities=caps)
    app = applicability(m, "magnon_modes")
    assert app["applicability"] == "NOT_APPLICABLE"
    assert "UNKNOWN" in app["reason_code"]


def test_alias_confusion_rejected():
    with pytest.raises(KeyError, match="unregistered material"):
        get_material("material.alpha_quartz_magnetic")
    with pytest.raises(KeyError, match="unregistered material"):
        get_material("alpha_quartz")          # bare alias rejected
    q = get_material("material.alpha_quartz")
    with pytest.raises(KeyError, match="unregistered capability"):
        q.capability("torsion_field")         # invented alias


def test_coupling_graph_accepts_supported_edges():
    q = get_material("material.alpha_quartz")
    g = CouplingGraph(q)
    g.add_edge(CouplingEdge(
        "mechanical", "electrical", "op.piezo_stress_charge",
        "C/m^2 per strain", "class-32", "piezoelectric",
        "CORE_VALIDATED", ("SRC-V4-00",), ("RGCS-V4-EQ-005",)))
    out = g.compile()
    assert out["edges"][0]["operator_id"] == "op.piezo_stress_charge"
    assert "mechanical" in out["blocks"]


def test_coupling_graph_rejects_unsupported_edges():
    """Gate C4: unsupported coupling edges cannot activate."""
    q = get_material("material.alpha_quartz")
    g = CouplingGraph(q)
    with pytest.raises(CouplingRejected, match="lacks"):
        g.add_edge(CouplingEdge(
            "optical", "domain", "op.iome_writing", "J",
            "toroidal", "domain_writing", "REDUCED_ORDER_VALIDATED"))
    li = get_material("reference.linipo4")
    g2 = CouplingGraph(li)
    g2.add_edge(CouplingEdge(
        "optical", "domain", "op.iome_writing", "J", "toroidal",
        "domain_writing", "REDUCED_ORDER_VALIDATED", ("SRC-V4-01",),
        ("RGCS-V4-EQ-002",)))               # allowed for LiNiPO4 ref
    assert len(g2.edges) == 1


def test_source_hypothesis_block_cannot_drive_physics():
    li = get_material("reference.linipo4")
    g = CouplingGraph(li)
    with pytest.raises(CouplingRejected, match="quarantine"):
        g.add_edge(CouplingEdge(
            "source_hypothesis", "domain", "op.fdt_force", "N",
            "n/a", "domain_writing", "SOURCE_HYPOTHESIS"))


def test_envelope_no_fake_zero_and_reason_codes():
    """Gate C3."""
    with pytest.raises(ValueError, match="null value"):
        make_result("mod.x", "material.alpha_quartz",
                    "NOT_APPLICABLE", ["ENG"], 0.0, {})
    env = not_applicable_result(
        "mod.magnon", "material.alpha_quartz",
        "MATERIAL_CAPABILITY_ABSENT",
        "Alpha quartz has no registered magnetic-order capability.")
    assert env["value"] is None
    assert env["reason_code"] == "MATERIAL_CAPABILITY_ABSENT"
    assert env["classification"] == "NOT_APPLICABLE"


def test_envelope_blocks_laundering_and_serializes_deterministically():
    with pytest.raises(Exception, match="laundering"):
        make_result("mod.fdt", "source_hypothesis.fdt_adapter",
                    "CORE_VALIDATED", ["EST"], 1.0, {"F": "N"},
                    source_ids=["SRC-V4-18"])
    e1 = make_result("mod.a", "reference.linipo4",
                     "REDUCED_ORDER_VALIDATED", ["DER", "EST"], 1.5,
                     {"x": "m"}, source_ids=["SRC-V4-01"],
                     equation_ids=["RGCS-V4-EQ-002"])
    e2 = make_result("mod.a", "reference.linipo4",
                     "REDUCED_ORDER_VALIDATED", ["EST", "DER"], 1.5,
                     {"x": "m"}, source_ids=["SRC-V4-01"],
                     equation_ids=["RGCS-V4-EQ-002"])
    assert e1["result_id"] == e2["result_id"]
    assert dumps(e1) == dumps(e2)
    parsed = json.loads(dumps(e1))
    assert parsed["schema_version"] == "rgcs.v4.result.1"


def test_capability_matrix_generation_complete():
    """Gate C5: every material and capability appears."""
    md = capability_matrix_markdown()
    for m in MATERIALS.values():
        assert m.material_id.split(".")[-1] in md
        assert f"## {m.material_id}" in md
    for k in CAPABILITY_KEYS:
        assert k in md
    # quartz not-supported section names the banned mechanisms
    assert "magnon_modes" in md.split(
        "## material.alpha_quartz")[1].split("##")[0]


def test_malformed_material_records_rejected():
    from rscs2_core.multiphysics.capabilities import (
        CapabilityRecord, MaterialCapabilities)
    with pytest.raises(ValueError, match="missing capability"):
        MaterialCapabilities("reference.bad", "bad", "test", True, (),
                             "none", "none", {},
                             capabilities={"piezoelectric":
                                           CapabilityRecord()})
    with pytest.raises(ValueError, match="bad capability status"):
        CapabilityRecord(status="TOTALLY_FINE")
