"""R10.59 -- FrameManifest and AddressCertificate emitters.

WHY THIS EXISTS
---------------
The NAIF/SPICE frame tutorial makes a separation RGCS had been eliding:

  * a REFERENCE FRAME is an ordered triple of orthogonal unit vectors,
    and it has a CENTER;
  * a COORDINATE SYSTEM is the mechanism for locating points within
    that frame;
  * state and pointing data require BOTH, plus an epoch when the frame
    is time-dependent.

A bare ``lat, lon`` pair carries none of that. It is the last projection
stage, not the object. So this module emits typed certificates instead
of naked coordinates: every projected point travels with the frame it
was projected in, the epoch gating that applies, the claim class, and
the blockers that bear on it.

Nothing here re-tunes the projector or adds an anchor. It is a
presentation layer over :mod:`r1053.projector` and :mod:`r1053.ledger`.
"""

from __future__ import annotations

from r1053 import kernel, ledger, lock, projector, residuals

#: Earth root D_V1. The frame is DECLARED, not derived here -- naming a
#: frame is what lets a receipt be checked against a different one.
EARTH_ROOT_D_V1 = {
    "frame_id": "RGCS_EARTH_ROOT_D_V1",
    "center": "EARTH_CENTRE_OF_MASS",
    "primary_axis": "MEAN_ROTATION_AXIS",
    "display_convention": "SOUTH_UP",
    "display_note": "viewed externally above Antarctica, positive "
                    "rotation is clockwise",
    "fixed_angular_root": "WILKES_LAND_GRAVITY_ANOMALY_CENTROID_CANDIDATE",
    "dynamic_phase_hand": "SOUTH_ATLANTIC_ANOMALY_FIELD_MINIMUM",
    "phase_hand_requires": ["epoch", "shell"],
    "surface": "SHELL_PLUS_EPOCH",
    "level3_datum": "MEAN_SEA_LEVEL",
    "status": "V1_CANDIDATE_NOT_VALIDATED",
}

#: What the epoch layer does and does not gate.
EPOCH_GATING = {
    "structural_decode": "EPOCH_OPTIONAL",
    "dynamic_projection": "EPOCH_REQUIRED",
    "public_receipt": "EPOCH_METADATA_REQUIRED",
    "requires_epoch": (
        "moving body frames", "SAA magnetic phase hand",
        "epoch-dependent shell radius", "barycentric or interstellar "
        "coordinates", "proper motion and ephemeris reconciliation",
        "reproducible public certificates"),
    "long_origin_candidate": "Ba-130",
    "conventional_metadata_layer": "UTC/TAI",
    "downstream_fine_phase_only": "Cs-133",
    "note": "the V1 spatial parse does not need a solved calendar; the "
            "epoch layer is gated, not removed",
}


def frame_manifest() -> dict:
    """The frame a certificate is expressed in, stated explicitly."""
    return {
        "schema": "rgcs.r1059.frame-manifest.v1",
        "frame": dict(EARTH_ROOT_D_V1),
        "coordinate_system": {
            "native": "hierarchical recursive cell address",
            "final_projection": "geodetic latitude/longitude, degrees",
            "projection_is_terminal": True,
            "note": "lat/lon is the LAST stage, not the object; the "
                    "native RGCS object is body + frame + epoch + root "
                    "+ ordered path + shell/state + local coordinate + "
                    "uncertainty",
        },
        "epoch": dict(EPOCH_GATING),
        "projector": {
            "law": "lat/lon = normalize(A u)",
            "split_t": kernel.SPLIT_T,
            "split_t_exact": "10/19",
            "face_map": "source_face = (F5 + 14) % 20",
            "pinning": projector.V1_PINNING,
            "free_parameters": projector.FREE_PARAMETERS,
            "anchors": len(projector.FIT_ANCHORS),
            "constraints": len(projector.FIT_ANCHORS)
            * projector.CONSTRAINTS_PER_ANCHOR,
            "over_determined": False,
            "anchors_needed_to_overdetermine":
                projector.ANCHORS_NEEDED_TO_OVERDETERMINE,
        },
    }


def _claim_class(word: str) -> list:
    if word in ledger.FIT_ANCHORS:
        return ["EXACT_ARITHMETIC", "TRAINING_EQUALITY",
                "NOT_EVIDENCE_FITS_THE_MAP"]
    return ["STRUCTURAL_PARSE_EXACT", "PROJECTION_UNDERDETERMINED",
            "CANDIDATE_NOT_LOCATED_TARGET"]


def _blockers_for(word: str) -> list:
    out = ["V1-B01", "V1-B02"]
    if word in ledger.FIT_ANCHORS:
        out.append("V1-B02")
    if kernel.branch(word) == "117" and word == "165879243":
        out.append("V1-B03")
    if word == "165879243":
        out += ["V1-B04", "V1-B06"]
    out.append("V1-B05")
    return sorted(set(out))


