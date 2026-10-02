# Local development

## Environment

The project is developed on Windows with Python 3.13. The virtual environment
is intentionally local to the repository and excluded from Git.

No local LLM, GPU, Ollama, Docker, or Docker Compose is required.

Docker artifacts are provided for a future reproducible deployment. They are
optional and are not needed for the Python-based local workflow.

Backend dependencies are in `requirements.txt`. Development and quality tools
are in `requirements-dev.txt`. Streamlit is intentionally optional and is
isolated in `requirements-frontend.txt` to reduce local disk usage.
Sentence Transformers is also optional and is isolated in
`requirements-embeddings.txt` because it installs PyTorch and downloads a
model on first use.
Set `EMBEDDING_PROVIDER=sentence_transformers` and optionally adjust
`EMBEDDING_MODEL` to activate semantic embeddings; the default remains the
lightweight hashing provider.

## Configuration

Copy `.env.example` to `.env`. Keep secrets out of Git. The default mock
provider makes tests and development possible without an external API key.
Configuration is validated when it is read. For example, `LLM_PROVIDER=openrouter`
requires `OPENROUTER_API_KEY`, while `RAG_MIN_SCORE` must be between `0` and `1`.
The optional frontend reads `API_BASE_URL` from the same `.env` file.

## Development loop

```powershell
pytest -q
ruff check .
ruff format --check .
mypy app
```

Or run the complete sequence with `.\scripts\quality-check.ps1`.

## Data

Runtime data is stored below `data/` and ignored by Git:

- `data/uploads`: uploaded PDFs
- `data/documents`: document metadata
- `data/conversations`: conversation history
- `data/vector_store`: reserved for persistent vector storage
## Docker dependency profile

The provided API image installs `requirements.txt`, the lightweight backend set.
It does not install Sentence Transformers or PyTorch. When using Docker Compose,
set `EMBEDDING_PROVIDER=hashing` in `.env`, or build a dedicated image from
`requirements-embeddings.txt` if semantic embeddings are required. This keeps
the default image small and makes the heavier model dependency an explicit
operational choice.
