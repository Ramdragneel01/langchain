# Repo Research Copilot

LangChain-powered assistant that answers questions about a target codebase using retrieval-augmented generation (RAG) and file-level citations.

## Why This Project
This project is designed for practical engineering workflows:
1. Understand large repositories quickly.
2. Locate implementation details with source citations.
3. Build reusable agent pipelines instead of one-off prompt scripts.

## Features
1. Repository ingestion for docs and code files.
2. Chunking + embeddings + FAISS vector index.
3. Question answering with explicit citation output.
4. FastAPI backend endpoint for integration.
5. Streamlit UI for interactive demos.
6. Basic evaluation harness for repeatable quality checks.

## Architecture
1. Ingestion stage: files -> chunks -> embeddings -> vector index.
2. Retrieval stage: question -> top-k relevant chunks.
3. Generation stage: LLM answer constrained to retrieved context.
4. Output stage: answer plus source paths/chunk identifiers.

## Tech Stack
1. Python 3.11+
2. LangChain
3. FAISS
4. FastAPI + Uvicorn
5. Streamlit

## Project Structure
```text
repo-research-copilot/
  src/
    ingest.py
    retrieval.py
    api.py
  ui/
    app.py
  eval/
    questions.json
    run_eval.py
  data/
    raw/
    index/
  .env.example
  requirements.txt
  README.md
```

## Quick Start

### 1) Create environment and install dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Configure environment
Copy `.env.example` to `.env` and fill required keys.

Example:
```env
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### 3) Build index
```powershell
python -m src.ingest --repo-path C:/github_repos/agentic-research-assistant --out-index data/index
```

### 4) Start API
```powershell
uvicorn src.api:app --reload --port 8010
```

### 5) Start UI
```powershell
streamlit run ui/app.py --server.port 8511
```

## API

### `POST /ask`
Request:
```json
{
  "question": "Where is retry logic implemented?",
  "k": 5
}
```

Response:
```json
{
  "answer": "Retry logic is implemented in ...",
  "sources": [
    {
      "path": "src/retries.py",
      "chunk_id": "chunk-42"
    }
  ]
}
```

## Evaluation
Run basic quality checks with:
```powershell
python -m eval.run_eval --api-url http://127.0.0.1:8010 --questions eval/questions.json
```

Suggested metrics:
1. Answer success rate.
2. Citation coverage rate.
3. Empty citation failures.

## Demo Script (90 Seconds)
1. Show question: "How is ingestion implemented?"
2. Show answer and citation list.
3. Open one cited file to validate trust.
4. Ask one architecture-level question.
5. Show consistent citation output.

## Roadmap
1. Multi-repo indexing and namespace filters.
2. Git-aware indexing by branch/commit.
3. Re-ranking for higher precision retrieval.
4. Optional web fallback tool for missing context.
5. CI evaluation gate before deployment.

## Keep vs Reference Fork Note
Use released LangChain packages for this app by default.
Keep your LangChain fork for upstream contributions, patch testing, and source exploration.
