"""Frequency Key Studio v1.1/v1.2 UI tests (offscreen)."""
from __future__ import annotations

from rgcs_desktop.services.sonic_audio import sine, write_wav


def _studio(main_window):
    return main_window.panels["Frequency Key Studio"]


def test_studio_has_timeline_editor_page(main_window):
    studio = _studio(main_window)
    titles = [studio.pages.tabText(i)
              for i in range(studio.pages.count())]
    assert titles == ["New Session", "Timeline Editor", "Recipe Library",
                      "Session Library", "Web Corpus"]


def test_timeline_editor_validates_and_feeds_wizard(main_window):
    studio = _studio(main_window)
    editor = studio.timeline_editor
    assert editor.validate()                       # default rows valid
    assert editor.custom_segments() is None        # not enabled yet
    editor.enabled.setChecked(True)
    segments = editor.custom_segments()
    assert segments is not None and len(segments) == 5
    session = studio.new_session.build_session()
    assert session["segments"] == segments
    assert session["duration_s"] == sum(s["duration_s"] for s in segments)
    editor.enabled.setChecked(False)


def test_timeline_editor_refuses_bad_rows(main_window):
    studio = _studio(main_window)
    editor = studio.timeline_editor
    editor.table.item(0, 1).setText("0")           # zero duration
    assert not editor.validate()
    assert "Refused" in editor.status.text()
    editor.table.item(0, 1).setText("60")
    assert editor.validate()


def test_multi_carrier_and_loudness_in_wizard(main_window):
    studio = _studio(main_window)
    page = studio.new_session
    page.extra_carriers.setText("200, 528")
    page.loudness_on.setChecked(True)
    session = page.preview()
    carriers = [la["carrier_hz"] for la in session["layers"]
                if la["type"] == "binaural"]
    assert carriers == [925.0, 200.0, 528.0]
    assert session["loudness"]["target_rms_db"] == -20.0
    page.extra_carriers.setText("")
    page.loudness_on.setChecked(False)


def test_voice_cue_layer_in_wizard(main_window, tmp_path):
    studio = _studio(main_window)
    page = studio.new_session
    cue = write_wav(tmp_path / "cue.wav", 0.4 * sine(500.0, 0.5), 48000)
    page.voice_file.setText(str(cue))
    session = page.preview()
    voice = [la for la in session["layers"] if la["type"] == "voice_cue"]
    assert len(voice) == 1
    assert voice[0]["file"] == str(cue)
    page.voice_file.setText("")


def test_spectrogram_preview_renders(main_window):
    studio = _studio(main_window)
    page = studio.new_session
    assert not page.spectro_view.isVisibleTo(page)
    assert page.show_spectrogram()
    assert page.spectro_view.isVisibleTo(page)


def test_playback_degrades_gracefully(main_window):
    """Play either starts (backend present) or states unavailability —
    never raises."""
    studio = _studio(main_window)
    page = studio.new_session
    result = page.play_preview()
    assert result in (True, False)
    page._player.stop()


def test_batch_render_from_library(main_window):
    studio = _studio(main_window)
    lib = studio.recipe_library
    lib.search.setText("schumann")                 # 1 recipe shown
    manifest = lib.batch_render_shown(duration_s=12.0)
    assert manifest is not None
    assert [r["status"] for r in manifest["results"]] == ["rendered"]
    lib.search.setText("")


def test_corpus_roundtrip_cluster_and_recommend(main_window):
    studio = _studio(main_window)
    corpus = studio.web_corpus
    corpus.url.setText("https://example.invalid/v1")
    corpus.title.setText("528Hz + 6.3 Hz Astral Projection Binaural Beat")
    parsed = corpus.parse()
    assert parsed is not None
    assert "recommended seed recipes" in corpus.result.toPlainText()
    assert "RGCS-AST-0001" in corpus.result.toPlainText()
    assert corpus.add_to_corpus()
    assert not corpus.add_to_corpus()              # duplicate URL
    corpus.url.setText("https://example.invalid/v2")
    corpus.title.setText("925 Hz binaural focus")
    corpus.parse()
    assert corpus.add_to_corpus()
    clusters = corpus.cluster()
    assert len(clusters) == 2
    csv_path = corpus.export_csv()
    assert csv_path is not None and csv_path.is_file()
    assert "corpus: 2 records" in corpus.corpus_label.text()


def test_wobble_selector_in_wizard(main_window):
    studio = _studio(main_window)
    page = studio.new_session
    assert page.wobble.count() == 39            # None + 38 presets
    idx = page.wobble.findData("Octave 2 Stage Wobble")
    assert idx > 0
    page.wobble.setCurrentIndex(idx)
    page.wobble_dwell.setValue(2.0)
    session = page.preview()
    wob = session["layers"][0]["wobble"]
    assert wob == {"name": "Octave 2 Stage Wobble", "dwell_s": 2.0,
                   "target": "carrier"}
    page.wobble.setCurrentIndex(0)              # back to None
    session2 = page.preview()
    assert "wobble" not in session2["layers"][0]
