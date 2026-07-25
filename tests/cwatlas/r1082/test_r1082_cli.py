"""P29 — backend API / CLI integration tests.

Invokes ``cli.main()`` with argv lists for every subcommand and asserts: exit 0,
valid JSON on stdout, the governance seals present, and no MEASURED / validated
source-origin leakage. Bad input yields a non-zero exit; a governance refusal is
surfaced as a refusal, not a crash.
"""

from __future__ import annotations

import json

import pytest

from cwatlas.r1082 import cli
from cwatlas.r1082 import root_certificate


@pytest.fixture(autouse=True)
def _clear_cache():
    root_certificate.cache_clear()
    yield


def _run(capsys, argv):
    code = cli.main(argv)
    out = capsys.readouterr().out
    return code, out


def _run_json(capsys, argv):
    code, out = _run(capsys, argv)
    assert code == 0, f"non-zero exit for {argv}: {out}"
    payload = json.loads(out)  # valid JSON or this raises
    return payload


def _assert_no_measured_leak(payload):
    blob = json.dumps(payload)
    assert '"MEASURED"' not in blob
    assert '"REPLICATED"' not in blob
    assert "SOURCE_ORIGIN_VALIDATED" not in blob
    assert payload["measured_here"] == "nothing"
    assert payload["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert payload["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0


def test_no_subcommand_errors():
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code != 0


def test_root_in_validity(capsys):
    d = _run_json(capsys, ["root", "--epoch", "2020", "--shell", "3"])
    assert d["in_validity"] is True
    assert d["certificate"]["profile_id"] == "EARTH_ROOT_D_V1"
    assert d["certificate_hash"].startswith("sha256:")
    assert d["shell_supplies_radius"] is True
    _assert_no_measured_leak(d)


def test_root_out_of_validity_typed_refusal(capsys):
    d = _run_json(capsys, ["root", "--epoch", "3000", "--shell", "3"])
    assert d["in_validity"] is False
    assert "reason" in d
    _assert_no_measured_leak(d)


def test_root_bad_shell_nonzero_exit(capsys):
    code, _ = _run(capsys, ["root", "--shell", "42"])
    assert code == 2


def test_decode_uncalibrated_region_or_alias(capsys):
    d = _run_json(capsys, ["decode", "--vector", "165876523", "--shell", "3"])
    assert d["result_type"] in {"CANDIDATE_REGION", "CANDIDATE_ALIAS_SET",
                                "UNDERDETERMINED"}
    assert d["evidence_class"] != "MEASURED"
    _assert_no_measured_leak(d)


def test_decode_single_family_is_calibrated_point(capsys):
    d = _run_json(capsys, ["decode", "--vector", "165876523", "--shell", "3",
                           "--profile", "single"])
    assert d["result_type"] == "CANDIDATE_CALIBRATED_POINT"
    assert d["evidence_class"] == "CALIBRATED_CANDIDATE"
    _assert_no_measured_leak(d)


def test_decode_all_families_alias_set(capsys):
    d = _run_json(capsys, ["decode", "--vector", "165876523", "--shell", "3",
                           "--profile", "all"])
    assert d["result_type"] in {"CANDIDATE_ALIAS_SET", "CANDIDATE_CALIBRATED_POINT"}
    _assert_no_measured_leak(d)


def test_decode_invalid_vector_typed_invalid(capsys):
    d = _run_json(capsys, ["decode", "--vector", "not-a-vector", "--shell", "3"])
    assert d["result_type"] == "INVALID"
    _assert_no_measured_leak(d)


def test_decode_foreign_body_out_of_scope(capsys):
    d = _run_json(capsys, ["decode", "--vector", "165876523", "--body", "MARS"])
    assert d["result_type"] == "INVALID"
    assert d["input"]["in_scope"] is False
    _assert_no_measured_leak(d)


def test_encode_map_to_vector(capsys):
    d = _run_json(capsys, ["encode", "--lat", "51.1789", "--lon", "-1.8262",
                           "--shell", "3", "--profile", "single"])
    assert d["result_type"] == "CANDIDATE_CALIBRATED_POINT"
    assert "source_vector" in d["geometry"]
    assert d["shell_supplies_radius"] is True
    _assert_no_measured_leak(d)


def test_encode_requires_named_profile(capsys):
    # 'none' is not offered for encode; an explicit bad choice errors out.
    with pytest.raises(SystemExit):
        cli.main(["encode", "--lat", "0", "--lon", "0", "--profile", "none"])


def test_inspect_valid(capsys):
    d = _run_json(capsys, ["inspect", "--vector", "165876523"])
    assert d["valid"] is True
    assert d["wire"] == "01|65|87|65|23"
    assert d["tokens"] == [1, 65, 87, 65, 23]
    _assert_no_measured_leak(d)


def test_inspect_invalid(capsys):
    d = _run_json(capsys, ["inspect", "--vector", "@@@"])
    assert d["valid"] is False
    assert d["result_type"] == "INVALID"
    _assert_no_measured_leak(d)


def test_batch_multiple_vectors(capsys):
    d = _run_json(capsys, ["batch", "--vectors", "165876523", "7777777777",
                           "--shell", "3"])
    assert d["count"] == 2
    assert len(d["results"]) == 2
    for r in d["results"]:
        assert r["result_type"] in {
            "CANDIDATE_REGION", "CANDIDATE_ALIAS_SET", "UNDERDETERMINED",
            "CANDIDATE_CALIBRATED_POINT", "INVALID"}
    _assert_no_measured_leak(d)


def test_batch_from_file(capsys, tmp_path):
    f = tmp_path / "vectors.txt"
    f.write_text("165876523\n0102030405\n", encoding="utf-8")
    d = _run_json(capsys, ["batch", "--input", str(f), "--shell", "3"])
    assert d["count"] == 2
    _assert_no_measured_leak(d)


def test_batch_empty_errors(capsys):
    code, _ = _run(capsys, ["batch", "--shell", "3"])
    assert code == 2


def test_calibration_freeze_receipt(capsys):
    d = _run_json(capsys, ["calibration"])
    assert d["profile_id"] == "EARTH_ROOT_D_V1"
    assert d["retuning_forbidden"] is True
    assert len(d["frozen_parameters"]) == 7
    _assert_no_measured_leak(d)


def test_receipt_manifest(capsys):
    # The receipt aggregates the claim taxonomy, which legitimately *names* the
    # MEASURED/REPLICATED evidence classes as part of the enumeration. The
    # firewall invariant is that no result carries evidence_class MEASURED --
    # not that the string never appears -- so this test checks the seals and
    # that the output guard passed (main() would have refused otherwise).
    d = _run_json(capsys, ["receipt"])
    assert "claim_taxonomy" in d
    assert "module_seals" in d
    assert d["claim_taxonomy"]["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert d["measured_here"] == "nothing"
    assert d["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert "SOURCE_ORIGIN_VALIDATED" not in json.dumps(d)


def test_receipt_single_module(capsys):
    d = _run_json(capsys, ["receipt", "--module", "cli"])
    assert d["report"]["phase_id"] == "P29"
    assert d["report"]["measured_here"] == "nothing"
    _assert_no_measured_leak(d)


def test_receipt_bad_module_nonzero(capsys):
    code, _ = _run(capsys, ["receipt", "--module", "does_not_exist"])
    assert code == 2


def test_deterministic_output(capsys):
    d1 = _run_json(capsys, ["root", "--epoch", "2020", "--shell", "3"])
    root_certificate.cache_clear()
    d2 = _run_json(capsys, ["root", "--epoch", "2020", "--shell", "3"])
    assert d1 == d2


def test_report_seals_claims():
    r = cli.cli_report()
    assert r["phase_id"] == "P29"
    assert r["tranche"] == "T08"
    assert r["candidate_never_emitted_as_measured"] is True
    assert r["t07_imported_lazily"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert set(r["subcommands"]) == {"root", "calibration", "encode", "decode",
                                     "inspect", "batch", "receipt"}


def test_guard_refuses_measured_leak():
    # The output firewall refuses to emit an evidence_class of MEASURED.
    from cwatlas.r1082 import claims
    with pytest.raises(claims.R1082ClaimError):
        cli._guard_no_measured_leak({"evidence_class": "MEASURED"})
