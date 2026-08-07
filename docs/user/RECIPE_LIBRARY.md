# Recipe Library

Seven seed recipes ship with the studio (searchable by text, frequency,
or family):

| Recipe | Carrier | Beat | Family |
|---|---|---|---|
| RGCS-BIN-0001 Simple 4 Hz Patent Seed | 102 Hz | 4 Hz | binaural |
| RGCS-GWY-0001 Gateway-Style Focus 10 Seed | 200 Hz | 5 Hz | gateway_style |
| RGCS-AST-0001 6.3 Hz Astral Source Lead | 528 Hz | 6.3 Hz | source_language |
| RGCS-SCH-0001 7.83 Hz Schumann Bridge | 925 Hz | 7.83 Hz | rgcs_bridge |
| RGCS-FKY-0925 925 Hz Frequency Key Carrier | 925 Hz | 7.83 Hz | frequency_key |
| RGCS-FKY-1337 1337 Hz Frequency Key Carrier | 1337 Hz | 4 Hz | frequency_key |
| RGCS-ISO-0001 Isochronic 4 Hz Pulse Seed | 200 Hz | 4 Hz | isochronic |

Each recipe converts to a full session (standard timeline shape +
layers) and renders from the library with one click, or headless:

```bash
rgcs-sonic render RGCS-FKY-0925 --out exports/
```

Recipes whose family is *source_language* or whose basis is a source
lead carry that status explicitly: their intents are recorded from
sources, not endorsed. Experimental audio recipes — results vary.
