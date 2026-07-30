# RGCS Earth Alignment Candidate

This package contains the first complete calibrated globe alignment built from the current project constraints.

Start with:

- `EARTH_ALIGNMENT_REPORT.md`
- `EARTH_ALIGNMENT_CANDIDATE.json`
- `EXACT_ARITHMETIC_TESTS.json`
- `figures/earth_alignment_equirectangular.png`

The complete frozen nonlinear operator is stored in:

- `operator/WARP_STEPS.json.gz`

Apply an arbitrary unit source vector with:

```bash
python apply_alignment.py X Y Z
```

This package is private research material. It is not an independent validation and is not cleared for publication.
