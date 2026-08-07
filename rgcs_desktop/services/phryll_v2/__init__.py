"""Phryll Generator Designer v2 — crystal-first parametric CAD.

The user's measured crystal dimensions drive every generated surface:
inner cone = crystal envelope + clearance, outer cone = inner + wall,
coil sleeve and grooves generated around that cone, and the crossed
copper/silver coil crossing plane aligned to the exact Eye coordinate.

Reference assets (CC-SA STL/3MF/GCODE/SCAD) are style and size-family
references ONLY — nothing in this package scales a stock mesh into an
output. Annular-ring craft locks (35/37, 47/72, 288/188 mm,
1,683,456 Hz) are a separate lane and are never cone-sizing inputs.
"""