def address_certificate(word) -> dict:
    """A typed receipt for one direct word. Never a naked coordinate."""
    w = str(word).strip()
    v = kernel.assert_direct_lane(w)
    f5, q22, s3 = kernel.fields(v)
    known = ledger.FIT_ANCHORS.get(w) or ledger.V1_PROJECTED.get(w)
    plat, plon = projector.project(v)
    cert = {
        "schema": "rgcs.r1059.address-certificate.v1",
        "wire": {"decimal": w, "width_bits": kernel.WORD_BITS,
                 "binary30": format(v, "030b"),
                 "octal10": kernel.octal10(v),
                 "branch_octal": kernel.branch(v),
                 "lane": "DIRECT_30BIT",
                 "decimal_header_table_applies":
                     kernel.decimal_header_table_applies(v)},
        "fields": {"F5": f5, "Q22": q22, "S3_m3": s3,
                   "S3_is_check_digit_not_geometry": True,
                   "source_face": kernel.source_face(v),
                   "q22_path": kernel.q22_symbols(q22)},
        "frame": frame_manifest(),
        "projection": {
            "v1_pinned_lat": plat, "v1_pinned_lon": plon,
            "pinning": projector.V1_PINNING,
            "is_located_target": False,
            "note": "projector output under one member of a 2-parameter "
                    "family; a different member of the same family fits "
                    "the anchors equally well and places this word "
                    "elsewhere",
        },
        "label": {
            "active": ledger.active_label(w) or (known or {}).get("label", ""),
            "retired": ledger.RETIRED_LABELS.get(w),
            "rule": ledger.LABEL_RULE,
        },
        "claim_class": _claim_class(w),
        "blockers": _blockers_for(w),
        "not_final_physical_validation": True,
    }
    if w in ledger.V1_PROJECTED:
        rec = ledger.V1_PROJECTED[w]
        cert["projection"]["operator_supplied_lat"] = rec["lat"]
        cert["projection"]["operator_supplied_lon"] = rec["lon"]
        cert["projection"]["pinning_gap_km"] = projector.haversine_km(
            plat, plon, rec["lat"], rec["lon"])
    if w in ledger.FIT_ANCHORS:
        rec = ledger.FIT_ANCHORS[w]
        cert["projection"]["anchor_target_lat"] = rec["lat"]
        cert["projection"]["anchor_target_lon"] = rec["lon"]
        cert["projection"]["residual_km"] = projector.haversine_km(
            plat, plon, rec["lat"], rec["lon"])
        cert["projection"]["residual_is_evidence"] = False
    if w == "165879243":
        cert["residuals"] = residuals.drummondville_report()["rows"]
    return cert


def envelope_rejection(record) -> dict:
    """The receipt a gated wide-envelope record gets. A refusal is data."""
    s = str(record).strip()
    bits = int(s).bit_length()
    return {
        "schema": "rgcs.r1059.envelope-rejection.v1",
        "record": s, "digits": len(s), "bits": bits,
        "direct_lane_max_bits": kernel.WORD_BITS,
        "admitted": False,
        "reason": "exceeds the 30-bit direct word; wide-envelope records "
                  "require a transport bridge",
        "bridge_status": "REFUTED_AS_GENERAL_TRANSPORT_BRIDGE",
        "blocker": "V1-B07",
        "never_truncated": True,
        "note": "the record is REFUSED, not silently truncated to 30 "
                "bits; truncation would manufacture a false address",
    }


def receipt_bundle() -> dict:
    """Every V1 receipt in one object, for export and for the manual."""
    words = list(ledger.FIT_ANCHORS) + list(ledger.V1_PROJECTED)
    return {
        "schema": "rgcs.r1059.receipt-bundle.v1",
        "frame": frame_manifest(),
        "certificates": [address_certificate(w) for w in words],
        "envelope_rejections": [envelope_rejection(r)
                                for r in ledger.GATED_WIDE_ENVELOPE],
        "verdicts": list(lock.VERDICTS),
        "blockers": lock.BLOCKERS,
        "claim_boundary": CLAIM_BOUNDARY,
    }


#: The exact public phrasing required by R10.59. Verbatim.
CLAIM_BOUNDARY = (
    "RGCS V1 is a coordinate/research workbench with a candidate "
    "Earth-root projection. It can parse and emit structured vector "
    "receipts, reproduce the V1 calibration artifacts, and classify "
    "residuals under declared cell-scale and operational-envelope "
    "hypotheses. It does not prove physical craft, alien sources, "
    "crop-circle authorship, Phryll propulsion, or metric engineering.")
