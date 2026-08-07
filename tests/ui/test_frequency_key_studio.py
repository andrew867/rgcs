"""Frequency Key Studio UI tests (offscreen): navigation, wizard golden
path, recipe library, and metadata parsing."""
from __future__ import annotations


def test_home_card_navigates_to_studio(main_window):
    home = main_window.panels["Design Studio"]
    card = next(c for c in home.cards
                if c.workflow["key"] == "frequency_key_studio")
    card.button.click()
    assert main_window.tabs.currentWidget() is \
        main_window.panels["Frequency Key Studio"]


def test_studio_pages_present(main_window):
    studio = main_window.panels["Frequency Key Studio"]
    titles = [studio.pages.tabText(i)
              for i in range(studio.pages.count())]
    assert titles == ["New Session", "Recipe Library", "Web Corpus"]
    info = studio.inspector_info()
    for key in ("properties", "classification", "units", "provenance"):
        assert key in info
    assert info["properties"]["seed recipes"] == 7


def test_new_session_wizard_golden_path(main_window):
    studio = main_window.panels["Frequency Key Studio"]
    page = studio.new_session
    session = page.preview()
    assert session is not None
    assert session["layers"][0]["carrier_hz"] == 925.0
    assert session["layers"][0]["beat_hz"] == 7.83
    # render a short session end to end
    exports = page.render_and_export(duration_s=12.0)
    assert exports["wav"].is_file()
    assert exports["json"].is_file()
    assert exports["pdf"].is_file()
    assert exports["bundle"].is_file()
    ws_root = str(main_window.context.workspace.root)
    assert str(exports["wav"]).startswith(ws_root)


def test_recipe_library_search_and_rows(main_window):
    studio = main_window.panels["Frequency Key Studio"]
    lib = studio.recipe_library
    assert lib.table.rowCount() == 7
    lib.search.setText("schumann")
    assert lib.table.rowCount() == 1
    lib.search.setText("925")
    assert lib.table.rowCount() == 2
    lib.search.setText("")
    assert lib.table.rowCount() == 7


def test_recipe_library_renders_preview(main_window):
    studio = main_window.panels["Frequency Key Studio"]
    lib = studio.recipe_library
    lib.search.setText("")
    lib.table.selectRow(0)
    wav = lib.render_selected(duration_s=12.0)
    assert wav is not None and wav.is_file()


def test_web_corpus_parses_metadata(main_window):
    studio = main_window.panels["Frequency Key Studio"]
    corpus = studio.web_corpus
    corpus.url.setText("https://example.invalid/watch?v=abc")
    corpus.title.setText("528Hz + 6.3 Hz Astral Projection Binaural Beat")
    corpus.description.setPlainText("with 7.83 Hz Schumann background")
    parsed = corpus.parse()
    assert parsed is not None
    values = {f["hz"] for f in parsed["extracted_frequencies_hz"]}
    assert {528.0, 6.3, 7.83} <= values
    assert "astral projection" in parsed["claimed_uses"]


def test_web_corpus_refuses_empty(main_window):
    studio = main_window.panels["Frequency Key Studio"]
    corpus = studio.web_corpus
    corpus.url.setText("")
    corpus.title.setText("")
    assert corpus.parse() is None
