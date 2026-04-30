# LangChain Repo Research Copilot: 1-2 Day Implementation Checklist

## Outcome
Ship a portfolio-ready LangChain app that answers questions about a codebase and returns file-level citations.

## Keep/Use Your LangChain Fork Decision
Use released LangChain packages first for this project.

Use your fork only when at least one of these is true:
1. You need a patch or feature that is not yet released.
2. You are actively contributing fixes upstream.
3. You are benchmarking or testing internals against upstream behavior.

If none are true, keep the fork as a profile/reference asset and build this project with pip-installed LangChain.

## Scope (MVP)
1. Ingest markdown/text/code files from one target repo.
2. Build embeddings and vector index.
3. Answer questions with citations to source chunks.
4. Expose one API endpoint for question answering.
5. Add a minimal Streamlit UI for demo.
6. Add a lightweight evaluation script with at least 10 questions.

## Suggested Target Repo For Demo
Start with one of your existing repos where architecture and docs are clear:
1. `agentic-research-assistant`
2. `mlops-sentinel`
3. `agent-tracer`

## Day 1 (Core Build)

### 1) Bootstrap project
```powershell
Set-Location C:/github_repos
New-Item -ItemType Directory -Path repo-research-copilot -Force | Out-Null
Set-Location C:/github_repos/repo-research-copilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install "langchain>=0.3,<0.4" "langchain-community>=0.3,<0.4" "langchain-openai>=0.2,<0.3" "faiss-cpu>=1.8,<2" "tiktoken>=0.8,<1" "fastapi>=0.116,<1" "uvicorn>=0.31,<1" "streamlit>=1.40,<2" "python-dotenv>=1.0,<2" "pydantic>=2.9,<3" "httpx>=0.28,<1"
pip freeze > requirements.txt
```

### 2) Create folder layout
```powershell
New-Item -ItemType Directory -Path src,ui,data/raw,data/index,eval -Force | Out-Null
New-Item -ItemType File -Path src/ingest.py,src/retrieval.py,src/api.py,ui/app.py,eval/questions.json,eval/run_eval.py,.env.example,README.md -Force | Out-Null
```

### 3) Build ingestion and retrieval pipeline
Implement these pieces:
1. Load files recursively for `.md`, `.txt`, `.py`, `.ts`, `.tsx`.
2. Chunk with overlap for context continuity.
3. Embed chunks and store in FAISS index under `data/index`.
4. Retrieval function returns top-k chunks plus source metadata.

### 4) Build answer chain with citations
Implement a QA chain that:
1. Uses retrieved chunks as context.
2. Forces answer format with `Answer` and `Sources` sections.
3. Returns source file paths and snippet hints.

### 5) Expose API
Create a `POST /ask` endpoint in FastAPI with payload:
```json
{
  "question": "Where is retry logic implemented?",
  "k": 5
}
```

Response shape:
```json
{
  "answer": "...",
  "sources": [
    {
      "path": "src/some_file.py",
      "chunk_id": "..."
    }
  ]
}
```

## Day 2 (Demo + Quality)

### 1) Add Streamlit UI
Features:
1. Question input box.
2. Answer panel.
3. Expandable citation list with source path and chunk text.

Run command:
```powershell
streamlit run ui/app.py
```

### 2) Add evaluation script
In `eval/questions.json`, add at least 10 portfolio-relevant questions.

Examples:
1. "What is the ingestion flow?"
2. "Where are environment variables defined?"
3. "How does the API expose health checks?"

`eval/run_eval.py` should report:
1. Question answered or failed.
2. Citation count per answer.
3. Simple pass/fail if citations are empty.

### 3) Final polish
1. README with setup, architecture, and demo instructions.
2. `.env.example` with required keys.
3. 90-second demo script in README.

## Exact Run Commands (MVP Demo)
```powershell
Set-Location C:/github_repos/repo-research-copilot
.\.venv\Scripts\Activate.ps1

# 1) Build index
python -m src.ingest --repo-path C:/github_repos/agentic-research-assistant --out-index data/index

# 2) Start API
uvicorn src.api:app --reload --port 8010

# 3) Start UI (new terminal)
streamlit run ui/app.py --server.port 8511

# 4) Run eval
python -m eval.run_eval --api-url http://127.0.0.1:8010 --questions eval/questions.json
```

## Definition of Done
1. Answers at least 10 eval questions.
2. Every answer includes at least one source citation.
3. End-to-end setup from clean clone works in under 10 minutes.
4. Demo can be explained clearly in under 2 minutes.

## Portfolio Positioning (Use In Repo Description)
"LangChain-powered repository research copilot with retrieval-augmented answers and source citations for engineering workflows."
