"""v4.9 R6 canonical lane.

Kept in its own module because the R6 lane is large and mostly
composed of *refusals and null results*, which are first-class rows
here rather than absences. Nothing in this lane is bench data: no coil
has been wound, no crystal driven, no clock compared, and no
geophysical field has ever been loaded into this repository.
"""

from __future__ import annotations


def build_r6(store, Record) -> None:
    """Populate the five R6 tables on ``store``."""
    from r6 import claims as _claims
    from r6 import grid as _grid
    from r6 import mailbox as _mailbox
    from r6 import navigation as _nav
    from r6 import witness as _wit
    from r6.helix import decompose_pulse_trains, validate_against_solenoid
    from r6.pulse import source_frequency_audit
    from r6.wigner import verify_projector

    # ---------------------------------------------------------------
    # P01 — claim registry, verbatim source beside its ceiling
    # ---------------------------------------------------------------
    for c in _claims.ALL_CLAIMS:
        store.add("r6_claims", Record(
            id=c.id, kind="source_claim",
            evidence_class=c.evidence_class,
            provenance=c.provenance,
            fields={
                "verbatim": c.verbatim,
                "source_class": c.source_class,
                "translation": c.translation,
                "standing": c.standing,
                "ceiling": c.ceiling,
                "correction": c.correction or "",
                "required_evidence": "; ".join(c.required_evidence),
                "ordinary_first": "; ".join(c.ordinary_first),
            }))

    # ---------------------------------------------------------------
    # P02/P03 — apparatus twins
    # ---------------------------------------------------------------
    sol = validate_against_solenoid()
    store.add("r6_apparatus", Record(
        id="R6-COIL-SOLENOID-VALIDATION", kind="solver_validation",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.helix.validate_against_solenoid",
        fields={
            "numeric_bz_t": sol["numeric_bz_t"],
            "analytic_finite_bz_t": sol["analytic_finite_bz_t"],
            "relative_error_finite": sol["relative_error_finite"],
            "relative_error_infinite": sol["relative_error_infinite"],
            "aspect_ratio": sol["aspect_ratio"],
            "note": ("Biot-Savart solver validated against the finite "
                     "solenoid analytic limit; this validates the "
                     "solver, not any claim")}))

    dec = decompose_pulse_trains([1, 0, 1, 0, 1, 0],
                                 [0, 1, 0, 1, 0, 1])
    store.add("r6_apparatus", Record(
        id="R6-DRIVE-ALTERNATING-DECOMPOSITION",
        kind="drive_decomposition",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.helix.decompose_pulse_trains",
        fields={
            "claim": "R6-C-002",
            "purely_differential_fraction":
                dec["purely_differential_fraction"],
            "antiphase_fraction": dec["antiphase_fraction"],
            "mean_common_mode_a": dec["mean_common_mode_a"],
            "mean_abs_differential_a": dec["mean_abs_differential_a"],
            "result": ("the source's unipolar alternating drive is NOT "
                       "purely differential: it carries an equal "
                       "common-mode component and produces a net axial "
                       "field at half amplitude"),
            "note": dec["note"]}))

    fa = source_frequency_audit(0.1)
    store.add("r6_apparatus", Record(
        id="R6-SOURCE-FREQUENCY-AUDIT", kind="frequency_null",
        # Not ORDINARY_CHANNEL_RESULT: nothing was measured on any
        # channel. This is a statistic computed against a MODELED
        # modal spectrum.
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.pulse.source_frequency_audit",
        fields={
            "claim": "R6-C-006",
            "frequencies_hz": str(fa["frequencies_hz"]),
            "fundamental_hz": fa["fundamental_hz"],
            "all_below_fundamental": fa["all_below_fundamental"],
            "statistic": fa["statistic"],
            "null_draws": fa["null_draws"],
            "null_at_least_as_good": fa["null_at_least_as_good"],
            "p_value": fa["p_value"],
            "significant": fa["significant"],
            "verdict": fa["verdict"],
            "ceiling": fa["ceiling"]}))

    # ---------------------------------------------------------------
    # P11 — witness memory
    # ---------------------------------------------------------------
    a = _wit.caesium_reference("CS-A")
    b = _wit.caesium_reference("CS-B")
    a.calibrated_against = b.calibrated_against = "REF"
    a.recorded_channels = b.recorded_channels = _wit.NUISANCE_CHANNELS
    pred = _wit.gravitational_redshift_frac(1.0)
    cs = _wit.compare_witnesses(
        a, b, measured_frac_diff=0.0, averaging_s=86400.0,
        transfer_link_frac_uncertainty=1e-17, predicted_frac=pred)
    store.add("r6_witness", Record(
        id="R6-WITNESS-CAESIUM-1M", kind="clock_comparison",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.witness.compare_witnesses",
        fields={
            "witness_a": cs.witness_a, "witness_b": cs.witness_b,
            "predicted_frac": pred,
            "frac_uncertainty": cs.frac_uncertainty,
            "status": cs.status,
            "witness_class": cs.evidence_class,
            "consistent": cs.consistent,
            "note": ("a caesium beam averaged for a day cannot resolve "
                     "the 1.09e-16 shift from a 1 m height "
                     "difference")}))

    oa = _wit.ClockWitness("OPT-A", 4.29e14, 1e-16)
    ob = _wit.ClockWitness("OPT-B", 4.29e14, 1e-16)
    oa.calibrated_against = ob.calibrated_against = "REF"
    oa.recorded_channels = ob.recorded_channels = _wit.NUISANCE_CHANNELS
    opt = _wit.compare_witnesses(
        oa, ob, measured_frac_diff=pred, averaging_s=10_000.0,
        transfer_link_frac_uncertainty=1e-19, predicted_frac=pred)
    store.add("r6_witness", Record(
        id="R6-WITNESS-OPTICAL-1M", kind="clock_comparison",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.witness.compare_witnesses",
        fields={
            "witness_a": opt.witness_a, "witness_b": opt.witness_b,
            "predicted_frac": pred,
            "frac_uncertainty": opt.frac_uncertainty,
            "status": opt.status,
            "witness_class": opt.evidence_class,
            "consistent": opt.consistent,
            "note": ("an optical clock pair resolves it; the platform "
                     "decides, not the architecture")}))

    store.add("r6_witness", Record(
        id="R6-WITNESS-DECAY-FIREWALL", kind="refusal",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.witness.infer_proper_time_from_payload",
        fields={
            "operation": "infer proper time from payload decay",
            "result": "REFUSED",
            "ordinary_decay_causes": len(_wit.ORDINARY_DECAY_CAUSES),
            "reason": ("payload relaxation has twelve ordinary causes "
                       "and a common environmental cause can move both "
                       "channels together; characterizing all twelve "
                       "still does not make a payload a clock"),
            "collapse": "DECAY_IS_PROPER_TIME"}))

    pay = _wit.ProbabilisticPayload(
        payload_id="R6-PAYLOAD-DEMO", p0=[0.97, 0.01, 0.01, 0.01],
        prior=[0.25] * 4, t0=0.0, tau=100.0, beta=1.0)
    rec = _wit.reconstruct(pay, t=1e6, root_certificate="ROOT-LOCK-1")
    store.add("r6_witness", Record(
        id="R6-WITNESS-ROOT-CERT-BOUND", kind="reconstruction",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.witness.reconstruct",
        fields={
            "payload_id": rec.payload_id,
            "status": rec.status,
            "root_certificate_present": True,
            "posterior_returned": rec.posterior is not None,
            "refusal_reason": rec.refusal_reason or "",
            "note": ("a root certificate attests provenance and "
                     "carries no information about the physical "
                     "state")}))

    # ---------------------------------------------------------------
    # P12 — mailbox and navigation
    # ---------------------------------------------------------------
    nav = _nav.sovereignty_audit()
    store.add("r6_mailbox", Record(
        id="R6-NAV-SOVEREIGNTY-AUDIT", kind="navigation_audit",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.navigation.sovereignty_audit",
        fields={
            "claim": "R6-C-107",
            "methods_examined": nav["methods_examined"],
            "methods_infrastructure_free":
                nav["methods_infrastructure_free"],
            "status": nav["status"],
            "verdict": nav["verdict"],
            "claim_ceiling": nav["claim_ceiling"]}))

    for m, deps in _nav.DEPENDENCIES.items():
        store.add("r6_mailbox", Record(
            id=f"R6-NAV-DEP-{m}", kind="navigation_dependency",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="r6.navigation.DEPENDENCIES",
            fields={"method": m,
                    "external_dependencies": len(deps),
                    "dependencies": "; ".join(deps),
                    "infrastructure_free": False}))

    obs = _nav.analyze_observability(
        "CLOCK_GEODESY",
        _nav.clock_rate_jacobian((0.0, 0.0, -9.80665)))
    store.add("r6_mailbox", Record(
        id="R6-NAV-CLOCK-OBSERVABILITY", kind="observability",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.navigation.analyze_observability",
        fields={
            "method": obs.method,
            "jacobian_rank": obs.jacobian_rank,
            "position_dof": obs.position_dof,
            "unobservable_dof": obs.unobservable_dof,
            "status": obs.status,
            "note": ("a scalar clock rate constrains one degree of "
                     "freedom and is constant over an equipotential "
                     "surface; two of three remain unobservable")}))

    lab = _mailbox.laboratory_scale_model()
    store.add("r6_mailbox", Record(
        id="R6-MAILBOX-LAB-SCALE", kind="scale_analogy",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.mailbox.laboratory_scale_model",
        fields={"au_m": lab["au_m"],
                "lab_extent_m": lab["lab_extent_m"],
                "ratio": lab["ratio"], "status": lab["status"],
                "note": lab["note"]}))

    store.add("r6_mailbox", Record(
        id="R6-MAILBOX-NONLOCAL-REFUSAL", kind="refusal",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.mailbox.refuse_nonlocal_delivery",
        fields={
            "operation": ("deliver a payload to the celestial "
                          "destination an address names"),
            "result": "REFUSED",
            "reason": ("the mailbox routes information locally through "
                       "a declared protocol and establishes no "
                       "nonlocal coupling to the named destination"),
            "collapse": "ADDRESS_IS_A_CHANNEL"}))

    # ---------------------------------------------------------------
    # P07 — planetary grid
    # ---------------------------------------------------------------
    fld = _grid.synthetic_field(lmax=6, seed=20260718)
    rep = _grid.audit(fld, n_orientations=8, n_surrogates=12,
                      seed=20260718,
                      groups=("TETRAHEDRAL", "OCTAHEDRAL",
                              "ICOSAHEDRAL"))
    for g, v in rep["groups"].items():
        store.add("r6_grid", Record(
            id=f"R6-GRID-{g}", kind="symmetry_audit",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="r6.grid.audit",
            fields={
                "group": g,
                "degrees": str(v["degrees"]),
                "observed_best_score": v["observed_best_score"],
                "selection_null_mean": v["selection_null_mean"],
                "degree_matched_null_mean":
                    v["degree_matched_null_mean"],
                "rotation_null_mean": v["rotation_null_mean"],
                "p_vs_selection_null": v["p_vs_selection_null"],
                "significant_after_holm":
                    rep["holm_bonferroni"][g]["significant"],
                "field_family": rep["field_family"],
                "planetary_status": rep["planetary_status"]}))

    store.add("r6_grid", Record(
        id="R6-GRID-DATA-AVAILABILITY", kind="data_status",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="r6.grid.data_availability",
        fields={
            "any_real_field": False,
            "gravity_model": "ABSENT",
            "geomagnetic_model": "ABSENT",
            "topography": "ABSENT",
            "status": "NO_REAL_DATA",
            "claim_ceiling": rep["claim_ceiling"],
            "verdict": rep["verdict"]}))

    for l, g in ((3, "TETRAHEDRAL"), (4, "OCTAHEDRAL"),
                 (6, "ICOSAHEDRAL")):
        v = verify_projector(l, g)
        store.add("r6_grid", Record(
            id=f"R6-GRID-PROJECTOR-{g}-L{l}", kind="projector_check",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="r6.wigner.verify_projector",
            fields={
                "group": g, "degree": l,
                "invariant_dimension": v["dimension"],
                "max_idempotency_error": v["max_idempotency_error"],
                "max_hermiticity_error": v["max_hermiticity_error"],
                "ok": v["ok"],
                "note": ("the projector independently reproduces the "
                         "textbook lowest invariant degree for this "
                         "group")}))
