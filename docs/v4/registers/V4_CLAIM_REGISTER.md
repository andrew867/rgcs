# V4.1 Completion Claim Register (orchestrator-owned)

Each claim: exact public wording, class, tags, sources/equations,
supporting tests, controls, limitations, forbidden stronger wording.
A claim with no supporting test cannot be release_allowed.

| id | public wording (exact) | class / tags | tests | forbidden stronger wording |
|---|---|---|---|---|
| CLM-V4C-01 | "Alpha quartz's validated capabilities are anisotropic elasticity, piezoelectricity, dielectric anisotropy, photoelasticity, and birefringence; all magnetic/quantum-material mechanisms have no validated quartz implementation and return typed refusals." | CORE_VALIDATED / EST,ENG | test_v4c_capability (13) | "quartz cannot host these mechanisms" (nonexistence claim — forbidden) |
| CLM-V4C-02 | "The Saint-Venant square-bar torsional benchmark agrees with the FEM authority within 5%." | CORE_VALIDATED / EST,DER | test_square_bar_torsional_ladder_vs_fem | any tighter tolerance |
| CLM-V4C-03 | "Optical topological charge is extracted only from actual phase winding; real fields and intensity nulls yield charge 0." | CORE_VALIDATED / EST,DER | test_vortex_charges_and_null_beam | "vortex detected" from curl/intensity |
| CLM-V4C-04 | "The reduced avoided-crossing model reproduces the frozen v3 coupled_two_mode to 1e-12 in the lossless limit." | CORE_VALIDATED / EST,DER | test_zero_coupling_exact_crossing_and_frozen_anchor | reinterpretation of frozen results |
| CLM-V4C-05 | "In the LiNiPO4 reference model, domain-writing bias is controlled by propagation direction and is polarization-invariant; helicity and polarization-angle responses belong to the IFE and thermal comparators respectively." | REDUCED_ORDER_VALIDATED / DER | test_polarization_ablation_iome_vs_comparators | any claim about measured LiNiPO4 values (source pending, DV4C-003) |
| CLM-V4C-06 | "FDT content is preserved as SOURCE_HYPOTHESIS with pre-registered discriminators; it cannot enter default solvers and no exclusive confirmation can be claimed." | SOURCE_HYPOTHESIS / SRC,HYP | test_v4c_fdt_lore (8) | endorsement or ridicule |
| CLM-V4C-07 | "The canonical 110 mm candidate at (−0.295, −0.205, 102.240) mm lies 3.906 mm from the nearest conventional node/antinode station; at the current mesh-dominated localization uncertainty (±3.08 mm) the intervals overlap, so the implemented conventional model may explain it within uncertainty." | CORE_VALIDATED evidence, verdict class UNCERTAINTY_OVERLAPS / DER | test_v4c_node_coincidence (7) + bundle eye/node_coincidence.json | "the candidate IS a conventional node" AND "the candidate is a confirmed anomaly" (both) |
| CLM-V4C-08 | "A finer mesh pair near clmax ≈ 4 mm would discriminate the 3.906 mm separation." | ENG (declared computation) | derived from evidence table | any promised outcome |
| CLM-V4C-09 | "No restricted source PDF ships in any release asset." | ENG / EST | test_no_restricted_source_in_current_release_assets + R1 audit | — |
| CLM-V4C-10 | "The metacrystal transfer is a declared bounded ENG rule validated on canonical photon-statistics fixtures; it is not a microscopic plasmonic simulation and not bulk quartz." | REDUCED_ORDER_VALIDATED / DER,ENG | test_v4c_metacrystal (6) | "simulates plasmonic metacrystals" |

# V4.1 Risk Register (delta over v4.0.0)

| risk | status / mitigation |
|---|---|
| New-wave source files absent → numeric fixtures cannot be compared to papers | OPEN, declared (DV4C-003); envelopes carry SOURCE_VALUE_COMPARISON_PENDING; ingest tool ready |
| Mesh-dominated eye localization (±3.08 mm) leaves the 3.906 mm question open | OPEN, declared; discriminating computation specified (CLM-V4C-08) |
| User-constructed MaterialCapabilities records can enable any mechanism | ACCEPTED by design: the firewall guards REGISTERED records; direct construction is a programming act, documented; Q1 verified registered-path integrity |
| Junction-plane conventional explanation for the 102.2 mm feature untested | OPEN; listed as viable conventional explanation, not assumed |
| Windows-only bit-determinism of bundles | Declared (as v4.0.0); CI checks tolerance-level only |

# V4.1 Traceability (agents → modules → tests → gates)

B0→tools/v4/baseline+docs/v4/baseline→test_v4c_baseline(5)→A1-A4;
M1→provenance_v4+sources/registry→test_v4c_provenance(11)→B1-B5;
M2→multiphysics/→test_v4c_capability(13)→C1-C5;
M3→quantity_registry,curves,torsion_mech,optical_am,circulation,
chiral_phonon→test_v4c_torsion_oam(14)→D1-D7;
M4→refmodels/{exciton_magnon,avoided_crossing,block_hamiltonian,
dressed_spin}→test_v4c_refmodels_m4(10)→E1-E3,E5;
M5→refmodels/dynamic_me→test_v4c_dynamic_me(8)→E4;
M6→dynamic_boundary→test_v4c_dynamic_boundary(6)→F1-F5;
M7→refmodels/metacrystal→test_v4c_metacrystal(6)→G1-G4;
M8→calibration→test_v4c_calibration(7)→I1-I5;
M11→refmodels/iome_linipo4→test_v4c_iome(9)→H1-H5;
M12→refmodels/nonlinear_spin→test_v4c_nonlinear_spin(7)→H6-H7;
M13/M10→source_hypotheses/→test_v4c_fdt_lore(8)→H8-H10,B5;
M14→optics_channels→test_v4c_channels(6)→ablation gates;
M9+correction→eye_votes+eye+proofbundle→test_v4c_eye_votes(5)+
test_v4c_node_coincidence(7)+test_rscs2_eye(16)→J1-J5;
D1→docs/v4+examples→test_v4c_docs_examples(5)→K1-K2.
