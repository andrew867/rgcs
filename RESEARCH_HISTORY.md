# Research History

A short, honest chronology of how this repository came to be. The full
detail lives in the registers (`docs/DECISION_LOG.md`,
`docs/PROGRAMME_PROGRESS.md`) and the Historical & Source Companion
manuscript; this is the orientation tour.

## Origins

The project began with a body of unconventional source material: a
historical practice tradition around faceted quartz instruments
(Vogel-style cuts), a personal working log with specific operating points
(a 4096 Hz coil carrier; sound keys at 1496/644/587 Hz; a 20 Hz
electrode-pulse family; 46 ms burst envelopes; opposed coils; a special
interior locus called "the eye"), and — later — K. Arisaka's publicly
presented NHT/HAL neuroscience proposals. The founding question was
never "is this true?" but "**can this be turned into something
testable without pretending it is true?**"

## v1 → v2: building the discipline

Early work established the pattern that still governs everything: every
statement classified (Established / Derived / Hypothesis / Source claim),
every equation registered with an id and a test, every hypothesis
pre-registered with an observable, controls, and a failure condition.

v2.0.0 (2026-07-14) shipped the deterministic core (`rgcs_core`, 61
registered equations), the desktop workbench, the experiment kit (8
protocol branches, JSON schemas, control matrices), and a fully generated
28-page manuscript. Its defining episode: **independent QA found the
project's own time-domain coupling map was wrong** (real-symmetric where
it must be anti-Hermitian, `K = i·2πg`). The correction changed the
physical interpretation, and the wrong convention is now permanently
pinned as a failing contrast test. v2 also shipped its own negative
results and an honest statement that nothing physical had been confirmed.

## v3 / RSCS 1.0: the typed layer (2026-07-14/15)

Version 3 was executed as a staged programme of twelve sequential agents,
each a tested, committed, documented unit:

| Stage | What happened |
|---|---|
| 01 | v2.0.0 byte-frozen (`archive/v2.0.0/`, tag `v2.0.0`); migration map |
| 02 | Source registry, equation-level provenance with binding forbidden-transfer clauses, frozen RSCS notation ledger |
| 03 | `rscs_core`: typed coordinates + operators, Conservative Extension Property, classification firewall |
| 04 | NHT/HAL → Hydrogenuine memory bridge (structure adapted as engineering; neuroscience quarantined) |
| 05 | Anisotropic Christoffel propagation — the v2 scalar wave-speed *hypothesis* resolved into a measured-orientation model that explains its own ±5 % band |
| 06 | Optical/photon-phonon layer with a pre-registered **reciprocity null** posture |
| 07 | Synchronized timing architecture; safety envelope frozen; the ambiguous source phrase "shorter by half" preserved as two distinctly named modes |
| 08 | Platform tranche: Windows defects fixed (one was real, two were an undeclared dependency — a lesson in itself), CI, persistence, embedded contract |
| 09 | Four generated-number manuscripts + public lessons learned |
| 10 | Independent adversarial QA — found three real defects, documented before fixes |
| 11 | Repairs, release packaging, tag `v3.0.0-rc1` |
| 12 | Publication polish (this document) |

## Where it stands

The strongest output so far is **methodological**: a demonstration that
unconventional source material can be preserved faithfully and tested
honestly without becoming evidence by repetition. The measurement
programme (claims H-20..H-30, several expected nulls) awaits bench work;
whatever it finds — including nothing — the framework is built to record
it truthfully.
