"""P52 — Multiple-hypothesis and description-length scoring.

POWER: the compact mapping that survives the multiplicity correction is the best
explanation even when an ornate codec has the smaller raw residual — the best
raw match is not the best explanation. Negative: a significance claim without a
multiplicity correction is refused; an uncorrected raw p-value that clears alpha
does not survive correction over a large space. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import mdl as M
from cwatlas.claims import ClaimError
from cwatlas.search_space import SearchSpace, count_search_space


def _candidates():
    ornate = M.Candidate("ornate_fit", codec_bits=8.0, param_bits=220.0,
                         residual_bits=0.5, p_value=0.002)
    compact = M.Candidate("compact_map", codec_bits=8.0, param_bits=24.0,
                          residual_bits=9.0, p_value=1e-6)
    noise = M.Candidate("noisy_guess", codec_bits=8.0, param_bits=40.0,
                        residual_bits=60.0, p_value=0.04)
    return ornate, compact, noise


# --- POWER: best raw match is not best explanation ---------------------------

def test_best_raw_is_not_best_explanation():
    ornate, compact, noise = _candidates()
    space = count_search_space(codecs=4, frames=3, depths=8, catalogue=5,
                               transforms=6)
    res = M.select_best_explanation([ornate, compact, noise], space,
                                    method=M.Correction.SIDAK)
    # Ornate has the smallest residual (the prettiest raw fit)...
    assert res.best_raw == "ornate_fit"
    # ...but the compact mapping is the best explanation once cost is charged.
    assert res.best_explanation == "compact_map"


def test_description_length_prefers_compact():
    ornate, compact, _ = _candidates()
    assert compact.description_length() < ornate.description_length()


def test_description_length_bits_sums():
    assert M.description_length_bits(8.0, 24.0, 9.0) == 41.0


# --- Multiplicity corrections -------------------------------------------------

def test_bonferroni_and_sidak_inflate_pvalues():
    assert M.bonferroni(0.01, 100) == pytest.approx(1.0)
    assert M.sidak(0.01, 100) > 0.01
    assert M.sidak(0.01, 1) == pytest.approx(0.01)


def test_uncorrected_hit_does_not_survive_large_space():
    # A raw p=0.002 looks significant, but not across a large search space.
    ornate, _, _ = _candidates()
    big = count_search_space(codecs=4, frames=3, depths=8, catalogue=5,
                             transforms=6, anchors=50)
    res = M.select_best_explanation([ornate], big, method=M.Correction.BONFERRONI)
    assert res.corrected_pvalues["ornate_fit"] == pytest.approx(1.0)
    assert "ornate_fit" not in res.survivors
    assert res.best_explanation is None


def test_benjamini_hochberg_decisions():
    # One clearly significant p-value plus null-ish ones.
    decisions = M.benjamini_hochberg([1e-6, 0.5, 0.6, 0.7], alpha=0.05)
    assert decisions[0] is True
    assert decisions[1] is False


# --- Negative -----------------------------------------------------------------

def test_refuse_uncorrected_multiplicity():
    with pytest.raises(ClaimError):
        M.refuse_uncorrected_multiplicity()


def test_bad_bits_refused():
    with pytest.raises(M.MDLError):
        M.Candidate("bad", codec_bits=-1.0, param_bits=1.0, residual_bits=1.0,
                    p_value=0.1)


def test_bad_pvalue_refused():
    with pytest.raises(M.MDLError):
        M.Candidate("bad", codec_bits=1.0, param_bits=1.0, residual_bits=1.0,
                    p_value=1.5)


def test_bh_via_correct_pvalue_refused():
    with pytest.raises(M.MDLError):
        M.correct_pvalue(0.01, 10, M.Correction.BENJAMINI_HOCHBERG)


def test_empty_candidates_refused():
    with pytest.raises(M.MDLError):
        M.select_best_explanation([], count_search_space(codecs=2))


# --- Determinism --------------------------------------------------------------

def test_selection_is_deterministic():
    cands = list(_candidates())
    space = count_search_space(codecs=4, frames=3, depths=8)
    a = M.select_best_explanation(cands, space)
    b = M.select_best_explanation(cands, space)
    assert a == b


def test_report_declares_boundary():
    r = M.mdl_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["best_raw_match"] != r["best_explanation"]
    assert r["tranche"] == "T07"
