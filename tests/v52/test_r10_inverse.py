"""Q19 — inverse hidden-hedron estimation.

The reproduction tests are the easy half. The load-bearing ones are the
tests that establish the *limits*, and this module is written so that
every one of them has an input that makes it fail:

* the uniformity chi-square is run twice, once on the correct sampler
  and once on :func:`~r10.inverse.sample_normalised_uniform`, a
  plausible-looking wrong sampler that it must reject. A goodness-of-fit
  test that has never rejected anything has not been tested;
* the exact moment factors 20 and 60 are checked against simulation, and
  then *wrong* factors are checked to confirm simulation rejects them;
* the documented instability of plain tensor power iteration is measured
  rather than asserted -- the transverse derivative is computed
  numerically and must come out at -1;
* the non-uniform-density bias is compared against a closed-form
  prediction at three sample sizes, and the test fails if the error
  shrinks with more data;
* the non-identifiability results are checked constructively: the
  second-moment twin must match mean, covariance and volume to machine
  precision *and* differ in shape, and the two shell-equivalent
  tetrahedra must share an insphere exactly while differing grossly.

Every draw is seeded. Nothing here is a measurement.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import numpy as np
import pytest

from r10 import inverse as V

REF = V.REFERENCE_TETRAHEDRON
REGULAR = np.array([[1.0, 1.0, 1.0], [1.0, -1.0, -1.0],
                    [-1.0, 1.0, -1.0], [-1.0, -1.0, 1.0]])


# --- the exact algebra --------------------------------------------------

def test_dirichlet_covariance_is_four_i_minus_j_over_eighty():
    cov = V.dirichlet_uniform_covariance()
    for i in range(4):
        for j in range(4):
            expected = F(4 if i == j else 0, 80) - F(1, 80)
            assert cov[i][j] == expected
    assert cov[0][0] == F(3, 80)
    assert cov[0][1] == F(-1, 80)


def test_covariance_rows_sum_to_zero():
    """The weights sum to one, so every row of Cov(W) must vanish."""
    cov = V.dirichlet_uniform_covariance()
    for row in cov:
        assert sum(row) == 0


def test_third_central_moments_are_exact():
    m = V.dirichlet_third_central_moments()
    assert m["triple"] == F(1, 160)
    assert m["pair"] == F(-1, 480)
    assert m["distinct"] == F(1, 480)


def test_third_moment_decomposition_gives_one_over_sixty():
    d = V.third_moment_decomposition()
    assert d["A"] == F(1, 60)
    assert d["B"] == F(-1, 240)
    assert d["D"] == F(1, 480)
    assert 1 / d["A"] == V.THIRD_MOMENT_FACTOR


def test_decomposition_reconstructs_every_index_pattern():
    """The decomposition is a claim, not a definition; check it holds."""
    d, m = V.third_moment_decomposition(), V.dirichlet_third_central_moments()
    assert d["A"] + 3 * d["B"] + d["D"] == m["triple"]
    assert d["B"] + d["D"] == m["pair"]
    assert d["D"] == m["distinct"]


def test_second_moment_factor_follows_from_the_covariance():
    """Cov(X) = (1/20) sum c_i c_i^T is derived, not assumed."""
    assert V.SECOND_MOMENT_FACTOR == 1 / (4 * F(1, 80))


def test_whitened_simplex_gram_is_forced():
    e = V.CANONICAL_WHITENED_SIMPLEX
    gram = e @ e.T
    assert np.allclose(np.diag(gram), float(V.WHITENED_VERTEX_NORM_SQ))
    off = gram[~np.eye(4, dtype=bool)]
    assert np.allclose(off, -0.25)
    assert np.allclose(e.sum(axis=0), 0.0)
    assert np.allclose(e.T @ e, np.eye(3))


def test_canonical_third_norm_is_three_halves():
    e = V.CANONICAL_WHITENED_SIMPLEX
    t = np.einsum("ni,nj,nk->ijk", e, e, e)
    assert float(np.linalg.norm(t)) ** 2 == pytest.approx(
        float(V.CANONICAL_THIRD_NORM_SQ), rel=1e-12)


def test_cubic_form_maximum_is_one_over_root_three():
    e = V.CANONICAL_WHITENED_SIMPLEX
    t = np.einsum("ni,nj,nk->ijk", e, e, e)
    d = e[0] / np.linalg.norm(e[0])
    assert V.cubic_form(t, d) == pytest.approx(
        V.CANONICAL_CUBIC_MAX, rel=1e-12)
    rng = np.random.default_rng(7)
    x = rng.normal(size=(20_000, 3))
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    best = max(V.cubic_form(t, xi) for xi in x)
    assert best <= V.CANONICAL_CUBIC_MAX + 1e-9


# --- the forward model really is uniform --------------------------------

def test_uniform_sampler_passes_the_chi_square():
    pts = V.sample_uniform(REF, 200_000, seed=101)
    r = V.uniformity_chi_square(pts, REF)
    assert r["dof"] == 4
    assert r["p_value"] > 1e-3, r


def test_the_chi_square_rejects_a_plausible_wrong_sampler():
    """Normalised U(0,1) weights look like barycentric coordinates and
    are not uniform. If this test ever passes the sampler, the
    uniformity check is worthless."""
    pts = V.sample_normalised_uniform(REF, 200_000, seed=101)
    r = V.uniformity_chi_square(pts, REF)
    assert r["p_value"] < 1e-9
    assert r["chi_square"] > 1_000


def test_volume_ratio_check_holds_for_the_uniform_sampler():
    pts = V.sample_uniform(REF, 200_000, seed=102)
    for row in V.volume_ratio_check(pts, REF):
        assert abs(row["sigma"]) < 5.0, row


def test_volume_ratio_check_rejects_the_wrong_sampler():
    pts = V.sample_normalised_uniform(REF, 200_000, seed=102)
    sigmas = [abs(r["sigma"]) for r in V.volume_ratio_check(pts, REF)]
    assert max(sigmas) > 20.0


def test_uniform_samples_lie_inside_the_tetrahedron():
    pts = V.sample_uniform(REF, 5_000, seed=103)
    assert (V.barycentric(pts, REF) >= -1e-12).all()


def test_sampling_is_reproducible_and_seed_dependent():
    a = V.sample_uniform(REF, 500, seed=11)
    b = V.sample_uniform(REF, 500, seed=11)
    c = V.sample_uniform(REF, 500, seed=12)
    assert np.array_equal(a, b)
    assert not np.allclose(a, c)


def test_barycentric_inverts_the_forward_map():
    pts = V.sample_uniform(REF, 1_000, seed=104)
    w = V.barycentric(pts, REF)
    assert np.allclose(w.sum(axis=1), 1.0)
    assert np.allclose(w @ REF, pts)


# --- the moment identities ----------------------------------------------

def _true_moments(vertices):
    c = np.asarray(vertices, float) - np.asarray(vertices, float).mean(axis=0)
    return c.T @ c, np.einsum("ni,nj,nk->ijk", c, c, c)


#: Sampling noise on the moment estimates at N = 1e6 is about 0.25% of
#: the largest entry, measured across several seeds. A 1% tolerance is
#: therefore comfortable for the true factors and tight enough to reject
#: a factor that is 2% wrong.
_MOMENT_TOL = 0.01
_MOMENT_N = 1_000_000


def test_scatter_identity_holds_in_simulation():
    """Cov(X) * 20 == sum_i c_i c_i^T."""
    s_true, _ = _true_moments(REF)
    m = V.empirical_moments(V.sample_uniform(REF, _MOMENT_N, seed=201))
    assert np.abs(m.scatter - s_true).max() < _MOMENT_TOL * np.abs(
        s_true).max()


def test_third_moment_identity_holds_in_simulation():
    """E[(X-mu)^3] * 60 == sum_i c_i^3."""
    _, t_true = _true_moments(REF)
    m = V.empirical_moments(V.sample_uniform(REF, _MOMENT_N, seed=202))
    assert np.abs(m.third - t_true).max() < _MOMENT_TOL * np.abs(t_true).max()


def test_simulation_rejects_the_wrong_moment_factors():
    """The identities pin down 20 and 60 specifically.

    The nearest wrong factors tried here are only 2% away, so the two
    tests above are not passing on a slack tolerance. If a neighbouring
    factor also passed, they would prove nothing.
    """
    s_true, t_true = _true_moments(REF)
    m = V.empirical_moments(V.sample_uniform(REF, _MOMENT_N, seed=203))
    for wrong in (10.0, 19.6, 20.4, 30.0):
        scaled = m.scatter * (wrong / float(V.SECOND_MOMENT_FACTOR))
        assert np.abs(scaled - s_true).max() > _MOMENT_TOL * np.abs(
            s_true).max(), wrong
    for wrong in (30.0, 58.8, 61.2, 120.0):
        scaled = m.third * (wrong / float(V.THIRD_MOMENT_FACTOR))
        assert np.abs(scaled - t_true).max() > _MOMENT_TOL * np.abs(
            t_true).max(), wrong


def test_empirical_moments_reject_bad_shapes():
    with pytest.raises(ValueError):
        V.empirical_moments(np.zeros((10, 2)))
    with pytest.raises(V.EstimatorFailure):
        V.empirical_moments(np.zeros((3, 3)))


# --- the extraction step ------------------------------------------------

def test_plain_power_iteration_is_neutrally_stable():
    """The documented reason the textbook iteration is not used.

    Perturb a fixed point transversely by eps, take one plain power
    step, and measure the transverse component of the result. The ratio
    must come out at -1: no contraction, hence no convergence.
    """
    e = V.CANONICAL_WHITENED_SIMPLEX
    t = np.einsum("ni,nj,nk->ijk", e, e, e)
    d = e[0] / np.linalg.norm(e[0])
    tan = np.array([1.0, -1.0, 0.0])
    tan -= tan.dot(d) * d
    tan /= np.linalg.norm(tan)
    for eps in (1e-4, 1e-5, 1e-6):
        x = math.cos(eps) * d + math.sin(eps) * tan
        y = np.einsum("ijk,j,k->i", t, x, x)
        y /= np.linalg.norm(y)
        assert float(y.dot(tan)) / eps == pytest.approx(-1.0, abs=1e-3)


def test_the_shift_removes_the_neutral_direction():
    """The same measurement for the shifted map used by the estimator."""
    e = V.CANONICAL_WHITENED_SIMPLEX
    t = np.einsum("ni,nj,nk->ijk", e, e, e)
    d = e[0] / np.linalg.norm(e[0])
    tan = np.array([1.0, -1.0, 0.0])
    tan -= tan.dot(d) * d
    tan /= np.linalg.norm(tan)
    for eps in (1e-4, 1e-5, 1e-6):
        x = math.cos(eps) * d + math.sin(eps) * tan
        y = V._shifted_step(t, x)
        y /= np.linalg.norm(y)
        assert abs(float(y.dot(tan)) / eps) < 0.05


def test_extract_directions_finds_the_canonical_frame():
    e = V.CANONICAL_WHITENED_SIMPLEX
    t = np.einsum("ni,nj,nk->ijk", e, e, e)
    dirs = V.extract_directions(t, seed=301)
    assert dirs.shape == (4, 3)
    want = e / np.linalg.norm(e, axis=1, keepdims=True)
    for w in want:
        assert max(float(d.dot(w)) for d in dirs) > 1.0 - 1e-8


def test_extract_directions_refuses_a_tensor_that_is_not_a_frame():
    """A rank-one symmetric tensor has one maximum, not four."""
    x = np.array([1.0, 0.0, 0.0])
    t = np.einsum("i,j,k->ijk", x, x, x)
    with pytest.raises(V.EstimatorFailure):
        V.extract_directions(t, seed=302)


# --- reproduction: recovery and how it scales ---------------------------

def test_recovers_the_reference_tetrahedron():
    pts = V.sample_uniform(REF, 100_000, seed=401)
    est = V.estimate_vertices(pts, seed=401)
    err = V.vertex_match_error(est.vertices, REF)
    assert err["relative_max_error"] < 0.02, err
    assert est.third_moment_signal == pytest.approx(1.0, abs=0.05)
    assert est.closure_residual < 0.05
    assert est.evidence_class == "SYNTHETIC_RESULT"


def test_recovers_a_regular_tetrahedron():
    pts = V.sample_uniform(REGULAR, 100_000, seed=402)
    est = V.estimate_vertices(pts, seed=402)
    assert V.vertex_match_error(est.vertices, REGULAR)[
        "relative_max_error"] < 0.03


def test_estimate_is_reproducible():
    pts = V.sample_uniform(REF, 20_000, seed=403)
    a = V.estimate_vertices(pts, seed=9)
    b = V.estimate_vertices(pts, seed=9)
    assert np.allclose(a.vertices, b.vertices)


def test_accuracy_improves_with_sample_size():
    rows = V.recovery_vs_n(sizes=(1_000, 100_000), trials=5, seed=404)
    small, large = rows[0], rows[1]
    assert small["failures"] == 0 and large["failures"] == 0
    assert large["median_relative_error"] < small["median_relative_error"] / 3


def test_the_regime_where_it_fails_is_reported_not_hidden():
    """Very small clouds are where the method stops working. The point
    of the test is that the number is bad and gets recorded."""
    rows = V.recovery_vs_n(sizes=(60,), trials=7, seed=405)
    row = rows[0]
    bad = row["failures"] > 0 or row["median_relative_error"] > 0.10
    assert bad, row


def test_flat_cloud_is_refused():
    pts = V.sample_uniform(REF, 5_000, seed=406)
    pts[:, 2] = 0.0
    with pytest.raises(V.EstimatorFailure):
        V.estimate_vertices(pts, seed=406)


# --- the generalisation gap: non-uniform density ------------------------

def test_scale_bias_formula_matches_simulation():
    for alpha in (0.5, 1.5, 2.0, 4.0):
        pts = V.sample_dirichlet(REF, 100_000, alpha=alpha, seed=501)
        est = V.estimate_vertices(pts, seed=501)
        ratio = V.tetrahedron_scale(est.vertices) / V.tetrahedron_scale(REF)
        assert ratio == pytest.approx(V.dirichlet_scale_bias(alpha), rel=0.03)


def test_uniform_is_the_only_unbiased_case():
    assert V.dirichlet_scale_bias(1.0) == pytest.approx(1.0)
    assert V.dirichlet_scale_bias(2.0) < 0.99
    assert V.dirichlet_scale_bias(0.5) > 1.01


def test_non_uniform_bias_does_not_shrink_with_more_data():
    """The single most important test in this module.

    Under a biased density the error is a bias, not noise. If a future
    change made the error fall off like 1/sqrt(N) here, that would mean
    the estimator had silently started assuming its way out of the
    problem, and this test would catch it.
    """
    errs = []
    for n in (10_000, 100_000, 1_000_000):
        pts = V.sample_dirichlet(REF, n, alpha=2.0, seed=502)
        est = V.estimate_vertices(pts, seed=502)
        errs.append(V.vertex_match_error(est.vertices, REF)
                    ["relative_max_error"])
    assert min(errs) > 0.20, errs
    assert max(errs) - min(errs) < 0.05, errs
    assert errs[-1] > errs[0] / 1.5, errs


def test_the_bias_carries_no_warning_in_the_diagnostics():
    """A healthy-looking signal on data the estimator gets badly wrong."""
    pts = V.sample_dirichlet(REF, 100_000, alpha=2.0, seed=503)
    est = V.estimate_vertices(pts, seed=503)
    assert est.third_moment_signal > 0.7
    assert est.closure_residual < 0.05
    assert V.vertex_match_error(est.vertices, REF)[
        "relative_max_error"] > 0.20


def test_density_piled_against_a_face_breaks_the_estimator():
    row = V.degradation_face_weighted(n=100_000, seed=504)
    assert row["refused"] or row["relative_max_error"] > 0.2, row


# --- the generalisation gap: shell-constrained observations -------------

def test_every_shell_inside_the_insphere_is_refused():
    for row in V.degradation_shell(n=50_000, seed=601):
        assert row["refused"], row


def test_shell_data_has_no_third_moment_signal():
    pts = V.sample_shell(REF, 100_000, inner_frac=0.85, outer_frac=0.9,
                         seed=602)
    m = V.empirical_moments(pts)
    wh, _ = V.whitening(m.scatter)
    t_w = np.einsum("ijk,ia,jb,kc->abc", m.third, wh, wh, wh)
    signal = float(np.linalg.norm(t_w)) / math.sqrt(
        float(V.CANONICAL_THIRD_NORM_SQ))
    assert signal < 0.05, signal


def test_shell_samples_stay_inside_the_tetrahedron():
    pts = V.sample_shell(REF, 5_000, outer_frac=0.9, seed=603)
    assert (V.barycentric(pts, REF) >= -1e-12).all()


def test_a_shell_cut_by_the_faces_is_still_not_recovered():
    """Identifiable in principle, and this estimator still cannot do it.
    Distinguishing the two kinds of failure is the point."""
    for row in V.degradation_clipped_shell(n=30_000, seed=604):
        assert row["identifiable_in_principle"]
        assert row["refused"] or row["relative_max_error"] > 0.15, row


# --- the generalisation gap: a moving target ----------------------------

def test_rotation_degrades_then_defeats_the_estimator():
    rows = {r["total_angle_rad"]: r
            for r in V.degradation_rotating(n=50_000, seed=701)}
    still = rows[0.0]
    assert not still["refused"]
    assert still["relative_max_error"] < 0.02

    small = rows[math.pi / 8]
    assert not small["refused"], "a small rotation should pass unnoticed"
    assert small["relative_max_error"] > 0.05, small

    for big in (math.pi / 2, math.pi, 2 * math.pi):
        r = rows[big]
        assert r["refused"] or r["relative_max_error"] > 0.3, r


def test_a_small_rotation_is_the_dangerous_case():
    """Large errors with no diagnostic complaint."""
    pts = V.sample_rotating(REF, 100_000, total_angle=math.pi / 8, seed=702)
    est = V.estimate_vertices(pts, seed=702)
    assert est.third_moment_signal > 0.7
    assert V.vertex_match_error(est.vertices, REF)[
        "relative_max_error"] > 0.05


def test_translation_inflates_the_recovered_solid():
    rows = {r["drift_fraction_of_scale"]: r
            for r in V.degradation_drifting(n=50_000, seed=703)}
    assert not rows[0.0]["refused"]
    assert rows[0.0]["relative_max_error"] < 0.02
    big = rows[1.0]
    assert not big["refused"], "drift is not detected, which is the point"
    assert big["relative_max_error"] > 0.5, big
    assert big["volume_ratio"] > 1.2, big
    assert big["third_moment_signal"] > 0.5, big


def test_rotation_is_a_real_rotation():
    """Guard the forward model: a rotating target must move."""
    still = V.sample_rotating(REF, 2_000, total_angle=0.0, seed=704)
    turned = V.sample_rotating(REF, 2_000, total_angle=math.pi, seed=704)
    assert not np.allclose(still, turned)
    assert np.allclose(still, V.sample_uniform(REF, 2_000, seed=704))


# --- identifiability ----------------------------------------------------

def test_second_moment_twin_matches_mean_covariance_and_volume():
    twin = V.second_moment_twin(REF, seed=801)
    s_ref, _ = _true_moments(REF)
    s_twin, _ = _true_moments(twin)
    assert np.allclose(twin.mean(axis=0), REF.mean(axis=0), atol=1e-10)
    assert np.allclose(s_twin, s_ref, atol=1e-9)
    assert V.tetrahedron_volume(twin) == pytest.approx(
        V.tetrahedron_volume(REF), rel=1e-9)


def test_second_moment_twin_is_a_different_shape():
    """If it were the same shape, the ambiguity would be cosmetic."""
    twin = V.second_moment_twin(REF, seed=801)

    def edges(v):
        return np.sort([np.linalg.norm(v[i] - v[j])
                        for i in range(4) for j in range(i)])

    assert np.max(np.abs(edges(twin) - edges(REF))) > 0.1


def test_second_moment_twin_of_a_regular_tetrahedron_is_rigid():
    """The documented exception: isotropic scatter has no shape twin."""
    twin = V.second_moment_twin(REGULAR, seed=802)

    def edges(v):
        return np.sort([np.linalg.norm(v[i] - v[j])
                        for i in range(4) for j in range(i)])

    assert np.allclose(edges(twin), edges(REGULAR), atol=1e-9)


def test_third_moment_separates_what_the_second_cannot():
    """The twin is invisible to moments 1-2 and visible to moment 3."""
    twin = V.second_moment_twin(REF, seed=801)
    _, t_ref = _true_moments(REF)
    _, t_twin = _true_moments(twin)
    assert np.abs(t_twin - t_ref).max() > 0.1 * np.abs(t_ref).max()


def test_circumscribing_tetrahedron_has_the_requested_insphere():
    rng = np.random.default_rng(803)
    checked = 0
    while checked < 8:
        n = rng.normal(size=(4, 3))
        n /= np.linalg.norm(n, axis=1, keepdims=True)
        # only positively-spanning normal sets bound a solid
        if np.linalg.matrix_rank(n) < 3:
            continue
        try:
            t = V.circumscribing_tetrahedron(n, np.zeros(3), 1.0)
        except ValueError:
            continue
        centre, radius = V.insphere(t)
        if radius < 1e-6:
            continue
        if not np.isclose(radius, 1.0, rtol=1e-6):
            continue        # normals did not positively span; unbounded
        assert np.allclose(centre, 0.0, atol=1e-6)
        checked += 1


def test_two_tetrahedra_share_an_insphere_exactly():
    ex = V.shell_nonidentifiability_example(radius=1.0)
    for key in ("insphere_a", "insphere_b"):
        assert ex[key]["radius"] == pytest.approx(1.0, rel=1e-9)
        assert np.allclose(ex[key]["centre"], 0.0, atol=1e-9)


def test_the_two_tetrahedra_are_grossly_different():
    ex = V.shell_nonidentifiability_example(radius=1.0)
    a, b = np.array(ex["tetrahedron_a"]), np.array(ex["tetrahedron_b"])
    assert ex["volume_ratio"] > 1.2 or ex["volume_ratio"] < 0.8

    def edges(v):
        return np.sort([np.linalg.norm(v[i] - v[j])
                        for i in range(4) for j in range(i)])

    assert np.max(np.abs(edges(a) - edges(b))) > 1.0
    assert ex["equivalence_class_dimension"] == 8


def test_shell_observations_of_the_two_are_literally_identical():
    """The strongest form of the non-identifiability result.

    Stronger than "statistically indistinguishable": the same seed
    produces the same points to 1e-9, because the sampling
    distribution is a function of the shared insphere and of nothing
    else. No estimator can separate inputs it cannot distinguish.

    Not *bit*-identical, and the distinction is worth keeping. The two
    inspheres are computed by a numerical solve and agree to ~1e-15
    rather than exactly, so the sample arrays differ in the last bits.
    That is floating-point in the construction, not information about
    the tetrahedra -- but "identical to 1e-9" is what was measured and
    is what this claims.
    """
    ex = V.shell_nonidentifiability_example(radius=1.0)
    a, b = np.array(ex["tetrahedron_a"]), np.array(ex["tetrahedron_b"])
    pa = V.sample_shell(a, 5_000, inner_frac=0.8, outer_frac=0.95, seed=804)
    pb = V.sample_shell(b, 5_000, inner_frac=0.8, outer_frac=0.95, seed=804)
    assert np.allclose(pa, pb, atol=1e-9)
    # and the same seed on genuinely different geometry does differ,
    # so the assertion above is not vacuous
    pc = V.sample_shell(REF, 5_000, inner_frac=0.8, outer_frac=0.95, seed=804)
    assert not np.allclose(pa, pc)


def test_identifiability_report_states_the_impossible_cases():
    r = V.identifiability_report()
    assert r["identified_by_moments_1_and_2"] is False
    assert r["second_moment_deficiency"]["constraints"] == 6
    assert r["second_moment_deficiency"]["degrees_of_freedom"] == 9
    assert set(r["not_identified_at_all"]) == {
        "shell_or_sphere_confined",
        "unknown_non_uniform_density",
        "target_moving_by_an_unknown_law"}


# --- model class --------------------------------------------------------

def test_estimator_rejects_solids_that_are_not_tetrahedra():
    probe = V.model_class_probe(n=100_000, seed=901)
    assert probe["tetrahedron_uniform"]["refused"] is False
    for name in ("square_pyramid", "box", "gaussian"):
        assert probe[name]["refused"] is True, probe[name]


def test_model_class_probe_does_not_overclaim():
    probe = V.model_class_probe(n=20_000, seed=902)
    assert "not an exhaustive model space" in probe["what_this_does_not_say"]


# --- refusals -----------------------------------------------------------

def test_earth_sphere_inverse_is_refused_whatever_it_is_given():
    for args in ((), (np.zeros((10, 3)),), ("please",)):
        with pytest.raises(V.InverseClaimRefused):
            V.refuse_earth_sphere_inverse(*args)


def test_the_earth_sphere_refusal_names_every_reason():
    with pytest.raises(V.InverseClaimRefused) as exc:
        V.refuse_earth_sphere_inverse()
    msg = str(exc.value)
    for token in ("SAMPLING", "SUPPORT", "MOTION", "MODEL CLASS",
                  "EVIDENCE CLASS", "LITERATURE_REPRODUCTION"):
        assert token in msg
    assert "not proof that the hidden object is tetrahedral" in msg


def test_shell_inverse_is_refused():
    with pytest.raises(V.NotIdentifiable) as exc:
        V.refuse_shell_inverse()
    assert "8-parameter" in str(exc.value)


def test_tetrahedral_object_claim_is_refused():
    with pytest.raises(V.InverseClaimRefused):
        V.refuse_tetrahedral_object_claim()


# --- the report ---------------------------------------------------------

def test_report_classes_the_reproduction_correctly():
    r = V.inverse_report(seed=1001)
    assert r["reproduction"]["evidence_class"] == "LITERATURE_REPRODUCTION"
    assert r["reproduction"]["relative_max_error"] < 0.02
    assert r["measured_here"] == "nothing"


def test_report_does_not_claim_a_measurement():
    r = V.inverse_report(seed=1002)
    blob = repr(r)
    for forbidden in ("BENCH_MEASUREMENT", "INDEPENDENT_REPLICATION",
                      "PROSPECTIVE_PREDICTION"):
        assert forbidden not in blob


def test_report_carries_the_disclaimer():
    r = V.inverse_report(seed=1003)
    assert "hidden object is a tetrahedron" in r["what_this_does_not_say"]


def test_prior_art_is_now_verified_against_the_supplied_paper():
    """R10.2: the 2018 paper arrived with the private corpus, so the
    Q19 'could not verify' caveat is closed. The reproduction stays a
    reproduction; only the citation's status changed."""
    r = V.inverse_report(seed=1003)
    assert r["prior_art"]["verified"] is True
    assert r["prior_art"]["doi"] == "10.1007/s10231-017-0688-6"
    assert "reproduction is a reproduction" in r["prior_art"]["note"]


def test_degradation_report_admits_the_undetected_failures():
    r = V.degradation_report(n=20_000, seed=1004)
    assert r["non_uniform_density_symmetric"][
        "caught_by_a_diagnostic"] is False
    assert r["translating_target"]["caught_by_a_diagnostic"] is False
    assert r["shell_confined"]["caught_by_a_diagnostic"] is True
    assert "not evidence that the assumptions hold" in \
        r["what_this_does_not_say"]


def test_module_is_exported():
    import r10
    assert "inverse" in r10.__all__
