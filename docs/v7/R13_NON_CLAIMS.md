# R13 Non-Claims

R13 is a complete software simulation and experiment **architecture**. It
establishes none of the following, and each is held down by a named refusal
in code that the red team (`tests/v6/test_r13_redteam.py`) exercises.

| R13 does NOT establish | Enforcing refusal (module) |
|---|---|
| **Phyrll** as a particle, field, or energy carrier | `refuse_paper_as_carrier_evidence` (`claimtypes`) |
| A **truncated photon** as a new object | `refuse_paper_as_carrier_evidence` (`claimtypes`) |
| **Neutrino / antineutrino** coupling to the apparatus | `refuse_paper_as_carrier_evidence` (`claimtypes`) |
| **Dark-matter** detection | `refuse_simulation_as_measurement` (`claimtypes`) |
| **Continuous-spin** fields | `refuse_paper_as_carrier_evidence` (`claimtypes`) |
| Unrestricted **isotropic emission** | `refuse_planar_uniformity_as_isotropy` (`sixangle`, `claimtypes`) |
| **Chiral phonons** in the specific RGCS crystal *without measurement* | `refuse_model_chirality_as_measured` (`chiral`) |
| A **decoded CQ/CW destination** | `refuse_alias_as_destination` (`coordfinal`, `claimtypes`) |
| An **artificial magnetic root** | `refuse_root_as_unique_location` (`magroot`) |
| A **unique Ba/Cs epoch** | `refuse_epoch_as_unique_time` (`epochsolve`) |
| **Energy production** beyond measured input | `refuse_unclosed_as_new_energy` (`boundaryenergy`, `daq`) |
| **External-source authentication** | `refuse_numeric_match_as_authentication`, `refuse_field_match_as_source`, `refuse_hash_match_as_authentication` |

## Why these stay unsupported

The strongest claim class any R13 module reaches from software alone is
`REPOSITORY_COMPUTATIONAL_RESULT`. Every named object above would require a
**measurement class** (`BENCH_MEASUREMENT` / `INDEPENDENTLY_REPLICATED`),
and no apparatus is operated here. The seven forbidden promotions in
`r13/claimtypes.py` (length asserted == 7) block the shortcuts by which a
model, a numeric match, an unclosed ledger, planar uniformity, a coordinate
alias, or a cited paper would be turned into one of these claims.

They remain unsupported unless future evidence satisfies the project's
prospective and calibration gates (preregistration + blinding, phase 44; the
falsification protocols, phases 30 and 42).

`PHYSICAL_VALIDATION_NOT_CLAIMED`.
