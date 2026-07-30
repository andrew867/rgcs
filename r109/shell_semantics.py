"""R10.9 shell integration (Phase 6, R109-SHL-01..03).

Source-confirmed semantics, typed and firewalled:

    shell 3 = finite crustal/surface band (variable-depth topography)
    shell 7 = orbital object class
    shell thickness = body-specific
    surface topography = variable depth WITHIN shell 3

The decimal terminal marker, the binary S3 field, the physical shell
semantics, and epoch/phase closure remain FOUR distinct reported
facts; :func:`shell_marker_report` returns all four and
:func:`refuse_marker_collapse` blocks any claim that the decimal
marker *is* the binary S3 bits (no transform receipt exists yet).

The outer-in shell-fraction equation of ``cwatlas.r1085a`` remains the
provisional production radial model (versioned, not silently trusted).
"""

from __future__ import annotations

from dataclasses import dataclass

from cwatlas.r1085a.shell_profile import (
    CANDIDATE_PROFILES,
    OPERATIONAL_SHELLS,
    ShellProfile,
    profile,
)

from r109.types import (
    CodecTypeError,
    DecimalTerminalMarker,
    SHELL3_CRUSTAL_BAND,
    SHELL7_ORBIT_CLASS,
    WireAddress,
)

PROVISIONAL_RADIAL_MODEL = "cwatlas.r1085a.outer_in_radial (OUTER_IN_GRAVITY_FIELD_LINE) — provisional, versioned"


@dataclass(frozen=True)
class CrustalBandProfile:
    """Shell 3 as a finite band with declared topographic depth range.

    Bounds are DECLARED engineering values (conventional Earth
    topography span), never fitted from source vectors; other bodies
    get their own declared profiles when resolved.
    """

    body: str
    band_floor_km: float       # depth of deepest surface (relative land-zero)
    band_ceiling_km: float     # height of highest surface
    provenance: str
    evidence_class: str

    def __post_init__(self) -> None:
        if self.band_floor_km >= self.band_ceiling_km:
            raise CodecTypeError(
                "crustal band floor must be below its ceiling")

    def contains_depth(self, depth_km: float) -> bool:
        """Sea floor, land, and mountains all live inside the band."""
        return self.band_floor_km <= depth_km <= self.band_ceiling_km

    def thickness_km(self) -> float:
        return self.band_ceiling_km - self.band_floor_km


TERRA_CRUSTAL_BAND = CrustalBandProfile(
    body="Terra (16-5, source-reported)",
    band_floor_km=-11.0,   # ~deepest ocean trench, conventional value
    band_ceiling_km=9.0,   # ~highest summit, conventional value
    provenance="conventional Earth topography span; DECLARED bounds, "
               "not fitted from any source vector",
    evidence_class="OPERATOR_NOTE",
)

LUNA_CRUSTAL_BAND = CrustalBandProfile(
    body="Luna (16-7, source-reported)",
    band_floor_km=-9.1,    # ~deepest basin floor, conventional value
    band_ceiling_km=10.8,  # ~highest highland, conventional value
    provenance="conventional lunar topography span; DECLARED bounds, "
               "not fitted; body-specific thickness differs from Terra "
               "(R109-SHL-01)",
    evidence_class="OPERATOR_NOTE",
)

_BANDS = {"terra": TERRA_CRUSTAL_BAND, "luna": LUNA_CRUSTAL_BAND}


def crustal_band(body: str) -> CrustalBandProfile:
    try:
        return _BANDS[body.lower()]
    except KeyError:
        raise CodecTypeError(
            f"no declared crustal band for body {body!r}; declare one, "
            f"never fit one from source vectors") from None


@dataclass(frozen=True)
class OrbitClass:
    """Shell 7 as an object class, not a band with surface topography."""

    shell_id: int = 7
    semantic: str = SHELL7_ORBIT_CLASS.semantic
    evidence_class: str = "SOURCE_REPORTED"

    def classify(self, extracted_shell: int) -> bool:
        return extracted_shell == self.shell_id


def shell_marker_report(wire: WireAddress, extracted_s3: int) -> dict:
    """All four shell-adjacent facts, reported side by side, never
    collapsed (shell-marker firewall)."""
    return {
        "decimal_terminal_marker": {
            "digit": wire.decimal_terminal_marker.digit,
            "source_reported_meaning":
                wire.decimal_terminal_marker.source_reported_meaning,
            "evidence_class": "SOURCE_REPORTED",
        },
        "binary_s3_field": {
            "value": extracted_s3,
            "evidence_class": "EXACT_ARITHMETIC",
        },
        "physical_shell_semantics": {
            "shell3": SHELL3_CRUSTAL_BAND.semantic,
            "shell7": SHELL7_ORBIT_CLASS.semantic,
            "evidence_class": "SOURCE_REPORTED",
        },
        "epoch_phase_closure": {
            "status": "UNRESOLVED",
        },
        "marker_equals_s3_proved": False,
        "note": "decimal terminal marker and binary S3 remain distinct "
                "until an exact transform receipt proves their "
                "relationship (R109-SHL-02)",
    }


def refuse_marker_collapse(*_a, **_k) -> None:
    raise CodecTypeError(
        "refused: the decimal terminal marker is not proved identical "
        "to the binary S3 field; no transform receipt exists "
        "(R109-SHL-02). Report both; collapse neither.")


def outer_in_inner_out_agreement(profile_id: str,
                                 epoch_year: float = 2025.0) -> dict:
    """Under a declared profile, outer-in and inner-out bookkeeping must
    describe the same stack (provisional-model consistency check)."""
    p: ShellProfile = profile(profile_id)
    rows = {}
    total = p.stack_height_km(epoch_year)
    for sid in OPERATIONAL_SHELLS:
        above = p.outer_stack_above_km(sid, epoch_year)
        below = p.inner_stack_below_km(sid, epoch_year)
        own = p.band(sid).thickness_km(epoch_year)
        rows[sid] = {
            "outer_in_km_above": above,
            "inner_out_km_below": below,
            "own_km": own,
            "closes": abs((above + below + own) - total) < 1e-9,
        }
    return {"profile": profile_id, "stack_km": total, "shells": rows,
            "all_close": all(r["closes"] for r in rows.values()),
            "radial_model": PROVISIONAL_RADIAL_MODEL}


def candidate_profile_ids() -> list[str]:
    return [p.profile_id for p in CANDIDATE_PROFILES]
