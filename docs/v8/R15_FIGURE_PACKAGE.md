# R15 P32 — Figure and Evidence Package Generator

Figure descriptors are built from synthetic data, each with traceable provenance and a synthetic-data caption.

- **Module:** `r15/figures.py`
- **Tests:** `tests/v8/test_figures.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Negative results

- A figure with no data provenance is refused; a caption not stating the data are synthetic is refused.
- No figure depicts a physical measurement.
