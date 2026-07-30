# RGCS v8.3.0 (R10.13 private release candidate)

Private candidate; publication HOLD. No tag, no push.

See CHANGELOG [8.3.0] and docs/r1013/manual/ for the full manual.

Reproduce the suite:

    pytest tests -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic

# expect: 8129 passed (1 archived-environment byte test deselected by policy D-V3-04)
