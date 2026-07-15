# Build instructions

1. `python tools/make_v3_artifacts.py`   (regenerates tables/ and figures/
   from the tested libraries -- no number in the text is hand-typed)
2. `xelatex -interaction=nonstopmode software_hardware_plan.tex`
3. `bibtex software_hardware_plan`
4. `xelatex -interaction=nonstopmode software_hardware_plan.tex`  (twice, for refs)

Or `latexmk -xelatex software_hardware_plan.tex` where latexmk/perl is available.
Fonts: TeX Gyre Pagella/Heros + DejaVu Sans Mono, loaded by filename from
the TeX distribution (no OS font registration needed).
Shared preamble: `../common/rgcs_v3_preamble.tex`; bibliography:
`references/references.bib` + `manuscripts/common/handbooks.bib`.
