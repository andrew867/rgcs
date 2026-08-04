"""R10.15 Phase A02 — public/private boundary, executable.

The private path-vector capture must never enter the tracked public
tree. Detecting a leak without storing the secret is the whole
problem: a per-wire hash would NOT be safe here, because a 9-to-11
digit decimal is brute-forceable in seconds, so publishing per-wire
digests would effectively publish the wires.

The design therefore uses:

1. STRUCTURAL DETECTION plus a public allowlist. Private wires share a
   known lexical signature (leading ``16``, terminal ``3``, 9-11
   decimal digits). The scanner flags every token with that signature
   that is not already public in the committed R10.11/R10.12 corpora.
   This catches an unknown private wire without ever storing one.
2. AGGREGATE COMMITMENTS. Two SHA-256 values over the whole capture and
   over the whole 17-wire list. These commit to the private records
   (so a later disclosure can be checked against them) but are not
   invertible to any individual value.
3. FORBIDDEN PHRASES and PRIVATE PATH FRAGMENTS: provenance wording,
   private pack directory names, and capture filenames.

The scan runs over tracked files only: an untracked private working
file is allowed to exist locally, which is exactly how the private
lane is meant to be used.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

#: Aggregate commitments to the private capture (Phase A02, verified
#: 2026-07-28 against the private lane; neither value is invertible).
PRIVATE_CAPTURE_SHA256 = \
    "1a41efe88402dcfb154b2e3fcd2700c58977a88516ec2c77572c8823815ecfd3"
PRIVATE_WIRE_LIST_SHA256 = \
    "0b079fc6b716b4261d2ba3ab56133a2a8c3515154c2789d58b05db8803ba0d93"

#: Structural census of the private capture (structure only, no values).
PRIVATE_STRUCTURE = {
    "wire_count": 17,
    "decimal_length_census": {"9": 3, "10": 6, "11": 8},
    "all_start_16": True,
    "all_end_3": True,
    "overlap_with_public_corpus": 0,
    "note": "counts and lexical structure only; no value is recorded "
            "here or anywhere in the public tree",
}

#: TRANSPORT HYPOTHESES ARE NOT SHARED ACROSS LANES (R10.15 override).
#: The R10.13 public codec assumes a FIXED 21+3d core. The private
#: path-vector lane is governed by a LATER operator answer describing a
#: VARIABLE-core, header-profiled, arbitrary-length decimal-to-octal
#: transport. Both readings are preserved; neither is promoted, and the
#: public lane's fixed-core result must never be applied to private
#: material or vice versa. Detection here is therefore purely lexical
#: and length-agnostic, so that it cannot fail on an arbitrary-length
#: private wire.
TRANSPORT_HYPOTHESES = {
    "H_FIXED_CORE_R1013": {
        "assumption": "fixed 21+3d bit core, 6 payload digits at depth "
                      "0 plus one per level",
        "scope": "PUBLIC lane only (R10.13 corpora)",
        "status": "EXECUTED_BASELINE",
        "immutable_result": "R10.13 full suite 8129 passed, exit 0",
    },
    "H_VARIABLE_CORE_R1015": {
        "assumption": "variable core, header-profiled, arbitrary-length "
                      "decimal payload converted directly to octal; no "
                      "maximum depth; semantic core and left/right "
                      "split unresolved",
        "scope": "PRIVATE path-vector lane only",
        "status": "ACTIVE_UNRESOLVED",
        "rule": "must not inherit the fixed-core reading",
    },
    "separation_rule": "every private-lane result records which "
                       "hypothesis produced it; no cross-lane promotion",
}

#: Lexical signature of the segmented-family wire.
#:
#: Tuned against the real tree. Two competing requirements had to be
#: reconciled: the private transport hypothesis allows ARBITRARY
#: length, but an unbounded "16...3" pattern matches ordinary numeric
#: data (a first scan produced 1563 false positives, almost all of
#: them digits inside CSV float columns). The signature therefore
#: requires a STANDALONE integer token -- not adjacent to another
#: digit, a decimal point, or an exponent marker -- and a generous
#: length band around the observed family (9-11 digits) with headroom
#: to 20. Anything longer is caught by the aggregate commitments and
#: by review, not by this regex.
WIRE_SIGNATURE = re.compile(r"(?<![\d.eE+-])16\d{6,17}3(?![\d.])")

#: Provenance wording that must not appear in tracked public files.
#: NOTE: "DO_NOT_COMMIT" alone is NOT listed. The repository already
#: uses that token as its own policy marker in cwatlas/privacy.py and
#: dozens of receipts, so listing it would flag the project's existing
#: privacy machinery as a leak. Only phrases specific to the private
#: path-vector capture appear here.
FORBIDDEN_PHRASES = (
    "PATH_VECTOR_LEDGER", "RAW_CAPTURE_UNCHANGED",
    "10_PRIVATE_PATH_VECTORS",
    "path-vector ledger", "raw capture unchanged",
    "EOT @15:40",
)

#: Directory names from the private lane. ONLY the private pack
#: directory is listed. The gitignored provenance ledger path is
#: REFERENCED by design in historical receipts ("recorded in the
#: private provenance ledger"); naming a gitignored path does not
#: disclose its contents, and listing it flagged four legitimate
#: R10.9 and consolidation receipts as leaks.
PRIVATE_PATH_FRAGMENTS = (
    "10_PRIVATE_PATH_VECTORS_DO_NOT_COMMIT",
)

#: Extensions worth scanning (text-bearing, tracked).
SCAN_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".csv", ".txt",
                 ".yaml", ".yml", ".toml", ".cfg", ".rst", ".html"}

#: This module necessarily names the forbidden strings in order to
#: detect them; the scanner skips its own source and its own tests.
SELF_EXEMPT = ("rgcs_surface_wave/privacy.py",
               "tests/r1015/test_privacy_boundary.py")


#: The R10.13 consolidation commit. Everything present in the tree at
#: this commit is ALREADY PUBLIC by definition; the gate's job is to
#: catch NEW private material entering after it.
BASELINE_COMMIT = "20545f4"

#: Public calibration candidates intentionally released in the R10 Terra
#: calibration receipt. All other post-baseline wire-shaped values must be
#: rejected by the release-candidate scan.
PUBLIC_RELEASE_WIRES = frozenset({"1680769543", "168593073"})

_ALLOW_CACHE: set[str] | None = None


def public_wire_allowlist(repo_root: Path | str | None = None
                          ) -> set[str]:
    """Every wire-signature token already public at the baseline commit.

    Computed from git rather than hard-coded. An earlier version listed
    only the 47 wires of the golden-28 and 19-wire corpora, which
    flagged 568 legitimate tokens in the committed R10.11/R10.12
    evidence (the frozen P5/P6 candidate sets, the vector census, the
    conditional prediction tables). Those are public research
    artifacts, not leaks.
    """
    global _ALLOW_CACHE
    if _ALLOW_CACHE is not None:
        return _ALLOW_CACHE
    root = Path(repo_root) if repo_root else         Path(__file__).resolve().parents[1]
    allow: set[str] = set()
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "grep", "-h", "-o", "-I", "-E",
             r"16[0-9]{6,17}3", BASELINE_COMMIT],
            capture_output=True, text=True, timeout=300)
        allow |= set(re.findall(r"16[0-9]{6,17}3", out.stdout))
    except Exception:                      # pragma: no cover - optional
        pass
    for mod, attr in (("r1012.corpus", "golden28"),
                      ("r1013.exact_cover", "WIRES_19")):
        try:
            m = __import__(mod, fromlist=[attr])
            v = getattr(m, attr)
            allow |= ({str(w) for w in v()["wires"]} if callable(v)
                      else set(v))
        except Exception:                  # pragma: no cover - optional
            pass
    allow |= PUBLIC_RELEASE_WIRES
    _ALLOW_CACHE = allow
    return allow


def tracked_files(repo_root: Path) -> list[Path]:
    out = subprocess.run(["git", "-C", str(repo_root), "ls-files"],
                         capture_output=True, text=True, timeout=180)
    files = []
    for rel in out.stdout.splitlines():
        if not rel.strip():
            continue
        p = repo_root / rel
        if p.suffix.lower() in SCAN_SUFFIXES and p.is_file():
            files.append(p)
    return files


def scan_tracked(repo_root: Path | str | None = None) -> dict:
    """Full public/private boundary scan of the tracked tree."""
    root = Path(repo_root) if repo_root else \
        Path(__file__).resolve().parents[1]
    allow = public_wire_allowlist()
    findings: list[dict] = []
    scanned = 0
    for p in tracked_files(root):
        rel = p.relative_to(root).as_posix()
        if any(rel.endswith(x) for x in SELF_EXEMPT):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:                     # pragma: no cover
            continue
        scanned += 1
        for m in WIRE_SIGNATURE.finditer(text):
            if m.group(0) not in allow:
                findings.append({
                    "kind": "UNKNOWN_WIRE_SIGNATURE", "file": rel,
                    "line": text[:m.start()].count("\n") + 1,
                    "detail": "a token with the private-capture lexical "
                              "signature that is not in the public "
                              "corpus allowlist",
                    "value_withheld": True})
        low = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in low:
                findings.append({"kind": "FORBIDDEN_PHRASE", "file": rel,
                                 "detail": phrase})
        for frag in PRIVATE_PATH_FRAGMENTS:
            if frag.lower() in low:
                findings.append({"kind": "PRIVATE_PATH_FRAGMENT",
                                 "file": rel, "detail": frag})
    return {"schema": "rgcs.r1015.privacy-scan.v1",
            "files_scanned": scanned,
            "allowlisted_public_wires": len(allow),
            "findings": findings, "clean": not findings,
            "commitments": {
                "private_capture_sha256": PRIVATE_CAPTURE_SHA256,
                "private_wire_list_sha256": PRIVATE_WIRE_LIST_SHA256},
            "method": "structural signature + public allowlist; no "
                      "per-wire digest is stored because a short "
                      "decimal digest would be brute-forceable"}


def scan_release_candidates(
    repo_root: Path | str | None = None,
    report_path: Path | str | None = None,
) -> dict:
    """Scan only the hash-pinned safe-public set selected for release.

    The repository intentionally contains private, quarantined, and review
    lanes. Treating the whole tracked tree as public defeats that boundary,
    so this gate consumes the exclusion-first release report and refuses a
    stale or missing manifest entry before scanning its selected files.
    """
    root = (Path(repo_root) if repo_root else
            Path(__file__).resolve().parents[1])
    report = (Path(report_path) if report_path else
              root / "docs" / "release" / "r10_release_filter_report.json")
    findings: list[dict] = []
    scanned = 0
    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
        rows = payload["rows"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {
            "schema": "rgcs.r1015.release-privacy-scan.v1",
            "files_scanned": 0,
            "allowlisted_public_wires": len(public_wire_allowlist(root)),
            "findings": [{"kind": "RELEASE_REPORT_INVALID",
                          "file": str(report), "detail": str(exc)}],
            "clean": False,
        }

    allow = public_wire_allowlist(root)
    for row in rows:
        if row.get("classification") != "safe-public":
            continue
        rel = str(row.get("path", ""))
        p = root / rel
        if not p.is_file():
            findings.append({"kind": "RELEASE_FILE_MISSING", "file": rel})
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest != row.get("sha256"):
            findings.append({"kind": "RELEASE_FILE_HASH_MISMATCH",
                             "file": rel})
            continue
        if p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:  # pragma: no cover - platform-specific
            findings.append({"kind": "RELEASE_FILE_UNREADABLE",
                             "file": rel, "detail": str(exc)})
            continue
        scanned += 1
        for match in WIRE_SIGNATURE.finditer(text):
            if match.group(0) not in allow:
                findings.append({
                    "kind": "UNKNOWN_WIRE_SIGNATURE", "file": rel,
                    "line": text[:match.start()].count("\n") + 1,
                    "detail": "wire-shaped token is not in the reviewed "
                              "public corpus allowlist",
                    "value_withheld": True,
                })
        low = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in low:
                findings.append({"kind": "FORBIDDEN_PHRASE", "file": rel,
                                 "detail": phrase})
        for fragment in PRIVATE_PATH_FRAGMENTS:
            if fragment.lower() in low:
                findings.append({"kind": "PRIVATE_PATH_FRAGMENT",
                                 "file": rel, "detail": fragment})

    return {
        "schema": "rgcs.r1015.release-privacy-scan.v1",
        "files_scanned": scanned,
        "allowlisted_public_wires": len(allow),
        "findings": findings,
        "clean": not findings,
        "report": report.relative_to(root).as_posix(),
        "method": "hash-pinned safe-public rows + structural signature + "
                  "explicit public allowlist",
    }


def would_leak(text: str) -> list[dict]:
    """Check a candidate string before it is written to a public file."""
    allow = public_wire_allowlist()
    out = []
    for m in WIRE_SIGNATURE.finditer(text):
        if m.group(0) not in allow:
            out.append({"kind": "UNKNOWN_WIRE_SIGNATURE",
                        "value_withheld": True})
    low = text.lower()
    out += [{"kind": "FORBIDDEN_PHRASE", "detail": p}
            for p in FORBIDDEN_PHRASES if p.lower() in low]
    return out
