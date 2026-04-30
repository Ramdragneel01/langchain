from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

from src.embeddings import build_embeddings
from src.settings import load_settings

try:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover
    ChatOpenAI = None
    ChatPromptTemplate = None
    StrOutputParser = None


@dataclass
class RetrievedSource:
    chunk_id: str
    path: str
    score: float
    excerpt: str


class RepoResearchEngine:
    def __init__(self, index_path: Path | None = None) -> None:
        load_dotenv()
        self.settings = load_settings()
        self.index_path = Path(index_path or self.settings.index_path)
        self.embedding_model = build_embeddings(self.settings)
        self._records: list[dict[str, str]] = []
        self._vectors = np.zeros((0, self.settings.embedding_dim), dtype=np.float32)
        self._load_index()

    def _load_index(self) -> None:
        vectors_path = self.index_path / "vectors.npz"
        docs_path = self.index_path / "documents.jsonl"
        if not vectors_path.exists() or not docs_path.exists():
            raise FileNotFoundError(
                f"Index files missing at {self.index_path}. Run ingest first."
            )

        npz = np.load(vectors_path)
        self._vectors = npz["embeddings"].astype(np.float32)

        records: list[dict[str, str]] = []
        with docs_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))

        if not records:
            raise RuntimeError("Loaded index is empty")
        if len(records) != len(self._vectors):
            raise RuntimeError("Index mismatch: vectors and documents length differ")

        self._records = records

    def _retrieve(self, question: str, k: int) -> list[RetrievedSource]:
        if not question.strip():
            raise ValueError("question cannot be empty")

        query = np.array(self.embedding_model.embed_query(question), dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            query_norm = 1.0
        query = query / query_norm

        scores = self._vectors @ query
        top_k = max(1, min(k, len(scores)))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[RetrievedSource] = []
        for idx in top_indices:
            row = self._records[int(idx)]
            excerpt = row["content"].replace("\n", " ").strip()
            excerpt = excerpt[:240] + ("..." if len(excerpt) > 240 else "")
            results.append(
                RetrievedSource(
                    chunk_id=row["chunk_id"],
                    path=row["source"],
                    score=float(scores[int(idx)]),
                    excerpt=excerpt,
                )
            )
        return results

    def _answer_with_openai(
        self, question: str, sources: list[RetrievedSource]
    ) -> str | None:
        if not self.settings.use_openai_chat:
            return None
        if ChatOpenAI is None or ChatPromptTemplate is None or StrOutputParser is None:
            return None

        context_lines = []
        for source in sources:
            context_lines.append(
                f"Source: {source.path} | Chunk: {source.chunk_id}\n{source.excerpt}"
            )
        context = "\n\n".join(context_lines)

        prompt = ChatPromptTemplate.from_template(
            """
You are a repository research assistant.
Answer only using the provided context. If context is insufficient, say so clearly.
Keep the answer concise and technical.

Question:
{question}

Context:
{context}
""".strip()
        )
        llm = ChatOpenAI(model=self.settings.openai_chat_model, temperature=0)
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"question": question, "context": context}).strip()

    def _answer_fallback(self, question: str, sources: list[RetrievedSource]) -> str:
        summary = [
            "Answer generated from retrieved repository context.",
            f"Question: {question.strip()}",
            "Most relevant snippets:",
        ]
        for source in sources[:3]:
            summary.append(f"- {source.path}: {source.excerpt}")
        return "\n".join(summary)

    def ask(self, question: str, k: int | None = None) -> dict[str, object]:
        top_k = k if k is not None else self.settings.top_k
        sources = self._retrieve(question=question, k=top_k)

        answer = self._answer_with_openai(question=question, sources=sources)
        if not answer:
            answer = self._answer_fallback(question=question, sources=sources)

        payload_sources = [
            {
                "path": source.path,
                "chunk_id": source.chunk_id,
                "score": round(source.score, 6),
                "excerpt": source.excerpt,
            }
            for source in sources
        ]

        return {
            "answer": answer,
            "sources": payload_sources,
        }
