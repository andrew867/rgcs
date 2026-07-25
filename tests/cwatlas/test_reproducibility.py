"""P63 -- reproducibility, fuzzing, clean-clone import, and security.

POWER: the fuzz harness survives N arbitrary raw inputs -- every one yields a
typed outcome (decode, alias set, or refusal), never a crash and never a forced
pin; the same seed produces identical inputs and outcomes across two runs
(determinism); and every ``cwatlas`` module imports cleanly from a fresh process
state (clean-clone / import check). Security: no public module or fixture leaks
a private path/identity token.
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import cwatlas
from cwatlas import fuzz, service
from cwatlas.fuzz import FuzzOutcome


# --- Determinism (same seed => identical outputs across two runs) -------------

def test_generate_raw_is_deterministic():
    a = fuzz.generate_raw(20260725, 300)
    b = fuzz.generate_raw(20260725, 300)
    assert a == b
    assert len(a) == 300


def test_different_seeds_differ():
    assert fuzz.generate_raw(1, 200) != fuzz.generate_raw(2, 200)


def test_campaign_is_deterministic():
    a = fuzz.run_campaign(4242, 400)
    b = fuzz.run_campaign(4242, 400)
    assert a == b
    assert a["all_typed"] is True


def test_service_round_trip_is_deterministic():
    kw = dict(body_id="EARTH", frame_id="CRS84", epoch="2020.0",
              latitude_deg=48.8566, longitude_deg=2.3522, uncertainty_m=1.0)
    assert service.round_trip(**kw) == service.round_trip(**kw)


# --- Fuzz: never crashes, always typed, never a forced pin --------------------

def test_fuzz_never_crashes_and_is_always_typed():
    inputs = fuzz.generate_raw(777, 1000)
    for raw in inputs:
        res = fuzz.run_one(raw)
        assert isinstance(res.outcome, FuzzOutcome)
        # Every outcome carries a claim class; none is a decoded destination.
        assert res.claim_class in {
            "CANONICAL_ROUND_TRIP", "LEGACY_ALIAS_CANDIDATE", "REFUSAL"}


def test_fuzz_campaign_tally_sums_to_n():
    summary = fuzz.run_campaign(9090, 800)
    assert summary["count"] == 800
    assert sum(summary["outcomes"].values()) == 800
    assert summary["all_typed"] is True


def test_fuzz_handles_pathological_inputs():
    for raw in ["", " ", "\x00", "999999999", "-".join("1" * 5),
                "v=1.0.0;codec=CW-GEO-1;lat=0*cwck1:bad", "\U0001F600" * 10]:
        res = fuzz.run_one(raw)
        assert isinstance(res.outcome, FuzzOutcome)


def test_fuzz_rejects_bad_generator_args():
    with pytest.raises(fuzz.FuzzError):
        fuzz.generate_raw("not-int", 10)
    with pytest.raises(fuzz.FuzzError):
        fuzz.generate_raw(1, -5)


# --- Clean-clone / import: every cwatlas module imports cleanly ---------------

def _all_cwatlas_modules():
    names = []
    for info in pkgutil.iter_modules(cwatlas.__path__):
        if not info.ispkg:
            names.append(f"cwatlas.{info.name}")
    return sorted(names)


def test_all_modules_import_cleanly():
    modules = _all_cwatlas_modules()
    assert "cwatlas.service" in modules
    assert "cwatlas.cli" in modules
    assert "cwatlas.interchange" in modules
    assert "cwatlas.fuzz" in modules
    for name in modules:
        importlib.import_module(name)  # must not raise


def test_new_phase_modules_expose_reports():
    for name, fn in (
        ("service", "service_report"),
        ("cli", "cli_report"),
        ("interchange", "interchange_report"),
        ("fuzz", "fuzz_report"),
    ):
        mod = importlib.import_module(f"cwatlas.{name}")
        report = getattr(mod, fn)()
        assert report["source_vector_geographic_semantics"] == "NOT_CLAIMED"
        assert report["measured_here"] == "nothing"


# --- Security: no private token in any public module source ------------------

def test_no_private_tokens_in_public_modules():
    import pathlib

    from cwatlas import privacy
    base = pathlib.Path(cwatlas.__file__).parent
    for path in base.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        hits = privacy.scan_for_private(text)
        assert not hits, f"{path.name} contains private tokens {hits}"
