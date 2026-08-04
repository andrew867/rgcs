# R10 Public Release Filter Report

Generated: `2026-08-04T00:06:17.332354-02:30`
Base: `d201550ac9644353053ce9336874d9c3ca3328b1`
Result: **PASS**

The audit is exclusion-first: an exclusion hit always defeats an inclusion rule, archive/private/quarantine material cannot be included, and an unmatched file is sent to `REVIEW`. This report is release-control evidence and is not itself copied into the public candidate because it necessarily enumerates the restricted vocabulary.

## Existing Filter

- Command: `python -m pytest tests/test_terra_public_release_filter.py -q --basetemp build/pytest-r10-release-existing`
- Result: **PASS** (38 passed)

## Scan Revision

The consolidated revision was scanned directly with no overlays.

## Counts

- Files scanned: **3018**
- Explicit public candidates: **532**
- Excluded/private: **96**
- Quarantine/archive: **410**
- Review: **1980**
- Files with excluded-term hits: **96**
- Excluded-term files classified public: **0**

## Required Vocabulary

`crabwood`, `cnt`, `carbon nanotube`, `ascii`, `plaintext`, `message decode`, `message_decode`, `message-decode`, `message decoding`, `message_decoding`, `message-decoding`, `decoded message`, `decoded_message`, `decoded-message`, `glyph message`, `glyph_message`, `glyph-message`, `private comms`, `private_comms`, `private-comms`, `deuterium`, `tritium`, `heavy water`, `heavy_water`, `heavy-water`, `neutron`, `fusion`, `transmutation`, `helium generation`, `helium_generation`, `helium-generation`, `reactor`, `uhv gas fill`, `uhv_gas_fill`, `uhv-gas-fill`

## Excluded Hit Evidence

