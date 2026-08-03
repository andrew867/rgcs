from __future__ import annotations

import cmath
import math
import shutil

import pytest

from rgcs_ardk.drive import (
    AuthorityRefused,
    effective_asymmetry,
    load_authority,
    mirror_weights,
    reverse_lag_weights,
    rotate_weights,
    table_weights,
)


def test_hash_pinned_r1073_authority_satisfies_locked_recipe():
    authority = load_authority()
    active = [row for row in authority.rows if row["active_floor_status"] == "OK"]
    assert authority.source_commit == "710e5947c80ea7a2299dc0a40fd63a4262891e39"
    assert len(authority.rows) == 37
    assert len(active) == 33
    assert min(row["amplitude_weight"] for row in active) == pytest.approx(0.544385754805932)
    assert authority.drive_table["mod"] == 0.5
    assert authority.drive_table["lag_rad"] == pytest.approx(math.pi)
    assert authority.drive_table["predicted_d_eff"]["magnitude"] == pytest.approx(0.4124, abs=2e-3)
    assert authority.drive_table["predicted_d_eff"]["offset_from_blank_axis_deg"] == pytest.approx(12.46, abs=0.1)


def test_seed_directory_is_structurally_refused():
    with pytest.raises(AuthorityRefused, match="seed"):
        load_authority("rgcs_ardk/drive/seed")


def test_modified_authority_is_refused(tmp_path):
    source = load_authority().root
    target = tmp_path / "authority"
    shutil.copytree(source, target)
    path = target / "drive_table.json"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(AuthorityRefused, match="stale or modified"):
        load_authority(target)


def test_equal_resource_randomizations_preserve_amplitude_multiset():
    authority = load_authority()
    baseline = sorted(round(row["amplitude_weight"], 12) for row in authority.rows)
    randomized = authority.null_masks["equal_resource_randomized"]
    assert len(randomized) == 8
    for control in randomized:
        amplitudes = sorted(round(abs(complex(*pair)), 12) for pair in control["weights"])
        assert control["equal_resource"] is True
        assert amplitudes == baseline


@pytest.mark.parametrize("cells", [1, 7, 36, 38])
def test_rotated_table_advances_by_exact_cell_pitch(cells):
    weights = table_weights(load_authority().rows)
    before = effective_asymmetry(weights)
    after = effective_asymmetry(rotate_weights(weights, cells))
    advance = math.degrees(cmath.phase(after / before)) % 360.0
    assert advance == pytest.approx((360.0 * cells / 37) % 360.0, abs=1e-9)
    assert abs(after) == pytest.approx(abs(before), abs=1e-12)


def test_mirror_negates_direction():
    weights = table_weights(load_authority().rows)
    before = effective_asymmetry(weights)
    after = effective_asymmetry(mirror_weights(weights))
    assert after == pytest.approx(before.conjugate(), abs=1e-12)


def test_reversed_lag_negates_offset_and_preserves_magnitude():
    authority = load_authority()
    tables = authority.null_masks["weight_tables"]
    forward = effective_asymmetry(table_weights(authority.rows))
    reverse = effective_asymmetry(reverse_lag_weights(authority.null_masks))
    amplitude_axis = effective_asymmetry([complex(*pair) for pair in tables["binary_blanking_best"]])
    axis = cmath.phase(amplitude_axis)
    forward_offset = (cmath.phase(forward) - axis + math.pi) % (2 * math.pi) - math.pi
    reverse_offset = (cmath.phase(reverse) - axis + math.pi) % (2 * math.pi) - math.pi
    assert reverse_offset == pytest.approx(-forward_offset, abs=1e-12)
    assert abs(reverse) == pytest.approx(abs(forward), abs=1e-12)
