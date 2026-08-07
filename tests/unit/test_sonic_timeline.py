"""Frequency Key Studio timeline engine tests."""
import json
from pathlib import Path

import numpy as np
import pytest

from rgcs_desktop.services.sonic_timeline import (
    RAMP_CURVES, TimelineError, beat_envelope, ramp, render_session,
    standard_session_shape, validate_session)

EXAMPLE = (Path(__file__).resolve().parents[2] / "experiments"
           / "templates" / "frequency_session.example.json")


def load_example() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_ramp_curves():
    for curve in RAMP_CURVES:
        values = ramp(10.0, 4.0, 100, curve)
        assert values[0] == pytest.approx(10.0, abs=1e-6)
        assert values[-1] == pytest.approx(4.0, abs=0.8 if curve == "stepped" else 1e-6)
    with pytest.raises(TimelineError):
        ramp(1, 2, 10, "wiggly")


def test_validate_session_checks_totals():
    session = load_example()
    validate_session(session)
    session["duration_s"] = 500.0
    with pytest.raises(TimelineError):
        validate_session(session)


def test_beat_envelope_follows_segments():
    session = load_example()
    env = beat_envelope(session, sample_rate=1000)
    assert len(env) == 60 * 1000
    assert env[0] == pytest.approx(10.0)
    assert env[-1] == pytest.approx(7.83)
    # hold segment is flat at the target
    assert env[30 * 1000] == pytest.approx(7.83, abs=1e-6)


def test_render_session_example():
    session = load_example()
    audio, stats = render_session(session, sample_rate=8000)
    assert audio.shape == (60 * 8000, 2)
    assert stats["peak"] <= 0.95 + 1e-6
    assert stats["normalized"] in (True, False)
    assert stats["beat_end_hz"] == pytest.approx(7.83)
    assert stats["skipped_layers"] == []


def test_render_skips_file_layers_with_statement():
    session = load_example()
    session["layers"].append({"layer_id": "L3", "type": "music_bed",
                              "gain_db": -12.0})
    _, stats = render_session(session, sample_rate=8000)
    assert len(stats["skipped_layers"]) == 1
    # v1.1: file layers render when a file is attached; without one the
    # skip is stated explicitly
    assert "no file attached" in stats["skipped_layers"][0]


def test_render_refuses_empty_layers():
    session = load_example()
    session["layers"] = []
    with pytest.raises(TimelineError):
        render_session(session, sample_rate=8000)


def test_standard_session_shape_sums_to_duration():
    segments = standard_session_shape(7.83, 600.0)
    assert sum(s["duration_s"] for s in segments) == pytest.approx(600.0)
    assert segments[0]["kind"] == "intro"
    assert segments[-2]["kind"] == "hold"
    assert segments[2]["beat_end_hz"] == 7.83
    with pytest.raises(TimelineError):
        standard_session_shape(4.0, 5.0)


def test_binaural_layer_tracks_envelope():
    """The rendered binaural pair's instantaneous difference follows
    the beat ramp (checked coarsely via zero-crossing rates)."""
    session = {
        "schema_version": "1.0.0", "session_id": "S", "title": "t",
        "duration_s": 4.0, "sample_rate": 8000,
        "segments": [
            {"kind": "hold", "duration_s": 2.0, "beat_start_hz": 4.0,
             "beat_end_hz": 4.0},
            {"kind": "hold", "duration_s": 2.0, "beat_start_hz": 12.0,
             "beat_end_hz": 12.0},
        ],
        "layers": [{"layer_id": "L1", "type": "binaural",
                    "carrier_hz": 200.0, "gain_db": -3.0}],
    }
    audio, _ = render_session(session)
    # beat rate = difference of L/R zero-cross rates
    def crossings(x):
        return int(np.sum(np.abs(np.diff(np.signbit(x)))))
    first_l = crossings(audio[:16000, 0]) / 2 / 2.0
    first_r = crossings(audio[:16000, 1]) / 2 / 2.0
    second_l = crossings(audio[16000:, 0]) / 2 / 2.0
    second_r = crossings(audio[16000:, 1]) / 2 / 2.0
    assert first_r - first_l == pytest.approx(4.0, abs=1.0)
    assert second_r - second_l == pytest.approx(12.0, abs=1.0)
