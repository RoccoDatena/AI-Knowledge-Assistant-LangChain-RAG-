# Roadmap

## Next

- activate the optional Sentence Transformers adapter when local model storage
  is acceptable
- add a versioned real-world retrieval evaluation dataset

## Later

- OCR for scanned PDFs
- reranking and MMR retrieval
- SQLite or PostgreSQL conversation repository
- authentication and multi-user knowledge bases
- RAG answer quality evaluation dataset
- observability and tracing
- optional AWS deployment

## Provider evolution

The application layer uses `LLMProvider` and `EmbeddingProvider` ports. Future
providers should be implemented as adapters, keeping use cases unchanged.
