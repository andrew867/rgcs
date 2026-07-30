# Units and Conventions

- Length input: millimetres unless the field states another unit.
- Mesh internal length: metres where required by the solver.
- Mass: grams for specimen input.
- Density: grams per cubic centimetre for specimen input; kilograms per cubic metre in SI solver records.
- Frequency: hertz.
- Time: seconds; display may use milliseconds or microseconds.
- Angle: degrees in user files; radians in internal trigonometric calculations.
- Diameter mode: `across_vertices` or `across_flats`.
- Angle mode: `face_slope`, `axis_to_face`, or `apex_included`.
- Body axis: female or wide apex toward male or narrow apex, unless the specimen file overrides the convention explicitly.
- Missing value: null, never zero.
