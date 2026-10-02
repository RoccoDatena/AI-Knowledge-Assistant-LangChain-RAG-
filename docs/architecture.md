# Architecture

## Layers

### Domain

Contains entities and ports. It does not import FastAPI, ChromaDB, LangChain
providers, or filesystem adapters.

### Application

Contains use cases such as indexing, retrieval, deletion, and RAG. It depends
on ports and coordinates infrastructure through dependency injection.

### Infrastructure

Contains concrete adapters for JSON, pypdf, OpenRouter, hashing embeddings,
and optional ChromaDB, with persistent JSON as the default vector store.

### Interfaces

Contains HTTP routes and Pydantic request/response models.

## RAG safety behavior

The RAG service applies a minimum retrieval score. When no chunk passes the
threshold, it returns `Informazione non trovata nei documenti.` without calling
the LLM. Citations are built from retrieved chunk metadata by the backend.

## Replacement points

| Current adapter | Future replacement |
| --- | --- |
| `MockLLM` | OpenRouter, Bedrock, OpenAI, Anthropic, Ollama |
| Hashing embeddings | Sentence Transformers or hosted embeddings |
| JSON vector store | ChromaDB, Qdrant, Pinecone |
| JSON repositories | SQLite, PostgreSQL, DynamoDB, S3 |
