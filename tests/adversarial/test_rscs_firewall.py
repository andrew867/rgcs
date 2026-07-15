"""Adversarial tests for the RSCS claim/provenance firewall, id/collision
lint, HYP quarantine, and protection of the frozen RGCS registry."""
from __future__ import annotations

import pathlib

import numpy as np
import pytest
import yaml

from rscs_core import operators as ops
from rscs_core.coordinates import (COORDINATE_TYPES, ModalState, MemoryLattice,
                                   ProvenanceTag)
from rscs_core.registry import (assert_no_src_upgrade, classification_of,
                                load_registry, registry_ids)
from rscs_core.transforms import space_to_phase

REPO = pathlib.Path(__file__).resolve().parents[2]


# --- claim firewall: no SRC/HYP -> EST/DER laundering ---

def test_no_src_upgrade():
    # EST output from an SRC input is forbidden
    with pytest.raises(ValueError):
        assert_no_src_upgrade("EST", "SRC")
    with pytest.raises(ValueError):
        assert_no_src_upgrade("DER", "HYP")
    # same or weaker is allowed
    assert_no_src_upgrade("HYP", "HYP")
    assert_no_src_upgrade("SRC", "EST")


def test_provenance_propagate_caps_class():
    src = ProvenanceTag("SRC-3-07", "SRC")
    # declaring an EST output from an SRC input must raise (firewall)
    with pytest.raises(ValueError):
        ops.propagate_provenance("bad_op", "EST", src)
    # a HYP boundary node is allowed
    out = ops.propagate_provenance("bridge", "HYP", src)
    assert out.claim_class == "HYP"


# --- HYP quarantine (NHT/HAL) ---

def test_memory_lattice_quarantined():
    with pytest.raises(ValueError):
        MemoryLattice((0,), [0.0])  # missing acknowledge_hypothesis


def test_memory_store_requires_ack():
    s = ModalState.from_components([1 + 0j, 0 + 1j])
    with pytest.raises(ValueError):
        ops.memory_store(s, (0, 1))  # acknowledge_hypothesis defaults False
    lat = ops.memory_store(s, (0, 1), acknowledge_hypothesis=True)
    assert lat.claim_class == "HYP"


def test_space_to_phase_is_hyp():
    assert classification_of(space_to_phase).label == "HYP"


# --- registry integrity and id/collision lint ---

def test_registry_ids_unique_and_expected():
    ids = registry_ids()
    coords = {f"RSCS-C.{i}" for i in range(1, 15)}
    opers = {f"RSCS-O.{i}" for i in range(1, 14)}
    assert coords | opers <= ids


def test_no_rscs_m_namespace_used():
    # RSCS-M.* is reserved and must NOT appear as an id (avoids RGCS-M clash)
    data = load_registry()
    for kind in ("coordinates", "operators"):
        for e in data[kind]:
            assert not e["id"].startswith("RSCS-M."), e["id"]


def test_every_coordinate_class_maps_to_registry():
    ids = registry_ids()
    for cid in COORDINATE_TYPES:
        assert cid in ids


def test_every_operator_has_classification_and_registry_row():
    ids = registry_ids()
    for oid, fn in ops.OPERATORS.items():
        meta = classification_of(fn)
        assert oid in ids
        assert oid in meta.registry, f"{oid} not in {fn.__name__} metadata"


def test_registry_entries_have_tests():
    data = load_registry()
    for kind in ("coordinates", "operators"):
        for e in data[kind]:
            assert e["tests"], f"{e['id']} has no tests"


# --- frozen RGCS registry must not be touched ---

def test_rgcs_registry_still_61_and_schema1():
    with open(REPO / "docs" / "model_registry.yaml", encoding="utf-8") as fh:
        reg = yaml.safe_load(fh)
    assert reg["schema_version"] == 1
    assert len(reg["models"]) == 61
    ids = [m["id"] for m in reg["models"]]
    assert ids[0] == "RGCS-M.1" and ids[-1] == "RGCS-M.61"


# --- coordinate validation: malformed serialization / bad units ---

def test_malformed_modal_state_rejected():
    with pytest.raises(ValueError):
        ModalState(np.array([], dtype=complex))


def test_incompatible_coupling_size_rejected():
    s = ModalState.from_components([1 + 0j, 0 + 1j])
    with pytest.raises(ValueError):
        ops.apply_coupling(s, [[0.0, 1.0, 0.0], [1.0, 0.0, 1.0],
                                [0.0, 1.0, 0.0]], 1e-4)


# --- HG memory bridge: ENG classification + NHT/HAL exclusion carried ---

def test_hg_operators_are_eng_never_evidence():
    from rscs_core.memory import hg_store, hg_replay, hg_update
    for fn in (hg_store, hg_replay, hg_update):
        assert classification_of(fn).label == "ENG"


def test_hg_store_carries_nht_exclusion():
    from rscs_core.memory import hg_store
    meta = classification_of(hg_store)
    joined = " ".join(meta.exclusions).lower()
    assert "src-3-07" in joined and "quartz" in joined


def test_hg_registry_ids_present():
    ids = registry_ids()
    assert {"RSCS-C.15", "RSCS-O.14", "RSCS-O.15", "RSCS-O.16"} <= ids


def test_nht_lattice_still_hyp_quarantined():
    # Agent 04 must NOT have promoted the NHT lattice out of HYP quarantine.
    from rscs_core.transforms import space_to_phase
    from rscs_core.memory import store as lattice_store
    assert classification_of(space_to_phase).label == "HYP"
    assert classification_of(lattice_store).label == "HYP"
