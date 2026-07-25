"""P28 — live impedance / BVD fitting: streaming convergence, outliers, blocking."""

from __future__ import annotations

import numpy as np
import pytest

from r15 import live_bvd as L


def test_streaming_fit_converges_to_planted_bvd():
    stream = L.SyntheticImpedanceStream(seed=7)
    planted = stream.planted()
    fitter = L.LiveBVDFitter(min_points=128, refit_interval=64).run(stream)
    res = fitter.result()          # raises unless converged
    est = res["estimate"]
    fs_fit = est.get("f_s_hz", est.get("f_s"))
    fs_true = planted.get("f_s_hz", planted.get("f_s"))
    assert fs_fit == pytest.approx(fs_true, rel=1e-2)


def test_hampel_mask_flags_an_injected_outlier():
    vals = np.ones(64)
    vals[32] = 1e6
    mask = L.hampel_mask(vals, window=7, k=6.0)
    # mask marks inliers True; the injected spike is rejected (False)
    assert not bool(mask[32])
    assert bool(mask[0])


def test_unconverged_stream_is_not_a_result():
    fitter = L.LiveBVDFitter(min_points=256, refit_interval=256)
    fitter.push(1.0e6, 50 + 0j)
    with pytest.raises(L.NotConvergedError):
        fitter.result()


def test_real_stream_acquires_nothing():
    real = L.RealImpedanceStream()
    rec = real.blocked_receipt()
    assert rec["status"] == "BLOCKED"
    assert rec["acquired"] is False
    with pytest.raises(L.NoLiveHardwareError):
        list(real.samples())


def test_report_claims_nothing_measured():
    r = L.live_bvd_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
