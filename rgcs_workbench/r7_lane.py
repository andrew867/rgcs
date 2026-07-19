"""v5.0 R7 canonical lane.

Like the R6 lane, this is mostly refusals and computed nulls, carried
as first-class rows. Nothing here is bench data: no oscillator pair
has been compared, no crystal aligned or excited, no field mapped, no
force measured.
"""

from __future__ import annotations


def build_r7(store, Record) -> None:
    """Populate the R7 tables on ``store``."""
    from r7 import clocklink as _cl
    from r7 import cw as _cw
    from r7 import gravity as _gv
    from r7 import legacy as _lg

    # ---------------------------------------------------------------
    # P02 — CW vector decoder and its null
    # ---------------------------------------------------------------
    cwrep = _cw.status_report()
    store.add("r7_cw", Record(
        id="R7-CW-PARSE-NULL", kind="parse_null",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r7.cw.status_report",
        fields={
            "claim": cwrep["claim"],
            "status": cwrep["status"],
            "forced_common_bits": cwrep["forced_common_bits"],
            "observed_common_bits": cwrep["observed_common_bits"],
            "informative_bits": cwrep["informative_bits"],
            "header_is_forced_by_span":
                cwrep["header_is_forced_by_span"],
            "null_3x12_p_both": cwrep["null_3x12_p_both"],
            "null_6x6_p_both": cwrep["null_6x6_p_both"],
            "verdict": cwrep["verdict"],
            "ceiling": cwrep["ceiling"]}))

    for i, s in enumerate(_cw.SOURCE_STRINGS):
        v = int(s)
        h, f = _cw.split_fields(v, 2, 12, 3)
        store.add("r7_cw", Record(
            id=f"R7-CW-VECTOR-{i:02d}", kind="source_vector",
            evidence_class="SOURCE_CLAIM",
            provenance="JH corpus CW vector strings",
            fields={
                "source_string": s,
                "value": v,
                "bit_length": v.bit_length(),
                "header_3x12": h,
                "field1_3x12": f[0],
                "field2_3x12": f[1],
                "field3_3x12": f[2],
                "note": ("header and field1 lie inside the 15 leading "
                         "bits forced identical by the interval; only "
                         "fields 2 and 3 carry any variation")}))

    for d in _cw.FROZEN_DECODERS:
        store.add("r7_cw", Record(
            id=f"R7-CW-DECODER-{d.parse}", kind="frozen_decoder",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="r7.cw.FROZEN_DECODERS",
            fields={"parse": d.parse, "header_bits": d.header_bits,
                    "field_bits": d.field_bits,
                    "n_fields": d.n_fields, "digest": d.digest(),
                    "semantics_declared": False,
                    "note": "frozen by digest so future vectors test "
                            "it prospectively; reassignment raises"}))

    # ---------------------------------------------------------------
    # P07 — geometry-to-gravity arithmetic
    # ---------------------------------------------------------------
    gv = _gv.full_assessment()
    for name, row in gv["configurations"].items():
        store.add("r7_gravity", Record(
            id=f"R7-GRAVITY-{name}", kind="gravity_arithmetic",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="r7.gravity.assess",
            fields={
                "configuration": name,
                "total_energy_j": row["total_energy_j"],
                "equivalent_mass_kg": row["equivalent_mass_kg"],
                "predicted_fractional_shift":
                    row["predicted_fractional_shift"],
                "predicted_acceleration_ms2":
                    row["predicted_acceleration_ms2"],
                "clock_gap_decades": row["clock_gap_decades"],
                "acceleration_gap_decades":
                    row["acceleration_gap_decades"],
                "status": row["status"],
                "note": row["note"]}))

    store.add("r7_gravity", Record(
        id="R7-GRAVITY-VERDICT", kind="gravity_verdict",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r7.gravity.full_assessment",
        fields={
            "all_refused": gv["all_refused"],
            "configurations_refused":
                "; ".join(gv["configurations_refused_by_arithmetic"]),
            "reference_1mm_height_shift":
                gv["reference_1mm_height_shift"],
            "ratio_1mm_lift_over_best_apparatus":
                gv["ratio_1mm_lift_over_best_apparatus"],
            "verdict": gv["verdict"],
            "consequence": gv["consequence"],
            "what_this_does_not_say": gv["what_this_does_not_say"]}))

    # ---------------------------------------------------------------
    # P03 — clock link ceiling
    # ---------------------------------------------------------------
    cl = _cl.ceiling_report()
    for osc, by_link in cl["oscillators"].items():
        for link, row in by_link.items():
            store.add("r7_clocklink", Record(
                id=f"R7-CLOCK-{osc}-{link}", kind="height_resolution",
                evidence_class="DERIVED_ARITHMETIC",
                provenance="r7.clocklink.height_resolution",
                fields={
                    "oscillator": osc, "link": link,
                    "target_height_m": row["target_height_m"],
                    "target_fractional": row["target_fractional"],
                    "combined_floor": row["combined_floor"],
                    "limiter": row["limiter"],
                    "resolvable": row["resolvable"],
                    "tau_required_years": row["tau_required_years"],
                    "status": row["status"]}))

    store.add("r7_clocklink", Record(
        id="R7-CLOCK-CEILING", kind="claim_ceiling",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r7.clocklink.ceiling_report",
        fields={
            "consumer_quartz_unresolvable":
                "; ".join(cl["consumer_quartz_unresolvable"]),
            "link_limited_pairings":
                "; ".join(cl["link_limited_pairings"]),
            "claim_ceiling": cl["claim_ceiling"],
            "bottleneck_note": cl["bottleneck_note"],
            "why_run_it_anyway": cl["why_run_it_anyway"]}))

    # ---------------------------------------------------------------
    # P09 — publication decision
    # ---------------------------------------------------------------
    decision = _lg.private_rc_decision(
        "Andrew Green", "2026-07-18",
        "Decision unresolved pending patent-agent consultation; "
        "PRIVATE_RC preserves both other paths.")
    auth = _lg.authorize_publication(decision)
    store.add("r7_governance", Record(
        id="R7-PUBLICATION-DECISION", kind="publication_decision",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r7.legacy.authorize_publication",
        fields={
            "path": decision.path,
            "signed_by": decision.signed_by,
            "signed_at": decision.signed_at,
            "digest": decision.digest(),
            "complete": decision.is_complete(),
            "reversible": True,
            "authorized_to_publish": auth["authorized"],
            "status": auth["status"],
            "note": auth["note"]}))

    cnf = _lg.commit_is_not_a_filing()
    store.add("r7_governance", Record(
        id="R7-COMMIT-IS-NOT-A-FILING", kind="legal_boundary",
        evidence_class="UNSUPPORTED",
        provenance="r7.legacy.commit_is_not_a_filing",
        fields={
            "status": cnf["status"],
            "provides": "; ".join(cnf["git_commit_provides"]),
            "does_not_provide":
                "; ".join(cnf["git_commit_does_not_provide"]),
            "why_it_matters": cnf["why_it_matters"]}))

    cmp = _lg.path_comparison()
    for path in ("FILE_THEN_PUBLISH", "DEFENSIVE_PUBLICATION",
                 "PRIVATE_RC"):
        row = cmp[path]
        store.add("r7_governance", Record(
            id=f"R7-PATH-{path}", kind="publication_path",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="r7.legacy.path_comparison",
            fields={
                "path": path,
                "preserves_patent_rights":
                    str(row["preserves_patent_rights"]),
                "creates_public_prior_art":
                    str(row["creates_public_prior_art"]),
                "reversible": row["reversible"],
                "forecloses": row["forecloses"],
                "cost": row["cost"]}))
