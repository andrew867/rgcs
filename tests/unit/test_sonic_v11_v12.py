"""Frequency Key Studio v1.1/v1.2 service tests: WAV import layers,
loudness normalization, multi-carrier, spectrogram, batch render,
corpus store, clustering, recommendation."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from rgcs_desktop.services.sonic_audio import (
    AudioError, load_wav, multi_carrier_layers, normalize_rms, peak,
    render_binaural, resample_linear, rms, sine, spectrogram, write_wav)
from rgcs_desktop.services.sonic_corpus import (CorpusStore,
                                                cluster_corpus,
                                                recommend_recipes)
from rgcs_desktop.services.sonic_exports import batch_render
from rgcs_desktop.services.sonic_ingest import parse_video_metadata
from rgcs_desktop.services.sonic_timeline import (TimelineError,
                                                  render_session,
                                                  standard_session_shape)

ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------- v1.1: audio

def test_wav_import_roundtrip(tmp_path):
    audio = render_binaural(200.0, 4.0, 0.5)
    path = write_wav(tmp_path / "cue.wav", audio)
    loaded, rate = load_wav(path)
    assert rate == 48000
    assert loaded.shape == audio.shape
    assert np.max(np.abs(loaded - audio)) < 1e-3   # 16-bit quantization


def test_resample_changes_length_preserves_tone():
    tone = sine(440.0, 1.0, 48000)
    down = resample_linear(tone, 48000, 16000)
    assert down.shape[0] == 16000
    spec = spectrogram(down, 16000, frame=1024, hop=256)
    peak_bin = spec["db"].mean(axis=0).argmax()
    assert spec["freqs_hz"][peak_bin] == pytest.approx(440.0, abs=20.0)


def test_normalize_rms_hits_target():
    quiet = 0.05 * render_binaural(200.0, 4.0, 0.5)
    out, stats = normalize_rms(quiet, -20.0)
    assert rms(out) == pytest.approx(0.1, rel=0.02)     # -20 dBFS
    assert not stats["peak_limited"]
    loud = 0.9 * render_binaural(200.0, 4.0, 0.5)
    out2, stats2 = normalize_rms(loud, -1.0)
    assert peak(out2) <= 0.95 + 1e-6                    # capped
    assert stats2["peak_limited"]
    with pytest.raises(AudioError):
        normalize_rms(quiet, 3.0)


def test_multi_carrier_layers():
    layers = multi_carrier_layers([200.0, 925.0], 7.83)
    assert len(layers) == 2
    assert all(la["type"] == "binaural" for la in layers)
    assert layers[1]["carrier_hz"] == 925.0
    with pytest.raises(AudioError):
        multi_carrier_layers([], 4.0)


def test_spectrogram_finds_the_carrier():
    tone = sine(925.0, 1.0, 48000)
    spec = spectrogram(tone, 48000)
    peak_bin = spec["db"].mean(axis=0).argmax()
    assert spec["freqs_hz"][peak_bin] == pytest.approx(925.0, abs=25.0)
    with pytest.raises(AudioError):
        spectrogram(sine(440.0, 0.01, 48000), 48000)    # too short


# ---------------------------------------------- v1.1: timeline layers

def _base_session(duration=12.0, layers=None):
    return {
        "schema_version": "1.0.0", "session_id": "S-V11", "title": "t",
        "duration_s": duration, "sample_rate": 8000,
        "segments": standard_session_shape(4.0, duration),
        "layers": layers or [{"layer_id": "L1", "type": "binaural",
                              "carrier_hz": 200.0, "gain_db": -6.0}],
    }


def test_voice_cue_layer_renders_from_file(tmp_path):
    cue = 0.5 * sine(600.0, 1.0, 8000)
    cue_path = write_wav(tmp_path / "cue.wav", cue, 8000)
    session = _base_session(layers=[
        {"layer_id": "L1", "type": "binaural", "carrier_hz": 200.0,
         "gain_db": -6.0},
        {"layer_id": "V1", "type": "voice_cue", "file": str(cue_path),
         "gain_db": -3.0, "start_s": 5.0},
    ])
    audio, stats = render_session(session)
    assert stats["skipped_layers"] == []
    sr = 8000
    # cue occupies [5.0 s, 6.0 s): that window is louder than before it
    before = rms(audio[int(3.5 * sr):int(4.5 * sr)])
    during = rms(audio[int(5.1 * sr):int(5.9 * sr)])
    assert during > before * 1.2


def test_file_layer_without_file_is_stated(tmp_path):
    session = _base_session(layers=[
        {"layer_id": "L1", "type": "binaural", "carrier_hz": 200.0,
         "gain_db": -6.0},
        {"layer_id": "V1", "type": "voice_cue", "gain_db": -3.0},
    ])
    _, stats = render_session(session)
    assert stats["skipped_layers"] == ["V1 (voice_cue: no file attached)"]


def test_music_bed_bad_start_refused(tmp_path):
    cue_path = write_wav(tmp_path / "bed.wav",
                         0.2 * sine(300.0, 0.5, 8000), 8000)
    session = _base_session(layers=[
        {"layer_id": "M1", "type": "music_bed", "file": str(cue_path),
         "gain_db": -6.0, "start_s": -2.0}])
    with pytest.raises(TimelineError):
        render_session(session)


def test_session_loudness_normalization():
    session = _base_session()
    session["loudness"] = {"target_rms_db": -20.0}
    audio, stats = render_session(session)
    assert stats["loudness_target_rms_db"] == -20.0
    assert rms(audio) == pytest.approx(0.1, rel=0.05)


def test_multi_carrier_session_renders():
    session = _base_session(layers=multi_carrier_layers(
        [200.0, 925.0], 4.0))
    audio, stats = render_session(session)
    assert stats["n_layers"] == 2
    assert stats["peak"] <= 0.95 + 1e-6


# ------------------------------------------------- v1.1: batch render

def test_batch_render_and_manifest(tmp_path):
    manifest = batch_render(["RGCS-BIN-0001", "RGCS-NOPE-0000"],
                            tmp_path, duration_s=10.0)
    by_id = {r["recipe_id"]: r for r in manifest["results"]}
    assert by_id["RGCS-BIN-0001"]["status"] == "rendered"
    assert (tmp_path / by_id["RGCS-BIN-0001"]["wav"]).is_file()
    assert by_id["RGCS-NOPE-0000"]["status"] == "failed"
    saved = json.loads((tmp_path / "batch_manifest.json")
                       .read_text(encoding="utf-8"))
    assert saved["results"] == manifest["results"]


def test_batch_cli(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "rgcs_desktop.services.sonic_cli",
         "batch", "RGCS-BIN-0001", "--duration", "10",
         "--out", str(tmp_path)],
        capture_output=True, text=True, timeout=300, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    assert "1/1 rendered" in proc.stdout


# ------------------------------------------------------ v1.2: corpus

def _record(url, title):
    return parse_video_metadata({"url": url, "title": title})


def test_corpus_store_roundtrip(tmp_path):
    store = CorpusStore(tmp_path / "corpus.json")
    assert store.add(_record("https://example.invalid/1",
                             "925 Hz binaural focus"))
    assert not store.add(_record("https://example.invalid/1",
                                 "duplicate url"))
    assert store.add(_record("https://example.invalid/2",
                             "528Hz 6.3 Hz astral"))
    store.save()
    reloaded = CorpusStore(tmp_path / "corpus.json")
    assert len(reloaded.records) == 2
    csv_path = reloaded.to_csv(tmp_path / "corpus.csv")
    text = csv_path.read_text(encoding="utf-8")
    assert "925" in text and "astral" in text


def test_cluster_corpus_groups_duplicates():
    records = [
        _record("https://example.invalid/a",
                "528Hz + 6.3 Hz Astral Projection Binaural Beat"),
        _record("https://example.invalid/b",
                "528 Hz 6.3Hz astral projection binaural beat HD"),
        _record("https://example.invalid/c",
                "925 Hz binaural focus"),
    ]
    clusters = cluster_corpus(records)
    assert len(clusters) == 2
    assert clusters[0]["size"] == 2
    assert clusters[0]["representative"]["url"].endswith("/a")


def test_recommend_recipes_by_frequency_and_use():
    record = _record("https://example.invalid/r",
                     "528Hz + 6.3 Hz Astral Projection Binaural Beat")
    ranked = recommend_recipes(record)
    assert ranked, "expected at least one recommendation"
    top = ranked[0]
    assert top["recipe"]["recipe_id"] == "RGCS-AST-0001"
    assert top["score"] >= 4                 # carrier + beat match
    assert any("carrier" in r for r in top["reasons"])

    schumann = _record("https://example.invalid/s",
                       "7.83 Hz Schumann binaural")
    ranked2 = recommend_recipes(schumann)
    ids = [r["recipe"]["recipe_id"] for r in ranked2]
    assert ids and set(ids) <= {"RGCS-SCH-0001", "RGCS-FKY-0925"}


def test_render_file_cli_imports_session(tmp_path):
    """rgcs-sonic render-file renders an imported frequency_session
    JSON (the shipped sample) and refuses invalid files with reasons."""
    sample = ROOT / "examples" / "sonic" / "binaural_session_sample.json"
    proc = subprocess.run(
        [sys.executable, "-m", "rgcs_desktop.services.sonic_cli",
         "render-file", str(sample), "--duration", "12",
         "--out", str(tmp_path)],
        capture_output=True, text=True, timeout=300, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "SES-SAMPLE-IMPORT.wav").is_file()
    assert (tmp_path / "SES-SAMPLE-IMPORT_bundle.zip").is_file()

    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": "1.0.0"}', encoding="utf-8")
    proc2 = subprocess.run(
        [sys.executable, "-m", "rgcs_desktop.services.sonic_cli",
         "render-file", str(bad), "--out", str(tmp_path)],
        capture_output=True, text=True, timeout=120, cwd=ROOT)
    assert proc2.returncode == 1
    assert "invalid" in proc2.stderr


# ------------------------------------------------------- wobbles

def test_wobble_dataset_loads():
    from rgcs_desktop.services.sonic_recipes import (load_wobbles,
                                                     wobble_by_name)
    wobbles = load_wobbles()
    assert len(wobbles) == 38
    oct8 = wobble_by_name("Octave 8 Stage Wobble")
    assert oct8["multipliers"] == [1, 2, 4, 8, 16, 8, 4, 2]
    fib = wobble_by_name("Fibonacci 8 Stage Wobble")
    assert fib["multipliers"] == [1, 2, 3, 5, 8, 5, 3, 2]
    feather = wobble_by_name("+-.02% Feathering")
    assert feather["stages"] == 50
    assert all(0.9997 < m < 1.0003 for m in feather["multipliers"])
    golden = wobble_by_name("Golden Ratio 6 Step Ramp Down")
    assert golden["multipliers"][1] == pytest.approx(0.618033989)
    families = {w["family"] for w in wobbles}
    assert {"feathering", "staged_percent", "octave", "odd",
            "fibonacci", "ramp_down", "phi"} <= families


def test_wobbled_layer_tracks_stage_table():
    """An Octave 2-stage wobble (x1, x2) on the carrier doubles the
    zero-crossing rate in alternate dwell windows."""
    session = _base_session(duration=12.0, layers=[
        {"layer_id": "L1", "type": "binaural", "carrier_hz": 200.0,
         "gain_db": -6.0,
         "wobble": {"name": "Octave 2 Stage Wobble", "dwell_s": 3.0,
                    "target": "carrier"}}])
    audio, _ = render_session(session)
    sr = 8000

    def crossings(seg):
        return int(np.sum(np.abs(np.diff(np.signbit(seg)))))
    # stage 0 (x1): ~200 Hz; stage 1 (x2): ~400 Hz
    f0 = crossings(audio[int(0.5 * sr):int(2.5 * sr), 0]) / 2 / 2.0
    f1 = crossings(audio[int(3.5 * sr):int(5.5 * sr), 0]) / 2 / 2.0
    assert f0 == pytest.approx(200.0, abs=8.0)
    assert f1 == pytest.approx(400.0, abs=12.0)


def test_wobble_nyquist_guard():
    session = _base_session(duration=12.0, layers=[
        {"layer_id": "L1", "type": "binaural", "carrier_hz": 925.0,
         "gain_db": -6.0,
         "wobble": {"name": "Octave 12 Stage Wobble",
                    "dwell_s": 1.0}}])  # 925*64 way past nyquist
    with pytest.raises(TimelineError):
        render_session(session)


def test_wobble_unknown_and_bad_target_refused():
    from rgcs_desktop.services.sonic_recipes import RecipeError
    session = _base_session(duration=12.0, layers=[
        {"layer_id": "L1", "type": "binaural", "carrier_hz": 200.0,
         "gain_db": -6.0, "wobble": {"name": "Nonexistent Wobble"}}])
    with pytest.raises(RecipeError):
        render_session(session)
    session2 = _base_session(duration=12.0, layers=[
        {"layer_id": "L1", "type": "binaural", "carrier_hz": 200.0,
         "gain_db": -6.0,
         "wobble": {"name": "Octave 2 Stage Wobble",
                    "target": "sideways"}}])
    with pytest.raises(TimelineError):
        render_session(session2)


def test_wobble_schema_valid():
    from rgcs_desktop.services.schemas import validate_instance
    layer = {"layer_id": "L1", "type": "binaural", "carrier_hz": 200.0,
             "gain_db": -6.0,
             "wobble": {"name": "Octave 4 Stage Wobble",
                        "dwell_s": 2.0, "target": "carrier"}}
    assert validate_instance(layer, "audio_layer.schema.json") == []
    bad = dict(layer, wobble={"dwell_s": 2.0})       # name missing
    assert validate_instance(bad, "audio_layer.schema.json")
