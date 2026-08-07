"""Frequency Key Studio metadata ingestion tests (metadata only)."""
import inspect

import pytest

from rgcs_desktop.services import sonic_ingest
from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.services.sonic_ingest import (
    IngestError, extract_claimed_tags, extract_frequencies,
    normalize_frequency, parse_corpus, parse_video_metadata)


def test_extract_hz_title():
    hits = extract_frequencies("528Hz + 6.3 Hz Astral Projection "
                               "Binaural Beat")
    values = [round(h["hz"], 3) for h in hits]
    assert 528.0 in values
    assert 6.3 in values
    roles = {h["hz"]: h["role"] for h in hits}
    assert roles[528.0] == "carrier_candidate"
    assert roles[6.3] == "beat_target_candidate"


def test_extract_khz_normalized():
    hits = extract_frequencies("1.2 kHz carrier sweep")
    assert hits[0]["hz"] == 1200.0


def test_extract_pair_and_difference():
    hits = extract_frequencies("classic 100/104 Hz patent pair")
    values = {h["hz"] for h in hits}
    assert {100.0, 104.0, 4.0} <= values


def test_normalize_frequency_units():
    assert normalize_frequency(2.5, "kHz") == 2500.0
    assert normalize_frequency(440, "hertz") == 440.0
    with pytest.raises(IngestError):
        normalize_frequency(1, "bpm")


def test_claimed_tags():
    tags = extract_claimed_tags(
        "Deep Sleep Schumann 7.83 Hz | third eye healing meditation")
    assert "sleep" in tags
    assert "schumann" in tags
    assert "third eye" in tags
    assert "healing claims" in tags
    assert "meditation" in tags


def test_parse_video_metadata_schema_valid():
    record = {
        "url": "https://example.invalid/watch?v=abc",
        "platform": "youtube",
        "title": "528Hz + 6.3 Hz Astral Projection Binaural Beat",
        "description": "with 7.83 Hz Schumann resonance background",
        "duration_s": 1800,
    }
    row = parse_video_metadata(record)
    assert validate_instance(row, "source_recipe.schema.json") == []
    by_hz = {f["hz"]: f for f in row["extracted_frequencies_hz"]}
    assert by_hz[528.0]["found_in"] == "title"
    assert by_hz[7.83]["role"] == "description_only"
    assert "astral projection" in row["claimed_uses"]
    assert row["recipe_type_guess"] == "binaural"
    assert row["source_status"] == "source-language"


def test_parse_requires_url_and_title():
    with pytest.raises(IngestError):
        parse_video_metadata({"title": "no url"})


def test_parse_corpus_dedupes():
    records = [
        {"url": "https://example.invalid/1", "title": "4 Hz focus"},
        {"url": "https://example.invalid/1", "title": "duplicate"},
        {"title": "broken record"},
    ]
    parsed, errors = parse_corpus(records)
    assert len(parsed) == 1
    assert len(errors) == 2


def test_no_audio_downloader_exists():
    """DR-004: metadata only. The ingest module must not import any
    download/network machinery."""
    source = inspect.getsource(sonic_ingest)
    for forbidden in ("urllib", "requests", "httpx", "yt_dlp", "yt-dlp",
                      "youtube_dl", "urlopen", "socket"):
        assert forbidden not in source, forbidden
