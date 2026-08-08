# RGCS Design Studio

Design Studio is the guided, task-first mode of the desktop workbench
(`rgcs-workbench`). It answers, at every step: what am I making, what
measurements do I need, what is derived, what is estimated, what can I export,
what claim class applies, and what should I do next.

## Launching

```bash
python -m pip install -e ".[desktop]"
rgcs-workbench
```

The app opens on the **Design Studio** home tab — a set of task cards:

- **Validate a crystal** → [Crystal Validator](CRYSTAL_VALIDATOR.md)
- **Generate a certification sheet** → [Certification Sheets](CERTIFICATION_SHEETS.md)
- **Design a crystal-first Phryll cone (v2)** → [Phryll Generator v2](PHRYLL_GENERATOR_V2.md)
- **Design coils and pulse settings** → [Coil / Pulse Designer](COIL_PULSE_DESIGNER.md)
- **Design an annular ring prototype** → [Annular Ring Designer](ANNULAR_RING_DESIGNER.md)
- **Open Frequency Key Library** → [Frequency Keys](FREQUENCY_KEYS.md)
- **Open Advanced Scientific Workbench** → [Advanced Mode](ADVANCED_MODE.md)

## The golden path

```text
Crystal Validator
  -> Certification Sheet
  -> Phryll Generator v2
  -> Coil and Pulse Designer
  -> Export Bundle
```

The original box-holder designer ("Phyrll Generator Designer", v1) is
retired from the UI as of v8.5.2 — the crystal-first
[Phryll Generator v2](PHRYLL_GENERATOR_V2.md) is the only Phryll path.
Existing v1 exports (SCAD, build PDFs, receipts) remain valid files, and
the v1 service is kept in the codebase for legacy reading; see the
retired [Phyrll Generator Designer](PHYRLL_GENERATOR_DESIGNER.md) page.

Each workflow writes a JSON receipt, a human-readable PDF, diagrams or generated
geometry where relevant, a checksum, and a claim-boundary block.

## Status vocabulary

Values are labelled as **measurement** (you entered it), **derived geometry**
(computed deterministically from measurements), or **model estimate** (output of
a declared model). Exports carry the claim classification of their least-settled
input.

## Claim boundary

Design Studio artifacts are engineering plans and reproducibility records.
Predictions are model outputs. They do not by themselves validate an anomalous
physical effect — measurements decide. See
[../CLAIM_BOUNDARIES.md](../CLAIM_BOUNDARIES.md).
