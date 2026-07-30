"""R10.8.5A §6 — OuterInRadialDecoder: outermost boundary inward.

The radial calculation begins at the **outer operational boundary**
(the outer edge of shell 8) and proceeds inward along a gravity-field
line. It does not begin at Earth's geometric centre: the physical core
may be offset relative to the magnetic structure and the ellipsoidal
figure, so the outer-shell geometry is the preferred reference
authority, and the production path here simply never references the
centre as an origin.

For shell ``s`` with epoch thickness ``Delta_s(t)`` and shell fraction
``zeta_s`` (0 at the inner boundary, 1 at the outer boundary, Z
increasing inner -> outer):

    D_in    = sum_{k > s} Delta_k(t)  +  (1 - zeta_s) * Delta_s(t)
    D_local = zeta_s * Delta_s(t)

Both must resolve to the same physical point; the invariant check is
computed on every decode, not sampled.

The shell fraction convention is itself a declared two-member family:
``ZETA_FROM_OCTREE_Z_V1`` reads ``zeta = (Z + 1/2) / 2**9`` from the
packet's 9 octree Z bits (Z increases inner -> outer, matching the
locked semantics); ``ZETA_MIDBAND_V1`` is the agnostic mid-band
``zeta = 1/2``. Both are run; neither is fitted.
"""

from __future__ import annotations

from dataclasses import dataclass

from cwatlas.claims import ClaimError
from cwatlas.r1085a.shell_profile import OPERATIONAL_SHELLS, ShellProfile

#: The production radial mode string; receipts assert it verbatim.
PRODUCTION_RADIAL_MODE = "OUTER_IN_GRAVITY_FIELD_LINE"

ZETA_CONVENTIONS = ("ZETA_FROM_OCTREE_Z_V1", "ZETA_MIDBAND_V1")
OCTREE_Z_BITS = 9
OCTREE_Z_CELLS = 2 ** OCTREE_Z_BITS         # 512


def zeta_from_octree_z(z_index: int) -> float:
    """zeta = (Z + 1/2) / 512 — cell-centre fraction, inner -> outer."""
    if not isinstance(z_index, int) or isinstance(z_index, bool):
        raise ClaimError("octree Z index must be a plain int")
    if not 0 <= z_index < OCTREE_Z_CELLS:
        raise ClaimError(
            f"octree Z index {z_index} outside 0..{OCTREE_Z_CELLS - 1}")
    return (z_index + 0.5) / OCTREE_Z_CELLS


def zeta_under(convention: str, z_index: int | None) -> float:
    if convention == "ZETA_FROM_OCTREE_Z_V1":
        if z_index is None:
            raise ClaimError("ZETA_FROM_OCTREE_Z_V1 needs the packet's "
                             "octree Z index")
        return zeta_from_octree_z(z_index)
    if convention == "ZETA_MIDBAND_V1":
        return 0.5
    raise ClaimError(
        f"unknown zeta convention {convention!r}; declared: "
        f"{ZETA_CONVENTIONS}")


@dataclass(frozen=True)
class OuterInRadialResult:
    """One outer-in radial decode, with the invariant receipted."""

    shell_id: int
    zeta: float
    epoch_year: float
    profile_id: str
    d_in_km: float                # inward from the outer operational bdry
    d_local_km: float             # outward from shell s's inner boundary
    stack_height_km: float        # land-zero -> outer operational boundary
    height_above_land_zero_km: float
    invariant_residual_km: float
    radial_mode: str = PRODUCTION_RADIAL_MODE


def decode(shell_id: int, zeta: float, profile: ShellProfile,
           epoch_year: float) -> OuterInRadialResult:
    """The locked outer-in decode, with the inner-out cross-check.

    ``height_above_land_zero_km`` is the resolved position expressed as
    distance above the shell-3 inner boundary (the land-zero surface);
    the outer-in and inner-out routes to it must agree exactly.
    """
    if shell_id not in OPERATIONAL_SHELLS:
        raise ClaimError(
            f"shell {shell_id} is not operational; the outer-in stack "
            f"covers shells {OPERATIONAL_SHELLS}. Shells 0..2 lie below "
            f"the land-zero surface and have no declared thickness.")
    if not 0.0 <= zeta <= 1.0:
        raise ClaimError(f"zeta {zeta} outside [0, 1]")
    delta_s = profile.band(shell_id).thickness_km(epoch_year)
    outer_stack = profile.outer_stack_above_km(shell_id, epoch_year)
    inner_stack = profile.inner_stack_below_km(shell_id, epoch_year)
    stack = profile.stack_height_km(epoch_year)

    d_in = outer_stack + (1.0 - zeta) * delta_s
    d_local = zeta * delta_s

    height_outer_in = stack - d_in
    height_inner_out = inner_stack + d_local
    residual = abs(height_outer_in - height_inner_out)
    if residual > 1e-9:
        raise ClaimError(
            f"outer-in / inner-out invariant violated by {residual} km — "
            f"the shell stack arithmetic is inconsistent; refuse the "
            f"decode rather than average the two answers.")
    return OuterInRadialResult(
        shell_id=shell_id, zeta=float(zeta),
        epoch_year=float(epoch_year), profile_id=profile.profile_id,
        d_in_km=d_in, d_local_km=d_local, stack_height_km=stack,
        height_above_land_zero_km=height_inner_out,
        invariant_residual_km=residual)


def refuse_geocentric_spherical_shortcut(*_a, **_k) -> None:
    """The banned shortcut: radius = R_earth + altitude from the centre.

    The production path measures inward from the outer operational
    boundary along a gravity-field line. A core-centred spherical
    radius silently re-anchors the whole stack to the geometric centre
    — the one reference the lock names as untrustworthy.
    """
    raise ClaimError(
        "refused: the core-centred spherical shortcut is not in the "
        "production path. Radial position is decoded outer-in "
        f"({PRODUCTION_RADIAL_MODE}); the geometric centre is not the "
        "reference authority — the outer-shell geometry is.")
