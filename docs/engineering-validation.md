# Engineering validation and development process

This document explains how the AI Knowledge Assistant was built, verified,
and hardened. It is intended to make the repository reproducible for a
reviewer, recruiter, or future contributor.

The objective was not only to make the chat work, but to prove that the
application behaves predictably when the answer is supported, unsupported, or
when an infrastructure component fails.

## 1. Development approach

The implementation followed short milestones:

1. Define the use cases and API contract.
2. Separate domain logic from infrastructure adapters.
3. Implement the document lifecycle: upload, extraction, chunking, indexing,
   search, and deletion.
4. Implement grounded RAG with citations and an explicit not-found response.
5. Add JSON persistence for conversations and documents.
6. Add the Streamlit interface.
7. Add quality gates, retrieval evaluation, and operational diagnostics.
8. Verify the application manually through the API and browser UI.

Each milestone was kept small enough to be tested independently before moving
to the next one.

## 2. Test strategy

The repository uses multiple verification layers. Each layer catches a
different class of defect.

### Unit tests

Unit tests cover isolated business and infrastructure behavior, including:

- chunking and page metadata;
- JSON repositories;
- hashing and Sentence Transformers embedding adapters;
- OpenRouter request and response mapping;
- retrieval score filtering;
- RAG refusal behavior;
- source citation construction;
- configuration validation.

Example command:

```powershell
python -m pytest -q tests/test_rag.py tests/test_conversation_repository.py
```

### API tests

FastAPI `TestClient` tests exercise the public REST contract without starting
a real server. They verify:

- HTTP status codes;
- request validation;
- structured error envelopes;
- request IDs;
- conversation lifecycle;
- document upload and deletion;
- search filters;
- persistence across history reads.

### End-to-end workflow tests

The document workflow test simulates a complete lifecycle:

```text
PDF upload → extraction → chunking → indexing → semantic search → chat → deletion
```

The conversation history test performs the equivalent of a UI refresh: it
writes an assistant answer with citations, creates a new client, reloads the
history endpoint, and verifies that grounding metadata and sources are still
present.

### Static quality checks

The project uses three automated quality gates:

```powershell
ruff check .
ruff format --check .
mypy app
```

Ruff catches style and common Python issues. Mypy checks the application layer
with static typing. Optional runtime dependencies are imported through
controlled adapters so that the default CI environment remains lightweight.

### Retrieval evaluation

Retrieval is evaluated independently from the LLM. This makes comparisons
repeatable and prevents a fluent model response from hiding a poor search
result. The benchmark reports Hit@K and Mean Reciprocal Rank (MRR).

The bundled synthetic corpus currently reports:

| Embedding provider | Hit@4 | MRR |
| --- | ---: | ---: |
| Hashing baseline | 1.00 | 0.8229 |
| `all-MiniLM-L6-v2` | 1.00 | 0.8750 |

These values are reference measurements for the fixture corpus, not a claim
about every future document collection.

Run the offline benchmark with:

```powershell
$env:EMBEDDING_PROVIDER="hashing"
python -m scripts.evaluate_retrieval --corpus evaluation/corpus.json
```

## 3. Manual verification

Automated tests are complemented by a local smoke test. The default setup
uses `LLM_PROVIDER=mock`, so no paid API or local LLM is required.

Start the services in separate terminals:

```powershell
python -m uvicorn app.main:app --reload
python -m streamlit run frontend/streamlit_app.py --server.port 8501
```

Then verify:

1. Open `http://127.0.0.1:8501`.
2. Confirm the document appears in the knowledge base.
3. Ask a question answered by the PDF.
4. Confirm `Risposta grounded` and the page citation.
5. Ask an unrelated question, such as a question about a different country.
6. Confirm `Informazione non trovata nei documenti.` and no sources.
7. Refresh the page and confirm that the conversation and citations remain.
8. Use the semantic search panel to inspect the retrieved chunks and scores.

The API can be checked independently at:

- `GET /health`
- `GET /health/ready`
- `http://127.0.0.1:8000/docs`

## 4. Real failures found during development

The following issues were intentionally diagnosed from logs and converted into
regression protections.

| Symptom | Root cause | Resolution |
| --- | --- | --- |
| CI mypy failure for `chromadb` | Optional dependency was imported statically | Load the optional module through an adapter boundary |
| CI upload test failure | Windows-style path traversal was not normalized on Linux | Normalize both slash styles before taking the filename basename |
| Chat requests taking minutes | Sentence Transformers repeatedly attempted Hugging Face network checks | Add configurable `local_files_only` mode for cached offline models |
| Out-of-domain questions receiving context | A semantic score threshold alone was too permissive | Require meaningful lexical evidence before calling the LLM |
| Local test embedding dimension mismatch | A test read persisted 384-dimensional vectors while using a 64-dimensional hashing provider | Isolate tests with an in-memory vector store |
| Citations disappearing after refresh | Message persistence stored only role and content | Persist grounded status and source metadata with assistant messages |

This workflow is important: each production-relevant failure resulted in a
code change, a focused test, or an explicit operational rule.

## 5. Error and observability checks

The API exposes structured errors instead of leaking implementation details.
Each request receives an `X-Request-ID`, which is also written to structured
logs. This allows a failed frontend request to be correlated with backend
output.

Provider failures are returned as `502 PROVIDER_ERROR`. Validation failures
are returned as `422 VALIDATION_ERROR`. Missing conversations and documents
return stable `404` responses.

The readiness endpoint verifies configuration separately from the liveness
endpoint, which is useful for future container or cloud deployments.

## 6. Definition of done for a milestone

A milestone is considered complete only when:

- the behavior is implemented behind the appropriate application boundary;
- the happy path is verified;
- the relevant failure path is verified;
- persistence or API contracts are tested when applicable;
- Ruff and mypy remain clean;
- the behavior is documented;
- the manual smoke test still works when the feature is user-visible.

## 7. Reproducing the quality gate

From the repository root:

```powershell
.\scripts\quality-check.ps1
```

Or run the checks individually:

```powershell
python -m pytest -q
ruff check .
ruff format --check .
mypy app
```

GitHub Actions runs the same checks on pushes and pull requests. The CI badge
in the main README is the first high-level signal; this document explains the
evidence behind it.

## 8. Current limitations

The validation process is intentionally honest about its boundaries:

- the retrieval benchmark uses a small synthetic corpus;
- PDF OCR is not covered because scanned PDFs are not yet supported;
- the default LLM is deterministic mock output;
- free remote model availability depends on the selected provider;
- JSON persistence is suitable for a portfolio and local demo, not concurrent
  production traffic.

These limitations are tracked in the project roadmap rather than hidden behind
 a successful demo.
