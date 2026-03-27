# Decision Framework for Hypothesis Revision

## The Three Decisions

### Persevere: Same Hypothesis, Adjusted Execution

**When to persevere**:
- Diagnosis points to a fixable issue (hyperparameters, data, implementation bug)
- The effect is present but smaller than expected (partial confirmation)
- There is remaining budget to try the fix
- The fix is well-defined and low-risk

**Persevere checklist**:
- [ ] Diagnosis identified a specific fixable cause
- [ ] The fix is concrete (not "try harder")
- [ ] Estimated cost of the fix is < 30% of remaining budget
- [ ] This is not the 3rd+ persevere on the same hypothesis

### Pivot: Revised Hypothesis

**When to pivot**:
- Original hypothesis was partially right but needs refinement
- Diagnosis revealed an unexpected finding that suggests a better direction
- A weaker but real effect was found — can build on it
- The core idea has merit but the specific formulation was wrong

**Pivot checklist**:
- [ ] Can articulate specifically what changed from H_n to H_n+1
- [ ] New hypothesis is informed by evidence (not just a new guess)
- [ ] New hypothesis is still falsifiable with clear success criteria
- [ ] Remaining budget supports at least one more full experiment cycle

### Abandon: Stop This Line

**When to abandon**:
- Multiple iterations failed to show any signal
- Evidence strongly suggests the fundamental approach does not work
- Remaining budget is insufficient for another meaningful iteration
- Deadline makes further iteration impossible
- A competing paper was published that undermines the contribution

**Abandon checklist**:
- [ ] At least 2 iterations attempted (avoid premature abandonment)
- [ ] Diagnosis explored all major failure modes
- [ ] Decision is based on evidence, not frustration
- [ ] What was learned is documented for future reference

## Resource-Aware Decision-Making

### Budget Heuristic

| Remaining Budget | Recommended Action |
|---|---|
| > 50% | Full flexibility: pivot, persevere, or new experiments |
| 25-50% | One more iteration: persevere with targeted fix or pivot to simpler hypothesis |
| 10-25% | Write up what you have: claim the confirmed results, hedge the rest |
| < 10% | Stop experimenting: focus on analysis and writing |

### Deadline Heuristic

| Time to Deadline | Recommended Action |
|---|---|
| > 6 weeks | Full flexibility |
| 3-6 weeks | One more iteration, then write |
| 1-3 weeks | No new experiments — write with what you have |
| < 1 week | Polish and submit |

## Common Decision Mistakes

1. **Sunk cost fallacy**: Continuing because "we've already spent 500 GPU-hours" rather than because evidence supports continuing
2. **Premature abandonment**: Giving up after one failed configuration without proper diagnosis
3. **Infinite persevere loop**: Always finding "one more thing to try" without clear termination criteria
4. **Pivot without learning**: Changing direction without understanding why the previous direction failed
5. **Abandoning too late**: Spending 90% of budget before admitting the approach does not work
6. **Not documenting**: Failing to record what was learned, making the same mistakes in the next project
