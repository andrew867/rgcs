# REJECTED — superseded by the R10.8.5 locked correction (2026-07-26)

The R10.8.4 interpretation (raw decimal digits read directly as recursive
XYZ triplet instructions, decimal-native 100-child simplex operator) is
**rejected**. The locked pipeline is:

    raw decimal integer -> fixed-width binary packet -> octal
    -> F5 | Q22 | S3 -> recursive hedron decode (radix 8; 8^12 = 2^36)

using the R12 grammar and refinement operator already in the repository
(`r12/icosapacket.py`, `r12/icosarefine.py`), reused verbatim.

Status of this directory: receipted rejected experiment. The code in
`cwatlas/r1084/` is retained under
`CW_RECURSIVE_XYZ_LEVELS_V1: REJECTED_FOR_SOURCE_DECODE` in
`cwatlas/r1082/decoder_candidates.py`. Its structural results (exact
triplet arithmetic, lattice bijection, containment invariant, inverse
encoder) remain correct mathematics about a rejected reading; its
placement results are `WRONG_MODEL_TESTED` for the octal-packet codec.

Successor receipts: `docs/proofs/r1085-octal-packet-recovery/`.
