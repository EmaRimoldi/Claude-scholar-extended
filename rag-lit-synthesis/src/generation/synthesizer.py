"""Literature synthesis generation: LLM-based and template-based fallback.

Generates a ~500-word summary of a topic using retrieved papers.
Three conditions:
  - C1/C2: retrieval-augmented (uses retrieved paper abstracts)
  - C3: no retrieval (generates from model knowledge alone)

Falls back to template-based generation if no GPU or model too large.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SynthesisResult:
    """Output of a synthesis generation."""
    text: str
    cited_paper_ids: list[str] = field(default_factory=list)
    method: str = ""  # "llm" or "template"
    model_name: str = ""
    condition: str = ""  # "bm25", "dense", "no_retrieval"


# --- Template-based synthesis (fallback, no GPU needed) ---

def template_synthesis(topic_name: str, retrieved_papers: list[dict],
                       condition: str) -> SynthesisResult:
    """Generate a structured summary by combining retrieved abstracts.

    This is the fallback when no LLM is available. It produces a deterministic,
    extractive summary by selecting key sentences from top retrieved papers.
    """
    if not retrieved_papers:
        return _no_retrieval_template(topic_name, condition)

    sections = []
    cited_ids = []

    # Introduction
    sections.append(
        f"This review surveys recent work on {topic_name}, covering "
        f"{len(retrieved_papers)} relevant papers from the literature."
    )

    # Group papers and extract key content
    sections.append("\n## Key Approaches and Findings\n")
    for i, paper in enumerate(retrieved_papers[:10]):
        title = paper.get("title", "Unknown")
        abstract = paper.get("abstract", "")
        authors = paper.get("authors", [])
        year = paper.get("year", "")
        pid = paper.get("paper_id", "")

        # Extract first 2 sentences as key contribution
        sentences = [s.strip() for s in abstract.split(". ") if len(s.strip()) > 20]
        key_content = ". ".join(sentences[:2]) + "." if sentences else abstract[:200]

        author_str = authors[0] if authors else "Unknown"
        if len(authors) > 1:
            author_str += " et al."

        sections.append(
            f"[{author_str}, {year}] ({title}): {key_content}"
        )
        if pid:
            cited_ids.append(pid)

    # Summary statistics
    years = [p.get("year", 0) for p in retrieved_papers if p.get("year")]
    if years:
        sections.append(
            f"\nThe surveyed papers span {min(years)}-{max(years)}, "
            f"reflecting active research in {topic_name}."
        )

    # Limitations
    sections.append(
        f"\n## Limitations and Open Questions\n"
        f"While significant progress has been made in {topic_name}, "
        f"several challenges remain. The field would benefit from more "
        f"standardized benchmarks and reproducible evaluation protocols."
    )

    text = "\n".join(sections)
    return SynthesisResult(
        text=text,
        cited_paper_ids=cited_ids,
        method="template",
        model_name="template-extractive",
        condition=condition,
    )


def _no_retrieval_template(topic_name: str, condition: str) -> SynthesisResult:
    """Baseline template with no retrieved papers."""
    text = (
        f"This review discusses {topic_name}. "
        f"Without access to specific retrieved documents, this summary "
        f"provides a general overview based on common knowledge in the field. "
        f"The topic of {topic_name} has seen significant recent interest "
        f"in the machine learning and natural language processing communities. "
        f"Key challenges include scalability, evaluation methodology, and "
        f"reproducibility of results across different experimental settings."
    )
    return SynthesisResult(
        text=text,
        cited_paper_ids=[],
        method="template",
        model_name="template-baseline",
        condition=condition,
    )


# --- LLM-based synthesis ---

RAG_PROMPT = """You are an expert scientific reviewer. Write a ~500-word literature review on: {topic}

Use ONLY the following retrieved papers as sources. Cite each paper as [Author, Year].

Retrieved papers:
{passages}

Write a structured review covering:
1. Key approaches and methods
2. Main findings
3. Limitations and open questions

