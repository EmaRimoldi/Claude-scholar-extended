# Search Strategy Guide

## Platform-Specific Query Construction

### Semantic Scholar

**Strengths**: Good at finding exact phrases, structured API, reliable metadata
**Best for**: Finding closely related methods and applications

**Query format**:
- Use quoted phrases for exact matching: `"cross-subject" "EEG" "contrastive"`
- Add year filter: `year:2025-2026`
- Use field-of-study filter when available

**Tips**:
- Start broad, then narrow based on result volume
- Check the "highly influential citations" for each result
- Look at the "related papers" sidebar for papers you might have missed

### arXiv

**Strengths**: Most recent preprints, often months before conference publication
**Best for**: Catching concurrent work before it appears in venues

**Query format**:
- URL: `https://arxiv.org/search/?query=TERMS&searchtype=all&order=-announced_date_first`
- Use `+` between terms for AND
- Sort by date (newest first) to catch recent work

**Tips**:
- Check both cs.LG and cs.AI categories
- Also check domain-specific categories (cs.CL for NLP, eess.SP for signal processing)
- Look at the "new submissions" page for your categories daily during critical periods

### Google Scholar

**Strengths**: Broadest coverage including workshops, theses, and reports
**Best for**: Comprehensive landscape check

**Query format**:
- Use quotes for exact phrases: `"contrastive learning" "EEG"`
- Use `after:YYYY` for date filtering
- Use `site:arxiv.org` to restrict to preprints

**Tips**:
- Results are ranked by relevance, not date — check multiple pages
- "Cited by" and "Related articles" links are useful for snowballing
- Set up Google Scholar Alerts for ongoing monitoring after the check

## Query Construction Strategy

### Step 1: Core Terms
Extract 3-5 core terms from your contribution:
- Method: "contrastive learning", "domain adversarial"
- Domain: "EEG", "brain-computer interface"
- Task: "cross-subject", "transfer learning"

### Step 2: Variant Combinations
Generate 3-5 queries by combining core terms differently:
- Query 1: Method + Domain (broadest)
- Query 2: Method + Task (catches different domains using same approach)
- Query 3: Domain + Task (catches different methods for same problem)
- Query 4: All three (most specific, fewest results)
- Query 5: Synonyms for key terms

### Step 3: Date Filtering
- For pre-submission checks: last 3-6 months
- For project start checks: last 1-2 years
- For comprehensive reviews: last 3-5 years

## Interpreting Results

### False Positives (looks competitive but isn't)
- Same keywords but fundamentally different approach
- Same method but completely different domain with no overlap
- Survey or review papers that mention both topics

### True Positives (actually competitive)
- Same method + same domain + same task
- Same method + same task + closely related domain
- Different method but same claim about the same benchmark
