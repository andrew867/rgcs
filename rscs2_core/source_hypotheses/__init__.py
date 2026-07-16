"""QUARANTINED source-hypothesis namespace (Agents M13/M10).

Everything in this package has classification ceiling
SOURCE_HYPOTHESIS with evidence tags SRC/HYP. IMPORT FIREWALL: no
default RGCS physics module (fem, quartz, piezo, projections, eye,
refsystems, multiphysics, refmodels.*) may import this package — the
adversarial suite scans for violations. The M2 coupling graph
additionally refuses source_hypothesis -> physics edges at runtime."""