Review:"""

NO_RETRIEVAL_PROMPT = """You are an expert scientific reviewer. Write a ~500-word literature review on: {topic}

Based on your knowledge, cover:
1. Key approaches and methods
2. Main findings
3. Limitations and open questions

Cite papers you know using [Author, Year] format.

Review:"""


def _format_papers_for_prompt(papers: list[dict]) -> str:
    parts = []
    for i, p in enumerate(papers, 1):
        authors = p.get("authors", [])
        author_str = authors[0] if authors else "Unknown"
        if len(authors) > 1:
            author_str += " et al."
        parts.append(
            f"[{i}] {author_str} ({p.get('year', '')}). {p.get('title', '')}\n"
            f"    Abstract: {p.get('abstract', '')[:500]}\n"
        )
    return "\n".join(parts)


def _try_load_llm():
    """Try to load a small LLM. Returns (model, tokenizer, model_name) or None."""
    import torch
    if not torch.cuda.is_available():
        logger.info("No GPU available, using template fallback")
        return None

    vram_gb = torch.cuda.get_device_properties(0).total_mem / (1024**3)
    logger.info(f"GPU VRAM: {vram_gb:.1f} GB")

    # Try models in order of preference (smallest first)
    candidates = [
        ("google/flan-t5-large", "seq2seq", 3.0),   # ~3GB, fits anywhere
        ("google/flan-t5-xl", "seq2seq", 8.0),       # ~8GB
    ]

    for model_name, model_type, min_vram in candidates:
        if vram_gb >= min_vram:
            try:
                logger.info(f"Loading {model_name}...")
                if model_type == "seq2seq":
                    from transformers import T5ForConditionalGeneration, AutoTokenizer
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = T5ForConditionalGeneration.from_pretrained(
                        model_name,
                        torch_dtype=torch.float16,
                        device_map="auto",
                    )
                else:
                    from transformers import AutoModelForCausalLM, AutoTokenizer
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch.float16,
                        device_map="auto",
                    )
                logger.info(f"Loaded {model_name} successfully")
                return model, tokenizer, model_name, model_type
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
                continue

    logger.info("No LLM fits in VRAM, using template fallback")
    return None


def llm_synthesis(topic_name: str, retrieved_papers: list[dict],
                  condition: str, model_bundle=None) -> SynthesisResult:
    """Generate synthesis using an LLM with retrieved context."""
    import torch

    if model_bundle is None:
        model_bundle = _try_load_llm()

    if model_bundle is None:
        return template_synthesis(topic_name, retrieved_papers, condition)

    model, tokenizer, model_name, model_type = model_bundle

    # Build prompt
    if retrieved_papers:
        passages_text = _format_papers_for_prompt(retrieved_papers)
        prompt = RAG_PROMPT.format(topic=topic_name, passages=passages_text)
    else:
        prompt = NO_RETRIEVAL_PROMPT.format(topic=topic_name)

    # Truncate prompt to fit model context
    max_input_tokens = 1024 if "t5" in model_name.lower() else 2048
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True,
                       max_length=max_input_tokens).to(model.device)

    with torch.no_grad():
        if model_type == "seq2seq":
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.3,
                do_sample=True,
                top_p=0.9,
                num_beams=1,
            )
            generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        else:
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.3,
                do_sample=True,
                top_p=0.9,
            )
            generated = tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True,
            )

    # Extract cited paper IDs by matching titles in generated text
    cited_ids = []
    gen_lower = generated.lower()
    for p in (retrieved_papers or []):
        # Check if any significant part of the title appears in the output
        title_words = p.get("title", "").lower().split()
        if len(title_words) >= 3:
            # Check if 3+ consecutive title words appear
            for j in range(len(title_words) - 2):
                trigram = " ".join(title_words[j:j+3])
                if trigram in gen_lower:
                    cited_ids.append(p["paper_id"])
                    break

    return SynthesisResult(
        text=generated,
        cited_paper_ids=cited_ids,
        method="llm",
        model_name=model_name,
        condition=condition,
    )
