from __future__ import annotations

from typing import Iterable

from openai import OpenAI


def build_embedding_texts(records) -> list[str]:
    texts = []
    for r in records:
        texts.append(" | ".join([str(r.get("title", "")), str(r.get("description", "")), str(r.get("customer_impact", ""))]))
    return texts


def generate_embeddings(texts: Iterable[str], api_key: str, model: str = "text-embedding-3-small") -> list[list[float]]:
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=model, input=list(texts))
    return [d.embedding for d in response.data]
