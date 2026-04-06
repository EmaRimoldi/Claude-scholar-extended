# Pipeline Completion Checklist

## ✅ Completed (as of 2026-04-06)

### Research Phase (Steps 1-8)
- [x] research-landscape — broad territory mapping
- [x] cross-field-search — adjacent fields identification
- [x] formulate-hypotheses — hypothesis generation
- [x] claim-search — atomic claim decomposition
- [x] citation-traversal — citation graph traversal
- [x] adversarial-search — novelty claim stress testing
- [x] novelty-gate N1 — full novelty evaluation (PROCEED)
- [x] recency-sweep 1 — concurrent work check

### Design Phase (Steps 9-10)
- [x] design-experiments — experiment plan with baselines
- [x] design-novelty-check — N2 gate (design validates novelty claim)

### Implementation Phase (Steps 11-15)
- [x] scaffold — project structure generation
- [x] build-data — dataset loaders
- [x] setup-model — model configuration
- [x] implement-metrics — metrics and statistical tests
- [x] validate-setup — pre-flight validation (5/5 checks pass)

### Cluster Preparation (Steps 16-17)
- [x] download-data — data cached on cluster
- [x] plan-compute — GPU estimation and SLURM scripts

## 🔄 In Progress (as of 2026-04-06)

### Execution Phase (Step 18: run-experiment)
- [x] Phase 0: Data analysis (rationale sparsity, agreement)
- [x] Phase 1: Head importance scoring (Gate G1: WARN → PROCEED)
- [ ] Phase 2 Wave 1: Training M0, M1, M3, M4b
  - Jobs submitted: 11464115, 11464117
  - Status: PENDING (awaiting cluster resources)
  - ETA: ~9 hours each
- [ ] Phase 2 Wave 2: Training M2, M4a, M4c, M5, M6, M7
  - Status: Ready for auto-submit after Wave 1

### Analysis Phase (Steps 19-25)
- [ ] Phase 3: Attribution analysis (IG, LIME, stability) — READY
- [ ] Phase 4: Statistics (bootstrap, power analysis, tests) — READY
- [ ] Phase 5: Adversarial (attention swap, IG agreement) — READY
- [ ] collect-results — aggregate metrics across conditions/seeds
- [ ] analyze-results — statistical analysis and hypothesis outcomes
- [ ] gap-detection — missing ablations (inline)
- [ ] novelty-gate N3 — post-results novelty re-evaluation
- [ ] recency-sweep 2 — concurrent work during execution

## 📋 Ready to Execute (Steps 20-38)

### Results & Novelty Re-evaluation
- [ ] literature-rescan — contextualize results with literature
- [ ] method-code-reconciliation — verify implementation vs. methods section
- [ ] novelty-gate N3 — re-evaluate novelty with actual results
- [ ] recency-sweep 2 — check for concurrent work

### Manuscript Writing (Steps 26-34)
- [ ] map-claims — claim-evidence architecture
- [ ] position — contribution positioning
- [ ] story — narrative arc and figure plan
- [ ] narrative-gap-detect — check narrative completeness
- [ ] argument-figure-align — ensure figures serve claims
- [ ] produce-manuscript — full prose generation
- [ ] cross-section-consistency — 5-check consistency verification
- [ ] claim-source-align — verify all claims are traced

### Quality & Finalization (Steps 35-38)
- [ ] verify-paper — 7-dimensional quality check (45 criteria)
- [ ] adversarial-review — 3 hostile simulated reviewers
- [ ] recency-sweep final — final concurrent work check (48h before submission)
- [ ] novelty-gate N4 — final novelty confirmation
- [ ] compile-manuscript — LaTeX → PDF, chktex

## 🔧 Critical Blockers Resolved

| Issue | Resolution | Status |
|-------|-----------|--------|
| `evaluation_strategy` TypeError | Changed to `eval_strategy` | ✅ Fixed |
| Hydra override syntax | Verified `experiment=name` (not `+experiment=`) | ✅ OK |
| Model weight loading | Confirmed working with ignore_mismatched_sizes | ✅ OK |
| Transformers version | Validated with 5.4.0 (supports eval_strategy) | ✅ OK |
| Validation script | All 5 checks pass ✅ | ✅ OK |
| Training job submission | Jobs 11464115, 11464117 submitted | ✅ OK |

## 📦 Deliverables

### Experiment Outputs
- [ ] outputs/M0/, M1/, M3/, M4b/ — Wave 1 training results
- [ ] outputs/M2/, M4a/, M4c/, M5/, M6/, M7/ — Wave 2 training results
- [ ] outputs/phase3/ — attribution analysis summary
- [ ] outputs/phase4/ — statistical analysis summary
- [ ] outputs/phase5/ — adversarial analysis summary

### Results Tables
- [ ] results/metrics_by_seed.csv — all metrics per condition and seed
- [ ] results/metrics_aggregated.csv — statistics per condition
- [ ] results/metrics_summary.json — full metrics JSON

### Manuscript
- [ ] manuscript/ — full LaTeX source
- [ ] manuscript/main.pdf — compiled PDF
- [ ] manuscript/figures/ — all figures (SVG/PNG)
- [ ] manuscript/tables/ — all tables
- [ ] supplementary/ — supplementary materials (if needed)

## 🚀 Estimated Timeline from Job Start

| Stage | Duration | Completion |
|-------|----------|------------|
| Wave 1 training | 9 hours | 2026-04-07 ~00:00 EDT |
| Wave 2 training | 9 hours | 2026-04-07 ~09:00 EDT |
| Phases 3-5 analysis | 4-6 hours | 2026-04-07 ~14:00 EDT |
| Manuscript writing | 4-8 hours | 2026-04-07 ~18:00 EDT |
| **Total pipeline** | **~26-32 hours** | **2026-04-07 18:00 EDT** |

## ✅ Go/No-Go Criteria

### Pre-Wave-1
- [x] Code validation: 5/5 checks pass
- [x] Jobs submitted: 11464115, 11464117
- [x] Wave 2 scripts ready
- [x] Phase 3-5 scripts ready

### Pre-Wave-2 (after Wave 1)
- [ ] Wave 1 outputs complete (M0, M1, M3, M4b with 3 seeds each)
- [ ] Gate G2 passed: M4b val IoU-F1 > M1 val IoU-F1 - 0.02
- [ ] No training errors or NaNs

### Pre-Analysis (after Wave 2)
- [ ] All Wave 1+2 training complete
- [ ] All output directories have expected structure
- [ ] Checkpoint files exist for all conditions/seeds

### Pre-Manuscript (after analysis)
- [ ] Phase 3-5 outputs complete
- [ ] Metrics aggregated without errors
- [ ] Novelty re-assessment ready

### Pre-Submission
- [ ] Manuscript completed and proofread
- [ ] All figures and tables generated
- [ ] Quality verification passed (45/45 criteria)
- [ ] Adversarial review responses prepared
- [ ] Concurrent work check complete

## 📞 Support Commands

```bash
# Check job status
squeue -j 11464115,11464117

# Monitor logs
tail -f logs/sparse-hate_11464115.out
tail -f logs/sparse-hate_11464117.out

# After Wave 1, run remaining phases
./scripts/run_remaining_pipeline.sh

# Check results
ls -la results/
cat results/metrics_by_seed.csv
```

## Notes

- All phases validated and ready ✅
- Code fixes confirmed and tested ✅
- SLURM jobs submitted successfully ✅
- Recovery documentation complete ✅
- Next: Monitor Wave 1 execution and run Wave 2 auto-submit

**Status**: Pipeline recovered and ready for autonomous execution
**Last updated**: 2026-04-06 14:17 EDT
