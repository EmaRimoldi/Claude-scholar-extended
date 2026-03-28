"""Literature synthesis generation using LLMs with retrieved passages."""

from dataclasses import dataclass
from typing import Optional

from ..registry import register
from ..retrieval.retrievers import RetrievedPassage


@dataclass
class SynthesisOutput:
    """Generated literature synthesis with metadata."""
    text: str
    cited_paper_ids: list[str]
    model_name: str
    prompt_type: str
    num_retrieved: int
    generation_config: dict


ZERO_SHOT_TEMPLATE = """You are an expert scientific reviewer. Write a comprehensive literature review section on the topic: {topic}

Use ONLY the following retrieved passages as sources. For each claim, cite the source using [Author, Year] format. Do not include any paper you cannot find in the provided passages.

Retrieved passages:
{passages}

Write a well-structured review covering:
1. Key approaches and methods
2. Main findings and results
3. Limitations of current work
4. Open research questions

Review:"""

FEW_SHOT_TEMPLATE = """You are an expert scientific reviewer writing a literature review.

Example of a well-cited review paragraph:
"Recent advances in retrieval-augmented generation have shown promising results for knowledge-intensive tasks [Gao et al., 2024]. The core idea is to combine a retriever that finds relevant documents with a generator that synthesizes information from them [Lewis et al., 2020]. However, hallucination remains a challenge even with retrieval, as models may generate claims not supported by the retrieved passages [Shuster et al., 2021]."

Now write a comprehensive literature review on: {topic}

Use ONLY the following retrieved passages. Cite every claim with [Author, Year].

Retrieved passages:
{passages}

Review:"""

COT_TEMPLATE = """You are an expert scientific reviewer. Your task is to write a literature review on: {topic}

Retrieved passages:
{passages}

Before writing, think step by step:
1. First, identify the main themes across the passages
2. Group papers by theme
3. For each theme, identify agreements, disagreements, and gaps
4. Plan the structure of your review

Now write the review, citing each claim with [Author, Year]:"""


TEMPLATES = {
    "zero_shot": ZERO_SHOT_TEMPLATE,
    "few_shot": FEW_SHOT_TEMPLATE,
    "cot": COT_TEMPLATE,
}


def format_passages(passages: list[RetrievedPassage]) -> str:
    """Format retrieved passages for the prompt."""
    parts = []
    for i, p in enumerate(passages, 1):
        parts.append(f"[{i}] Title: {p.title}\nPaper ID: {p.paper_id}\nText: {p.text}\n")
    return "\n".join(parts)


@register("generator", "llm_synthesizer")
class LLMSynthesizer:
    """Generate literature synthesis using an LLM."""

    def __init__(self, model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
                 temperature: float = 0.3, max_tokens: int = 4096):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """Lazy-load the model."""
        if self._model is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        )

    def generate(self, topic: str, passages: list[RetrievedPassage],
                 prompt_type: str = "few_shot") -> SynthesisOutput:
        """Generate a literature synthesis."""
        self._load_model()

        template = TEMPLATES.get(prompt_type, TEMPLATES["few_shot"])
        formatted_passages = format_passages(passages)
        prompt = template.format(topic=topic, passages=formatted_passages)

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            do_sample=True,
            top_p=0.9,
        )
        generated = self._tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

        cited_ids = [p.paper_id for p in passages if p.title.lower() in generated.lower()]

        return SynthesisOutput(
            text=generated,
            cited_paper_ids=cited_ids,
            model_name=self.model_name,
            prompt_type=prompt_type,
            num_retrieved=len(passages),
            generation_config={"temperature": self.temperature, "max_tokens": self.max_tokens},
        )


@register("generator", "no_retrieval")
class NoRetrievalSynthesizer:
    """Generate literature synthesis without retrieval (baseline)."""

    NO_RETRIEVAL_TEMPLATE = """You are an expert scientific reviewer. Write a comprehensive literature review on: {topic}

Cover key approaches, main findings, limitations, and open questions. Cite papers using [Author, Year] format based on your knowledge.

Review:"""

    def __init__(self, model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
                 temperature: float = 0.3, max_tokens: int = 4096):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        if self._model is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        )

    def generate(self, topic: str) -> SynthesisOutput:
        """Generate synthesis without retrieval."""
        self._load_model()

        prompt = self.NO_RETRIEVAL_TEMPLATE.format(topic=topic)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            do_sample=True,
            top_p=0.9,
        )
        generated = self._tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

        return SynthesisOutput(
            text=generated,
            cited_paper_ids=[],
            model_name=self.model_name,
            prompt_type="no_retrieval",
            num_retrieved=0,
            generation_config={"temperature": self.temperature, "max_tokens": self.max_tokens},
        )
