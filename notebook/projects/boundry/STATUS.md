# Boundry -- Status

## Current State
Boundry is a Python package for protein engineering combining LigandMPNN
(neural network sequence design) with OpenMM AMBER (physics-based energy
minimization). Core operations (idealize, minimize, repack, relax, mpnn,
design, analyze-interface, optimize) are functional with a Typer-based CLI
and YAML workflow system.

The `boundry optimize` command implements beam-search interface optimization
with alanine-scan-guided position selection, parallel design+relax expansion,
and campaign-based restarts. It is the primary interface engineering tool.

A detailed scoring analysis (`SCORING_ANALYSIS.md`) comparing boundry optimize
against Rosetta's flex-ddG protocol has been completed. Three critical scoring
misalignments were identified that are likely reducing ddG prediction accuracy.

## Open Questions
- How much does fixing the solvation mismatch improve ddG correlation with
  experiment? Need a benchmark dataset to test.
- Should constrained minimization (with position restraints) be the default
  for optimize, or should it remain opt-in?
- Is multi-structure averaging (3-5 seeds) worth the computational cost for
  the optimize scoring loop?

## Next Steps
1. Fix solvation model mismatch in `relaxer.py` (use GBn2 in
   `_relax_unconstrained()` when `implicit_solvent=True`).
2. Enable `relax_separated=True` in optimize scoring path.
3. Apply position restraints during unconstrained minimization.
4. Benchmark scoring changes against experimental ddG data.
5. Consider multi-structure scoring for noise reduction.

## Recent Context
- **2026-03-13**: Performed comprehensive scoring analysis comparing boundry
  optimize vs Rosetta flex-ddG. Identified 3 critical issues: solvation
  mismatch (vacuum relax + GBn2 scoring), no unbound-state relaxation in
  optimize, and no ensemble averaging. Wrote findings to `SCORING_ANALYSIS.md`.
