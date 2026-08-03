"""Public-release filter for the Terra coordinate/codec surface.

Includes coordinate and codec artifacts; excludes private message/ASCII
decoding artifacts. The exclusion terms are the v0.6 declared list, and
exclusion wins over inclusion on any conflict -- a path matching both is
PRIVATE_EXCLUDED, because a false release is worse than a false hold.

A path already inside a declared private/non-release archive is reported
as PRIVATE_ARCHIVED rather than excluded again, per the spec's "unless it
is inside a private/nonrelease archive" clause: such material is not
release-bound in the first place.
"""

from __future__ import annotations

import pathlib

#: v0.6 declared exclusion terms, matched case-insensitively anywhere in
#: path, title or tag.
EXCLUDE_TERMS = ("crabwood", "ascii", "plaintext", "message_decode",
                 "message-decoding", "glyph_message", "private_comms")

#: Roots that mark private, non-release archives.
PRIVATE_ARCHIVE_MARKERS = ("internal-docs", "release/r1013-private",
                           "cwatlas_private", "negative_results")

#: Inclusion hints for coordinate/codec material.
INCLUDE_HINTS = ("coordinate", "codec", "terra", "vector", "parse", "map",
                 "polygon", "path", "root", "variable_length",
                 "variable-length", "projector", "geodesic")

CLASS_PUBLIC = "PUBLIC_RELEASE_ALLOWED"
CLASS_EXCLUDED = "PRIVATE_EXCLUDED"
CLASS_ARCHIVED = "PRIVATE_ARCHIVED"
CLASS_REVIEW = "REVIEW_REQUIRED"


def classify(path_or_title: str, tags=()) -> dict:
    """Classify one candidate artifact. Deterministic, exclusion-first."""
    hay = " ".join([str(path_or_title), *map(str, tags)]).lower()
    hit = next((t for t in EXCLUDE_TERMS if t in hay), None)
    archived = next((m for m in PRIVATE_ARCHIVE_MARKERS
                     if m in hay.replace("\\", "/")), None)
    if hit and archived:
        cls, why = CLASS_ARCHIVED, (f"matches '{hit}' but already inside "
                                    f"private archive '{archived}'")
    elif hit:
        cls, why = CLASS_EXCLUDED, f"matches exclusion term '{hit}'"
    elif archived:
        cls, why = CLASS_ARCHIVED, f"inside private archive '{archived}'"
    elif any(h in hay for h in INCLUDE_HINTS):
        cls, why = CLASS_PUBLIC, "matches a coordinate/codec inclusion hint"
    else:
        cls, why = CLASS_REVIEW, "no rule matched; a human decides"
    return {"path": str(path_or_title), "class": cls, "reason": why}


def filter_manifest(paths, tags_by_path=None) -> list:
    tags_by_path = tags_by_path or {}
    rows = [classify(p, tags_by_path.get(str(p), ())) for p in paths]
    rows.sort(key=lambda r: (r["class"], r["path"]))
    return rows


def release_report(rows) -> dict:
    counts = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    return {"total": len(rows), "counts": counts,
            "no_excluded_term_released": not any(
                r["class"] == CLASS_PUBLIC and any(
                    t in r["path"].lower() for t in EXCLUDE_TERMS)
                for r in rows)}


def scan_repo_tree(root: str | pathlib.Path, subdirs=("docs", "r1053",
                                                      "cwatlas")) -> list:
    """Classify real tracked trees, for the filter report."""
    root = pathlib.Path(root)
    paths = []
    for sub in subdirs:
        base = root / sub
        if base.is_dir():
            paths.extend(p.as_posix() for p in base.rglob("*")
                         if p.is_file())
    return filter_manifest(sorted(paths))


__all__ = ["EXCLUDE_TERMS", "PRIVATE_ARCHIVE_MARKERS", "INCLUDE_HINTS",
           "CLASS_PUBLIC", "CLASS_EXCLUDED", "CLASS_ARCHIVED",
           "CLASS_REVIEW", "classify", "filter_manifest", "release_report",
           "scan_repo_tree"]
