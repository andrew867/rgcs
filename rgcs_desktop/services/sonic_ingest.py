"""Frequency Key Studio metadata ingestion (metadata ONLY).

Parses public web/video titles and descriptions into structured
source-recipe records: extracted frequencies with roles, claimed-use
tags, and a recipe-type guess. Claimed uses are recorded from source
text, never endorsed.

Deliberately absent: there is no audio downloader in this module or
anywhere in Frequency Key Studio (DR-004). Ingestion is titles,
descriptions, and metadata fields the caller already has.
"""
from __future__ import annotations

import re

#: value + unit ("528Hz", "6.3 hz", "1.2 kHz")
_FREQ_RE = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>hz|hertz|khz|kilohertz)\b",
    re.IGNORECASE)
#: slash pairs ("100/104 Hz")
_PAIR_RE = re.compile(
    r"(?P<left>\d+(?:\.\d+)?)\s*/\s*(?P<right>\d+(?:\.\d+)?)\s*hz\b",
    re.IGNORECASE)

#: claimed-use taxonomy: tag -> trigger words (lowercase substrings)
CLAIMED_USE_TAXONOMY: dict[str, tuple[str, ...]] = {
    "sleep": ("sleep", "insomnia", "deep rest"),
    "relaxation": ("relax", "calm", "stress relief", "soothing"),
    "focus": ("focus", "study", "concentration", "attention", "adhd"),
    "meditation": ("meditation", "meditate", "mindfulness"),
    "astral projection": ("astral", "obe", "out of body",
                          "out-of-body"),
    "lucid dreaming": ("lucid dream",),
    "third eye": ("third eye", "pineal"),
    "schumann": ("schumann",),
    "gateway-style": ("gateway", "focus 10", "focus 12"),
    "hemi-sync-inspired": ("hemi sync", "hemi-sync", "hemisync"),
    "healing claims": ("healing", "heal", "dna repair", "miracle"),
    "energy claims": ("chakra", "kundalini", "aura", "energy cleanse"),
    "manifestation claims": ("manifest", "abundance", "law of attraction"),
    "anxiety claims": ("anxiety", "depression"),
}

#: beats live below this; carriers above
_BEAT_CEILING_HZ = 45.0


class IngestError(ValueError):
    pass


def normalize_frequency(value: float, unit: str) -> float:
    unit = unit.strip().lower()
    if unit in ("hz", "hertz"):
        return float(value)
    if unit in ("khz", "kilohertz"):
        return float(value) * 1000.0
    raise IngestError(f"unknown frequency unit {unit!r}")


def extract_frequencies(text: str) -> list[dict]:
    """All frequencies in a text, deduplicated, with a role guess.

    Returns dicts: {hz, role, raw}. Roles: carrier_candidate,
    beat_target_candidate, ambiguous.
    """
    hits: list[dict] = []
    seen: set[float] = set()

    def add(hz: float, raw: str) -> None:
        hz = round(hz, 6)
        if hz <= 0 or hz in seen:
            return
        seen.add(hz)
        if hz < _BEAT_CEILING_HZ:
            role = "beat_target_candidate"
        elif hz >= 20000:
            role = "ambiguous"
        else:
            role = "carrier_candidate"
        hits.append({"hz": hz, "role": role, "raw": raw})

    for m in _PAIR_RE.finditer(text):
        left = float(m.group("left"))
        right = float(m.group("right"))
        add(left, m.group(0))
        add(right, m.group(0))
        beat = abs(right - left)
        if 0 < beat < _BEAT_CEILING_HZ:
            add(beat, f"{m.group(0)} (pair difference)")
    for m in _FREQ_RE.finditer(text):
        add(normalize_frequency(float(m.group("value")), m.group("unit")),
            m.group(0))
    return hits


def extract_claimed_tags(text: str) -> list[str]:
    """Claimed-use tags found in text (taxonomy order, deduplicated).

    Triggers match on word boundaries: "aura" must not fire inside
    "binaural", nor "sleep" inside "asleep"."""
    low = text.lower()
    out = []
    for tag, triggers in CLAIMED_USE_TAXONOMY.items():
        for trigger in triggers:
            if re.search(rf"\b{re.escape(trigger)}\b", low):
                out.append(tag)
                break
    return out


def _recipe_type_guess(text: str, freqs: list[dict]) -> str:
    low = text.lower()
    if "isochronic" in low:
        return "isochronic"
    if "monaural" in low:
        return "monaural"
    if "binaural" in low:
        return "binaural"
    if any(f["role"] == "beat_target_candidate" for f in freqs) and \
       any(f["role"] == "carrier_candidate" for f in freqs):
        return "binaural (guessed from frequency pair)"
    if "noise" in low or "ambient" in low or "rain" in low:
        return "noise_bed"
    return "unknown"


def parse_video_metadata(record: dict) -> dict:
    """A source_recipe dict (schema-valid) from raw video metadata.

    ``record``: url (required), title (required), plus optional
    platform, channel, description, duration_s, published, language.
    Only metadata fields are read — never media."""
    url = record.get("url", "").strip()
    title = record.get("title", "").strip()
    if not url or not title:
        raise IngestError("record needs at least url and title")
    description = record.get("description", "") or ""

    title_hits = extract_frequencies(title)
    desc_hits = extract_frequencies(description)
    title_hz = {h["hz"] for h in title_hits}
    extracted = []
    for h in title_hits:
        extracted.append({"hz": h["hz"], "role": h["role"],
                          "found_in": "title"})
    for h in desc_hits:
        if h["hz"] not in title_hz:
            extracted.append({"hz": h["hz"], "role": "description_only",
                              "found_in": "description"})

    combined = f"{title}\n{description}"
    out = {
        "source_id": record.get("source_id")
                     or f"SRC-{abs(hash(url)) % 10**8:08d}",
        "url": url,
        "platform": record.get("platform", "unknown"),
        "title": title,
        "channel": record.get("channel", ""),
        "description": description,
        "extracted_frequencies_hz": extracted,
        "claimed_uses": extract_claimed_tags(combined),
        "recipe_type_guess": _recipe_type_guess(combined,
                                                title_hits + desc_hits),
        "source_status": "source-language",
        "review_status": "unreviewed",
    }
    for key in ("duration_s", "published", "language"):
        if record.get(key) not in (None, ""):
            out[key] = record[key]
    return out


def parse_corpus(records: list[dict]) -> tuple[list[dict], list[str]]:
    """Parse many records; returns (parsed, error strings). Duplicate
    URLs are collapsed (first record wins)."""
    parsed, errors, seen_urls = [], [], set()
    for i, record in enumerate(records):
        try:
            row = parse_video_metadata(record)
        except IngestError as exc:
            errors.append(f"record {i}: {exc}")
            continue
        if row["url"] in seen_urls:
            errors.append(f"record {i}: duplicate url {row['url']}")
            continue
        seen_urls.add(row["url"])
        parsed.append(row)
    return parsed, errors
