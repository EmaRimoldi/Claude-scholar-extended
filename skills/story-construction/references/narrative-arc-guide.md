# Narrative Arc Guide

## The 4-Part Narrative Arc

Every strong research paper tells a story. The narrative arc structures that story into four parts that map directly to paper sections.

### Part 1: Setup (Known Context + Gap)

Establish what the field knows and where it falls short.

**What to include**:
- The broad problem area and why it matters
- What existing approaches can do
- The specific limitation, contradiction, or open question (the gap)

**Maps to**: Introduction paragraphs 1-3, Related Work

**Example (from Vaswani et al., 2017 -- Attention Is All You Need)**:
- Known context: Sequence transduction models use encoder-decoder with recurrent or convolutional layers
- Gap: Recurrence prevents parallelization and becomes a bottleneck at long sequence lengths

**Example (from Brown et al., 2020 -- GPT-3)**:
- Known context: Pre-trained language models fine-tuned on downstream tasks achieve strong results
- Gap: Fine-tuning requires task-specific datasets and modifies the model for each task

### Part 2: Question (What This Paper Asks)

State the specific question the reader should hold in mind.

**What to include**:
- A single, focused question or claim
- Why answering this question resolves the gap from Part 1

**Maps to**: Introduction final paragraph, Abstract

**Example (Vaswani et al.)**:
"Can a model based entirely on attention -- without recurrence or convolution -- achieve competitive sequence transduction?"

**Example (Brown et al.)**:
"Can scaling a language model enough enable it to perform tasks from just a few examples in context, without gradient updates?"

### Part 3: Evidence (Which Results Answer the Question)

Present the experimental chain that resolves the question.

**What to include**:
- The logical order of evidence (not the chronological order you ran experiments)
- Each result explicitly connected to the question
- Statistical support for each claim

**Maps to**: Results, Method

**Example (Vaswani et al.)**:
1. Transformer achieves new SOTA on WMT 2014 English-to-German (28.4 BLEU)
2. Training time is significantly shorter than recurrent models
3. Ablations show multi-head attention and positional encoding are both necessary

### Part 4: Implication (What This Means for the Field)

State why the answer matters beyond the specific experiments.

**What to include**:
- New understanding or capability enabled
- How this changes practice or opens new research directions
- Honest limitations that bound the implication

**Maps to**: Discussion, Abstract final sentence, Conclusion

**Example (Vaswani et al.)**:
"Attention-only architectures are viable for sequence transduction, enabling parallelizable training. This suggests attention can replace recurrence more broadly."

**Example (Brown et al.)**:
"Sufficient scale enables in-context learning -- task performance from examples alone -- which may reduce the need for task-specific fine-tuning."

## The "One Thing" Test

A well-constructed paper can be summarized in a single sentence:

- "This paper shows that [method/finding] achieves [result] by [mechanism], which means [implication]."

**Good examples**:
- "This paper shows that a pure attention architecture matches RNN performance on translation while training 10x faster, suggesting recurrence is not necessary for sequence transduction."
- "This paper shows that scaling language models to 175B parameters enables few-shot learning without fine-tuning, suggesting that in-context learning emerges from scale."

**If you cannot write this sentence**, the paper is trying to tell more than one story. Solutions:
1. Pick the strongest story and make the others supporting
2. Split into two papers
3. Find the unifying thread that connects the results

## Common Narrative Mistakes

### Mistake 1: Trying to Tell Too Many Stories

**Symptom**: The abstract has 4+ contributions that feel disconnected. The introduction lists contributions as bullet points with no narrative thread.

**Fix**: Pick the one result that most changes the reader's understanding. Make everything else support that result. If two results are equally important, find the unifying story or split.

### Mistake 2: Burying the Lead

**Symptom**: The most interesting finding appears in Section 4.3 of the results, mentioned briefly. The paper leads with a less interesting but "safer" contribution.

**Fix**: Restructure so the most important finding comes first. The narrative arc should build toward the strongest result, not save it for the end.

### Mistake 3: Weak or Missing Implication

**Symptom**: The discussion section restates the results without saying what they mean. The abstract ends with "our method achieves X% on Y benchmark."

**Fix**: Answer "so what?" explicitly. What should the reader do differently now? What new research does this enable? What belief should change?

### Mistake 4: Setup Without a Gap

**Symptom**: The introduction describes the field thoroughly but never articulates what is missing or wrong. The reader does not understand why this paper exists.

**Fix**: Every setup must end with a gap. The gap is the tension that the paper resolves. Without it, there is no story.

### Mistake 5: Evidence That Does Not Answer the Question

**Symptom**: The results section contains interesting experiments, but the reader cannot connect them to the question posed in the introduction.

**Fix**: For each result, write one sentence connecting it to the question. If you cannot, the result belongs in the appendix or a different paper.

## Adapting the Arc for Different Paper Types

### Method Paper

- **Setup**: Existing methods have limitation X
- **Question**: Can we design a method that removes limitation X while maintaining Y?
- **Evidence**: Our method achieves Y on benchmarks while resolving X (shown by ablation)
- **Implication**: This enables applications previously blocked by limitation X

### Analysis/Understanding Paper

- **Setup**: Phenomenon X is observed but not understood
- **Question**: What mechanism explains phenomenon X?
- **Evidence**: Controlled experiments isolate mechanism M as the driver (shown by intervention)
- **Implication**: Understanding M suggests how to improve/control X

### Benchmark Paper

- **Setup**: Field lacks a reliable way to evaluate capability X
- **Question**: Can we create a benchmark that measures X accurately and differentiates methods?
- **Evidence**: Our benchmark reveals differences invisible to existing benchmarks (shown by evaluation)
- **Implication**: The field can now make informed progress on X

### Negative Result Paper

- **Setup**: Approach X is widely believed to work for problem Y
- **Question**: Does approach X actually work for Y under rigorous evaluation?
- **Evidence**: Controlled experiments show X fails for Y (shown by systematic evaluation)
- **Implication**: The field should reconsider assumptions about X and invest in alternative approaches

### Systems Paper

- **Setup**: Current systems cannot handle requirement X at scale Y
- **Question**: Can we design a system that achieves X at scale Y?
- **Evidence**: Our system achieves X at scale Y with acceptable overhead (shown by benchmarks)
- **Implication**: Workloads previously infeasible at scale Y are now practical
