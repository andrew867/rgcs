"""P19 — publication firewall.

Every test here must be able to fail. A leak scanner that finds
nothing because it looks for nothing is the worst possible outcome, so
the detection tests plant content and require a hit.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

from r10 import firewall as F

ROOT = pathlib.Path(__file__).resolve().parents[2]


# --- the scanner actually detects -------------------------------------

@pytest.mark.parametrize("category,sample", [
    ("PERSONAL_IDENTITY", "notes from the star family session"),
    ("PRIVATE_PATH", r"C:\Users\someone\Documents\thing.txt"),
    ("PRIVATE_PATH", "/home/someone/private/notes.md"),
    ("CREDENTIAL", "token = ghp_abcdefghij0123456789abcdefghij"),
    ("CREDENTIAL", "-----BEGIN RSA PRIVATE KEY-----"),
    ("SUPERNATURAL_AUTHENTICATION", "this proves extraterrestrial origin"),
])
def test_planted_content_is_detected(category, sample):
    """If these do not fire, the scanner is decorative."""
    hits = F.scan_text(sample, "planted.md", "WORKING_TREE")
    assert hits, f"{category} sample was not detected"
    assert any(h.category == category for h in hits)


def test_ordinary_content_is_not_flagged():
    """A scanner that flags everything is equally useless."""
    clean = (
        "The octave ratio is exactly 2:1 and the analysis uses "
        "Fraction throughout. See docs/v52/R9_FINDINGS.md for the "
        "carrier feasibility result of 0.060 interactions per year."
    )
    assert F.scan_text(clean, "clean.md", "WORKING_TREE") == []


def test_findings_never_quote_the_leak():
    """A leak report that includes the leak is a second leak."""
    hits = F.scan_text("the star family transcript", "x.md", "WORKING_TREE")
    rec = hits[0].as_record()
    assert rec["excerpt"] == ("REDACTED — a leak report must not quote "
                              "the leak")
    assert "star" not in str(rec).lower()


# --- the real repository ----------------------------------------------

def test_committed_tree_is_clean():
    """R10-D-003. The gate scans what is COMMITTED, because that is
    what publication means. The working tree is the developer's disk
    and carries transient state -- including files that tests/v4
    rewrites mid-run (R10-D-002), which is exactly how this failed on
    Linux CI while passing on Windows and macOS.
    """
    findings = F.scan_committed(ROOT)
    assert findings == [], [f.as_record() for f in findings]


def test_the_gate_is_immune_to_test_suite_tree_mutation(tmp_path):
    """The regression test for the CI failure itself.

    A tracked file that is clean in the commit but dirtied on disk
    must NOT trip the gate -- and must still trip the working-tree
    scanner, so the pre-commit check keeps its teeth.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.st"],
                   cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"],
                   cwd=repo, check=True)
    f = repo / "inventory.json"
    f.write_text('{"clean": true}\n')
    subprocess.run(["git", "add", "inventory.json"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "clean"], cwd=repo, check=True)

    # a test run stamps a runner path into the tracked file
    f.write_text('{"root": "/home/runner/work/repo/repo"}\n')

    assert F.scan_committed(repo) == []          # gate: unaffected
    assert F.scan_working_tree(repo) != []       # pre-commit: still bites
    assert F.enforce(repo, check_history=False)["clean"]


def test_public_git_history_carries_a_declared_residual():
    """R10-D-001. History contains absolute build paths committed
    before this scanner existed. Deleting a file later does not
    unpublish it, and rewriting public history is forbidden by the
    release contract, so this is DECLARED, not silently excluded.

    The test asserts the exposure is bounded and of the known
    category. If a NEW category ever appears in history, it fails.
    """
    findings = F.scan_git_history(ROOT, max_commits=400)
    categories = {f.category for f in findings}
    assert categories <= {"PRIVATE_PATH"}, (
        f"unexpected category in git history: "
        f"{categories - {'PRIVATE_PATH'}}")


