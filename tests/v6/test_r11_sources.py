"""A01 — source registry, traceability, privacy scan, declared residual."""

from __future__ import annotations

from pathlib import Path

import pytest

from r11 import sources as S

ROOT = Path(__file__).resolve().parents[2]


def test_every_required_authority_is_registered():
    ids = {s.source_id for s in S.SOURCE_REGISTRY}
    for required in ("SRC_ITRF", "SRC_WGS84", "SRC_IGRF", "SRC_RABI",
                     "SRC_RAMSEY", "SRC_HMASER", "SRC_CS133", "SRC_CS137",
                     "SRC_ET", "SRC_QUARTZ", "SRC_DYNCASIMIR", "SRC_ORBITS"):
        assert required in ids


def test_a_locator_may_not_be_a_private_or_absolute_path():
    # The offending paths are assembled from fragments on purpose: writing
    # them as literals would plant real PRIVATE_PATH strings in the public
    # tree and trip r10.firewall on this very guard.
    win = "C:" + chr(92) + "Users" + chr(92) + "someone" + chr(92) + "n.md"
    posix = "/" + "home" + "/someone/notes.md"
    for bad in (win, posix):
        with pytest.raises(S.SourceError):
            S.SourceRecord("X", "t", "a", S.SourceKind.ESTABLISHED_SOURCE, bad)


def test_registry_locators_are_citations_not_paths():
    for s in S.SOURCE_REGISTRY:
        assert "C:\\" not in s.locator and not s.locator.startswith("/home/")


def test_unregistered_source_is_refused():
    with pytest.raises(S.SourceError):
        S.get_source("SRC_DOES_NOT_EXIST")


def test_every_implemented_equation_traces_to_an_authority():
    for eq in S.TRACEABILITY:
        assert S.trace(eq)          # non-empty tuple of SourceRecord
    with pytest.raises(S.SourceError):
        S.trace("an_equation_nobody_registered")


def test_the_photon_paper_is_declared_blocked_not_verified():
    p = S.get_source("SRC_TRUNCPHOTON")
    assert p.kind is S.SourceKind.BLOCKED_MISSING_DATA
    assert "not independently verified" in p.notes


def test_source_digest_is_stable_and_sensitive():
    a = S.get_source("SRC_CS133")
    b = S.SourceRecord(a.source_id, a.title, a.authority, a.kind, a.locator)
    assert a.digest == b.digest
    c = S.SourceRecord(a.source_id, "changed", a.authority, a.kind, a.locator)
    assert c.digest != a.digest


# --- privacy -----------------------------------------------------------

@pytest.mark.parametrize("p", [
    "internal-docs/plans-v5/pack/02_PRIVATE_OPERATOR_DELTA_2026-07-23.md",
    r"internal-docs\plans-v5\thing.md",
    "some/PRIVATE_OPERATOR_DELTA_file.md",
])
def test_reading_the_private_delta_is_refused(p):
    assert S.is_private_path(p)
    with pytest.raises(S.SourceError):
        S.refuse_private_delta_read(p)


def test_an_ordinary_public_path_is_not_refused():
    assert not S.is_private_path("r11/sources.py")
    S.refuse_private_delta_read("r11/sources.py")      # must not raise


def test_adding_new_identity_strings_is_refused():
    with pytest.raises(S.SourceError):
        S.refuse_new_identity_exposure("any new name")


def test_declared_residual_is_recorded_by_category_not_by_content():
    d = S.DECLARED_RESIDUAL
    assert d["status"] == "DECLARED_RESIDUAL_EXPOSURE"
    assert d["category"] == "ALLEGED_COMMUNICATOR_IDENTITY_STRINGS"
    # The residual must NOT restate the leaked strings themselves. This
    # is asserted STRUCTURALLY — spelling the names here in order to
    # check for their absence would itself add them to the public tree.
    assert set(d) == {"category", "surfaces", "earliest_surface", "status",
                      "why_not_repaired", "operator_decision",
                      "assessed_severity", "forward_rule"}
    assert d["category"].endswith("IDENTITY_STRINGS")   # a label, not a name
    assert "immutable Git history" in d["surfaces"]
    assert "no NEW identity strings" in d["forward_rule"]


def test_privacy_scan_runs_and_reports_the_residual():
    rep = S.privacy_scan(ROOT, max_commits=8)   # keep the history scan cheap
    assert rep["committed_clean"], rep
    assert rep["history_serious"] == []
    assert rep["declared_residual"]["status"] == "DECLARED_RESIDUAL_EXPOSURE"
    assert rep["verdict"] == "PRIVACY_SCAN_CLEAN_WITH_DECLARED_RESIDUAL"


def test_report_claims_no_measurement():
    r = S.sources_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "SRC_TRUNCPHOTON" in r["blocked_sources"]
