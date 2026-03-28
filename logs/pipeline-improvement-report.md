# Pipeline Improvement Report

**Date**: 2026-03-28
**Trigger**: Expert review identified 8 systematic weaknesses in generated paper

## Changes Summary

### New Pipeline Components

| Component | Type | Purpose |
|-----------|------|---------|
| `/quality-review` | Command | Quality gate (8 dimensions, scores 1-10, BLOCKS if any < 5) |
| `paper-quality-check` | Skill | Reusable quality audit at any pipeline stage |
| Step 17 in pipeline | Pipeline state | quality-review between produce-manuscript and compile-manuscript |

### Updated Commands (6 commands modified)

| Command | Changes |
|---------|---------|
| `/design-experiments` | Added: statistical rigor requirements (min 5 seeds, mandatory tests), baseline completeness checklist, metric-claim alignment check, threat-to-validity analysis |
| `/implement-metrics` | Added: metric coverage validation, faithfulness metrics catalog (comprehensiveness, sufficiency, AOPC), cross-reference with research question keywords |
| `/analyze-results` | Added: mandatory statistical tests (bootstrap, CI, Cohen's d), contradiction detection, error analysis (per-class stratification), results health check |
| `/map-claims` | Added: claim-evidence consistency gate, title keyword audit, require both supporting AND contradicting evidence, honest framing of negative results |
| `/story` | Added: devil's advocate review, top 5 hostile reviewer objections, address-or-flag-as-limitation requirement |
| `/produce-manuscript` | Added: pre-generation verification gates (abstract audit, title audit, contribution audit), BLOCK on unsupported claims |

### Weakness → Fix Mapping

| Weakness | Root Fix | Gate Added |
|----------|----------|------------|
| W1: No faithfulness metrics | `/design-experiments` metric-claim alignment, `/implement-metrics` coverage validation | BLOCKS if RQ keyword has no metric |
| W2: Only 3 seeds | `/design-experiments` min 5 seeds, `/analyze-results` seed count warning | WARNS if < 5, BLOCKS claim without stats |
| W3: No IG comparison | `/design-experiments` baseline completeness checklist | BLOCKS if no alternative explanation method |
| W4: Single dataset | `/design-experiments` multi-dataset requirement | FLAGS as limitation if not addressed |
| W5: No adversarial test | `/design-experiments` threat-to-validity, baseline checklist | BLOCKS "faithful" claim without causal test |
| W6: Contradicted contribution | `/map-claims` consistency gate, `/analyze-results` contradiction detection | BLOCKS overclaimed contribution |
| W7: No error analysis | `/analyze-results` mandatory stratification | REQUIRES per-class + 1 other dimension |
| W8: Abstract overclaims | `/produce-manuscript` abstract audit | BLOCKS abstract claims without data |

### Pipeline Step Count

19 steps (was 18, added quality-review as step 17):
```
1-2: Research ideation & competition
3: Design experiments (enhanced with quality gates)
4-7: Implementation (enhanced metric coverage)
8-9: Validation & compute
10-12: Execution, collection, analysis (enhanced with stats)
13-15: Claims, positioning, story (enhanced with honesty checks)
16: Manuscript production (enhanced with verification gates)
17: Quality review (NEW — blocks if quality insufficient)
18: Compile manuscript
19: Rebuttal
```
