from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable

from langchain_core.embeddings import Embeddings

from src.settings import Settings

try:
    from langchain_openai import OpenAIEmbeddings
except Exception:  # pragma: no cover
    OpenAIEmbeddings = None


class HashEmbeddings(Embeddings):
    """Deterministic local embeddings for offline development and smoke testing."""

    def __init__(self, dim: int = 256) -> None:
        if dim < 16:
            raise ValueError("dim must be at least 16")
        self.dim = dim

    def _tokenize(self, text: str) -> Iterable[str]:
        return re.findall(r"[A-Za-z0-9_]+", text.lower())

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = list(self._tokenize(text))
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            value = int.from_bytes(digest[:8], byteorder="big", signed=False)
            index = value % self.dim
            sign = 1.0 if (digest[8] & 1) == 0 else -1.0
            weight = 1.0 + ((digest[9] % 7) / 10.0)
            vector[index] += sign * weight

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)


def build_embeddings(settings: Settings) -> Embeddings:
    use_openai = settings.embedding_provider == "openai"
    if use_openai:
        if OpenAIEmbeddings is None:
            raise RuntimeError(
                "langchain-openai is not installed. Install dependencies or switch EMBEDDING_PROVIDER=hash"
            )
        return OpenAIEmbeddings(model=settings.openai_embedding_model)

    return HashEmbeddings(dim=settings.embedding_dim)
