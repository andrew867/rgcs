"""P23b — tomographic reconstruction: full-angle recovery is the
correctness test, and few coplanar angles underdetermine the field."""

from __future__ import annotations

import numpy as np
import pytest

from r13 import imaging as IM


FULL = np.linspace(0.0, 180.0, 90, endpoint=False)
FEW = np.linspace(0.0, 180.0, 6, endpoint=False)


def test_forward_project_shape():
    ph = IM.centered_disk_phantom(48)
    sino = IM.forward_project(ph, FULL)
    assert sino.shape == (FULL.size, 48)


def test_phantom_recovered_from_full_angle_sinogram():
    # POWER: the forward/inverse round trip recovers a simple phantom.
    ph = IM.two_disk_phantom(48)
    recon = IM.reconstruct(IM.forward_project(ph, FULL), FULL, image_size=48)
    err = IM.reconstruction_error(recon, ph)
    assert err < 0.15


def test_six_angle_reconstruction_is_much_worse_than_full():
    # Load-bearing: few coplanar views are streaky and underdetermined.
    ph = IM.two_disk_phantom(48)
    err_full = IM.reconstruction_error(
        IM.reconstruct(IM.forward_project(ph, FULL), FULL, image_size=48), ph)
    err_few = IM.reconstruction_error(
        IM.reconstruct(IM.forward_project(ph, FEW), FEW, image_size=48), ph)
    assert err_few > err_full
    assert err_few > 2.0 * err_full


def test_reconstruction_error_rises_as_angles_drop():
    ph = IM.two_disk_phantom(48)
    rows = IM.error_vs_angles(ph, [6, 12, 30, 90])
    errs = [r["error"] for r in rows]
    # fewest angles is worst; most angles is best
    assert errs[0] == max(errs)
    assert errs[-1] == min(errs)


def test_psf_broadens_as_angles_decrease():
    pt = IM.point_phantom(48)
    psf_full = IM.psf_width(
        IM.reconstruct(IM.forward_project(pt, FULL), FULL, image_size=48))
    psf_few = IM.psf_width(
        IM.reconstruct(IM.forward_project(pt, FEW), FEW, image_size=48))
    assert psf_few > psf_full


def test_refuse_reconstruction_as_measured_raises():
    with pytest.raises(IM.ImagingError):
        IM.refuse_reconstruction_as_measured()


def test_refuse_fewangle_as_complete_raises():
    with pytest.raises(IM.ImagingError):
        IM.refuse_fewangle_as_complete(6)


def test_report_verdict_and_measured_nothing():
    r = IM.imaging_report()
    assert r["verdict"] == "IMAGING_RECONSTRUCTION_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "NUMERICAL_SIMULATION"
    assert r["few_angle_is_worse"] is True
    assert r["psf_broadens_with_fewer_angles"] is True
