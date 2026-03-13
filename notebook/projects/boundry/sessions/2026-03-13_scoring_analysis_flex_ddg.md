---
title: "Scoring analysis vs flex-ddG"
date: 2026-03-13
time: ~
project: boundry
tldr: >
  Performed a detailed technical analysis comparing boundry optimize's scoring
  functions against Rosetta's flex-ddG protocol. Identified 3 critical, 3
  significant, and 4 moderate misalignments. Wrote findings to SCORING_ANALYSIS.md.
model: claude-opus-4-6
harness: claude-code
duration: ~
tokens: ~
git_branch: dev
status: completed
tags: [scoring, analysis, flex-ddg, optimize, binding-energy]
---

# 2026-03-13 -- Scoring analysis vs flex-ddG

## Summary
Conducted a systematic technical comparison of `boundry optimize`'s scoring
functions against Rosetta's flex-ddG protocol. Read the full flex-ddG tutorial
repository (XML protocols, analysis scripts, example scripts) and all relevant
boundry source files (optimize.py, binding_energy.py, relaxer.py,
interface_position_energetics.py, surface_area.py, interface.py, config.py).
Wrote a comprehensive analysis to `SCORING_ANALYSIS.md` at the repo root.

## Work Performed

### Flex-ddG Protocol Analysis
- Read `ddG-backrub.xml` (the core Rosetta protocol): identified the full
  pipeline of constraint addition, backrub ensemble generation, per-structure
  WT/mutant repacking+minimization, and InterfaceDdGMover scoring of 4 states
  (bound_wt, unbound_wt, bound_mut, unbound_mut).
- Read `analyze_flex_ddG.py`: extracted the GAM reweighting function and its
  7 per-term parameter pairs (fa_sol, hbond_sc, hbond_bb_sc, fa_rep, fa_elec,
  hbond_lr_bb, fa_atr), the SQL schema for score extraction, and the ensemble
  averaging methodology.
- Read `ddG-no_backrub_control.xml` and `run_example_1.py` for parameter
  defaults (35k backrub trials, 5k minimization iterations, 35 nstruct,
  talaris2014 score function with `-restore_talaris_behavior`).

### Boundry Scoring Analysis
- Read full source of `optimize.py` (1204 lines): traced the complete
  optimize workflow from CLI through alanine scan, beam expansion, parallel
  design+relax, binding energy scoring, and campaign selection.
- Read `binding_energy.py`: analyzed `calculate_binding_energy()` which
  computes dG = E_complex - sum(E_separated). Noted `relax_separated=False`
  default.
- Read `relaxer.py`: found the critical solvation model mismatch —
  `_relax_unconstrained()` always uses `amber14-all.xml + amber14/tip3pfb.xml`
  (no explicit waters = vacuum), while `get_energy_breakdown()` uses
  `amber14-all.xml + implicit/gbn2.xml` when `implicit_solvent=True` (default).
- Read `interface_position_energetics.py`: analyzed alanine scan and
  per-position dG computation. Confirmed both use `_compute_rosetta_dG()`
  which wraps `calculate_binding_energy()`.
- Read `surface_area.py`, `interface.py`, `config.py` for complete picture.

### Analysis Document
Wrote `SCORING_ANALYSIS.md` covering:
- Protocol overviews (12 sections)
- Energy function comparison (AMBER14 vs talaris2014)
- Solvation model mismatch (critical finding)
- Unbound-state treatment gap
- Backbone sampling differences
- Minimization protocol comparison
- Side-chain packing methodology
- ddG calculation formulas
- Interface definition
- Ranked summary of 13 misalignments (3 critical, 3 significant, 4 moderate, 3 minor)
- Prioritized recommendations in 3 phases
- Areas where boundry's approach is actually superior

## Key Decisions & Rationale
- **Decision**: Organized misalignments into critical/significant/moderate/minor tiers.
  **Why**: Not all differences are equally impactful. The solvation mismatch and
  unbound-state relaxation are fixable with small code changes and would yield
  the largest accuracy improvements. Ensemble averaging and backbone sampling
  are architecturally significant changes that should be planned separately.

## Issues & Blockers
None — this was a research/analysis session, not a code change session.

## Next Steps
1. Fix solvation model mismatch in `relaxer.py` (~5 lines: use implicit solvent
   in `_relax_unconstrained()` when `config.implicit_solvent` is True).
2. Enable `relax_separated=True` in optimize's scoring path
   (`_score_interface()` and `_execute_beam_expansion()`).
3. Apply position restraints during unconstrained minimization when
   `config.stiffness > 0`.
4. Consider multi-structure scoring (3-5 seeds averaged) for reduced noise.
5. Benchmark scoring changes against experimental ddG data to quantify improvement.
