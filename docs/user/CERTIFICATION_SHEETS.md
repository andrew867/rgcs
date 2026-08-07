# Certification Sheets

A certification sheet is a one-to-two page PDF documenting a measured specimen.

## Sections

1. Header with specimen ID
2. Diagram (or a placeholder stating no image was supplied)
3. Entered measurements
4. Derived geometry
5. Mode estimates (or "unavailable" — never silently zero)
6. Uncertainty and missing fields
7. Provenance
8. Claim boundary
9. Receipt hash and software version

## Rules

- No certification sheet without uncertainty fields.
- No certification sheet without claim-boundary text.
- Absent images produce a stated placeholder, not a crash.
- Unavailable estimates are written as *unavailable*, not zero.

## Claim boundary

This sheet records measured inputs, derived geometry, model estimates, and
provenance. It does not by itself validate an anomalous physical effect.
