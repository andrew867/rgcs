"""Gate G42: the master coverage ledger is release-blocking.

Any ledger ID without an owner and a disposition is a P1 defect."""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "v4x_coverage_ledger", ROOT / "tools" / "v4x_coverage_ledger.py")
cov = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cov)


@pytest.fixture(scope="module")
def report():
    return cov.build()


def test_every_ledger_id_has_owner_and_disposition(report):
    assert not report["uncovered"], \
        f"P1: uncovered ledger IDs {report['uncovered']}"
    assert report["gate_G42_pass"]
    for row in report["rows"]:
        assert row["owner"] and row["artifact"]
        assert row["status"] != "UNCOVERED_P1"


def test_all_lanes_present(report):
    ids = {r["id"] for r in report["rows"]}
    for prefix, n in (("A", 18), ("F", 52), ("G", 30), ("E", 27),
                      ("S", 24), ("W", 17), ("H", 17), ("C", 52),
                      ("I", 11)):
        got = {i for i in ids if i[0] == prefix}
        assert len(got) == n, f"{prefix}: {len(got)} != {n}"
    assert report["total_ids"] == 248


def test_statuses_are_declared_classes(report):
    from rscs2_core.research_records import STATUS_CLASSES
    extra = {"CANDIDATE_NEW_COUPLING"}
    for row in report["rows"]:
        assert row["status"] in set(STATUS_CLASSES) | extra, row
