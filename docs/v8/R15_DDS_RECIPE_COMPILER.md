# R15 P25 — DDS Recipe Compiler

Compiles a frozen protocol / sweep into a deterministic sequence of DDS tuning words (FTW = round(f/f_clk * 2^N), phase and amplitude words, chirp/ramp steps). A dyadic target compiles to an exact FTW; an approximate target round-trips within one LSB. Device limits (Nyquist, max FTW, phase/amplitude resolution) are enforced and out-of-range or post-seal-edited recipes are refused. Running a recipe on real DDS hardware is PREREGISTERED_NOT_RUN.

- **Module:** `r15/dds_recipes.py`
- **Tests:** `tests/v8/test_dds_recipes.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.