def test_no_credentials_or_personal_identity_anywhere_in_history():
    """The categories that would actually matter must be empty, in
    history as well as the working tree."""
    findings = F.scan_git_history(ROOT, max_commits=400)
    serious = [f for f in findings
               if f.category in ("CREDENTIAL", "PERSONAL_IDENTITY",
                                 "PRIVATE_CHANNELLING")]
    assert serious == [], [f.as_record() for f in serious]


def test_enforce_passes_on_the_committed_tree():
    report = F.enforce(ROOT, check_history=False)
    assert report["clean"]
    assert report["finding_count"] == 0


def test_frozen_surface_exposure_is_declared_not_hidden():
    """A clean live tree with history quietly excluded is not honest.
    The exposure has to be reported with a severity assessment."""
    fz = F.frozen_surface_exposure(ROOT)
    assert fz["status"] == "DECLARED_RESIDUAL_EXPOSURE"
    assert fz["finding_count"] > 0
    assert fz["categories"] == ["PRIVATE_PATH"]
    assert "invalidate the provenance" in fz["why_not_repaired"] or         "invalidate the" in fz["why_not_repaired"]
    assert fz["assessed_severity"].startswith("LOW")


def test_frozen_surfaces_are_skipped_by_default_but_reachable():
    default = F.scan_committed(ROOT)
    with_frozen = F.scan_committed(ROOT, include_frozen=True)
    assert len(with_frozen) > len(default)
    assert default == []


def test_enforce_raises_when_something_is_found(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.st"],
                   cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"],
                   cwd=repo, check=True)
    (repo / "leak.md").write_text("the chosen one transcript\n")
    subprocess.run(["git", "add", "leak.md"], cwd=repo, check=True)
    # must be committed: the gate scans the committed surface, and a
    # staged-but-uncommitted file is not yet published (R10-D-003)
    subprocess.run(["git", "commit", "-qm", "leak"], cwd=repo, check=True)
    with pytest.raises(F.LeakDetected) as e:
        F.enforce(repo, check_history=False)
    assert "Publication is blocked" in str(e.value)
    assert "chosen" not in str(e.value).lower()


# --- private root placement -------------------------------------------

def test_private_root_inside_the_worktree_is_refused():
    """.gitignore is not confidentiality."""
    r = F.private_root_is_outside(ROOT, ROOT / "private")
    assert r["private_is_inside_public"]
    assert not r["acceptable"]
    assert "not\nconfidentiality" in r["note"] or \
        "not confidentiality" in r["note"]


def test_the_actual_private_root_is_outside_the_public_tree():
    priv = ROOT.parent / "RGCS-private"
    r = F.private_root_is_outside(ROOT, priv)
    assert r["acceptable"]


# --- sanitized export -------------------------------------------------

def test_export_requires_actual_redaction():
    with pytest.raises(ValueError) as e:
        F.sanitized_export_record("a" * 64, "b" * 64, [], "reviewer", "1")
    assert "not a sanitisation" in str(e.value)


def test_export_refuses_an_unchanged_copy():
    with pytest.raises(ValueError) as e:
        F.sanitized_export_record("a" * 64, "a" * 64, ["names"],
                                  "reviewer", "1")
    assert "nothing was\nchanged" in str(e.value) or \
        "nothing was changed" in str(e.value)


def test_valid_export_record_carries_the_no_reconstruction_statement():
    rec = F.sanitized_export_record(
        "a" * 64, "b" * 64, ["removed operator name", "removed URL"],
        "operator", "sanitizer-1.0")
    assert rec["schema"] == "rgcs.sanitized_export.v1"
    assert "does not permit reconstruction" in \
        rec["no_reconstruction_statement"]
    assert len(rec["redactions"]) == 2


# --- registry hygiene --------------------------------------------------

def test_every_category_has_patterns():
    for cat, pats in F.FORBIDDEN_PATTERNS.items():
        assert pats, cat


def test_allowlist_is_small_and_explicit():
    """An allowlist that grows is a firewall that stops working."""
    assert len(F.POLICY_ALLOWLIST) <= 5