| Path | Path hits | Content hits | Class |
|---|---|---|---|
| `CHANGELOG.md` | none | neutron | private |
| `archive/v2.0.0/release/SHA256SUMS.txt` | none | ascii | private |
| `archive/v2.0.0/release/rgcs-v2-src-2.0.0.zip` | none | cnt | private |
| `archive/v2.0.0/release/rgcs_v2.pdf` | none | cnt | private |
| `cwatlas/codec_base100.py` | none | ascii | private |
| `cwatlas/codec_pack38.py` | none | ascii | private |
| `cwatlas/codec_pack40.py` | none | ascii | private |
| `cwatlas/codec_triplet9.py` | none | ascii | private |
| `cwatlas/ingest.py` | none | ascii | private |
| `cwatlas/privacy.py` | none | private comms, private-comms, private_comms | private |
| `cwatlas/provenance_ledger.py` | none | private comms, private-comms, private_comms | private |
| `cwatlas/r1082/route_core.py` | none | ascii | private |
| `cwatlas/share.py` | none | ascii | private |
| `docs/DEFECT_REGISTER.md` | none | ascii | private |
| `docs/RGCS_126BIT_WIDE_ENVELOPE.md` | none | ascii, plaintext | private |
| `docs/assets/user-manual/03_decode_toronto_168930443.png` | none | cnt | private |
| `docs/assets/user-manual/07_path_toronto_drummondville.png` | none | cnt | private |
| `docs/assets/user-manual/09_path_stonehenge_orangeA.png` | none | cnt | private |
| `docs/assets/user-manual/10_polygon_uk4.png` | none | cnt | private |
| `docs/cwatlas/R10_8_1_MANUSCRIPT.md` | none | private comms, private-comms, private_comms | private |
| `docs/cwatlas/receipts/P21.json` | none | ascii | private |
| `docs/proofs/r1071-phyrll-terra/RGCS_TERRA_PUBLIC_RELEASE_FILTER_REPORT.md` | none | ascii, crabwood, glyph message, glyph-message, glyph_message, message decode, message decoding, message-decode, message-decoding, message_decode, message_decoding, plaintext, private comms, private-comms, private_comms | private |
| `docs/proofs/r1071-phyrll-terra/r1071_filter_scan.txt` | none | crabwood | private |
| `docs/proofs/r1074-annular-devkit/safety_and_claim_firewall.md` | none | ascii | private |
| `docs/r1015a/README.md` | none | ascii | private |
| `docs/r109/earth_v1/RGCS_Earth_Alignment_Candidate_2026-07-26/figures/earth_alignment_equirectangular.png` | none | cnt | private |
| `docs/r109/earth_v1/RGCS_Earth_Alignment_Candidate_2026-07-26/figures/earth_alignment_globe.png` | none | cnt | private |
| `docs/r109/earth_v1/RGCS_Earth_Alignment_Candidate_2026-07-26/operator/WARP_STEPS.json.gz` | none | cnt | private |
| `docs/release/r10_branch_worktree_inventory.json` | none | crabwood | private |
| `docs/release/r10_release_filter_report.json` | none | ascii, carbon nanotube, cnt, crabwood, decoded message, decoded-message, decoded_message, deuterium, fusion, glyph message, glyph-message, glyph_message, heavy water, heavy-water, heavy_water, helium generation, helium-generation, helium_generation, message decode, message decoding, message-decode, message-decoding, message_decode, message_decoding, neutron, plaintext, private comms, private-comms, private_comms, reactor, transmutation, tritium, uhv gas fill, uhv-gas-fill, uhv_gas_fill | private |
| `docs/release/r10_release_filter_report.md` | none | ascii, carbon nanotube, cnt, crabwood, decoded message, decoded-message, decoded_message, deuterium, fusion, glyph message, glyph-message, glyph_message, heavy water, heavy-water, heavy_water, helium generation, helium-generation, helium_generation, message decode, message decoding, message-decode, message-decoding, message_decode, message_decoding, neutron, plaintext, private comms, private-comms, private_comms, reactor, transmutation, tritium, uhv gas fill, uhv-gas-fill, uhv_gas_fill | private |
| `docs/v4/FABRICATION_CONTRACT.md` | none | ascii | private |
| `docs/v4/R6_MANUSCRIPT.md` | none | fusion | private |
| `docs/v4/RELEASE_NOTES_V4_3_0.md` | none | neutron | private |
| `docs/v4/V4X2_QA_VERDICT.md` | none | neutron | private |
| `docs/v4/resonator/CLOSED_LOOP_PLATFORM.md` | none | neutron | private |
| `docs/v4/resonator/LORE_AND_INTUITION_POLICY.md` | none | neutron | private |
| `docs/v52/R9_FINDINGS.md` | none | neutron, reactor | private |
| `docs/v6/R12_FINDINGS.md` | none | neutron | private |
| `docs/v6/RELEASE_NOTES_V6_3_0.md` | none | neutron | private |
| `docs/v7/R13_FINDINGS.md` | none | neutron | private |
| `docs/v7/R13_R12_DEFERRED_CLOSURE.csv` | none | neutron | private |
| `docs/v7/R13_TRACEABILITY_MATRIX.csv` | none | neutron | private |
| `docs/v7/R14_HANDOFF.md` | none | neutron | private |
| `docs/v7/RELEASE_NOTES_V7_0_0.md` | none | neutron | private |
| `docs/v7/receipts/02_DEFERRED_BACKLOG_CLOSURE_AND_REQUIREMENT_TRACEABILITY.md` | none | neutron | private |
| `docs/v7/receipts/31_EUPHONIC_AND_FORCE_CONSTANT_PIPELINE.md` | none | neutron | private |
| `docs/v7/receipts/32_SYNTHETIC_INS_AND_IXS_EXPERIMENTS.md` | none | neutron | private |
| `docs/v7/receipts/33_NEUTRON_FACILITY_REALITY_SAFETY_AND_LICENSING.md` | neutron | neutron, reactor | private |
| `docs/v7/receipts/34_BEAM_TIME_AND_COLLABORATION_PROPOSAL.md` | none | neutron | private |
| `docs/v7/receipts/35_RAMAN_RIXS_IXS_AND_ELECTRON_SCATTERING_ALTERNATIVES.md` | none | neutron, reactor | private |
| `docs/v7/receipts/48_V7_RELEASE_AND_R14_HANDOFF.md` | none | neutron | private |
| `docs/v8/R15_R13_CLOSURE.csv` | none | neutron | private |
| `manuscript/figures/fig_spiral_projection.pdf` | none | cnt | private |
| `manuscript/rgcs_v2.pdf` | none | cnt | private |
| `model_playground.py` | none | neutron | private |
| `negative_results/R1063_WIDE_ENVELOPE_NULLS.md` | none | ascii | private |
| `r1010/orientation.py` | none | ascii | private |
| `r1013/specimen.py` | none | ascii | private |
| `r1015a/cli.py` | none | ascii | private |
| `r1015a/scad.py` | none | ascii | private |
| `r1028/payload.py` | none | ascii | private |
| `r1034/descramble.py` | none | ascii | private |
| `r109/sealed_holdout.py` | none | ascii | private |
| `r12/reciprocal.py` | none | neutron | private |
| `r13/__init__.py` | none | neutron | private |
| `r13/euphonic.py` | none | neutron | private |
| `r13/preregister.py` | none | ascii | private |
| `r13/scattering.py` | none | neutron | private |
| `r13/serialize.py` | none | ascii | private |
| `r15/specimens.py` | none | ascii | private |
| `r6/navigation.py` | none | fusion | private |
| `r9/betadecay.py` | none | neutron | private |
| `r9/carrier.py` | none | neutron, reactor | private |
| `release/r1013-private/artifacts/rgcs-8.3.0.tar.gz` | none | cnt | private |
| `resonator_platform/composite_modes.py` | none | neutron | private |
| `rgcs_archive/text_lanes.py` | none | plaintext | private |
| `rgcs_ardk/reports/release.py` | none | ascii | private |
| `rgcs_ardk/tests/test_bench_readiness_firewall.py` | none | ascii | private |
| `rgcs_terra_release/__init__.py` | none | ascii, crabwood, message decoding, message-decoding, message_decoding, plaintext | private |
| `rgcs_terra_release/release_filter.py` | none | ascii, carbon nanotube, cnt, crabwood, decoded message, decoded-message, decoded_message, deuterium, fusion, glyph message, glyph-message, glyph_message, heavy water, heavy-water, heavy_water, helium generation, helium-generation, helium_generation, message decode, message decoding, message-decode, message-decoding, message_decode, message_decoding, neutron, plaintext, private comms, private-comms, private_comms, reactor, transmutation, tritium, uhv gas fill, uhv-gas-fill, uhv_gas_fill | private |
| `rscs2_core/proofbundle.py` | none | cnt | private |
| `rscs2_core/spiral_cone.py` | none | ascii | private |
| `sources/registry/v4_source_registry.yaml` | none | neutron | private |
| `sources/registry/v4x2_source_registry.py` | none | neutron | private |
| `tests/cwatlas/test_codec_base100.py` | none | ascii | private |
| `tests/r1015a/test_scale_a.py` | none | ascii | private |
| `tests/release/test_r10_public_release.py` | none | ascii, carbon nanotube, cnt, crabwood, decoded message, decoded-message, decoded_message, deuterium, fusion, glyph message, glyph-message, glyph_message, heavy water, heavy-water, heavy_water, helium generation, helium-generation, helium_generation, message decode, message-decode, message_decode, neutron, plaintext, private comms, private-comms, private_comms, reactor, transmutation, tritium, uhv gas fill, uhv-gas-fill, uhv_gas_fill | private |
| `tests/test_r1061_wide_envelope.py` | none | plaintext | private |
| `tests/test_terra_public_release_filter.py` | none | ascii, carbon nanotube, cnt, crabwood, decoded message, decoded-message, decoded_message, deuterium, fusion, glyph message, glyph-message, glyph_message, heavy water, heavy-water, heavy_water, helium generation, helium-generation, helium_generation, message decode, message decoding, message-decode, message-decoding, message_decode, message_decoding, neutron, plaintext, private comms, private-comms, private_comms, reactor, transmutation, tritium, uhv gas fill, uhv-gas-fill, uhv_gas_fill | private |
| `tests/v4/test_resonator_platform.py` | none | neutron | private |
| `tests/v49/test_r6_navigation.py` | none | fusion | private |
| `tests/v52/test_r9_betadecay.py` | none | neutron | private |
| `tests/v6/test_r13_scattering.py` | none | neutron | private |
| `tools/make_v3_artifacts.py` | none | ascii | private |
| `tools/r10_public_release.py` | none | ascii, carbon nanotube, cnt, crabwood, decoded message, decoded-message, decoded_message, deuterium, fusion, glyph message, glyph-message, glyph_message, heavy water, heavy-water, heavy_water, helium generation, helium-generation, helium_generation, message decode, message decoding, message-decode, message-decoding, message_decode, message_decoding, neutron, plaintext, private comms, private-comms, private_comms, reactor, transmutation, tritium, uhv gas fill, uhv-gas-fill, uhv_gas_fill | private |

## Gate Interpretation

`PASS` means the classifier cannot promote a matching file. It does not mean every public candidate has been released. The final candidate directory receives a second byte-for-byte scan, and any match there is a mandatory stop.
