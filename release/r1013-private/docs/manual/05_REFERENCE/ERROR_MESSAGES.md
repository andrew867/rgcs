# Error Message Contract

An error message must state:

1. What failed.
2. Which field or artifact caused it.
3. Why the operation cannot continue.
4. The smallest repair action.
5. Whether the input was modified.

Examples:

`SPECIMEN_SCHEMA_INVALID: geometry.length_mm must be greater than zero. Enter the measured tip-to-tip length in millimetres. The file was not modified.`

`INSUFFICIENT_GEOMETRY_FOR_FEM: geometry.narrow_diameter_mm is null. Add the measured narrow diameter or use a quick estimate. No mesh was created.`

`GMSH_NOT_FOUND: the full mesh command needs the Gmsh executable. Install Gmsh and run 'gmsh --version'. Quick estimates remain available.`

`ORIENTATION_UNDERDETERMINED: the full anisotropic result requires orientation. Add an orientation record or run an orientation ensemble.`
