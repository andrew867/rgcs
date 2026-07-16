"""P00/P01: hash the complete local research corpus and upgrade the
v4 source registry where the previously metadata-only primaries are
now locally present (DV4C-003 upgrade path).

    python tools/v4x_ingest_corpus.py

Writes sources/registry/v4x_corpus_inventory.json (path, bytes,
sha256, family) and upgrades mapped SRC-V4-* records via
provenance_v4.ingest_file. Corpus files are LOCAL_ANALYSIS_ONLY and
never redistributed (internal-docs is gitignored)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REF = REPO / "internal-docs" / "plans-v4" / "references"
OUT = REPO / "sources" / "registry" / "v4x_corpus_inventory.json"

#: previously metadata-only registry records now locally present
UPGRADES = {
    "SRC-V4-01": "2506.07051v1.pdf",          # Toyoda IOME (arXiv)
    "SRC-V4-03": "2001.06255v1.pdf",          # Schlauderer (arXiv)
    "SRC-V4-05": "ncomms10720.pdf",           # Higuchi MnF2
    "SRC-V4-06": "Excitons in van der Waals magnetic materials.pdf",
    "SRC-V4-13": "lujan-et-al-2024-spin-orbit-exciton-induced-"
                 "phonon-chirality-in-a-quantum-magnet.pdf",
    "SRC-V4-14": "spin-momentum-locking-in-the-near-field-of-metal-"
                 "nanoparticles.pdf",
    "SRC-V4-18": "fdt-analysis-inverse-optical-magnetoelectric-"
                 "effect.pdf",
}

FAMILIES = (
    ("vogel", ("vogel", "lifestream", "labnotes", "crystal wisdom",
               "crystal knowledge", "crystal research", "legacy of "
               "marcel")),
    ("communications_log", ("jenhancommunicationslog",)),
    ("arisaka", ("arisaka", "rt1_", "rt2_", "rt3_", "rt4_",
                 "katsushi")),
    ("subtitle_transcript", ("c.e.r.n", "cern", "star nation",
                             "downsub")),
    ("physics_primary", ("2506.07051", "2001.06255", "ncomms10720",
                         "excitons in van der waals", "lujan",
                         "spin-momentum-locking", "2104.04803",
                         "2403.10628", "s41567", "s41586", "s41467",
                         "tsq1", "2510.14021", "physics.19",
                         "niyogi", "s41377", "s42005", "s41598",
                         "integrated_magnetless", "s10714")),
    ("fdt", ("fdt-analysis",)),
    ("source_lore_deck", ("18", "soul", "astral", "atlantis",
                          "radionics", "vibrational", "structured-"
                          "water", "body-electric", "dreamhill",
                          "powell", "understandingnew", "markovich",
                          "atree", "v1-", "v2-", "v3-", "v4-", "v5-",
                          "v6-", "v7-", "v8-")),
    ("historical_engineering", ("us725605", "ieee-spectrum", "beck",
                                "ems114675", "etop", "10562961",
                                "gravity_science", "mechanics___",
                                "quantum_theory", "relativity")),
)


def family(name: str) -> str:
    low = name.lower()
    for fam, keys in FAMILIES:
        for k in keys:
            if low.startswith(k) or k in low:
                return fam
    return "unclassified"


def main() -> int:
    from rscs2_core import provenance_v4 as pv
    inv = []
    for p in sorted(REF.iterdir()):
        if not p.is_file():
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        inv.append({"filename": p.name, "bytes": p.stat().st_size,
                    "sha256": h, "family": family(p.name),
                    "licence_status": "LOCAL_ANALYSIS_ONLY",
                    "redistribution_allowed": False})
    OUT.write_text(json.dumps(
        {"generated_by": "tools/v4x_ingest_corpus.py",
         "n_files": len(inv), "root":
         "internal-docs/plans-v4/references (gitignored; hashes only "
         "are committed)", "files": inv}, indent=2) + "\n",
        encoding="utf-8")
    print(f"inventory: {len(inv)} files hashed")
    fam_counts = {}
    for r in inv:
        fam_counts[r["family"]] = fam_counts.get(r["family"], 0) + 1
    print("families:", json.dumps(fam_counts, sort_keys=True))

    upgraded = []
    for sid, fname in UPGRADES.items():
        f = REF / fname
        if f.exists():
            try:
                rec = pv.ingest_file(sid, f)
                upgraded.append((sid, rec["access_status"]))
            except pv.ProvenanceError as e:
                print(f"{sid}: {e}")
        else:
            print(f"{sid}: file missing: {fname}")
    for sid, st in upgraded:
        print(f"upgraded {sid} -> {st}")
    # SRC-V4-19 (subtitle transcripts): record the hashes in the note
    return 0


if __name__ == "__main__":
    sys.exit(main())
