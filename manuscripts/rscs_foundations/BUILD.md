# Build instructions

1. `python tools/make_v3_artifacts.py`   (regenerates tables/ and figures/
   from the tested libraries -- no number in the text is hand-typed)
2. `xelatex -interaction=nonstopmode rscs_foundations.tex`
3. `bibtex rscs_foundations`
4. `xelatex -interaction=nonstopmode rscs_foundations.tex`  (twice, for refs)

Or `latexmk -xelatex rscs_foundations.tex` where latexmk/perl is available.
Fonts: TeX Gyre Pagella/Heros + DejaVu Sans Mono, loaded by filename from
the TeX distribution (no OS font registration needed).
Shared preamble: `../common/rgcs_v3_preamble.tex`; bibliography:
`references/references.bib` + `manuscripts/common/handbooks.bib`.
