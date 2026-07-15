# manuscript/ — the frozen v2 manuscript

This directory holds the **RGCS v2** manuscript (`rgcs_v2.pdf`,
`rgcs_v2.tex`, generated figures/tables), retained in place as the
shipped v2 artifact.

**The four v3 manuscripts live in [`manuscripts/`](../manuscripts/)**
(note the plural): RSCS Foundations, RGCS Crystal Application, Software &
Hardware Roadmap, and the Historical & Source Companion.

Rebuild v2: `python tools/make_figures.py && python tools/make_tables.py`
then `xelatex rgcs_v2.tex && bibtex rgcs_v2 && xelatex rgcs_v2.tex`
(twice). Layout record: `LAYOUT_QA_REPORT.md`.
