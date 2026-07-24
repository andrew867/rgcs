"""P19 — the 192-feature disk: fixed width, contiguous unique indices,
partitioning groups, a freeze hash that changes on mutation, and the two
refusals."""

from __future__ import annotations

import dataclasses

import pytest

from r13 import diskdrive as D


# --- (1) the disk is exactly 192 features --------------------------------

def test_disk_is_exactly_192_features():
    assert len(D.DISK) == 192
    assert D.DISK_DIMENSIONS == 192


def test_indices_are_contiguous_unique_and_ordered():
    indices = [f.index for f in D.DISK]
    assert indices == list(range(192))          # 0..191, in order
    assert len(set(indices)) == 192             # all unique


def test_every_feature_is_well_formed():
    for f in D.DISK:
        assert isinstance(f, D.FeatureSpec)
        assert f.name
        assert isinstance(f.group, D.FeatureGroup)
        assert f.unit
        assert f.claim_class in D.CLAIM_CLASSES
        assert f.transform


def test_feature_at_round_trips_and_bounds_are_checked():
    assert D.feature_at(0).index == 0
    assert D.feature_at(191).index == 191
    with pytest.raises(D.DiskDriveError):
        D.feature_at(192)
    with pytest.raises(D.DiskDriveError):
        D.feature_at(-1)


# --- (2) the groups partition the disk -----------------------------------

def test_groups_partition_the_disk():
    assert D.groups_partition_the_disk() is True


def test_group_sizes_sum_to_192_and_cover_every_index_once():
    sizes = D.group_sizes()
    assert sum(sizes.values()) == 192
    seen: set[int] = set()
    for group in D.FeatureGroup:
        members = D.features_in_group(group)
        assert len(members) == sizes[group]
        for f in members:
            assert f.index not in seen          # no overlap
            seen.add(f.index)
    assert seen == set(range(192))              # no gaps


# --- (3) freeze by hash: stable, and changes on mutation (POWER) ---------

def test_disk_hash_is_stable_across_calls():
    assert D.disk_hash() == D.disk_hash()
    assert D.disk_hash() == D.DISK_HASH
    assert len(D.DISK_HASH) == 64


def test_disk_hash_changes_if_a_feature_is_altered():
    """POWER: the freeze must actually detect tampering. A single edited
    feature -- here just its unit -- must move the digest, or the hash
    would not be protecting anything."""
    mutated = list(D.DISK)
    mutated[100] = dataclasses.replace(mutated[100], unit="TAMPERED_UNIT")
    assert D.disk_hash(tuple(mutated)) != D.disk_hash()
    # a reordering also changes it
    swapped = list(D.DISK)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    assert D.disk_hash(tuple(swapped)) != D.disk_hash()


def test_verify_disk_hash():
    assert D.verify_disk_hash(D.DISK_HASH) is True
    assert D.verify_disk_hash("0" * 64) is False
    with pytest.raises(D.DiskDriveError):
        D.verify_disk_hash("too-short")


# --- (4) a feature is an input, never a decoded output -------------------

def test_refuse_feature_as_decoded_output_raises():
    with pytest.raises(D.DiskDriveError):
        D.refuse_feature_as_decoded_output(D.DISK[137])
    with pytest.raises(D.DiskDriveError):
        D.refuse_feature_as_decoded_output(42)


def test_refuse_disk_as_measurement_raises():
    with pytest.raises(D.DiskDriveError):
        D.refuse_disk_as_measurement()


# --- (5) a malformed feature is refused ----------------------------------

def test_malformed_feature_specs_are_refused():
    with pytest.raises(D.DiskDriveError):
        D.FeatureSpec(0, "", D.FeatureGroup.SPECTRAL, "u",
                      D.FEATURE_CLAIM_CLASS, "t")
    with pytest.raises(D.DiskDriveError):
        D.FeatureSpec(-1, "n", D.FeatureGroup.SPECTRAL, "u",
                      D.FEATURE_CLAIM_CLASS, "t")
    with pytest.raises(D.DiskDriveError):
        D.FeatureSpec(0, "n", D.FeatureGroup.SPECTRAL, "u",
                      "NOT_A_CLAIM_CLASS", "t")


# --- (6) the report ------------------------------------------------------

def test_report_verdict_and_claims_no_measurement():
    rep = D.diskdrive_report()
    assert rep["verdict"] == "FEATURE_DISK_FINALIZED_192_DIMENSIONS"
    assert rep["dimensions"] == 192
    assert rep["feature_count"] == 192
    assert rep["groups_partition_the_disk"] is True
    assert rep["indices_contiguous_and_unique"] is True
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] in D.CLAIM_CLASSES
    assert "what_this_does_not_say" in rep


def test_diskdrive_module_imports_from_r13():
    from r13 import diskdrive          # noqa: F401
    assert diskdrive.DEFAULT_VERDICT == "FEATURE_DISK_FINALIZED_192_DIMENSIONS"
