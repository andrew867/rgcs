# Finite-Element Pipeline


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Steps

1. Validate the specimen.
2. Build or import a closed geometry.
3. Generate a tetrahedral mesh.
4. Audit element quality and orientation.
5. Rotate material tensors.
6. Apply fixture and electrical boundary conditions.
7. Assemble matrices.
8. Solve eigenpairs.
9. Remove or label rigid modes.
10. Calculate residuals and orthogonality.
11. Classify mode shapes.
12. Repeat on a refinement ladder.
13. Write a result certificate.

## Shared requirements

- deterministic inputs produce deterministic manifests;
- mesh units are explicit;
- solver backend is recorded;
- CPU float64 remains the numerical authority unless a later release changes the policy explicitly;
- an unavailable requested backend fails loudly;
- full deep meshes are bounded by memory policy.
