# Portfolio and interview guide

## What this project demonstrates

AI Knowledge Assistant is a document-grounded assistant designed around
replaceable AI providers and explicit application boundaries. It demonstrates:

- Python and FastAPI API design
- LangChain prompt orchestration without coupling the domain to LangChain
- PDF ingestion, chunking, embeddings, retrieval, and citations
- grounded answers that refuse to invent unsupported information
- JSON persistence suitable for a free local demo
- provider adapters ready for OpenRouter, Ollama, Bedrock, or another backend
- testing, linting, typing, structured logs, Docker, and CI

## Suggested demo flow

1. Start the API with the mock provider.
2. Call `/health` and `/health/ready`.
3. Upload a text-based PDF and index it.
4. Search the document and inspect chunk metadata.
5. Ask a question whose answer is present and show its citations.
6. Ask a question absent from the document and show the safe refusal.
7. Explain how `LLMProvider`, `EmbeddingProvider`, and `VectorStore` allow
   infrastructure changes without rewriting use cases.

## Talking points

- The mock provider makes the happy path deterministic and free.
- OpenRouter is an optional remote adapter; secrets stay in `.env`.
- The JSON vector store is intentionally lightweight; ChromaDB and semantic
  embeddings are isolated extension points.
- Citations are generated from retrieved metadata, never fabricated by the
  LLM.
- AWS deployment is documented but intentionally opt-in and not provisioned.

## Honest limitations

The current version does not include OCR, authentication, multi-user tenancy,
production database transactions, or a large benchmark dataset. These are
documented roadmap items rather than hidden gaps.
