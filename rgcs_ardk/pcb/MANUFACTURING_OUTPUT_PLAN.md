# Manufacturing Output Plan

The generator emits separate KiCad-native design scaffolds for Board A and
Board B. It never labels those files fabrication-ready.

Fabrication release additionally requires the pinned R10.73 inputs, an
approved manufacturer stackup, local KiCad DRC evidence, reviewed BOM and
assembly data, Gerber/drill/STEP exports, output hashes, Board A calibration,
Board B dummy-load and symmetric-control receipts, and safety approval.

Expected local commands, after the board files have been generated:

```text
kicad-cli pcb drc <board.kicad_pcb> --output <drc-report.json>
kicad-cli pcb render <board.kicad_pcb> --output <preview.png>
kicad-cli pcb export gerbers <board.kicad_pcb> --output <gerber-dir>
kicad-cli pcb export drill <board.kicad_pcb> --output <drill-dir>
kicad-cli pcb export step <board.kicad_pcb> --output <board.step>
```

The exact command syntax must be checked against the installed KiCad version.
No manufacturing archive is produced by the reference generator.
