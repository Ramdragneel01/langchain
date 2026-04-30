from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

from src.embeddings import build_embeddings
from src.settings import load_settings

SUPPORTED_SUFFIXES = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
}

IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "coverage",
    "storybook-static",
}

MAX_FILE_BYTES = 2_000_000


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative")

    step = max(1, chunk_size - chunk_overlap)
    chunks: list[str] = []
    for start in range(0, len(text), step):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
    return chunks


def iter_source_files(repo_path: Path) -> list[Path]:
    results: list[Path] = []
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        lower_parts = [part.lower() for part in path.parts]
        if any(part in IGNORED_DIR_NAMES for part in lower_parts):
            continue
        if any(part.startswith(".venv") or part.startswith("venv") for part in lower_parts):
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        results.append(path)
    return results


def build_index(repo_path: Path, out_index: Path) -> dict[str, int]:
    settings = load_settings()
    embedding_model = build_embeddings(settings)

    files = iter_source_files(repo_path)
    records: list[dict[str, str]] = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not content.strip():
            continue

        relative_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
        chunks = chunk_text(
            content,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        for chunk_number, chunk in enumerate(chunks):
            chunk_id = f"{relative_path}::chunk-{chunk_number}"
            records.append(
                {
                    "chunk_id": chunk_id,
                    "source": relative_path,
                    "content": chunk,
                }
            )

    if not records:
        raise RuntimeError("No indexable content found in target repo")

    texts = [record["content"] for record in records]
    embeddings = np.array(embedding_model.embed_documents(texts), dtype=np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normalized = embeddings / norms

    out_index.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_index / "vectors.npz", embeddings=normalized)

    with (out_index / "documents.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo_path": str(repo_path),
        "total_files": len(files),
        "total_chunks": len(records),
        "embedding_provider": settings.embedding_provider,
        "embedding_dim": int(normalized.shape[1]),
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }
    (out_index / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return {"files": len(files), "chunks": len(records)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a retrieval index from a source repository"
    )
    parser.add_argument("--repo-path", required=True, help="Path to target repository")
    parser.add_argument(
        "--out-index",
        default=None,
        help="Output index directory (defaults to INDEX_PATH env or data/index)",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    settings = load_settings()
    repo_path = Path(args.repo_path).resolve()
    out_index = Path(args.out_index).resolve() if args.out_index else settings.index_path

    stats = build_index(repo_path=repo_path, out_index=out_index)
    print(
        f"Index built successfully at {out_index} (files={stats['files']}, chunks={stats['chunks']})"
    )


if __name__ == "__main__":
    main()
