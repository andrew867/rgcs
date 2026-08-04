# Public Variable-Length Vector Codec Receipt

The `terra-variable-r4-s8-p12` adapter provides reversible parsing for the 27, 30, 33, and 36-bit structural family.

Layout: `R4 | S8 | P12 | tail`.

The tail contains zero to three optional 3-bit epoch/state groups followed by one mandatory 3-bit check group. The adapter preserves an explicit framed width, including leading-zero roots, and returns `NOT_PERFORMED` for physical projection.

Acceptance test: `tests/rgcs_coordinate/test_variable_length_36.py`.
