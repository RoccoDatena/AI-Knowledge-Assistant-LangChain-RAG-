# Portfolio demo

This walkthrough demonstrates the complete local flow without Ollama, Docker, or a paid API.

## 1. Configure the backend

From the repository root:

```powershell
Copy-Item .env.example .env
.\.venv\Scripts\Activate.ps1
```

The default `LLM_PROVIDER=mock` is deterministic and requires no API key. For semantic retrieval, use:

```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## 2. Start the API

```powershell
python -m uvicorn app.main:app --reload
```

Verify readiness at `http://127.0.0.1:8000/health/ready`.

## 3. Start the UI

In a second terminal:

```powershell
streamlit run frontend/streamlit_app.py
```

Open `http://127.0.0.1:8501`.

## 4. Demonstrate the RAG flow

1. Create a conversation in the sidebar.
2. Upload a text-based PDF.
3. Click **Index documents**.
4. Ask a question whose answer is present in the PDF.
5. Inspect the grounded answer and its page citation.
6. Ask a question absent from the PDF and verify the standard response:
   `Informazione non trovata nei documenti.`

## 5. Automated verification

```powershell
python -m scripts.check_semantic_embeddings
python -m pytest -q
ruff check .
```

The demo keeps runtime data under `data/`, which is excluded from Git.
