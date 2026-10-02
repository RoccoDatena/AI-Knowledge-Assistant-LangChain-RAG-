# ADR-001: Layered architecture with ports and adapters

## Status

Accepted

## Decision

Use a layered architecture with domain ports and infrastructure adapters.

## Rationale

The project must support several LLM, embedding, persistence, and vector store
providers without changing business logic. Protocol-based ports keep those
choices explicit and testable.

## Consequences

- More files than a single-script prototype.
- Easier provider replacement and isolated tests.
- Infrastructure details remain outside the domain.
