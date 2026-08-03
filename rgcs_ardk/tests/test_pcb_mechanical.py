from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rgcs_ardk.drive import AuthorityRefused, load_authority
from rgcs_ardk.geometry import AnnularGeometry
from rgcs_ardk.mech import FixtureModel, render_openscad
from rgcs_ardk.pcb.generator import generate_boards, render_board
from rgcs_ardk.pcb.model import BoardVariant, net_registry, validate_net_registry


def test_net_registry_is_complete_unique_and_checked_in():
    validate_net_registry()
    records = net_registry()
    assert len(records) == 37 * 5 + 3 + 8
    assert len({record.name for record in records}) == len(records)


def test_board_variants_are_separate_and_feature_correct():
    authority = load_authority()
    board_a = render_board(BoardVariant.BOARD_A, authority)
    board_b = render_board(BoardVariant.BOARD_B, authority)
    assert 'BOARD_VARIANT" "RGCS_ARDK_001_BoardA_PassiveSensor' in board_a
    assert 'BOARD_VARIANT" "RGCS_ARDK_001_BoardB_ActiveDrive' in board_b
    assert 'net_name "SENSE_00"' in board_a
    assert 'net_name "DRV_00"' not in board_a
    assert 'net_name "LOAD_00"' not in board_a
    assert 'net_name "DRV_00"' in board_b
    assert 'net_name "LOAD_00"' in board_b
    assert 'TPKELVIN_P_00' in board_b
    assert 'TPSENSE_00' in board_b


def test_board_outline_and_sector_geometry_are_locked():
    text = render_board(BoardVariant.BOARD_A, load_authority())
    assert "(end 144 0)" in text
    assert "(end 94 0)" in text
    assert text.count('(net_name "SENSE_') == 37
    assert text.count("np_thru_hole") == 4
    assert text.count("(zone") == 37
    assert text.count("(") == text.count(")")


def test_kicad_generation_is_byte_deterministic_and_not_fab_ready(tmp_path):
    first_dir = tmp_path / "one"
    second_dir = tmp_path / "two"
    first = generate_boards(first_dir)
    second = generate_boards(second_dir)
    assert [item.board_sha256 for item in first] == [item.board_sha256 for item in second]
    assert [item.metadata_sha256 for item in first] == [item.metadata_sha256 for item in second]
    for left, right in zip(first, second):
        assert left.board_path.read_bytes() == right.board_path.read_bytes()
        metadata = json.loads(left.metadata_path.read_text(encoding="utf-8"))
        assert metadata["fabrication_ready"] is False
        assert metadata["authority"]["seed_used"] is False
        assert metadata["drc_executed"] is False
        assert hashlib.sha256(left.board_path.read_bytes()).hexdigest() == metadata["board_sha256"]


def test_generator_refuses_seed_input(tmp_path):
    with pytest.raises(AuthorityRefused, match="seed"):
        generate_boards(tmp_path, authority_root="rgcs_ardk/drive/seed")


def test_fixture_and_pcb_mounting_holes_share_one_geometry():
    geometry = AnnularGeometry()
    fixture = FixtureModel().geometry
    assert fixture.mounting_holes() == geometry.mounting_holes()
    assert [hole.center for hole in fixture.mounting_holes()] == [
        hole.center for hole in geometry.mounting_holes()
    ]


def test_checked_in_openscad_is_generated_and_contains_no_electrical_registry():
    checked_in = Path("rgcs_ardk/mech/annular_fixture_revA.scad").read_text(encoding="utf-8")
    assert checked_in.replace("\r\n", "\n") == render_openscad()
    assert "pcb_mount_radius = 136" in checked_in
    assert "sector_count = 37" in checked_in
    assert "DRV_" not in checked_in
    assert "SENSE_" not in checked_in
