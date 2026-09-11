"""
rag.py
Retrieval-grounded explanations for each finding.

Design choice, on purpose: retrieval is keyword-based, not embeddings,
so the tool has zero required external dependencies and zero required
API keys to run. Every explanation is grounded in a knowledge_base/*.md
file and always carries that file's source_url as a citation.

If GEMINI_API_KEY is set, generation is upgraded to a Gemini call that
is instructed to use ONLY the retrieved chunk as context (grounded
generation). Without a key, the tool falls back to a deterministic
template built directly from the retrieved chunk - so the tool is
fully usable, and fully inspectable, with no API key at all.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .cost_tracker import log_cost

KB_DIR = Path(__file__).parent.parent / "knowledge_base"

_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is",
    "it", "this", "that", "be", "as", "with", "your", "you", "will",
}


@dataclass
class KBDoc:
    doc_id: str
    title: str
    source_url: str
    body: str


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z_]{3,}", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def load_knowledge_base() -> dict[str, KBDoc]:
    docs: dict[str, KBDoc] = {}
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text()
        doc_id = _extract_field(text, "id") or path.stem
        title = _extract_field(text, "title") or path.stem
        source_url = _extract_field(text, "source_url") or ""
        body = text.split("\n\n", 1)[-1].strip()
        docs[doc_id] = KBDoc(doc_id, title, source_url, body)
    return docs


def _extract_field(text: str, field: str) -> str | None:
    m = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def retrieve(topic: str, kb: dict[str, KBDoc]) -> KBDoc | None:
    # doc_topic from the classifier maps 1:1 to a doc id - this is the
    # "retrieval" step for now. Swap for real embedding similarity search
    # once there's a large enough corpus that keyword/topic lookup breaks down.
    return kb.get(topic)


def explain(topic: str, finding_line: str, kb: dict[str, KBDoc]) -> str:
    doc = retrieve(topic, kb)
    if doc is None:
        return "No matching guidance found in the knowledge base for this finding."

    # Provider priority: Gemini (if key present) -> Groq (if key present) ->
    # deterministic offline template. Both providers get the exact same
    # grounded prompt, so swapping providers doesn't change *what* is
    # generated, only which model generates it.
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    if gemini_key:
        try:
            return _explain_with_gemini(finding_line, doc, gemini_key)
        except Exception as exc:  # network/SDK errors shouldn't kill a scan
            return _explain_template(doc) + f"\n(Gemini generation unavailable: {exc})"

    if groq_key:
        try:
            return _explain_with_groq(finding_line, doc, groq_key)
        except Exception as exc:
            return _explain_template(doc) + f"\n(Groq generation unavailable: {exc})"

    return _explain_template(doc)


def _build_prompt(finding_line: str, doc: KBDoc) -> str:
    return (
        "You are a migration assistant. Explain in 2-3 sentences, in plain "
        "language, what the developer should do about the code line below. "
        "Use ONLY the CONTEXT provided - do not add facts that aren't in it. "
        "End your answer with a citation in the form (source: <title>).\n\n"
        f"CODE LINE:\n{finding_line}\n\n"
        f"CONTEXT (title: {doc.title}):\n{doc.body}\n"
    )


def _explain_template(doc: KBDoc) -> str:
    # Deterministic, no-API-key fallback - a cited summary of the retrieved
    # chunk. Uses the first TWO sentences, not just one: some docs (e.g.
    # secret_key_rotation.md) put the actual required action in the second
    # sentence, and a one-sentence summary was silently dropping it - caught
    # by tests/eval_explanations.py's behavioral assertions, not by eyeballing.
    sentences = doc.body.split(". ")
    summary = ". ".join(sentences[:2]).strip().rstrip(".") + "."
    return f"{summary} (source: {doc.title}, {doc.source_url})"


def _explain_with_gemini(finding_line: str, doc: KBDoc, api_key: str) -> str:
    import google.generativeai as genai  # imported lazily - optional dependency

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(_build_prompt(finding_line, doc))

    usage = getattr(response, "usage_metadata", None)
    if usage:
        log_cost(
            provider="gemini",
            model="gemini-2.0-flash",
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count,
        )
    return response.text.strip()


def _explain_with_groq(finding_line: str, doc: KBDoc, api_key: str) -> str:
    # Groq serves open-weight models behind an OpenAI-compatible API, with a
    # free tier and no billing setup required - the open-weight alternative
    # to the Gemini path above. Same grounded prompt either way.
    # Note: llama-3.3-70b-versatile was deprecated by Groq on 2026-06-17;
    # gpt-oss-120b is their recommended replacement (see console.groq.com/docs/deprecations).
    from groq import Groq  # imported lazily - optional dependency

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": _build_prompt(finding_line, doc)}],
        temperature=0.2,
        max_tokens=200,
    )

    usage = getattr(completion, "usage", None)
    if usage:
        log_cost(
            provider="groq",
            model="openai/gpt-oss-120b",
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
        )
    return completion.choices[0].message.content.strip()
