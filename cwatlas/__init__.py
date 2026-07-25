"""RGCS R10.8.1 — CW Atlas and bidirectional geocoder.

Two separate systems live here, and the boundary between them is the whole
point.

**A canonical synthetic geocoder** (``CW-GEO-1`` and the icosahedral
``CW-HCM-ICO-1``) converts a *declared* canonical coordinate — body, frame,
epoch, shell, altitude convention, codec — to a versioned CW vector and back,
exactly, within a declared quantization. It is fully reversible and testable
now.

**A source-vector hypothesis decoder** takes a legacy or operator-reported
vector string and enumerates the *admissible* decodes as an alias set, with a
score, an uncertainty, and a search-space count — or, where calibration is
missing, a region, a heat map, or an explicit refusal. It never forces one
pin, and it never claims the reversible codec proves what a source vector
*meant*.

The standing rules (System Contract invariants, enforced in
:mod:`cwatlas.claims`):

* raw input bytes and original strings are immutable;
* every decode records codec id/version/params, frame, epoch, orientation
  profile, shell law, and software commit;
* a canonical codec round-trips exactly within its declared quantization;
* a legacy candidate decoder may return zero, one, or many aliases — never a
  forced pin;
* a map pin is never produced without a coordinate-reference-system and epoch
  receipt;
* extraordinary interpretations stay ``SOURCE_CLAIM``,
  ``OPERATOR_HYPOTHESIS``, or ``MATHEMATICAL_TRANSLATION`` until prospective
  evidence warrants promotion.

No physical or extraterrestrial validation is claimed. Public code uses
synthetic fixtures; private source corpora load only through ignored local
paths and never enter version control, builds, logs, or exports.
"""

from __future__ import annotations
