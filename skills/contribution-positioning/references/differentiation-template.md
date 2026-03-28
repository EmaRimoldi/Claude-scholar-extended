# Differentiation Framework Guide

## The 5-Dimension Comparison Framework

Compare each closest work along five dimensions that capture how two papers differ.

### Dimension 1: Research Question

- **Same question, different answer**: Strongest positioning -- "We address the same challenge through a different lens"
- **Related question, different scope**: Position as complementary -- "While [X] studies [narrow], we examine [broader]"
- **Same question, same framing**: Hardest to differentiate -- focus on dimensions 2-5

**Write** a 1-2 sentence comparative statement. Example: "Kostas et al. ask whether domain adaptation can reduce calibration, while we ask whether pre-training can eliminate it entirely."

### Dimension 2: Method

- **Component-level**: Specific module, loss, or architecture choice that differs
- **Paradigm-level**: Different learning paradigm (supervised vs. self-supervised)
- **Engineering vs. insight**: Technical choice vs. different understanding of the problem

**Write** the specific technical delta. Avoid "improved" or "enhanced." Example: "Where Zhao et al. use MMD alignment, we replace it with a contrastive loss on temporal segments."

### Dimension 3: Models / Data

- **Dataset coverage**: Different benchmarks, domains, or scales
- **Model architecture**: Different backbone, capacity, or modality
- **Setting differences**: Online vs. offline, few-shot vs. full-data

**Write** what is shared and what differs. Example: "Both evaluate on BCI-IV-2a, but we add MOABB and a clinical dataset."

### Dimension 4: Key Findings

- **Complementary**: Their findings and yours tell a coherent story together
- **Contradictory**: Your results challenge their conclusions -- explain why
- **Deeper**: You reproduce their result and go further

**Write** what the reader learns from your paper that they could not learn from the prior work.

### Dimension 5: Limitation Addressed

- **Explicit**: Stated in their "limitations" or "future work" section
- **Implicit**: Obvious to the community but not stated by the authors
- **Scope**: Works in setting A but not B; you address B

**Write** the limitation precisely. Example: "Zhang et al. note their approach requires 50 calibration trials; ours requires zero."

## Differentiation Matrix Template

```markdown
### vs. [Author et al., YEAR] -- "[Paper Title]"

| Dimension | [Author et al.] | Our Work | Comparative Statement |
|---|---|---|---|
| Research Question | [What they ask] | [What we ask] | [How questions differ] |
| Method | [Their approach] | [Our approach] | [Specific technical delta] |
| Models / Data | [Their setup] | [Our setup] | [Coverage difference] |
| Key Findings | [Their results] | [Our results] | [New knowledge provided] |
| Limitation Addressed | [Their limitation] | [How we address it] | [Why it matters] |
```

Repeat for each of the 3-5 closest works.

## Contribution Statement Formula

### Core Formula

> "While [prior work] showed [X], our work [Y], revealing [Z]."

- **[prior work]**: Most relevant prior result or state of knowledge
- **[X]**: What was known before (accurately stated)
- **[Y]**: What your work does differently
- **[Z]**: What new understanding the community gains

### Variant Formulas

**Method-first**: "We introduce [method], which unlike [prior approaches], [does Y]. On [benchmark], this yields [result], demonstrating [insight]."

**Finding-first**: "We find that [surprising result], challenging the assumption that [prior belief]. This is achieved by [method], which [key mechanism]."

**Problem-first**: "Existing approaches to [problem] require [limitation]. We show that [alternative] eliminates this while [maintaining performance], suggesting [broader insight]."

### Anti-Patterns

- **Component listing**: "We propose X, Y, and Z" -- describes what you built, not what you contribute
- **Performance-only**: "We achieve SOTA on [benchmark]" -- numbers without insight
- **Vague novelty**: "We present a novel approach" -- "novel" is for reviewers to decide
- **Overclaiming scope**: "We solve [broad problem]" when you address a specific setting

## Reviewer Objection Patterns and Responses

### "Incremental over [X]"

**Trigger**: Small method delta, similar setup, comparable numbers.

**Strategy**: Emphasize qualitative difference in findings, not just method. Highlight the limitation of [X] you address.

**Template**: "While the method builds upon [X], the key contribution is not [component] but the finding that [insight]. [X] does not examine [aspect], and our results show [what changes]."

### "Limited evaluation"

**Trigger**: Few datasets, metrics, or small scale.

**Strategy**: Justify dataset choice for the claim. Offer additional experiments if feasible.

**Template**: "We chose [datasets] as standard benchmarks for [setting], enabling comparison with [baselines]. We have added [experiment] in the revision."

### "Unclear novelty vs. [Y]"

**Trigger**: Overlapping contribution with a known paper.

**Strategy**: Side-by-side comparison table. Acknowledge overlap, state delta clearly.

**Template**: "We provide a comparison in Table R1. Key differences: (1) [dim], (2) [dim]. While [Y] focuses on [X], we address [Z], leading to [unique insight]."

### "Missing comparison with [Z]"

**Trigger**: Absent relevant baseline.

**Strategy**: Add comparison if applicable. If not comparable, explain why. Never dismiss the concern.

**Template**: "[If added] We include this in revised Table X. [If not applicable] [Z] addresses [different setting], making direct comparison not straightforward. We discuss the relationship in Section X."

## Handling Special Cases

### Concurrent Work

- Acknowledge explicitly in related work; state independent development
- Frame as mutual validation if results are similar
- Explain methodological differences if results differ

### Incremental-Seeming Contributions

Reframe around:
- **Insight over method**: "The contribution is the finding that [insight], not component X itself"
- **Analysis over numbers**: "Beyond accuracy, we provide evidence that [understanding]"
- **Scope over delta**: "Consistency across [N settings] suggests [principle]"

### Negative Results as Contributions

Strong when they challenge a widely held assumption, save the community from a dead end, or reveal failure in an important setting.

**Positioning**: "Contrary to [prior work], we find [method] does not [expected benefit] in [setting]. Our analysis identifies [root cause], suggesting [implication]."
