# DOI / Zenodo Release Guide

How to mint a DOI for an RGCS release. Publication is **not** delayed for
this — the sequence below can run any time after the GitHub release
exists. No DOI value appears anywhere in this repository until Zenodo
issues one.

## One-time setup

1. Log in to https://zenodo.org with the GitHub account (`andrew867`).
2. Zenodo → Settings → GitHub → flip the toggle for `andrew867/rgcs`.
   (Requires the repository to be public.)
3. From then on, every **published GitHub release** is archived
   automatically and receives its own DOI, plus a concept DOI that always
   resolves to the latest version.

## Per-release sequence

1. Publish the GitHub release (tag `vX.Y.Z`).
2. Wait for Zenodo to ingest it (minutes), then open the new record.
3. Verify the metadata below; edit on Zenodo if the automatic import
   missed anything; press Publish on Zenodo.
4. Follow-up commit to this repository:
   - add to `CITATION.cff`:
     ```yaml
     identifiers:
       - type: doi
         value: <the version DOI Zenodo issued>
         description: "Zenodo archive of this release"
     ```
   - add the DOI badge under the README title:
     `[![DOI](https://zenodo.org/badge/DOI/<doi>.svg)](https://doi.org/<doi>)`

## Zenodo-ready metadata (copy from here)

| Field | Value |
|---|---|
| Title | RGCS v3.0.0 — RSCS 1.0: typed coordinates, conservative extension, and a pre-registered falsification programme |
| Creators | Green, Andrew (me@andrewgreen.ca) |
| Resource type | Software |
| License | MIT |
| Abstract | use the `abstract` block of `CITATION.cff` verbatim |
| Keywords | reproducible-research, research-software, resonance, quartz, elastodynamics, coupled-oscillators, acousto-optics, falsification, pre-registration, provenance |
| Related identifiers | `isSupplementTo` → the GitHub release URL; earlier version relation to the v2.0.0 record if one is ever minted |
| Version | 3.0.0 |

## Notes

- The frozen v2.0.0 tag can optionally receive its own retroactive record
  by uploading `archive/v2.0.0/release/` artifacts manually; only do this
  if a citation to v2 specifically is needed.
- Zenodo archives the *tag tarball*; the checksummed artifacts under
  `release/` are attached to the GitHub release and travel with it.
