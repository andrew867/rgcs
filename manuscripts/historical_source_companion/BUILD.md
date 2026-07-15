# Build instructions

1. `python tools/make_v3_artifacts.py`   (regenerates tables/ and figures/
   from the tested libraries -- no number in the text is hand-typed)
2. `xelatex -interaction=nonstopmode historical_source_companion.tex`
3. `bibtex historical_source_companion`
4. `xelatex -interaction=nonstopmode historical_source_companion.tex`  (twice, for refs)

Or `latexmk -xelatex historical_source_companion.tex` where latexmk/perl is available.
Fonts: TeX Gyre Pagella/Heros + DejaVu Sans Mono, loaded by filename from
the TeX distribution (no OS font registration needed).
Shared preamble: `../common/rgcs_v3_preamble.tex`; bibliography:
`references/references.bib` + `manuscripts/common/handbooks.bib`.
