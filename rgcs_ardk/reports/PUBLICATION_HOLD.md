# PUBLICATION_HOLD

R10.74 fabrication, hardware publication, and performance claims remain under
`PUBLICATION_HOLD`. No push, fabrication-ready declaration, hardware release,
or performance claim is authorized by this scaffold.

Removal requires explicit approval plus pinned R10.73 authority, Board A
calibration, Board B low-power control receipts, local KiCad DRC, approved
manufacturer stackup, hashed fabrication outputs, safety review, complete
bench receipts, and a clean public-path audit.

## R10 Public RC1 Gate Resolution

The R10 public release gates explicitly resolve the software-publication part
of this hold for the filtered local `r10-public-rc1` software and documentation
candidate only. The gate evidence records 8,919 passed tests, zero failures,
zero excluded-term public leaks, zero force/thrust namespace leaks, zero
wall-power paths, pinned R10.73 authority, and hash-verified candidate files.

This resolution authorizes a local annotated release-candidate tag. It does not
authorize a remote push. ARDK fabrication readiness remains `REFUSED`, seed
drive inputs remain `NOT_AUTHORITY`, and every fabrication and performance
restriction above remains asserted.
