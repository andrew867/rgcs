# Mechanical Fixture Specification

The RevA fixture is stationary and shares its four mounting-hole coordinates
with both PCB variants. It supports Board A alone, Board A and Board B as a
registered stack, removable annular coupons, controlled spacers, a PTFE center
sleeve, and a 37-position probe-holder pattern at the 119 mm mean radius.

OpenSCAD owns only fixture solids. It contains no copper, electrical registry,
or fabrication-net data. KiCad remains the authority for PCB holes and board
exports; the test suite compares the fixture coordinates to the geometry
kernel.

Per-run records must include fixture serial, spacer height, mapped gap,
measured clamp torque, orientation, remount count, and probe-position
uncertainty. The first characterization uses Board A only. No part rotates or
moves during a run.

`annular_fixture_revA.scad` is a parametric scaffold. STL/STEP or drawings may
be generated only after a CAD review confirms tolerances and material choices.
