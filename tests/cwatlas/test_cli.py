"""P57 -- the ``cw-atlas`` CLI.

POWER: every subcommand (encode/decode/legacy/roundtrip/export/verify) prints a
single JSON object carrying CRS + epoch + claim class and is reachable through
``main(argv)``. Negative: malformed args exit 2 (argparse); a rejected request
(bad codec) prints a typed error and exits 1; a malformed vector decodes to a
typed refusal at exit 0. Deterministic output.
"""

from __future__ import annotations

import json

import pytest

from cwatlas import cli


def _run(capsys, argv):
    code = cli.main(argv)
    out = capsys.readouterr().out
    return code, json.loads(out)


# --- POWER --------------------------------------------------------------------

def test_encode_prints_json_receipt(capsys):
    code, obj = _run(capsys, [
        "encode", "--lat", "45", "--lon", "-75", "--uncertainty", "1.0"])
    assert code == 0
    assert obj["codec_id"] == "CW-GEO-1"
    assert obj["crs"] == "CRS84"
    assert obj["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert obj["vector"]


def test_decode_round_trips_through_cli(capsys):
    _, enc = _run(capsys, [
        "encode", "--lat", "12.5", "--lon", "30.25", "--uncertainty", "1.0"])
    code, dec = _run(capsys, ["decode", enc["vector"]])
    assert code == 0
    assert dec["status"] == "OK_POINT"
    assert dec["point"]["latitude_deg"] == pytest.approx(12.5, abs=1e-6)


def test_legacy_subcommand(capsys):
    code, obj = _run(capsys, ["legacy", "123456789"])
    assert code == 0
    assert obj["status"] == "OK_ALIAS_SET"
    assert obj["claim_class"] == "LEGACY_ALIAS_CANDIDATE"


def test_roundtrip_subcommand(capsys):
    code, obj = _run(capsys, [
        "roundtrip", "--lat", "-10", "--lon", "100", "--uncertainty", "1.0"])
    assert code == 0
    assert obj["closed"] is True


def test_roundtrip_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["roundtrip", "--help"])
    assert exc.value.code == 0


def test_export_subcommand_builds_bundle(capsys):
    from cwatlas import audit_bundle
    code, obj = _run(capsys, [
        "export", "--point", "1,2", "--point", "3,4,5", "--uncertainty", "1.0"])
    assert code == 0
    assert obj["receipt_count"] == 2
    assert audit_bundle.verify_bundle(obj) is True


def test_verify_vector_subcommand(capsys):
    _, enc = _run(capsys, [
        "encode", "--lat", "0", "--lon", "0", "--uncertainty", "1.0"])
    code, obj = _run(capsys, ["verify", "--vector", enc["vector"]])
    assert code == 0
    assert obj["valid"] is True


def test_verify_bundle_file(capsys, tmp_path):
    from cwatlas import service
    bundle = service.export_bundle([
        {"body_id": "EARTH", "frame_id": "CRS84", "epoch": "2020.0",
         "latitude_deg": 1.0, "longitude_deg": 2.0, "uncertainty_m": 1.0}])
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    code, obj = _run(capsys, ["verify", "--bundle", str(path)])
    assert code == 0
    assert obj["valid"] is True


def test_ico_codec_via_cli(capsys):
    code, obj = _run(capsys, [
        "encode", "--lat", "5", "--lon", "6", "--uncertainty", "1.0",
        "--codec", "CW-HCM-ICO"])
    assert code == 0
    assert obj["codec_id"] == "CW-HCM-ICO"


# --- Negative -----------------------------------------------------------------

def test_missing_required_arg_exits_2():
    with pytest.raises(SystemExit) as exc:
        cli.main(["encode", "--lat", "45"])  # missing --lon and --uncertainty
    assert exc.value.code == 2


def test_unknown_subcommand_exits_2():
    with pytest.raises(SystemExit) as exc:
        cli.main(["frobnicate"])
    assert exc.value.code == 2


def test_bad_codec_choice_exits_2():
    with pytest.raises(SystemExit) as exc:
        cli.main(["encode", "--lat", "1", "--lon", "1", "--uncertainty", "1",
                  "--codec", "NOPE"])
    assert exc.value.code == 2


def test_malformed_point_exits_2():
    with pytest.raises(SystemExit) as exc:
        cli.main(["export", "--point", "not-a-point", "--uncertainty", "1"])
    assert exc.value.code == 2


def test_decode_garbage_is_typed_refusal(capsys):
    code, obj = _run(capsys, ["decode", "total-garbage"])
    assert code == 0
    assert obj["status"] == "REFUSED"
    assert obj["claim_class"] == "REFUSAL"


def test_verify_missing_group_exits_2():
    with pytest.raises(SystemExit) as exc:
        cli.main(["verify"])  # neither --vector nor --bundle
    assert exc.value.code == 2


# --- Determinism --------------------------------------------------------------

def test_cli_output_deterministic(capsys):
    _, a = _run(capsys, ["encode", "--lat", "1", "--lon", "2", "--uncertainty", "1"])
    _, b = _run(capsys, ["encode", "--lat", "1", "--lon", "2", "--uncertainty", "1"])
    assert a == b


def test_cli_report_boundary():
    r = cli.cli_report()
    assert r["prog"] == "cw-atlas"
    assert "encode" in r["subcommands"]
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
