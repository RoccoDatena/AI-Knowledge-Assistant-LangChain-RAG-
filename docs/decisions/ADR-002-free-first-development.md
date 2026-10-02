# ADR-002: Free-first local development

## Status

Accepted

## Decision

Use a mock provider and lightweight hashing embeddings by default. Keep remote
OpenRouter access optional and configure it only through `.env`.

## Rationale

The project must not require paid APIs, Docker, Ollama, local LLMs, or large
model downloads during development.

## Consequences

- The default embedding baseline is weaker than a transformer model.
- External provider limits do not block automated tests.
- Quality-focused adapters can be added later behind the same ports.
