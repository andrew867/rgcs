"""RCW locks — CLI behaviour and exit-code contract (in-process)."""

import json

import pytest

from rgcs_coordinate import cli


def run(argv, capsys):
    code = cli.main(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


def test_decode_human_and_json(capsys):
    code, out, _ = run(["decode", "165876523"], capsys)
    assert code == 0
    assert "1170611453" in out and "TRAINING EQUALITY" in out
    assert "not" in out and "coordinates" in out
    code, out, _ = run(["decode", "165876523", "--json"], capsys)
    assert code == 0
    d = json.loads(out)
    assert d["schema"] == "rgcs.structural-trace.v1"
    assert d["fixture_label"].startswith("Stonehenge")
    assert "training equality" in d["fixture_label"]


def test_decode_orange_correction_label(capsys):
    code, out, _ = run(["decode", "165892763", "--json"], capsys)
    assert code == 0
    d = json.loads(out)
    assert d["extracted_shell"] == 3          # raw arithmetic, verbatim
    assert "active shell 7" in d["fixture_label"]
    assert "provenance" in d["fixture_label"]


def test_encode_and_roundtrip(capsys):
    code, out, _ = run(["encode", "--face", "4",
                        "--path", "33012021211", "--shell", "3"], capsys)
    assert code == 0 and "165876523" in out
    code, out, _ = run(["roundtrip", "165876523"], capsys)
    assert code == 0 and "EXACT" in out


def test_exit_codes(capsys):
    code, _, err = run(["decode", "not-a-number"], capsys)
    assert code == 2 and "error" in err
    code, _, err = run(["decode", "1678523973"], capsys)
    assert code == 2 and "family" in err
    code, _, err = run(["inspect-codec", "base-100"], capsys)
    assert code == 3 and "unsupported codec" in err
    code, out, _ = run(["project", "165876523"], capsys)
    assert code == 4                     # honest: underdetermined
    assert json.loads(out)["status"] == "UNDERDETERMINED"


def test_corpus_validate_and_doctor_and_version(capsys):
    code, out, _ = run(["corpus", "validate"], capsys)
    assert code == 0 and json.loads(out)["valid"]
    code, out, _ = run(["doctor"], capsys)
    assert code == 0
    d = json.loads(out)
    assert d["structural_codec"] == "OK" and d["fixtures"] == "OK"
    code, out, _ = run(["version", "--full"], capsys)
    assert code == 0
    v = json.loads(out)
    assert v["package"] == "rgcs-coordinate"
    assert v["claims"]["SOURCE_ORIGIN_VALIDATED"] == "no"


def test_corpus_validate_external_file(tmp_path, capsys):
    bad = {"schema": "rgcs.golden-vectors.v1",
           "vectors": [{"label": "wrong", "raw_decimal": "165876523",
                        "face": 9}]}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    code, out, _ = run(["corpus", "validate", str(p)], capsys)
    assert code == 2
    assert not json.loads(out)["valid"]


def test_no_serve_stub():
    """The local web workbench ships in a later slice; the CLI must not
    carry a mock 'serve' command meanwhile."""
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["serve"])
