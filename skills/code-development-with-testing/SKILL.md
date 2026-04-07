---
name: code-development-with-testing
description: Orchestrates automatic test-driven code development for experiment pipelines. Writes code (data loaders, models, metrics), runs pre-flight validation + CPU smoke test, fixes failures automatically with Opus extended thinking, and retests in a loop until all tests pass.
version: 0.1.0
tags: [Development, Testing, TDD, Automation, Opus]
---

# Code Development with Testing

Automates the entire code-writing → test → fix → retest cycle for experiment components. Uses Opus with extended thinking to automatically diagnose failures and propose fixes, eliminating manual iteration.

## Core Loop

```
WRITE CODE → TEST (pre-flight + cpu-smoke) → PASS?
                    ↓ NO (max 5 iterations)
            OPUS DIAGNOSIS & FIX → RETEST
                    ↓
                  PASS?
                  /    \
                YES    NO (abort after 5 iterations)
```

## Three Components (In Order)

1. **experiment-data-builder** — Datasets, loaders, validation
   - Pre-flight: Config/import checks
   - CPU smoke: Load dataset, verify shapes, no NaN/Inf
   
2. **model-setup** — Models, forward pass, loss
   - Pre-flight: Model init, config override syntax
   - CPU smoke: Forward pass, gradient computation
   
3. **measurement-implementation** — Metrics, handles various shapes
   - Pre-flight: Metrics import, config loading
   - CPU smoke: Compute metrics on various input shapes

## Automatic Diagnosis

When tests fail, **Opus with extended thinking**:
- Analyzes error root cause
- Traces execution path
- Proposes specific fix
- Rates confidence (HIGH/MEDIUM/LOW)
- Provides rationale

## Success Criteria

- All 3 components write, test, and pass
- No timeout (pre-flight ≤30s, cpu-smoke ≤10min)
- Max 5 iterations per component

## Output

✅ Success: Ready-to-train codebase with all tests passing
❌ Failure: Diagnostic report with attempted fixes and recommendations

